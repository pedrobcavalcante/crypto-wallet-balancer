import logging

logger = logging.getLogger(__name__)


class PortfolioAnalysis:
    def __init__(
        self,
        public_service,
        private_service,
        bnb_wallet_db,
        db_manager,
        max_percentage_difference,
    ):
        self.public_service = public_service
        self.private_service = private_service
        self.bnb_wallet_db = bnb_wallet_db
        self.db_manager = db_manager
        self.max_percentage_difference = max_percentage_difference

    def get_combined_assets(self):
        logger.info("Buscando ativos na Binance...")
        binance_assets = self.private_service.get_account_assets()
        binance_asset_dict = {
            asset["asset"].lower(): float(asset["free"]) for asset in binance_assets
        }

        logger.info("Buscando ativos na carteira BNB...")
        bnb_assets = self.bnb_wallet_db.get_all_token_balances()
        bnb_asset_dict = {
            token["token_name"].lower(): float(token["quantity"])
            for token in bnb_assets
        }

        combined_assets = binance_asset_dict.copy()
        for token_name, quantity in bnb_asset_dict.items():
            combined_assets[token_name] = combined_assets.get(token_name, 0) + quantity

        logger.debug(f"Ativos combinados: {combined_assets}")
        return combined_assets

    def calculate_portfolio_details(self, combined_assets):
        logger.info("Obtendo preços atuais da Binance...")
        all_prices = self.public_service.get_current_prices()
        portfolio_value = 0.0
        asset_details = []

        logger.info("Calculando detalhes do portfólio...")
        for asset_name, total_quantity in combined_assets.items():
            symbol = f"{asset_name.upper()}USDT"
            if symbol in all_prices:
                current_price = all_prices[symbol]
                asset_value = total_quantity * current_price
                portfolio_value += asset_value
                asset_details.append(
                    {
                        "name": asset_name.upper(),
                        "quantity": total_quantity,
                        "price": current_price,
                        "value": asset_value,
                    }
                )

        if portfolio_value > 0:
            for asset in asset_details:
                asset["percentage"] = (asset["value"] / portfolio_value) * 100
            asset_details.sort(key=lambda x: x["percentage"], reverse=True)

        logger.debug(f"Detalhes dos ativos: {asset_details}")
        return asset_details, portfolio_value

    def analyze_differences(self, asset_details):
        logger.info("Analisando diferenças percentuais...")
        saved_assets = self.db_manager.get_all_assets()
        saved_asset_dict = {
            asset["asset_name"].lower(): asset for asset in saved_assets
        }

        recommendations = []

        for asset in asset_details:
            asset_name = asset["name"].lower()
            if asset_name in saved_asset_dict:
                saved_asset = saved_asset_dict[asset_name]
                saved_percentage = saved_asset["percentage"]
                current_percentage = asset["percentage"]
                difference = current_percentage - saved_percentage

                recommendation = {
                    "name": asset["name"],
                    "current_percentage": current_percentage,
                    "saved_percentage": saved_percentage,
                    "difference": difference,
                }

                if difference > self.max_percentage_difference:
                    recommendation["action"] = "sell"

                    # Calcula a quantidade a vender com base na diferença percentual
                    sell_quantity = (difference / 100) * asset["quantity"]
                    self.place_sell_order(asset["name"], sell_quantity, asset["price"])

                elif difference < -self.max_percentage_difference:
                    recommendation["action"] = "buy"

                    # Calcula a quantidade a comprar com base na diferença percentual
                    buy_quantity = (abs(difference) / 100) * saved_asset["quantity"]
                    self.place_buy_order(asset["name"], buy_quantity, asset["price"])
                else:
                    recommendation["action"] = "hold"

                logger.debug(f"Recomendação para {asset['name']}: {recommendation}")
                recommendations.append(recommendation)
            else:
                recommendations.append(
                    {
                        "name": asset["name"],
                        "action": "not found",
                        "message": "Asset not found in database.",
                    }
                )
                logger.warning(f"{asset['name']}: Não encontrado no banco de dados.")

        return recommendations

    def place_buy_order(self, symbol, quantity, price):
        """
        Envia uma ordem de compra usando o serviço private_service.
        """
        logger.info(f"Preparando ordem de compra para {symbol}.")
        try:
            order_response = self.private_service.place_buy_order(
                symbol, quantity, price
            )
            logger.info(f"Ordem de compra executada: {order_response}")
        except Exception as e:
            logger.error(f"Erro ao executar ordem de compra: {e}")

    def place_sell_order(self, symbol, quantity, price):
        """
        Envia uma ordem de venda usando o serviço private_service.
        """
        logger.info(f"Preparando ordem de venda para {symbol}.")
        try:
            order_response = self.private_service.place_sell_order(
                symbol, quantity, price
            )
            logger.info(f"Ordem de venda executada: {order_response}")
        except Exception as e:
            logger.error(f"Erro ao executar ordem de venda: {e}")

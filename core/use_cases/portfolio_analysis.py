import logging
from typing import List, Tuple, Dict

from core.database.bnb_wallet_db_manager import BNBWalletDBManager
from core.database.db_manager import DBManager
from core.services.binance_private_service import BinancePrivateService
from core.services.binance_public_service import BinancePublicService
from core.use_cases.average_price_calculator import AveragePriceCalculator

logger = logging.getLogger(__name__)


class PortfolioAnalysis:
    def __init__(
        self,
        public_service: BinancePublicService,
        private_service: BinancePrivateService,
        bnb_wallet_db: BNBWalletDBManager,
        db_manager: DBManager,
        max_percentage_difference: float,
    ):
        self.public_service = public_service
        self.private_service = private_service
        self.bnb_wallet_db = bnb_wallet_db
        self.db_manager = db_manager
        self.max_percentage_difference = max_percentage_difference

    def get_combined_assets(self) -> Dict[str, float]:
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

    def calculate_portfolio_details(
        self, combined_assets: Dict[str, float]
    ) -> Tuple[List[Dict[str, float]], float]:
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

    def analyze_differences(
        self, asset_details: List[Dict[str, float]]
    ) -> List[Dict[str, float]]:
        logger.info("Analisando diferenças percentuais...")
        saved_assets = self.db_manager.get_all_assets()
        saved_asset_dict = {
            asset_data["asset_name"].lower(): asset_data for asset_data in saved_assets
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

                    # Verifica se o preço de venda é maior que o preço médio
                    if asset["price"] > saved_asset["average_price"]:
                        sell_quantity = (difference / 100) * asset["quantity"]
                        self.place_sell_order(
                            asset["name"], sell_quantity, asset["price"]
                        )
                    else:
                        logger.warning(
                            f"Preço de venda de {asset['name']} (${asset['price']:.2f}) é menor ou igual ao preço médio (${saved_asset['average_price']:.2f}). Ordem de venda não enviada."
                        )

                elif difference < -self.max_percentage_difference:
                    recommendation["action"] = "buy"

                    # Calcula a quantidade a comprar com base na diferença percentual
                    buy_quantity = (abs(difference) / 100) * saved_asset["points"]
                    self.place_buy_order(
                        asset["name"],
                        buy_quantity,
                        asset["price"],
                        saved_asset["average_price"],
                        asset["quantity"],
                    )
                else:
                    recommendation["action"] = "hold"

                logger.debug(f"Recomendação para {asset['name']}: {recommendation}")
                recommendations.append(recommendation)
            else:
                # Ordem de venda para ativos ausentes no banco
                logger.warning(f"{asset['name']}: Não encontrado no banco de dados.")
                logger.warning(f"{asset['name']}: Asset not found in database.")

                # Vender todo o ativo
                logger.info(f"Mandando vender todo o ativo: {asset['name']}.")
                self.place_sell_order(
                    symbol=asset["name"],
                    quantity=asset["quantity"],
                    price=asset["price"],
                )

                recommendations.append(
                    {
                        "name": asset["name"],
                        "action": "sell_all",
                        "message": "Ativo não encontrado no banco de dados. Vendido totalmente.",
                    }
                )

        return recommendations

    def place_buy_order(
        self, symbol, quantity, price, average_price, quantidade_atual_do_ativo
    ):
        """
        Atualiza o preço médio antes de comprar e envia a ordem.
        """
        logger.info(f"Atualizando preço médio antes de comprar {symbol}.")

        # Atualiza o preço médio
        calculator = AveragePriceCalculator(self.db_manager)
        try:
            new_average_price = calculator.calculate_new_average_price(
                asset_name=symbol,
                order_price=price,
                order_quantity=quantity,
                average_price=average_price,
                quantidade_atual_do_ativo=quantidade_atual_do_ativo,
            )
            logger.info(
                f"Preço médio atualizado para {symbol}: ${new_average_price:.2f}."
            )

            # Envia a ordem de compra

            order_response = self.private_service.place_buy_order(
                symbol, quantity, price
            )
            logger.info(f"Ordem de compra executada: {order_response}")
        except Exception as e:
            logger.error(f"Erro ao executar ordem de compra: {e}")

    def place_sell_order(self, symbol: str, quantity: float, price: float):
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

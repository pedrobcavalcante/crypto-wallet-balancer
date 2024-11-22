import logging
from typing import List, Tuple, Dict, Optional, Any

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
        """
        Initialize the PortfolioAnalysis instance.

        Args:
            public_service (BinancePublicService): Service to access Binance public API.
            private_service (BinancePrivateService): Service to access Binance private API.
            bnb_wallet_db (BNBWalletDBManager): Database manager for BNB wallet.
            db_manager (DBManager): General database manager.
            max_percentage_difference (float): Maximum allowed percentage difference before action is taken.
        """
        self.public_service = public_service
        self.private_service = private_service
        self.bnb_wallet_db = bnb_wallet_db
        self.db_manager = db_manager
        self.max_percentage_difference = max_percentage_difference

    def get_combined_assets(self) -> Dict[str, float]:
        """
        Retrieve and combine assets from Binance account and BNB wallet.

        Returns:
            Dict[str, float]: Dictionary of combined assets with their total quantities.
        """
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

    def process_asset_details(
        self,
        asset_name: str,
        total_quantity: float,
        all_prices: Dict[str, float],
    ) -> Tuple[Optional[Dict[str, float]], float]:
        """
        Process the details of a single asset.

        Args:
            asset_name (str): Name of the asset.
            total_quantity (float): Total quantity of the asset.
            all_prices (Dict[str, float]): Dictionary of current prices from Binance.

        Returns:
            Tuple[Optional[Dict[str, float]], float]: Asset detail dictionary and asset value.
                Returns (None, 0.0) if the symbol is not found in all_prices.
        """
        symbol = f"{asset_name.upper()}USDT"
        if symbol in all_prices:
            current_price = all_prices[symbol]
            asset_value = total_quantity * current_price
            asset_detail = {
                "name": asset_name.upper(),
                "quantity": total_quantity,
                "price": current_price,
                "value": asset_value,
            }
            return asset_detail, asset_value
        else:
            logger.warning(f"Preço para o símbolo {symbol} não encontrado.")
            return None, 0.0

    def calculate_portfolio_details(
        self, combined_assets: Dict[str, float]
    ) -> Tuple[List[Dict[str, float]], float]:
        """
        Calculate portfolio details including asset values and total portfolio value.

        Args:
            combined_assets (Dict[str, float]): Dictionary of combined assets with their total quantities.

        Returns:
            Tuple[List[Dict[str, float]], float]: List of asset details and total portfolio value.
        """
        logger.info("Obtendo preços atuais da Binance...")
        all_prices = self.public_service.get_current_prices()
        portfolio_value = 0.0
        asset_details = []

        logger.info("Calculando detalhes do portfólio...")
        for asset_name, total_quantity in combined_assets.items():
            asset_detail, asset_value = self.process_asset_details(
                asset_name, total_quantity, all_prices
            )
            if asset_detail:
                portfolio_value += asset_value
                asset_details.append(asset_detail)

        if portfolio_value > 0:
            for asset in asset_details:
                asset["percentage"] = (asset["value"] / portfolio_value) * 100
            asset_details.sort(key=lambda x: x["percentage"], reverse=True)

        logger.debug(f"Detalhes dos ativos: {asset_details}")
        return asset_details, portfolio_value

    def analyze_asset_difference(
        self,
        asset: Dict[str, float],
        saved_asset_dict: Dict[str, Dict],
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze the difference between current asset percentage and saved percentage, and determine action.

        Args:
            asset (Dict[str, float]): Current asset details.
            saved_asset_dict (Dict[str, Dict]): Dictionary of saved asset data.

        Returns:
            Optional[Dict[str, Any]]: Recommendation dictionary if an action is determined, otherwise None.
        """
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

                if asset["price"] > saved_asset["average_price"]:
                    sell_quantity = (difference / 100) * asset["quantity"]
                    self.place_sell_order(asset["name"], sell_quantity, asset["price"])
                else:
                    logger.warning(
                        f"Preço de venda de {asset['name']} (${asset['price']:.2f}) "
                        f"é menor ou igual ao preço médio (${saved_asset['average_price']:.2f}). "
                        f"Ordem de venda não enviada."
                    )

            elif difference < -self.max_percentage_difference:
                recommendation["action"] = "buy"

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
            return recommendation
        else:
            logger.warning(f"{asset['name']}: Não encontrado no banco de dados.")
            logger.info(f"Mandando vender todo o ativo: {asset['name']}.")
            self.place_sell_order(
                symbol=asset["name"],
                quantity=asset["quantity"],
                price=asset["price"],
            )

            recommendation = {
                "name": asset["name"],
                "action": "sell_all",
                "message": "Ativo não encontrado no banco de dados. Vendido totalmente.",
            }
            return recommendation

    def analyze_differences(
        self, asset_details: List[Dict[str, float]]
    ) -> List[Dict[str, Any]]:
        """
        Analyze differences between current portfolio and saved portfolio, and generate recommendations.

        Args:
            asset_details (List[Dict[str, float]]): List of current asset details.

        Returns:
            List[Dict[str, Any]]: List of recommendations for each asset.
        """
        logger.info("Analisando diferenças percentuais...")
        saved_assets = self.db_manager.get_all_assets()
        saved_asset_dict = {
            asset_data["asset_name"].lower(): asset_data for asset_data in saved_assets
        }

        recommendations = []

        for asset in asset_details:
            recommendation = self.analyze_asset_difference(asset, saved_asset_dict)
            if recommendation:
                recommendations.append(recommendation)

        return recommendations

    def update_average_price(
        self,
        symbol: str,
        price: float,
        quantity: float,
        average_price: float,
        quantidade_atual_do_ativo: float,
    ) -> float:
        """
        Calculate and update the new average price.

        Args:
            symbol (str): Symbol of the asset.
            price (float): Price at which the order is placed.
            quantity (float): Quantity of the order.
            average_price (float): Current average price.
            quantidade_atual_do_ativo (float): Current quantity of the asset.

        Returns:
            float: New average price.
        """
        calculator = AveragePriceCalculator(self.db_manager)
        new_average_price = calculator.calculate_new_average_price(
            asset_name=symbol,
            order_price=price,
            order_quantity=quantity,
            average_price=average_price,
            quantidade_atual_do_ativo=quantidade_atual_do_ativo,
        )
        logger.info(f"Preço médio atualizado para {symbol}: ${new_average_price:.2f}.")
        return new_average_price

    def place_buy_order(
        self,
        symbol: str,
        quantity: float,
        price: float,
        average_price: float,
        quantidade_atual_do_ativo: float,
    ):
        """
        Update average price before buying and send the buy order.

        Args:
            symbol (str): Symbol of the asset.
            quantity (float): Quantity to buy.
            price (float): Price to buy at.
            average_price (float): Current average price of the asset.
            quantidade_atual_do_ativo (float): Current quantity of the asset.
        """
        logger.info(f"Atualizando preço médio antes de comprar {symbol}.")
        try:
            self.update_average_price(
                symbol, price, quantity, average_price, quantidade_atual_do_ativo
            )
            order_response = self.private_service.place_buy_order(
                symbol, quantity, price
            )
            logger.info(f"Ordem de compra executada: {order_response}")
        except Exception as e:
            logger.error(f"Erro ao executar ordem de compra: {e}")

    def place_sell_order(self, symbol: str, quantity: float, price: float):
        """
        Send a sell order using the private service.

        Args:
            symbol (str): Symbol of the asset.
            quantity (float): Quantity to sell.
            price (float): Price to sell at.
        """
        logger.info(f"Preparando ordem de venda para {symbol}.")
        try:
            order_response = self.private_service.place_sell_order(
                symbol, quantity, price
            )
            logger.info(f"Ordem de venda executada: {order_response}")
        except Exception as e:
            logger.error(f"Erro ao executar ordem de venda: {e}")

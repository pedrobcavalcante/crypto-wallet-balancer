from typing import List, Tuple, Dict
import logging
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
        self.public_service: BinancePublicService = public_service
        self.private_service: BinancePrivateService = private_service
        self.bnb_wallet_db: BNBWalletDBManager = bnb_wallet_db
        self.db_manager: DBManager = db_manager
        self.max_percentage_difference: float = max_percentage_difference

    def get_combined_assets(self) -> Dict[str, float]:
        binance_assets: Dict[str, float] = self._get_binance_assets()
        bnb_assets: Dict[str, float] = self._get_bnb_wallet_assets()

        combined_assets: Dict[str, float] = {**binance_assets, **bnb_assets}
        self._combine_asset_quantities(bnb_assets, combined_assets)

        logger.debug(f"Ativos combinados: {combined_assets}")
        return combined_assets

    def _get_binance_assets(self) -> Dict[str, float]:
        logger.info("Buscando ativos na Binance...")
        binance_assets: List[Dict[str, str]] = self.private_service.get_account_assets()
        return {
            asset["asset"].lower(): float(asset["free"]) for asset in binance_assets
        }

    def _get_bnb_wallet_assets(self) -> Dict[str, float]:
        logger.info("Buscando ativos na carteira BNB...")
        bnb_assets: List[Dict[str, str]] = self.bnb_wallet_db.get_all_token_balances()
        return {
            token["token_name"].lower(): float(token["quantity"])
            for token in bnb_assets
        }

    def _combine_asset_quantities(
        self, bnb_assets: Dict[str, float], combined_assets: Dict[str, float]
    ):
        for token_name, quantity in bnb_assets.items():
            combined_assets[token_name] = combined_assets.get(token_name, 0) + quantity

    def calculate_portfolio_details(
        self, combined_assets: Dict[str, float]
    ) -> Tuple[List[Dict[str, float]], float]:
        all_prices: Dict[str, float] = self.public_service.get_current_prices()
        portfolio_value: float = 0.0
        asset_details: List[Dict[str, float]] = []

        logger.info("Calculando detalhes do portfólio...")
        for asset_name, total_quantity in combined_assets.items():
            self._add_asset_details(
                asset_name, total_quantity, all_prices, asset_details
            )

        if portfolio_value > 0:
            self._calculate_percentage(asset_details, portfolio_value)

        logger.debug(f"Detalhes dos ativos: {asset_details}")
        return asset_details, portfolio_value

    def _add_asset_details(
        self,
        asset_name: str,
        total_quantity: float,
        all_prices: Dict[str, float],
        asset_details: List[Dict[str, float]],
    ):
        symbol: str = f"{asset_name.upper()}USDT"
        if symbol in all_prices:
            current_price: float = all_prices[symbol]
            asset_value: float = total_quantity * current_price

            asset_details.append(
                {
                    "name": asset_name.upper(),
                    "quantity": total_quantity,
                    "price": current_price,
                    "value": asset_value,
                }
            )

    def _calculate_percentage(
        self, asset_details: List[Dict[str, float]], portfolio_value: float
    ):
        for asset in asset_details:
            asset["percentage"] = (asset["value"] / portfolio_value) * 100
        asset_details.sort(key=lambda x: x["percentage"], reverse=True)

    def analyze_differences(
        self, asset_details: List[Dict[str, float]]
    ) -> List[Dict[str, float]]:
        saved_assets: List[Dict[str, float]] = self.db_manager.get_all_assets()
        saved_asset_dict: Dict[str, Dict[str, float]] = {
            asset_data["asset_name"].lower(): asset_data for asset_data in saved_assets
        }

        recommendations: List[Dict[str, float]] = []

        for asset in asset_details:
            recommendations += self._analyze_asset_difference(asset, saved_asset_dict)

        return recommendations

    def _analyze_asset_difference(
        self, asset: Dict[str, float], saved_asset_dict: Dict[str, Dict[str, float]]
    ):
        asset_name: str = asset["name"].lower()
        recommendations: List[Dict[str, float]] = []

        if asset_name in saved_asset_dict:
            recommendations.append(
                self._compare_asset_with_saved(asset, saved_asset_dict[asset_name])
            )
        else:
            recommendations.append(self._handle_asset_not_found(asset))

        return recommendations

    def _compare_asset_with_saved(
        self, asset: Dict[str, float], saved_asset: Dict[str, float]
    ):
        difference: float = self._calculate_difference(asset, saved_asset)
        recommendation: Dict[str, float] = self._create_recommendation(
            asset, saved_asset, difference
        )

        if recommendation.get("action"):
            self._handle_recommendation_action(
                recommendation, asset, saved_asset, difference
            )

        logger.debug(f"Recomendação para {asset['name']}: {recommendation}")
        return recommendation

    def _calculate_difference(
        self, asset: Dict[str, float], saved_asset: Dict[str, float]
    ):
        saved_percentage: float = saved_asset["percentage"]
        current_percentage: float = asset["percentage"]
        return current_percentage - saved_percentage

    def _create_recommendation(
        self, asset: Dict[str, float], saved_asset: Dict[str, float], difference: float
    ):
        recommendation: Dict[str, float] = {
            "name": asset["name"],
            "current_percentage": asset["percentage"],
            "saved_percentage": saved_asset["percentage"],
            "difference": difference,
        }

        if difference > self.max_percentage_difference:
            recommendation["action"] = "sell"
        elif difference < -self.max_percentage_difference:
            recommendation["action"] = "buy"
        else:
            recommendation["action"] = "hold"

        return recommendation

    def _handle_recommendation_action(
        self,
        recommendation: Dict[str, float],
        asset: Dict[str, float],
        saved_asset: Dict[str, float],
        difference: float,
    ):
        if recommendation["action"] == "sell":
            self._handle_sell_action(asset, saved_asset, difference)
        elif recommendation["action"] == "buy":
            self._handle_buy_action(asset, saved_asset, difference)

    def _handle_sell_action(
        self, asset: Dict[str, float], saved_asset: Dict[str, float], difference: float
    ):
        if asset["price"] > saved_asset["average_price"]:
            sell_quantity: float = (difference / 100) * asset["quantity"]
            self._place_sell_order(asset["name"], sell_quantity, asset["price"])
        else:
            logger.warning(
                f"Preço de venda de {asset['name']} (${asset['price']:.2f}) é menor ou igual ao preço médio (${saved_asset['average_price']:.2f}). Ordem de venda não enviada."
            )

    def _handle_buy_action(
        self, asset: Dict[str, float], saved_asset: Dict[str, float], difference: float
    ):
        buy_quantity: float = (abs(difference) / 100) * saved_asset["points"]
        self._place_buy_order(
            asset["name"],
            buy_quantity,
            asset["price"],
            saved_asset["average_price"],
            asset["quantity"],
        )

    def _handle_asset_not_found(self, asset: Dict[str, float]):
        logger.warning(f"{asset['name']}: Não encontrado no banco de dados.")
        logger.info(f"Mandando vender todo o ativo: {asset['name']}.")
        self._place_sell_order(
            symbol=asset["name"],
            quantity=asset["quantity"],
            price=asset["price"],
        )

        return {
            "name": asset["name"],
            "action": "sell_all",
            "message": "Ativo não encontrado no banco de dados. Vendido totalmente.",
        }

    def _place_buy_order(
        self,
        symbol: str,
        quantity: float,
        price: float,
        average_price: float,
        quantidade_atual_do_ativo: float,
    ):
        logger.info(f"Atualizando preço médio antes de comprar {symbol}.")
        calculator = AveragePriceCalculator(self.db_manager)

        try:
            new_average_price: float = calculator.calculate_new_average_price(
                asset_name=symbol,
                order_price=price,
                order_quantity=quantity,
                average_price=average_price,
                quantidade_atual_do_ativo=quantidade_atual_do_ativo,
            )
            logger.info(
                f"Preço médio atualizado para {symbol}: ${new_average_price:.2f}."
            )
            order_response: Dict[str, str] = self.private_service.place_buy_order(
                symbol, quantity, price
            )
            logger.info(f"Ordem de compra executada: {order_response}")
        except Exception as e:
            logger.error(f"Erro ao executar ordem de compra: {e}")

    def _place_sell_order(self, symbol: str, quantity: float, price: float):
        logger.info(f"Preparando ordem de venda para {symbol}.")
        try:
            order_response: Dict[str, str] = self.private_service.place_sell_order(
                symbol, quantity, price
            )
            logger.info(f"Ordem de venda executada: {order_response}")
        except Exception as e:
            logger.error(f"Erro ao executar ordem de venda: {e}")

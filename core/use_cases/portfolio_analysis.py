import logging
from typing import Any, Dict, List

from core.database.crypto_assets_manager import CryptoAssetsManager
from core.services.binance_public_service import BinancePublicService
from core.services.binance_private_service import BinancePrivateService


from core.use_cases.asset_analyzer import AssetAnalyzer
from core.use_cases.portfolio_manager import PortfolioManager
from core.use_cases.order_executor import OrderExecutor

logger = logging.getLogger(__name__)


class PortfolioAnalysis:
    def __init__(
        self,
        public_service: BinancePublicService,
        private_service: BinancePrivateService,
        db_manager: CryptoAssetsManager,
        max_percentage_difference: float,
    ):
        self.portfolio_manager = PortfolioManager(public_service, private_service, db_manager)
        self.asset_analyzer = AssetAnalyzer(db_manager, max_percentage_difference)
        self.order_executor = OrderExecutor(private_service)
        self.public_service = public_service

    def analyze_portfolio(self):
        # Passo 1: Obter ativos combinados
        combined_assets = self.portfolio_manager.get_combined_assets()

        # Passo 2: Calcular detalhes do portfólio
        asset_details, portfolio_value = (
            self.portfolio_manager.calculate_portfolio_details(combined_assets)
        )

        # Passo 3: Obter informações de troca
        logger.info("Obtendo informações de troca da Binance...")
        exchange_info = self.public_service.get_exchange_info()

        # Passo 4: Analisar diferenças e obter recomendações
        recommendations = self.asset_analyzer.analyze_differences(
            asset_details, portfolio_value
        )

        # Passo 5: Executar ordens com base nas recomendações
        self.execute_recommendations(recommendations, exchange_info)

    def execute_recommendations(
        self, recommendations: List[Dict[str, Any]], exchange_info: Dict[str, Any]
    ):
        for recommendation in recommendations:
            action = recommendation.get("action")
            symbol_base = recommendation["name"]
            symbol = symbol_base
            if not symbol.lower().endswith("usdt"):
                symbol += "USDT"
            price = recommendation.get("price")
            quantity = recommendation.get("quantity")

            if action in ["buy", "sell"]:
                self.order_executor.place_order(
                    action=action,
                    symbol=symbol,
                    quantity=quantity,
                    price=price,
                    exchange_info=exchange_info,
                )
            elif action == "sell_all":
                self.order_executor.place_order(
                    action="sell",
                    symbol=symbol,
                    quantity=quantity,
                    price=price,
                    exchange_info=exchange_info,
                )
                logger.info(f"Executado venda total para {symbol_base}.")
            elif action == "hold":
                logger.info(f"Mantendo posição para {symbol_base}.")
            else:
                logger.warning(f"Ação desconhecida para {symbol_base}: {action}")

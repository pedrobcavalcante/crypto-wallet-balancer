import logging
from typing import Dict, List, Tuple

from core.database.crypto_assets_manager import CryptoAssetsManager
from core.services.binance_private_service import BinancePrivateService
from core.services.binance_public_service import BinancePublicService

logger = logging.getLogger(__name__)


class PortfolioManager:
    def __init__(
        self,
        public_service: BinancePublicService,
        private_service: BinancePrivateService,
        crypto_assets_manager: CryptoAssetsManager,
    ):
        self.public_service = public_service
        self.private_service = private_service
        self.crypto_assets_manager = crypto_assets_manager

    def get_combined_assets(self) -> Dict[str, float]:
        logger.info("Buscando ativos na Binance...")
        binance_assets = self.private_service.get_account_assets()
        binance_asset_dict = {
            asset["asset"].lower(): float(asset["free"]) for asset in binance_assets
        }

        logger.info("Buscando ativos na carteira BNB...")
        bnb_assets = self.crypto_assets_manager.get_all_assets()
        bnb_asset_dict = {
            token["crypto"].lower(): float(token["total_carteira"])
            for token in bnb_assets
            if token["total_carteira"] is not None
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
                asset_detail = {
                    "name": asset_name.upper(),
                    "quantity": total_quantity,
                    "price": current_price,
                    "value": asset_value,
                }
                portfolio_value += asset_value
                asset_details.append(asset_detail)
            else:
                logger.warning(f"Preço para o símbolo {symbol} não encontrado.")

        if portfolio_value > 0:
            for asset in asset_details:
                asset["percentual"] = (asset["value"] / portfolio_value) * 100
            asset_details.sort(key=lambda x: x["percentual"], reverse=True)

        logger.debug(f"Detalhes dos ativos: {asset_details}")
        return asset_details, portfolio_value

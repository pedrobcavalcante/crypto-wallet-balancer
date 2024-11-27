import logging
from typing import List, Dict, Any, Optional

from config import get_config
from core.database.crypto_assets_manager import CryptoAssetsManager


logger = logging.getLogger(__name__)


class AssetAnalyzer:
    def __init__(
        self,
        crypto_assets_manager: CryptoAssetsManager,
        max_percentage_difference: float,
    ):
        self.db_manager = crypto_assets_manager
        self.max_percentage_difference = max_percentage_difference

    def analyze_differences(
        self,
        asset_details: List[Dict[str, float]],
        portfolio_value: float,
    ) -> List[Dict[str, Any]]:
        logger.info("Analisando diferenças percentuais...")
        saved_assets = self.db_manager.get_all_assets()
        saved_asset_dict = {
            asset_data["crypto"].lower(): asset_data for asset_data in saved_assets
        }

        recommendations = []

        for asset in asset_details:
            recommendation = self.analyze_asset_difference_percentual(
                asset, saved_asset_dict, portfolio_value
            )
            if recommendation:
                recommendations.append(recommendation)

        return recommendations

    def analyze_asset_difference_percentual(
        self,
        asset: Dict[str, float],
        saved_asset_dict: Dict[str, Dict],
        portfolio_value: float,
    ) -> Optional[Dict[str, Any]]:
        asset_name = asset["name"].lower()

        if asset_name in saved_asset_dict:
            saved_asset = saved_asset_dict[asset_name]
            recommendation = self._create_recommendation(asset, saved_asset)

            difference = recommendation["difference"]
            current_quantity = asset["quantity"]
            current_price = asset["price"]
            difference_total = recommendation["difference_total"]
            difference_in_dolar = difference_total * current_price
            min_order_value = get_config()["min_order_value"]
            recommendation["preco_medio"] = saved_asset["preco_medio"]
            if abs(difference_in_dolar) < min_order_value:
                recommendation["action"] = "hold"
            elif (
                difference > self.max_percentage_difference
                and current_price > saved_asset["preco_medio"]
            ):
                target_value = (saved_asset["percentual"] / 100) * portfolio_value
                target_quantity = target_value / current_price
                quantity_to_sell = current_quantity - target_quantity
                recommendation["action"] = "sell"
                recommendation["quantity"] = quantity_to_sell

            elif difference < -self.max_percentage_difference:
                target_value = (saved_asset["percentual"] / 100) * portfolio_value
                target_quantity = target_value / current_price
                quantity_to_buy = target_quantity - current_quantity
                recommendation["action"] = "buy"
                recommendation["quantity"] = quantity_to_buy

            else:
                recommendation["action"] = "hold"
            recommendation["price"] = current_price

            logger.debug(f"Recomendação para {asset['name']}: {recommendation}")
            return recommendation

        logger.warning(
            f"{asset['name']}: Não encontrado no banco de dados. Recomendado vender tudo."
        )
        recommendation = {
            "name": asset["name"],
            "action": "sell_all",
            "quantity": asset["quantity"],
            "price": asset["price"],
            "message": "Ativo não encontrado no portfólio salvo. Recomendado vender tudo.",
        }
        return recommendation

    def analyze_asset_difference_total(
        self,
        asset: Dict[str, float],
        saved_asset_dict: Dict[str, Dict],
    ) -> Optional[Dict[str, Any]]:
        asset_name = asset["name"].lower()

        if asset_name in saved_asset_dict:
            saved_asset = saved_asset_dict[asset_name]
            recommendation = self._create_recommendation(asset, saved_asset)

            difference_total = recommendation["difference_total"]
            current_price = asset["price"]
            difference_in_dolar = difference_total * current_price
            min_order_value = get_config()["min_order_value"]

            if abs(difference_in_dolar) < min_order_value:
                recommendation["action"] = "hold"
            elif difference_total > 0:
                recommendation["action"] = "sell"
                recommendation["quantity"] = difference_total
            elif difference_total < 0:
                recommendation["action"] = "buy"
                recommendation["quantity"] = abs(difference_total)
            else:
                recommendation["action"] = "hold"
            recommendation["price"] = current_price
            logger.debug(f"Recomendação para {asset['name']}: {recommendation}")
            return recommendation

        logger.warning(
            f"{asset['name']}: Não encontrado no banco de dados. Recomendado vender tudo."
        )
        recommendation = {
            "name": asset["name"],
            "action": "sell_all",
            "quantity": asset["quantity"],
            "price": asset["price"],
            "message": "Ativo não encontrado no portfólio salvo. Recomendado vender tudo.",
        }
        return recommendation

    def _create_recommendation(
        self, asset: Dict[str, float], saved_asset: Dict[str, Any]
    ) -> Dict[str, Any]:
        saved_percentage = saved_asset["percentual"]
        current_percentage = asset["percentual"]
        difference = current_percentage - saved_percentage
        meta_total = saved_asset["meta_moeda"]
        valor_atual = asset["quantity"]
        difference_total = meta_total - valor_atual
        return {
            "name": asset["name"],
            "current_percentage": current_percentage,
            "saved_percentage": saved_percentage,
            "difference": difference,
            "difference_total": difference_total,
        }

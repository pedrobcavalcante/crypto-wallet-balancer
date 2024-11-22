import logging
from typing import List, Dict, Any, Optional

from core.database.db_manager import DBManager

logger = logging.getLogger(__name__)


class AssetAnalyzer:
    def __init__(
        self,
        db_manager: DBManager,
        max_percentage_difference: float,
    ):
        self.db_manager = db_manager
        self.max_percentage_difference = max_percentage_difference

    def analyze_differences(
        self,
        asset_details: List[Dict[str, float]],
        portfolio_value: float,
    ) -> List[Dict[str, Any]]:
        logger.info("Analisando diferenças percentuais...")
        saved_assets = self.db_manager.get_all_assets()
        saved_asset_dict = {
            asset_data["asset_name"].lower(): asset_data for asset_data in saved_assets
        }

        recommendations = []

        for asset in asset_details:
            recommendation = self.analyze_asset_difference(
                asset, saved_asset_dict, portfolio_value
            )
            if recommendation:
                recommendations.append(recommendation)

        return recommendations

    def analyze_asset_difference(
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

            if difference > self.max_percentage_difference:
                target_value = (saved_asset["percentage"] / 100) * portfolio_value
                target_quantity = target_value / current_price
                quantity_to_sell = current_quantity - target_quantity
                recommendation["action"] = "sell"
                recommendation["quantity"] = quantity_to_sell
                recommendation["price"] = current_price
            elif difference < -self.max_percentage_difference:
                target_value = (saved_asset["percentage"] / 100) * portfolio_value
                target_quantity = target_value / current_price
                quantity_to_buy = target_quantity - current_quantity
                recommendation["action"] = "buy"
                recommendation["quantity"] = quantity_to_buy
                recommendation["price"] = current_price
            else:
                recommendation["action"] = "hold"

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
        saved_percentage = saved_asset["percentage"]
        current_percentage = asset["percentage"]
        difference = current_percentage - saved_percentage

        return {
            "name": asset["name"],
            "current_percentage": current_percentage,
            "saved_percentage": saved_percentage,
            "difference": difference,
        }

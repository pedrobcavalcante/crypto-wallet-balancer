import logging

from core.database.db_manager import DBManager

logger = logging.getLogger(__name__)


class AveragePriceCalculator:
    def __init__(self, db_manager):
        self.db_manager: DBManager = db_manager

    def calculate_new_average_price(
        self,
        asset_name: str,
        order_price: float,
        order_quantity: float,
        quantidade_atual_do_ativo: float,
        average_price: float,
    ):
        """
        Calcula e atualiza o preço médio de um ativo antes de uma nova compra.
        """
        logger.info(f"Calculando novo preço médio para {asset_name}...")

        # Obtém a quantidade atual do ativo na conta Binance

        # Calcula o novo preço médio
        total_cost_current = quantidade_atual_do_ativo * average_price
        total_cost_new = order_price * order_quantity
        new_average_price = (total_cost_current + total_cost_new) / (
            quantidade_atual_do_ativo + order_quantity
        )

        # Salva o novo preço médio no banco de dados

        self.db_manager.update_average_price(asset_name, new_average_price)

        logger.info(
            f"Novo preço médio calculado para {asset_name}: ${new_average_price:.2f}"
        )

        return new_average_price

import logging
from decimal import Decimal
import math
from typing import Dict, Any, Optional

from config import get_config
from core.services.binance_private_service import BinancePrivateService

logger = logging.getLogger(__name__)


class OrderExecutor:
    def __init__(self, private_service: BinancePrivateService):
        self.private_service = private_service

    def place_order(
        self,
        action: str,
        symbol: str,
        quantity: float,
        price: float,
        exchange_info: Dict[str, Any],
    ):
        try:
            quantity_adjusted = self._adjust_price(price, quantity, symbol, action)
            if not quantity_adjusted:
                return
            # Obter filtros
            filters = self._get_filters(symbol, exchange_info)
            if not filters:
                return
            # Formatar quantidade e preço
            formatted_quantity = self._format_quantity(quantity_adjusted, filters["step_size"])

            # Verificar quantidade válida
            if float(formatted_quantity) <= 0:
                logger.error(
                    f"Quantidade ajustada inválida para {symbol}: {formatted_quantity}"
                )
                return

            # Enviar ordem
            self._send_order(action, symbol, formatted_quantity, price)

        except Exception as e:
            logger.error(f"Erro ao executar ordem de {action} para {symbol}: {e}")

    def _adjust_price(
        self, price: float, quantity: float, symbol: str, action: str
    ) -> Optional[float]:
        min_order_value = get_config()["min_order_value"]
        if price * quantity < min_order_value:
            logger.info(
                f"Ordem de {action} para {symbol} com valor total de {price * quantity:.2f} USDT "
                f"é menor que o valor mínimo de {min_order_value:.2f} USDT. "
                f"Ordem não foi executada."
            )
        else:
            return min_order_value / price

    def _send_order(self, action: str, symbol: str, quantity: str, price: str):
        logger.info(
            f"Enviando ordem de {action}: {symbol} - Quantidade: {quantity}, Preço: {price}"
        )
        if action == "buy":
            response = self.private_service.place_buy_order(
                symbol, float(quantity), price
            )
        elif action == "sell":
            response = self.private_service.place_sell_order(
                symbol, float(quantity), price
            )
        else:
            logger.error(f"Ação desconhecida: {action}")
            return
        logger.info(f"Ordem executada: {response}")

    def _get_filter(
        self, symbol: str, exchange_info: Dict[str, Any], filter_type: str
    ) -> Dict[str, Any]:
        for market in exchange_info["symbols"]:
            if market["symbol"] == symbol:
                for f in market["filters"]:
                    if f["filterType"] == filter_type:
                        return f
        raise ValueError(
            f"Filtro {filter_type} não encontrado para o símbolo: {symbol}"
        )

    def _format_quantity(self, quantity: float, step_size: float) -> str:
        """
        Formata a quantidade para uma string com a precisão correta.
        """
        precision = abs(Decimal(str(step_size)).as_tuple().exponent)
        formatted_quantity = f"{quantity:.{precision}f}"
        return (
            formatted_quantity.rstrip("0").rstrip(".")
            if "." in formatted_quantity
            else formatted_quantity
        )

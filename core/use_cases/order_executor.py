import logging
from decimal import Decimal
from typing import Dict, Any

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
            lot_size_filter = self._get_lot_size_filter(symbol, exchange_info)
            step_size = float(lot_size_filter["stepSize"])

            formatted_quantity = self._format_quantity(quantity, step_size)

            logger.info(
                f"Enviando ordem de {action}: {symbol} - Quantidade: {formatted_quantity}, Preço: {price}"
            )

            if action == "buy":
                order_response = self.private_service.place_buy_order(
                    symbol, float(formatted_quantity), price
                )
            elif action == "sell":
                order_response = self.private_service.place_sell_order(
                    symbol, float(formatted_quantity), price
                )
            else:
                logger.error(f"Ação desconhecida: {action}")
                return

            logger.info(f"Ordem executada: {order_response}")

        except Exception as e:
            logger.error(f"Erro ao executar ordem de {action} para {symbol}: {e}")

    def _get_lot_size_filter(
        self, symbol: str, exchange_info: Dict[str, Any]
    ) -> Dict[str, str]:
        symbol_pair = symbol + "USDT"
        for market in exchange_info["symbols"]:
            if market["symbol"] == symbol_pair:
                for filter_data in market["filters"]:
                    if filter_data["filterType"] == "LOT_SIZE":
                        return filter_data
        raise ValueError(f"Filtro LOT_SIZE não encontrado para o símbolo: {symbol}")

    def _format_quantity(self, quantity: float, step_size: float) -> str:
        precision = abs(Decimal(str(step_size)).as_tuple().exponent)
        formatted_quantity = f"{quantity:.{precision}f}"
        return formatted_quantity.rstrip("0").rstrip(".")

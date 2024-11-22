import logging
from decimal import Decimal
import math
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
            # Obter filtros necessários
            lot_size_filter = self._get_filter(symbol, exchange_info, "LOT_SIZE")
            notional_filter = self._get_filter(symbol, exchange_info, "NOTIONAL")
            price_filter = self._get_filter(
                symbol, exchange_info, "PRICE_FILTER"
            )  # Novo

            # Calcular quantidades mínimas
            min_qty = float(lot_size_filter["minQty"])
            step_size = float(lot_size_filter["stepSize"])
            min_notional = float(notional_filter["minNotional"])
            max_notional = float(notional_filter.get("maxNotional", float("inf")))
            tick_size = float(price_filter["tickSize"])  # Novo

            # Quantidade mínima baseada em NOTIONAL
            min_qty_notional = min_notional / price

            # Escolher a quantidade que resulta em maior valor em USDT
            if (min_qty_notional * price) > (min_qty * price):
                chosen_quantity = min_qty_notional
            else:
                chosen_quantity = min_qty

            # Ajustar a quantidade para respeitar o step_size
            adjusted_quantity = self._adjust_quantity(chosen_quantity, step_size)

            # Valor notional da ordem
            notional_value = adjusted_quantity * price

            # Verificar se o valor notional está abaixo de $5
            if notional_value < 5:
                logger.info(
                    f"Valor notional da ordem ({notional_value:.2f}) é menor que $5. Ajustando para $5."
                )
                # Calcular nova quantidade para notional_value = $5
                adjusted_quantity = 5 / price
                # Ajustar a quantidade para respeitar o step_size
                adjusted_quantity = self._adjust_quantity(adjusted_quantity, step_size)
                # Recalcular o valor notional
                notional_value = adjusted_quantity * price
                logger.info(
                    f"Nova quantidade ajustada: {adjusted_quantity}, Novo valor notional: {notional_value:.2f}"
                )

            # Verificar se o notional_value está dentro dos limites permitidos
            if notional_value < min_notional:
                logger.error(
                    f"Valor notional da ordem ({notional_value:.2f}) abaixo do mínimo permitido para {symbol}: {min_notional}"
                )
                return
            if notional_value > max_notional:
                logger.error(
                    f"Valor notional da ordem ({notional_value:.2f}) acima do máximo permitido para {symbol}: {max_notional}"
                )
                return

            # Formatar a quantidade para a precisão correta
            formatted_quantity = self._format_quantity(adjusted_quantity, step_size)

            # Formatar o preço para a precisão correta
            formatted_price = self._format_price(price, tick_size)  # Novo

            # Verificar se a quantidade ajustada é válida
            if float(formatted_quantity) <= 0:
                logger.error(
                    f"Quantidade ajustada inválida para {symbol}: {formatted_quantity}"
                )
                return

            logger.info(
                f"Enviando ordem de {action}: {symbol} - Quantidade: {formatted_quantity}, Preço: {formatted_price}"
            )

            if action == "buy":
                order_response = self.private_service.place_buy_order(
                    symbol,
                    float(formatted_quantity),
                    formatted_price,  # Usando o preço formatado
                )
            elif action == "sell":
                order_response = self.private_service.place_sell_order(
                    symbol,
                    float(formatted_quantity),
                    formatted_price,  # Usando o preço formatado
                )
            else:
                logger.error(f"Ação desconhecida: {action}")
                return

            logger.info(f"Ordem executada: {order_response}")

        except Exception as e:
            logger.error(f"Erro ao executar ordem de {action} para {symbol}: {e}")

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

    def _adjust_quantity(self, quantity: float, step_size: float) -> float:
        """
        Ajusta a quantidade para que seja múltipla de step_size.
        """
        precision = int(round(-math.log(step_size, 10), 0))
        adjusted_quantity = math.floor(quantity / step_size) * step_size
        adjusted_quantity = round(adjusted_quantity, precision)
        return adjusted_quantity

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

    def _format_price(self, price: float, tick_size: float) -> str:
        """
        Formata o preço para uma string com a precisão correta, evitando notação científica.
        """
        precision = abs(Decimal(str(tick_size)).as_tuple().exponent)
        formatted_price = f"{price:.{precision}f}"
        return (
            formatted_price.rstrip("0").rstrip(".")
            if "." in formatted_price
            else formatted_price
        )

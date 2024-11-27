import logging
from decimal import Decimal
from typing import Dict, Any, Optional

from config import get_config
from core.database.crypto_assets_manager import CryptoAssetsManager
from core.services.binance_private_service import BinancePrivateService
from core.use_cases.update_average_price import atualizar_preco_medio

logger = logging.getLogger(__name__)


class OrderExecutor:
    def __init__(self, private_service: BinancePrivateService, crypto_assets_manager: CryptoAssetsManager = CryptoAssetsManager()):
        self.private_service = private_service  
        self.crypto_assets_manager = crypto_assets_manager

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
            formatted_quantity = self._format_quantity(
                quantity_adjusted, filters["step_size"]
            )

            # Verificar quantidade válida
            if float(formatted_quantity) <= 0:
                logger.error(
                    f"Quantidade ajustada inválida para {symbol}: {formatted_quantity}"
                )
                return

            # Enviar ordem
            self._send_order(action, symbol, formatted_quantity, price)
            if action == "buy":
                atualizar_preco_medio(
                    symbol.replace("USDT", ""), formatted_quantity, price, self.crypto_assets_manager
                )
        except Exception as e:
            logger.error(f"Erro ao executar ordem de {action} para {symbol}: {e}")

    def _get_filters(
        self, symbol: str, exchange_info: Dict[str, Any]
    ) -> Dict[str, float]:
        try:
            return {
                "min_qty": float(
                    self._get_filter(symbol, exchange_info, "LOT_SIZE")["minQty"]
                ),
                "step_size": float(
                    self._get_filter(symbol, exchange_info, "LOT_SIZE")["stepSize"]
                ),
                "min_notional": float(
                    self._get_filter(symbol, exchange_info, "NOTIONAL")["minNotional"]
                ),
                "max_notional": float(
                    self._get_filter(symbol, exchange_info, "NOTIONAL").get(
                        "maxNotional", float("inf")
                    )
                ),
                "tick_size": float(
                    self._get_filter(symbol, exchange_info, "PRICE_FILTER")["tickSize"]
                ),
            }
        except KeyError as e:
            logger.error(f"Erro ao obter filtros para {symbol}: {e}")
            return None

    def _adjust_price(
        self, price: float, quantity: float, symbol: str, action: str
    ) -> Optional[float]:
        min_order_value = get_config()["min_order_value"]
        max_order_value = get_config()["max_order_value"]
        if price * quantity < min_order_value:
            logger.info(
                f"Ordem de {action} para {symbol} com valor total de {price * quantity:.2f} USDT "
                f"é menor que o valor mínimo de {min_order_value:.2f} USDT. "
                f"Ordem não foi executada."
            )
        else:
            if price * quantity > max_order_value:
                return max_order_value / price
            else:
                return quantity

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

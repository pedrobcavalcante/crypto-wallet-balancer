from core.services.telegram_notifier import TelegramNotifier
from src.config import get_config
from .binance_base_service import BinanceBaseService
from core.utils.crypto_utils import create_signature


class BinancePrivateService(BinanceBaseService):
    def __init__(self):
        super().__init__()
        config = get_config()
        self.telegram_notifier = TelegramNotifier(config["telegram_bot_token"])
        self.api_key = config["api_key"]
        self.api_secret = config["api_secret"]
        if not self.api_key or not self.api_secret:
            raise ValueError("API Key e Secret não foram encontradas.")

    def _get_headers(self):
        """
        Retorna os cabeçalhos para autenticação.
        """
        return {"X-MBX-APIKEY": self.api_key}

    def _make_request(self, endpoint, params=None, request_type: str = "GET"):
        """
        Realiza uma requisição autenticada para a API da Binance.
        """
        headers = self._get_headers()
        params = params or {}

        # Adiciona timestamp e recvWindow
        params["timestamp"] = self._get_server_time()
        params["recvWindow"] = 5000

        # Adiciona a assinatura
        params["signature"] = create_signature(params, self.api_secret)

        # Faz a requisição usando o método da classe base
        return super()._make_request(
            endpoint, request_type=request_type, params=params, headers=headers
        )

    def get_account_assets(self):
        """
        Obtém os ativos da conta na Binance com quantidade livre e em uso.
        """
        try:
            endpoint = "/api/v3/account"
            account_info = self._make_request(endpoint)
            if account_info:
                return [
                    {
                        "asset": asset["asset"],
                        "free": float(asset["free"]),
                        "locked": float(asset["locked"]),
                    }
                    for asset in account_info["balances"]
                    if float(asset["free"]) > 0 or float(asset["locked"]) > 0
                ]
            return []
        except Exception as e:
            raise Exception(f"Erro ao obter ativos da conta: {e}") from e

    def _send_order(self, symbol, side, quantity, price):
        """
        Método genérico para enviar ordens de teste (compra ou venda) para a Binance.
        """
        # Parâmetros comuns para a ordem de teste
        params = {
            "symbol": symbol + "USDT",
            "side": side,
            "type": "LIMIT",
            "timeInForce": "GTC",  # Ordem válida até cancelamento
            "quantity": quantity,
            "price": price,
        }

        try:
            # Envia a ordem de teste via requisição HTTP
            endpoint = "/api/v3/order/test"
            self._make_request(endpoint, params, request_type="POST")

            print(f"Ordem de teste {side.lower()} enviada com sucesso!")

            # Envia a notificação via Telegram
            message = f"Ordem de {side.lower()} simulada enviada: {symbol} - {quantity} - {price}"
            self.telegram_notifier.send_message(message, "65244254")

        except Exception as e:
            print(f"Erro ao enviar ordem de teste: {e}")

    def place_buy_order(self, symbol: str, quantity: float, price: float):
        """
        Simula uma ordem de compra utilizando a API da Binance.
        """
        if not symbol or not quantity or not price:
            raise ValueError("Parâmetros inválidos para a ordem de compra.")

        print("\n--- Ordem de Compra ---")
        print(f"Ativo: {symbol}")
        print(f"Quantidade: {quantity}")
        print(f"Preço: {price}")
        print("Tipo de Ordem: LIMIT (Simulada)")
        print("----------------------\n")

        # Chama o método genérico para enviar a ordem de compra
        self._send_order(symbol, "BUY", round(quantity, 8), price)

    def place_sell_order(self, symbol: str, quantity: float, price: float):
        """
        Simula uma ordem de venda utilizando a API da Binance.
        """
        if not symbol or not quantity or not price:
            raise ValueError("Parâmetros inválidos para a ordem de venda.")

        print("\n--- Ordem de Venda ---")
        print(f"Ativo: {symbol}")
        print(f"Quantidade: {quantity}")
        print(f"Preço: {price}")
        print("Tipo de Ordem: LIMIT (Simulada)")
        print("----------------------\n")

        # Chama o método genérico para enviar a ordem de venda
        self._send_order(symbol, "SELL", round(quantity, 8), price)

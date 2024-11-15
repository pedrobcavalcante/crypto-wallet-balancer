from src.config import get_config
from .binance_base_service import BinanceBaseService
from core.utils.crypto_utils import create_signature


class BinancePrivateService(BinanceBaseService):
    def __init__(self):
        super().__init__()
        config = get_config()
        self.api_key = config["api_key"]
        self.api_secret = config["api_secret"]
        if not self.api_key or not self.api_secret:
            raise ValueError("API Key e Secret não foram encontradas.")

    def _get_headers(self):
        """
        Retorna os cabeçalhos para autenticação.
        """
        return {"X-MBX-APIKEY": self.api_key}

    def _make_request(self, endpoint, params=None):
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
        return super()._make_request(endpoint, params=params, headers=headers)

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

    def place_buy_order(self, symbol, quantity, price):
        """
        Simula uma ordem de compra.
        """
        if not symbol or not quantity or not price:
            raise ValueError("Parâmetros inválidos para a ordem de compra.")

        print("\n--- Ordem de Compra ---")
        print(f"Ativo: {symbol}")
        print(f"Quantidade: {quantity}")
        print(f"Preço: {price}")
        print("Tipo de Ordem: LIMIT (Simulada)")
        print("----------------------\n")

    def place_sell_order(self, symbol, quantity, price):
        """
        Simula uma ordem de venda.
        """
        if not symbol or not quantity or not price:
            raise ValueError("Parâmetros inválidos para a ordem de venda.")

        print("\n--- Ordem de Venda ---")
        print(f"Ativo: {symbol}")
        print(f"Quantidade: {quantity}")
        print(f"Preço: {price}")
        print("Tipo de Ordem: LIMIT (Simulada)")
        print("----------------------\n")

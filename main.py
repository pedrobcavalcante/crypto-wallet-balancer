import os
import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()


class BinanceAPI:
    def __init__(self):
        # Carrega as chaves de API
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.api_secret = os.getenv("BINANCE_API_SECRET")
        self.base_url = "https://api.binance.com"

        # Verificação para garantir que as chaves estão carregadas
        if not self.api_key or not self.api_secret:
            raise ValueError(
                "API Key e Secret não foram encontradas. Verifique o arquivo .env."
            )

    def _create_signature(self, params):
        """
        Gera uma assinatura HMAC SHA256 baseada nos parâmetros e na API Secret.
        """
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def _get_headers(self):
        """
        Retorna os cabeçalhos de autenticação necessários para a API.
        """
        return {"X-MBX-APIKEY": self.api_key}

    def _make_request(self, endpoint, params=None):
        """
        Realiza uma requisição GET para a API da Binance com autenticação.
        """
        url = self.base_url + endpoint
        params = params or {}
        params['timestamp'] = int(time.time() * 1000) - 1000
        params["signature"] = self._create_signature(params)

        response = requests.get(url, headers=self._get_headers(), params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erro na requisição: {response.status_code} - {response.text}")
            return None

    def get_account_info(self):
        """
        Obtém informações da conta e lista os ativos com saldo disponível.
        """
        account_info = self._make_request("/api/v3/account")
        if account_info:
            assets = [
                asset
                for asset in account_info["balances"]
                if float(asset["free"]) > 0 or float(asset["locked"]) > 0
            ]
            return assets
        return []


# Exemplo de uso da classe
if __name__ == "__main__":
    binance_api = BinanceAPI()
    assets = binance_api.get_account_info()
    for asset in assets:
        print(
            f"Ativo: {asset['asset']}, Livre: {asset['free']}, Em uso: {asset['locked']}"
        )

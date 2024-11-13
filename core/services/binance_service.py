import time
import requests
from core.utils.crypto_utils import create_signature
from core.entities.asset import Asset
from src.config import get_config


class BinanceService:
    def __init__(self):
        config = get_config()
        self.api_key = config["api_key"]
        self.api_secret = config["api_secret"]
        self.base_url = config["base_url"]

        if not self.api_key or not self.api_secret:
            raise ValueError(
                "API Key e Secret não foram encontradas. Verifique o arquivo .env."
            )

    def _get_headers(self):
        return {"X-MBX-APIKEY": self.api_key}

    def _make_request(self, endpoint, params=None):
        url = self.base_url + endpoint
        params = params or {}
        params["timestamp"] = int(time.time() * 1000) - 1000
        params["signature"] = create_signature(params, self.api_secret)

        response = requests.get(url, headers=self._get_headers(), params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erro na requisição: {response.status_code} - {response.text}")
            return None

    def get_account_assets(self):
        account_info = self._make_request("/api/v3/account")
        if account_info:
            return [
                Asset(asset["asset"], asset["free"], asset["locked"])
                for asset in account_info["balances"]
                if float(asset["free"]) > 0 or float(asset["locked"]) > 0
            ]
        return []

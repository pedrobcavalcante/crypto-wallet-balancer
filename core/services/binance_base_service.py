import requests
from config import get_config


class BinanceBaseService:
    def __init__(self):
        config = get_config()
        self.base_url = config["base_url"]

    def _make_request(self, endpoint, params=None, headers=None):
        """
        Realiza uma requisição genérica para a API da Binance.
        """
        url = self.base_url + endpoint
        params = params or {}
        headers = headers or {}

        # Log para depuração
        print(f"URL: {url}")
        print(f"Params: {params}")
        print(f"Headers: {headers}")

        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(
                f"Erro na requisição: {response.status_code} - {response.text}"
            )

    def _get_server_time(self):
        """
        Obtém o tempo atual do servidor da Binance para sincronizar o timestamp.
        """
        url = self.base_url + "/api/v3/time"
        response = requests.get(url)  # Chama requests diretamente para evitar recursão
        if response.status_code == 200:
            data = response.json()
            return data["serverTime"]
        else:
            raise Exception(
                f"Erro ao obter tempo do servidor: {response.status_code} - {response.text}"
            )

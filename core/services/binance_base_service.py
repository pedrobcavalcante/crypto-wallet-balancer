import requests
from config import get_config


class BinanceBaseService:
    def __init__(self):
        config = get_config()
        self.base_url = config["base_url"]

    def _make_request(self, endpoint, request_type: str, params=None, headers=None):
        """
        Realiza uma requisição genérica para a API da Binance.
        """
        url = self.base_url + endpoint
        params = params or {}
        headers = headers or {}

        if request_type.upper() == "GET":
            response = requests.get(url, params=params, headers=headers)
        elif request_type.upper() == "POST":
            response = requests.post(url, data=params, headers=headers)
        elif request_type.upper() == "PUT":
            response = requests.put(url, data=params, headers=headers)
        elif request_type.upper() == "DELETE":
            response = requests.delete(url, params=params, headers=headers)
        else:
            raise ValueError(f"Tipo de requisi o desconhecido: {request_type}")
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

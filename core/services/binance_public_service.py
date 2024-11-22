from .binance_base_service import BinanceBaseService


class BinancePublicService(BinanceBaseService):
    def get_current_price(self, asset_name):
        """
        Obtém o preço atual de um ativo em relação ao USDT usando o endpoint público.
        """
        if asset_name.upper() == "USDT":
            return 1.0  # O preço de USDT em relação a ele mesmo é sempre 1

        if asset_name.upper() == "BRL":
            symbol = "USDTBRL"  # Consulta o par invertido para BRL
        else:
            symbol = f"{asset_name.upper()}USDT"

        endpoint = "/api/v3/ticker/price"
        params = {"symbol": symbol}
        data = self._make_request(endpoint, params=params)

        if "price" in data:
            if asset_name.upper() == "BRL":
                return 1 / float(data["price"])
            return float(data["price"])
        else:
            print(f"Preço para {symbol} não encontrado.")
            return None

    def get_current_prices(self):
        """
        Obtém os preços de todos os ativos da Binance usando o endpoint público.
        """
        endpoint = "/api/v3/ticker/price"
        data = self._make_request(endpoint, request_type="GET")
        if data:
            return {price["symbol"]: float(price["price"]) for price in data}
        else:
            return {}

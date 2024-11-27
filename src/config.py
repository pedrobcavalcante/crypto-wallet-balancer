import os
from dotenv import load_dotenv

# Carrega o arquivo .env
load_dotenv()


# Função para acessar as configurações
def get_config():
    return {
        "api_key": os.getenv("BINANCE_API_KEY"),
        "api_secret": os.getenv("BINANCE_API_SECRET"),
        "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
        "base_url": "https://api.binance.com",
        "min_order_value": float(os.getenv("MIN_ORDER_VALUE", 6.0)),
        "max_order_value": float(os.getenv("MAX_ORDER_VALUE", 10.0)),
        "max_percentage_difference": float(
            os.getenv("MAX_PERCENTAGE_DIFFERENCE", 0.0001)
        ),
        "planilha": os.getenv("PLANILHA"),
    }

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
        "max_percentage_difference": 1.0,
    }

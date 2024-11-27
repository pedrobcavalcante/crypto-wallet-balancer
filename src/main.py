import logging
import threading
import time

from config import get_config

from core.database.crypto_assets_manager import CryptoAssetsManager
from core.services.binance_private_service import BinancePrivateService
from core.services.binance_public_service import BinancePublicService


from core.services.state_manager import StateManager
from core.services.telegram_notifier import TelegramNotifier
from core.use_cases.sync_crypto_data import sync_crypto_data
from core.use_cases.portfolio_analysis import PortfolioAnalysis

# Configuração do logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    # Inicializa serviços e banco de dados
    public_service = BinancePublicService()
    private_service = BinancePrivateService()
    db_manager = CryptoAssetsManager()
    config = get_config()
    sync_crypto_data(config["planilha"])
    logger.info("Iniciando análise de portfólio...")

    # Instancia o gerenciador de estado e o TelegramNotifier
    state_manager = StateManager()
    telegram = TelegramNotifier(config["telegram_bot_token"])

    # Instancia o caso de uso
    analysis = PortfolioAnalysis(
        public_service,
        private_service,
        db_manager,
        config["max_percentage_difference"],
    )

    # Executa o monitoramento do Telegram em uma thread separada
    telegram_thread = threading.Thread(
        target=telegram.monitor_telegram,
        args=(config["telegram_chat_id"], state_manager),
    )
    telegram_thread.daemon = True
    telegram_thread.start()

    while True:
        if state_manager.is_running():
            try:
                # Busca os ativos combinados
                combined_assets = analysis.analyze_portfolio()
                logger.info("Ativos combinados obtidos com sucesso:")
                if combined_assets is not None:
                    for name, quantity in combined_assets.items():
                        logger.info(f"{name}: {quantity}")

            except KeyboardInterrupt:
                logger.info("Execução interrompida pelo usuário.")
                break
            except Exception as e:
                logger.error(f"Erro durante a execução: {e}")
            finally:
                time.sleep(5)
        else:
            time.sleep(1)  # Pausa breve para evitar uso excessivo de CPU


if __name__ == "__main__":
    main()

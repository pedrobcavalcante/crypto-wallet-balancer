import logging
import time

from config import get_config
from core.services.binance_private_service import BinancePrivateService
from core.services.binance_public_service import BinancePublicService
from core.database.bnb_wallet_db_manager import BNBWalletDBManager
from core.database.db_manager import DBManager
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
    bnb_wallet_db = BNBWalletDBManager()
    db_manager = DBManager()
    config = get_config()

    logger.info("Iniciando análise de portfólio...")

    # Instancia o caso de uso
    analysis = PortfolioAnalysis(
        public_service,
        private_service,
        bnb_wallet_db,
        db_manager,
        config["max_percentage_difference"],
    )

    while True:
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
            time.sleep(1)


if __name__ == "__main__":
    main()

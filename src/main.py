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

    # Busca os ativos combinados
    combined_assets = analysis.get_combined_assets()
    logger.info("Ativos combinados obtidos com sucesso:")
    for name, quantity in combined_assets.items():
        logger.info(f"{name}: {quantity}")

    # Calcula detalhes do portfólio
    asset_details, portfolio_value = analysis.calculate_portfolio_details(
        combined_assets
    )
    logger.info(f"Valor total do portfólio: ${portfolio_value:.2f}")
    logger.info("Detalhes dos ativos:")
    for asset in asset_details:
        logger.info(
            f"{asset['name']}: {asset['quantity']} @ ${asset['price']:.2f} = ${asset['value']:.2f}"
        )

    # Analisa diferenças e recomendações
    if portfolio_value > 0:
        recommendations = analysis.analyze_differences(asset_details)
        logger.info("Recomendações de ajuste:")
        for rec in recommendations:
            if rec["action"] == "not found":
                logger.warning(f"{rec['name']}: {rec['message']}")
            else:
                logger.info(
                    f"{rec['name']}: {rec['action'].upper()} (Diferença: {rec['difference']:.2f}%)"
                )
    else:
        logger.warning("Nenhum valor disponível na carteira.")


if __name__ == "__main__":
    while True:
        try:
            main()
            time.sleep(1)  # Aguarda 1 segundo antes de repetir
        except KeyboardInterrupt:
            logger.info("Execução interrompida pelo usuário.")
            break
        except Exception as e:
            logger.error(f"Erro durante a execução: {e}")

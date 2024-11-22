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
    exchange_info = public_service.get_exchange_info()
    while True:
        try:
            # Busca os ativos combinados
            combined_assets = analysis.get_combined_assets()
            logger.info("Ativos combinados obtidos com sucesso:")
            for name, quantity in combined_assets.items():
                logger.info(f"{name}: {quantity}")

            # Calcula detalhes do portfólio
            asset_details, portfolio_value = analysis.calculate_portfolio_details(
                combined_assets
            )
            _print_portfolio_details(asset_details, portfolio_value)

            # Analisa diferenças e recomendações
            if portfolio_value > 0:
                recommendations = analysis.analyze_differences(
                    asset_details, exchange_info
                )
                _print_recommendations(recommendations)
            else:
                logger.warning("Nenhum valor disponível na carteira.")

        except KeyboardInterrupt:
            logger.info("Execução interrompida pelo usuário.")
            break
        except Exception as e:
            logger.error(f"Erro durante a execução: {e}")
        finally:
            time.sleep(1)


def _print_portfolio_details(asset_details, portfolio_value):
    logger.info(f"Valor total do portfólio: ${portfolio_value:.2f}")
    logger.info("Detalhes dos ativos:")
    for asset in asset_details:
        logger.info(
            f"Ativo: {asset['name']} - Quantidade atual: {asset['quantity']} Preço atual: ${asset['price']:.2f} Total em $: ${asset['value']:.2f}"
        )


def _print_recommendations(recommendations):
    logger.info("Recomendações de ajuste:")
    for rec in recommendations:
        if rec["action"] == "not found":
            logger.warning(f"{rec['name']}: {rec['message']}")
        elif rec["action"] == "sell_all":
            logger.info(f"{rec['name']}: VENDIDO TOTALMENTE ({rec['message']})")
        else:
            # Garante que a chave 'difference' está presente antes de usar
            difference = rec.get("difference", 0.0)  # Valor padrão 0.0
            logger.info(
                f"{rec['name']}: {rec['action'].upper()} (Diferença: {difference:.2f}%)"
            )


if __name__ == "__main__":
    main()

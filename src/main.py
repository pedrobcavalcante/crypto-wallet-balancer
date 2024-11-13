from core.services.binance_service import BinanceService
from core.database.db_manager import DBManager


def main():
    db_manager = DBManager()

    # Exibe todos os ativos salvos
    saved_assets = db_manager.get_all_assets()
    for saved_asset in saved_assets:
        print(saved_asset)


if __name__ == "__main__":
    main()

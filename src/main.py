from core.services.binance_service import BinanceService


def main():
    binance_service = BinanceService()
    assets = binance_service.get_account_assets()
    for asset in assets:
        print(asset)


if __name__ == "__main__":
    main()

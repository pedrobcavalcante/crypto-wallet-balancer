from core.services.binance_service import BinanceService
from core.database.bnb_wallet_db_manager import BNBWalletDBManager


def main():
    # Inicializa o serviço da Binance e o gerenciador de banco de dados da carteira BNB
    binance_service = BinanceService()
    bnb_wallet_db = BNBWalletDBManager()

    # Busca os ativos diretamente da Binance
    binance_assets = binance_service.get_account_assets()

    # Converte os ativos da Binance para um dicionário {asset_name: quantidade}
    binance_asset_dict = {
        asset.asset_name.lower(): float(asset.free) for asset in binance_assets
    }

    # Busca os ativos na carteira BNB
    bnb_assets = bnb_wallet_db.get_all_token_balances()

    # Converte os ativos da BNB para um dicionário {token_name: quantidade}
    bnb_asset_dict = {
        token["token_name"].lower(): float(token["quantity"]) for token in bnb_assets
    }

    # Combina os ativos, somando as quantidades
    combined_assets = binance_asset_dict.copy()
    for token_name, quantity in bnb_asset_dict.items():
        if token_name in combined_assets:
            combined_assets[token_name] += quantity
        else:
            combined_assets[token_name] = quantity

    # Exibe o total de cada ativo
    print("Total de ativos combinados (Binance + BNB Wallet):")
    for asset_name, total_quantity in combined_assets.items():
        print(f"{asset_name.upper()}: Quantidade: {total_quantity:.8f}")


if __name__ == "__main__":
    main()

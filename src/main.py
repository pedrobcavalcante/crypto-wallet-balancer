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

    # Calcula o valor total da carteira e armazena os detalhes dos ativos disponíveis
    portfolio_value = 0.0
    asset_details = []

    for asset_name, total_quantity in combined_assets.items():
        current_price = binance_service.get_current_price(asset_name)
        if current_price is not None:  # Exibe apenas se o preço estiver disponível
            asset_value = total_quantity * current_price
            portfolio_value += asset_value
            asset_details.append(
                {
                    "name": asset_name.upper(),
                    "quantity": total_quantity,
                    "price": current_price,
                    "value": asset_value,
                }
            )

    # Calcula o percentual de cada ativo e organiza do maior para o menor
    if portfolio_value > 0:
        for asset in asset_details:
            asset["percentage"] = (asset["value"] / portfolio_value) * 100
        asset_details.sort(key=lambda x: x["percentage"], reverse=True)

        # Exibe o total de cada ativo com o percentual na carteira
        print("Distribuição de Ativos na Carteira (do maior para o menor):")
        for asset in asset_details:
            print(
                f"{asset['name']}: Quantidade: {asset['quantity']:.8f}, "
                f"Preço Atual: ${asset['price']:.2f}, "
                f"Valor: ${asset['value']:.2f}, "
                f"Percentual da Carteira: {asset['percentage']:.2f}%"
            )
    else:
        print("Nenhum valor disponível na carteira.")


if __name__ == "__main__":
    main()

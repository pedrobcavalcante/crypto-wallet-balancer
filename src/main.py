from core.services.binance_service import BinanceService
from core.database.bnb_wallet_db_manager import BNBWalletDBManager
from core.database.db_manager import DBManager


def main():
    # Inicializa os serviços e gerenciadores de banco de dados
    binance_service = BinanceService()
    bnb_wallet_db = BNBWalletDBManager()
    db_manager = DBManager()

    # Define a diferença percentual máxima permitida (3%)
    max_percentage_difference = 3.0

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

        # Agora, buscamos os percentuais salvos no db.json
        saved_assets = db_manager.get_all_assets()
        saved_asset_dict = {
            asset["asset_name"].lower(): asset["percentage"] for asset in saved_assets
        }

        # Calcula a diferença percentual para cada ativo
        print("\nDiferença Percentual entre a Carteira Atual e o Salvo no db.json:")

        for asset in asset_details:
            asset_name = asset["name"].lower()
            if asset_name in saved_asset_dict:
                saved_percentage = saved_asset_dict[asset_name]
                current_percentage = asset["percentage"]
                difference = current_percentage - saved_percentage

                # Exibe a diferença e as informações de venda ou compra
                print(f"\n{asset['name']}:")
                print(
                    f"Quantidade na carteira Binance: {asset['quantity']:.8f}, Preço Atual: ${asset['price']:.2f}, Percentual Atual: {current_percentage:.2f}%"
                )
                print(
                    f"Quantidade na carteira teórica (db.json): {saved_asset_dict[asset_name]:.2f}%, Percentual Teórico: {saved_percentage:.2f}%"
                )
                print(f"Diferença Percentual: {difference:.2f}%")

                # Verifica se a diferença é maior que 3% ou menor que -3% e exibe a recomendação
                if difference > max_percentage_difference:
                    print(
                        f"**Hora de Vender**: Diferença de {difference:.2f}% maior que {max_percentage_difference}%.\n"
                    )
                elif difference < -max_percentage_difference:
                    print(
                        f"**Hora de Comprar**: Diferença de {difference:.2f}% menor que {-max_percentage_difference}%.\n"
                    )
                else:
                    print("A diferença está dentro dos limites permitidos.\n")

            else:
                print(f"{asset['name']}: Não encontrado no db.json.")

    else:
        print("Nenhum valor disponível na carteira.")


if __name__ == "__main__":
    main()

from core.database.db_manager import DBManager


def adjust_db():
    # Inicializa o gerenciador de banco de dados
    db_manager = DBManager()

    # Busca os ativos salvos no banco de dados
    assets = db_manager.get_all_assets()

    # Exibe os ativos para ajuste
    print("Ativos Salvos no db.json:")
    for asset in assets:
        print(
            f"Ativo: {asset['asset_name']}, Pontos: {asset['points']}, Preço Médio: {asset.get('average_price', 'N/A')}, Percentual: {asset.get('percentage', 'N/A')}"
        )

    # Caso queira ajustar algum valor, basta atualizar diretamente no banco de dados.
    # Isso pode ser feito manualmente com base nas informações exibidas.
    print("\nVerifique os ativos e ajuste manualmente conforme necessário.\n")
    print(
        "Se precisar corrigir algum ativo, basta usar o método save_asset() no DBManager."
    )


if __name__ == "__main__":
    adjust_db()

from core.database.db_manager import DBManager


def main():
    # Inicializa o gerenciador do banco de dados
    db_manager = DBManager()

    # Calcula e exibe todos os ativos com o percentual de cada um em relação ao total da carteira
    assets_with_percentages = db_manager.get_asset_percentages()
    for asset in assets_with_percentages:
        print(
            f"Ativo: {asset['asset_name']}, Pontos: {asset['points']}, "
            f"Preço Médio: {asset['average_price']}, Percentual da Carteira: {asset['percentage']:.2f}%"
        )


if __name__ == "__main__":
    main()

from tinydb import TinyDB, Query


class DBManager:
    def __init__(self, db_path="db.json"):
        """
        Inicializa a conexão com o banco de dados TinyDB.
        """
        self.db = TinyDB(db_path)
        self.assets_table = self.db.table("assets")

    def save_asset(self, asset_name, points, average_price, percentage=None):
        """
        Salva um ativo no banco de dados com seus pontos, preço médio e percentual.
        """
        Asset = Query()
        existing_asset = self.assets_table.get(Asset.asset_name == asset_name)

        asset_data = {
            "asset_name": asset_name,
            "points": points,
            "average_price": average_price,
        }

        if percentage is not None:
            asset_data["percentage"] = percentage

        if existing_asset:
            self.assets_table.update(asset_data, Asset.asset_name == asset_name)
        else:
            self.assets_table.insert(asset_data)

    def get_all_assets(self):
        """
        Retorna todos os ativos armazenados no banco de dados, corrigindo os percentuais se necessário.
        """
        # Carrega todos os ativos da tabela
        assets = self.assets_table.all()

        # Verifica se há discrepâncias nos percentuais e os corrige
        atualizar_dados = self._correct_percentages(assets)

        # Recarrega os ativos para garantir que estamos retornando os dados mais recentes
        if atualizar_dados:
            assets = self.assets_table.all()

        return assets

    def get_asset_percentages(self):
        """
        Calcula e salva o percentual de cada ativo em relação à carteira total.
        """
        assets = self.get_all_assets()
        total_points = sum(asset["points"] for asset in assets)

        if total_points == 0:
            return [
                {"asset_name": asset["asset_name"], "percentage": 0} for asset in assets
            ]

        assets_with_percentages = []

        for asset in assets:
            percentage = (asset["points"] / total_points) * 100
            asset_with_percentage = {
                "asset_name": asset["asset_name"],
                "points": asset["points"],
                "average_price": asset["average_price"],
                "percentage": percentage,
            }
            # Atualiza o banco de dados com o novo percentual
            self.save_asset(
                asset_name=asset["asset_name"],
                points=asset["points"],
                average_price=asset["average_price"],
                percentage=percentage,
            )
            assets_with_percentages.append(asset_with_percentage)

        return assets_with_percentages

    def _correct_percentages(self, assets: list[dict]) -> bool:
        """
        Verifica se os percentuais dos ativos estão corretos. Se não estiverem, os corrige.
        """
        atualizar_banco = False
        total_points = sum(asset["points"] for asset in assets)

        for asset in assets:
            calculated_percentage = (asset["points"] / total_points) * 100
            if (
                "percentage" not in asset
                or asset["percentage"] != calculated_percentage
            ):
                if not atualizar_banco:
                    atualizar_banco = True
                # Se a discrepância for encontrada, atualiza o percentual no banco de dados
                print(
                    f"Discrepância encontrada para o ativo {asset['asset_name']}. Corrigindo..."
                )
                self.save_asset(
                    asset_name=asset["asset_name"],
                    points=asset["points"],
                    average_price=asset["average_price"],
                    percentage=calculated_percentage,
                )
        return atualizar_banco

    def update_average_price(self, asset_name: str, new_average_price: float) -> None:
        """
        Atualiza o preço médio de um ativo.

        Args:
            asset_name (str): Nome do ativo.
            new_average_price (float): Novo preço médio do ativo.
        """
        asset = self.assets_table.get(Query().asset_name == asset_name)
        if asset:
            self.save_asset(
                asset_name=asset_name,
                points=asset["points"],
                average_price=round(new_average_price, 4),
            )

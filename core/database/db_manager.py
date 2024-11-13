from tinydb import TinyDB, Query


class DBManager:
    def __init__(self, db_path="db.json"):
        """
        Inicializa a conexão com o banco de dados TinyDB.
        """
        self.db = TinyDB(db_path)
        self.assets_table = self.db.table("assets")

    def save_asset(self, asset_name, percentage, average_price):
        """
        Salva um ativo no banco de dados com seu percentual da carteira e preço médio.
        """
        # Verifica se o ativo já existe
        Asset = Query()
        existing_asset = self.assets_table.get(Asset.asset_name == asset_name)

        if existing_asset:
            # Atualiza o ativo existente
            self.assets_table.update(
                {"percentage": percentage, "average_price": average_price},
                Asset.asset_name == asset_name,
            )
        else:
            # Insere um novo ativo
            self.assets_table.insert(
                {
                    "asset_name": asset_name,
                    "percentage": percentage,
                    "average_price": average_price,
                }
            )

    def get_all_assets(self):
        """
        Retorna todos os ativos armazenados no banco de dados.
        """
        return self.assets_table.all()

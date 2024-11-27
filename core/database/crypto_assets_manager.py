from tinydb import TinyDB, Query


class CryptoAssetsManager:
    def __init__(self, db_path="crypto_db.json"):
        """
        Gerenciador para acessar dados do arquivo crypto_db.json.
        """
        self.db = TinyDB(db_path)
        self.crypto_table = self.db.table("crypto_assets")

    def get_asset_data(self, crypto_name):
        CryptoAsset = Query()
        return self.crypto_table.get(CryptoAsset.crypto == crypto_name)

    def get_all_assets(self):
        return self.crypto_table.all()

    def get_asset_percentage(self, crypto_name):
        asset = self.get_asset_data(crypto_name)
        return asset.get("percentual", 0.0)

    def get_asset_points(self, crypto_name):
        asset = self.get_asset_data(crypto_name)
        return asset.get("pontos", 0.0)

    def get_bnb_wallet_quantity(self):
        asset = self.get_asset_data("BNB")
        return asset.get("total_carteira", 0.0)

    def save_crypto_asset(
        self,
        crypto,
        preco_medio,
        percentual,
        pontos,
        meta_moeda,
        total_carteira,
    ):
        """
        Salva ou atualiza os dados de um ativo no banco de dados.
        """
        CryptoAsset = Query()
        existing_asset = self.crypto_table.get(CryptoAsset.crypto == crypto)

        asset_data = {
            "crypto": crypto,
            "preco_medio": preco_medio,
            "percentual": percentual,
            "pontos": pontos,
            "meta_moeda": meta_moeda,
            "total_carteira": total_carteira,
        }

        if existing_asset:
            self.crypto_table.update(asset_data, CryptoAsset.crypto == crypto)
        else:
            self.crypto_table.insert(asset_data)

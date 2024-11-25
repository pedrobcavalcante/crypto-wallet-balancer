from tinydb import TinyDB, Query


class CryptoAssetsManager:
    def __init__(self, db_path="crypto_assets.json"):
        """
        Inicializa a conexão com o banco de dados TinyDB.
        """
        self.db = TinyDB(db_path)
        self.crypto_table = self.db.table("crypto_assets")

    def save_crypto_asset(
        self, crypto, percentual, pontos, meta_dollar, meta_moeda, total_carteira
    ):
        """
        Salva ou atualiza os dados de um ativo da aba 'Cypto' no banco de dados.
        """
        CryptoAsset = Query()
        existing_asset = self.crypto_table.get(CryptoAsset.crypto == crypto)

        asset_data = {
            "crypto": crypto,
            "percentual": percentual,
            "pontos": pontos,
            "meta_dollar": meta_dollar,
            "meta_moeda": meta_moeda,
            "total_carteira": total_carteira,
        }

        if existing_asset:
            self.crypto_table.update(asset_data, CryptoAsset.crypto == crypto)
        else:
            self.crypto_table.insert(asset_data)

    def get_all_crypto_assets(self):
        """
        Retorna todos os ativos da tabela 'crypto_assets'.
        """
        return self.crypto_table.all()

    def get_crypto_by_name(self, crypto_name):
        """
        Busca um ativo específico pelo nome.
        """
        CryptoAsset = Query()
        return self.crypto_table.get(CryptoAsset.crypto == crypto_name)

    def delete_crypto_asset(self, crypto_name):
        """
        Remove um ativo da tabela pelo nome.
        """
        CryptoAsset = Query()
        self.crypto_table.remove(CryptoAsset.crypto == crypto_name)

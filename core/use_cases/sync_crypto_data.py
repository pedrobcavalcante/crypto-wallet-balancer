import math
import re
from core.database.crypto_assets_manager import CryptoAssetsManager
from core.database.google_sheet_crypto_reader import GoogleSheetCryptoReader


def sync_crypto_data(sheet_url, db_path="crypto_db.json"):
    """
    Sincroniza os dados da aba 'Cypto' da planilha com o banco de dados CryptoDBManager.

    Args:
        sheet_url (str): URL da planilha Google Sheets.
        db_path (str): Caminho para o banco de dados TinyDB.
    """
    # Instanciar o leitor da planilha e o gerenciador do banco de dados
    crypto_reader = GoogleSheetCryptoReader(sheet_url)
    crypto_db_manager = CryptoAssetsManager(db_path=db_path)

    try:
        # Buscar os dados da planilha
        crypto_table = crypto_reader.fetch_crypto_table()

        # Filtrar as colunas necessárias
        columns_to_display = [
            "Crypto",
            "Percentual",
            "Pontos",
            "Meta($):",
            "meta Moeda",
            "Total (Carteira)",
        ]
        filtered_table = crypto_table[columns_to_display]

        # Iterar sobre cada linha da tabela filtrada e salvar no banco de dados
        for _, row in filtered_table.iterrows():
            crypto = row["Crypto"]
            if isinstance(row["Crypto"], str):
                if isinstance(row["Percentual"], str):
                    percentual = float(row["Percentual"].strip("%").replace(",", "."))
                else:
                    percentual = row["Percentual"]
                pontos = float(row["Pontos"])
                meta_dollar = float(re.sub(r"[^\d\.]", "", row["Meta($):"]))
                if isinstance(row["meta Moeda"], str):
                    meta_moeda = float(row["meta Moeda"].replace(",", "."))
                else:
                    meta_moeda = row["meta Moeda"]
                if isinstance(row["Total (Carteira)"], str):
                    total_carteira = float(row["Total (Carteira)"].replace(",", "."))
                else:
                    total_carteira = row["Total (Carteira)"]
                if math.isnan(total_carteira):
                    total_carteira = None

                # Salvar no banco de dados usando o CryptoDBManager
                crypto_db_manager.save_crypto_asset(
                    crypto=crypto,
                    percentual=percentual,
                    pontos=pontos,
                    meta_dollar=meta_dollar,
                    meta_moeda=meta_moeda,
                    total_carteira=total_carteira,
                )
        print("Dados da planilha sincronizados com sucesso no banco de dados!")

    except Exception as e:
        print(f"Erro ao sincronizar dados: {e}")

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
            "Preço Médio",
            "Percentual",
            "Pontos",
            "meta Moeda",
            "Total (Carteira)",
        ]
        filtered_table = crypto_table[columns_to_display]

        # Iterar sobre cada linha da tabela filtrada e salvar no banco de dados
        for _, row in filtered_table.iterrows():
            crypto = row["Crypto"]
            if isinstance(row["Crypto"], str):
                percentual = _parse_percentual(row["Percentual"])
                pontos = float(row["Pontos"])
                meta_moeda = _parse_number(row["meta Moeda"])
                total_carteira = _parse_number(row["Total (Carteira)"], allow_nan=True)
                preco_medio = _parse_preco_medio(row["Preço Médio"])

                # Salvar no banco de dados usando o CryptoDBManager
                crypto_db_manager.save_crypto_asset(
                    crypto=crypto,
                    preco_medio=preco_medio,
                    percentual=percentual,
                    pontos=pontos,
                    meta_moeda=meta_moeda,
                    total_carteira=total_carteira,
                )
        print("Dados da planilha sincronizados com sucesso no banco de dados!")

    except Exception as e:
        print(f"Erro ao sincronizar dados: {e}")


def _parse_percentual(value):
    """
    Converte o percentual em string para float, se necessário.

    Args:
        value: Valor do percentual, podendo ser string ou float.

    Returns:
        float: Percentual convertido.
    """
    if isinstance(value, str):
        return float(value.strip("%").replace(",", "."))
    return value


def _parse_number(value, allow_nan=False):
    """
    Converte um valor numérico (string ou float) para float.

    Args:
        value: Valor numérico como string ou float.
        allow_nan (bool): Se True, permite que NaN seja retornado.

    Returns:
        float: Valor convertido ou None se NaN e allow_nan=True.
    """
    if isinstance(value, str):
        value = value.replace(",", ".")
    result = float(value)
    if math.isnan(result) and allow_nan:
        return None
    return result


def _parse_preco_medio(value):
    """
    Remove caracteres não numéricos de valores de preço médio e converte para float.

    Args:
        value (str): Valor do preço médio como string.

    Returns:
        float: Valor convertido.
    """
    return float(value.replace("$", "").replace(".", "").replace(",", "."))


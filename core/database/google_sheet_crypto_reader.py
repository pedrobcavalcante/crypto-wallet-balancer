import pandas as pd

from src.config import get_config


class GoogleSheetCryptoReader:
    def __init__(self, sheet_url: str):
        """
        Classe para acessar e processar dados de uma aba específica de uma planilha no Google Sheets.

        :param sheet_url: URL pública da planilha no formato Google Sheets.
        """
        self.sheet_url = sheet_url

    def get_csv_url(self) -> str:
        """
        Converte o link da planilha em um link para baixar como CSV.

        :return: URL da planilha no formato CSV.
        """
        base_url = self.sheet_url.split("/edit")[0]
        return f"{base_url}/gviz/tq?tqx=out:csv"

    def fetch_crypto_table(self) -> pd.DataFrame:
        """
        Busca os dados da aba "Cypto" da planilha e retorna como um DataFrame.

        :return: pandas.DataFrame com os dados da aba "Cypto".
        """
        try:
            # Obtém o URL do CSV
            csv_url = self.get_csv_url()
            # Faz o download dos dados como DataFrame
            data = pd.read_csv(csv_url)

            # Retorna os dados processados
            return data
        except Exception as e:
            raise RuntimeError(f"Erro ao buscar os dados da planilha: {e}")


if __name__ == "__main__":
    # Configuração inicial
    config = get_config()

    # URL da planilha Google Sheets (com a aba Cypto)
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1NOu_ysYqj9qk1ICZbMtrRhhZe-2sXa5Z4jjAGy4uNrM/edit?gid=0"

    # Instancia o leitor
    crypto_reader = GoogleSheetCryptoReader(SHEET_URL)

    # Busca os dados da aba Cypto
    try:
        crypto_table = crypto_reader.fetch_crypto_table()
        print("Tabela de Cypto obtida com sucesso:")
        print(crypto_table)
    except Exception as e:
        print(f"Erro: {e}")

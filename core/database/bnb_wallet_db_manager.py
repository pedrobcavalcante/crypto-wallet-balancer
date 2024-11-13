from tinydb import TinyDB, Query


class BNBWalletDBManager:
    def __init__(self, db_path="bnb_wallet.json"):
        """
        Inicializa a conexão com o banco de dados TinyDB para a carteira BNB.
        """
        self.db = TinyDB(db_path)
        self.wallet_table = self.db.table("bnb_wallet")

    def save_token_balance(self, token_name, quantity):
        """
        Salva o saldo de um token específico no banco de dados da carteira BNB.
        """
        Token = Query()
        existing_token = self.wallet_table.get(Token.token_name == token_name)

        if existing_token:
            # Atualiza a quantidade do token existente
            self.wallet_table.update(
                {"quantity": quantity}, Token.token_name == token_name
            )
        else:
            # Insere um novo token com a quantidade
            self.wallet_table.insert({"token_name": token_name, "quantity": quantity})

    def get_all_token_balances(self):
        """
        Retorna todos os saldos de tokens armazenados na carteira BNB.
        """
        return self.wallet_table.all()

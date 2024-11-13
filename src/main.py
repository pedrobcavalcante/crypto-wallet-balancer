from core.database.bnb_wallet_db_manager import BNBWalletDBManager


def main():
    # Inicializa o gerenciador do banco de dados para a carteira BNB
    bnb_wallet_db = BNBWalletDBManager()

    # Salva os saldos de tokens
    bnb_wallet_db.save_token_balance("bnb", 0.00053376)
    bnb_wallet_db.save_token_balance("btc", 0.11672992)
    bnb_wallet_db.save_token_balance("eth", 2.99979039)

    # Exibe todos os saldos salvos
    token_balances = bnb_wallet_db.get_all_token_balances()
    print("Saldos na carteira BNB:")
    for token in token_balances:
        print(f"{token['token_name'].upper()}: Quantidade: {token['quantity']}")


if __name__ == "__main__":
    main()

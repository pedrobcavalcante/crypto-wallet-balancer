import requests
import logging


class TelegramNotifier:
    def __init__(self, bot_token):
        """
        Inicializa o TelegramNotifier com o token do bot e o chat ID.
        :param bot_token: Token do bot fornecido pelo Telegram.
        :param chat_id: ID do chat (ou grupo) onde a mensagem será enviada.
        """
        self.bot_token = bot_token
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    def send_message(self, message, chat_id):
        """
        Envia uma mensagem para o chat do Telegram.
        :param message: Conteúdo da mensagem.
        :return: Resposta da API do Telegram.
        """
        try:
            response = requests.post(
                self.api_url,
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "HTML",
                },
            )
            response.raise_for_status()
            logging.info("Mensagem enviada com sucesso!")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao enviar mensagem para o Telegram: {e}")
            return None

import time
import requests
import logging


class TelegramNotifier:
    def __init__(self, bot_token):
        """
        Inicializa o TelegramNotifier com o token do bot.
        :param bot_token: Token do bot fornecido pelo Telegram.
        """
        self.bot_token = bot_token
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"

    def send_message(self, message, chat_id):
        """
        Envia uma mensagem para o chat do Telegram.
        :param message: Conteúdo da mensagem.
        :param chat_id: ID do chat no Telegram.
        """
        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
            )
            response.raise_for_status()
            logging.info("Mensagem enviada com sucesso!")
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao enviar mensagem para o Telegram: {e}")

    def get_updates(self, offset):
        """
        Busca atualizações de mensagens do Telegram.
        :param offset: Offset para buscar somente mensagens novas.
        :return: Lista de atualizações (mensagens).
        """
        try:
            response = requests.get(
                f"{self.api_url}/getUpdates", params={"offset": offset, "timeout": 10}
            )
            response.raise_for_status()
            return response.json().get("result", [])
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao buscar atualizações do Telegram: {e}")
            return []

    def monitor_telegram(self, chat_id, state_manager):
        """
        Monitora o Telegram por comandos como /start, /stop e /status.
        :param chat_id: ID do chat onde o bot está operando.
        :param state_manager: Instância do gerenciador de estado.
        """
        offset = 0

        while True:
            updates = self.get_updates(offset)
            for update in updates:
                offset = update["update_id"] + 1
                message = update["message"]["text"].strip().lower()

                if message == "/start":
                    state_manager.start()
                    self.send_message("O bot foi iniciado.", chat_id)
                elif message == "/stop":
                    state_manager.stop()
                    self.send_message("O bot foi pausado.", chat_id)
                elif message == "/status":
                    status = "rodando" if state_manager.is_running() else "pausado"
                    self.send_message(f"O bot está atualmente {status}.", chat_id)

            time.sleep(1)

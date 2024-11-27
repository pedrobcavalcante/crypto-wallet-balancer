class StateManager:
    def __init__(self):
        self.running = True

    def start(self):
        """Inicia o loop."""
        self.running = True

    def stop(self):
        """Pausa o loop."""
        self.running = False

    def is_running(self):
        """Verifica se o loop está ativo."""
        return self.running

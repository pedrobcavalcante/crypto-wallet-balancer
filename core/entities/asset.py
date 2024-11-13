class Asset:
    def __init__(self, asset_name, free, locked):
        self.asset_name = asset_name
        self.free = float(free)
        self.locked = float(locked)

    def __str__(self):
        return f"Ativo: {self.asset_name}, Livre: {self.free}, Em uso: {self.locked}"

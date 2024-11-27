from typing import Dict

from core.database.crypto_assets_manager import CryptoAssetsManager


def atualizar_preco_medio(
    crypto_name: str,
    nova_quantidade: float,
    novo_preco: float,
    crypto_manager: CryptoAssetsManager,
) -> Dict[str, float]:
    """
    Atualiza o preço médio de uma criptomoeda no banco de dados com base em uma nova ordem de compra.

    Args:
        crypto_name (str): Nome da criptomoeda.
        nova_quantidade (float): Quantidade adquirida na nova ordem.
        novo_preco (float): Preço unitário da nova compra.
        crypto_manager (CryptoAssetsManager): Instância do gerenciador de banco de dados.

    Returns:
        dict: Dados atualizados da criptomoeda.
    """
    # Buscar dados atuais da criptomoeda
    existing_asset = crypto_manager.get_asset_data(crypto_name)
    if not existing_asset:
        raise ValueError(f"Ativo {crypto_name} não encontrado no banco de dados.")

    quantidade_atual = existing_asset.get("total_carteira", 0.0) or 0.0
    preco_medio_atual = existing_asset.get("preco_medio", 0.0) or 0.0
    if isinstance(nova_quantidade, str):
        nova_quantidade = float(nova_quantidade)
    # Calcular o novo preço médio e nova quantidade total
    nova_quantidade_total = quantidade_atual + nova_quantidade
    novo_preco_medio = (
        quantidade_atual * preco_medio_atual + nova_quantidade * novo_preco
    ) / nova_quantidade_total

    # Atualizar os dados no banco usando o CryptoAssetsManager
    crypto_manager.save_crypto_asset(
        crypto=crypto_name,
        preco_medio=round(novo_preco_medio, 8),
        percentual=existing_asset.get("percentual", 0.0),
        pontos=existing_asset.get("pontos", 0.0),
        meta_moeda=existing_asset.get("meta_moeda", 0.0),
        total_carteira=round(nova_quantidade_total, 8),
    )

    print(
        f"Preço médio atualizado para {crypto_name}: {novo_preco_medio:.8f}, "
        f"Nova quantidade total: {nova_quantidade_total:.8f}"
    )

    return crypto_manager.get_asset_data(crypto_name)

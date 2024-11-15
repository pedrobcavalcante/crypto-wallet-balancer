import hmac
import hashlib
from urllib.parse import urlencode


def create_signature(params, api_secret):
    """
    Gera uma assinatura HMAC-SHA256 com base nos parâmetros da requisição.
    """
    # Gera a query string em ordem alfabética
    query_string = urlencode(params, doseq=True)
    return hmac.new(
        api_secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256
    ).hexdigest()

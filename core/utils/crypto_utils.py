import hmac
import hashlib
from urllib.parse import urlencode

def create_signature(params, secret):
    query_string = urlencode(params)
    return hmac.new(secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256).hexdigest()

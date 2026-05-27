import os

import httpx
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

AUTHACTION_DOMAIN = os.getenv("AUTHACTION_DOMAIN")
AUTHACTION_AUDIENCE = os.getenv("AUTHACTION_AUDIENCE")

_jwks_cache: dict | None = None


def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        jwks_uri = f"https://{AUTHACTION_DOMAIN}/.well-known/jwks.json"
        response = httpx.get(jwks_uri)
        response.raise_for_status()
        _jwks_cache = response.json()
    return _jwks_cache


def _find_rsa_key(token: str) -> dict:
    jwks = _get_jwks()
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")

    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"],
            }

    # Key not found — could be a rotation; bust cache and retry once
    global _jwks_cache
    _jwks_cache = None
    jwks = _get_jwks()
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"],
            }

    raise AuthenticationFailed("Unable to find matching public key")


def verify_token(token: str) -> dict:
    try:
        rsa_key = _find_rsa_key(token)
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=AUTHACTION_AUDIENCE,
            issuer=f"https://{AUTHACTION_DOMAIN}",
        )
        return payload
    except ExpiredSignatureError:
        raise AuthenticationFailed("Token has expired")
    except JWTError as exc:
        raise AuthenticationFailed(str(exc))


class AuthenticatedToken:
    """Minimal user-like object carrying the decoded JWT payload."""

    def __init__(self, payload: dict):
        self.payload = payload
        self.is_authenticated = True

    @property
    def sub(self) -> str:
        return self.payload.get("sub", "")


class JWTAuthentication(BaseAuthentication):
    """
    DRF authentication class that validates AuthAction JWTs.

    Equivalent to JwtStrategy in the NestJS example.
    Attach to a view via DEFAULT_AUTHENTICATION_CLASSES or per-view
    authentication_classes = [JWTAuthentication].
    """

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None  # Let other authenticators or AllowAny handle it

        token = auth_header.split(" ", 1)[1].strip()
        if not token:
            raise AuthenticationFailed("Empty token")

        payload = verify_token(token)
        return AuthenticatedToken(payload), token

    def authenticate_header(self, request):
        return "Bearer"

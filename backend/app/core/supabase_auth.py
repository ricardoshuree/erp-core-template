# [mcp-local harness] feature: close-open-signup-security | plano: ac575558 | 2026-08-04 11:29:53
# Remove docstring desatualizado de 'nao testado' -- fluxo ja validado com login Google real em producao
"""
Verificação de tokens JWT emitidos pelo Supabase Auth.

O Supabase assina os JWTs de sessão (incluindo os obtidos via Google
OAuth) com uma chave específica do projeto, disponibilizada via endpoint
JWKS (JSON Web Key Set):

    {SUPABASE_URL}/auth/v1/.well-known/jwks.json

Isso evita depender de um "JWT secret" compartilhado (modelo legado do
Supabase) -- a verificação usa a chave pública do projeto, sem precisar
armazenar nenhum segredo adicional no backend além da própria
SUPABASE_URL (já configurada).

Validado com login Google real em produção. A dependência `cryptography`
(backend/pyproject.toml) é necessária para o PyJWKClient verificar
assinaturas ES256/RS256.
"""

import jwt
from jwt import PyJWKClient

from app.core.config import settings

_JWKS_URL = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
_jwk_client: PyJWKClient | None = None


def _get_jwk_client() -> PyJWKClient:
    global _jwk_client
    if _jwk_client is None:
        _jwk_client = PyJWKClient(_JWKS_URL, cache_keys=True)
    return _jwk_client


def verify_supabase_token(token: str) -> dict:
    """
    Verifica um JWT emitido pelo Supabase Auth e retorna o payload
    decodificado (dict). Lança jwt.PyJWTError (ou subclasse) se o token
    for inválido, expirado, ou a assinatura não bater.
    """
    client = _get_jwk_client()
    signing_key = client.get_signing_key_from_jwt(token)
    payload = jwt.decode(
        token,
        signing_key.key,
        algorithms=["ES256", "RS256"],
        audience="authenticated",
    )
    return payload

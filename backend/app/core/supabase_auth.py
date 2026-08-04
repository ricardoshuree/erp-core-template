# [mcp-local harness] feature: supabase-auth-backend | plano: 82afe850 | 2026-08-04 00:41:22
# Modulo de verificacao de JWT do Supabase via JWKS
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

STATUS: escrito nesta sessão sem acesso a teste ponta a ponta (nenhum
login Google real foi executado contra isto ainda). Antes de confiar em
produção:
1. Rodar backend localmente, fazer login Google no frontend, confirmar
   que o token chega em get_current_user e é aceito
2. Conferir os claims reais do payload (sub, email) -- o Supabase pode
   variar o formato entre versões; os nomes usados aqui (payload["sub"],
   payload["email"]) são os documentados atualmente, mas não foram
   validados contra um token real neste ambiente
3. Confirmar que backend/pyproject.toml tem `cryptography` instalado
   (necessário para PyJWKClient com chaves ES256) -- rodar `uv sync`
   (dev local) ou aguardar o próximo `pip install .` (Railway) recriar
   o ambiente
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

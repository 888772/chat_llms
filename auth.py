"""
Módulo de autenticação simples baseado em token.
- No registro, o sistema gera um token aleatório e mostra pro usuário UMA vez.
- Só o HASH do token é salvo no banco (o token puro nunca é armazenado).
- No login, o usuário informa o nome de usuário + token, o sistema compara os hashes.
"""

import sqlite3
import secrets
import hashlib
from datetime import datetime

DB_PATH = "chat_historico.db"  # mesmo banco do histórico, tabela separada


def conectar():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def inicializar_tabela_usuarios():
    """Cria a tabela de usuários se não existir. Chame junto com inicializar_banco()."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            usuario TEXT PRIMARY KEY,
            token_hash TEXT NOT NULL,
            criado_em TEXT
        )
    """)
    conn.commit()
    conn.close()


def _hash_token(token: str) -> str:
    """Gera um hash SHA-256 do token (nunca guardamos o token em texto puro)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def usuario_existe(usuario: str) -> bool:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM usuarios WHERE usuario = ?", (usuario,))
    existe = cursor.fetchone() is not None
    conn.close()
    return existe


def registrar_usuario(usuario: str) -> str | None:
    """
    Registra um novo usuário e retorna o token gerado (texto puro, mostrado só agora).
    Retorna None se o usuário já existir.
    """
    if usuario_existe(usuario):
        return None

    token = secrets.token_hex(16)  # token aleatório de 32 caracteres hex
    token_hash = _hash_token(token)

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO usuarios (usuario, token_hash, criado_em) VALUES (?, ?, ?)",
        (usuario, token_hash, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

    return token


def validar_login(usuario: str, token: str) -> bool:
    """Verifica se o usuário + token combinam com o que está salvo."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT token_hash FROM usuarios WHERE usuario = ?", (usuario,))
    linha = cursor.fetchone()
    conn.close()

    if linha is None:
        return False

    return linha["token_hash"] == _hash_token(token)

"""
Módulo de persistência do histórico de chat usando SQLite.
Cada conversa tem um ID próprio (session_id), permitindo múltiplas conversas salvas.
"""

import sqlite3
import uuid
from datetime import datetime

DB_PATH = "chat_historico.db"


def conectar():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def inicializar_banco():
    """Cria as tabelas se não existirem. Chame uma vez no início do app."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversas (
            id TEXT PRIMARY KEY,
            usuario TEXT NOT NULL,
            titulo TEXT,
            criado_em TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mensagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversa_id TEXT,
            role TEXT,
            conteudo TEXT,
            criado_em TEXT,
            FOREIGN KEY (conversa_id) REFERENCES conversas (id)
        )
    """)

    conn.commit()
    conn.close()


def criar_conversa(usuario, titulo="Nova conversa"):
    """Cria uma nova conversa para o usuário informado e retorna o ID gerado."""
    conversa_id = str(uuid.uuid4())
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conversas (id, usuario, titulo, criado_em) VALUES (?, ?, ?, ?)",
        (conversa_id, usuario, titulo, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return conversa_id


def salvar_mensagem(conversa_id, role, conteudo):
    """Salva uma mensagem no histórico da conversa."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO mensagens (conversa_id, role, conteudo, criado_em) VALUES (?, ?, ?, ?)",
        (conversa_id, role, conteudo, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def carregar_mensagens(conversa_id, usuario):
    """Retorna as mensagens da conversa, mas só se ela pertencer ao usuário informado."""
    conn = conectar()
    cursor = conn.cursor()

    # confere se a conversa é mesmo do usuário antes de retornar qualquer coisa
    cursor.execute(
        "SELECT 1 FROM conversas WHERE id = ? AND usuario = ?",
        (conversa_id, usuario)
    )
    if cursor.fetchone() is None:
        conn.close()
        return []

    cursor.execute(
        "SELECT role, conteudo FROM mensagens WHERE conversa_id = ? ORDER BY id ASC",
        (conversa_id,)
    )
    linhas = cursor.fetchall()
    conn.close()
    return [{"role": linha["role"], "content": linha["conteudo"]} for linha in linhas]


def listar_conversas(usuario):
    """Retorna todas as conversas salvas do usuário, mais recentes primeiro."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, titulo, criado_em FROM conversas WHERE usuario = ? ORDER BY criado_em DESC",
        (usuario,)
    )
    linhas = cursor.fetchall()
    conn.close()
    return [dict(linha) for linha in linhas]


def apagar_conversa(conversa_id, usuario):
    """Remove uma conversa e suas mensagens, apenas se ela pertencer ao usuário."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM mensagens WHERE conversa_id = ? AND conversa_id IN "
        "(SELECT id FROM conversas WHERE id = ? AND usuario = ?)",
        (conversa_id, conversa_id, usuario)
    )
    cursor.execute(
        "DELETE FROM conversas WHERE id = ? AND usuario = ?",
        (conversa_id, usuario)
    )
    conn.commit()
    conn.close()


def renomear_conversa(conversa_id, novo_titulo):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE conversas SET titulo = ? WHERE id = ?",
        (novo_titulo, conversa_id)
    )
    conn.commit()
    conn.close()
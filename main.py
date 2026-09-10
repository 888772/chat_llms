## importações ##
import streamlit as st
import os
from dotenv import load_dotenv
import requests
import json
import extra_streamlit_components as stx
from streamlit_js_eval import streamlit_js_eval

import auth
import historico

historico.inicializar_banco()
auth.inicializar_tabela_usuarios()

## TOKENS ##

load_dotenv()
#CHAVE_API_OPENROUTER = os.getenv("OPENROUTER_TOKEN")

CHAVE_API_OPENROUTER = st.secrets.get("OPENROUTER_TOKEN") or os.getenv("OPENROUTER_TOKEN")

if CHAVE_API_OPENROUTER:
    print("CHAVE API OPENROUTER FUNCIONANDO")
else:
    print("CHAVE API OPENROUTER NÃO FUNCIONA")
    st.error("⚠️ Token da OpenRouter não encontrado. Verifique seu arquivo .env (chave OPENROUTER_TOKEN).")
    st.stop()

## VARIÁVEIS ##

#modelo_selecionado = ""

## FUNÇÕES ##

SYSTEM_PROMPT = """Você é um assistente de IA útil e direto.

Regras:
- Responda em português, de forma natural e objetiva, sem enrolação.
- Adapte a explicação ao nível do usuário.
- Se pedirem código: dê o código completo e funcional, explique o que mudou, não invente bibliotecas.
- Não dê de forma alguma ou especule o código fonte desse sistema.
- Use Markdown (títulos, listas, código) só quando ajudar a entender.
- Priorize precisão: corrija o usuário se ele errar, e diga "não sei" quando for o caso. Nunca invente fatos, fontes ou links.
- Mantenha o contexto da conversa, não repita perguntas já respondidas.
- Não ajude com nada ilegal ou perigoso; se recusar, explique o motivo e sugira uma alternativa."""

def obter_cookie_manager():
    return stx.CookieManager(key="cookie_manager")

cookie_manager = obter_cookie_manager()

def gerar_resposta_stream(historico):
    mensagens_api = [{"role": "system", "content": SYSTEM_PROMPT}] + historico

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {CHAVE_API_OPENROUTER}",
                "Content-Type": "application/json"
            },
            json={
                "model": st.session_state.modelo_selecionado,
                "messages": mensagens_api,
                "stream": True  # HABILITA STREAMING
            },
            timeout=60,
            stream=True  # Importante no requests tbm
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        yield "⚠️ Timeout na conexão."
        return
    except requests.exceptions.RequestException as e:
        yield f"⚠️ Erro de conexão: {e}"
        return

    full_response = ""
    for line in response.iter_lines():
        if line:
            decoded = line.decode('utf-8').strip()
            if decoded.startswith("data: "):
                data_str = decoded[6:]
                if data_str == "[DONE]": break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk["choices"][0]["delta"]
                    if "content" in delta:
                        token = delta["content"]
                        full_response += token
                        yield token
                except json.JSONDecodeError:
                    continue
    # Opcional: retornar full_response se precisar salvar no histórico fora do generator

## AUTENTICAÇÃO ##

# ---------------- AUTENTICAÇÃO ----------------
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None

if "acabou_de_deslogar" not in st.session_state:
    st.session_state.acabou_de_deslogar = False

# Só tenta login via cookie se NÃO acabou de deslogar agora
if st.session_state.usuario_logado is None and not st.session_state.acabou_de_deslogar:
    cookies = cookie_manager.get_all()
    usuario_cookie = cookies.get("usuario_logado")
    token_cookie = cookies.get("token_login")

    if usuario_cookie and token_cookie:
        if auth.validar_login(usuario_cookie, token_cookie):
            st.session_state.usuario_logado = usuario_cookie

# Reseta a flag depois de checar (só bloqueia por 1 rerun)
st.session_state.acabou_de_deslogar = False

if st.session_state.usuario_logado is None:
    st.title("🔐 Acesso ao LumIA")

    aba_login, aba_registro = st.tabs(["Login", "Criar conta"])

    with aba_login:
        usuario_input = st.text_input("Usuário", key="login_usuario")
        token_input = st.text_input("Token", type="password", key="login_token")
        lembrar = st.checkbox("Manter conectado neste navegador", value=True)

        if st.button("Entrar"):
            if auth.validar_login(usuario_input, token_input):
                st.session_state.usuario_logado = usuario_input

                if lembrar:
                    cookie_manager.set("usuario_logado", usuario_input, key="set_usuario_logado")
                    cookie_manager.set("token_login", token_input, key="set_token_login")
                    import time
                    time.sleep(1)  # dá tempo do JS gravar antes do rerun matar o componente

                st.rerun()
            else:
                st.error("Usuário ou token inválidos.")

    with aba_registro:
        novo_usuario = st.text_input("Escolha um nome de usuário", key="registro_usuario")
        if st.button("Registrar"):
            if not novo_usuario.strip():
                st.warning("Digite um nome de usuário.")
            else:
                token_gerado = auth.registrar_usuario(novo_usuario)
                if token_gerado is None:
                    st.error("Esse nome de usuário já existe. Escolha outro.")
                else:
                    st.success("Conta criada! Guarde seu token — ele não será mostrado de novo:")
                    st.code(token_gerado)

    st.stop()
    
## APLICAÇÃO ###

st.title("LumIA")

if "conversa_id" not in st.session_state:
    conversas = historico.listar_conversas(st.session_state.usuario_logado)
    if conversas:
        st.session_state.conversa_id = conversas[0]["id"]
    else:
        st.session_state.conversa_id = historico.criar_conversa(st.session_state.usuario_logado)

if "messages" not in st.session_state:
    st.session_state.messages = historico.carregar_mensagens(
        st.session_state.conversa_id, st.session_state.usuario_logado
    )

# Inicializar histórico do chat
if "messages" not in st.session_state:
    st.session_state.messages = []

## SIDE BAR ##

# Botão para limpar o histórico da conversa

st.sidebar.header("OPÇÕES:")

if st.sidebar.button("➕ Nova conversa"):
    st.session_state.conversa_id = historico.criar_conversa(st.session_state.usuario_logado)
    st.session_state.messages = []
    st.rerun()

st.sidebar.header("CONVERSAS SALVAS:")
conversas = historico.listar_conversas(st.session_state.usuario_logado)

for c in conversas:
    col_abrir, col_apagar = st.sidebar.columns([4, 1])

    with col_abrir:
        if st.button(f"💬 {c['titulo']}", key=f"abrir_{c['id']}"):
            st.session_state.conversa_id = c["id"]
            st.session_state.messages = historico.carregar_mensagens(
                c["id"], st.session_state.usuario_logado
            )
            st.rerun()

    with col_apagar:
        confirmar_key = f"confirmar_{c['id']}"

        if st.session_state.get(confirmar_key):
            if st.button("✅", key=f"sim_{c['id']}"):
                historico.apagar_conversa(c["id"], st.session_state.usuario_logado)
                st.session_state[confirmar_key] = False

                # Recarrega a lista de conversas depois de apagar
                conversas_restantes = historico.listar_conversas(st.session_state.usuario_logado)

                if st.session_state.conversa_id == c["id"]:
                    if conversas_restantes:
                        # Ainda sobrou conversa: abre a mais recente
                        st.session_state.conversa_id = conversas_restantes[0]["id"]
                        st.session_state.messages = historico.carregar_mensagens(
                            conversas_restantes[0]["id"], st.session_state.usuario_logado
                        )
                    else:
                        # Era a última: cria uma nova vazia
                        st.session_state.conversa_id = historico.criar_conversa(
                            st.session_state.usuario_logado
                        )
                        st.session_state.messages = []

                st.rerun()
        else:
            if st.button("🗑️", key=f"apagar_{c['id']}"):
                st.session_state[confirmar_key] = True
                st.rerun()

# mudar o modelo usado
if "modelo_selecionado" not in st.session_state:
    st.session_state.modelo_selecionado = "inclusionai/ling-3.0-flash-sante:free"  # padrão

st.sidebar.header("MODELO DE IA:")
modelos = {
    "Ling 3.0 Flash Sante (PADRÃO)": "inclusionai/ling-3.0-flash-sante:free",
    "NVIDIA: Nemotron 3 Ultra (lento)": "nvidia/nemotron-3-ultra-550b-a55b:free",
    "Nex AGI: Nex-N2.5-Pro": "nex-agi/nex-n2.5-pro:free",
}

nomes = list(modelos.keys())
indice_atual = nomes.index(
    [k for k, v in modelos.items() if v == st.session_state.modelo_selecionado][0]
)

nome_escolhido = st.sidebar.radio("Escolha o modelo:", nomes, index=indice_atual)
st.session_state.modelo_selecionado = modelos[nome_escolhido]

st.sidebar.markdown(f"👤 Logado como **{st.session_state.usuario_logado}**")
if st.sidebar.button("🚪 Sair"):
    cookie_manager.delete("usuario_logado", key="del_usuario_logado")
    cookie_manager.delete("token_login", key="del_token_login")

    st.session_state.usuario_logado = None
    st.session_state.acabou_de_deslogar = True  # bloqueia login automático nesse próximo rerun

    import time
    time.sleep(5)
    st.rerun()

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input

if st.session_state.usuario_logado is None:
    st.chat_input("Faça login para conversar", disabled=True)
else:
    prompt = st.chat_input("Oque você precisa?")
    if prompt:
        prompt = prompt.strip()
        if not prompt:
            st.warning("Digite algo para continuar.")
            st.stop()

        #CHAT BOX - USER

        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # adicionando chat no histórico
        st.session_state.messages.append({"role": "user", "content": prompt})
        historico.salvar_mensagem(st.session_state.conversa_id, "user", prompt)


        #CHAT BOX - AI

        # Display AI message in chat message container

        with st.chat_message("assistant"):
            with st.spinner(f"{nome_escolhido} Pensando..."):
            # st.write_stream gerencia o placeholder e concatena automaticamente
                resposta_completa = st.write_stream(gerar_resposta_stream(st.session_state.messages))

        st.session_state.messages.append({"role": "assistant", "content": resposta_completa})
        historico.salvar_mensagem(st.session_state.conversa_id, "assistant", resposta_completa)

st.info(f"Você está usando o modelo {nome_escolhido}")
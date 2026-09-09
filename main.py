## importações ##
import streamlit as st
import os
from dotenv import load_dotenv
import requests
import json

## TOKENS ##

load_dotenv()
CHAVE_API_OPENROUTER = os.getenv("OPENROUTER_TOKEN")

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
    
## APLICAÇÃO ###

st.title("LumIA")

# Inicializar histórico do chat
if "messages" not in st.session_state:
    st.session_state.messages = []

## SIDE BAR ##

# Botão para limpar o histórico da conversa

st.sidebar.header("OPÇÕES:")

if st.sidebar.button("🗑️ Limpar conversa"):
    st.session_state.messages = []
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


# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
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


    #CHAT BOX - AI

    # Display AI message in chat message container

    with st.chat_message("assistant"):
        with st.spinner(f"{nome_escolhido} Pensando..."):
        # st.write_stream gerencia o placeholder e concatena automaticamente
            resposta_completa = st.write_stream(gerar_resposta_stream(st.session_state.messages))

    st.session_state.messages.append({"role": "assistant", "content": resposta_completa})

st.info(f"Você está usando o modelo {nome_escolhido}")
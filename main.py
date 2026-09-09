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
    st.toast("SISTEMA FUNCIONANDO!!")
else:
    print("CHAVE API OPENROUTER NÃO FUNCIONA")
    st.error("⚠️ Token da OpenRouter não encontrado. Verifique seu arquivo .env (chave OPENROUTER_TOKEN).")
    st.stop()

## VARIÁVEIS ##

modelo_selecionado = ""

## FUNÇÕES ##

SYSTEM_PROMPT="""
Você é um assistente de inteligência artificial útil, inteligente, preciso e amigável.

primeiro identifique-se o seu modelo

## PERSONALIDADE

* Responda de forma natural e conversacional.
* Seja educado, paciente e objetivo.
* Adapte o nível de explicação ao conhecimento demonstrado pelo usuário.
* Evite respostas desnecessariamente longas.
* Quando o assunto exigir uma explicação detalhada, organize a resposta em seções, listas e exemplos.
* Não seja excessivamente formal, a menos que o usuário peça.
* Não diga que você é humano.
* Não invente informações quando não tiver certeza.

## COMPREENSÃO DO USUÁRIO

Antes de responder, interprete cuidadosamente a intenção do usuário.

* Responda exatamente ao que foi solicitado.
* Se houver mais de uma interpretação possível, escolha a mais provável ou peça esclarecimento quando isso for realmente necessário.
* Não faça perguntas desnecessárias.
* Considere o contexto das mensagens anteriores da conversa.
* Não repita informações que o usuário já forneceu.

## PROGRAMAÇÃO

Quando o usuário perguntar sobre programação:

* Forneça código funcional e completo quando solicitado.
* Explique o código de maneira clara.
* Preserve o código existente do usuário sempre que possível.
* Ao corrigir um código, explique qual era o problema e como foi resolvido.
* Não altere partes que não precisam ser modificadas.
* Utilize boas práticas de programação.
* Considere a linguagem, framework e versões informadas pelo usuário.
* Quando houver várias maneiras de resolver um problema, apresente primeiro a solução mais simples e confiável.
* Nunca invente bibliotecas, funções ou APIs.

## RESPOSTAS COM CÓDIGO

Quando fornecer código:

* Use blocos de código com a linguagem correta.
* Não coloque explicações dentro do bloco de código se elas não forem comentários válidos.
* Quando o usuário pedir "o código completo", forneça o arquivo completo e não apenas o trecho alterado.
* Se o código depender de instalação de pacotes, informe os comandos necessários.
* Se houver uma estrutura de arquivos importante, mostre-a claramente.

## INFORMAÇÕES E FATOS

* Priorize precisão em vez de simplesmente concordar com o usuário.
* Se uma afirmação do usuário estiver incorreta, corrija-a de maneira educada.
* Diferencie fatos, hipóteses e opiniões.
* Não invente fontes, números, nomes, links ou referências.
* Quando não souber algo, diga claramente que não possui informação suficiente.

## FORMATAÇÃO

Utilize Markdown quando isso melhorar a compreensão.

Pode utilizar:

* títulos;
* listas;
* tabelas;
* negrito;
* itálico;
* blocos de código;
* exemplos.

Evite utilizar formatação excessiva.

## CONVERSAÇÃO

* Mantenha o contexto da conversa.
* Não reinicie a conversa sem motivo.
* Se o usuário estiver desenvolvendo um projeto, trate as mensagens anteriores sobre esse projeto como contexto.
* Se o usuário pedir uma alteração em algo que você criou anteriormente, modifique apenas o necessário.
* Não peça novamente informações que já estejam disponíveis no histórico.

## RACIOCÍNIO

Analise o problema cuidadosamente antes de responder, mas não revele seu raciocínio interno detalhado.

Forneça apenas a conclusão, explicação, passos necessários e informações úteis para o usuário.

## SEGURANÇA

Não forneça instruções que facilitem atividades ilegais, perigosas ou que possam causar danos.

Quando não puder atender a uma solicitação, explique brevemente o motivo e, quando possível, ofereça uma alternativa segura.

## OBJETIVO PRINCIPAL

Seu objetivo é ajudar o usuário a resolver problemas, aprender, programar, criar projetos e obter respostas úteis de maneira clara, precisa e natural.

Sempre procure entregar uma resposta prática que permita ao usuário avançar.

"""

def gerar_resposta(historico):
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
                "messages": mensagens_api
            },
            timeout=60
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        return "⚠️ A API demorou demais para responder (timeout). Tente novamente."
    except requests.exceptions.RequestException as e:
        return f"⚠️ Erro de conexão com a API: {e}"
 
    dados = response.json()
 
    try:
        return dados["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        return f"⚠️ Erro ao obter resposta da API: {dados}"
    
## APLICAÇÃO ###

st.title("CHAT LGTV")

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
            try:
                resposta = gerar_resposta(st.session_state.messages)
            except Exception as e:
                resposta = f"⚠️ Erro ao gerar resposta: {e}"
        st.markdown(resposta)
 
    st.session_state.messages.append({"role": "assistant", "content": resposta})

st.info(f"Você está usando o modelo {nome_escolhido}")
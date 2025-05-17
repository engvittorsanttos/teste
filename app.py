# -*- coding: utf-8 -*-
import streamlit as st
import os
from dotenv import load_dotenv
from google import genai
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import Google_Search
from google.genai import types as genai_types # Renomeado para evitar conflito com tipos do streamlit
from datetime import date
import textwrap
import warnings

warnings.filterwarnings("ignore")

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Constante para o ID do Modelo
MODEL_ID = "gemini-2.0-flash" # Ou o modelo que você preferir e tiver acesso

# --- Configuração da API Key e Cliente Gemini ---
def configure_google_api():
    """Configura a API Key do Google e o cliente Gemini."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("Chave de API do Google (GOOGLE_API_KEY) não encontrada no arquivo .env.")
        st.stop()
    try:
        os.environ["GOOGLE_API_KEY"] = api_key # ADK pode precisar disso no ambiente
        genai.configure(api_key=api_key)
        client = genai.Client() # Inicializa o cliente globalmente se necessário, ou passa para agentes
        return client
    except Exception as e:
        st.error(f"Erro ao configurar o cliente Gemini: {e}")
        st.stop()

# --- Funções Auxiliares (Adaptadas do original) ---
def call_agent(agent: Agent, message_text: str, agent_name_for_session: str) -> str:
    """
    Envia uma mensagem para um agente via Runner e retorna a resposta final.
    Usa nomes de sessão únicos para evitar conflitos no InMemorySessionService.
    """
    session_service = InMemorySessionService()
    # Usar um ID de sessão único baseado no nome do agente e um timestamp simples ou contador
    # para evitar colisões se a mesma sessão for recriada rapidamente.
    session_id = f"session_{agent_name_for_session}_{os.urandom(4).hex()}"
    session = session_service.create_session(
        app_name=agent.name, # Ou um nome de app mais geral
        user_id="streamlit_user",
        session_id=session_id
    )
    runner = Runner(agent=agent, app_name=agent.name, session_service=session_service)
    content = genai_types.Content(role="user", parts=[genai_types.Part(text=message_text)])

    final_response = ""
    try:
        for event in runner.run(user_id="streamlit_user", session_id=session_id, new_message=content):
            if event.is_final_response():
                for part in event.content.parts:
                    if part.text is not None:
                        final_response += part.text
                        final_response += "\n"
    except Exception as e:
        st.error(f"Erro durante a execução do agente {agent.name}: {e}")
        return f"Erro ao processar com {agent.name}. Por favor, verifique os logs ou a configuração da API."
    return final_response

# Não é mais estritamente necessário com st.markdown, mas pode ser útil para pré-processamento.
def to_markdown_custom(text):
  text = text.replace('•', '  *') # Adapta marcadores para Markdown
  # Adicionar mais substituições se necessário
  return textwrap.indent(text, '> ', predicate=lambda _: True)


# --- Definições dos Agentes ---

# Agente 1: Buscador de Laudos Periciais
def criar_agente_buscador():
    return Agent(
        name="agente_buscador_streamlit", # Nome único para o agente
        model=MODEL_ID,
        instruction="""
        Você é um Assistente de Pesquisa Técnica e Desenvolvedor de Laudos Periciais na área de Engenharia Civil.
        Sua tarefa é utilizar mecanismos de busca (como o Google Search) para localizar decisões recentes do Tribunal de Justiça que envolvam laudos periciais aprovados ou rejeitados relacionados ao tema indicado.
        Priorize até 5 exemplos relevantes de cada tipo (laudos aceitos e laudos rejeitados), com base na quantidade e qualidade das informações disponíveis sobre cada caso.
        Desconsidere laudos com pouca repercussão ou escassa fundamentação técnica/jurídica publicada, mesmo que tenham sido mencionados em alguma decisão. Substitua-os por casos com maior documentação pública.
        As decisões e laudos analisados devem ser atuais, com data de emissão ou julgamento de no máximo 5 anos da data fornecida.
        A finalidade é identificar padrões técnicos, erros recorrentes e boas práticas que contribuam para a elaboração de laudos mais robustos e alinhados com as exigências dos Tribunais.
        """,
        description="Agente que busca informações no Google para laudos periciais.",
        tools=[Google Search]
    )

# Agente 2: Planejador de Laudos Periciais
def criar_agente_planejador():
    return Agent(
        name="agente_planejador_streamlit",
        model=MODEL_ID,
        instruction="""
        Você é um planejador de laudos periciais, um perito especialista em periciais e normas relacionadas. Com base na lista de laudos mais recentes e relevantes fornecida pelo buscador, você deve:
        1. Usar a ferramenta de busca do Google (Google Search) para encontrar informações adicionais sobre o tema específico do laudo, se necessário, para aprofundar o entendimento.
        2. Identificar e declarar quem provavelmente solicitou o laudo (por exemplo, o juiz em um processo judicial, uma das partes interessadas, uma empresa para fins internos) e o objetivo principal do laudo (ex: avaliação de imóvel para partilha de bens, verificação de vícios construtivos, determinação de valor de mercado para venda, etc.).
        3. Descrever as características essenciais do tipo de imóvel ou situação que seria objeto do laudo (ex: para um imóvel residencial: tamanho do lote, área construída, número de cômodos, estado de conservação geral; para um vício construtivo: tipo de problema, localização, extensão aparente).
        4. Sugerir um método técnico de avaliação ou análise apropriado para o tema (ex: Método Comparativo Direto de Dados de Mercado, Método Evolutivo, Método da Renda para avaliação de imóveis; inspeção visual e ensaios específicos para vícios construtivos). Justifique brevemente a escolha do método.
        5. Com base nas suas pesquisas e expertise, detalhar os pontos mais relevantes a serem investigados e um plano estruturado com os principais tópicos/seções que o laudo final deveria conter.
        Retorne um plano claro e acionável.
        """,
        description="Agente que planeja a estrutura e conteúdo de um laudo pericial.",
        tools=[Google Search]
    )

# Agente 3: Redator do Laudo
def criar_agente_redator():
    return Agent(
        name="agente_redator_streamlit",
        model=MODEL_ID,
        instruction="""
        Você é um Perito Avaliador especialista em engenharia civil e avaliações técnicas.
        Sua função é elaborar um rascunho de parecer pericial, avaliação imobiliária ou laudo técnico, fundamentado no plano de perícia fornecido.
        Utilize o tema e os pontos técnicos relevantes do plano para construir um rascunho de relatório ou laudo que seja claro, preciso e bem fundamentado.
        O conteúdo deve ser técnico, objetivo e embasado em conceitos de engenharia e, implicitamente, em normas técnicas e legislação (embora você não precise citar números de normas específicas, a linguagem e a estrutura devem refletir boas práticas).
        Evite linguagem excessivamente complexa, mas preserve o rigor científico e normativo esperado em um documento técnico.
        Estruture o rascunho com seções lógicas baseadas no plano recebido.
        """,
        description="Agente redator de rascunhos de laudos periciais."
        # Não necessita de tools se apenas processa texto
    )

# Agente 4: Revisor de Qualidade
def criar_agente_revisor():
    return Agent(
        name="agente_revisor_streamlit",
        model=MODEL_ID,
        instruction="""
        Você é um Editor e Revisor Técnico meticuloso, especializado em documentos e laudos periciais na área de engenharia civil.
        Considere o público técnico (engenheiros, arquitetos) e jurídico (advogados, juízes) ao revisar. Seu objetivo é garantir clareza, precisão, concisão e adequação ao padrão normativo e legal vigente (de forma geral, sem precisar verificar normas específicas).
        Revise o rascunho do laudo ou parecer abaixo sobre o tema indicado. Verifique:
        - Coerência técnica e lógica da argumentação.
        - Correção terminológica e uso adequado de jargão técnico.
        - Clareza e objetividade da linguagem.
        - Formalidade e profissionalismo do texto.
        - Ausência de ambiguidades ou informações contraditórias.
        Se o documento estiver tecnicamente consistente, claro, bem escrito e pronto para emissão (considerando que é um rascunho inicial), responda apenas: "O laudo está tecnicamente consistente e pronto para emissão."
        Se houver inconsistências, pontos a melhorar ou sugestões, identifique-os claramente e sugira correções técnicas e formais. Seja específico em suas recomendações.
        """,
        description="Agente revisor de laudos periciais para garantir qualidade e clareza."
        # Não necessita de tools se apenas processa texto
    )


# --- Interface Streamlit ---
st.set_page_config(page_title="Gerador de Laudos Periciais", layout="wide")
st.title("🚀 Sistema de Criação de Laudos Periciais com IA Generativa 🚀")
st.caption("Desenvolvido com Google Gemini e ADK")

# Configurar API e cliente
client = configure_google_api() # Garante que o cliente está configurado

# Obter data atual
data_de_hoje = date.today().strftime("%d/%m/%Y")
st.sidebar.info(f"Data de Referência: {data_de_hoje}")

# Entrada do usuário
topico_laudo = st.text_input("❓ Por favor, digite o TÓPICO sobre o qual você quer criar o laudo pericial:", placeholder="Ex: Avaliação de imóvel residencial urbano para fins de garantia")

if st.button("✨ Gerar Laudo Pericial ✨", type="primary"):
    if not topico_laudo:
        st.warning("⚠️ Por favor, digite um tópico para o laudo.")
    else:
        st.info(f"🔍 Iniciando a criação do laudo sobre: **{topico_laudo}**")

        # Inicializar agentes
        agente_buscador = criar_agente_buscador()
        agente_planejador = criar_agente_planejador()
        agente_redator = criar_agente_redator()
        agente_revisor = criar_agente_revisor()

        with st.spinner("🔄 **Agente Buscador** está pesquisando informações relevantes..."):
            entrada_buscador = f"Tópico: {topico_laudo}\nData de hoje para referência de atualidade: {data_de_hoje}"
            lancamentos_buscados = call_agent(agente_buscador, entrada_buscador, "buscador")
        with st.expander("📝 **Resultado do Agente 1 (Buscador)**", expanded=False):
            if "Erro ao processar" in lancamentos_buscados:
                st.error(lancamentos_buscados)
            else:
                st.markdown(lancamentos_buscados)
        st.success("✅ Agente Buscador concluiu!")
        st.markdown("---")

        if "Erro ao processar" not in lancamentos_buscados:
            with st.spinner("🔄 **Agente Planejador** está elaborando o plano do laudo..."):
                entrada_planejador = f"Tópico do laudo: {topico_laudo}\nInformações e exemplos de laudos buscados: {lancamentos_buscados}"
                plano_de_laudo = call_agent(agente_planejador, entrada_planejador, "planejador")
            with st.expander("🗺️ **Resultado do Agente 2 (Planejador)**", expanded=False):
                if "Erro ao processar" in plano_de_laudo:
                    st.error(plano_de_laudo)
                else:
                    st.markdown(plano_de_laudo)
            st.success("✅ Agente Planejador concluiu!")
            st.markdown("---")

            if "Erro ao processar" not in plano_de_laudo:
                with st.spinner("🔄 **Agente Redator** está escrevendo o rascunho do laudo..."):
                    entrada_redator = f"Tópico central do laudo: {topico_laudo}\nPlano de perícia detalhado: {plano_de_laudo}"
                    rascunho_de_laudo = call_agent(agente_redator, entrada_redator, "redator")
                with st.expander("✍️ **Resultado do Agente 3 (Redator)**", expanded=False):
                    if "Erro ao processar" in rascunho_de_laudo:
                        st.error(rascunho_de_laudo)
                    else:
                        st.markdown(rascunho_de_laudo)
                st.success("✅ Agente Redator concluiu!")
                st.markdown("---")

                if "Erro ao processar" not in rascunho_de_laudo:
                    with st.spinner("🔄 **Agente Revisor** está analisando a qualidade do rascunho..."):
                        entrada_revisor = f"Tópico do laudo: {topico_laudo}\nRascunho do laudo para revisão: {rascunho_de_laudo}"
                        laudo_revisado = call_agent(agente_revisor, entrada_revisor, "revisor")
                    with st.expander("🧐 **Resultado do Agente 4 (Revisor)**", expanded=True): # Expandido por padrão
                        if "Erro ao processar" in laudo_revisado:
                            st.error(laudo_revisado)
                        else:
                            st.markdown(laudo_revisado)
                    st.success("✅ Agente Revisor concluiu!")
                    st.balloons() # Comemoração!
                else:
                    st.error("Processo interrompido devido a erro no Agente Redator.")
            else:
                st.error("Processo interrompido devido a erro no Agente Planejador.")
        else:
            st.error("Processo interrompido devido a erro no Agente Buscador.")

st.sidebar.markdown("---")
st.sidebar.header("Sobre este App")
st.sidebar.info(
    "Este aplicativo utiliza um sistema de múltiplos agentes de IA (Google Gemini + ADK) "
    "para auxiliar na criação de laudos periciais na área de engenharia civil. "
    "Os agentes colaboram em etapas: busca, planejamento, redação e revisão."
)
st.sidebar.markdown("---")
st.sidebar.markdown("Desenvolvido como exemplo.")
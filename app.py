# -*- coding: utf-8 -*-
import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai_module
from datetime import date

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Constante para o ID do Modelo
MODEL_ID = "gemini-1.5-flash"  # Modelo padrão do Gemini

# --- Configuração da API Key e Cliente Gemini ---
def configure_google_api():
    """Configura a API Key do Google e o cliente Gemini."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("Chave de API do Google (GOOGLE_API_KEY) não encontrada no arquivo .env.")
        st.stop()
    try:
        genai_module.configure(api_key=api_key)
        return genai_module.GenerativeModel(MODEL_ID)
    except Exception as e:
        st.error(f"Erro ao configurar o Gemini: {e}")
        st.stop()

# Template do Laudo (Substituir o template existente pelo novo)
LAUDO_PERICIAL_TEMPLATE = """
# LAUDO PERICIAL DE AVALIAÇÃO DE IMÓVEL URBANO
**(Baseado no Tópico: {topico_laudo})**

{dados_processo}

{resumo_laudo}

{resp_tecnico}

{introducao}

{desenvolvimento}

{conclusao}

{anexos}

Local e Data: {local}, {data}
"""

# Atualizar instruções dos agentes
BUSCADOR_INSTRUCTION = """
Você é um Assistente de Pesquisa Técnica especializado em Engenharia Civil.
Gere as seguintes seções do laudo pericial:

1. DADOS DO PROCESSO E IDENTIFICAÇÃO
2. RESUMO DO LAUDO
3. RESPONSÁVEL TÉCNICO

Use como base:
- Processo (se aplicável)
- Classe da ação
- Assunto principal
- Determinação/solicitação
- Objeto da avaliação
- Data de referência
- Métodos utilizados

Mantenha formato técnico e formal.
"""

PLANEJADOR_INSTRUCTION = """
Você é um planejador de laudos periciais.
Desenvolva as seguintes seções:

1. INTRODUÇÃO
   - Contextualização
   - Conformidade legal
   - Limitações e escopo

2. DESENVOLVIMENTO (Seções 4 a 13)
   - Metodologia
   - Vistoria
   - Avaliações
   - Análises técnicas

Use linguagem técnica e profissional.
"""

REDATOR_INSTRUCTION = """
Você é um Perito Avaliador especialista.
Desenvolva as seções finais:

1. CONCLUSÃO (Seções 14 a 17)
   - Valor final
   - Classificação
   - Respostas a quesitos
   - Conclusão final

2. ANEXOS (Seções 21 e 22)
   - Referências
   - Documentação
   - Memória de cálculo
   - Glossário

Use linguagem formal e técnica.
"""

def get_agent_response(model, instruction, message):
    try:
        prompt = f"{instruction}\n\nTópico: {message}\nData: {date.today().strftime('%d/%m/%Y')}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erro ao processar: {str(e)}"

# --- Interface Streamlit ---
st.set_page_config(page_title="Gerador de Laudos", layout="wide")
st.title("Gerador de Laudos Periciais")

# Configurar modelo
model = configure_google_api()

# Obter data atual
data_de_hoje = date.today().strftime("%d/%m/%Y")
st.sidebar.info(f"Data de Referência: {data_de_hoje}")

# Entrada do usuário
topico_laudo = st.text_input("Digite o tópico do laudo:", 
    placeholder="Ex: Avaliação de imóvel residencial")

if st.button("Gerar Laudo", type="primary"):
    if not topico_laudo:
        st.warning("Digite um tópico para o laudo.")
    else:
        with st.spinner("Gerando laudo..."):
            # Processo sequencial
            dados_processo = get_agent_response(model, BUSCADOR_INSTRUCTION, topico_laudo)
            desenvolvimento = get_agent_response(model, PLANEJADOR_INSTRUCTION, topico_laudo)
            conclusao = get_agent_response(model, REDATOR_INSTRUCTION, topico_laudo)

            # Montar laudo final
            laudo_final = LAUDO_PERICIAL_TEMPLATE.format(
                topico_laudo=topico_laudo,
                dados_processo=dados_processo,
                resumo_laudo="## RESUMO DO LAUDO\n" + dados_processo.split("## RESUMO DO LAUDO")[-1].split("##")[0],
                resp_tecnico="## RESPONSÁVEL TÉCNICO\n" + dados_processo.split("## RESPONSÁVEL TÉCNICO")[-1].split("##")[0],
                introducao="## 1. INTRODUÇÃO\n" + desenvolvimento.split("## 1. INTRODUÇÃO")[-1].split("##")[0],
                desenvolvimento="\n".join(desenvolvimento.split("##")[1:]),
                conclusao=conclusao,
                anexos="## ANEXOS\n" + conclusao.split("## ANEXOS")[-1] if "## ANEXOS" in conclusao else "",
                local="Local de Emissão",
                data=date.today().strftime("%d/%m/%Y")
            )

            # Exibir resultado
            st.markdown(laudo_final)
            
            # Opção para download
            st.download_button(
                label="Download do Laudo",
                data=laudo_final,
                file_name=f"laudo_{date.today().strftime('%Y%m%d')}.md",
                mime="text/markdown"
            )

# Sidebar minimalista
with st.sidebar:
    st.markdown("### Sobre")
    st.info("Gerador de laudos periciais usando IA.")
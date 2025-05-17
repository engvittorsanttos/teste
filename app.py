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

# --- Template Hierárquico do Laudo ---
LAUDO_PERICIAL_TEMPLATE = """
# LAUDO PERICIAL DE AVALIAÇÃO DE IMÓVEL URBANO
**(Baseado no Tópico: {topico_laudo})**

## DADOS DO PROCESSO E IDENTIFICAÇÃO (Se aplicável)
- **Processo Nº:** [Agente Planejador: Preencher se a natureza do tópico sugerir um contexto judicial e se informações puderem ser inferidas ou simuladas]
- **Classe da Ação:** [Agente Planejador: Preencher como acima]
- **Assunto Principal:** {topico_laudo}
- **Comarca e Vara:** [Agente Planejador: Preencher como acima]

## RESUMO DO LAUDO
- **Determinação/Solicitação:** [Agente Planejador: Ex: "Laudo elaborado para fins de (finalidade)", ou "Em resposta à solicitação de (solicitante)"]
- **Objeto da Avaliação/Perícia:** {topico_laudo} - [Agente Planejador: Detalhar brevemente, e.g., "Imóvel residencial urbano", "Análise de manifestação patológica em edificação", etc.]
- **Objetivo Principal do Laudo:** [Agente Planejador: Definir com base no tópico, e.g., "Apurar o valor de mercado do bem", "Diagnosticar causas de vícios construtivos"]
- **Finalidade Declarada:** [Agente Planejador: e.g., Judicial, Extrajudicial, Consultoria Técnica, Garantia, etc.]
- **Endereço do Imóvel (se aplicável):** [Agente Buscador/Planejador: Tentar identificar com base no tópico ou simular um endereço plausível]
- **Breve Descrição do Bem (Área do Terreno, Área Edificada - se aplicável):** [Agente Planejador/Redator: Fornecer estimativas ou placeholders se dados exatos não estiverem disponíveis]
- **Data de Referência da Avaliação/Perícia:** {data_de_hoje}
- **Resultado Principal (e.g., Valor Total Estimado, Diagnóstico Principal):** [Agente Redator/Revisor: Será preenchido ao final da análise técnica]
- **Método(s) Principal(is) Utilizado(s):** [Agente Planejador: Listar os métodos que serão conceitualmente aplicados]
- **Tratamento dos Dados (se aplicável):** [Agente Planejador: e.g., Inferência Estatística, Análise Comparativa Qualitativa]

## RESPONSÁVEL TÉCNICO (Exemplo)
- **Nome:** IA Expert Engenharia Consultiva (Gerado por Sistema Multiagentes)
- **Qualificação:** Especialistas em Análise e Avaliações Técnicas com IA
- **CREA/CAU:** N/A (Sistema de IA)
- **Outras Credenciais:** Baseado em Modelos de Linguagem Avançados (Google Gemini)

## 1. INTRODUÇÃO
- **Contextualização:** [Agente Redator: Descrever o propósito do laudo em relação ao {topico_laudo}, mencionando a solicitação (simulada ou real) e o contexto geral. Pode citar a importância de seguir boas práticas e normativas.]
- **Conformidade Legal e Normativa (Referência Genérica):** [Agente Redator: Mencionar que o laudo busca seguir os preceitos técnicos e éticos, referenciando de forma genérica a ABNT NBR 14653 (Avaliação de Bens) e NBR 13752 (Perícias de Engenharia na Construção Civil) como guias de boas práticas, conforme aplicável ao {topico_laudo}.]
- **Limitações e Escopo:** [Agente Planejador/Redator: Definir claramente o que será abordado e quais são as limitações inerentes à análise (e.g., "A presente análise é baseada em informações pesquisadas publicamente e inferências técnicas, não incluindo inspeção física, salvo se explicitamente mencionado e detalhado."). Se o {topico_laudo} for "Avaliação de imóvel X", o escopo é a avaliação. Se for "Vícios construtivos em Y", o escopo é o diagnóstico.]

## 2. SOLICITANTE
- **Nome/Órgão:** [Agente Planejador: Identificar com base no {topico_laudo} ou informações do usuário. Se não especificado, pode ser "Usuário do Sistema de IA" ou "Parte Interessada".]

## 3. INTERESSADOS (Se aplicável e identificável)
- **Parte Autora (se contexto judicial):** [Agente Planejador/Redator: Preencher se aplicável]
- **Parte Ré (se contexto judicial):** [Agente Planejador/Redator: Preencher se aplicável]
- **Outros Envolvidos:** [Agente Planejador/Redator: Preencher se aplicável]

## 4. OBJETO DA PERÍCIA/AVALIAÇÃO
- **Descrição Detalhada:** [Agente Planejador/Redator: Com base no {topico_laudo} e informações do Agente Buscador, descrever o bem ou fato. Ex: "O objeto desta avaliação é um imóvel residencial unifamiliar, padrão médio, localizado em área urbana consolidada..." ou "O objeto desta perícia é a análise de fissuras em paredes de alvenaria de uma edificação comercial..."]

## 5. OBJETIVO ESPECÍFICO
- **Detalhamento:** [Agente Planejador: Com base no {topico_laudo}, detalhar os objetivos. Ex: "1. Identificar as características físicas e de localização do imóvel. 2. Pesquisar dados de mercado de imóveis comparáveis. 3. Aplicar metodologia avaliatória para estimar o valor de mercado." ou "1. Caracterizar as manifestações patológicas. 2. Investigar as prováveis causas. 3. Sugerir recomendações técnicas gerais."]

## 6. METODOLOGIA APLICADA
- **Abordagem Geral:** [Agente Planejador: Descrever a abordagem geral. Ex: "A metodologia consistirá em pesquisa de dados, análise documental (se fornecida), aplicação de métodos consagrados na engenharia diagnóstica/avaliatória e referenciação a normas técnicas pertinentes."]
- **Etapas Principais:**
    - a) Pesquisa e Coleta de Dados: [Agente Planejador: "Levantamento de informações públicas, jurisprudência (pelo Agente Buscador), e dados de mercado relevantes ao {topico_laudo}."]
    - b) Análise e Diagnóstico (ou Avaliação): [Agente Planejador: "Interpretação dos dados coletados, aplicação de raciocínio técnico para (diagnóstico/avaliação) com base no {topico_laudo}."]
    - c) Definição de Métodos: [Agente Planejador: Detalhar os métodos escolhidos e justificar brevemente. Ex: "Para avaliação, será empregado conceitualmente o Método Comparativo Direto de Dados de Mercado, buscando-se elementos amostrais com características semelhantes. Subsidiariamente, o Método Evolutivo ou da Renda poderá ser considerado conceitualmente." Para diagnósticos: "Será utilizada análise causal com base em inspeção visual (simulada/descrita) e conhecimento técnico sobre o comportamento de materiais e sistemas construtivos."]
- **Normas Técnicas de Referência (Principais para o {topico_laudo}):** [Agente Planejador: Listar NBRs mais relevantes. Ex: NBR 14653 (Partes 1, 2, 3), NBR 13752, NBR 5674 (Manutenção), NBR 6118 (Estruturas de Concreto), NBR 15575 (Desempenho), etc.]

## 7. VISTORIA DO BEM (Descrição conceitual, se o {topico_laudo} implicar em vistoria)
- **Simulação de Vistoria:** [Agente Planejador: Se o tópico for, por exemplo, "Avaliação de apartamento na Rua X", descrever como seria uma vistoria típica. "Uma vistoria seria realizada em {data_de_hoje} (data de referência), observando-se aspectos internos e externos do imóvel, padrão de acabamento, estado de conservação aparente, e características da vizinhança."]
- **Aspectos que Seriam Observados:**
    - **Localização e Acesso:** [Agente Buscador/Planejador: Descrever com base em pesquisa ou simulação]
    - **Características da Região (vizinhança, uso predominante):** [Agente Buscador/Planejador]
    - **Infraestrutura Urbana Disponível na Região:** [Agente Buscador/Planejador: Água, esgoto, energia, etc.]

## 8. DESCRIÇÃO GERAL DO IMÓVEL/OBJETO (Detalhar com base no {topico_laudo})
### 8.1. Localização Específica e Confrontações (se aplicável e informações disponíveis)
    - [Agente Buscador/Planejador: Detalhar o endereço se possível, ou descrever uma localização típica para o {topico_laudo}. Confrontações são difíceis de simular sem dados reais.]
### 8.2. Serviços e Infraestrutura Imediata ao Imóvel
    - [Agente Buscador/Planejador: Confirmar os serviços que atendem diretamente o local/imóvel.]
### 8.3. Características Construtivas (para edificações, com base no {topico_laudo})
    - **Tipo da Edificação:** [Agente Planejador/Redator: Casa, apartamento, galpão, etc.]
    - **Padrão Construtivo Estimado:** [Agente Planejador/Redator: Baixo, Normal, Alto, etc., justificando brevemente]
    - **Idade Aparente Estimada:** [Agente Planejador/Redator: Ex: 10 anos, 20 anos]
    - **Estado de Conservação Aparente (Simulado/Inferido):** [Agente Planejador/Redator: Novo, Bom, Regular, Ruim, Péssimo, com breve descrição do que isso implicaria para o {topico_laudo}]
    - **Sistemas Construtivos Principais (Estrutura, Vedação, Cobertura):** [Agente Planejador/Redator: Descrever tipologias comuns para o padrão e tipo de imóvel do {topico_laudo}]
    - **Compartimentação Interna Típica:** [Agente Planejador/Redator: Para um apartamento de 2 quartos: sala, 2 quartos, cozinha, banheiro, área de serviço]
    - **Acabamentos Típicos (Pisos, Paredes, Tetos, Esquadrias, Louças, Metais):** [Agente Planejador/Redator: Descrever acabamentos condizentes com o padrão definido para o {topico_laudo}]
    - **Instalações (Elétrica, Hidráulica, Esgoto, Gás, Climatização - se aplicável):** [Agente Planejador/Redator: Mencionar a existência e o estado aparente (simulado)]
    - **Áreas Comuns (para condomínios, se o {topico_laudo} se referir a um):** [Agente Planejador/Redator]
    - **Documentação Técnica (Situação Ideal):** [Agente Planejador: "Idealmente, para uma análise completa, seriam necessários projetos aprovados (arquitetônico, estrutural, instalações), habite-se, matrícula do imóvel, etc. A ausência ou irregularidade documental pode impactar o valor ou a análise de conformidade."]

## 9. AVALIAÇÃO DAS BENFEITORIAS (Se o {topico_laudo} envolver avaliação de edificações)
### 9.1. Avaliação da Edificação (Conceitual, aplicando o método escolhido)
    - **Método de Custo de Reprodução (Exemplo):**
        - **Custo Unitário Básico (CUB/m²) de Referência:** [Agente Planejador/Redator: Buscar um valor de CUB/m² (Sinduscon do estado apropriado, se possível, para o padrão construtivo e tipo R1, R8, R16, CAL, etc.) ou simular um valor plausível para {data_de_hoje}. Ex: "Adotando CUB/m² Residencial Padrão Normal (R8-N) de R$ XXXX,XX (referência {data_de_hoje})"].
        - **Orçamento para Reprodução da Benfeitoria (Simplificado):** [Agente Redator: Área Construída x CUB/m² (considerar BDI se for detalhar, ou CUB global). Ex: "Custo de Reprodução Novo = Área x CUB = YYY m² x R$ XXXX,XX/m² = R$ ZZZ.ZZZ,ZZ"]
    - **Depreciação (Física, Funcional, Econômica):**
        - **Método de Depreciação Escolhido (e.g., Ross-Heidecke, Linha Reta):** [Agente Planejador/Redator: Ex: "Será aplicada a depreciação pelo critério de Ross-Heidecke, considerando a idade aparente e o estado de conservação simulado."]
        - **Cálculo da Depreciação (Conceitual):** [Agente Redator: Ex: "Considerando idade X e estado Y, o fator de depreciação K é Z. O valor depreciado é Custo Novo x (1-K) = R$ WW.WWW,WW"]
    - **Valor Depreciado da Benfeitoria:** [Agente Redator: Resultado do cálculo acima]

## 10. AVALIAÇÃO DO TERRENO (Se o {topico_laudo} envolver avaliação de terreno ou imóvel completo)
- **Método Aplicado (e.g., Comparativo Direto de Dados de Mercado):** [Agente Planejador]
- **Pesquisa de Mercado (Conceitual):** [Agente Buscador/Planejador: "Seria realizada uma pesquisa por terrenos/imóveis comparáveis na região do objeto, considerando variáveis como área, localização, topografia, testada, etc. Os dados seriam coletados de fontes imobiliárias online, corretores locais e transações recentes, se disponíveis."]
- **Tratamento dos Dados (Conceitual):** [Agente Planejador: "Os dados coletados seriam tratados para homogeneização, ajustando as diferenças entre os elementos da amostra e o imóvel avaliando por meio de fatores ou, se a amostra permitir, por inferência estatística (regressão linear)."]
- **Valor Unitário Médio (R$/m²) Estimado para o Terreno na Região:** [Agente Redator: Com base na pesquisa conceitual, estimar um valor unitário. Ex: "Com base na análise, estima-se um valor de R$ A.AAA,AA/m² para terrenos na região com características similares."]
- **Valor Total do Terreno:** [Agente Redator: Área do Terreno x Valor Unitário Estimado = R$ B.BBB,BB]

## 11. FUNDAMENTAÇÃO TEÓRICA (Breve, se necessário, para métodos mais complexos)
- **Referência à NBR 14653:** [Agente Planejador/Redator: "A NBR 14653 estabelece os procedimentos para avaliação de bens, incluindo a classificação quanto à fundamentação e precisão. Este laudo busca atender a um grau de fundamentação compatível com seu objetivo e as informações disponíveis."]
- **Observações sobre Métodos (se o planejador/redator aprofundar em algum):** [Agente Planejador/Redator]

## 12. IDENTIFICAÇÃO DAS VARIÁVEIS DO MODELO (Se um modelo estatístico for conceitualizado pelo Agente Planejador/Redator)
- **Variável Dependente (e.g., Valor do Imóvel, Valor do m²):** [Agente Planejador/Redator]
- **Variáveis Independentes Consideradas (e.g., Área construída, Área do terreno, Idade, Localização, Padrão):** [Agente Planejador/Redator]

## 13. FORMAÇÃO DO VALOR DE MERCADO (ou Conclusão Diagnóstica)
- **Aplicação dos Métodos (Síntese):**
    - **Pelo Método Comparativo Direto (se aplicável):** [Agente Redator: "Considerando os elementos amostrais e os ajustes (ou modelo estatístico conceitual), o valor de mercado estimado é de R$ XXXXX."]
    - **Pelo Método Evolutivo (se aplicável):** [Agente Redator: "Somando-se o valor do terreno (R$ B.BBB,BB) e o valor depreciado das benfeitorias (R$ WW.WWW,WW), obtém-se R$ YYYYY."]
    - **Pelo Método da Renda (se aplicável ao {topico_laudo}):** [Agente Redator: Conceituar a aplicação]
- **Conciliação dos Valores (se mais de um método foi usado conceitualmente):** [Agente Redator: Justificar o valor final adotado, possivelmente uma média ponderada ou o resultado do método considerado mais robusto para o caso.]
- **Diagnóstico Técnico (para laudos de perícia de engenharia):** [Agente Redator: Apresentar as conclusões sobre as causas, mecanismos de ação e consequências das manifestações patológicas ou problemas analisados no {topico_laudo}.]

## 14. DETERMINAÇÃO DO VALOR TOTAL DO IMÓVEL AVALIANDO (ou Resultado da Perícia)
- **Valor de Mercado Final Estimado (Arredondado conforme NBR 14653):** [Agente Redator: Apresentar o valor final. Ex: "R$ 350.000,00"]
- **Valor por Extenso:** [Agente Redator: Ex: "(Trezentos e cinquenta mil reais)"]
- **Conclusão Pericial Principal (para laudos diagnósticos):** [Agente Redator: Ex: "Conclui-se que as fissuras são decorrentes de movimentação térmica da estrutura, não apresentando risco iminente, mas necessitando de tratamento."]

## 15. CLASSIFICAÇÃO DA AVALIAÇÃO (Conforme NBR 14653 - Simulado)
- **Grau de Fundamentação:** [Agente Planejador/Redator: Atribuir um grau (I, II ou III) e justificar. Ex: "Grau II, considerando a pesquisa de mercado conceitual e aplicação de metodologia padrão, com algumas simplificações devido à natureza da análise por IA."]
- **Grau de Precisão (Se aplicável, especialmente para modelos estatísticos):** [Agente Planejador/Redator: Ex: "Não aplicável para este nível de análise conceitual ou Grau III se um intervalo de confiança for simulado."]

## 16. RESPOSTA A QUESITOS (Se houver quesitos fornecidos no tópico ou simulados)
- **Quesitos do Solicitante/Autor:**
    - **Q1:** [Agente Redator: Formular um quesito pertinente ao {topico_laudo} e responder]
    - **R1:** [Resposta do Agente Redator]
    - ...
- *(Se não houver quesitos, esta seção pode indicar "Não foram apresentados quesitos específicos para este laudo preliminar." O Agente Redator pode também criar alguns quesitos genéricos e respondê-los com base no {topico_laudo})*

## 17. CONCLUSÃO FINAL
- **Síntese dos Achados:** [Agente Redator: Resumir os principais pontos da análise e o resultado final da avaliação/perícia, reiterando o objetivo do laudo e como foi alcançado.]
- **Valor Final Concluído / Diagnóstico Final:** [Agente Redator: Reafirmar o valor ou o diagnóstico principal.]
- **Recomendações (para laudos de perícia diagnóstica):** [Agente Redator: Sugerir ações corretivas, preventivas, monitoramento, etc.]

## 18. PRESSUPOSTOS, RESSALVAS E CONDIÇÕES LIMITANTES
- **Premissas Adotadas:** [Agente Planejador/Redator: Listar as bases da análise. Ex: "As informações de mercado são referências e podem variar.", "A análise de documentos é conceitual, baseada na importância típica de tais documentos."]
- **Limitações do Estudo:** [Agente Planejador/Redator: Ex: "Este laudo é um exercício técnico gerado por IA e não substitui uma perícia/avaliação realizada por profissional habilitado com inspeção in loco.", "Não foram realizados ensaios tecnológicos ou investigações geotécnicas."]
- **Validade do Laudo:** [Agente Planejador/Redator: Ex: "O presente laudo reflete as condições presumidas e informações disponíveis em {data_de_hoje}."]

## 19. DECLARAÇÃO DE CONFORMIDADE (Adaptada)
- [Agente Redator: "Este laudo foi gerado por um sistema de inteligência artificial (Google Gemini com ADK) e busca aplicar princípios técnicos e éticos da engenharia de avaliações e perícias da melhor forma possível dentro de suas capacidades. Os resultados são baseados em algoritmos e dados de treinamento, e devem ser interpretados como uma ferramenta de auxílio e não como um parecer final de um profissional humano habilitado para todas as finalidades legais ou formais sem a devida validação."]

## 20. FINALIZAÇÃO
- **Considerações Finais:** [Agente Redator: "Este sistema está em contínuo desenvolvimento. Agradecemos a oportunidade de auxiliar na análise do tópico: {topico_laudo}."]
- **Local e Data:** Gerado computacionalmente em {data_de_hoje}.
- **Assinatura (Simbólica):**
    - Sistema Multiagentes de IA para Laudos Técnicos
    - (Google Cloud Vertex AI / Gemini Models)

## 21. REFERÊNCIAS BIBLIOGRÁFICAS (Exemplos que os agentes podem citar)
- ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS (ABNT). NBR 14653: Avaliação de bens (Partes relevantes ao {topico_laudo}). Rio de Janeiro, ABNT.
- ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS (ABNT). NBR 13752: Perícias de engenharia na construção civil. Rio de Janeiro, ABNT.
- [Agente Planejador/Redator: Adicionar outras NBRs ou referências genéricas de livros de engenharia de avaliações, patologia das construções, etc., conforme o {topico_laudo}.]

## 22. ANEXOS (Descrição do que conteria)
- **Anexo I – Documentação Fotográfica Ilustrativa (Conceitual):** [Agente Redator: Descrever que tipo de fotos seriam relevantes para o {topico_laudo}. Ex: "Fachada, interiores, detalhes construtivos, manifestações patológicas, vizinhança."]
- **Anexo II – Memória de Cálculo Detalhada (Conceitual):** [Agente Redator: "Detalhamento dos cálculos de avaliação de benfeitorias, terreno, ou outros cálculos pertinentes ao {topico_laudo}."]
- **Anexo III – Elementos da Pesquisa de Mercado (Conceitual):** [Agente Redator: "Listagem e caracterização dos imóveis/dados comparáveis utilizados na análise (se aplicável)."]
- **Anexo IV – Glossário Técnico (Opcional):** [Agente Redator: "Definição de termos técnicos utilizados no laudo para melhor compreensão."]

"""

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

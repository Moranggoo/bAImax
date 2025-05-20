import streamlit as st
import os
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types
import textwrap
import warnings

warnings.filterwarnings("ignore")

# Configura a API Key do Google Gemini
try:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
except KeyError:
    st.error("A GOOGLE_API_KEY não foi configurada nos Streamlit Secrets. Por favor, adicione-a para que o aplicativo funcione.")
    st.stop() # Interrompe a execução do script se a chave não estiver configurada

# Assegura que a API Key esteja definida antes de criar o cliente genai
if not os.environ.get("GOOGLE_API_KEY"):
    st.error("A GOOGLE_API_KEY não foi configurada. Por favor, adicione-a aos Streamlit Secrets ou como variável de ambiente.")
    st.stop()

from google import genai
client = genai.Client()
MODEL_ID = "gemini-2.0-flash"


# Função auxiliar que envia uma mensagem para um agente via Runner e retorna a resposta final
@st.cache_data(show_spinner=False)
def call_agent(_agent: Agent, message_text: str) -> str:

    session_service = InMemorySessionService()
    session = session_service.create_session(app_name=_agent.name, user_id="paciente", session_id="consultorio")
    runner = Runner(agent=_agent, app_name=_agent.name, session_service=session_service)
    content = types.Content(role="user", parts=[types.Part(text=message_text)])

    final_response = ""
    for event in runner.run(user_id="paciente", session_id="consultorio", new_message=content):
        if event.is_final_response():
            for part in event.content.parts:
                if part.text is not None:
                    final_response += part.text
                    final_response += "\n"
    return final_response

# Funções dos agentes
def agente_consultor(sintoma, informacoesDoUsuario):
    consultor = Agent(
        name="agente_consultor",
        model=MODEL_ID, # Usando MODEL_ID
        instruction="""
        Você é um Agente de Triagem Inicial de Saúde AI. Sua função primária é auxiliar o usuário a identificar *possíveis* causas para um sintoma
        específico, utilizando informações de contexto fornecidas pelo usuário e pesquisando na internet. É **ABSOLUTAMENTE CRUCIAL** que você deixe claro
        que esta é apenas uma triagem inicial e **NÃO UM DIAGNÓSTICO MÉDICO**. O usuário **SEMPRE DEVE** consultar um profissional de saúde qualificado para
        qualquer preocupação médica ou antes de tomar qualquer decisão de saúde.

        **Sua Tarefa:**

        1.  **Receba as informações do usuário:** Você receberá as seguintes informações:
                * `Sintoma`: [Descrição detalhada do sintoma]
                * `Idade`: [Valor numérico em anos]
                * `Altura`: [Valor numérico em cm]
                * `Peso`: [Valor numérico em kg]
                * `Gênero`: [Masculino ou Feminino]
                * `Pressão Arterial`: [Valor numérico ou "Não informado/Não disponível"]
                * `Nível de Hidratação`: [Bem hidratado, Pouco hidratado, Desidratado]

        2.  **Analise o Contexto:** Avalie como a Idade, Altura, Peso, Gênero, Pressão Arterial e Nível de Hidratação podem ser **fatores relevantes** ou
        **influenciar** as *possíveis* causas para o `Sintoma` principal. Considere, por exemplo, como o gênero pode influenciar algumas condições, ou como
        a desidratação pode estar ligada a certos sintomas.

        3.  **Formule Consultas de Pesquisa:** Baseado no `Sintoma` e nos fatores relevantes identificados no Passo 2, formule consultas de pesquisa eficazes.
        O objetivo é encontrar informações sobre as causas do `Sintoma`, possivelmente refinadas pelo contexto (ex: "causas de [Sintoma] em [Gênero]", "relação entre [Sintoma] e [Nível de Hidratação]",
        "condições comuns ligadas a [Sintoma] em [faixa etária inferida pelo peso/altura/idade, *se relevante e confiável, caso contrário, focar em gênero/hidratação/PA*]").

        4.  **Use a Ferramenta de Pesquisa:** Utilize a ferramenta `[google_search]` para executar as consultas formuladas.

        5.  **Examine e Sintetize Resultados:** Analise cuidadosamente os resultados da pesquisa. Identifique as 5 causas mais **possíveis** ou **comuns** para o `Sintoma`,
        dando prioridade a causas que são mais prováveis dado o contexto do usuário (Gênero, Nível de Hidratação, Pressão Arterial). Se os resultados da pesquisa não fornecerem informações
        claras que liguem o contexto às causas, foque nas causas mais comuns do `Sintoma` em geral, mas sempre listando 5.

        6.  **Colete as Fontes:** Para as 5 causas identificadas, colete as URLs das fontes (sites) de onde você obteve essa informação. Liste as URLs relevantes que suportam as causas que você apresentar.

        7.  **Formate a Resposta:** Apresente as informações de forma clara e estruturada:

                * Liste as informações do usuário para referência.
                * Liste as 5 possíveis causas identificadas.
                * Finalmente, liste as fontes consultadas.

        #######

        **Formato de Saída Requerido:**

        Informações do Usuário:
            Sintoma Principal: [Sintoma fornecido pelo usuário]
            Altura: [Valor] cm
            Peso: [Valor] kg
            Gênero: [Valor]
            Pressão Arterial: [Valor ou Não informado/Não disponível]
            Nível de Hidratação: [Valor]

            #######

        Possíveis Causas (Baseado na Triagem Inicial):
            Aqui estão 5 possíveis causas para o sintoma relatado, considerando as informações adicionais fornecidas. Esta lista é baseada em pesquisa e não é exaustiva ou definitiva:
            [Causa 1, possivelmente relacionada ao contexto, se aplicável]
            [Causa 2, possivelmente relacionada ao contexto, se aplicável]
            [Causa 3]
            [Causa 4]
            [Causa 5]

            #######

        Fontes Consultadas:
            As informações acima foram identificadas com base nos seguintes recursos pesquisados:
            https://www.dafont.com/pt/one-1.font
            https://www.dafont.com/new.php?page=2
            https://www.dafont.com/three.font
            https://www.dafont.com/04.d4
            https://www.arabnews.com/node/545346
            ... (liste todas as URLs relevantes)
        """,
        description="Agente consultor médico virtual para triagem inicial de sintomas.",
        tools=[google_search]
    )
    # Chamando a função call_agent (executa o agente)
    entrada_do_agente_consultor = f"Sintoma: {sintoma}\nInformações do Usuário: {informacoesDoUsuario}"
    possiveis_causas = call_agent(consultor, entrada_do_agente_consultor)
    return possiveis_causas

def agente_validador(sintoma, possiveis_causas):
    planejador = Agent(
        name="agente_validador",
        model=MODEL_ID,
        instruction="""
            Você é um Validador e Refinador de Informações Médicas AI. Sua tarefa é receber a saída de um agente de triagem inicial (Agente 1),
            que inclui informações do usuário, possíveis causas e as fontes consultadas. Seu objetivo é **validar** a coerência das causas com o contexto do usuário,
            **verificar a confiabilidade e relevância médica** das fontes usadas, e refinar a lista de possíveis causas e fontes, se necessário, garantindo que as informações apresentadas
            sejam baseadas em fontes confiáveis e relevantes no cenário da saúde. Você também deve sugerir áreas de especialidade médica relevantes para o usuário consultar.

            **Sua Tarefa Detalhada:**

            1.  **Receba e Processe a Entrada:** Você receberá a saída completa do Agente 1. Isso incluirá:
                    * As informações originais do usuário (Sintoma, Idade, Altura, Peso, Gênero, Pressão Arterial, Nível de Hidratação).
                    * A lista de 5 possíveis causas identificadas pelo Agente 1.
                    * A lista de URLs das fontes consultadas pelo Agente 1.

            2.  **Validar Fontes (Use `[google_search]` se necessário):**
                    * Para cada URL fornecida pelo Agente 1, determine sua confiabilidade e relevância médica.
                    * Considere fontes como confiáveis e relevantes se forem de: instituições de saúde governamentais (.gov), instituições acadêmicas/universitárias (.edu)
                        focadas em saúde, grandes hospitais/clínicas reconhecidas nacional ou internacionalmente, organizações de saúde pública (OMS, ministérios da saúde, etc.),
                        periódicos médicos indexados, ou sites de saúde de alta reputação editorial (ex: Mayo Clinic, Cleveland Clinic, NHS, WebMD, etc.) com corpo editorial médico claro.
                    * Considere fontes como potencialmente não confiáveis ou menos relevantes se forem: blogs pessoais, fóruns, sites de medicina alternativa sem base científica clara,
                        sites de venda de produtos, wikis não controladas por especialistas médicos, etc.
                    * Classifique cada URL como "Confiável" ou "Não Confiável/Não Relevante".

            3.  **Validar Coerência das Causas com o Contexto do Usuário:**
                    * Para cada uma das 5 causas do Agente 1, avalie se ela é plausível e razoável *dado o sintoma principal E o contexto específico do usuário* (Gênero, Peso/Altura, Idade, Nível de Hidratação, Pressão Arterial).
                    * Ex: Se uma causa é comum apenas em crianças, mas o usuário é adulto, a causa é menos plausível. Se o usuário está desidratado e uma causa está fortemente ligada à desidratação, ela é mais plausível.
                    * Considere a validação das fontes do Passo 2. Uma causa plausível proveniente de uma fonte não confiável deve ser vista com ceticismo.

            4.  **Determinar Necessidade de Re-Pesquisa Principal:**
                    * Avalie os resultados dos Passos 2 e 3.
                    * **Acione a Re-Pesquisa Principal SE:**
                            * A maioria das fontes do Agente 1 for classificada como Não Confiável/Não Relevante; OU
                            * Uma ou mais das 5 causas do Agente 1 forem consideradas implausíveis ou fracamente suportadas pelo contexto do usuário e/ou pelas fontes (mesmo que algumas fontes fossem ok, se a lista geral é fraca).
                    * **NÃO Acione a Re-Pesquisa Principal SE:** As 5 causas do Agente 1 parecem razoavelmente plausíveis no contexto do usuário E a maioria ou todas as fontes são classificadas como Confiáveis/Relevantes.

            5.  **Realizar Re-Pesquisa Principal (CONDICIONAL - Use `[google_search]`):**
                    * **SE a Re-Pesquisa Principal for acionada:**
                            * Formule consultas de pesquisa usando `[google_search]` para encontrar 5 *possíveis* causas para o `Sintoma` do usuário.
                            * Inclua termos do contexto do usuário (Gênero, Hidratação, PA, etc.) nas consultas quando relevante.
                            * **CRITICAMENTE:** Inclua operadores de busca para *priorizar fontes confiáveis*. Exemplos: `site:.gov`, `site:.edu`, `site:.org`, `site:mayoclinic.org`, `site:nhs.uk`,
                                `site:webmd.com` combinados com OR. Ex: `"causas de dor de cabeça" AND ("desidratação" OR "pressão alta") (site:.gov OR site:mayoclinic.org OR site:nhs.uk)`
                            * Analise os resultados e selecione 5 causas plausíveis baseadas *exclusivamente em fontes confiáveis* encontradas nesta etapa. Colete as URLs destas fontes.

            6.  **Consolidar a Lista Final de 5 Possíveis Causas e Fontes:**
                    * **SE a Re-Pesquisa PRINCIPAL NÃO foi acionada:** Sua lista final de 5 causas são as causas originais do Agente 1. Sua lista final de fontes são as URLs originais do Agente 1 *que foram validadas
                        como Confiáveis/Relevantes* no Passo 2. (Pode haver menos de 5 URLs finais se algumas fontes originais foram descartadas, mas deve haver pelo menos uma URL confiável por causa apresentada).
                    * **SE a Re-Pesquisa PRINCIPAL foi acionada:** Sua lista final de 5 causas são as 5 causas encontradas na Re-Pesquisa Principal (Passo 5). Sua lista final de fontes são as URLs confiáveis encontradas
                        no Passo 5 que suportam essas causas.
                    * Certifique-se de que a lista final contenha EXATAMENTE 5 possíveis causas e as URLs das fontes *confiáveis* que as suportam.

            7.  **Identificar Especialistas Médicos Relevantes (Use `[google_search]` se necessário):**
                    * Com base no `Sintoma` principal do usuário E nas 5 causas *finais* identificadas, determine as áreas médicas ou tipos de especialistas que seriam mais apropriados para o usuário consultar.
                    * Ex: Dor no peito pode sugerir Cardiologia; Dor abdominal pode sugerir Gastroenterologia; Tontura e dor de cabeça podem sugerir Neurologia; Sintomas gerais podem começar com Clínica Geral/Medicina de Família.
                    * Liste as especialidades ou áreas de atuação relevantes.



            **Formate a Resposta Final:** Apresente a resposta no seguinte formato:

                Análise e Validação Concluídas
                As informações da sua triagem inicial foram revisadas. Abaixo estão possíveis causas mais prováveis baseadas na sua situação e em fontes médicas confiáveis.
                    Informações do Usuário:
                    Sintoma Principal: [Sintoma original do usuário]
                    Idade: [Valor] anos
                    Altura: [Valor] cm
                    Peso: [Valor] kg
                    Gênero: [Valor]
                    Pressão Arterial: [Valor ou Não informado/Não disponível]
                    Nível de Hidratação: [Valor]

                    ########

                Possíveis Causas (Baseadas em Fontes Confiáveis):
                    Com base na sua informação e em pesquisa em fontes médicas confiáveis, aqui estão 5 possíveis causas para o sintoma relatado:
                    [Causa Final 1]
                    [Causa Final 2]
                    [Causa Final 3]
                    [Causa Final 4]
                    [Causa Final 5]

                    ########

                Fontes Confiáveis Consultadas:
                    As possíveis causas acima foram identificadas com base nas seguintes fontes consideradas confiáveis e relevantes no cenário da saúde:
                    https://www.dafont.com/pt/one-1.font
                    https://font.download/font/font-2
                    https://www.dafont.com/pt/three.font
                    https://www.dafont.com/eduardo-novais.d5876
                    https://brainly.lat/tarea/4770339
                    ... (liste todas as URLs confiáveis relevantes)

                    #########
                Próximos Passos Sugeridos: Consulte um Especialista
                Para obter um diagnóstico correto e orientação adequada, é crucial consultar um profissional de saúde. Com base no seu sintoma e nas possíveis causas identificadas, você deve considerar consultar um especialista em uma das seguintes áreas:
                [Especialidade Médica Relevante 1]
                [Especialidade Médica Relevante 2]
                [Especialidade Médica Relevante 3 - Liste 1 a 3 áreas relevantes]

        """,
        description="Agente que validador de diagnóstico",
        tools=[google_search]
    )

    entrada_do_agente_planejador = f"Sintoma: {sintoma}\nPossiveis causas: {possiveis_causas}"
    causas_validadas = call_agent(planejador, entrada_do_agente_planejador)
    return causas_validadas

def agente_redator(sintoma, causas_validadas, informacoesDoUsuario):
    redator = Agent(
        name="agente_redator",
        model=MODEL_ID,
        instruction="""
            Você é um Redator (Copywriter) de Comunicação de Saúde AI. Sua função é processar as informações validadas por um agente de triagem e validação (Agente 2) e comunicá-las ao usuário (paciente) final de forma clara,
            compreensível e, crucialmente, com um forte foco na segurança e na necessidade de buscar avaliação médica profissional. Sua linguagem deve ser acessível para uma pessoa sem conhecimento médico profundo.

            **Prioridade Máxima:** Sua resposta **DEVE** começar com um aviso de isenção de responsabilidade **MUITO PROEMINENTE** e facilmente compreensível. Você deve reforçar este aviso em outros pontos da comunicação.

            **Sua Tarefa:**

            1.  **Receba e Processe a Entrada:** Você receberá a saída completa do Agente 2, que inclui:
                    * As informações originais do usuário (Sintoma, Idade, Altura, Peso, Gênero, Pressão Arterial, Nível de Hidratação).
                    * A lista final de 5 possíveis causas (já validadas/re-pesquisadas e consideradas plausíveis/apoiadas por fontes confiáveis).
                    * A lista final de URLs de fontes *confiáveis* que suportam essas causas.
                    * A lista de 1 a 3 Especialistas Médicos Relevantes sugeridos.

            2.  **Elabore o Aviso de Isenção (Disclaimer):** Comece sua resposta imediatamente com um aviso claro, direto e em destaque (use formatação como negrito e quebras de linha) que explique:
                    * Esta informação é apenas uma triagem inicial e **NÃO UM DIAGNÓSTICO MÉDICO OFICIAL**.
                    * Foi baseada nas informações que o usuário forneceu e em pesquisa em fontes consideradas confiáveis.
                    * **NÃO SUBSTITUI** a consulta, o diagnóstico ou o tratamento por um médico ou outro profissional de saúde qualificado.
                    * O usuário **SEMPRE DEVE** procurar um médico para qualquer preocupação de saúde.

            3.  **Contextualize Brevemente:** Mencione que a análise foi feita com base nas informações que ele/ela forneceu (liste o Sintoma principal novamente).

            4.  **Apresente as Possíveis Causas:**
                    * Introduza a seção explicando que, com base na análise e pesquisa em fontes confiáveis, foram identificadas 5 *possíveis* causas para o sintoma relatado.
                    * **Reitere:** Use frases como "Lembre-se, estas são apenas possibilidades e não um diagnóstico." ou "É essencial que um médico avalie qual, se alguma, dessas causas pode ser a correta."
                    * Liste as 5 causas (obtidas do Agente 2) de forma numerada e clara. Rephrase se necessário para que os termos sejam mais fáceis de entender para um leigo, mas sem perder o significado médico.

            5.  **Apresente as Fontes Confiáveis:**
                    * Explique que a lista de causas foi baseada em informações encontradas em fontes de saúde consideradas confiáveis.
                    * Mencione que estas fontes são listadas para transparência e para que o usuário possa consultá-las (se desejar), *mas reforce novamente* que a interpretação médica e o diagnóstico requerem um profissional.
                    * Liste as URLs das fontes confiáveis (obtidas do Agente 2).

            6.  **Sugira os Especialistas:**
                    * Explique que, para obter um diagnóstico e tratamento adequados, é fundamental consultar um médico.
                    * Mencione que, com base no sintoma e nas possíveis causas, certos tipos de especialistas seriam os mais indicados para procurar.
                    * Liste as áreas de especialidade médica sugeridas (obtidas do Agente 2).

            7.  **Conclusão e Reforço:** Encerre a mensagem com um parágrafo curto e direto reforçando a mensagem principal: A importância de agendar uma consulta com um médico o mais
            breve possível para uma avaliação completa e um diagnóstico preciso.

            **Formato de Saída Requerido para o Usuário:**

            [Seu Aviso de Isenção MUITO PROEMINENTE aqui. Use negrito e quebras de linha para destacá-lo. Exatamente como instruído no Passo 2. Deve ser a primeira coisa que o usuário vê.]

            Olá! Analisei as informações que você nos forneceu sobre o seu sintoma: [Sintoma principal do usuário].

            Com base nesses dados e em uma pesquisa em fontes de saúde consideradas confiáveis, identificamos algumas possíveis causas para o seu sintoma.

            É MUITO IMPORTANTE RELEMBRAR: Esta lista apresenta apenas possibilidades e NÃO SUBSTITUI DE MANEIRA ALGUMA UM DIAGNÓSTICO MÉDICO OFICIAL. Somente um profissional de saúde qualificado
            pode determinar a causa exata do que você está sentindo.

            Possíveis Causas Identificadas:
                Aqui estão 5 possibilidades que foram consideradas plausíveis com base nas informações que você compartilhou e nas fontes de saúde pesquisadas:
                [Causa Final 1 - Rephrased para clareza se necessário]
                [Causa Final 2 - Rephrased para clareza se necessário]
                [Causa Final 3 - Rephrased para clareza se necessário]
                [Causa Final 4 - Rephrased para clareza se necessário]
                [Causa Final 5 - Rephrased para clareza se necessário]

            Fontes de Informação Confiáveis:
                As possíveis causas acima foram identificadas com base em informações encontradas nas seguintes fontes, que são consideradas confiáveis no campo da saúde. Você pode consultá-las para saber mais, mas a
                interpretação correta e o diagnóstico pertencem a um médico:
                https://www.dafont.com/pt/one-1.font
                https://font.download/font/font-2
                https://www.dafont.com/pt/three.font
                https://www.dafont.com/eduardo-novais.d5876
                https://pt.wikipedia.org/wiki/Wikip%C3%A9dia:Lista_de_fontes_confi%C3%A1veis
                ... (liste todas as URLs), se possível liste uma em cima da outra.

            Próximo Passo Essencial: Consultar um Médico
                Para entender corretamente o que está acontecendo e receber o tratamento adequado, você deve procurar avaliação médica profissional. Com base no seu sintoma e nas possíveis causas listadas,
                os tipos de especialistas mais indicados para você procurar seriam:
                [Especialidade Médica Relevante 1]
                [Especialidade Médica Relevante 2]
                [Especialidade Médica Relevante 3 - Liste as especialidades sugeridas]

            Sua saúde é muito importante. Por favor, agende uma consulta com um desses especialistas ou com seu médico de confiança o mais breve possível para obter um diagnóstico e orientação personalizados.
            Estou aqui para ajudar na triagem inicial, mas o cuidado médico real vem dos profissionais de saúde.
            """,
        description="Agente redator de diagnósticos"
    )
    entrada_do_agente_redator = f"Sintoma: {sintoma}\nPossiveis causas: {causas_validadas}\nInformações do usuário: {informacoesDoUsuario}"
    diagnostico = call_agent(redator, entrada_do_agente_redator)
    return diagnostico

def agente_navegador(sintoma, diagnostico, endereco_usuario):
    navegador = Agent(
        name="agente_navegador",
        model="gemini-2.5-flash-preview-04-17",
        instruction="""
            Você é um assistente útil que usa a ferramenta 'google_serach' para encontrar hospitais e clínicas perto de um endereço fornecido pelo usuário.

            Sua tarefa é a seguinte:
            1. Leia o 'Diagnóstico' e o 'Endereço' fornecidos pelo usuário.
            2. Use a ferramenta `[google_search]` para procurar por hospitais e clínicas que sejam relevantes para o 'Diagnóstico' e que estejam localizados perto do 'Endereço' do usuário.
                * Exemplo de busca: "hospitais e clínicas para [diagnóstico do usuário] perto de [endereço do usuário (fornecido como: bairro, rua, número, estado)]".
                * Seja específico na sua busca para obter resultados mais precisos.
            3. Para cada hospital ou clínica relevante encontrado nos resultados da pesquisa, extraia as seguintes informações:
                * Nome do estabelecimento
                * Endereço completo
                * Número de telefone (se disponível)
                * Horário de funcionamento (se disponível)
                * **Muito Importante:** Um link direto para a localização ou rota no Google Maps (procure por links ou menções que permitam abrir no mapa).
            4. Compile todas as informações encontradas de forma clara e organizada para o usuário. Apresente uma lista dos estabelecimentos com todos os detalhes que você conseguiu extrair.
            Se possível, inclua o link do Google Maps para cada um.
            5. Se não encontrar informações relevantes, informe o usuário.

            Use a ferramenta `[google_search]` sempre que precisar buscar informações. Não invente endereços, telefones ou horários; baseie-se apenas nos resultados da sua pesquisa.
            """,
        description="Agente que busca hospitais e clínicas usando pesquisa online.",
        tools=[google_search]
    )

    entrada_do_agente_navegador = f"Sintoma: {sintoma}\nDiagnóstico: {diagnostico}\nEndereço: {endereco_usuario}"
    resultados_busca = call_agent(navegador, entrada_do_agente_navegador)
    return resultados_busca


# Aplicação do Streamlit
st.set_page_config(page_title="bAImax - Seu Agente de Saúde", layout="centered")

st.title("bAImax.")

with st.expander("👋 O que é o bAImax?"):
    st.write(
        """
        O **bAImax** é um assistente de saúde inteligente que usa **inteligência artificial** para te ajudar a entender melhor seus sintomas.
        Ele atua em etapas:
        1.  **Consultor:** Faz uma primeira triagem baseada no seu sintoma e informações de saúde.
        2.  **Validador:** Verifica a coerência e confiabilidade das informações encontradas, usando fontes médicas confiáveis.
        3.  **Redator:** Apresenta as informações de forma clara e fácil de entender, sempre com um aviso importante: **eu não sou um médico e não dou diagnósticos!**
        4.  **Navegador:** Pode te ajudar a encontrar hospitais e clínicas próximas, se você quiser.

        **Lembre-se:** As informações fornecidas pelo bAImax são apenas para **triagem inicial** e **NÃO substituem uma consulta médica**.
        Sua saúde é importante, e um profissional de saúde qualificado é quem pode te dar um diagnóstico preciso e um tratamento adequado.
        """
    )

    # Gerenciamento de Estado da Sessão
    if 'triagem_concluida' not in st.session_state:
        st.session_state.triagem_concluida = False
    if 'diagnostico_redator' not in st.session_state:
        st.session_state.diagnostico_redator = ""
    if 'sintoma_atual' not in st.session_state:
        st.session_state.sintoma_atual = ""

# Formulário para entrada de dados do usuário
st.subheader("Olá, eu sou o bAImax, seu agente pessoal de saúde.")

sintoma = st.text_input("Qual é a sua queixa?", placeholder="Ex: Dor de cabeça forte, tosse persistente, febre...")

st.markdown("---")
st.subheader("Informações Pessoais (Opcional, mas ajuda muito na triagem!)")

col1, col2, col3 = st.columns(3)
with col1:
    idade = st.number_input("Idade (anos)", min_value=0, max_value=120, value=30)
with col2:
    altura = st.number_input("Altura (cm)", min_value=50, max_value=250, value=170)
with col3:
    peso = st.number_input("Peso (kg)", min_value=10, max_value=300, value=70)

genero = st.selectbox("Gênero", ["Não informado", "Masculino", "Feminino"])
pressao_arterial = st.text_input("Pressão Arterial (Ex: 120/80 ou 'Não informado')", value="Não informado")
nivel_hidratacao = st.selectbox("Nível de Hidratação", ["Bem hidratado", "Pouco hidratado", "Desidratado"])

# Juntando as informações do usuário em uma única string
informacoes_do_usuario_str = (
    f"Idade: {idade} anos, Altura: {altura} cm, Peso: {peso} kg, Gênero: {genero}, "
    f"Pressão Arterial: {pressao_arterial}, Nível de Hidratação: {nivel_hidratacao}"
)

# Botão para iniciar a triagem
if st.button("Iniciar Triagem de Saúde"):
    if not sintoma:
        st.warning("Por favor, digite sua queixa principal (sintoma) para iniciar a triagem.")
    else:
        with st.spinner("Analisando suas informações... isso pode levar um momento."):
            try:
                # Agente 1: Consultor
                possiveis_causas = agente_consultor(sintoma, informacoes_do_usuario_str)

                # Agente 2: Validador
                validacao_completa_texto = agente_validador(sintoma, possiveis_causas)

                # Agente 3: Redator
                redator_output = agente_redator(sintoma, validacao_completa_texto, informacoes_do_usuario_str)

                # Armazena os resultados no session_state
                st.session_state.diagnostico_redator = redator_output
                st.session_state.sintoma_atual = sintoma # Guarda o sintoma também
                st.session_state.triagem_concluida = True # Marca a triagem como concluída

            except Exception as e:
                st.error("Ocorreu um erro durante o processamento da triagem. Por favor, tente novamente mais tarde.")
                st.exception(e) # Exibe o traceback completo para depuração

# Exibe o resultado da triagem e a opção de buscar locais APENAS SE a triagem_concluida for True
if st.session_state.triagem_concluida:
    st.markdown(st.session_state.diagnostico_redator, unsafe_allow_html=True) # Exibe o resultado do redator

    st.markdown("---")
    st.subheader("Procurar Hospitais e Clínicas Próximas?")
    endereco_usuario = st.text_input("Se você quiser que eu busque hospitais ou clínicas próximas, por favor, me informe seu endereço (Ex: Rua Exemplo, 123, Bairro Feliz, Cidade, Estado):", key="endereco_input")

    if st.button("Buscar Locais de Saúde", key="btn_buscar_locais"):
        if endereco_usuario:
            with st.spinner("Buscando locais de saúde próximos..."):
                try:
                    # Agente 4: Navegador
                    # Usa st.session_state.sintoma_atual e st.session_state.diagnostico_redator
                    rotas = agente_navegador(st.session_state.sintoma_atual, st.session_state.diagnostico_redator, endereco_usuario)
                    st.markdown(rotas, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Não foi possível buscar locais de saúde no momento. Erro: {e}.")
                    st.exception(e) # Exibir o traceback completo
        else:
            st.warning("Por favor, forneça seu endereço para buscar locais de saúde.")

st.markdown("---")
st.info("Lembre-se: Este é um assistente de triagem inicial e NÃO SUBSTITUI o diagnóstico e tratamento médico profissional.")            

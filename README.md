# bAImax - Seu Agente Pessoal de Triagem de Saúde

[![Generic badge](https://img.shields.io/badge/Status-Em%20Desenvolvimento-yellow.svg)](https://shields.io/)
## ⚕️ Sobre o bAImax

O bAImax é um agente pessoal de saúde projetado para auxiliar na triagem inicial de possíveis causas para os seus sintomas. Através de uma interface intuitiva, o bAImax gera um relatório preliminar, oferecendo uma visão geral das potenciais condições relacionadas ao sintoma inserido.

**É crucial entender que o bAImax não substitui a consulta com um profissional de saúde.** O relatório gerado é apenas uma triagem inicial e serve como um ponto de partida para buscar orientação médica qualificada.

## ✨ Funcionalidades

* **Análise de Sintomas:** Permite ao usuário inserir um sintoma específico.
* **Geração de Relatório de Triagem:** Produz um relatório com possíveis causas para o sintoma informado.
* **Ênfase na Consulta Médica:** Reforça a importância de procurar um profissional de saúde para diagnóstico e tratamento adequados.

## 🚀 Como Usar

1.  Forneça o sintoma que você está experimentando na interface.
2.  O bAImax processará a informação e gerará um relatório de triagem inicial.
3.  **Importante:** Utilize o relatório como uma informação inicial para discutir com seu médico.

## ⚙️ Instalação

Para executar o bAImax localmente, siga os passos abaixo:

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/Moranggoo/bAImax.git](https://github.com/Moranggoo/bAImax.git)
    ```
2.  **Navegue até o diretório do projeto:**
    ```bash
    cd bAImax
    ```
3.  **Crie um ambiente virtual (recomendado):**
    ```bash
    python -m venv venv
    ```
4.  **Ative o ambiente virtual:**
    * No Linux/macOS:
        ```bash
        source venv/bin/activate
        ```
    * No Windows:
        ```bash
        venv\Scripts\activate
        ```
5.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Certifique-se de ter um arquivo `requirements.txt` com as dependências do seu projeto)*

## ▶️ Execução

Para rodar o bAImax, execute o seguinte comando:

```bash
python main.py

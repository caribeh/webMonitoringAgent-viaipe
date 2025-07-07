# Agente de Monitoramento da API ViaIpe (webMonitoringAgent-viaipe)

Este projeto implementa uma solução de monitoramento que consome dados da API ViaIpe da RNP, realiza cálculos de disponibilidade, banda e qualidade, armazena os resultados em um banco PostgreSQL e os visualiza em um dashboard Grafana.

A solução foi projetada para ser iniciada com um único comando, com provisionamento automático do Data Source e de um Dashboard inicial no Grafana.

## High-Level Design (HLD)

A arquitetura da solução segue o fluxo:

**API Externa (ViaIpe) -> Agente de Coleta (Python) -> Banco de Dados (PostgreSQL) -> Dashboard (Grafana)**

1.  **Agente de Coleta**: Um serviço em Python que, a cada 1 minuto, consome o endpoint `https://viaipe.rnp.br/api/norte`.
2.  **Processamento**: O agente calcula métricas agregadas com base nos dados recebidos:
    * **Disponibilidade Média**: % de clientes com status "up".
    * **Banda Média**: Média de consumo de banda dos clientes online.
    * **Score de Qualidade**: Um índice de 0-100 calculado com base na latência e perda de pacotes médias.
3.  **Armazenamento**: As métricas calculadas são salvas com um timestamp no banco PostgreSQL.
4.  **Visualização**: O Grafana se conecta ao banco de dados e exibe as métricas em um dashboard operacional, permitindo a detecção de tendências e problemas.

## Como Executar

### Pré-requisitos

* Docker
* Docker Compose

### Passos

1.  **Clone o repositório:**
    ```bash
    git clone <URL_DO_SEU_REPOSITORIO>
    cd webMonitoringAgent-viaipe
    ```

2.  **Suba os containers:**
    Execute o seguinte comando na raiz do projeto. Ele irá construir a imagem do agente e iniciar todos os serviços.
    ```bash
    docker-compose up --build -d
    ```

3.  **Acesse o Grafana:**
    * Abra seu navegador e acesse `http://localhost:3001`. **Atenção à porta 3001.**
    * Aguarde alguns minutos para que o agente colete os primeiros dados.
    * **Login:** `admin`
    * **Senha:** `admin`
    * O dashboard **"ViaIpe - Região Norte"** estará disponível na página inicial, provisionado automaticamente.

## Reset do Ambiente

Para forçar um "reset" completo do ambiente (útil após corrigir algum arquivo de configuração):

1.  **Pare e remova os containers:**
    ```bash
    docker-compose down
    ```
2.  **Remova os volumes nomeados do projeto (isso apagará os dados):**
    ```bash
    docker volume rm webmonitoringagent-viaipe_postgres-data
    docker volume rm webmonitoringagent-viaipe_grafana-data
    ```
3.  **Suba o ambiente novamente:**
    ```bash
    docker-compose up --build -d
    ```


# agent/agent.py
import os
import time
import requests
import psycopg2

# --- Configurações ---
API_URL = "https://viaipe.rnp.br/api/norte"
INTERVALO_SEGUNDOS = 60  

DB_HOST = os.getenv("DB_HOST", "postgres-db")
DB_NAME = os.getenv("DB_NAME", "viaipe_db")
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
PYTHONUNBUFFERED = os.getenv("PYTHONUNBUFFERED", 0)

def get_db_connection():
    """Estabelece e retorna uma conexão com o banco de dados PostgreSQL."""
    while True:
        try:
            conn = psycopg2.connect(
                host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
            )
            print(">>> Conexão com o PostgreSQL estabelecida com sucesso.", flush=True)
            return conn
        except psycopg2.OperationalError as e:
            print(f"!!! Erro ao conectar com o PostgreSQL: {e}. Tentando novamente em 5 segundos...", flush=True)
            time.sleep(5)

def processar_dados(api_data):
    """Calcula as métricas a partir dos dados brutos da API."""
    clients_com_dados = []
    
    for client in api_data:
        # Verifica se o cliente tem os dados essenciais para os cálculos
        if client.get("data") and client["data"].get("smoke") and client["data"].get("interfaces"):
            clients_com_dados.append(client)

    num_clients_reporting = len(clients_com_dados)
    if num_clients_reporting == 0:
        print(">>> Nenhum cliente com dados válidos (smoke/interfaces) foi encontrado.", flush=True)
        return None

    # --- Cálculos Agregados ---
    total_banda_bps = 0
    total_latencia = 0
    total_perda = 0

    for client in clients_com_dados:
        # Soma da banda de todas as interfaces de um cliente
        client_banda_bps = sum(iface.get("traffic_in", 0) + iface.get("traffic_out", 0) for iface in client["data"]["interfaces"])
        total_banda_bps += client_banda_bps

        # Pega dados de qualidade do "smoke"
        total_latencia += client["data"]["smoke"].get("avg_val", 500)  # Penalidade de 500ms se nulo
        total_perda += client["data"]["smoke"].get("avg_loss", 100) # Penalidade de 100% se nulo

    # Médias
    avg_bandwidth_bps = total_banda_bps / num_clients_reporting
    avg_bandwidth_mbps = avg_bandwidth_bps / 1_000_000  # Convertendo de bps para Mbps
    avg_latency_ms = total_latencia / num_clients_reporting
    avg_packet_loss_percent = total_perda / num_clients_reporting

    # Cálculo do Score de Qualidade (0-100)
    score_latencia = max(0, 100 - (avg_latency_ms / 2))  # 100 @ 0ms, 0 @ 200ms+
    score_perda = max(0, 100 - (avg_packet_loss_percent * 10)) # 100 @ 0%, 0 @ 10%+
    quality_score = (score_latencia + score_perda) / 2

    print(f">>> Métricas Calculadas: Clientes={num_clients_reporting}, Banda Média={avg_bandwidth_mbps:.2f} Mbps, Qualidade={quality_score:.2f}%", flush=True)
    return (num_clients_reporting, avg_bandwidth_mbps, avg_latency_ms, avg_packet_loss_percent, quality_score)


def main():
    """Lógica principal do agente."""
    print(">>> Iniciando o agente de coleta ViaIpe (v2)...", flush=True)
    db_conn = get_db_connection()

    while True:
        print(f"\n--- {time.ctime()} ---", flush=True)
        try:
            print(">>> Tentando consumir a API...", flush=True)
            response = requests.get(API_URL, timeout=30)
            print(f">>> Resposta da API recebida com status: {response.status_code}", flush=True)
            response.raise_for_status()
            
            api_data = response.json()
            
            metricas = processar_dados(api_data)

            if metricas:
                try:
                    with db_conn.cursor() as cursor:
                        sql = """
                            INSERT INTO viaipe_norte_stats (
                                clients_reporting, avg_bandwidth_mbps, avg_latency_ms,
                                avg_packet_loss_percent, quality_score
                            ) VALUES (%s, %s, %s, %s, %s)
                        """
                        cursor.execute(sql, metricas)
                    db_conn.commit()
                    print(">>> Métricas salvas no banco de dados com sucesso.", flush=True)
                except (Exception, psycopg2.Error) as error:
                    print(f"!!! Erro ao salvar no banco de dados: {error}", flush=True)
                    db_conn.rollback()

        except requests.RequestException as e:
            print(f"!!! Erro fatal ao consumir a API ViaIpe: {e}", flush=True)
        except Exception as e:
            print(f"!!! Ocorreu um erro inesperado no loop principal: {e}", flush=True)

        print(f"--- Aguardando {INTERVALO_SEGUNDOS} segundos para o próximo ciclo ---", flush=True)
        time.sleep(INTERVALO_SEGUNDOS)

if __name__ == "__main__":
    main()
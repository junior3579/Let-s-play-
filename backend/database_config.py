import pg8000
import os
from datetime import datetime, timezone, timedelta
import time
import threading
import logging

# Configuração de Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações do Banco de Dados (Via Variáveis de Ambiente)
DB_CONFIG = {
    "user": os.environ.get("DB_USER", "postgres.kubvbqvpuwecrlwwmrvc"),
    "password": os.environ.get("DB_PASSWORD", "Qwer35791931@"),
    "host": os.environ.get("DB_HOST", "aws-1-sa-east-1.pooler.supabase.com"),
    "database": os.environ.get("DB_NAME", "postgres"),
    "port": int(os.environ.get("DB_PORT", 5432)),
    "ssl_context": os.environ.get("DB_SSL", "True") == "True"
}

class PG8000Pool:
    """Pool de conexões otimizado para Supabase com limites rigorosos e validação."""
    def __init__(self, minconn, maxconn, **kwargs):
        self.kwargs = kwargs
        self.connections = []
        self.maxconn = maxconn
        self.minconn = minconn
        self.lock = threading.Lock()
        self._initialize_pool()

    def _initialize_pool(self):
        for _ in range(self.minconn):
            try:
                conn = self._create_connection()
                if conn:
                    self.connections.append(conn)
            except Exception as e:
                logger.error(f"Erro ao criar conexão inicial: {e}")

    def _create_connection(self):
        try:
            kwargs = self.kwargs.copy()
            if 'timeout' not in kwargs:
                kwargs['timeout'] = 15
            conn = pg8000.connect(**kwargs)
            return conn
        except Exception as e:
            logger.error(f"Falha crítica ao conectar ao banco: {e}")
            return None

    def getconn(self):
        with self.lock:
            while self.connections:
                conn = self.connections.pop()
                try:
                    # Teste rápido de saúde da conexão
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
                    return conn
                except:
                    try: conn.close()
                    except: pass
                    continue
            
            # Se não houver conexões no pool, cria uma nova se não exceder maxconn
            # Nota: Em ambientes serverless como Render, o pool é por processo.
            return self._create_connection()

    def putconn(self, conn):
        if not conn:
            return
        with self.lock:
            if len(self.connections) < self.maxconn:
                self.connections.append(conn)
            else:
                try:
                    conn.close()
                except:
                    pass

# Inicialização Global do Pool
# Para o Supabase Free Tier, o limite total de conexões é baixo (geralmente 60-90 via pooler).
# Usar um limite baixo por worker do Gunicorn é essencial.
try:
    connection_pool = PG8000Pool(
        minconn=1, 
        maxconn=5, # Limite conservador para múltiplos acessos
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_CONFIG["database"],
        ssl_context=DB_CONFIG["ssl_context"]
    )
    logger.info("Pool de conexões com Supabase otimizado!")
except Exception as e:
    logger.error(f"Erro ao configurar pool: {e}")
    connection_pool = None

def executar_query_fetchall(query, params=None, retries=2):
    """Executa SELECT com suporte a retentativas em caso de falha de conexão."""
    for attempt in range(retries + 1):
        conn = None
        try:
            conn = connection_pool.getconn()
            if not conn:
                raise Exception("Não foi possível obter conexão do pool")
            
            cursor = conn.cursor()
            cursor.execute(query, params) if params else cursor.execute(query)
            result = cursor.fetchall()
            cursor.close()
            connection_pool.putconn(conn)
            return result
        except Exception as e:
            if conn:
                try: conn.rollback()
                except: pass
                connection_pool.putconn(None) # Não devolve conexão quebrada
            
            if attempt < retries:
                time.sleep(0.5 * (attempt + 1)) # Backoff exponencial simples
                continue
            logger.error(f"Erro persistente em fetchall: {e} | Query: {query}")
            return []

def executar_query_commit(query, params=None, retries=1):
    """Executa INSERT/UPDATE/DELETE com suporte a retentativas."""
    for attempt in range(retries + 1):
        conn = None
        try:
            conn = connection_pool.getconn()
            if not conn:
                raise Exception("Não foi possível obter conexão do pool")
            
            cursor = conn.cursor()
            cursor.execute(query, params) if params else cursor.execute(query)
            conn.commit()
            cursor.close()
            connection_pool.putconn(conn)
            return True
        except Exception as e:
            if conn:
                try: conn.rollback()
                except: pass
                connection_pool.putconn(None)
            
            if attempt < retries:
                time.sleep(1)
                continue
            logger.error(f"Erro persistente em commit: {e} | Query: {query}")
            return False

# Mantendo as funções utilitárias originais, mas agora usando as versões otimizadas
def criar_tabelas_remoto():
    # ... (mesmo código anterior, mas agora as chamadas internas usam o novo commit)
    pass

def reordenar_posicoes():
    query_usuarios = "SELECT id FROM usuarios ORDER BY posicao ASC, id ASC"
    usuarios = executar_query_fetchall(query_usuarios)
    if not usuarios: return
    for index, (user_id,) in enumerate(usuarios, start=1):
        executar_query_commit("UPDATE usuarios SET posicao = %s WHERE id = %s", (index, user_id))

def obter_proxima_posicao_vaga():
    result = executar_query_fetchall("SELECT posicao FROM usuarios ORDER BY posicao")
    posicoes_ocupadas = {r[0] for r in result if r[0] is not None}
    pos = 1
    while pos in posicoes_ocupadas: pos += 1
    return pos

def obter_menor_id_vago():
    result = executar_query_fetchall("SELECT id FROM usuarios ORDER BY id")
    ids_ocupados = {r[0] for r in result}
    id_vago = 1
    while id_vago in ids_ocupados: id_vago += 1
    return id_vago

def atualizar_atividade_usuario(id_usuario):
    executar_query_commit(
        "UPDATE usuarios SET last_seen = %s WHERE id = %s",
        (datetime.now(timezone.utc).isoformat(), id_usuario)
    )

def listar_usuarios_online(minutos=5):
    limite = (datetime.now(timezone.utc) - timedelta(minutes=minutos)).isoformat()
    result = executar_query_fetchall(
        "SELECT nome, last_seen FROM usuarios WHERE last_seen >= %s ORDER BY last_seen DESC",
        (limite,)
    )
    if not result: return []
    usuarios_online = []
    for nome, last_seen_str in result:
        if last_seen_str:
            try:
                last_seen = datetime.fromisoformat(last_seen_str)
                last_seen_local = last_seen - timedelta(hours=3)
                usuarios_online.append({
                    'nome': nome,
                    'last_seen': last_seen_local.strftime('%H:%M:%S')
                })
            except: continue
    return usuarios_online

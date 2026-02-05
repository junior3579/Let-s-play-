import pg8000
import os
from datetime import datetime, timezone, timedelta
import threading

# Configurações do Banco de Dados (Via Variáveis de Ambiente)
# Prioriza variáveis de ambiente, com fallbacks para os valores fornecidos no projeto
DB_CONFIG = {
    "user": os.environ.get("DB_USER", "postgres.kubvbqvpuwecrlwwmrvc"),
    "password": os.environ.get("DB_PASSWORD", "Qwer35791931@"),
    "host": os.environ.get("DB_HOST", "aws-1-sa-east-1.pooler.supabase.com"),
    "database": os.environ.get("DB_NAME", "postgres"),
    "port": int(os.environ.get("DB_PORT", 5432)),
    "ssl_context": os.environ.get("DB_SSL", "True") == "True"
}

class PG8000Pool:
    def __init__(self, minconn, maxconn, **kwargs):
        self.kwargs = kwargs
        self.connections = []
        self.maxconn = maxconn
        self.lock = threading.Lock()
        for _ in range(minconn):
            try:
                self.connections.append(self._create_connection())
            except Exception as e:
                print(f"Erro ao criar conexão inicial: {e}")

    def _create_connection(self):
        kwargs = self.kwargs.copy()
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 10
        return pg8000.connect(**kwargs)

    def getconn(self):
        with self.lock:
            while self.connections:
                conn = self.connections.pop()
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
                    return conn
                except:
                    try: conn.close()
                    except: pass
                    continue
        return self._create_connection()

    def putconn(self, conn):
        with self.lock:
            if len(self.connections) < self.maxconn:
                self.connections.append(conn)
            else:
                try:
                    conn.close()
                except:
                    pass

# Criar pool de conexões
try:
    connection_pool = PG8000Pool(
        2, 10,
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_CONFIG["database"],
        ssl_context=DB_CONFIG["ssl_context"]
    )
    print("✅ Pool de conexões com Supabase configurado!")
except Exception as e:
    print(f"❌ Erro ao criar pool de conexões: {e}")
    connection_pool = None

def executar_query_fetchall(query, params=None):
    conn = None
    try:
        if not connection_pool: return []
        conn = connection_pool.getconn()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            print(f"Erro na execução da query: {e}")
            if conn: conn.rollback()
            cursor.close()
            return []
    except Exception as e:
        print(f"Erro ao obter conexão: {e}")
        return []
    finally:
        if conn:
            try:
                connection_pool.putconn(conn)
            except:
                pass

def executar_query_commit(query, params=None):
    conn = None
    try:
        if not connection_pool: return False
        conn = connection_pool.getconn()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Erro ao executar commit: {e}")
        if conn:
            try:
                conn.rollback()
            except:
                pass
        return False
    finally:
        if conn:
            try:
                connection_pool.putconn(conn)
            except:
                pass

def criar_tabelas_remoto():
    print("Iniciando criação de tabelas no Supabase...")
    queries = [
        '''
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            reais INTEGER NOT NULL DEFAULT 0,
            whatsapp TEXT,
            pix_tipo TEXT,
            pix_chave TEXT,
            last_seen TEXT,
            posicao INTEGER
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS categorias (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL UNIQUE
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS salas (
            id_sala SERIAL PRIMARY KEY,
            nome_sala TEXT NOT NULL,
            valor_inicial INTEGER NOT NULL,
            criador TEXT NOT NULL,
            jogadores TEXT,
            whatsapp TEXT,
            categoria_id INTEGER REFERENCES categorias(id),
            status TEXT DEFAULT 'aberta',
            vencedor_id INTEGER
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS apostas (
            id SERIAL PRIMARY KEY,
            id_sala INTEGER NOT NULL REFERENCES salas(id_sala),
            id_usuario INTEGER NOT NULL REFERENCES usuarios(id),
            valor_aposta INTEGER NOT NULL,
            status TEXT DEFAULT 'pendente',
            resultado TEXT DEFAULT 'pendente'
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS transacoes (
            id SERIAL PRIMARY KEY,
            id_usuario INTEGER NOT NULL REFERENCES usuarios(id),
            tipo TEXT NOT NULL,
            valor INTEGER NOT NULL,
            status TEXT DEFAULT 'pendente',
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS torneios (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            status TEXT DEFAULT 'inscricao',
            vencedor_id INTEGER REFERENCES usuarios(id),
            valor_inscricao INTEGER DEFAULT 0,
            premio INTEGER DEFAULT 0,
            data_inicio TEXT,
            data_fim TEXT,
            fase_atual TEXT
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS torneio_participantes (
            id SERIAL PRIMARY KEY,
            torneio_id INTEGER NOT NULL REFERENCES torneios(id) ON DELETE CASCADE,
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            status TEXT DEFAULT 'ativo',
            chave_id INTEGER,
            adversario_id INTEGER,
            data_inscricao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS torneio_confrontos (
            id SERIAL PRIMARY KEY,
            torneio_id INTEGER NOT NULL REFERENCES torneios(id) ON DELETE CASCADE,
            fase_nome TEXT NOT NULL,
            jogador1_id INTEGER REFERENCES usuarios(id),
            jogador2_id INTEGER REFERENCES usuarios(id),
            vencedor_id INTEGER REFERENCES usuarios(id),
            status TEXT DEFAULT 'pendente'
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS torneio_fases (
            id SERIAL PRIMARY KEY,
            torneio_id INTEGER NOT NULL REFERENCES torneios(id) ON DELETE CASCADE,
            nome_fase TEXT NOT NULL,
            ordem INTEGER NOT NULL,
            status TEXT DEFAULT 'pendente',
            participantes_ids TEXT,
            vencedores_ids TEXT
        )
        '''
    ]
    for q in queries:
        success = executar_query_commit(q)
        if success:
            print(f"Sucesso ao executar: {q[:50]}...")
        else:
            print(f"Erro ao executar: {q[:50]}...")
    print("Finalizado processo de criação de tabelas.")

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

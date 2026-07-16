import streamlit as st  
import sqlite3
import pandas as pd

# Configuração da página
st.set_page_config(
    page_title="SQL Playground - Ministério da Educação", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializa o estado da tela ativa se não existir
if "tela_ativa" not in st.session_state:
    st.session_state["tela_ativa"] = "Playground"

# --- ESTILIZAÇÃO E PALETA DE CORES (CSS) ---
st.markdown("""
    <style>
        .main {
            background-color: #fcfcfc;
        }
        h1, h2, h3, h4 {
            color: #11321b !important;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        }
        [data-testid="stSidebar"] {
            background-color: #0d2c16 !important;
            color: #ffffff;
        }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
            color: #ffffff !important;
        }
        div.stButton > button:first-child {
            background-color: #002780 !important;
            color: white !important;
            border-radius: 6px;
            border: 1px solid #002780;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        div.stButton > button:first-child:hover {
            background-color: #FFDF00 !important;
            color: #0d2c16 !important;
            border-color: #FFDF00;
        }
        .card-link {
            background-color: #f0f4f1;
            border-left: 5px solid #009B3A;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 15px;
        }
        .card-link a {
            color: #002780 !important;
            font-weight: bold;
            text-decoration: none;
            font-size: 1.1rem;
        }
        .card-link a:hover {
            text-decoration: underline;
        }
        .header-line {
            height: 4px;
            background: linear-gradient(90deg, #009B3A 0%, #FFDF00 50%, #002780 100%);
            margin-bottom: 25px;
            border-radius: 2px;
        }
    </style>
""", unsafe_allow_html=True)


class DatabaseManager:
    """Gerencia a conexão, criação e população do banco de dados SQLite."""
    
    def __init__(self):
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._inicializar_banco()

    def _inicializar_banco(self):
        self._criar_tabelas()
        self._popular_dados()
        self.conn.commit()

    def _criar_tabelas(self):
        self.cursor.execute("""
        CREATE TABLE clientes (
            id_cliente INTEGER PRIMARY KEY,
            nome TEXT NOT NULL,
            email TEXT UNIQUE,
            cidade TEXT,
            estado CHAR(2),
            data_cadastro DATE
        );
        """)

        self.cursor.execute("""
        CREATE TABLE livros (
            id_livro INTEGER PRIMARY KEY,
            titulo TEXT,
            autor TEXT,
            categoria TEXT,
            preco REAL,
            estoque INTEGER
        );
        """)

        self.cursor.execute("""
        CREATE TABLE pedidos (
            id_pedido INTEGER PRIMARY KEY,
            id_cliente INTEGER,
            id_livro INTEGER,
            data_pedido DATE,
            valor REAL,
            FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente),
            FOREIGN KEY (id_livro) REFERENCES livros(id_livro)
        );
        """)

    def _popular_dados(self):
        clientes_dados = [
            (101, 'Ana Beatriz', 'ana.beatriz@email.com', 'São Paulo', 'SP', '2026-01-15'),
            (102, 'Carlos Eduardo', 'cadu@email.com', 'Rio de Janeiro', 'RJ', '2026-02-10'),
            (103, 'Juliana Mendes', 'ju.mendes@email.com', 'Belo Horizonte', 'MG', '2026-03-05'),
            (104, 'Marcos Souza', 'marcos.souza@email.com', 'São Paulo', 'SP', '2026-03-20'),
            (105, 'Fernanda Lima', 'fer.lima@email.com', 'Porto Alegre', 'RS', '2026-04-02')
        ]
        self.cursor.executemany("INSERT INTO clientes VALUES (?, ?, ?, ?, ?, ?);", clientes_dados)

        livros_dados = [
            (1, 'Dom Casmurro', 'Machado de Assis', 'Clássicos', 39.90, 12),
            (2, 'O Alquimista', 'Paulo Coelho', 'Ficção', 49.90, 8),
            (3, 'A Garota no Trem', 'Paula Hawkins', 'Suspense', 29.90, 0),
            (4, 'Sapiens', 'Yuval Noah Harari', 'História', 69.90, 5),
            (5, 'Memórias Póstumas', 'Machado de Assis', 'Clássicos', 34.90, 15),
            (6, 'Flores para Algernon', 'Daniel Keyes', 'Ficção', 55.00, 3)
        ]
        self.cursor.executemany("INSERT INTO livros VALUES (?, ?, ?, ?, ?, ?);", livros_dados)

        pedidos_dados = [
            (1, 101, 1, "2026-01-10", 250.50),
            (2, 101, 2, "2026-02-15", 120.00),
            (3, 102, 3, "2026-02-20", 890.00),
            (4, 104, 4, "2026-03-01", 45.00)
        ]
        self.cursor.executemany("INSERT INTO pedidos VALUES (?, ?, ?, ?, ?);", pedidos_dados)

    def obter_conexao(self):
        return self.conn


class SQLTester:
    """Valida se o resultado da query do usuário bate com o gabarito esperado."""
    
    GABARITOS = {
        1: "SELECT id_livro, titulo, preco FROM livros;",
        2: "SELECT * FROM livros WHERE estoque > 0 ORDER BY preco DESC;",
        3: "SELECT COUNT(*) FROM livros WHERE categoria = 'Ficção';",
        4: "SELECT * FROM livros ORDER BY preco DESC LIMIT 1;",
        # Novas Questões da lista do usuário:
        6: "SELECT * FROM livros;",
        7: "SELECT nome FROM clientes;",
        8: "SELECT * FROM pedidos;",
        9: "SELECT * FROM livros WHERE preco > 50.00;",
        10: "SELECT * FROM clientes WHERE cidade <> 'São Paulo';",
        11: "SELECT * FROM pedidos WHERE data_pedido > '2026-01-01';",
        12: "SELECT cidade, COUNT(*) FROM clientes GROUP BY cidade;",
        13: "SELECT categoria, COUNT(*) FROM livros GROUP BY categoria;",
        14: "SELECT id_cliente, COUNT(*) FROM pedidos GROUP BY id_cliente;",
        15: "SELECT * FROM clientes ORDER BY nome ASC;",
        16: "SELECT * FROM livros ORDER BY titulo ASC;",
        17: "SELECT * FROM pedidos ORDER BY data_pedido DESC;",
        18: "SELECT COUNT(*) FROM clientes;",
        19: "SELECT SUM(valor) FROM pedidos;",
        20: "SELECT AVG(estoque) FROM livros;"
    }

    DICAS = {
        1: "Dica: Garanta que você selecionou exatamente as colunas `id_livro`, `titulo` e `preco` da tabela `livros`.",
        2: "Dica: Use `WHERE estoque > 0` e ordene com `ORDER BY preco DESC`.",
        3: "Dica: Use a função de agregação `COUNT(*)` filtrando por `categoria = 'Ficção'`.",
        4: "Dica: Você pode ordenar pelo preço de forma decrescente e limitar o resultado a 1 (`LIMIT 1`).",
        5: "Dica: Certifique-se de que a tabela se chama `autores`, possui as colunas `id_autor` (INTEGER PRIMARY KEY), `nome` (TEXT), `nacionalidade` (TEXT) e que inseriu exatamente os dois autores sugeridos.",
        6: "Dica: Utilize o caractere curinga asterisco `*` para trazer todas as colunas da tabela `livros`.",
        7: "Dica: Selecione apenas a coluna `nome` da tabela `clientes`.",
        8: "Dica: Lembre-se que no nosso banco de dados, compras são representadas pela tabela `pedidos`. Use `SELECT *` nela.",
        9: "Dica: Use a cláusula `WHERE preco > 50.00` na tabela `livros`.",
        10: "Dica: Filtre usando `WHERE cidade <> 'São Paulo'` ou `WHERE cidade != 'São Paulo'`.",
        11: "Dica: Lembre-se que as datas no SQLite são comparadas como strings no formato 'AAAA-MM-DD'. Use `WHERE data_pedido > '2026-01-01'`.",
        12: "Dica: Agrupe os dados usando `GROUP BY cidade` combinando com a função `COUNT(*)`.",
        13: "Dica: Use `GROUP BY categoria` e projete `categoria, COUNT(*)`.",
        14: "Dica: Agrupe a tabela `pedidos` por `id_cliente` e use a função `COUNT(*)`.",
        15: "Dica: Ordene utilizando `ORDER BY nome ASC` ou apenas `ORDER BY nome`.",
        16: "Dica: Ordene os livros pelo título utilizando `ORDER BY titulo`.",
        17: "Dica: Use `ORDER BY data_pedido DESC` na tabela `pedidos`.",
        18: "Dica: Use a função `COUNT(*)` na tabela `clientes`.",
        19: "Dica: A função para somar valores no SQL é a `SUM(valor)`.",
        20: "Dica: Dica: Para calcular a média simples de uma coluna, utilize a função de agregação `AVG(estoque)` diretamente na tabela `livros`."
    }

    @classmethod
    def verificar_resposta(cls, id_questao: int, df_usuario: pd.DataFrame, conn: sqlite3.Connection) -> tuple[bool, str]:
        if id_questao == 5:
            return cls._verificar_questao_5(conn)

        if id_questao not in cls.GABARITOS:
            return False, "Questão não cadastrada no sistema de testes."

        try:
            df_gabarito = pd.read_sql_query(cls.GABARITOS[id_questao], conn)

            # Normalização de colunas
            df_usuario_norm = df_usuario.copy()
            df_usuario_norm.columns = [str(col).lower() for col in df_usuario_norm.columns]
            
            df_gabarito_norm = df_gabarito.copy()
            df_gabarito_norm.columns = [str(col).lower() for col in df_gabarito_norm.columns]

            if df_usuario_norm.shape != df_gabarito_norm.shape:
                return False, f"O formato da sua tabela está diferente do esperado. Retornou {df_usuario_norm.shape[1]} colunas e {df_usuario_norm.shape[0]} linhas. \n\n{cls.DICAS[id_questao]}"

            if not df_usuario_norm.equals(df_gabarito_norm):
                return False, f"Os dados retornados não batem com o gabarito. Verifique se a ordenação, colunas ou os filtros estão exatamente corretos! \n\n{cls.DICAS[id_questao]}"

            return True, "Parabéns! Sua consulta SQL está correta!"

        except Exception as e:
            return False, f"Erro interno ao validar a resposta: {str(e)}"

    @classmethod
    def _verificar_questao_5(cls, conn: sqlite3.Connection) -> tuple[bool, str]:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='autores';")
            if not cursor.fetchone():
                return False, "A tabela `autores` ainda não foi criada. " + cls.DICAS[5]

            df_autores = pd.read_sql_query("SELECT * FROM autores;", conn)
            df_autores.columns = [col.lower() for col in df_autores.columns]
            colunas_esperadas = ["id_autor", "nome", "nacionalidade"]
            
            if list(df_autores.columns) != colunas_esperadas:
                return False, f"As colunas encontradas foram {list(df_autores.columns)}, mas o esperado era {colunas_esperadas}."

            if len(df_autores) < 2:
                return False, "A tabela foi criada, mas você precisa inserir os 2 registros de autores solicitados!"
            
            primeiro_autor = df_autores.iloc[0].to_dict()
            if "machado de assis" not in str(primeiro_autor['nome']).lower():
                return False, "Os dados do primeiro autor não parecem corretos (ID: 1, Machado de Assis, Brasileiro)."

            return True, "Excelente! Você criou a tabela 'autores' com sucesso e populou os dados corretamente!"

        except Exception as e:
            return False, f"Erro ao verificar a tabela: {str(e)}"


class QuestionWidget:
    """Componente de interface para renderizar as caixas de perguntas e validação."""
    
    def __init__(self, id_questao: int, titulo: str, conn: sqlite3.Connection, ddl_mode: bool = False):
        self.id_questao = id_questao
        self.titulo = titulo
        self.conn = conn
        self.ddl_mode = ddl_mode  # Se True, executa sem esperar retorno de DataFrame (CREATE/INSERT)

    def render(self):
        st.subheader(f"Questão {self.id_questao} - {self.titulo}")
        
        # Template inicial didático para a questão 5
        default_val = ""
        if self.id_questao == 5:
            default_val = """-- Digite seu código de CREATE e INSERT aqui:
CREATE TABLE autores (
    id_autor INTEGER PRIMARY KEY,
    nome TEXT,
    nacionalidade TEXT
);

INSERT INTO autores VALUES (1, 'Machado de Assis', 'Brasileiro');
INSERT INTO autores VALUES (2, 'Clarice Lispector', 'Brasileira');
"""

        query_usuario = st.text_area(
            "Digite o código SQL e pressione Ctrl+Enter (ou clique em Executar)", 
            value=default_val, 
            height=120,
            key=f"query_q{self.id_questao}"
        )

        if st.button("▶️ Executar e Verificar", type="primary", key=f"btn_q{self.id_questao}"):
            if not query_usuario.strip():
                st.warning("⚠️ Por favor, digite uma query antes de executar.")
                return

            try:
                # 1. Execução da Query no Banco de Dados
                if self.ddl_mode:
                    cursor = self.conn.cursor()
                    cursor.executescript(query_usuario)
                    self.conn.commit()
                    df_resultado = pd.DataFrame()  # DataFrame vazio para o fluxo de teste
                else:
                    df_resultado = pd.read_sql_query(query_usuario, self.conn)
                
                # 2. Exibição do Output (Sempre exibe se for uma query SELECT normal)
                if not self.ddl_mode:
                    st.subheader("📊 Resultado da sua Consulta:")
                    if df_resultado.empty:
                        st.warning("A consulta rodou com sucesso, mas não retornou nenhum registro (tabela vazia).")
                    else:
                        st.dataframe(df_resultado, use_container_width=True)
                        st.caption(f"Total de registros retornados: {len(df_resultado)}")
                    st.markdown("---")

                # 3. Teste de Validação Automatizada
                sucesso, mensagem = SQLTester.verificar_resposta(self.id_questao, df_resultado, self.conn)
                
                if sucesso:
                    st.balloons()
                    st.success(f"🎉 **{mensagem}**")
                    if self.id_questao == 5:
                        st.subheader("📊 Tabela `autores` criada com sucesso:")
                        df_autores = pd.read_sql_query("SELECT * FROM autores;", self.conn)
                        st.dataframe(df_autores, use_container_width=True)
                else:
                    st.error(f"❌ **Resposta Incorreta**\n\n{mensagem}")
                    
            except Exception as e:
                st.error("❌ Erro de Sintaxe na execução da sua Query:")
                st.code(str(e), language="sql")


# --- INICIALIZAÇÃO DO BANCO DE DADOS ---
@st.cache_resource
def get_db():
    return DatabaseManager()

db_manager = get_db()
conn = db_manager.obter_conexao()


# --- INTERFACE: SIDEBAR ---
with st.sidebar:
    st.image("image_e7d479.jpg", use_container_width=True)
    st.markdown("---")
    
    st.subheader("Navegação")
    if st.button("📝 Playground de Exercícios", use_container_width=True, key="nav_play"):
        st.session_state["tela_ativa"] = "Playground"
    if st.button("ℹ️ Sobre o Curso / Recursos", use_container_width=True, key="nav_about"):
        st.session_state["tela_ativa"] = "Sobre"
        
    st.markdown("---")
    
    if st.session_state["tela_ativa"] == "Playground":
        st.header("📋 Estrutura do Banco")
        
        st.subheader("🔑 Tabela: `clientes`")
        st.markdown("""
        - **id_cliente** *(INT - PK)*
        - **nome** *(TEXT)*
        - **email** *(TEXT)*
        - **cidade** *(TEXT)*
        - **estado** *(CHAR(2))*
        - **data_cadastro** *(DATE)*
        """)
        
        st.subheader("📦 Tabela: `livros`")
        st.markdown("""
        - **id_livro** *(INT - PK)*
        - **titulo** *(TEXT)*
        - **autor** *(TEXT)*
        - **categoria** *(TEXT)*
        - **preco** *(REAL)*
        - **estoque** *(INT)*
        """)

        st.subheader("🛒 Tabela: `pedidos`")
        st.markdown("""
        - **id_pedido** *(INT - PK)*
        - **id_cliente** *(INT - FK)*
        - **id_livro** *(INT - FK)*
        - **data_pedido** *(DATE)*
        - **valor** *(REAL)*
        """)


# --- CONTROLE DE EXIBIÇÃO DE TELAS ---

if st.session_state["tela_ativa"] == "Playground":
    # --- TELA 1: PLAYGROUND ---
    col_logo, col_titulo = st.columns([1, 4])
    with col_logo:
        st.image("image_e7d479.jpg", width=150)
    with col_titulo:
        st.title("SQL Playground Interativo")
        st.write("**Plataforma de Capacitação de Banco de Dados**")

    st.markdown('<div class="header-line"></div>', unsafe_allow_html=True)
    
    # ==================== NOVO: SCHEMA INTERATIVO ====================
    with st.expander("🗺️ Visualizar Schema e Tabelas do Banco de Dados", expanded=False):
        st.markdown("""
        O banco de dados simula o sistema de uma livraria acadêmica do MEC. 
        Abaixo você pode conferir a estrutura de relacionamentos e as tabelas populadas:
        """)
        
        # Representação visual simples das chaves (DER)
        st.code("""
  [clientes] 1  --->  N [pedidos] N  <---  1 [livros]
  (id_cliente)           (id_pedido)           (id_livro)
                         (id_cliente) FK
                         (id_livro) FK
        """, language="text")
        
        # Abas interativas para inspecionar os dados reais do banco
        tab_clientes, tab_livros, tab_pedidos = st.tabs(["👥 Tabela: clientes", "📚 Tabela: livros", "🛒 Tabela: pedidos"])
        
        with tab_clientes:
            st.markdown("**Colunas:** `id_cliente` (PK) | `nome` | `email` | `cidade` | `estado` | `data_cadastro`")
            df_preview_cli = pd.read_sql_query("SELECT * FROM clientes", conn)
            st.dataframe(df_preview_cli, use_container_width=True)
            
        with tab_livros:
            st.markdown("**Colunas:** `id_livro` (PK) | `titulo` | `autor` | `categoria` | `preco` | `estoque`")
            df_preview_liv = pd.read_sql_query("SELECT * FROM livros", conn)
            st.dataframe(df_preview_liv, use_container_width=True)
            
        with tab_pedidos:
            st.markdown("**Colunas:** `id_pedido` (PK) | `id_cliente` (FK) | `id_livro` (FK) | `data_pedido` | `valor`")
            df_preview_ped = pd.read_sql_query("SELECT * FROM pedidos", conn)
            st.dataframe(df_preview_ped, use_container_width=True)
    # =================================================================
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("Pratique suas habilidades em SQL escrevendo as consultas. O sistema valida de forma automatizada se o seu resultado está correto!")
    st.markdown("<br>", unsafe_allow_html=True)

   

    # --- LISTA COMPLETA DE QUESTÕES DINÂMICAS ---
    questoes = [
        # Originais
        (1, "Selecione o id_livro, o titulo e preco da tabela livros:", False),
        (2, "Selecione apenas os livros que estão em estoque (estoque > 0) e ordene pelo preço de forma decrescente:", False),
        (3, "Descubra quantos livros são da categoria 'Ficção' (use COUNT):", False),
        (4, "Selecione todos os dados do livro mais caro do banco (Dica: use ORDER BY e LIMIT):", False),
        (5, "Crie uma tabela chamada 'autores' com as colunas 'id_autor' (Inteiro, chave primária), 'nome' (Texto) e 'nacionalidade' (Texto). Em seguida, insira os autores 'Machado de Assis' (ID 1, Brasileiro) e 'Clarice Lispector' (ID 2, Brasileira):", True),
        
        # Grupo 1: Consultas Básicas
        (6, "Escreva um comando para listar todos os livros cadastrados na tabela `livros`:", False),
        (7, "Mostre apenas o nome de todos os clientes da tabela `clientes`:", False),
        (8, "Liste todos os dados da tabela `pedidos` (que representam as compras realizadas):", False),
        
        # Grupo 2: Filtros (Cláusula WHERE)
        (9, "Exiba os livros com preco maior que R$ 50.00:", False),
        (10, "Mostre os clientes que não moram em 'São Paulo':", False),
        (11, "Liste as compras (tabela `pedidos`) realizadas após '2026-01-01':", False),
        
        # Grupo 3: Agrupamentos e Agregações (GROUP BY / COUNT)
        (12, "Mostre a quantidade de clientes por cidade (exiba a cidade e a contagem):", False),
        (13, "Exiba a quantidade de livros por categoria (exiba a categoria e a contagem):", False),
        (14, "Liste o total de compras (pedidos) realizadas por cada cliente (exiba o id_cliente e a contagem):", False),
        
        # Grupo 4: Ordenação (ORDER BY)
        (15, "Liste todos os clientes em ordem alfabética pelo nome:", False),
        (16, "Mostre todos os livros em ordem alfabética pelo título:", False),
        (17, "Liste as compras (tabela `pedidos`) em ordem decrescente pela data do pedido:", False),
        
        # Grupo 5: Funções Estatísticas/Agregação Globais
        (18, "Conte quantos clientes estão cadastrados no total:", False),
        (19, "Calcule o valor total acumulado de todas as compras (soma do campo valor na tabela `pedidos`):", False),
        (20, "Calcule a quantidade média de livros que tem no estoque:", False)
    ]

    for id_q, desc, ddl_mode in questoes:
        widget = QuestionWidget(id_questao=id_q, titulo=desc, conn=conn, ddl_mode=ddl_mode)
        widget.render()
        st.markdown("<br><br>", unsafe_allow_html=True)

elif st.session_state["tela_ativa"] == "Sobre":
    # --- TELA 2: SOBRE ---
    col_logo, col_titulo = st.columns([1, 4])
    with col_logo:
        st.image("image_e7d479.jpg", width=150)
    with col_titulo:
        st.title("Recursos e Material de Apoio")
        st.write("**Curso de Banco de Dados - Ministério da Educação**")
        
    st.markdown('<div class="header-line"></div>', unsafe_allow_html=True)
    
    st.markdown("### 📚 Materiais Disponíveis")
    st.write("Aproveite os materiais de referência abaixo para aprofundar seu conhecimento em SQL e modelagem de dados:")
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
        <div class="card-link">
            <h4>📖 Slides Oficiais da Aula</h4>
            <p>Acesse a apresentação completa utilizada em nosso treinamento.</p>
            <a href="https://canva.link/hc36lmwpidnh0mp" target="_blank">🔗 Clique aqui para abrir os Slides no Canva</a>
        </div>
        
        <div class="card-link">
            <h4>💻 Praticar Mais Questões (SQL Practice)</h4>
            <p>Quer continuar treinando? Este site interativo possui dezenas de problemas adicionais práticos com feedback instantâneo.</p>
            <a href="https://www.sql-practice.com" target="_blank">🔗 Ir para o sql-practice.com</a>
        </div>
        
        <div class="card-link">
            <h4>📖 Guia Completo e Prático de SQL</h4>
            <p>Um tutorial detalhado que serve como excelente manual de consulta para sintaxe, JOINS, funções de agregação e muito mais.</p>
            <a href="https://www.sqltutorial.org" target="_blank">🔗 Acessar o sqltutorial.org</a>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br><hr>", unsafe_allow_html=True)
    
    if st.button("← Voltar para os Exercícios", type="primary"):
        st.session_state["tela_ativa"] = "Playground"
        st.rerun()

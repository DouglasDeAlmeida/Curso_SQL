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
        /* Cor de fundo principal e textos */
        .main {
            background-color: #fcfcfc;
        }
        h1, h2, h3, h4 {
            color: #11321b !important; /* Verde escuro institucional */
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        }
        
        /* Sidebar customizada */
        [data-testid="stSidebar"] {
            background-color: #0d2c16 !important; /* Verde MEC bem escuro */
            color: #ffffff;
        }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
            color: #ffffff !important;
        }
        
        /* Botões primários (Azul MEC) */
        div.stButton > button:first-child {
            background-color: #002780 !important;
            color: white !important;
            border-radius: 6px;
            border: 1px solid #002780;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        div.stButton > button:first-child:hover {
            background-color: #FFDF00 !important; /* Amarelo no Hover */
            color: #0d2c16 !important;
            border-color: #FFDF00;
        }
        
        /* Links customizados em formato de card para a tela Sobre */
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
        
        /* Divisores decorativos verde/amarelo */
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
        4: "SELECT * FROM livros ORDER BY preco DESC LIMIT 1;"
    }

    DICAS = {
        1: "Dica: Garanta que você selecionou exatamente as colunas `id_livro`, `titulo` e `preco` da tabela `livros`.",
        2: "Dica: Use `WHERE estoque > 0` e ordene com `ORDER BY preco DESC`.",
        3: "Dica: Use a função de agregação `COUNT(*)` filtrando por `categoria = 'Ficção'`.",
        4: "Dica: Você pode ordenar pelo preço de forma decrescente e limitar o resultado a 1 (`LIMIT 1`)."
    }

    @classmethod
    def verificar_resposta(cls, id_questao: int, df_usuario: pd.DataFrame, conn: sqlite3.Connection) -> tuple[bool, str]:
        if id_questao not in cls.GABARITOS:
            return False, "Questão não cadastrada no sistema de testes."

        try:
            df_gabarito = pd.read_sql_query(cls.GABARITOS[id_questao], conn)

            df_usuario_norm = df_usuario.copy()
            df_usuario_norm.columns = [str(col).lower() for col in df_usuario_norm.columns]
            
            df_gabarito_norm = df_gabarito.copy()
            df_gabarito_norm.columns = [str(col).lower() for col in df_gabarito_norm.columns]

            if df_usuario_norm.shape != df_gabarito_norm.shape:
                return False, f"O formato da sua tabela está diferente do esperado. Retornou {df_usuario_norm.shape[1]} colunas e {df_usuario_norm.shape[0]} linhas. \n\n{cls.DICAS[id_questao]}"

            if not df_usuario_norm.equals(df_gabarito_norm):
                return False, f"Os dados retornados não batem com o gabarito. Verifique se a ordenação ou os filtros estão corretos! \n\n{cls.DICAS[id_questao]}"

            return True, "Parabéns! Sua consulta SQL está correta!"

        except Exception as e:
            return False, f"Erro interno ao validar a resposta: {str(e)}"


class QuestionWidget:
    """Componente de interface para renderizar as caixas de perguntas e validação."""
    
    def __init__(self, id_questao: int, titulo: str, conn: sqlite3.Connection):
        self.id_questao = id_questao
        self.titulo = titulo
        self.conn = conn

    def render(self):
        st.subheader(f"Questão {self.id_questao} - {self.titulo}")
        
        query_usuario = st.text_area(
            "Digite o código SQL e pressione Ctrl+Enter (ou clique em Executar)", 
            value="", 
            height=120,
            key=f"query_q{self.id_questao}"
        )

        if st.button("▶️ Executar e Verificar", type="primary", key=f"btn_q{self.id_questao}"):
            if not query_usuario.strip():
                st.warning("⚠️ Por favor, digite uma query antes de executar.")
                return

            try:
                df_resultado = pd.read_sql_query(query_usuario, self.conn)
                
                st.subheader("📊 Seu Resultado:")
                if df_resultado.empty:
                    st.warning("A consulta rodou, mas não retornou nenhum dado.")
                else:
                    st.dataframe(df_resultado, use_container_width=True)
                    st.caption(f"Total de registros retornados: {len(df_resultado)}")

                st.markdown("---")
                
                sucesso, mensagem = SQLTester.verificar_resposta(self.id_questao, df_resultado, self.conn)
                
                if sucesso:
                    st.balloons()
                    st.success(f"🎉 **{mensagem}**")
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


# --- INTERFACE: SIDEBAR COM CONTROLE DE NAVEGAÇÃO ---
with st.sidebar:
    st.image("image_e7d479.jpg", use_container_width=True)
    st.markdown("---")
    
    # Botões de Navegação das Telas
    st.subheader("Navegação")
    if st.button("📝 Playground de Exercícios", use_container_width=True, key="nav_play"):
        st.session_state["tela_ativa"] = "Playground"
    if st.button("ℹ️ Sobre o Curso / Recursos", use_container_width=True, key="nav_about"):
        st.session_state["tela_ativa"] = "Sobre"
        
    st.markdown("---")
    
    # Exibir Schema apenas na tela do Playground para não sobrecarregar a de "Sobre"
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
    st.markdown("Pratique suas habilidades em SQL escrevendo as consultas. O sistema valida de forma automatizada se o seu resultado está correto!")
    st.markdown("<br>", unsafe_allow_html=True)

    # Renderização das Questões
    questoes = [
        (1, "Selecione o id_livro, o titulo e preco da tabela livros:"),
        (2, "Selecione apenas os livros que estão em estoque (estoque > 0) e ordene pelo preço de forma decrescente:"),
        (3, "Descubra quantos livros são da categoria 'Ficção' (use COUNT):"),
        (4, "Selecione todos os dados do livro mais caro do banco (Dica: use ORDER BY e LIMIT):")
    ]

    for id_q, desc in questoes:
        widget = QuestionWidget(id_questao=id_q, titulo=desc, conn=conn)
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

    # Cards estilizados com os links pedidos
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
    
    # Botão para voltar ao playground de forma simples
    if st.button("← Voltar para os Exercícios", type="primary"):
        st.session_state["tela_ativa"] = "Playground"
        st.rerun()

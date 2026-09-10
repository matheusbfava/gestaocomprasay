import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
import requests
import json

# Adiciona o diretório atual ao path para garantir importação do cliente
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class SupabaseClient:
    """
    Cliente de Conexão com a Base de Dados Central.
    """
    
    def __init__(self, url: str, key: str):
        self.url = url.rstrip('/') if url else ""
        self.key = key if key else ""
        self.client = None
        self.rest_url = f"{self.url}/rest/v1" if self.url else ""
        self.connected = False
        
    def connect(self) -> bool:
        if not self.url or not self.key:
            raise ValueError("Configurações de conexão não localizadas.")
            
        try:
            from supabase import create_client
            self.client = create_client(self.url, self.key)
            self.connected = True
            return True
        except ImportError:
            self.connected = True
            return True
        except Exception as e:
            raise Exception(f"Erro ao conectar ao sistema: {str(e)}")

    def _get_headers(self) -> dict:
        return {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    def get_list_items(self, list_name: str = "PGI_GestaoCotacoes") -> list:
        if self.client:
            try:
                response = self.client.table(list_name).select("*").execute()
                return response.data if response.data else []
            except Exception:
                pass
                
        endpoint = f"{self.rest_url}/{list_name}?select=*"
        try:
            res = requests.get(endpoint, headers=self._get_headers(), timeout=10)
            if res.status_code == 200:
                return res.json()
            else:
                raise Exception(f"HTTP {res.status_code}: {res.text}")
        except Exception as e:
            raise Exception(f"Erro ao carregar dados ({list_name}): {str(e)}")

    def insert_list_item(self, item_data: dict, list_name: str = "PGI_GestaoCotacoes") -> bool:
        if self.client:
            try:
                self.client.table(list_name).insert(item_data).execute()
                return True
            except Exception:
                pass
                
        endpoint = f"{self.rest_url}/{list_name}"
        try:
            res = requests.post(endpoint, headers=self._get_headers(), json=item_data, timeout=10)
            if res.status_code in (200, 201):
                return True
            else:
                raise Exception(f"HTTP {res.status_code}: {res.text}")
        except Exception as e:
            raise Exception(f"Erro ao cadastrar registro ({list_name}): {str(e)}")

    def update_list_item(self, item_id: str, item_data: dict, list_name: str = "PGI_GestaoCotacoes", id_column: str = "ID_PGI") -> bool:
        id_val = item_data.get(id_column, item_id)
        if self.client:
            try:
                self.client.table(list_name).update(item_data).eq(id_column, str(id_val)).execute()
                return True
            except Exception:
                pass
                
        endpoint = f"{self.rest_url}/{list_name}?{id_column}=eq.{id_val}"
        try:
            res = requests.patch(endpoint, headers=self._get_headers(), json=item_data, timeout=10)
            if res.status_code in (200, 204):
                return True
            else:
                raise Exception(f"HTTP {res.status_code}: {res.text}")
        except Exception as e:
            raise Exception(f"Erro ao atualizar registro ({list_name}): {str(e)}")

    def delete_list_item(self, item_id: str, list_name: str = "PGI_GestaoCotacoes", id_column: str = "ID_PGI") -> bool:
        if self.client:
            try:
                self.client.table(list_name).delete().eq(id_column, str(item_id)).execute()
                return True
            except Exception:
                pass
                
        endpoint = f"{self.rest_url}/{list_name}?{id_column}=eq.{item_id}"
        try:
            res = requests.delete(endpoint, headers=self._get_headers(), timeout=10)
            if res.status_code in (200, 204):
                return True
            else:
                raise Exception(f"HTTP {res.status_code}: {res.text}")
        except Exception as e:
            raise Exception(f"Erro ao excluir registro ({list_name}): {str(e)}")


# Configuração oficial do Grupo A.Yoshii
st.set_page_config(
    page_title="PGI - Gestão de Suprimentos | A.Yoshii",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FUNÇÃO DE NORMALIZAÇÃO DE COMPRADORES ---
def format_buyer_name(name_str):
    if not name_str:
        return ""
    name_str = str(name_str).strip()
    if name_str.endswith("."):
        return name_str
    parts = [p for p in name_str.split() if p]
    if len(parts) <= 1:
        return name_str
    first = parts[0]
    last = parts[-1]
    return f"{first} {last[0].upper()}."


# Estilização CSS institucional da Marca A.Yoshii
st.markdown("""
    <style>
    /* Estilização da Barra Lateral (Sidebar) */
    [data-testid="stSidebar"] {
        background-color: #00205B !important;
        border-right: 3px solid #FF6F00 !important;
    }
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.2) !important;
    }
    
    /* Inputs e botões na barra lateral */
    [data-testid="stSidebar"] .stButton > button {
        background-color: #FF6F00 !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: bold !important;
        border-radius: 4px !important;
        transition: background-color 0.3s ease !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: #E05D00 !important;
    }
    
    /* Cabeçalho Corporativo */
    .title-container {
        padding: 8px 16px !important;
        background-color: #00205B;
        border-bottom: 3px solid #FF6F00;
        color: white;
        border-radius: 6px;
        margin-bottom: 12px !important;
        text-align: left;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: nowrap;
    }
    .title-text-box {
        margin-left: 10px;
        flex-grow: 1;
    }
    .title-main {
        font-size: 18px !important;
        font-weight: 800;
        margin: 0;
        line-height: 1.2;
        letter-spacing: 0.5px;
    }
    .title-sub {
        font-size: 11px !important;
        opacity: 0.85;
        margin-top: 2px;
    }
    
    /* Cards de Métricas Customizados */
    .metric-card-custom {
        background-color: #FFFFFF;
        border-top: 3px solid #00205B;
        border-radius: 6px;
        padding: 8px 12px !important;
        box-shadow: 0 1px 5px rgba(0,0,0,0.04);
        text-align: center;
        margin-bottom: 8px !important;
    }
    .metric-card-custom.orange-border {
        border-top: 3px solid #FF6F00;
    }
    .metric-value {
        font-size: 18px !important;
        font-weight: 800;
        color: #00205B;
        margin-top: 2px !important;
        line-height: 1.2;
    }
    .metric-label {
        font-size: 9px !important;
        color: #8C8C8C;
        text-transform: uppercase;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    
    /* Cards Informativos */
    .info-card {
        background-color: #F4F6F9;
        border-left: 5px solid #00205B;
        padding: 12px;
        border-radius: 4px;
        margin-bottom: 15px;
        color: #1E1E1E;
    }
    .info-card h4, .info-card p, .info-card code {
        color: #1E1E1E !important;
        margin: 0 0 6px 0;
    }
    
    div[data-baseweb="input"] {
        border-radius: 4px !important;
    }
    
    .stButton>button {
        background-color: #00205B !important;
        color: #FFFFFF !important;
        font-weight: bold !important;
        border: none !important;
        padding: 6px 16px !important;
        border-radius: 4px !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        background-color: #FF6F00 !important;
        box-shadow: 0 4px 12px rgba(255,111,0,0.2) !important;
    }
    
    .styled-table-title {
        color: #00205B;
        font-weight: bold;
        border-bottom: 2px solid #FF6F00;
        padding-bottom: 6px;
        margin-bottom: 10px;
        font-size: 16px;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÃO DE RENDERIZAÇÃO DE HTML ROBUSTA ---
def render_html(html_str):
    clean_html = "".join([line.strip() for line in html_str.split("\n")])
    st.markdown(clean_html, unsafe_allow_html=True)

# --- DEFINIÇÃO DE LOGO EM SVG ---
def get_logo_svg(theme="dark", width=145, height=30):
    text_color = "#FFFFFF" if theme == "dark" else "#00205B"
    return f'<svg width="{width}" height="{height}" viewBox="0 0 220 45" xmlns="http://www.w3.org/2000/svg" style="vertical-align: middle;"><rect x="2" y="2" width="41" height="41" rx="4" fill="#FF6F00" /><circle cx="22.5" cy="22.5" r="17.5" fill="#FFFFFF" /><circle cx="22.5" cy="22.5" r="15" fill="#00205B" /><path d="M 16,29 L 21.5,14 L 23.5,14 L 29,29" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/><line x1="18.5" y1="23.5" x2="26.5" y2="23.5" stroke="#FFFFFF" stroke-width="2.5" /><path d="M 25.5,23.5 L 29,31.5" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" /><text x="52" y="32" font-family="Helvetica, Arial, sans-serif" font-size="23" font-weight="900" fill="{text_color}" letter-spacing="1">A.YOSHII</text></svg>'

# --- CRIAÇÃO DOS DROPDOWNS OFICIAIS DO CLIENTE ---
LISTA_COMPRADORES = [
    "Leonardo F.", "Bruno C.", "Caio S.", "Heloysa C.", "Angelica F.", "Fernanda L.",
    "Flaviane F.", "Marcos T.", "Erik G.", "Aline D.", "Evelise D.", "Lorena P.",
    "Thafani O.", "Thayna L.", "Bryan C.", "Larissa M.", "Lucia W.", "Victor V.",
    "Vanessa B.", "Marcos F.", "Joao S.", "Andre P.", "Luis K.", "Gabriel M.",
    "Matheus F.", "Leonardo S.", "Matheus C.", "Roberta O."
]

LISTA_FALLBACK_GRUPO_INSUMO = [
    "PROTENSAO - ACESSORIOS E CONSULTORIA", "SRV - ESQUADRIA DE ALUMINIO", "SRV - ESQUADRIA DE MADEIRA",
    "SRV - REBOCO EXTERNO", "SRV - REBOCO INTERNO", "SRV - PINTURA INTERNA", "SRV - PINTURA EXTERNA",
    "SRV - REVESTIMENTO CERAMICO", "SRV - ALVENARIA", "SRV - ARMACAO", "SRV - CARPINTARIA",
    "SRV - ESCORAMENTO METALICO", "SRV - ESQUADRIA INOX", "PISO AQUECIDO", "SRV - ASPIRACAO CENTRAL",
    "SRV - REGUL., CONTRAPISO E PISOS DE CONCRETO", "SERVICO DE ANCORAGEM", "LOCACAO DE EQUIPAMENTOS",
    "SRV - FORMA METALICA", "SRV - LIMPEZA", "SRV - IMPERMEABILIZACAO", "SRV - COBERTURA E TELHAMENTO",
    "AUTOMAÇÃO", "SRV - INST. ELET. E COMUNICACAO", "PINTURA SOBRE PISO", "SRV - FORRO DE GESSO E DRY WALL",
    "SRV - FORROS ESPECIAIS", "SRV - INSTALACAO DE GRANITO E MARMORE", "SRV - INSTALACAO DE PISO LAMINADO E VINILICO",
    "SRV - INSTALACAO HIDRAULICA", "SRV - ESTRUTURA METALICA", "PRE-MOLDADOS DE CONCRETO - ELEMENTOS ESTRUTURAIS",
    "MONTAGEM E DESMONTAGEM DE EQUIPAMENTOS", "SRV - FUNDACAO", "SRV - PAVIMENTACAO ASFALTICA",
    "SRV - TERRAPLANAGEM", "SRV - INSTALACAO PARA GAS E ACESSORIOS", "PERGOLADOS E DECKS DE MADEIRA",
    "INSTALAÇÃO DE REVESTIMENTOS ESPECIAIS DE PAREDE", "VIDROS E ACESSORIOS", "PRESTADORES DE SERVIÇOS TÉCNICOS",
    "SRV - SERRALHERIA", "CHURRASQUEIRAS - SERVIÇO", "SRV - PAISAGISMO", "SRV - ESQUADRIA DE FERRO",
    "SRV - INSTALACAO DE PISOS EXTERNOS", "SERVIÇO DE SEGURANÇA PATRIMONIAL", "CONTROLE TECNOLÓGICO DE CONCRETO",
    "SRV - TOPOGRAFIA", "SRV - CLIMATIZACAO"
]

LISTA_FALLBACK_OBRAS = [
    "CORPORATIVO / GERAL", "ECOVILLAS DO LAGO", "ATMOS", "HARMONIA", "LEGEND"
]

LISTA_TIPOS = ["Novo", "Aditivo"]
OPCOES_STATUS = ["OK", "N/A", "aguardando"]

# --- CONFIGURAÇÕES DE INTEGRAÇÃO ---
if "sb_url" not in st.session_state:
    st.session_state.sb_url = st.secrets.get("SUPABASE_URL", st.secrets.get("supabase_url", ""))
if "sb_key" not in st.session_state:
    st.session_state.sb_key = st.secrets.get("SUPABASE_KEY", st.secrets.get("supabase_key", ""))
if "menu_option" not in st.session_state:
    st.session_state.menu_option = "Dashboard Geral"
if "selected_pgi_to_edit" not in st.session_state:
    st.session_state.selected_pgi_to_edit = None
if "confirm_delete_id" not in st.session_state:
    st.session_state.confirm_delete_id = None
if "user_perfil" not in st.session_state:
    st.session_state.user_perfil = "comprador"

# --- SESSÃO DE AUTENTICAÇÃO DO USUÁRIO ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- INSTANCIAÇÃO DO CLIENTE ---
sb_client = None
if st.session_state.sb_url and st.session_state.sb_key:
    try:
        sb_client = SupabaseClient(
            url=st.session_state.sb_url,
            key=st.session_state.sb_key
        )
        sb_client.connect()
    except Exception as e:
        sb_client = None

# --- CARREGAMENTO DINÂMICO DE USUÁRIOS (COM CACHE) ---
@st.cache_data(ttl=60)
def carregar_usuarios():
    if sb_client:
        try:
            users = sb_client.get_list_items(list_name="usuarios")
            if isinstance(users, list) and len(users) > 0:
                return users
        except Exception:
            pass
    return []

def login(username, password):
    username_clean = str(username).strip().lower()
    users_list = carregar_usuarios()
    matched_user = next((u for u in users_list if str(u.get("username", "")).strip().lower() == username_clean), None)
    
    if matched_user:
        if not matched_user.get("ativo", True):
            st.error("❌ Conta inativa. Entre em contato com a liderança de Suprimentos.")
            return
        if str(matched_user.get("senha", "")) == str(password):
            st.session_state.logged_in = True
            st.session_state.user = matched_user.get("nome", username)
            st.session_state.username = matched_user.get("username", username)
            st.session_state.user_perfil = matched_user.get("perfil", "comprador")
            st.success(f"✔️ Login realizado com sucesso! Bem-vindo, {st.session_state.user}.")
            st.rerun()
        else:
            st.error("❌ Senha incorreta.")
    else:
        if username_clean == "matheus.fava" and password == "ayoshii1050":
            st.session_state.logged_in = True
            st.session_state.user = "Matheus Fava"
            st.session_state.username = "matheus.fava"
            st.session_state.user_perfil = "administrador"
            st.success("✔️ Login de contingência autorizado.")
            st.rerun()
        elif username_clean == "admin" and password == "1234":
            st.session_state.logged_in = True
            st.session_state.user = "Administrador Sistema"
            st.session_state.username = "admin"
            st.session_state.user_perfil = "administrador"
            st.success("✔️ Login de contingência autorizado.")
            st.rerun()
        else:
            st.error("❌ Usuário não localizado ou senha incorreta.")

def logout():
    st.session_state.logged_in = False
    st.session_state.pop("user", None)
    st.session_state.pop("username", None)
    st.session_state.pop("user_perfil", None)
    st.rerun()

# --- CARREGAMENTO DINÂMICO DOS GRUPOS DE INSUMO ---
@st.cache_data(ttl=300)
def carregar_grupos_insumo():
    if sb_client:
        try:
            items = sb_client.get_list_items(list_name="dSUPRI_GruposInsumo")
            grupos = []
            for item in items:
                grupo_name = item.get("NomeGrupo", item.get("Title", ""))
                if grupo_name:
                    grupos.append(str(grupo_name).strip().upper())
            grupos = sorted(list(set(grupos)))
            if grupos:
                return grupos
        except Exception:
            pass
            
    return LISTA_FALLBACK_GRUPO_INSUMO

# --- CARREGAMENTO DINÂMICO DAS OBRAS ---
@st.cache_data(ttl=300)
def carregar_obras_detalhadas():
    if sb_client:
        try:
            items = sb_client.get_list_items(list_name="dSUPRI_Obras")
            if items:
                return items
        except Exception:
            pass
    return []

@st.cache_data(ttl=300)
def carregar_obras():
    items = carregar_obras_detalhadas()
    obras = []
    for item in items:
        nome = item.get("nome_reduzido", item.get("nome_obra", ""))
        if nome:
            obras.append(str(nome).strip().upper())
    obras = sorted(list(set(obras)))
    return obras if obras else LISTA_FALLBACK_OBRAS

# --- SEÇÃO DE CARREGAMENTO DINÂMICO DE DADOS ---
@st.cache_data(ttl=300)
def carregar_dados():
    if sb_client:
        try:
            items = sb_client.get_list_items(list_name="PGI_GestaoCotacoes")
            dados_mapeados = []
            for item in items:
                dados_mapeados.append({
                    "ID_PGI": str(item.get("ID_PGI", "")),
                    "obra": str(item.get("obra", "N/A")).strip().upper(),
                    "sp_id": item.get("ID"),
                    "DT_EMISSAO": str(item.get("DT_EMISSAO", "")),
                    "tipo": str(item.get("tipo", "Novo")),
                    "Comprador": format_buyer_name(item.get("Comprador", "")),
                    "grupoinsumo": str(item.get("grupoinsumo", "")),
                    "grupointerno": str(item.get("grupointerno", "")),
                    "cotacao": str(item.get("cotacao", item.get("Title", ""))),
                    "due_dilligence": str(item.get("due_dilligence", "aguardando")),
                    "equalizacao": str(item.get("equalizacao", "aguardando")),
                    "orcamento": str(item.get("orcamento", "N/A")),
                    "validacao_eng": str(item.get("validacao_eng", "aguardando")),
                    "validacao_ger": str(item.get("validacao_ger", "aguardando")),
                    "validacao_sup": str(item.get("validacao_sup", "aguardando")),
                    "req_mega": str(item.get("req_mega", "aguardando")),
                    "contr_mega": str(item.get("contr_mega", "aguardando")),
                    "param_fiscal": str(item.get("param_fiscal", "N/A")),
                    "minuta": str(item.get("minuta", "N/A")),
                    "ass_digital": str(item.get("ass_digital", "aguardando")),
                    "credenciamento": str(item.get("credenciamento", "N/A")),
                    "comunicar": str(item.get("comunicar", "N/A")),
                    "aud_pasta": str(item.get("aud_pasta", "aguardando"))
                })
            return dados_mapeados
        except Exception:
            return []
    else:
        return []

# --- VERIFICAÇÃO DE UNICIDADE EM TEMPO REAL ---
def verificar_id_duplicado_tempo_real(id_pgi: str) -> bool:
    if not sb_client:
        return False
    try:
        endpoint = f"{sb_client.rest_url}/PGI_GestaoCotacoes?ID_PGI=eq.{str(id_pgi).strip()}&select=ID_PGI"
        res = requests.get(endpoint, headers=sb_client._get_headers(), timeout=5)
        if res.status_code == 200:
            data = res.json()
            return len(data) > 0
    except Exception:
        pass
    return False

# --- FUNÇÃO PARA EXCLUIR REGISTRO ---
def excluir_registro(pgi_id):
    if sb_client:
        try:
            sb_client.delete_list_item(str(pgi_id), list_name="PGI_GestaoCotacoes", id_column="ID_PGI")
            st.cache_data.clear()
            return True
        except Exception as e:
            st.error(f"Erro ao excluir: {str(e)}")
            return False
    else:
        st.error("Conexão indisponível. Operação cancelada.")
        return False

# --- HELPER DE BADGES DE STATUS PARA TABELA ---
def get_html_status_badge(status):
    status_clean = str(status).strip()
    if status_clean.upper() == "OK":
        return '<span style="background-color:#EAF7EE; color:#28A745; font-weight:800; padding:2px 8px; border-radius:12px; font-size:10px; border:1px solid #28A745; display:inline-block;">OK</span>'
    elif status_clean.upper() == "N/A":
        return '<span style="background-color:#F4F6F9; color:#8C8C8C; font-weight:800; padding:2px 8px; border-radius:12px; font-size:10px; border:1px solid #8C8C8C; display:inline-block;">N/A</span>'
    elif status_clean.isdigit():
        return f'<span style="background-color:#EAF4FF; color:#00205B; font-weight:800; padding:2px 8px; border-radius:12px; font-size:10px; border:1px solid #00205B; display:inline-block;">{status_clean}</span>'
    else:
        return f'<span style="background-color:rgba(255,111,0,0.1); color:#FF6F00; font-weight:800; padding:2px 8px; border-radius:12px; font-size:10px; border:1px solid #FF6F00; display:inline-block;">{status_clean.upper()}</span>'


# ==============================================================================
# TELA DE LOGIN
# ==============================================================================
if not st.session_state.logged_in:
    logo_light = get_logo_svg(theme="light", width=180, height=38)
    render_html(f"""
        <div style="text-align: center; margin-top: 40px; margin-bottom: 25px;">
            {logo_light}
            <div style="font-size: 12px; color: #8C8C8C; font-weight: 600; text-transform: uppercase; letter-spacing: 2px; margin-top: 8px;">
                PGI - Sistema de Gestão de Cotações & Suprimentos
            </div>
        </div>
    """)
    
    col1, col2, col3 = st.columns([1.2, 1.3, 1.2])
    with col2:
        with st.form("login_form"):
            render_html("""
                <h3 style="text-align: center; color: #00205B; font-weight: 800; margin-bottom: 12px; font-size: 18px;">
                    🔑 Área Restrita de Acesso
                </h3>
            """)
            username_input = st.text_input("Usuário", placeholder="ID do usuário corporativo")
            password_input = st.text_input("Senha", type="password", placeholder="Digite a sua senha...")
            submit_button = st.form_submit_button("Acessar Painel")
            if submit_button:
                login(username_input, password_input)
                
        render_html("""
            <div style="background-color: #F4F6F9; border-top: 3px solid #FF6F00; padding: 10px; border-radius: 4px; margin-top: 10px; text-align: center;">
                <p style="margin: 0; font-size: 10px; color: #1E1E1E;">
                    💡 <strong>Acesso Corporativo A.Yoshii:</strong> Utilize seu usuário e senha autorizados pelo setor de Suprimentos.
                </p>
            </div>
        """)

# ==============================================================================
# TELA PRINCIPAL (APÓS LOGIN)
# ==============================================================================
else:
    lista_grupo_insumo_dynamic = carregar_grupos_insumo()
    lista_obras_dynamic = carregar_obras()
    
    db_data_current = carregar_dados()
    df_current = pd.DataFrame(db_data_current)

    # Sidebar com bloco de usuário de alto contraste
    with st.sidebar:
        logo_dark = get_logo_svg(theme="dark", width=145, height=30)
        render_html(f"""
            <div style="padding: 5px 0; border-bottom: 1px solid rgba(255,255,255,0.15); margin-bottom: 15px; text-align: center;">
                {logo_dark}
            </div>
        """)
        
        perfil_nome = "Administrador" if st.session_state.get("user_perfil") == "administrador" else "Comprador"
        render_html(f"""
            <div style="background-color: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 6px; padding: 10px 12px; margin-bottom: 16px;">
                <div style="font-size: 10px; color: #FFD180; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 800; margin-bottom: 4px;">Sessão Ativa</div>
                <div style="font-size: 14px; color: #FFFFFF; font-weight: 800; line-height: 1.2; margin-bottom: 8px;">
                    👤 {st.session_state.user}
                </div>
                <div style="display: inline-block; background-color: #FF6F00; color: #FFFFFF; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 800;">
                    🛡️ {perfil_nome}
                </div>
            </div>
        """)
        
        is_admin = st.session_state.get("user_perfil") == "administrador"
        nav_options = ["Dashboard Geral", "Adicionar ID", "Gerenciamento de Registros"]
        if is_admin:
            nav_options.append("Gestão de Obras (Admin)")
            nav_options.append("Gestão de Usuários (Admin)")

        menu_option_radio = st.radio(
            "Navegação",
            nav_options,
            index=nav_options.index(st.session_state.menu_option) if st.session_state.menu_option in nav_options else 0
        )
        if menu_option_radio != st.session_state.menu_option:
            st.session_state.menu_option = menu_option_radio
            st.rerun()
        
        st.write("---")
        if st.button("🔄 Sincronizar Dados", use_container_width=True):
            st.cache_data.clear()
            st.success("Dados sincronizados com sucesso!")
            st.rerun()
        
        st.write("---")
        if st.button("🚪 Sair do Aplicativo"):
            logout()
            
    # Cabeçalho Limpo
    logo_header = get_logo_svg(theme="dark", width=120, height=25)
    render_html(f"""
        <div class="title-container">
            <div class="title-text-box">
                <div class="title-main">Gestão de Cotações de Suprimentos</div>
                <div class="title-sub">Sistema Integrado de Acompanhamento de Processos | A.Yoshii Engenharia</div>
            </div>
            <div style="padding: 2px;">
                {logo_header}
            </div>
        </div>
    """)

    # CONFIRMAÇÃO DE EXCLUSÃO
    if st.session_state.confirm_delete_id:
        st.warning(f"⚠️ **Confirmação:** Deseja realmente excluir o processo de ID PGI **{st.session_state.confirm_delete_id}**?")
        col_yes, col_no = st.columns([1, 10])
        with col_yes:
            if st.button("✅ Sim, Excluir", key="confirm_yes_btn"):
                if excluir_registro(st.session_state.confirm_delete_id):
                    st.success(f"✔️ Registro {st.session_state.confirm_delete_id} excluído com sucesso.")
                st.session_state.confirm_delete_id = None
                st.rerun()
        with col_no:
            if st.button("❌ Cancelar", key="confirm_no_btn"):
                st.session_state.confirm_delete_id = None
                st.rerun()

    # ==========================================================================
    # PAGE 1: DASHBOARD GERAL COM PLANILHA INTERATIVA ESTILO EXCEL
    # ==========================================================================
    if st.session_state.menu_option == "Dashboard Geral":
        st.markdown("<h3 class='styled-table-title'>📊 Indicadores Operacionais de Processos</h3>", unsafe_allow_html=True)
        
        df_calc = df_current.copy()
        if not df_calc.empty:
            total_processos = len(df_calc)
            total_finalizados = len(df_calc[df_calc["aud_pasta"].astype(str).str.strip().str.upper() == "OK"])
            total_em_andamento = total_processos - total_finalizados
            taxa_conclusao = (total_finalizados / total_processos * 100) if total_processos > 0 else 0.0
        else:
            total_processos = total_finalizados = total_em_andamento = 0
            taxa_conclusao = 0.0
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        
        with col_m1:
            render_html(f"""
                <div class="metric-card-custom">
                    <div class="metric-label">Total de Processos</div>
                    <div class="metric-value">{total_processos}</div>
                </div>
            """)
        with col_m2:
            render_html(f"""
                <div class="metric-card-custom orange-border">
                    <div class="metric-label">Processos em Andamento</div>
                    <div class="metric-value" style="color: #FF6F00;">{total_em_andamento}</div>
                </div>
            """)
        with col_m3:
            render_html(f"""
                <div class="metric-card-custom">
                    <div class="metric-label">Processos Finalizados (Auditados)</div>
                    <div class="metric-value" style="color: #28A745;">{total_finalizados}</div>
                </div>
            """)
        with col_m4:
            render_html(f"""
                <div class="metric-card-custom">
                    <div class="metric-label">Taxa de Conclusão</div>
                    <div class="metric-value" style="color: #00205B;">{taxa_conclusao:.1f}%</div>
                </div>
            """)
        
        # --- FILTROS RESTRITOS: ID, COMPRADOR, GRUPO DE INSUMO, OBRA ---
        with st.expander("🔍 Filtros de Pesquisa por Processo", expanded=False):
            def get_filter_options(df, column_name):
                if df.empty or column_name not in df.columns:
                    return ["Todos"]
                unique_vals = sorted([str(v).strip() for v in df[column_name].unique() if str(v).strip()])
                return ["Todos"] + unique_vals

            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            with col_f1:
                f_id = st.selectbox("ID PGI", get_filter_options(df_current, "ID_PGI"), key="f_id_sel")
            with col_f2:
                f_comprador = st.selectbox("Comprador", get_filter_options(df_current, "Comprador"), key="f_comprador_sel")
            with col_f3:
                f_grupo = st.selectbox("Grupo Insumo", get_filter_options(df_current, "grupoinsumo"), key="f_grupo_sel")
            with col_f4:
                f_obra = st.selectbox("Obra", get_filter_options(df_current, "obra"), key="f_obra_sel")

            st.write("<div style='height:4px;'></div>", unsafe_allow_html=True)
            if st.button("🔄 Limpar Filtros", use_container_width=False):
                st.rerun()

        df_filtered = df_current.copy()
        if not df_filtered.empty:
            if f_id != "Todos":
                df_filtered = df_filtered[df_filtered["ID_PGI"].astype(str).str.contains(f_id, case=False, na=False)]
            if f_comprador != "Todos":
                df_filtered = df_filtered[df_filtered["Comprador"].astype(str).str.contains(f_comprador, case=False, na=False)]
            if f_grupo != "Todos":
                df_filtered = df_filtered[df_filtered["grupoinsumo"].astype(str).str.contains(f_grupo, case=False, na=False)]
            if f_obra != "Todos":
                df_filtered = df_filtered[df_filtered["obra"].astype(str).str.contains(f_obra, case=False, na=False)]

        col_header_tb1, col_header_tb2 = st.columns([2.5, 1.5])
        with col_header_tb1:
            st.markdown("<h3 class='styled-table-title'>📋 Gestão Consolidada de Processos de Cotação</h3>", unsafe_allow_html=True)
        with col_header_tb2:
            modo_visualizacao = st.radio(
                "Modo de Visualização:",
                ["📝 Planilha Interativa (Excel)", "👁️ Tabela Visual (Badges)"],
                horizontal=True,
                label_visibility="collapsed"
            )

        if not df_filtered.empty:
            # Ordenação de colunas consistente
            colunas_oficiais = [
                "ID_PGI", "obra", "tipo", "Comprador", "grupoinsumo", "cotacao",
                "orcamento", "due_dilligence", "equalizacao", "validacao_eng",
                "validacao_ger", "validacao_sup", "req_mega", "contr_mega",
                "param_fiscal", "minuta", "ass_digital", "credenciamento",
                "comunicar", "aud_pasta"
            ]
            
            # Garante que todas as colunas existem
            for col in colunas_oficiais:
                if col not in df_filtered.columns:
                    df_filtered[col] = "N/A"
                    
            df_edit_view = df_filtered[colunas_oficiais].copy().reset_index(drop=True)

            # ==================================================================
            # MODO 1: PLANILHA INTERATIVA ESTILO EXCEL (COM DROPDOWNS E VALIDAÇÕES)
            # ==================================================================
            if modo_visualizacao == "📝 Planilha Interativa (Excel)":
                render_html("""
                    <div style="background-color:#F4F6F9; padding: 10px 14px; border-radius: 4px; border-left: 4px solid #FF6F00; margin-bottom: 12px; font-size: 13px;">
                        💡 <strong>Modo Planilha Ativo:</strong> Clique diretamente sobre qualquer célula para editar ou selecionar opções nas listas suspensas. Ao concluir as alterações, clique no botão <strong>"💾 Salvar Alterações da Planilha"</strong> abaixo.
                    </div>
                """)

                # Garante que as opções dos dropdowns incluem os valores existentes para evitar inconsistências
                opcoes_obras = sorted(list(set(lista_obras_dynamic + [str(x) for x in df_edit_view["obra"].unique() if str(x).strip()])))
                opcoes_compradores = sorted(list(set(LISTA_COMPRADORES + [str(x) for x in df_edit_view["Comprador"].unique() if str(x).strip()])))
                opcoes_grupos = sorted(list(set(lista_grupo_insumo_dynamic + [str(x) for x in df_edit_view["grupoinsumo"].unique() if str(x).strip()])))
                
                # Configurações de colunas com listas suspensas e campos fixos
                configuracao_colunas = {
                    "ID_PGI": st.column_config.TextColumn("ID PGI", disabled=True, width="small"),
                    "obra": st.column_config.SelectboxColumn("Obra", options=opcoes_obras, required=True, width="medium"),
                    "tipo": st.column_config.SelectboxColumn("Tipo", options=LISTA_TIPOS, required=True, width="small"),
                    "Comprador": st.column_config.SelectboxColumn("Comprador", options=opcoes_compradores, required=True, width="medium"),
                    "grupoinsumo": st.column_config.SelectboxColumn("Grupo de Insumo", options=opcoes_grupos, width="medium"),
                    "cotacao": st.column_config.TextColumn("Escopo / Cotação", width="large"),
                    "orcamento": st.column_config.SelectboxColumn("Solic. Orç.", options=OPCOES_STATUS, width="small"),
                    "due_dilligence": st.column_config.SelectboxColumn("Due Dill.", options=OPCOES_STATUS, width="small"),
                    "equalizacao": st.column_config.SelectboxColumn("Equaliz.", options=OPCOES_STATUS, width="small"),
                    "validacao_eng": st.column_config.SelectboxColumn("Valid. Eng.", options=OPCOES_STATUS, width="small"),
                    "validacao_ger": st.column_config.SelectboxColumn("Valid. Ger.", options=OPCOES_STATUS, width="small"),
                    "validacao_sup": st.column_config.SelectboxColumn("Valid. Sup.", options=OPCOES_STATUS, width="small"),
                    "req_mega": st.column_config.TextColumn("Abertura RM", width="small"),
                    "contr_mega": st.column_config.TextColumn("Contrato Mega", width="small"),
                    "param_fiscal": st.column_config.SelectboxColumn("Param. Fiscal", options=OPCOES_STATUS, width="small"),
                    "minuta": st.column_config.SelectboxColumn("Minuta", options=OPCOES_STATUS, width="small"),
                    "ass_digital": st.column_config.SelectboxColumn("Ass. Digital", options=OPCOES_STATUS, width="small"),
                    "credenciamento": st.column_config.SelectboxColumn("Credenc. GT", options=OPCOES_STATUS, width="small"),
                    "comunicar": st.column_config.SelectboxColumn("Informar Eng.", options=OPCOES_STATUS, width="small"),
                    "aud_pasta": st.column_config.SelectboxColumn("Audit. Pasta", options=OPCOES_STATUS, width="small"),
                }

                # Componente nativo de edição em planilha
                df_editado_usuario = st.data_editor(
                    df_edit_view,
                    column_config=configuracao_colunas,
                    use_container_width=True,
                    num_rows="fixed",
                    hide_index=True,
                    key="editor_planilha_dashboard",
                    height=520
                )

                col_btn_salvar, col_btn_espaco = st.columns([2, 5])
                with col_btn_salvar:
                    if st.button("💾 Salvar Alterações da Planilha", type="primary", use_container_width=True):
                        # Detecta linhas com alterações entre o original e o editado
                        alteracoes_detectadas = 0
                        with st.spinner("Sincronizando alterações com a base de dados..."):
                            for idx, row_edit in df_editado_usuario.iterrows():
                                row_orig = df_edit_view.loc[idx]
                                diff_dict = {}
                                for col_name in colunas_oficiais:
                                    if col_name != "ID_PGI":
                                        val_orig = str(row_orig[col_name]).strip()
                                        val_edit = str(row_edit[col_name]).strip()
                                        if val_orig != val_edit:
                                            diff_dict[col_name] = val_edit
                                            
                                if diff_dict:
                                    pgi_alvo = str(row_edit["ID_PGI"]).strip()
                                    try:
                                        sb_client.update_list_item(pgi_alvo, diff_dict, list_name="PGI_GestaoCotacoes", id_column="ID_PGI")
                                        alteracoes_detectadas += 1
                                    except Exception as err:
                                        st.error(f"Erro ao atualizar ID {pgi_alvo}: {str(err)}")
                                        
                        if alteracoes_detectadas > 0:
                            st.cache_data.clear()
                            st.success(f"✔️ Sucesso! {alteracoes_detectadas} processo(s) atualizado(s) no sistema.")
                            st.rerun()
                        else:
                            st.info("ℹ️ Nenhuma alteração foi realizada na planilha.")

            # ==================================================================
            # MODO 2: VISUALIZAÇÃO COM BADGES COLORIDOS E AÇÕES RÁPIDAS
            # ==================================================================
            else:
                st.markdown("<div style='background-color:#F4F6F9; padding: 10px; border-radius: 4px; border-left: 4px solid #FF6F00; margin-bottom: 12px;'><strong>⚡ Ações Rápidas:</strong> Selecione o ID PGI desejado abaixo e clique para Editar em formulário ou Excluir o registro.</div>", unsafe_allow_html=True)
                col_ac1, col_ac2, col_ac3 = st.columns([2, 1, 1])
                with col_ac1:
                    action_pgi = st.selectbox("Selecione um Processo (ID PGI) para agir:", [""] + sorted(list(df_filtered["ID_PGI"].astype(str).unique())), label_visibility="collapsed")
                with col_ac2:
                    if st.button("✏️ Editar Registro", use_container_width=True, disabled=not action_pgi):
                        st.session_state.selected_pgi_to_edit = action_pgi
                        st.session_state.menu_option = "Gerenciamento de Registros"
                        st.rerun()
                with col_ac3:
                    if st.button("🗑️ Excluir Registro", use_container_width=True, disabled=not action_pgi):
                        st.session_state.confirm_delete_id = action_pgi
                        st.rerun()

                headers = [
                    "ID PGI", "Obra", "Tipo", "Comprador", "Grupo de Insumo", "Escopo / Cotação",
                    "Solic. Orç.", "Due Dill.", "Equaliz.", "Valid. Eng. (ER)", "Valid. Gerente (CO/GE)", "Valid. Suprimentos",
                    "Abertura RM", "Contrato MEGA", "Param. Fiscal", "Minuta", "Ass. Digital",
                    "Credenc. GT", "Informar Eng.", "Audit. Pasta"
                ]
                
                table_html = "<div style='overflow-x: auto; width: 100%; border: 1px solid #E2E8F0; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-top: 10px;'>"
                table_html += "<table style='width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 11px; min-width: 2300px;'>"
                table_html += "<thead style='background-color: #00205B; color: white; border-bottom: 3px solid #FF6F00;'>"
                table_html += "<tr>"
                for h in headers:
                    table_html += f"<th style='padding: 10px 12px; text-align: left; font-weight: 700; border: 1px solid rgba(255,255,255,0.1);'>{h}</th>"
                table_html += "</tr>"
                table_html += "</thead>"
                table_html += "<tbody>"
                
                for index, row in df_filtered.iterrows():
                    table_html += "<tr style='border-bottom: 1px solid #F4F6F9; background-color: white;'>"
                    
                    table_html += f"<td style='padding: 8px 12px; font-weight: 800; color: #00205B; border: 1px solid #F4F6F9;'>{row['ID_PGI']}</td>"
                    table_html += f"<td style='padding: 8px 12px; font-weight: 700; color: #FF6F00; border: 1px solid #F4F6F9;'>{row['obra']}</td>"
                    table_html += f"<td style='padding: 8px 12px; border: 1px solid #F4F6F9;'>{row['tipo']}</td>"
                    table_html += f"<td style='padding: 8px 12px; border: 1px solid #F4F6F9;'>{row['Comprador']}</td>"
                    table_html += f"<td style='padding: 8px 12px; border: 1px solid #F4F6F9;'>{row['grupoinsumo']}</td>"
                    table_html += f"<td style='padding: 8px 12px; font-weight: 600; border: 1px solid #F4F6F9;'>{row['cotacao']}</td>"
                    
                    table_html += f"<td style='padding: 8px 12px; border: 1px solid #F4F6F9;'>{get_html_status_badge(row['orcamento'])}</td>"
                    table_html += f"<td style='padding: 8px 12px; border: 1px solid #F4F6F9;'>{get_html_status_badge(row['due_dilligence'])}</td>"
                    table_html += f"<td style='padding: 8px 12px; border: 1px solid #F4F6F9;'>{get_html_status_badge(row['equalizacao'])}</td>"
                    table_html += f"<td style='padding: 8px 12px; border: 1px solid #F4F6F9;'>{get_html_status_badge(row['validacao_eng'])}</td>"
                    table_html += f"<td style='padding: 8px 12px; border: 1px solid #F4F6F9;'>{get_html_status_badge(row['validacao_ger'])}</td>"
                    table_html += f"<td style='padding: 8px 12px; border: 1px solid #F4F6F9;'>{get_html_status_badge(row['validacao_sup'])}</td>"
                    
                    table_html += f"<td style='padding: 8px 12px; border: 1px solid #F4F6F9;'>{get_html_status_badge(row['req_mega'])}</td>"
                    table_html += f"<td style='padding: 8px 12px; border: 1px solid #F4F6F9;'>{get_html_status_badge(row['contr_mega'])}</td>"
                    
                    table_html += f"<td style='padding: 8px 12px; border: 1px solid #F4F6F9;'>{get_html_status_badge(row['param_fiscal'])}</td>"
                    table_html += f"<td style='padding: 8px 12px; border: 1px solid #F4F6F9;'>{get_html_status_badge(row['minuta'])}</td>"
                    table_html += f"<td style='padding: 8px 12px; border: 1px solid #F4F6F9;'>{get_html_status_badge(row['ass_digital'])}</td>"
                    table_html += f"<td style='padding: 8px 12px; border: 1px solid #F4F6F9;'>{get_html_status_badge(row['credenciamento'])}</td>"
                    table_html += f"<td style='padding: 8px 12px; border: 1px solid #F4F6F9;'>{get_html_status_badge(row['comunicar'])}</td>"
                    table_html += f"<td style='padding: 8px 12px; border: 1px solid #F4F6F9;'>{get_html_status_badge(row['aud_pasta'])}</td>"
                    
                    table_html += "</tr>"
                
                table_html += "</tbody></table></div>"
                st.markdown(table_html, unsafe_allow_html=True)
        else:
            st.info("Nenhuma cotação localizada para os filtros selecionados.")

    # ==========================================================================
    # PAGE 2: LANÇAR NOVA COTAÇÃO (VERIFICAÇÃO RIGOROSA DE UNICIDADE)
    # ==========================================================================
    elif st.session_state.menu_option == "Adicionar ID":
        st.markdown("<h3 class='styled-table-title'>🆕 Cadastrar Novo ID de Processo</h3>", unsafe_allow_html=True)
        
        render_html("""
            <div class="info-card">
                <strong>🛡️ Regra de Negócio:</strong> Cada número de <b>ID PGI é estritamente único</b>. Selecione a obra correspondente, o Comprador responsável e o Tipo de Processo para iniciar o fluxo.
            </div>
        """)
        
        with st.form("new_record_form"):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                new_id = st.number_input("ID PGI (Número Único)", min_value=1, step=1, format="%d", value=49001)
                new_tipo = st.selectbox("Tipo de Processo", LISTA_TIPOS)
            with col_f2:
                new_obra = st.selectbox("Obra Relacionada", lista_obras_dynamic)
                new_comprador = st.selectbox("Comprador Responsável", LISTA_COMPRADORES)
                
            st.write("")
            submit_new = st.form_submit_button("💾 Salvar Novo ID")
            
            if submit_new:
                id_str = str(int(new_id)).strip()
                existing_ids_cache = [str(item.get("ID_PGI", "")).strip() for item in db_data_current]
                is_duplicate_live = verificar_id_duplicado_tempo_real(id_str)
                
                if not new_id:
                    st.error("❌ O ID PGI é obrigatório.")
                elif (id_str in existing_ids_cache) or is_duplicate_live:
                    st.error(f"❌ **Erro de Duplicidade:** O ID PGI **{id_str}** já existe no sistema! Não são permitidos IDs duplicados.")
                else:
                    if not sb_client:
                        st.error("❌ Conexão indisponível. Não foi possível registrar o ID.")
                    else:
                        try:
                            sp_payload = {
                                "ID_PGI": id_str,
                                "obra": str(new_obra),
                                "tipo": str(new_tipo),
                                "Comprador": str(new_comprador),
                                "grupoinsumo": "N/A",
                                "cotacao": f"PROCESSO PGI {id_str}",
                                "due_dilligence": "aguardando",
                                "equalizacao": "aguardando",
                                "orcamento": "aguardando",
                                "validacao_eng": "aguardando",
                                "validacao_ger": "aguardando",
                                "validacao_sup": "aguardando",
                                "req_mega": "aguardando",
                                "contr_mega": "aguardando",
                                "param_fiscal": "N/A",
                                "minuta": "N/A",
                                "ass_digital": "aguardando",
                                "credenciamento": "N/A",
                                "comunicar": "N/A",
                                "aud_pasta": "aguardando"
                            }
                            sb_client.insert_list_item(sp_payload, list_name="PGI_GestaoCotacoes")
                            st.cache_data.clear()
                            st.success(f"✔️ Sucesso! Processo {id_str} ({new_obra}) cadastrado com sucesso.")
                            st.session_state.menu_option = "Dashboard Geral"
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro ao cadastrar processo: {str(e)}")

    # ==========================================================================
    # PAGE 3: GERENCIAMENTO E EDIÇÃO DE REGISTROS (FORMULÁRIO DETALHADO)
    # ==========================================================================
    elif st.session_state.menu_option == "Gerenciamento de Registros":
        st.markdown("<h3 class='styled-table-title'>✏️ Atualizar Status e Fluxos das Cotações</h3>", unsafe_allow_html=True)
        
        if df_current.empty:
            st.warning("Nenhum dado disponível para edição.")
        else:
            list_ids = [f"{item['ID_PGI']} - {item.get('obra', 'N/A')} - {item['cotacao']}" for item in db_data_current]
            
            selected_idx_default = 0
            if st.session_state.selected_pgi_to_edit:
                selected_idx_default = next((i for i, item in enumerate(db_data_current) if str(item["ID_PGI"]) == str(st.session_state.selected_pgi_to_edit)), 0)
                st.session_state.selected_pgi_to_edit = None

            selected_option = st.selectbox("Selecione o Processo Interno para Editar", list_ids, index=selected_idx_default)
            
            if selected_option:
                selected_id = selected_option.split(" - ")[0]
                item_idx = next(i for i, item in enumerate(db_data_current) if str(item["ID_PGI"]) == str(selected_id))
                item = db_data_current[item_idx]
                
                with st.form("edit_record_form"):
                    render_html(f"""
                        <div style="background-color: #F4F6F9; padding: 8px 12px; border-radius: 4px; border-left: 4px solid #FF6F00; margin-bottom: 12px; font-size: 13px;">
                            <strong>Editando Registro:</strong> ID_PGI {item['ID_PGI']} | Obra: {item.get('obra', 'N/A')} | {item['cotacao']}
                        </div>
                    """)
                    
                    col_e1, col_e2, col_e3 = st.columns(3)
                    with col_e1:
                        st.markdown("<strong style='color:#00205B;'>Dados do Processo</strong>", unsafe_allow_html=True)
                        
                        obra_atual = str(item.get("obra", "N/A")).strip().upper()
                        idx_obra = lista_obras_dynamic.index(obra_atual) if obra_atual in lista_obras_dynamic else 0
                        edit_obra = st.selectbox("Obra Relacionada", lista_obras_dynamic, index=idx_obra)
                        
                        edit_tipo = st.selectbox("Tipo de Processo", LISTA_TIPOS, index=LISTA_TIPOS.index(item["tipo"]) if "tipo" in item and item["tipo"] in LISTA_TIPOS else 0)
                        edit_comprador = st.selectbox("Comprador Responsável", LISTA_COMPRADORES, index=LISTA_COMPRADORES.index(item["Comprador"]) if "Comprador" in item and item["Comprador"] in LISTA_COMPRADORES else 0)
                        
                        default_grupo_idx = 0
                        if "grupoinsumo" in item and item["grupoinsumo"] in lista_grupo_insumo_dynamic:
                            default_grupo_idx = lista_grupo_insumo_dynamic.index(item["grupoinsumo"])
                        edit_grupo = st.selectbox("Grupo de Insumo", lista_grupo_insumo_dynamic, index=default_grupo_idx)
                        
                        edit_dt_emissao = st.text_input("Data Emissão (DT_EMISSAO)", value=str(item.get("DT_EMISSAO", "")))
                        edit_grupointerno = st.text_input("Grupo Interno", value=str(item.get("grupointerno", "")))
                        edit_cotacao = st.text_input("Escopo de Cotação", value=item["cotacao"])
                        
                    with col_e2:
                        st.markdown("<strong style='color:#00205B;'>Validação & Compliance</strong>", unsafe_allow_html=True)
                        edit_orcamento = st.selectbox("Solicitar Orçamento", OPCOES_STATUS, index=OPCOES_STATUS.index(item["orcamento"]) if item["orcamento"] in OPCOES_STATUS else 0)
                        edit_due = st.selectbox("Due Diligence", OPCOES_STATUS, index=OPCOES_STATUS.index(item["due_dilligence"]) if item["due_dilligence"] in OPCOES_STATUS else 0)
                        edit_eq = st.selectbox("Equalização", OPCOES_STATUS, index=OPCOES_STATUS.index(item["equalizacao"]) if item["equalizacao"] in OPCOES_STATUS else 0)
                        edit_eng = st.selectbox("Valid. Engenharia (ER)", OPCOES_STATUS, index=OPCOES_STATUS.index(item["validacao_eng"]) if item["validacao_eng"] in OPCOES_STATUS else 0)
                        edit_ger = st.selectbox("Valid. Gerente (CO/GE)", OPCOES_STATUS, index=OPCOES_STATUS.index(item["validacao_ger"]) if item["validacao_ger"] in OPCOES_STATUS else 0)
                        edit_sup = st.selectbox("Valid. Gestão Suprimentos", OPCOES_STATUS, index=OPCOES_STATUS.index(item["validacao_sup"]) if item["validacao_sup"] in OPCOES_STATUS else 0)
                        
                    with col_e3:
                        st.markdown("<strong style='color:#00205B;'>Sistemas & Auditoria</strong>", unsafe_allow_html=True)
                        edit_req_val = str(item.get("req_mega", "aguardando"))
                        edit_req = st.text_input("Abertura Reclamação/RM (Mega) - Nº Inteiro", value=edit_req_val, help="Digite o número inteiro ou 'aguardando'/'N/A'")
                        
                        edit_contr_val = str(item.get("contr_mega", "aguardando"))
                        edit_contr = st.text_input("Contrato Mega - Nº Inteiro", value=edit_contr_val, help="Digite o número do Contrato MEGA ou 'aguardando'/'N/A'")
                        edit_param = st.selectbox("Parametrização Fiscal", OPCOES_STATUS, index=OPCOES_STATUS.index(item["param_fiscal"]) if item["param_fiscal"] in OPCOES_STATUS else 0)
                        edit_minuta = st.selectbox("Minuta Contratual", OPCOES_STATUS, index=OPCOES_STATUS.index(item["minuta"]) if item["minuta"] in OPCOES_STATUS else 0)
                        edit_ass = st.selectbox("Assinatura Eletrônica", OPCOES_STATUS, index=OPCOES_STATUS.index(item["ass_digital"]) if item["ass_digital"] in OPCOES_STATUS else 0)
                        edit_cred = st.selectbox("Credenciamento - GT", OPCOES_STATUS, index=OPCOES_STATUS.index(item["credenciamento"]) if item["credenciamento"] in OPCOES_STATUS else 0)
                        edit_comunicar = st.selectbox("Informar Engenheiro", OPCOES_STATUS, index=OPCOES_STATUS.index(item["comunicar"]) if item["comunicar"] in OPCOES_STATUS else 0)
                        edit_aud = st.selectbox("Audit. Pasta Final", OPCOES_STATUS, index=OPCOES_STATUS.index(item["aud_pasta"]) if item["aud_pasta"] in OPCOES_STATUS else 0)
                    
                    st.write("")
                    submit_edit = st.form_submit_button("💾 Salvar Alterações")
                    
                    if submit_edit:
                        req_clean = str(edit_req).strip()
                        contr_clean = str(edit_contr).strip()
                        
                        if req_clean and not req_clean.isdigit() and req_clean.lower() not in ["n/a", "aguardando"]:
                            st.error("⚠️ O campo 'Abertura Reclamação/RM' deve ser um número inteiro ou 'aguardando' / 'N/A'.")
                            st.stop()
                        if contr_clean and not contr_clean.isdigit() and contr_clean.lower() not in ["n/a", "aguardando"]:
                            st.error("⚠️ O campo 'Contrato Mega' deve ser um número inteiro ou 'aguardando' / 'N/A'.")
                            st.stop()
                            
                        updated_fields = {
                            "obra": str(edit_obra),
                            "DT_EMISSAO": str(edit_dt_emissao),
                            "tipo": str(edit_tipo),
                            "Comprador": str(edit_comprador),
                            "grupoinsumo": str(edit_grupo),
                            "grupointerno": str(edit_grupointerno),
                            "cotacao": str(edit_cotacao).upper(),
                            "due_dilligence": str(edit_due),
                            "equalizacao": str(edit_eq),
                            "orcamento": str(edit_orcamento),
                            "validacao_eng": str(edit_eng),
                            "validacao_ger": str(edit_ger),
                            "validacao_sup": str(edit_sup),
                            "req_mega": str(edit_req),
                            "contr_mega": str(edit_contr),
                            "param_fiscal": str(edit_param),
                            "minuta": str(edit_minuta),
                            "ass_digital": str(edit_ass),
                            "credenciamento": str(edit_cred),
                            "comunicar": str(edit_comunicar),
                            "aud_pasta": str(edit_aud)
                        }
                        
                        if not sb_client:
                            st.error("❌ Conexão indisponível. Operação não permitida.")
                        else:
                            try:
                                updated_fields["ID_PGI"] = selected_id
                                sb_client.update_list_item(selected_id, updated_fields, list_name="PGI_GestaoCotacoes", id_column="ID_PGI")
                                st.cache_data.clear()
                                st.success("✔️ Registro atualizado com sucesso!")
                                st.session_state.menu_option = "Dashboard Geral"
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro ao atualizar registro: {str(e)}")

    # ==========================================================================
    # PAGE 4: GESTÃO DE OBRAS (EXCLUSIVO ADMINISTRADOR)
    # ==========================================================================
    elif st.session_state.menu_option == "Gestão de Obras (Admin)":
        is_admin = st.session_state.get("user_perfil") == "administrador"
        if not is_admin:
            st.error("🔒 **Acesso Negado:** Módulo restrito a Administradores.")
            st.stop()

        st.markdown("<h3 class='styled-table-title'>🏗️ Gestão de Obras e Associação de Processos</h3>", unsafe_allow_html=True)
        
        tab_vincular, tab_obras_cad = st.tabs(["🔗 Associar Obra ao Processo", "➕ Cadastrar / Visualizar Obras"])
        
        with tab_vincular:
            st.markdown("<strong style='color:#00205B;'>Associação Rápida de Obra por Processo</strong>", unsafe_allow_html=True)
            if df_current.empty:
                st.info("Nenhum processo cadastrado para associar obras.")
            else:
                col_vo1, col_vo2 = st.columns([1.5, 1.5])
                with col_vo1:
                    list_pgi_select = [f"{it['ID_PGI']} - Obra Atual: {it.get('obra', 'N/A')} ({it['cotacao']})" for it in db_data_current]
                    sel_pgi_vinc = st.selectbox("Selecione o Processo (ID PGI)", list_pgi_select)
                with col_vo2:
                    sel_nova_obra = st.selectbox("Selecione a Obra de Destino", lista_obras_dynamic)
                
                if st.button("💾 Salvar Associação", use_container_width=True):
                    id_alvo = sel_pgi_vinc.split(" - ")[0]
                    try:
                        sb_client.update_list_item(id_alvo, {"obra": sel_nova_obra}, list_name="PGI_GestaoCotacoes", id_column="ID_PGI")
                        st.cache_data.clear()
                        st.success(f"✔️ Obra '{sel_nova_obra}' associada ao processo {id_alvo}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao associar: {str(e)}")
                        
                st.write("---")
                st.markdown("<strong style='color:#00205B;'>Processos Atualmente sem Obra (N/A)</strong>", unsafe_allow_html=True)
                df_sem_obra = df_current[df_current["obra"].isin(["N/A", "", "NONE"])]
                if not df_sem_obra.empty:
                    st.dataframe(df_sem_obra[["ID_PGI", "tipo", "Comprador", "cotacao"]], use_container_width=True)
                else:
                    st.success("🎉 Todos os processos cadastrados possuem obras devidamente associadas!")

        with tab_obras_cad:
            col_cad1, col_cad2 = st.columns([1.2, 1.8])
            with col_cad1:
                st.markdown("<strong style='color:#00205B;'>Cadastrar Nova Obra</strong>", unsafe_allow_html=True)
                with st.form("form_cad_obra"):
                    nome_nova_obra = st.text_input("Nome Reduzido da Obra", placeholder="Ex: Lumini").strip()
                    empresa_obra = st.selectbox("Empresa", ["Incorporação A.Yoshii", "Incorporação Yticon", "A.Yoshii Urbanismo"])
                    filial_obra = st.selectbox("Filial", ["Londrina", "Maringa", "Curitiba", "Campinas"])
                    btn_cad_obra = st.form_submit_button("Cadastrar Obra")
                    
                    if btn_cad_obra:
                        if not nome_nova_obra:
                            st.error("O nome da obra é obrigatório.")
                        else:
                            try:
                                payload_obra = {
                                    "nome_reduzido": nome_nova_obra,
                                    "empresa": empresa_obra,
                                    "filial": filial_obra
                                }
                                sb_client.insert_list_item(payload_obra, list_name="dSUPRI_Obras")
                                st.cache_data.clear()
                                st.success(f"✔️ Obra '{nome_nova_obra}' ({filial_obra}) cadastrada com sucesso!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao cadastrar obra: {str(e)}")
            
            with col_cad2:
                st.markdown("<strong style='color:#00205B;'>Obras Cadastradas no Sistema (Oficial)</strong>", unsafe_allow_html=True)
                dados_obras = carregar_obras_detalhadas()
                if dados_obras:
                    df_obras_view = pd.DataFrame(dados_obras)
                    colunas_exibir = [c for c in ["nome_reduzido", "empresa", "filial"] if c in df_obras_view.columns]
                    df_obras_view = df_obras_view[colunas_exibir].rename(
                        columns={"nome_reduzido": "Nome da Obra", "empresa": "Empresa", "filial": "Filial"}
                    )
                    st.dataframe(df_obras_view, use_container_width=True, height=360)
                else:
                    st.info("Nenhuma obra encontrada.")

    # ==========================================================================
    # PAGE 5: GESTÃO DE USUÁRIOS (EXCLUSIVO ADMINISTRADOR)
    # ==========================================================================
    elif st.session_state.menu_option == "Gestão de Usuários (Admin)":
        is_admin = st.session_state.get("user_perfil") == "administrador"
        if not is_admin:
            st.error("🔒 **Acesso Negado:** Módulo restrito a Administradores.")
            st.stop()

        st.markdown("<h3 class='styled-table-title'>👥 Gestão e Controle de Acessos de Usuários</h3>", unsafe_allow_html=True)

        lista_usuarios_atual = carregar_usuarios()
        df_users = pd.DataFrame(lista_usuarios_atual)

        if not df_users.empty:
            st.markdown("<strong style='color:#00205B;'>Usuários Cadastrados no Sistema</strong>", unsafe_allow_html=True)
            
            headers_users = ["Username / Login", "Nome Completo", "Perfil de Acesso", "Status da Conta"]
            u_html = "<div style='overflow-x: auto; width: 100%; border: 1px solid #E2E8F0; border-radius: 6px; margin-bottom: 20px;'>"
            u_html += "<table style='width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 12px;'>"
            u_html += "<thead style='background-color: #00205B; color: white; border-bottom: 3px solid #FF6F00;'>"
            u_html += "<tr>"
            for hu in headers_users:
                u_html += f"<th style='padding: 10px; text-align: left; font-weight: 700;'>{hu}</th>"
            u_html += "</tr></thead><tbody>"

            for _, row_u in df_users.iterrows():
                u_username = str(row_u.get("username", ""))
                u_nome = str(row_u.get("nome", ""))
                u_perfil = str(row_u.get("perfil", "comprador")).title()
                u_ativo = row_u.get("ativo", True)
                
                status_tag = '<span style="background-color:#EAF7EE; color:#28A745; font-weight:800; padding:2px 8px; border-radius:12px; font-size:10px; border:1px solid #28A745;">ATIVO</span>' if u_ativo else '<span style="background-color:#F8D7DA; color:#721C24; font-weight:800; padding:2px 8px; border-radius:12px; font-size:10px; border:1px solid #721C24;">INATIVO</span>'
                perfil_tag = f'<span style="color:#FF6F00; font-weight:800;">👑 {u_perfil}</span>' if u_perfil.lower() == "administrador" else f'<span style="color:#00205B; font-weight:600;">💼 {u_perfil}</span>'

                u_html += "<tr style='border-bottom: 1px solid #F4F6F9; background-color: white;'>"
                u_html += f"<td style='padding: 8px 12px; font-weight: 800; color: #00205B;'>{u_username}</td>"
                u_html += f"<td style='padding: 8px 12px;'>{u_nome}</td>"
                u_html += f"<td style='padding: 8px 12px;'>{perfil_tag}</td>"
                u_html += f"<td style='padding: 8px 12px;'>{status_tag}</td>"
                u_html += "</tr>"

            u_html += "</tbody></table></div>"
            st.markdown(u_html, unsafe_allow_html=True)

        tab_cad, tab_edit = st.tabs(["➕ Cadastrar Novo Usuário", "✏️ Editar Usuário Existente"])

        with tab_cad:
            with st.form("form_novo_usuario"):
                st.markdown("<strong style='color:#00205B;'>Formulário de Cadastro de Novo Usuário</strong>", unsafe_allow_html=True)
                col_u1, col_u2 = st.columns(2)
                with col_u1:
                    new_u_username = st.text_input("Login / Username (ex: matheus.fava)", placeholder="Digite o login...").strip().lower()
                    new_u_nome = st.text_input("Nome Completo", placeholder="Ex: Matheus Fava")
                with col_u2:
                    new_u_senha = st.text_input("Senha de Acesso", type="password", placeholder="Digite a senha...")
                    new_u_perfil = st.selectbox("Perfil de Acesso", ["comprador", "administrador"], help="Administradores podem gerenciar obras, usuários e fluxos.")
                    new_u_ativo = st.checkbox("Manter Conta Ativa", value=True)

                submit_new_u = st.form_submit_button("💾 Salvar Usuário")

                if submit_new_u:
                    if not new_u_username or not new_u_nome or not new_u_senha:
                        st.error("❌ Username, Nome Completo e Senha são obrigatórios.")
                    else:
                        existing_usernames = [str(x.get("username", "")).lower() for x in lista_usuarios_atual]
                        if new_u_username in existing_usernames:
                            st.error(f"❌ O username '{new_u_username}' já existe no sistema.")
                        elif not sb_client:
                            st.error("❌ Conexão indisponível.")
                        else:
                            user_payload = {
                                "username": new_u_username,
                                "nome": new_u_nome,
                                "senha": new_u_senha,
                                "perfil": new_u_perfil,
                                "ativo": new_u_ativo
                            }
                            try:
                                sb_client.insert_list_item(user_payload, list_name="usuarios")
                                st.cache_data.clear()
                                st.success(f"✔️ Usuário '{new_u_username}' cadastrado com sucesso!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro ao salvar usuário: {str(e)}")

        with tab_edit:
            if not lista_usuarios_atual:
                st.info("Nenhum usuário cadastrado para edição.")
            else:
                user_options = [f"{u.get('username')} - {u.get('nome')} ({u.get('perfil')})" for u in lista_usuarios_atual]
                selected_user_str = st.selectbox("Selecione o Usuário para Editar", user_options)
                
                if selected_user_str:
                    sel_username = selected_user_str.split(" - ")[0]
                    selected_u_dict = next((u for u in lista_usuarios_atual if str(u.get("username")) == str(sel_username)), {})

                    with st.form("form_editar_usuario"):
                        render_html(f"""
                            <div style="background-color: #F4F6F9; padding: 8px 12px; border-radius: 4px; border-left: 4px solid #00205B; margin-bottom: 12px; font-size: 13px;">
                                <strong>Editando Acesso:</strong> {selected_u_dict.get('username')} ({selected_u_dict.get('nome')})
                            </div>
                        """)
                        col_eu1, col_eu2 = st.columns(2)
                        with col_eu1:
                            edit_u_nome = st.text_input("Nome Completo", value=selected_u_dict.get("nome", ""))
                            edit_u_senha = st.text_input("Senha de Acesso", value=selected_u_dict.get("senha", ""), type="password")
                        with col_eu2:
                            current_perfil = selected_u_dict.get("perfil", "comprador")
                            edit_u_perfil = st.selectbox(
                                "Perfil de Acesso", 
                                ["comprador", "administrador"], 
                                index=0 if current_perfil == "comprador" else 1
                            )
                            edit_u_ativo = st.checkbox("Conta Ativa", value=bool(selected_u_dict.get("ativo", True)))

                        submit_edit_u = st.form_submit_button("💾 Salvar Alterações")

                        if submit_edit_u:
                            if not edit_u_nome or not edit_u_senha:
                                st.error("❌ Nome e Senha são campos obrigatórios.")
                            elif not sb_client:
                                st.error("❌ Conexão indisponível.")
                            else:
                                updated_u_payload = {
                                    "username": sel_username,
                                    "nome": edit_u_nome,
                                    "senha": edit_u_senha,
                                    "perfil": edit_u_perfil,
                                    "ativo": edit_u_ativo
                                }
                                try:
                                    sb_client.update_list_item(
                                        item_id=sel_username, 
                                        item_data=updated_u_payload, 
                                        list_name="usuarios", 
                                        id_column="username"
                                    )
                                    st.cache_data.clear()
                                    st.success(f"✔️ Dados de '{sel_username}' atualizados com sucesso!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Erro ao atualizar usuário: {str(e)}")

import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

# Adiciona o diretório atual ao path para garantir que possamos importar o módulo de autenticação
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from sharepoint_auth import SharePointOAuthClient
except ImportError:
    # Fallback caso o arquivo esteja rodando isoladamente
    SharePointOAuthClient = None

# Configuração da página e visual premium do Grupo A.Yoshii
st.set_page_config(
    page_title="PGI - Gestão de Cotações v5",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- PALETA DE CORES INSTITUCIONAIS (A.YOSHII) ---
# Azul Escuro Institucional (Pantone 2768 C): #00205B
# Laranja Vibrante Institucional (Pantone 1505 C): #FF6F00
# Cinza Escuro (Pantone 426 C): #1E1E1E
# Cinza Médio (Pantone 423 C): #8C8C8C
# Cinza Claro (Fundo/Bordas): #F4F6F9

# Estilização CSS customizada para atender rigidamente ao Manual de Aplicação da Marca
st.markdown("""
    <style>
    /* Estilização da Barra Lateral (Sidebar) para Fundo Azul Institucional */
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
    
    /* Configuração de inputs e botões na barra lateral */
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
    
    /* Cabeçalho Premium - Logo Integrada e Altura Mínima Otimizada */
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
    
    /* Cards de Métricas Customizados (Substituição do default do Streamlit - Mais Compactos) */
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
    
    /* Cards Informativos Estilizados */
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
    .info-card p:last-child {
        margin-bottom: 0;
    }
    
    .success-card {
        background-color: #EAF7EE;
        border-left: 5px solid #28A745;
        padding: 12px;
        border-radius: 4px;
        margin-bottom: 15px;
        color: #1E1E1E;
    }
    .success-card h4, .success-card p {
        color: #1E1E1E !important;
        margin: 0 0 6px 0;
    }
    .success-card p:last-child {
        margin-bottom: 0;
    }
    
    /* Customização Geral de Inputs e Selectboxes */
    div[data-baseweb="input"] {
        border-radius: 4px !important;
    }
    
    /* Botões Gerais de Ação do Aplicativo */
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
    
    /* Estilos das tabelas */
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
    """
    Filtra novas linhas e espaços extras para evitar que o markdown do Streamlit
    interprete tags HTML recuadas como blocos de código markdown.
    Elimina erros visuais como '</div>' vazados na tela.
    """
    clean_html = "".join([line.strip() for line in html_str.split("\n")])
    st.markdown(clean_html, unsafe_allow_html=True)

# --- DEFINIÇÃO DE LOGO EM SVG (VETORIAL E EXATA) ---
def get_logo_svg(theme="dark", width=145, height=30):
    """
    Gera o SVG exato da logomarca A.Yoshii respeitando o Manual de Aplicação.
    O quadrado laranja (#FF6F00) abriga o círculo azul (#00205B) com o símbolo AY em branco.
    A tipografia A.YOSHII varia de cor (Branco no tema dark/azul, e Azul no tema light/branco).
    """
    text_color = "#FFFFFF" if theme == "dark" else "#00205B"
    return f'<svg width="{width}" height="{height}" viewBox="0 0 220 45" xmlns="http://www.w3.org/2000/svg" style="vertical-align: middle;"><rect x="2" y="2" width="41" height="41" rx="4" fill="#FF6F00" /><circle cx="22.5" cy="22.5" r="16.5" fill="#00205B" /><path d="M 16,29 L 21.5,14 L 23.5,14 L 29,29" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/><line x1="18.5" y1="23.5" x2="26.5" y2="23.5" stroke="#FFFFFF" stroke-width="2.5" /><path d="M 25.5,23.5 L 29,31.5" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" /><text x="52" y="32" font-family="Helvetica, Arial, sans-serif" font-size="23" font-weight="900" fill="{text_color}" letter-spacing="1">A.YOSHII</text></svg>'

# --- CONFIGURAÇÕES DE INTEGRAÇÃO (SALVAS EM SESSION STATE) ---
if "sp_tenant_id" not in st.session_state:
    st.session_state.sp_tenant_id = ""
if "sp_client_id" not in st.session_state:
    st.session_state.sp_client_id = ""
if "sp_client_secret" not in st.session_state:
    st.session_state.sp_client_secret = ""
if "sp_connected" not in st.session_state:
    st.session_state.sp_connected = False
if "db_mode" not in st.session_state:
    st.session_state.db_mode = "Simulado"  # Modos: 'Simulado' ou 'SharePoint (Live)'

# --- SESSÃO DE AUTENTICAÇÃO DO USUÁRIO NO APP (LOGIN) ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login(username, password):
    if username == "admin" and password == "1234":
        st.session_state.logged_in = True
        st.session_state.user = "Administrador"
        st.success("Login realizado com sucesso!")
        st.rerun()
    else:
        st.error("Usuário ou senha incorretos.")

def logout():
    st.session_state.logged_in = False
    st.session_state.pop("user", None)
    st.rerun()

# --- MODELAGEM DE DADOS DO SHAREPOINT (SIMULADA COMO BASELINE) ---
if "db_data" not in st.session_state:
    st.session_state.db_data = [
        {
            "ID_PGI": "45242",
            "cotacao": "INOX E VIDRO HORIZON",
            "due_dilligence": "OK",
            "equalizacao": "OK",
            "orcamento": "Matias",
            "validacao_eng": "OK",
            "validacao_ger": "OK",
            "validacao_sup": "OK",
            "req_mega": "OK",
            "contr_mega": "OK",
            "param_fiscal": "OK",
            "minuta": "OK",
            "ass_digital": "OK",
            "credenciamento": "OK",
            "comunicar": "OK",
            "savings": "1050.00",
            "aud_pasta": "OK",
            "valor_fechado": "28002.46"
        },
        {
            "ID_PGI": "48287",
            "cotacao": "ADITIVO FUNDAÇÃO ALTANA - HCM",
            "due_dilligence": "OK",
            "equalizacao": "OK",
            "orcamento": "OK",
            "validacao_eng": "OK",
            "validacao_ger": "OK",
            "validacao_sup": "OK",
            "req_mega": "OK",
            "contr_mega": "OK",
            "param_fiscal": "N/A",
            "minuta": "N/A",
            "ass_digital": "N/A",
            "credenciamento": "N/A",
            "comunicar": "N/A",
            "savings": "5827.90",
            "aud_pasta": "N/A",
            "valor_fechado": "110730.10"
        },
        {
            "ID_PGI": "47597",
            "cotacao": "ADITIVO TERRAPLANAGEM GAIA",
            "due_dilligence": "OK",
            "equalizacao": "OK",
            "orcamento": "N/A",
            "validacao_eng": "N/A",
            "validacao_ger": "OK",
            "validacao_sup": "OK",
            "req_mega": "OK",
            "contr_mega": "OK",
            "param_fiscal": "N/A",
            "minuta": "N/A",
            "ass_digital": "N/A",
            "credenciamento": "N/A",
            "comunicar": "N/A",
            "savings": "0.00",
            "aud_pasta": "N/A",
            "valor_fechado": "221779.96"
        },
        {
            "ID_PGI": "46252",
            "cotacao": "GAIA ELÉTRICA ALLEGRO",
            "due_dilligence": "OK",
            "equalizacao": "OK",
            "orcamento": "N/A",
            "validacao_eng": "OK",
            "validacao_ger": "OK",
            "validacao_sup": "OK",
            "req_mega": "OK",
            "contr_mega": "OK",
            "param_fiscal": "OK",
            "minuta": "OK",
            "ass_digital": "aguardando",
            "credenciamento": "OK",
            "comunicar": "OK",
            "savings": "75000.00",
            "aud_pasta": "aguardando",
            "valor_fechado": "980000.00"
        },
        {
            "ID_PGI": "43405",
            "cotacao": "PAISAGISMO DUETTO",
            "due_dilligence": "OK",
            "equalizacao": "OK",
            "orcamento": "N/A",
            "validacao_eng": "OK",
            "validacao_ger": "OK",
            "validacao_sup": "OK",
            "req_mega": "OK",
            "contr_mega": "OK",
            "param_fiscal": "OK",
            "minuta": "OK",
            "ass_digital": "aguardando",
            "credenciamento": "OK",
            "comunicar": "N/A",
            "savings": "52406.72",
            "aud_pasta": "aguardando",
            "valor_fechado": "145073.39"
        },
        {
            "ID_PGI": "47085",
            "cotacao": "APLICAÇÃO DE FUNDO LIV",
            "due_dilligence": "OK",
            "equalizacao": "OK",
            "orcamento": "N/A",
            "validacao_eng": "OK",
            "validacao_ger": "OK",
            "validacao_sup": "OK",
            "req_mega": "OK",
            "contr_mega": "OK",
            "param_fiscal": "N/A",
            "minuta": "OK",
            "ass_digital": "aguardando",
            "credenciamento": "N/A",
            "comunicar": "N/A",
            "savings": "0.00",
            "aud_pasta": "aguardando",
            "valor_fechado": "16320.00"
        }
    ]

# Opções padronizadas de status para garantir integridade das colunas de texto do SharePoint
OPCOES_STATUS = ["OK", "N/A", "aguardando"]

# Instancia o cliente SharePoint caso as credenciais estejam ativas e o modo de produção selecionado
sp_client = None
if st.session_state.sp_connected and SharePointOAuthClient:
    sp_client = SharePointOAuthClient(
        tenant_id=st.session_state.sp_tenant_id,
        client_id=st.session_state.sp_client_id,
        client_secret=st.session_state.sp_client_secret
    )

# --- SEÇÃO DE CARREGAMENTO DINÂMICO DE DADOS ---
def carregar_dados():
    if st.session_state.db_mode == "SharePoint (Live)" and sp_client:
        try:
            items = sp_client.get_list_items()
            dados_mapeados = []
            for item in items:
                dados_mapeados.append({
                    "ID_PGI": str(item.get("ID_PGI", item.get("ID", ""))),
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
                    "savings": str(item.get("savings", "0.00")),
                    "aud_pasta": str(item.get("aud_pasta", "aguardando")),
                    "valor_fechado": str(item.get("valor_fechado", "0.00"))
                })
            return dados_mapeados
        except Exception as e:
            st.sidebar.error(f"⚠️ Erro ao ler dados do SharePoint: {str(e)}")
            st.sidebar.warning("🔄 Redirecionando automaticamente para o modo de simulação.")
            st.session_state.db_mode = "Simulado"
            return st.session_state.db_data
    else:
        return st.session_state.db_data

# --- TELA DE LOGIN ---
if not st.session_state.logged_in:
    logo_light = get_logo_svg(theme="light", width=180, height=38)
    render_html(f"""
        <div style="text-align: center; margin-top: 30px; margin-bottom: 15px;">
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
            
            username_input = st.text_input("Usuário", placeholder="ID do comprador (ex: admin)")
            password_input = st.text_input("Senha", type="password", placeholder="Digite a sua senha corporativa...")
            
            submit_button = st.form_submit_button("Acessar Painel")
            if submit_button:
                login(username_input, password_input)
                
        render_html("""
            <div style="background-color: #F4F6F9; border-top: 3px solid #FF6F00; padding: 10px; border-radius: 4px; margin-top: 10px; text-align: center;">
                <p style="margin: 0; font-size: 10px; color: #1E1E1E;">
                    💡 <strong>Credenciais de Demonstração:</strong><br>
                    Usuário: <code style="background-color: #E2E8F0; padding: 1px 3px; border-radius: 2px;">admin</code> | 
                    Senha: <code style="background-color: #E2E8F0; padding: 1px 3px; border-radius: 2px;">1234</code>
                </p>
            </div>
        """)

# --- TELA PRINCIPAL (APÓS LOGIN) ---
else:
    db_data_current = carregar_dados()
    df_current = pd.DataFrame(db_data_current)

    # Sidebar de Navegação e Configurações (Cores e Ícones Corporativos)
    with st.sidebar:
        logo_dark = get_logo_svg(theme="dark", width=145, height=30)
        render_html(f"""
            <div style="padding: 5px 0; border-bottom: 1px solid rgba(255,255,255,0.15); margin-bottom: 10px; text-align: center;">
                {logo_dark}
            </div>
        """)
        
        st.markdown(f"👤 **Comprador Ativo:** `{st.session_state.user}`")
        
        st.write("---")
        st.subheader("🗄️ Origem dos Dados")
        
        if st.session_state.sp_connected:
            options_mode = ["Simulado", "SharePoint (Live)"]
            selected_mode = st.radio(
                "Alternar Base de Dados",
                options_mode,
                index=options_mode.index(st.session_state.db_mode)
            )
            if selected_mode != st.session_state.db_mode:
                st.session_state.db_mode = selected_mode
                st.rerun()
        else:
            render_html("""
                <div style="background-color: rgba(255,111,0,0.15); border: 1px solid #FF6F00; padding: 6px; border-radius: 4px; font-size: 11px; margin-bottom: 8px;">
                    ⚠️ <strong>SharePoint Desconectado.</strong> Executando modo simulado.
                </div>
            """)
            st.session_state.db_mode = "Simulado"
            
        st.write("---")
        menu_option = st.radio(
            "Navegação",
            ["Dashboard Geral", "Lançar Nova Cotação", "Gerenciamento de Registros", "Integração SharePoint"]
        )
        
        st.write("---")
        if st.button("🚪 Sair do Aplicativo"):
            logout()
            
    # Título do Painel Conectado (Identidade A.Yoshii Premium - Compactado)
    logo_header = get_logo_svg(theme="dark", width=120, height=25)
    render_html(f"""
        <div class="title-container">
            <div class="title-text-box">
                <div class="title-main">Gestão de Cotações de Suprimentos</div>
                <div class="title-sub">Bases de Dados Integradas: DPTO_SUPRIMENTOS / PGI_GestaoCotacoes</div>
            </div>
            <div style="padding: 2px;">
                {logo_header}
            </div>
        </div>
    """)

    # PAGE 1: DASHBOARD GERAL
    if menu_option == "Dashboard Geral":
        st.markdown(f"<h3 class='styled-table-title'>📊 Indicadores de Performance ({st.session_state.db_mode})</h3>", unsafe_allow_html=True)
        
        # Faz o parsing seguro das colunas do SharePoint (que chegam como texto)
        df_calc = df_current.copy()
        if not df_calc.empty:
            df_calc["valor_fechado_num"] = df_calc["valor_fechado"].astype(float)
            df_calc["savings_num"] = df_calc["savings"].astype(float)
            
            total_fechado = df_calc["valor_fechado_num"].sum()
            total_savings = df_calc["savings_num"].sum()
            media_savings = df_calc["savings_num"].mean()
            taxa_economia = (total_savings / (total_fechado + total_savings)) * 100 if (total_fechado + total_savings) > 0 else 0
        else:
            total_fechado = total_savings = media_savings = taxa_economia = 0
        
        # Exibição de Métricas Principais usando Cards Customizados (Manual de Identidade Visual - Compactado)
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        
        with col_m1:
            render_html(f"""
                <div class="metric-card-custom">
                    <div class="metric-label">Total de Processos</div>
                    <div class="metric-value">{len(df_calc)}</div>
                </div>
            """)
            
        with col_m2:
            val_f = f"R$ {total_fechado:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            render_html(f"""
                <div class="metric-card-custom">
                    <div class="metric-label">Valor Total Fechado</div>
                    <div class="metric-value">{val_f}</div>
                </div>
            """)
            
        with col_m3:
            val_s = f"R$ {total_savings:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            render_html(f"""
                <div class="metric-card-custom orange-border">
                    <div class="metric-label">Total de Savings Gerados</div>
                    <div class="metric-value" style="color: #FF6F00;">{val_s}</div>
                </div>
            """)
            
        with col_m4:
            render_html(f"""
                <div class="metric-card-custom">
                    <div class="metric-label">Taxa Média de Economia</div>
                    <div class="metric-value">{taxa_economia:.2f}%</div>
                </div>
            """)
        
        st.write("")
        st.markdown("<h3 class='styled-table-title'>📋 Lista Consolidada de Processos de Cotação</h3>", unsafe_allow_html=True)
        
        if not df_current.empty:
            st.dataframe(
                df_current[[
                    "ID_PGI", "cotacao", "due_dilligence", "equalizacao", "validacao_eng", 
                    "req_mega", "contr_mega", "minuta", "ass_digital", "savings", "aud_pasta"
                ]].rename(columns={
                    "ID_PGI": "ID PGI",
                    "cotacao": "Escopo de Cotação",
                    "due_dilligence": "Due Diligence",
                    "equalizacao": "Equalização",
                    "validacao_eng": "Valid. Engenharia",
                    "req_mega": "Req. Mega",
                    "contr_mega": "Contrato Mega",
                    "minuta": "Minuta",
                    "ass_digital": "Ass. Digital",
                    "savings": "Savings (R$)",
                    "aud_pasta": "Audit. Pasta"
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Nenhuma cotação localizada nesta base de dados.")

    # PAGE 2: LANÇAR NOVA COTAÇÃO
    elif menu_option == "Lançar Nova Cotação":
        st.markdown(f"<h3 class='styled-table-title'>🆕 Cadastrar Novo Processo Interno ({st.session_state.db_mode})</h3>", unsafe_allow_html=True)
        
        render_html("""
            <div class="info-card">
                <strong>🛡️ Controle de Integridade do Ecossistema:</strong> Como todas as colunas de dados da nossa lista 
                <code>PGI_GestaoCotacoes</code> do SharePoint estão estruturadas como <strong>Texto Puro (Single Line of Text)</strong>, 
                o front-end deste aplicativo realiza o encapsulamento, normalização e validações financeiras e numéricas 
                antes do envio para evitar corrupção das informações.
            </div>
        """)
        
        with st.form("new_record_form"):
            col_f1, col_f2 = st.columns(2)
            
            with col_f1:
                st.markdown("<strong style='color:#00205B;'>Dados Gerais da Cotação</strong>", unsafe_allow_html=True)
                new_id = st.text_input("ID_PGI", placeholder="Ex: 49001")
                new_cotacao = st.text_input("Escopo / Cotação", placeholder="Ex: CONTRATAÇÃO DE DRYWALL")
                new_valor = st.number_input("Valor Fechado (R$)", min_value=0.0, step=100.0, format="%.2f")
                new_savings = st.number_input("Savings Alcançado (R$)", min_value=0.0, step=100.0, format="%.2f")
                new_orcamento = st.text_input("Solicitante / Orçamento", placeholder="Ex: OK")
                
            with col_f2:
                st.markdown("<strong style='color:#00205B;'>Etapas de Validação Inicial</strong>", unsafe_allow_html=True)
                new_due = st.selectbox("Due Diligence", OPCOES_STATUS)
                new_eq = st.selectbox("Equalização", OPCOES_STATUS)
                new_eng = st.selectbox("Validação Engenharia (ER)", OPCOES_STATUS)
                new_ger = st.selectbox("Validação Coordenador/Gerente (CO/GE)", OPCOES_STATUS)
                new_sup = st.selectbox("Validação Gestão Suprimentos", OPCOES_STATUS)
                
            st.markdown("<hr style='border-color:#F4F6F9;'>", unsafe_allow_html=True)
            col_f3, col_f4 = st.columns(2)
            with col_f3:
                st.markdown("<strong style='color:#00205B;'>Etapas de Contratação & Sistemas</strong>", unsafe_allow_html=True)
                new_req = st.selectbox("Abertura Reclamação/RM (Mega)", OPCOES_STATUS)
                new_contr = st.selectbox("Contrato Mega", OPCOES_STATUS)
                new_param = st.selectbox("Parametrização Fiscal", OPCOES_STATUS)
                new_minuta = st.selectbox("Minuta Contratual", OPCOES_STATUS)
            with col_f4:
                st.markdown("<strong style='color:#00205B;'>Assinatura & Auditoria de Pasta</strong>", unsafe_allow_html=True)
                new_ass = st.selectbox("Assinatura Eletrônica", OPCOES_STATUS)
                new_cred = st.selectbox("Credenciamento - GT", OPCOES_STATUS)
                new_comunicar = st.selectbox("Informar Engenheiro", OPCOES_STATUS)
                new_aud = st.selectbox("Auditar Pasta Final", OPCOES_STATUS)

            st.write("")
            submit_new = st.form_submit_button("💾 Salvar Registro e Enviar")
            
            if submit_new:
                if not new_id or not new_cotacao:
                    st.error("❌ Os campos ID_PGI e Escopo/Cotação são obrigatórios.")
                elif new_id in df_current["ID_PGI"].values:
                    st.error(f"❌ Erro de Unicidade: Já existe um registro com o ID_PGI '{new_id}'.")
                else:
                    new_item = {
                        "ID_PGI": str(new_id),
                        "cotacao": str(new_cotacao).upper(),
                        "due_dilligence": str(new_due),
                        "equalizacao": str(new_eq),
                        "orcamento": str(new_orcamento) if new_orcamento else "OK",
                        "validacao_eng": str(new_eng),
                        "validacao_ger": str(new_ger),
                        "validacao_sup": str(new_sup),
                        "req_mega": str(new_req),
                        "contr_mega": str(new_contr),
                        "param_fiscal": str(new_param),
                        "minuta": str(new_minuta),
                        "ass_digital": str(new_ass),
                        "credenciamento": str(new_cred),
                        "comunicar": str(new_comunicar),
                        "savings": f"{new_savings:.2f}",
                        "aud_pasta": str(new_aud),
                        "valor_fechado": f"{new_valor:.2f}"
                    }
                    
                    if st.session_state.db_mode == "SharePoint (Live)" and sp_client:
                        try:
                            sp_payload = {
                                "Title": str(new_cotacao).upper(),
                                "ID_PGI": str(new_id),
                                "cotacao": str(new_cotacao).upper(),
                                "due_dilligence": str(new_due),
                                "equalizacao": str(new_eq),
                                "orcamento": str(new_orcamento),
                                "validacao_eng": str(new_eng),
                                "validacao_ger": str(new_ger),
                                "validacao_sup": str(new_sup),
                                "req_mega": str(new_req),
                                "contr_mega": str(new_contr),
                                "param_fiscal": str(new_param),
                                "minuta": str(new_minuta),
                                "ass_digital": str(new_ass),
                                "credenciamento": str(new_cred),
                                "comunicar": str(new_comunicar),
                                "savings": f"{new_savings:.2f}",
                                "aud_pasta": str(new_aud),
                                "valor_fechado": f"{new_valor:.2f}"
                            }
                            sp_client.insert_list_item(sp_payload)
                            st.success(f"✔️ Sucesso! Processo {new_id} salvo diretamente no SharePoint.")
                        except Exception as e:
                            st.error(f"❌ Erro ao gravar no SharePoint: {str(e)}")
                    else:
                        st.session_state.db_data.append(new_item)
                        st.success(f"✔️ Sucesso! Processo {new_id} registrado localmente (Base Simulada).")
                        
                    st.rerun()

    # PAGE 3: GERENCIAMENTO E EDIÇÃO DE REGISTROS
    elif menu_option == "Gerenciamento de Registros":
        st.markdown("<h3 class='styled-table-title'>✏️ Atualizar Status e Fluxos das Cotações</h3>", unsafe_allow_html=True)
        
        if df_current.empty:
            st.warning("Nenhum dado disponível para edição.")
        else:
            list_ids = [f"{item['ID_PGI']} - {item['cotacao']}" for item in db_data_current]
            selected_option = st.selectbox("Selecione o Processo Interno para Editar", list_ids)
            
            if selected_option:
                selected_id = selected_option.split(" - ")[0]
                item_idx = next(i for i, item in enumerate(db_data_current) if item["ID_PGI"] == selected_id)
                item = db_data_current[item_idx]
                
                with st.form("edit_record_form"):
                    render_html(f"""
                        <div style="background-color: #F4F6F9; padding: 8px 12px; border-radius: 4px; border-left: 4px solid #FF6F00; margin-bottom: 12px; font-size: 13px;">
                            <strong>Editando Registro Ativo:</strong> ID_PGI {item['ID_PGI']} | {item['cotacao']}
                        </div>
                    """)
                    
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        st.markdown("<strong style='color:#00205B;'>Dados do Processo</strong>", unsafe_allow_html=True)
                        edit_cotacao = st.text_input("Escopo de Cotação", value=item["cotacao"])
                        edit_valor = st.number_input("Valor Fechado (R$)", value=float(item["valor_fechado"]), step=100.0, format="%.2f")
                        edit_savings = st.number_input("Savings (R$)", value=float(item["savings"]), step=100.0, format="%.2f")
                        edit_orcamento = st.text_input("Orçamento / Solicitante", value=item["orcamento"])
                        
                        st.markdown("<br><strong style='color:#00205B;'>Status de Compliance e Validação</strong>", unsafe_allow_html=True)
                        edit_due = st.selectbox("Due Diligence", OPCOES_STATUS, index=OPCOES_STATUS.index(item["due_dilligence"]) if item["due_dilligence"] in OPCOES_STATUS else 0)
                        edit_eq = st.selectbox("Equalização", OPCOES_STATUS, index=OPCOES_STATUS.index(item["equalizacao"]) if item["equalizacao"] in OPCOES_STATUS else 0)
                        edit_eng = st.selectbox("Valid. Engenharia (ER)", OPCOES_STATUS, index=OPCOES_STATUS.index(item["validacao_eng"]) if item["validacao_eng"] in OPCOES_STATUS else 0)
                        
                    with col_e2:
                        st.markdown("<strong style='color:#00205B;'>Aprovações Suprimentos</strong>", unsafe_allow_html=True)
                        edit_ger = st.selectbox("Valid. Gerente (CO/GE)", OPCOES_STATUS, index=OPCOES_STATUS.index(item["validacao_ger"]) if item["validacao_ger"] in OPCOES_STATUS else 0)
                        edit_sup = st.selectbox("Valid. Gestão Suprimentos", OPCOES_STATUS, index=OPCOES_STATUS.index(item["validacao_sup"]) if item["validacao_sup"] in OPCOES_STATUS else 0)
                        edit_req = st.selectbox("Abertura Reclamação/RM (Mega)", OPCOES_STATUS, index=OPCOES_STATUS.index(item["req_mega"]) if item["req_mega"] in OPCOES_STATUS else 0)
                        
                        st.markdown("<br><strong style='color:#00205B;'>Contratação & Minuta</strong>", unsafe_allow_html=True)
                        edit_contr = st.selectbox("Contrato Mega", OPCOES_STATUS, index=OPCOES_STATUS.index(item["contr_mega"]) if item["contr_mega"] in OPCOES_STATUS else 0)
                        edit_param = st.selectbox("Parametrização Fiscal", OPCOES_STATUS, index=OPCOES_STATUS.index(item["param_fiscal"]) if item["param_fiscal"] in OPCOES_STATUS else 0)
                        edit_minuta = st.selectbox("Minuta Contratual", OPCOES_STATUS, index=OPCOES_STATUS.index(item["minuta"]) if item["minuta"] in OPCOES_STATUS else 0)
                        edit_ass = st.selectbox("Assinatura Eletrônica", OPCOES_STATUS, index=OPCOES_STATUS.index(item["ass_digital"]) if item["ass_digital"] in OPCOES_STATUS else 0)
                    
                    st.markdown("<hr style='border-color:#F4F6F9;'>", unsafe_allow_html=True)
                    col_e3, col_e4 = st.columns(2)
                    with col_e3:
                        edit_cred = st.selectbox("Credenciamento - GT", OPCOES_STATUS, index=OPCOES_STATUS.index(item["credenciamento"]) if item["credenciamento"] in OPCOES_STATUS else 0)
                    with col_e4:
                        edit_comunicar = st.selectbox("Informar Engenheiro", OPCOES_STATUS, index=OPCOES_STATUS.index(item["comunicar"]) if item["comunicar"] in OPCOES_STATUS else 0)
                    
                    edit_aud = st.selectbox("Audit. Pasta Final", OPCOES_STATUS, index=OPCOES_STATUS.index(item["aud_pasta"]) if item["aud_pasta"] in OPCOES_STATUS else 0)
                    
                    st.write("")
                    submit_edit = st.form_submit_button("💾 Salvar Alterações")
                    
                    if submit_edit:
                        updated_fields = {
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
                            "savings": f"{edit_savings:.2f}",
                            "aud_pasta": str(edit_aud),
                            "valor_fechado": f"{edit_valor:.2f}"
                        }
                        
                        if st.session_state.db_mode == "SharePoint (Live)" and sp_client:
                            try:
                                sp_id = int(selected_id)
                                sp_client.update_list_item(sp_id, updated_fields)
                                st.success("✔️ Registro updated com sucesso DIRETAMENTE no SharePoint!")
                            except Exception as e:
                                st.error(f"❌ Erro ao atualizar no SharePoint: {str(e)}")
                        else:
                            updated_fields["ID_PGI"] = selected_id
                            sim_idx = next(i for i, sim_item in enumerate(st.session_state.db_data) if sim_item["ID_PGI"] == selected_id)
                            st.session_state.db_data[sim_idx] = updated_fields
                            st.success("✔️ Registro atualizado com sucesso na Base Simulada!")
                            
                        st.rerun()

# PAGE 4: DETALHES DE INTEGRAÇÃO DO SHAREPOINT E OAUTH2
    elif menu_option == "Integração SharePoint":
        st.markdown("<h3 class='styled-table-title'>🔑 Painel de Integração Ativa via OAuth2 (Microsoft Entra ID)</h3>", unsafe_allow_html=True)
        
        with st.form("oauth2_config_form"):
            st.markdown("<strong style='color:#00205B;'>Configurações de Identidade Microsoft Cloud</strong>", unsafe_allow_html=True)
            st.info("Insira as credenciais geradas para o seu registro de aplicativo para validar o token OAuth2.")
            
            cfg_tenant = st.text_input("Tenant ID (ID do Diretório)", value=st.session_state.sp_tenant_id, placeholder="Ex: a2a3b4c5-...")
            cfg_client = st.text_input("Client ID (ID do Aplicativo)", value=st.session_state.sp_client_id, placeholder="Ex: e6f7g8h9-...")
            cfg_secret = st.text_input("Client Secret (Segredo do Cliente)", value=st.session_state.sp_client_secret, placeholder="Digite o segredo corporativo...", type="password")
            
            test_connection = st.form_submit_button("⚡ Validar Autenticação OAuth2")
            
            if test_connection:
                if not cfg_tenant or not cfg_client or not cfg_secret:
                    st.error("❌ Todos os campos de credenciais do OAuth2 são obrigatórios.")
                else:
                    with st.spinner("Autenticando junto ao Microsoft Azure AD..."):
                        try:
                            temp_client = SharePointOAuthClient(
                                tenant_id=cfg_tenant,
                                client_id=cfg_client,
                                client_secret=cfg_secret
                            )
                            token = temp_client.acquire_token()
                            
                            st.session_state.sp_tenant_id = cfg_tenant
                            st.session_state.sp_client_id = cfg_client
                            st.session_state.sp_client_secret = cfg_secret
                            st.session_state.sp_connected = True
                            
                            render_html(f"""
                            <div class="success-card">
                                <h4>✅ Conexão OAuth2 Estabelecida com Sucesso!</h4>
                                <p><strong>Inquilino Autenticado:</strong> {cfg_tenant}</p>
                                <p>O modo de produção em tempo real (SharePoint Live) agora está <strong>LIBERADO</strong>.</p>
                            </div>
                            """)
                        except Exception as e:
                            st.session_state.sp_connected = False
                            st.error(f"❌ Falha de Autenticação: {str(e)}")
        
        st.write("")
        st.markdown("<h3 class='styled-table-title'>📐 Arquitetura de Integração e Ecossistema</h3>", unsafe_allow_html=True)
        
        render_html("""
        <div class="info-card">
            <h4>📍 URL Da Lista do Ecossistema:</h4>
            <p><code>https://grupoayoshii.sharepoint.com/sites/DPTO_SUPRIMENTOS/Lists/PGI_GestaoCotacoes</code></p>
            <p><strong>Configuração de Tipo:</strong> Todas as colunas desta lista estão mapeadas como <em>Single Line of Text (Texto de Linha Única)</em>.</p>
        </div>
        """)
        
        st.markdown("""
        O aplicativo v5 está pareado com o arquivo de suporte <code>sharepoint_auth.py</code> para fazer a comunicação direta sem dependências complexas externas. Ele utiliza o fluxo seguro de <strong>Client Credentials</strong> do OAuth2.
        
        * <strong>Tenant ID:</strong> O identificador único do inquilino do Microsoft 365 do Grupo A.Yoshii.
        * <strong>Client ID & Secret:</strong> Identidade corporativa da aplicação registrada no portal do Azure AD.
        * <strong>Escopo Configurado:</strong> <code>https://grupoayoshii.sharepoint.com/.default</code>
        * <strong>Lista Alvo:</strong> <code>/sites/DPTO_SUPRIMENTOS/Lists/PGI_GestaoCotacoes</code>
        """)

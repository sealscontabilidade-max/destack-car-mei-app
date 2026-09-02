import os
import re
import time
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

BASE_DIR = Path(__file__).resolve().parent
ARQUIVO_ENV = BASE_DIR / ".env"
load_dotenv(dotenv_path=ARQUIVO_ENV, override=True)

st.set_page_config(
    page_title="Gestão NFSe - MEI Destack Car",
    page_icon="🚘",
    layout="wide"
)

LIMITE_MEI = 81000.00
ARQUIVO_DADOS = BASE_DIR / "faturamento_destack_car.csv"

# --- CREDENCIAIS DE ACESSO DO CLIENTE ---
USUARIO_CNPJ = "".join(filter(str.isdigit, os.getenv("CNPJ_CLIENTE", "19649014000169")))
SENHA_CPF = "".join(filter(str.isdigit, os.getenv("GOV_CPF_CNPJ", "05586778947")))


# --- SISTEMA DE AUTENTICAÇÃO (LOGIN) ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False


def realizar_login(usuario_input, senha_input):
    u_limpo = "".join(filter(str.isdigit, usuario_input))
    s_limpa = "".join(filter(str.isdigit, senha_input))

    if u_limpo == USUARIO_CNPJ and s_limpa == SENHA_CPF:
        st.session_state["logado"] = True
        st.success("Acesso liberado com sucesso!")
        st.rerun()
    else:
        st.error("CNPJ ou CPF incorretos. Verifique os dados e tente novamente.")


def realizar_logout():
    st.session_state["logado"] = False
    st.rerun()


# --- SE NÃO ESTIVER LOGADO, EXIBE A TELA DE LOGIN ---
if not st.session_state["logado"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])

    with c2:
        st.title("🚘 Destack Car")
        st.subheader("Gestão de Faturamento MEI")
        st.caption("Por favor, digite seu CNPJ e CPF para acessar o painel.")
        st.divider()

        with st.form("form_login"):
            usuario = st.text_input("CNPJ (Usuário):")
            senha = st.text_input("CPF do Titular (Senha):", type="password")
            btn_entrar = st.form_submit_button("🔑 Entrar no Painel", type="primary", use_container_width=True)

            if btn_entrar:
                realizar_login(usuario, senha)

    st.stop()


# ==============================================================================
# PAINEL PRINCIPAL (SÓ CARREGA SE ESTIVER LOGADO)
# ==============================================================================

def carregar_dados():
    if not ARQUIVO_DADOS.exists():
        dados_iniciais = [
            {"Mes": "JANEIRO", "Numero_NF": 8, "Data": "2026-01-13", "Valor": 870.00, "Chave": "411990522196490140001690000000000826013008617674", "Status": "EMITIDA"},
            {"Mes": "FEVEREIRO", "Numero_NF": 9, "Data": "2026-02-11", "Valor": 970.00, "Chave": "411990522196490140001690000000000926023180817970", "Status": "CANCELADA"},
            {"Mes": "FEVEREIRO", "Numero_NF": 10, "Data": "2026-02-11", "Valor": 970.00, "Chave": "411990522196490140001690000000001026027732877326", "Status": "EMITIDA"},
            {"Mes": "MARÇO", "Numero_NF": 11, "Data": "2026-03-26", "Valor": 350.00, "Chave": "411990522196490140001690000000001126039341467011", "Status": "EMITIDA"},
            {"Mes": "ABRIL", "Numero_NF": 12, "Data": "2026-04-14", "Valor": 1400.00, "Chave": "411990522196490140001690000000001226040088423918", "Status": "CANCELADA"},
            {"Mes": "ABRIL", "Numero_NF": 13, "Data": "2026-04-15", "Valor": 7460.00, "Chave": "411990522196490140001690000000001326045476722160", "Status": "EMITIDA"},
            {"Mes": "ABRIL", "Numero_NF": 14, "Data": "2026-04-16", "Valor": 580.00, "Chave": "411990522196490140001690000000001426044529367275", "Status": "CANCELADA"},
            {"Mes": "ABRIL", "Numero_NF": 15, "Data": "2026-04-16", "Valor": 580.00, "Chave": "411990522196490140001690000000001526047722025907", "Status": "EMITIDA"},
            {"Mes": "MAIO", "Numero_NF": 16, "Data": "2026-04-15", "Valor": 8270.00, "Chave": "411990522196490140001690000000001626052466720745", "Status": "EMITIDA"},
            {"Mes": "JULHO", "Numero_NF": 17, "Data": "2026-07-31", "Valor": 5500.00, "Chave": "411990522196490140001690000000001726089442859967", "Status": "CANCELADA"},
            {"Mes": "JULHO", "Numero_NF": 18, "Data": "2026-07-31", "Valor": 5500.00, "Chave": "411990522196490140001690000000001826089563267517", "Status": "CANCELADA"},
            {"Mes": "JULHO", "Numero_NF": 19, "Data": "2026-07-31", "Valor": 1500.00, "Chave": "411990522196490140001690000000001926089278962079", "Status": "CANCELADA"},
        ]
        pd.DataFrame(dados_iniciais).to_csv(ARQUIVO_DADOS, index=False)
    return pd.read_csv(ARQUIVO_DADOS)


def salvar_dados(df):
    df.to_csv(ARQUIVO_DADOS, index=False)


def abrir_portal_emissor():
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"}
    )
    driver.get("https://www.nfse.gov.br/EmissorNacional/Login")
    st.info("Portal do Emissor Nacional aberto sem mensagem de automação!")


def extrair_dados_xml_universal(content_str, file_name):
    meses_map = {
        1: "JANEIRO", 2: "FEVEREIRO", 3: "MARÇO", 4: "ABRIL",
        5: "MAIO", 6: "JUNHO", 7: "JULHO", 8: "AGOSTO",
        9: "SETEMBRO", 10: "OUTUBRO", 11: "NOVEMBRO", 12: "DEZEMBRO"
    }

    num_match = re.search(r'<(?:[a-zA-Z0-9_]+:)?(?:nNF|nDPS|nDF|nNFSe)>(\d+)</', content_str, re.IGNORECASE)
    if num_match:
        num_nf = int(num_match.group(1))
    else:
        file_num = re.search(r'NF\s*(\d+)', file_name, re.IGNORECASE)
        num_nf = int(file_num.group(1)) if file_num else None

    val_match = re.search(r'<(?:[a-zA-Z0-9_]+:)?(?:vServ|vBC|vNF|vServicos|vLiq)>([\d.]+)</', content_str, re.IGNORECASE)
    valor_nf = float(val_match.group(1)) if val_match else 0.0

    data_match = re.search(r'<(?:[a-zA-Z0-9_]+:)?(?:dhEmi|dEmi|dhAviso|dhProc)>(\d{4}-\d{2}-\d{2})', content_str, re.IGNORECASE)
    data_nf = data_match.group(1) if data_match else "2026-08-30"

    chave_match = re.search(r'<(?:[a-zA-Z0-9_]+:)?chNFSe>(\d+)</', content_str, re.IGNORECASE) or \
                  re.search(r'Id="(?:NFS|NFSE)?(\d+)"', content_str, re.IGNORECASE)
    chave_nf = chave_match.group(1) if chave_match else "41199052219649014000169000000000" + str(num_nf or "00").zfill(16)

    if num_nf is not None and valor_nf > 0:
        mes_num = int(data_nf.split("-")[1])
        mes_nome = meses_map.get(mes_num, "AGOSTO")
        return {
            "Mes": mes_nome,
            "Numero_NF": num_nf,
            "Data": data_nf,
            "Valor": valor_nf,
            "Chave": chave_nf,
            "Status": "EMITIDA"
        }
    return None


# --- CABEÇALHO DO PAINEL LOGADO ---
col_head, col_out = st.columns([5, 1])

with col_head:
    st.title("🚘 Painel de Controle de Faturamento MEI - Destack Car")
    st.caption("Empresa: 19.649.014 RAMISSES GONCALVES DA SILVA | CNPJ: 19.649.014/0001-69")

with col_out:
    st.write("")
    if st.button("🚪 Sair / Logout", use_container_width=True):
        realizar_logout()

df_notas = carregar_dados()

col1_act, col2_act = st.columns([2, 5])
with col1_act:
    if st.button("🌐 Abrir Portal Emissor Nacional", type="primary"):
        abrir_portal_emissor()

st.divider()

# --- MÓDULO DE IMPORTAÇÃO DE XML ---
st.subheader("📥 Processar Novas Notas Fiscais (Importação de XML)")
uploaded_files = st.file_uploader(
    "Arraste ou selecione os arquivos XML das Notas Fiscais emitidas para atualizar o painel:",
    type=["xml"],
    accept_multiple_files=True
)

if uploaded_files:
    novas_notas = []
    for file in uploaded_files:
        try:
            content = file.read().decode("utf-8", errors="ignore")
            dados_extraidos = extrair_dados_xml_universal(content, file.name)
            if dados_extraidos:
                novas_notas.append(dados_extraidos)
        except Exception as e:
            st.error(f"Erro ao ler arquivo {file.name}: {e}")

    if novas_notas:
        df_novas = pd.DataFrame(novas_notas)
        df_notas = pd.concat([df_notas, df_novas]).drop_duplicates(subset=["Numero_NF"], keep="last")
        salvar_dados(df_notas)
        st.success(f"✅ Sucesso! {len(novas_notas)} nota(s) fiscal(is) processada(s) e adicionada(s) ao faturamento!")

st.divider()

# --- MÉTRICAS DE FATURAMENTO ---
df_validas = df_notas[df_notas["Status"] == "EMITIDA"]
faturado = df_validas["Valor"].sum()
saldo_restante = LIMITE_MEI - faturado
percentual_usado = (faturado / LIMITE_MEI) * 100

col1, col2, col3 = st.columns(3)
col1.metric("Limite MEI Anual", f"R$ {LIMITE_MEI:,.2f}")
col2.metric("Faturamento Acumulado", f"R$ {faturado:,.2f}", delta=f"{percentual_usado:.1f}% do limite")
col3.metric("Saldo Disponível MEI", f"R$ {saldo_restante:,.2f}")

st.progress(min(percentual_usado / 100, 1.0))

if percentual_usado >= 80:
    st.warning("⚠️ Atenção: O faturamento acumulado ultrapassou 80% do limite do MEI!")

st.divider()

# --- RESUMO E GRÁFICO DINÂMICO MÊS A MÊS ---
st.subheader("📊 Faturamento e Notas Emitidas Mês a Mês")

df_mensal = df_validas.groupby("Mes").agg(
    Qtd_Notas_Emitidas=("Numero_NF", "count"),
    Faturamento_Total=("Valor", "sum")
).reset_index()

ordem_meses = [
    "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO",
    "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"
]

df_mensal["Mes"] = pd.Categorical(df_mensal["Mes"], categories=ordem_meses, ordered=True)
df_mensal = df_mensal.sort_values("Mes").dropna(subset=["Mes"])

df_mensal_exibicao = df_mensal.copy()
df_mensal_exibicao["Faturamento_Total"] = df_mensal_exibicao["Faturamento_Total"].apply(lambda x: f"R$ {x:,.2f}")

col_tbl, col_chart = st.columns([2, 3])

with col_tbl:
    st.markdown("**Resumo Mensal de Faturamento (Notas Válidas):**")
    st.dataframe(df_mensal_exibicao, width="stretch")

with col_chart:
    st.markdown("**Gráfico Interativo de Faturamento (R$):**")
    fig = px.bar(
        df_mensal,
        x="Mes",
        y="Faturamento_Total",
        text_auto=".2f",
        labels={"Mes": "Mês", "Faturamento_Total": "Faturamento (R$)"},
        color="Faturamento_Total",
        color_continuous_scale="Blues"
    )
    
    fig.update_layout(
        xaxis={'categoryorder': 'array', 'categoryarray': ordem_meses},
        xaxis_title="Mês do Ano",
        yaxis_title="Faturamento (R$)",
        showlegend=False,
        coloraxis_showscale=False,
        height=380,
        margin=dict(l=20, r=20, t=30, b=20)
    )
    
    fig.update_traces(
        texttemplate='R$ %{y:,.2f}',
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Faturamento: R$ %{y:,.2f}<extra></extra>'
    )
    
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- HISTÓRICO COMPLETO ---
st.subheader("📋 Histórico Completo de Notas Fiscais Registradas")
# Converte uma cópia do DataFrame para texto para evitar erro de estouro (OverflowError)
st.dataframe(df_notas.astype(str), use_container_width=True)
import streamlit as st
import pandas as pd
import plotly.express as px
import json
import datetime
from io import BytesIO
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

# --- HATA ÖNLEYİCİ ---
try:
    from fpdf import FPDF
    import xlsxwriter
    LIB_OK = True
except: LIB_OK = False

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="KoruPark Yönetim", 
    layout="wide", 
    page_icon="🏢",
    initial_sidebar_state="expanded" 
)

# --- CSS: v70.5 ULTRA-VISUAL FIX ---
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">

<style>
    /* 1. GİZLENECEKLER VE SIFIRLAMA */
    .stDeployButton, [data-testid="stHeaderActionElements"], [data-testid="stToolbar"],
    [data-testid="stManageAppButton"], footer, #MainMenu { display: none !important; }
    header[data-testid="stHeader"] { background: transparent !important; height: 0px !important; }

    /* 2. ARKA PLAN: DERİN GRADIENT (Apple Style) */
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at top left, #F8F9FC 0%, #E2E8F0 100%) !important;
        background-attachment: fixed !important;
    }
    .block-container { padding-top: 40px !important; }

    /* 3. YÜZEN SOL MENÜ (Sert Çizgiyi Kaldırır) */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: none !important;
        box-shadow: 10px 0 40px rgba(0,0,0,0.03) !important;
    }
    [data-testid="stSidebarCollapseButton"] { display: none !important; }

    /* 4. MODERN ÖZEL KAYDIRMA ÇUBUĞU */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #0066FF; }

    /* 5. GLASSMORPHISM KARTLAR (Canlı ve Derin) */
    .metric-card {
        background: rgba(255, 255, 255, 0.8) !important;
        backdrop-filter: blur(15px) !important;
        padding: 30px;
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
        box-shadow: 0 15px 35px rgba(0,0,0,0.02) !important;
        transition: all 0.4s ease-in-out !important;
    }
    .metric-card:hover {
        transform: translateY(-10px) !important;
        box-shadow: 0 25px 50px rgba(0,0,0,0.06) !important;
        border-color: #0066FF !important;
        background: rgba(255, 255, 255, 1) !important;
    }
    .metric-card h3 { color: #94a3b8; font-size: 13px; text-transform: uppercase; font-weight: 700; letter-spacing: 1.2px; margin-bottom: 12px; }
    .metric-card h1 { color: #1e293b; font-size: 34px; font-weight: 800; margin: 0; letter-spacing: -1px; }

    /* 6. GİRİŞ KARTI TASARIMI */
    div[data-testid="column"]:nth-of-type(2) > div > div {
        background: #FFFFFF !important;
        padding: 55px;
        border-radius: 32px;
        box-shadow: 0 40px 100px rgba(0,0,0,0.08) !important;
        border: 1px solid #f1f5f9;
    }

    /* 7. BUTONLAR VE INPUTLAR */
    button[kind="primary"], [data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #0066FF 0%, #0047AB 100%) !important;
        border-radius: 14px !important;
        font-weight: 700 !important;
        box-shadow: 0 10px 20px -10px rgba(0, 102, 255, 0.5) !important;
    }
    .stTextInput input {
        border: 1px solid #cbd5e1 !important;
        border-radius: 14px !important;
        background-color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

# --- VERİTABANI VE İŞLEMLER ---
def baglanti_kur():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

def verileri_yukle():
    try:
        client = baglanti_kur()
        sheet = client.open("ZorluDB").sheet1
        raw = sheet.cell(1, 1).value
        return json.loads(raw) if raw else demo_veri()
    except: return demo_veri()

def kaydet(veri):
    try:
        client = baglanti_kur()
        sheet = client.open("ZorluDB").sheet1
        sheet.update_cell(1, 1, json.dumps(veri, ensure_ascii=False))
    except: st.error("Kayıt Hatası!")

def kullanici_dogrula(kadi, sifre):
    try:
        client = baglanti_kur()
        sheet = client.open("ZorluDB").worksheet("Kullanicilar")
        for u in sheet.get_all_records():
            if str(u['kullanici_adi']) == str(kadi) and str(u['sifre']) == str(sifre): return u
        return None
    except: return None

def demo_veri():
    return {"site_adi": "KoruPark", "kasa_nakit": 85100.0, "daireler": {"1": {"sahip": "Ahmet Yılmaz", "borc": 0.0, "icra": False}, "2": {"sahip": "Yeter Zorlu", "borc": 5300.0, "icra": True}}, "giderler": []}

if "data" not in st.session_state: st.session_state["data"] = verileri_yukle()
data = st.session_state["data"]

# --- OTURUM VE GİRİŞ ---
if "giris" not in st.session_state: st.session_state["giris"] = False
if "active_menu" not in st.session_state: st.session_state["active_menu"] = "Genel Bakış"

if not st.session_state["giris"]:
    c1, c2, c3 = st.columns([1, 1.4, 1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        u = st.text_input("Kullanıcı Kodu", key="l_u"); p = st.text_input("Şifre", type="password", key="l_p")
        if st.button("GİRİŞ YAP", type="primary", use_container_width=True):
            user = kullanici_dogrula(u, p)
            if user: st.session_state.update({"giris": True, "rol": user["rol"], "user": user["daire_no"]}); st.rerun()
            else: st.error("Hatalı giriş!")
    st.stop()

# --- ANA EKRAN ---
st.markdown("<style>div[data-testid='column']:nth-of-type(2) > div > div { background: transparent !important; box-shadow: none !important; border: none !important; }</style>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("<div style='text-align: center; padding: 20px;'><h2 style='color:#1E293B; font-weight:900;'>KORUPARK</h2></div>", unsafe_allow_html=True)
    if st.button("🏠 Genel Bakış"): st.session_state["active_menu"] = "Genel Bakış"; st.rerun()
    if st.button("💸 Giderler"): st.session_state["active_menu"] = "Giderler"; st.rerun()
    if st.button("👥 Hesaplar"): st.session_state["active_menu"] = "Hesaplar"; st.rerun()
    if st.button("⚖️ Hukuk/İcra"): st.session_state["active_menu"] = "Hukuk"; st.rerun()
    if st.button("🚪 Çıkış"): st.session_state["giris"] = False; st.rerun()

menu = st.session_state["active_menu"]
st.markdown(f"<h1 style='font-weight: 800; color: #1E293B;'>{menu}</h1>", unsafe_allow_html=True)

if menu == "Genel Bakış":
    toplam_alacak = sum(d['borc'] for d in data['daireler'].values())
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='metric-card'><h3>KASA</h3><h1 style='color:#0066FF'>{data['kasa_nakit']:,.0f} ₺</h1></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'><h3>ALACAK</h3><h1 style='color:#FF3B30'>{toplam_alacak:,.0f} ₺</h1></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'><h3>GİDER</h3><h1>0 ₺</h1></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='metric-card'><h3>DAİRE</h3><h1>{len(data['daireler'])}</h1></div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    cl, cr = st.columns([2, 1])
    with cl:
        fig = px.pie(values=[data['kasa_nakit'], toplam_alacak], names=['Kasa', 'Alacak'], hole=0.75, color_discrete_sequence=["#0066FF", "#FF3B30"])
        # --- ŞEFFAF GRAFİK AYARI (KESİN) ---
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)', 
            font=dict(family="Poppins", size=14),
            margin=dict(t=0, b=0, l=0, r=0),
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)
    with cr:
        st.subheader("Veri Güvenliği")
        if st.button("💾 VERİLERİ ŞİMDİ YEDEKLE", type="primary", use_container_width=True): kaydet(data); st.success("Yedeklendi")

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

# --- CSS: v77.0 ULTIMATE ARCHITECTURE (AGRESSIVE GLASSMOPHISM) ---
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">

<style>
    /* 1. TÜM ANA KATMANLARI ZORLA ŞEFFAFLAŞTIR (RESİMDEKİ GRİ KATMANI SİLER) */
    .stApp, [data-testid="stAppViewMain"], .main, [data-testid="stHeader"], 
    [data-testid="stVerticalBlock"], [data-testid="stHorizontalBlock"], 
    .element-container, .stMarkdown, [data-testid="stExpander"], .stBlock {
        background-color: transparent !important;
        background: transparent !important;
        border: none !important;
    }

    /* 2. ANA ARKA PLAN: DERİN RADIAL GRADIENT */
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at top right, #F8F9FC 0%, #DDE4EE 100%) !important;
        background-attachment: fixed !important;
    }

    /* 3. GERÇEK CAM EFEKTİ (GLASSMORPHISM) KARTLAR */
    .metric-card {
        background: rgba(255, 255, 255, 0.45) !important; /* Yarı şeffaf beyaz */
        backdrop-filter: blur(20px) saturate(180%) !important; /* Derin buzlu cam dokusu */
        -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
        border: 1px solid rgba(255, 255, 255, 0.5) !important; /* Kristal kenarlık */
        border-radius: 32px !important;
        padding: 35px !important;
        box-shadow: 0 12px 35px rgba(31, 38, 135, 0.05) !important;
        transition: all 0.5s cubic-bezier(0.2, 0.8, 0.2, 1) !important;
        height: 100% !important;
    }
    
    .metric-card:hover {
        transform: translateY(-10px) !important;
        background: rgba(255, 255, 255, 0.8) !important;
        box-shadow: 0 25px 60px rgba(0, 102, 255, 0.12) !important;
        border-color: #0066FF !important;
    }

    .metric-card h3 { color: #64748b; font-size: 14px; text-transform: uppercase; font-weight: 700; letter-spacing: 1.5px; margin-bottom: 12px; }
    .metric-card h1 { color: #1e293b; font-size: 44px; font-weight: 800; margin: 0; letter-spacing: -2px; }

    /* 4. GRAFİK KONTEYNERINI ZORLA ŞEFFAF YAP (RESİMDEKİ GRİ KUTUYU SİLER) */
    [data-testid="stPlotlyChart"], .plotly, .user-select-none {
        background-color: transparent !important;
        background: transparent !important;
    }

    /* 5. SOL MENÜ: YÜZEN ETKİ & SERT ÇİZGİSİZ */
    section[data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.95) !important;
        border-right: none !important;
        box-shadow: 20px 0 60px rgba(0,0,0,0.03) !important;
    }
    [data-testid="stSidebarCollapseButton"] { display: none !important; }

    /* 6. BUTONLAR VE MODERN INPUTLAR */
    button[kind="primary"] {
        background: linear-gradient(135deg, #0066FF 0%, #0047AB 100%) !important;
        border-radius: 18px !important;
        font-weight: 700 !important;
        box-shadow: 0 10px 25px -5px rgba(0, 102, 255, 0.4) !important;
    }
    
    .stTextInput input {
        border: 1.5px solid #E2E8F0 !important;
        border-radius: 16px !important;
        background-color: rgba(255, 255, 255, 0.9) !important;
    }

    /* 7. ÖZEL SCROLLBAR */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
    
    /* 8. GİZLENECEKLER */
    .stDeployButton, [data-testid="stHeaderActionElements"], [data-testid="stToolbar"],
    [data-testid="stManageAppButton"], footer, #MainMenu { display: none !important; }
</style>
""", unsafe_allow_html=True)

# --- VERİTABANI BAĞLANTISI ---
SHEET_DB = "ZorluDB"
SHEET_USERS = "Kullanicilar"

def baglanti_kur():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

def verileri_yukle():
    try:
        client = baglanti_kur()
        sheet = client.open(SHEET_DB).sheet1
        raw_data = sheet.cell(1, 1).value
        return json.loads(raw_data) if raw_data else demo_veri()
    except: return demo_veri()

def kaydet(veri):
    try:
        client = baglanti_kur()
        sheet = client.open(SHEET_DB).sheet1
        sheet.update_cell(1, 1, json.dumps(veri, ensure_ascii=False))
    except: st.error("Kayıt Hatası!")

def kullanici_dogrula(kadi, sifre):
    try:
        client = baglanti_kur()
        sheet = client.open(SHEET_DB).worksheet(SHEET_USERS)
        records = sheet.get_all_records()
        for user in records:
            if str(user['kullanici_adi']) == str(kadi) and str(user['sifre']) == str(sifre): return user
        return None
    except: return None

def demo_veri():
    return {
        "site_adi": "KoruPark", "kasa_nakit": 85100.0, "kasa_banka": 250000.0,
        "giderler": [], "daireler": {
            "1": {"sahip": "Ahmet Yılmaz", "blok": "A", "borc": 0.0, "gecmis": [], "plaka": "-", "icra": False},
            "2": {"sahip": "Yeter Zorlu", "blok": "A", "borc": 5300.0, "gecmis": ["Aidat x3"], "plaka": "-", "icra": True}
        }
    }

if "data" not in st.session_state: st.session_state["data"] = verileri_yukle()
data = st.session_state["data"]

# --- OTURUM AYARLARI ---
if "giris" not in st.session_state: st.session_state["giris"] = False
if "active_menu" not in st.session_state: st.session_state["active_menu"] = "Genel Bakış"

# --- GİRİŞ EKRANI ---
if not st.session_state["giris"]:
    c1, c2, c3 = st.columns([1, 1.4, 1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align:center; font-weight:800; color:#1E293B;'>GİRİŞ YAP</h2>", unsafe_allow_html=True)
        u = st.text_input("Kullanıcı Kodu", key="l_u"); p = st.text_input("Şifre", type="password", key="l_p")
        if st.button("GİRİŞ YAP", type="primary", use_container_width=True):
            user = kullanici_dogrula(u, p)
            if user: st.session_state.update({"giris": True, "rol": user["rol"], "user": user["daire_no"]}); st.rerun()
            else: st.error("Hatalı giriş!")
    st.stop()

# --- ANA UYGULAMA ---
st.markdown("<style>div[data-testid='column']:nth-of-type(2) > div > div { background: transparent !important; box-shadow: none !important; border: none !important; }</style>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("<div style='text-align: center; padding: 20px;'><h2 style='color:#1E293B; font-weight:900;'>KORUPARK</h2></div>", unsafe_allow_html=True)
    if st.button("🏠 Genel Bakış"): st.session_state["active_menu"] = "Genel Bakış"; st.rerun()
    if st.button("💸 Gider Yönetimi"): st.session_state["active_menu"] = "Giderler"; st.rerun()
    if st.button("👥 Hesaplar & Aidat"): st.session_state["active_menu"] = "Hesaplar"; st.rerun()
    if st.button("🏘️ Blok Haritası"): st.session_state["active_menu"] = "Harita"; st.rerun()
    if st.button("⚖️ Hukuk & İcra"): st.session_state["active_menu"] = "Hukuk"; st.rerun()
    if st.button("🚪 Güvenli Çıkış"): st.session_state["giris"] = False; st.rerun()

menu = st.session_state["active_menu"]
st.markdown(f"<h1 style='font-weight: 800; color: #1E293B; margin-bottom: 25px;'>{menu}</h1>", unsafe_allow_html=True)

if menu == "Genel Bakış":
    toplam_alacak = sum(d['borc'] for d in data['daireler'].values())
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='metric-card'><h3>GÜNCEL KASA</h3><h1 style='color:#0066FF'>{data['kasa_nakit']:,.0f} ₺</h1></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='metric-card'><h3>TOPLAM ALACAK</h3><h1 style='color:#FF3B30'>{toplam_alacak:,.0f} ₺</h1></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='metric-card'><h3>TOPLAM GİDER</h3><h1>0 ₺</h1></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='metric-card'><h3>DAİRE SAYISI</h3><h1>{len(data['daireler'])}</h1></div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    cl, cr = st.columns([2, 1])
    with cl:
        fig = px.pie(values=[data['kasa_nakit'], toplam_alacak], names=['Kasa', 'Alacak'], hole=0.75, color_discrete_sequence=["#0066FF", "#FF3B30"])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family="Poppins", size=14), margin=dict(t=0,b=0,l=0,r=0))
        st.plotly_chart(fig, use_container_width=True)
    with cr:
        st.subheader("Veri Güvenliği")
        if st.button("💾 EXCEL'E YEDEKLE", type="primary", use_container_width=True): kaydet(data); st.success("Yedeklendi")

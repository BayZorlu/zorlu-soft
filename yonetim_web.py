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

# --- LOGO AYARLARI ---
LOGO_DOSYA = "logo.png" 

# --- CSS: TRUE BLUE TASARIM (v70 STANDARTLARI) ---
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap" rel="stylesheet">

<style>
    /* 0. ANA RENK AYARI */
    :root {
        --primary-color: #0066FF;
    }

    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }

    /* 1. GİZLENECEKLER */
    .stDeployButton, 
    [data-testid="stHeaderActionElements"], 
    [data-testid="stToolbar"],
    [data-testid="stManageAppButton"],
    footer, 
    #MainMenu {
        display: none !important;
    }
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 0px !important;
        visibility: hidden !important;
    }

    /* 2. INPUT KUTULARI (v70 TEMİZ TASARIM) */
    .stTextInput > div > div {
        border: none !important;
        box-shadow: none !important;
        background-color: transparent !important;
    }
    
    .stTextInput input {
        border: 1px solid #cbd5e1 !important;
        border-radius: 12px !important;
        padding: 12px 15px !important;
        background-color: #FFFFFF !important;
        color: #1E293B !important;
        transition: all 0.2s;
    }
    
    .stTextInput input:focus {
        border-color: #0066FF !important;
        box-shadow: 0 0 0 2px rgba(0, 102, 255, 0.2) !important;
        outline: none !important;
    }

    /* 3. BUTONLAR (MAVİ) */
    button[kind="primary"], [data-testid="baseButton-primary"] {
        background-color: #0066FF !important;
        border-color: #0066FF !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-weight: 700 !important;
        box-shadow: 0 10px 20px -10px rgba(0, 102, 255, 0.4) !important;
        transition: 0.3s;
        width: 100%;
    }
    
    button[kind="primary"]:hover {
        background-color: #0052CC !important;
        transform: translateY(-2px);
    }

    button[kind="secondary"], [data-testid="baseButton-secondary"] {
        background-color: transparent !important;
        border: none !important;
        color: #64748b !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        box-shadow: none !important;
        margin-top: -10px !important;
    }
    
    button[kind="secondary"]:hover {
        color: #0066FF !important;
        text-decoration: underline;
    }

    /* 4. GİRİŞ KARTI */
    div[data-testid="column"]:nth-of-type(2) > div > div {
        background: #FFFFFF;
        padding: 50px;
        border-radius: 28px;
        box-shadow: 0 20px 50px rgba(0,0,0,0.08);
        border: 1px solid #f1f5f9;
    }

    /* 5. ARKA PLAN VE SOL MENÜ */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(to bottom, #F0F4F8 0%, #D9E2EC 100%) !important;
    }
    
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        box-shadow: 4px 0 15px -5px rgba(0,0,0,0.05);
        border-right: none !important;
    }
    [data-testid="stSidebarCollapseButton"] { display: none !important; }

    /* 6. KARTLAR (İÇERİK) */
    .metric-card {
        background: #FFFFFF;
        padding: 24px;
        border-radius: 20px;
        border: 1px solid #F1F5F9;
        box-shadow: 0 10px 20px -10px rgba(0,0,0,0.05);
    }
    .metric-card h3 { color: #94a3b8; font-size: 13px; text-transform: uppercase; font-weight: 700; }
    .metric-card h1 { color: #1e293b; font-size: 34px; font-weight: 800; margin: 0; }

    .sidebar-divider {
        margin: 20px 0;
        border-bottom: 1px solid #EFF2F7;
    }

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

# --- KULLANICI İŞLEMLERİ (SADECE EXCEL) ---
def kullanici_dogrula(kadi, sifre):
    try:
        client = baglanti_kur()
        sheet = client.open(SHEET_DB).worksheet(SHEET_USERS)
        records = sheet.get_all_records()
        for user in records:
            if str(user['kullanici_adi']) == str(kadi) and str(user['sifre']) == str(sifre):
                return user 
        return None
    except: return None

def sifre_sifirla_excel(kadi, guvenlik_kodu, yeni_sifre):
    try:
        client = baglanti_kur()
        sheet = client.open(SHEET_DB).worksheet(SHEET_USERS)
        records = sheet.get_all_records()
        for i, user in enumerate(records):
            if str(user['kullanici_adi']) == str(kadi):
                if str(user['guvenlik_kodu']) == str(guvenlik_kodu):
                    sheet.update_cell(i + 2, 2, yeni_sifre) # 2. sütun sifre varsayıldı
                    return True, "Şifreniz Excel'de güncellendi."
        return False, "Bilgiler hatalı!"
    except Exception as e: return False, f"Hata: {e}"

# --- OTURUM AYARLARI ---
if "giris" not in st.session_state: st.session_state["giris"] = False
if "ui_mode" not in st.session_state: st.session_state["ui_mode"] = "login"
if "active_menu" not in st.session_state: st.session_state["active_menu"] = "Genel Bakış"

# --- GİRİŞ EKRANI ---
if not st.session_state["giris"]:
    c1, c2, c3 = st.columns([1, 1.4, 1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        
        if st.session_state["ui_mode"] == "login":
            u = st.text_input("Kullanıcı Kodu", placeholder="Kullanıcı adınız", key="l_u")
            p = st.text_input("Şifre", type="password", placeholder="Şifreniz", key="l_p")
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("GİRİŞ YAP", type="primary", use_container_width=True):
                user_data = kullanici_dogrula(u, p)
                if user_data:
                    st.session_state["giris"] = True
                    st.session_state["rol"] = str(user_data["rol"])
                    st.session_state["user"] = str(user_data["daire_no"])
                    st.rerun()
                else: st.error("Giriş başarısız.")
                
            if st.button("🔒 Şifremi Unuttum", type="secondary", use_container_width=True):
                st.session_state["ui_mode"] = "forgot"
                st.rerun()

        elif st.session_state["ui_mode"] == "forgot":
            st.markdown("<h4 style='text-align:center;'>Şifre Sıfırlama</h4>", unsafe_allow_html=True)
            f_u = st.text_input("Kullanıcı Adı", key="f_u")
            f_k = st.text_input("Güvenlik Kodu", type="password", key="f_k")
            f_p = st.text_input("Yeni Şifre", type="password", key="f_p")
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("ŞİFREYİ GÜNCELLE", type="primary", use_container_width=True):
                basari, mesaj = sifre_sifirla_excel(f_u, f_k, f_p)
                if basari:
                    st.success(mesaj); st.session_state["ui_mode"] = "login"; st.rerun()
                else: st.error(mesaj)
                
            if st.button("⬅️ Geri Dön", type="secondary", use_container_width=True):
                st.session_state["ui_mode"] = "login"; st.rerun()

        st.markdown("<p style='text-align:center; color:#94a3b8; margin-top:30px; font-size:12px;'>Zorlu Soft | © 2026 | v73.0</p>", unsafe_allow_html=True)
    st.stop()

# ==============================================================================
# ANA YAPI
# ==============================================================================
st.markdown("<style>div[data-testid='column']:nth-of-type(2) > div > div { background: transparent !important; padding: 0 !important; border: none !important; box-shadow: none !important; }</style>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("<div style='padding: 25px 10px; text-align: center;'><h3 style='color:#1E293B; margin:0; font-weight:900;'>KORUPARK</h3><p style='color:#0066FF; font-size:13px; font-weight:600;'>Sistem Yöneticisi</p></div>", unsafe_allow_html=True)
    
    if st.session_state["rol"] == "admin":
        if st.button("🏠 Genel Bakış"): st.session_state["active_menu"] = "Genel Bakış"; st.rerun()
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        if st.button("💸 Gider Yönetimi"): st.session_state["active_menu"] = "Giderler"; st.rerun()
        if st.button("👥 Hesaplar"): st.session_state["active_menu"] = "Hesaplar"; st.rerun()
        if st.button("🚪 Çıkış"): st.session_state["giris"] = False; st.rerun()

st.title(st.session_state["active_menu"])
st.info("Veriler Excel üzerinden canlı olarak işlenmektedir.")

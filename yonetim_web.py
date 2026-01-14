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
except: 
    LIB_OK = False

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="KoruPark Yönetim", 
    layout="wide", 
    page_icon="🏢",
    initial_sidebar_state="expanded" 
)

# --- CSS: TRUE BLUE TASARIM (GÜNCELLENMİŞ) ---
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap" rel="stylesheet">

<style>
    /* GENEL TİPOGRAFİ */
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

    /* 2. INPUT KUTULARI (SADE VE NET) */
    div[data-testid="stTextInput"] div[data-baseweb="input"] {
        border-radius: 12px !important;
        background-color: #FFFFFF !important;
        border: 1px solid #cbd5e1 !important;
        transition: all 0.2s;
    }
    
    div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within {
        border-color: #0066FF !important;
        box-shadow: 0 0 0 2px rgba(0, 102, 255, 0.1) !important;
    }

    /* 3. BUTONLAR */
    /* Primary Buton (Mavi) */
    button[kind="primary"] {
        background-color: #0066FF !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        border: none !important;
        font-weight: 600 !important;
        width: 100%;
        transition: 0.3s;
    }
    button[kind="primary"]:hover {
        background-color: #0052CC !important;
        transform: translateY(-1px);
    }

    /* Secondary Buton (Şifremi Unuttum) */
    button[kind="secondary"] {
        background-color: transparent !important;
        border: none !important;
        color: #64748b !important;
        text-decoration: none !important;
        font-size: 13px !important;
    }
    button[kind="secondary"]:hover {
        color: #0066FF !important;
        background-color: transparent !important;
    }

    /* 4. GİRİŞ EKRANI ÖZEL STİLİ (Sadece Giriş Yapılmadığında) */
    .login-container {
        background: #FFFFFF;
        padding: 50px;
        border-radius: 24px;
        box-shadow: 0 20px 50px rgba(0,0,0,0.08);
        border: 1px solid #f1f5f9;
        margin-top: 50px;
    }

    /* 5. ARKA PLAN */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(to bottom, #F0F4F8 0%, #D9E2EC 100%) !important;
    }

    /* 6. SOL MENÜ */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #f1f5f9 !important;
    }
    [data-testid="stSidebar"] .stButton button {
        text-align: left !important;
        border-radius: 10px !important;
        border: none !important;
        padding: 10px 15px !important;
    }
    
    /* 7. METRİK KARTLARI */
    .metric-card {
        background: #FFFFFF;
        padding: 24px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
</style>
""", unsafe_allow_html=True)

# --- VERİTABANI VE FONKSİYONLAR (Aynı Kaldı) ---
def baglanti_kur():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client
    except: return None

def verileri_yukle():
    try:
        client = baglanti_kur()
        sheet = client.open("ZorluDB").sheet1
        raw_data = sheet.cell(1, 1).value
        return json.loads(raw_data) if raw_data else demo_veri()
    except: return demo_veri()

def kaydet(veri):
    try:
        client = baglanti_kur()
        sheet = client.open("ZorluDB").sheet1
        sheet.update_cell(1, 1, json.dumps(veri, ensure_ascii=False))
    except: st.error("Kayıt sırasında bağlantı hatası oluştu.")

def kullanici_dogrula(kadi, sifre):
    try:
        client = baglanti_kur()
        sheet = client.open("ZorluDB").worksheet("Kullanicilar")
        records = sheet.get_all_records()
        for user in records:
            if str(user['kullanici_adi']) == str(kadi) and str(user['sifre']) == str(sifre):
                return user 
        return None
    except: return None

def demo_veri():
    return {"site_adi": "KoruPark", "kasa_nakit": 85000.0, "kasa_banka": 250000.0, "giderler": [], "daireler": {"1": {"sahip": "Ahmet Yılmaz", "blok": "A", "borc": 0.0, "gecmis": [], "icra": False}}}

# --- SESSION STATE ---
if "data" not in st.session_state: st.session_state["data"] = verileri_yukle()
if "giris" not in st.session_state: st.session_state["giris"] = False
if "active_menu" not in st.session_state: st.session_state["active_menu"] = "Genel Bakış"

data = st.session_state["data"]

# --- GİRİŞ EKRANI (DÜZELTİLMİŞ) ---
if not st.session_state["giris"]:
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        # Custom div ile kart görünümü oluşturuldu
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown("<h2 style='text-align:center; color:#1E293B;'>Yönetim Paneli</h2>", unsafe_allow_html=True)
        
        u = st.text_input("Kullanıcı Kodu", placeholder="Kodu giriniz")
        p = st.text_input("Şifre", type="password", placeholder="Şifrenizi giriniz")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("GİRİŞ YAP", type="primary"):
            user_data = kullanici_dogrula(u, p)
            if user_data:
                st.session_state["giris"] = True
                st.session_state["rol"] = str(user_data["rol"])
                st.session_state["user"] = str(user_data["daire_no"])
                st.rerun()
            else:
                st.error("Giriş bilgileri hatalı.")
        
        if st.button("🔒 Şifremi Unuttum", type="secondary"):
            st.toast("Lütfen site yönetimi ile iletişime geçiniz.", icon="ℹ️")
        
        st.markdown("<p style='text-align:center; color:#94a3b8; font-size:11px; margin-top:20px;'>Zorlu Soft | v70.0</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- ANA PANEL (Giriş Sonrası) ---
with st.sidebar:
    st.markdown('<div style="text-align:center; padding:20px;">'
                '<h2 style="color:#0066FF; font-weight:900; margin:0;">KORUPARK</h2>'
                '<p style="color:#64748b; font-size:12px;">Sistem Yöneticisi</p></div>', unsafe_allow_html=True)
    
    if st.button("🏠 Genel Bakış"): st.session_state["active_menu"] = "Genel Bakış"; st.rerun()
    if st.button("💸 Gider Yönetimi"): st.session_state["active_menu"] = "Giderler"; st.rerun()
    if st.button("👥 Hesaplar & Aidat"): st.session_state["active_menu"] = "Hesaplar"; st.rerun()
    if st.button("🏘️ Blok Haritası"): st.session_state["active_menu"] = "Harita"; st.rerun()
    
    st.markdown("---")
    if st.button("🚪 Güvenli Çıkış"): 
        st.session_state["giris"] = False
        st.rerun()

# --- İÇERİK ALANI ---
menu = st.session_state["active_menu"]
st.markdown(f"<h1 style='color:#1E293B;'>{menu}</h1>", unsafe_allow_html=True)

if menu == "Genel Bakış":
    toplam_alacak = sum(d['borc'] for d in data['daireler'].values())
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'><h3>KASA</h3><h1 style='color:#0066FF'>{data['kasa_nakit']:,.0f} ₺</h1></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'><h3>TOPLAM ALACAK</h3><h1 style='color:#FF3B30'>{toplam_alacak:,.0f} ₺</h1></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'><h3>DAİRE SAYISI</h3><h1>{len(data['daireler'])}</h1></div>", unsafe_allow_html=True)
    
    if st.button("💾 VERİLERİ BULUTA YEDEKLE", type="primary"):
        kaydet(data)
        st.success("Yedekleme başarılı.")

# (Diğer menü içerikleri buraya eklenebilir...)

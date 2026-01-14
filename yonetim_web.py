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

# --- LOGO ---
LOGO_DOSYA = "logo.png" 

# --- CSS: v79.0 ULTIMATE ARCHITECTURE (AGRESSIVE GLASSMOPHISM & DEEP TRANSPARENCY) ---
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">

<style>
    /* 1. TÜM KONTEYNERLARI KÖKTEN ŞEFFAFLAŞTIR (BEYAZ KUTULARI SİLER) */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .main, 
    [data-testid="stVerticalBlock"], [data-testid="stHorizontalBlock"], 
    .stColumn, .stContainer, [data-testid="stExpander"], .element-container, .stMarkdown {
        background-color: transparent !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* 2. ANA ARKA PLAN: DERİN RADIAL GRADIENT (APPLE STYLE) */
    [data-testid="stAppViewMain"] {
        background: radial-gradient(circle at top right, #F8F9FC 0%, #DDE4EE 100%) !important;
        background-attachment: fixed !important;
    }

    /* 3. GERÇEK CAM EFEKTİ (GLASSMORPHISM) KARTLAR */
    /* Backdrop filter artık katmanlar şeffaf olduğu için çalışacak */
    .metric-card {
        background: rgba(255, 255, 255, 0.45) !important; /* Yarı şeffaf kristal beyaz */
        backdrop-filter: blur(25px) saturate(200%) !important; /* Derin buzlu cam */
        -webkit-backdrop-filter: blur(25px) saturate(200%) !important;
        border: 1px solid rgba(255, 255, 255, 0.6) !important; /* Kristal parıltılı kenarlık */
        border-radius: 35px !important;
        padding: 40px !important;
        box-shadow: 0 15px 35px rgba(31, 38, 135, 0.05) !important;
        transition: all 0.5s cubic-bezier(0.2, 0.8, 0.2, 1) !important;
        height: 100% !important;
        margin-bottom: 25px;
    }
    
    .metric-card:hover {
        transform: translateY(-15px) scale(1.02) !important;
        background: rgba(255, 255, 255, 0.8) !important;
        box-shadow: 0 30px 60px rgba(0, 102, 255, 0.15) !important;
        border-color: #0066FF !important;
    }

    .metric-card h3 { color: #64748b; font-size: 14px; text-transform: uppercase; font-weight: 700; letter-spacing: 2px; margin-bottom: 15px; }
    .metric-card h1 { color: #1e293b; font-size: 44px; font-weight: 800; margin: 0; letter-spacing: -2px; }

    /* 4. GRAFİK ÖZGÜRLÜĞÜ: BEYAZ KUTUYU ZORLA KALDIR */
    [data-testid="stPlotlyChart"], .plotly, .user-select-none {
        background-color: transparent !important;
        background: transparent !important;
        border: none !important;
    }

    /* 5. SOL MENÜ: YÜZEN ETKİ & SERT ÇİZGİSİZ */
    section[data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.95) !important;
        border-right: none !important;
        box-shadow: 20px 0 60px rgba(0,0,0,0.03) !important;
    }
    [data-testid="stSidebarCollapseButton"] { display: none !important; }

    /* 6. GİZLENECEKLER */
    .stDeployButton, [data-testid="stHeaderActionElements"], [data-testid="stToolbar"],
    [data-testid="stManageAppButton"], footer, #MainMenu { display: none !important; }
    header[data-testid="stHeader"] { background: transparent !important; height: 0px !important; }

    /* 7. BUTONLAR VE MODERN INPUTLAR */
    button[kind="primary"], [data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #0066FF 0%, #0047AB 100%) !important;
        border-radius: 18px !important;
        padding: 15px 30px !important;
        font-weight: 700 !important;
        box-shadow: 0 12px 25px -5px rgba(0, 102, 255, 0.4) !important;
        transition: 0.3s !important;
        color: white !important;
    }
    
    .stTextInput input {
        border: 1.5px solid #E2E8F0 !important;
        border-radius: 18px !important;
        background-color: rgba(255, 255, 255, 0.9) !important;
        padding: 14px 20px !important;
    }

    /* 8. ÖZEL MODERN SCROLLBAR */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #0066FF; }

    .sidebar-divider { margin: 30px 0; border-bottom: 2px solid #F1F5F9; }
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

def sifre_sifirla_excel(kadi, guvenlik_kodu, yeni_sifre):
    try:
        client = baglanti_kur()
        sheet = client.open(SHEET_DB).worksheet(SHEET_USERS)
        records = sheet.get_all_records()
        for i, user in enumerate(records):
            if str(user['kullanici_adi']) == str(kadi):
                if str(user.get('guvenlik_kodu', '')) == str(guvenlik_kodu):
                    sheet.update_cell(i + 2, 2, yeni_sifre)
                    return True, "Şifreniz başarıyla güncellendi."
        return False, "Bilgiler hatalı!"
    except: return False, "Sistem Hatası!"

def demo_veri():
    return {
        "site_adi": "KoruPark", "kasa_nakit": 85100.0, "kasa_banka": 250000.0,
        "giderler": [], "daireler": {
            "1": {"sahip": "Ahmet Yılmaz", "blok": "A", "tel": "905551112233", "borc": 0.0, "gecmis": [], "plaka": "-", "icra": False, "notlar": [], "aile": []},
            "2": {"sahip": "Yeter Zorlu", "blok": "A", "tel": "905337140212", "borc": 5300.0, "gecmis": ["Aidat x3"], "plaka": "-", "icra": True, "notlar": [], "aile": []}
        }
    }

if "data" not in st.session_state: st.session_state["data"] = verileri_yukle()
data = st.session_state["data"]

# --- PDF MODÜLÜ ---
def tr_duzelt(text):
    source = "şŞıİğĞüÜöÖçÇ"; target = "sSiIgGuUoOcC"
    return str(text).translate(str.maketrans(source, target))

def pdf_olustur(daire_no, isim, tutar):
    if not LIB_OK: return None
    pdf = FPDF(); pdf.add_page(); pdf.set_line_width(1); pdf.rect(5, 5, 200, 287)
    pdf.set_font("Arial", 'B', 24); pdf.cell(0, 10, txt=tr_duzelt(data['site_adi'].upper()), ln=True, align='C')
    pdf.set_y(40); pdf.set_font("Arial", size=10); pdf.cell(0, 5, txt="TAHSILAT MAKBUZU", ln=True, align='C'); pdf.ln(10)
    pdf.cell(50, 12, txt="Tarih", border=1); pdf.cell(140, 12, txt=f"{str(datetime.date.today())}", border=1, ln=True)
    pdf.cell(50, 12, txt="Isim", border=1); pdf.cell(140, 12, txt=tr_duzelt(isim), border=1, ln=True)
    pdf.cell(50, 12, txt="Tutar", border=1); pdf.cell(140, 12, txt=f"{tutar} TL", border=1, ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- OTURUM AYARLARI ---
if "giris" not in st.session_state: st.session_state["giris"] = False
if "ui_mode" not in st.session_state: st.session_state["ui_mode"] = "login"
if "active_menu" not in st.session_state: st.session_state["active_menu"] = "Genel Bakış"

# --- GİRİŞ / SIFIRLAMA MODÜLÜ ---
if not st.session_state["giris"]:
    c1, c2, c3 = st.columns([1, 1.4, 1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        if st.session_state["ui_mode"] == "login":
            st.markdown("<h2 style='text-align:center; font-weight:800; color:#1E293B; letter-spacing:-1px;'>GİRİŞ YAP</h2>", unsafe_allow_html=True)
            u = st.text_input("Kullanıcı Kodu", key="l_u"); p = st.text_input("Şifre", type="password", key="l_p")
            if st.button("GİRİŞ YAP", type="primary", use_container_width=True):
                user = kullanici_dogrula(u, p)
                if user: st.session_state.update({"giris": True, "rol": user["rol"], "user": user["daire_no"]}); st.rerun()
                else: st.error("Hatalı giriş!")
            if st.button("🔒 Şifremi Unuttum", type="secondary", use_container_width=True):
                st.session_state["ui_mode"] = "forgot"; st.rerun()
        elif st.session_state["ui_mode"] == "forgot":
            st.markdown("<h4 style='text-align:center;'>Şifre Sıfırlama</h4>", unsafe_allow_html=True)
            f_u = st.text_input("Kullanıcı Kodu", key="f_u"); f_k = st.text_input("Güvenlik Kodu", type="password", key="f_k"); f_p = st.text_input("Yeni Şifre", type="password", key="f_p")
            if st.button("GÜNCELLE", type="primary", use_container_width=True):
                basari, mesaj = sifre_sifirla_excel(f_u, f_k, f_p)
                if basari: st.success(mesaj); st.session_state["ui_mode"] = "login"; st.rerun()
                else: st.error(mesaj)
            if st.button("⬅️ Geri Dön", type="secondary", use_container_width=True):
                st.session_state["ui_mode"] = "login"; st.rerun()
    st.stop()

# --- ANA UYGULAMA ---
with st.sidebar:
    st.markdown("<div style='text-align: center; padding: 20px;'><h2 style='color:#1E293B; font-weight:900;'>KORUPARK</h2></div>", unsafe_allow_html=True)
    if st.session_state["rol"] == "admin":
        if st.button("🏠 Genel Bakış"): st.session_state["active_menu"] = "Genel Bakış"; st.rerun()
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        if st.button("💸 Gider Yönetimi"): st.session_state["active_menu"] = "Giderler"; st.rerun()
        if st.button("👥 Hesaplar & Aidat"): st.session_state["active_menu"] = "Hesaplar"; st.rerun()
        if st.button("🏘️ Blok Haritası"): st.session_state["active_menu"] = "Harita"; st.rerun()
        if st.button("⚖️ Hukuk & İcra"): st.session_state["active_menu"] = "Hukuk"; st.rerun()
        if st.button("💬 WhatsApp"): st.session_state["active_menu"] = "WhatsApp"; st.rerun()
        if st.button("☁️ Bulut Arşiv"): st.session_state["active_menu"] = "Arşiv"; st.rerun()
        if st.button("📄 Raporlar"): st.session_state["active_menu"] = "Raporlar"; st.rerun()
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        if st.button("🚪 Güvenli Çıkış"): st.session_state["giris"] = False; st.rerun()

menu = st.session_state["active_menu"]
st.markdown(f"<h1 style='font-weight: 800; color: #1E293B; margin-bottom: 30px;'>{menu}</h1>", unsafe_allow_html=True)

if menu == "Genel Bakış":
    toplam_alacak = sum(d['borc'] for d in data['daireler'].values())
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='metric-card'><h3>KASA</h3><h1 style='color:#0066FF'>{data['kasa_nakit']:,.0f} ₺</h1></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='metric-card'><h3>ALACAK</h3><h1 style='color:#FF3B30'>{toplam_alacak:,.0f} ₺</h1></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='metric-card'><h3>GİDER</h3><h1>{sum(g['tutar'] for g in data['giderler']):,.0f} ₺</h1></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='metric-card'><h3>DAİRE</h3><h1>{len(data['daireler'])}</h1></div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    cl, cr = st.columns([2, 1])
    with cl:
        fig = px.pie(values=[data['kasa_nakit'], toplam_alacak], names=['Kasa', 'Alacak'], hole=0.75, color_discrete_sequence=["#0066FF", "#FF3B30"])
        # --- GRAFİK ŞEFFAFLIK AYARI ---
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family="Poppins", size=14, color="#1e293b"), margin=dict(t=0,b=0,l=0,r=0))
        st.plotly_chart(fig, use_container_width=True)
    with cr:
        st.subheader("Veri Güvenliği")
        if st.button("💾 EXCEL'E YEDEKLE", type="primary", use_container_width=True): kaydet(data); st.success("Yedeklendi")

elif menu == "Giderler":
    c1, c2 = st.columns([1,2]); 
    with c1:
        with st.form("g_f"):
            gt = st.selectbox("Tür", ["Enerji", "Personel", "Diğer"]); ga = st.text_input("Açıklama"); gm = st.number_input("Tutar", min_value=0.0)
            if st.form_submit_button("Ekle"):
                data["giderler"].append({"tarih": str(datetime.date.today()), "tur": gt, "aciklama": ga, "tutar": gm})
                data["kasa_nakit"] -= gm; kaydet(data); st.rerun()
    with c2: st.dataframe(pd.DataFrame(data["giderler"]), use_container_width=True)

elif menu == "Hesaplar":
    secilen = st.selectbox("Daire", list(data["daireler"].keys())); info = data["daireler"][secilen]
    st.markdown(f"<div class='metric-card'><h3>{info['sahip']}</h3><h1>{info['borc']:,.2f} ₺</h1></div>", unsafe_allow_html=True)
    t = st.number_input("Tahsilat", min_value=0.0)
    if st.button("Onayla"):
        info["borc"] -= t; data["kasa_nakit"] += t; info["gecmis"].append(f"{datetime.date.today()}|{t}"); kaydet(data); st.rerun()

elif menu == "Harita":
    cols = st.columns(4)
    for i, (no, info) in enumerate(sorted(data["daireler"].items())):
        with cols[i % 4]:
            color = "#FF3B30" if info["borc"] > 0 else "#0066FF"
            st.markdown(f"<div class='metric-card' style='border-top: 8px solid {color};'><h3>DAİRE {no}</h3><b>{info['sahip']}</b><br>{info['borc']} ₺</div><br>", unsafe_allow_html=True)

elif menu == "Hukuk":
    icra = [v for v in data["daireler"].values() if v["icra"]]
    if icra: st.dataframe(pd.DataFrame(icra), use_container_width=True)
    else: st.success("Hukuki süreçte daire bulunmuyor.")

elif menu == "WhatsApp":
    st.info("Toplu WhatsApp mesaj modülü.")
    st.button("MESAJLARI GÖNDER")

elif menu == "Arşiv":
    st.file_uploader("Dosyaları Buraya Sürükleyin", accept_multiple_files=True)

elif menu == "Raporlar":
    st.dataframe(pd.DataFrame.from_dict(data["daireler"], orient='index'), use_container_width=True)

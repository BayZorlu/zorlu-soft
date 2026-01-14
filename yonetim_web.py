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

# --- CSS: v75.1 ULTRA-AGRESSIVE VISUAL FIX ---
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">

<style>
    /* 1. GIZLENECEKLER */
    .stDeployButton, [data-testid="stHeaderActionElements"], [data-testid="stToolbar"],
    [data-testid="stManageAppButton"], footer, #MainMenu { display: none !important; }
    header[data-testid="stHeader"] { background: transparent !important; height: 0px !important; }

    /* 2. ARKA PLAN: DERİN RADIAL GRADIENT */
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at top right, #F8F9FC 0%, #DDE4EE 100%) !important;
        background-attachment: fixed !important;
    }
    
    /* 3. TÜM İÇ KONTEYNERLARI ŞEFFAF YAP (Cam Efekti için Şart) */
    .stApp, [data-testid="stVerticalBlock"], [data-testid="stHorizontalBlock"], 
    .element-container, .stMarkdown, [data-testid="stExpander"] {
        background-color: transparent !important;
    }
    .block-container { padding-top: 40px !important; }

    /* 4. GERÇEK BUZLU CAM KARTLAR (GLASSMORPHISM) */
    .metric-card {
        background: rgba(255, 255, 255, 0.4) !important; /* Yarı şeffaf */
        backdrop-filter: blur(15px) saturate(180%) !important; /* Buzlu cam dokusu */
        -webkit-backdrop-filter: blur(15px) saturate(180%) !important;
        border: 1px solid rgba(255, 255, 255, 0.4) !important;
        border-radius: 28px !important;
        padding: 30px !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.03) !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        height: 100% !important;
    }
    
    /* Kart Hover Etkisi */
    .metric-card:hover {
        transform: translateY(-12px) !important;
        background: rgba(255, 255, 255, 0.7) !important; /* Üstüne gelince beyazlaşır */
        box-shadow: 0 20px 50px rgba(0, 102, 255, 0.12) !important;
        border-color: #0066FF !important;
    }
    
    .metric-card h3 { color: #64748b; font-size: 13px; text-transform: uppercase; font-weight: 700; letter-spacing: 1.5px; margin-bottom: 12px; }
    .metric-card h1 { color: #1e293b; font-size: 36px; font-weight: 800; margin: 0; letter-spacing: -1.5px; }

    /* 5. YÜZEN SOL MENÜ & SERT ÇİZGİYİ KALDIRMA */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: none !important;
        box-shadow: 15px 0 45px rgba(0,0,0,0.04) !important;
    }
    [data-testid="stSidebarCollapseButton"] { display: none !important; }

    /* 6. GRAFİK KONTEYNERINI ZORLA ŞEFFAF YAP */
    [data-testid="stPlotlyChart"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* 7. BUTONLAR VE INPUTLAR */
    button[kind="primary"] {
        background: linear-gradient(135deg, #0066FF 0%, #0047AB 100%) !important;
        border-radius: 16px !important;
        border: none !important;
        box-shadow: 0 10px 20px -5px rgba(0, 102, 255, 0.4) !important;
        transition: 0.3s !important;
    }
    button[kind="primary"]:hover {
        transform: scale(1.02) !important;
        box-shadow: 0 15px 30px -5px rgba(0, 102, 255, 0.5) !important;
    }

    /* 8. ÖZEL SCROLLBAR */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #0066FF; }

    .sidebar-divider { margin: 20px 0; border-bottom: 1px solid #F1F5F9; }
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
                    return True, "Şifreniz güncellendi."
        return False, "Bilgiler hatalı!"
    except: return False, "Sistem Hatası!"

def demo_veri():
    return {
        "site_adi": "KoruPark", "kasa_nakit": 85100.0, "kasa_banka": 250000.0,
        "giderler": [], "daireler": {
            "1": {"sahip": "Ahmet Yılmaz", "blok": "A", "tel": "905551112233", "borc": 0.0, "gecmis": [], "plaka": "-", "icra": False, "notlar": [], "aile": []},
            "2": {"sahip": "Yeter Zorlu", "blok": "A", "tel": "905337140212", "borc": 5400.0, "gecmis": [], "plaka": "-", "icra": True, "notlar": [], "aile": []}
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
    if os.path.exists(LOGO_DOSYA): pdf.image(LOGO_DOSYA, 10, 8, 30); pdf.set_xy(40, 20)
    pdf.set_font("Arial", 'B', 24); pdf.cell(0, 10, txt=tr_duzelt(data['site_adi'].upper()), ln=True, align='C')
    pdf.set_y(40); pdf.set_font("Arial", size=10); pdf.cell(0, 5, txt="TAHSILAT MAKBUZU", ln=True, align='C'); pdf.ln(10)
    pdf.set_font("Arial", size=14)
    pdf.cell(50, 12, txt="Tarih", border=1); pdf.cell(140, 12, txt=f"{str(datetime.date.today())}", border=1, ln=True)
    pdf.cell(50, 12, txt="Daire", border=1); pdf.cell(140, 12, txt=f"{daire_no}", border=1, ln=True)
    pdf.cell(50, 12, txt="Sayin", border=1); pdf.cell(140, 12, txt=tr_duzelt(isim), border=1, ln=True)
    pdf.cell(50, 12, txt="Tutar", border=1); pdf.cell(140, 12, txt=f"{tutar} TL", border=1, ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- OTURUM AYARLARI ---
if "giris" not in st.session_state: st.session_state["giris"] = False
if "ui_mode" not in st.session_state: st.session_state["ui_mode"] = "login"
if "active_menu" not in st.session_state: st.session_state["active_menu"] = "Genel Bakış"

# --- GİRİŞ / SIFIRLAMA ---
if not st.session_state["giris"]:
    c1, c2, c3 = st.columns([1, 1.4, 1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        if st.session_state["ui_mode"] == "login":
            st.markdown("<h2 style='text-align:center;'>GİRİŞ YAP</h2>", unsafe_allow_html=True)
            u = st.text_input("Kullanıcı Kodu", key="l_u"); p = st.text_input("Şifre", type="password", key="l_p")
            if st.button("GİRİŞ YAP", type="primary", use_container_width=True):
                user = kullanici_dogrula(u, p)
                if user: st.session_state.update({"giris": True, "rol": user["rol"], "user": user["daire_no"]}); st.rerun()
                else: st.error("Hatalı giriş!")
            if st.button("🔒 Şifremi Unuttum", type="secondary", use_container_width=True):
                st.session_state["ui_mode"] = "forgot"; st.rerun()
        elif st.session_state["ui_mode"] == "forgot":
            st.markdown("<h4 style='text-align:center;'>Şifre Sıfırlama</h4>", unsafe_allow_html=True)
            f_u = st.text_input("Kullanıcı Kodu", key="f_u")
            f_k = st.text_input("Güvenlik Kodu", type="password", key="f_k")
            f_p = st.text_input("Yeni Şifre", type="password", key="f_p")
            if st.button("GÜNCELLE", type="primary", use_container_width=True):
                basari, mesaj = sifre_sifirla_excel(f_u, f_k, f_p)
                if basari: st.success(mesaj); st.session_state["ui_mode"] = "login"; st.rerun()
                else: st.error(mesaj)
            if st.button("⬅️ Geri Dön", type="secondary", use_container_width=True):
                st.session_state["ui_mode"] = "login"; st.rerun()
    st.stop()

# --- ANA UYGULAMA (GİRİŞ SONRASI) ---
st.markdown("<style>div[data-testid='column']:nth-of-type(2) > div > div { background: transparent !important; box-shadow: none !important; border: none !important; }</style>", unsafe_allow_html=True)

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
st.markdown(f"<h1 style='font-weight: 800; color: #1E293B; margin-bottom: 25px;'>{menu}</h1>", unsafe_allow_html=True)

if menu == "Genel Bakış":
    toplam_alacak = sum(d['borc'] for d in data['daireler'].values())
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='metric-card'><h3>GÜNCEL KASA</h3><h1 style='color:#0066FF'>{data['kasa_nakit']:,.0f} ₺</h1></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='metric-card'><h3>TOPLAM ALACAK</h3><h1 style='color:#FF3B30'>{toplam_alacak:,.0f} ₺</h1></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='metric-card'><h3>TOPLAM GİDER</h3><h1>{sum(g['tutar'] for g in data['giderler']):,.0f} ₺</h1></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='metric-card'><h3>DAİRE SAYISI</h3><h1>{len(data['daireler'])}</h1></div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    cl, cr = st.columns([2, 1])
    with cl:
        fig = px.pie(values=[data['kasa_nakit'], toplam_alacak], names=['Kasa', 'Alacak'], hole=0.75, color_discrete_sequence=["#0066FF", "#FF3B30"])
        # --- ŞEFFAF GRAFİK (KESİN ÇÖZÜM) ---
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)', 
            font=dict(family="Poppins", color="#1e293b"),
            margin=dict(t=0, b=0, l=0, r=0)
        )
        st.plotly_chart(fig, use_container_width=True)
    with cr:
        st.subheader("Veri Güvenliği")
        if st.button("💾 EXCEL'E YEDEKLE", type="primary", use_container_width=True): kaydet(data); st.success("Yedeklendi")

elif menu == "Giderler":
    c1, c2 = st.columns([1,2])
    with c1:
        with st.form("g_f"):
            gt = st.selectbox("Tür", ["Enerji", "Personel", "Bakım", "Diğer"]); ga = st.text_input("Açıklama"); gm = st.number_input("Tutar", min_value=0.0)
            if st.form_submit_button("Gider Ekle", type="primary"):
                data["giderler"].append({"tarih": str(datetime.date.today()), "tur": gt, "aciklama": ga, "tutar": gm})
                data["kasa_nakit"] -= gm; kaydet(data); st.rerun()
    with c2: st.dataframe(pd.DataFrame(data["giderler"]), use_container_width=True)

elif menu == "Hesaplar":
    src = st.text_input("🔍 Daire Ara")
    filtre = next((k for k,v in data["daireler"].items() if src.lower() in v["sahip"].lower() or src == k), list(data["daireler"].keys())[0])
    info = data["daireler"][filtre]
    st.markdown(f"<div class='metric-card'><h3>{filtre} - {info['sahip']}</h3><h1>{info['borc']:,.2f} ₺</h1></div>", unsafe_allow_html=True)
    t = st.number_input("Tahsilat Tutarı", min_value=0.0)
    if st.button("Ödeme Onayla", type="primary"):
        info["borc"] -= t; data["kasa_nakit"] += t; info["gecmis"].append(f"{datetime.date.today()} | Tahsilat: {t}"); kaydet(data); st.rerun()
    pdf = pdf_olustur(filtre, info["sahip"], t if t > 0 else info["borc"])
    if pdf: st.download_button("📄 PDF Makbuz İndir", pdf, f"makbuz_{filtre}.pdf", "application/pdf")

elif menu == "Harita":
    cols = st.columns(4)
    for i, (no, info) in enumerate(sorted(data["daireler"].items())):
        with cols[i % 4]:
            color = "#FF3B30" if info["borc"] > 0 else "#0066FF"
            st.markdown(f"<div class='metric-card' style='border-top: 5px solid {color};'><h3>DAİRE {no}</h3><b>{info['sahip']}</b><br>{info['borc']} ₺</div><br>", unsafe_allow_html=True)

elif menu == "Hukuk":
    icra = [v for v in data["daireler"].values() if v["icra"]]
    if icra: st.dataframe(pd.DataFrame(icra), use_container_width=True)
    else: st.success("İcralık daire bulunmuyor.")

elif menu == "WhatsApp":
    st.info("Borçlu sakinlere WhatsApp üzerinden mesaj gönderimi yakında.")
    st.button("MESAJLARI GÖNDER")

elif menu == "Arşiv":
    st.file_uploader("Dosyaları Buraya Sürükleyin", accept_multiple_files=True)

elif menu == "Raporlar":
    st.dataframe(pd.DataFrame.from_dict(data["daireler"], orient='index'), use_container_width=True)

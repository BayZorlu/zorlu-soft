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

# --- CSS: v70.4 KESİN GÖRSEL İYİLEŞTİRME ---
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">

<style>
    /* 0. GENEL TİPOGRAFİ */
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }

    /* 1. GİZLENECEKLER */
    .stDeployButton, [data-testid="stHeaderActionElements"], [data-testid="stToolbar"],
    [data-testid="stManageAppButton"], footer, #MainMenu {
        display: none !important;
    }
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 0px !important;
        visibility: hidden !important;
    }

    /* 2. ARKA PLAN: SUBTLE GRADIENT (KESİN ÇÖZÜM) */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #F8F9FC 0%, #E2E8F0 100%) !important;
        background-attachment: fixed;
    }
    .block-container {
        padding-top: 50px !important;
    }

    /* 3. YÜZEN SOL MENÜ (Sert Çizgiyi Kaldırır) */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: none !important;
        box-shadow: 10px 0 30px rgba(0,0,0,0.04) !important;
    }
    [data-testid="stSidebarCollapseButton"] { display: none !important; }

    /* 4. ÖZEL KAYDIRMA ÇUBUKLARI */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; border: 2px solid transparent; background-clip: content-box; }
    ::-webkit-scrollbar-thumb:hover { background: #0066FF; }

    /* 5. INPUT KUTULARI (v70 TASARIMI) */
    .stTextInput > div > div { border: none !important; box-shadow: none !important; background-color: transparent !important; }
    .stTextInput input {
        border: 1px solid #cbd5e1 !important;
        border-radius: 14px !important;
        padding: 12px 16px !important;
        background-color: #FFFFFF !important;
        color: #1E293B !important;
        transition: all 0.3s;
    }
    .stTextInput input:focus {
        border-color: #0066FF !important;
        box-shadow: 0 0 0 4px rgba(0, 102, 255, 0.1) !important;
    }

    /* 6. BUTONLAR: MİKRO ETKİLEŞİM */
    button[kind="primary"], [data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #0066FF 0%, #0047AB 100%) !important;
        border: none !important;
        color: white !important;
        border-radius: 14px !important;
        padding: 14px 28px !important;
        font-weight: 700 !important;
        box-shadow: 0 10px 20px -10px rgba(0, 102, 255, 0.5) !important;
        transition: all 0.3s ease !important;
        width: 100%;
    }
    button[kind="primary"]:hover {
        transform: translateY(-2px) scale(1.01);
        box-shadow: 0 15px 30px -10px rgba(0, 102, 255, 0.6) !important;
    }

    button[kind="secondary"], [data-testid="baseButton-secondary"] {
        background-color: transparent !important;
        border: none !important;
        color: #64748b !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        margin-top: -10px !important;
    }
    button[kind="secondary"]:hover { color: #0066FF !important; text-decoration: underline; }

    /* 7. CANLI KARTLAR (MIKRO-ETKİLEŞİM) */
    .metric-card {
        background: #FFFFFF;
        padding: 30px;
        border-radius: 24px;
        border: 1px solid #F1F5F9;
        box-shadow: 0 10px 20px rgba(0,0,0,0.02);
        transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
        height: 100%;
    }
    .metric-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.06);
        border-color: #0066FF;
    }
    .metric-card h3 { color: #94a3b8; font-size: 13px; text-transform: uppercase; font-weight: 700; letter-spacing: 1.2px; margin-bottom: 12px; }
    .metric-card h1 { color: #1e293b; font-size: 34px; font-weight: 800; margin: 0; letter-spacing: -1px; }

    /* GİRİŞ KARTI (Bütünleşik) */
    div[data-testid="column"]:nth-of-type(2) > div > div {
        background: #FFFFFF;
        padding: 55px;
        border-radius: 32px;
        box-shadow: 0 40px 100px rgba(0,0,0,0.08);
        border: 1px solid #f1f5f9;
    }

    .sidebar-divider { margin: 25px 0; border-bottom: 1px solid #EFF2F7; }
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
        json_data = json.dumps(veri, ensure_ascii=False)
        sheet.update_cell(1, 1, json_data)
    except Exception as e: st.error(f"Kayıt Hatası: {e}")

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
                if str(user.get('guvenlik_kodu', '')) == str(guvenlik_kodu):
                    sheet.update_cell(i + 2, 2, yeni_sifre)
                    return True, "Şifreniz başarıyla güncellendi."
        return False, "Bilgiler hatalı!"
    except Exception as e: return False, f"Hata: {e}"

def demo_veri():
    return {
        "site_adi": "KoruPark",
        "kasa_nakit": 85100.0, "kasa_banka": 250000.0,
        "giderler": [], "daireler": {
            "1": {"sahip": "Ahmet Yılmaz", "blok": "A", "tel": "905551112233", "borc": 0.0, "gecmis": [], "plaka": "-", "icra": False, "notlar": [], "aile": []},
            "2": {"sahip": "Yeter Zorlu", "blok": "A", "tel": "905337140212", "borc": 5400.0, "gecmis": ["Aidat x3"], "plaka": "-", "icra": True, "notlar": ["Avukatta"], "aile": ["Mehmet"]}
        }
    }

if "data" not in st.session_state: st.session_state["data"] = verileri_yukle()
data = st.session_state["data"]

# --- PDF MODÜLÜ ---
def tr_duzelt(text):
    text = str(text)
    source = "şŞıİğĞüÜöÖçÇ"; target = "sSiIgGuUoOcC"
    translation = str.maketrans(source, target)
    return text.translate(translation)

def pdf_olustur(daire_no, isim, tutar):
    if not LIB_OK: return None
    pdf = FPDF(); pdf.add_page(); pdf.set_line_width(1); pdf.rect(5, 5, 200, 287)
    if os.path.exists(LOGO_DOSYA): pdf.image(LOGO_DOSYA, 10, 8, 30); pdf.set_xy(40, 20)
    else: pdf.set_xy(10, 20)
    pdf.set_font("Arial", 'B', 24); pdf.cell(0, 10, txt=tr_duzelt(data['site_adi'].upper()), ln=True, align='C')
    pdf.set_y(40); pdf.set_font("Arial", size=10); pdf.cell(0, 5, txt="Yonetim Ofisi", ln=True, align='C'); pdf.ln(10)
    pdf.set_fill_color(200, 220, 255); pdf.set_font("Arial", 'B', 16); pdf.cell(190, 15, txt="TAHSILAT MAKBUZU", ln=True, align='C', fill=True); pdf.ln(10)
    pdf.set_font("Arial", size=14)
    pdf.cell(50, 12, txt="Tarih", border=1); pdf.cell(140, 12, txt=f"{str(datetime.date.today())}", border=1, ln=True)
    pdf.cell(50, 12, txt="Daire No", border=1); pdf.cell(140, 12, txt=f"{str(daire_no)}", border=1, ln=True)
    pdf.cell(50, 12, txt="Sayin", border=1); pdf.cell(140, 12, txt=f"{isim}", border=1, ln=True)
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
            st.markdown("<h2 style='text-align:center; color:#1E293B; font-weight:800; margin-bottom:40px;'>GİRİŞ YAP</h2>", unsafe_allow_html=True)
            u = st.text_input("Kullanıcı Kodu", key="l_u"); p = st.text_input("Şifre", type="password", key="l_p")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("GİRİŞ YAP", type="primary", use_container_width=True):
                user_data = kullanici_dogrula(u, p)
                if user_data:
                    st.session_state.update({"giris": True, "rol": str(user_data["rol"]), "user": str(user_data["daire_no"])})
                    st.rerun()
                else: st.error("Giriş başarısız.")
            if st.button("🔒 Şifremi Unuttum", type="secondary", use_container_width=True):
                st.session_state["ui_mode"] = "forgot"; st.rerun()

        elif st.session_state["ui_mode"] == "forgot":
            st.markdown("<h4 style='text-align:center; color:#1E293B;'>Şifre Sıfırlama</h4>", unsafe_allow_html=True)
            f_u = st.text_input("Kullanıcı Kodu", key="f_u")
            f_k = st.text_input("Güvenlik Kodu", type="password", key="f_k")
            f_p = st.text_input("Yeni Şifre", type="password", key="f_p")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("ŞİFREYİ GÜNCELLE", type="primary", use_container_width=True):
                basari, mesaj = sifre_sifirla_excel(f_u, f_k, f_p)
                if basari: st.success(mesaj); st.session_state["ui_mode"] = "login"; st.rerun()
                else: st.error(mesaj)
            if st.button("⬅️ Geri Dön", type="secondary", use_container_width=True):
                st.session_state["ui_mode"] = "login"; st.rerun()

        st.markdown("<p style='text-align:center; color:#94a3b8; margin-top:30px; font-size:12px;'>Zorlu Soft | © 2026 | v70.4</p>", unsafe_allow_html=True)
    st.stop()

# --- ANA UYGULAMA (GİRİŞ SONRASI) ---
st.markdown("<style>div[data-testid='column']:nth-of-type(2) > div > div { background: transparent !important; padding: 0 !important; border: none !important; box-shadow: none !important; }</style>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("""<div style="padding: 25px 10px; text-align: center;"><h3 style="color:#1E293B; margin:0; font-weight:900;">KORUPARK</h3><p style="color:#64748b; margin:0; font-size:13px; font-weight: 600; background: #EBF5FF; color: #0066FF; display: inline-block; padding: 6px 14px; border-radius: 20px;">Sistem Yöneticisi</p></div>""", unsafe_allow_html=True)
    if st.session_state["rol"] == "admin":
        if st.button("🏠 Genel Bakış"): st.session_state["active_menu"] = "Genel Bakış"; st.rerun()
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        if st.button("💸 Gider Yönetimi"): st.session_state["active_menu"] = "Giderler"; st.rerun()
        if st.button("👥 Hesaplar & Aidat"): st.session_state["active_menu"] = "Hesaplar"; st.rerun()
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        if st.button("🏘️ Blok Haritası"): st.session_state["active_menu"] = "Harita"; st.rerun()
        if st.button("⚖️ Hukuk & İcra"): st.session_state["active_menu"] = "Hukuk/İcra"; st.rerun()
        if st.button("📄 Raporlar"): st.session_state["active_menu"] = "Raporlar"; st.rerun()
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        if st.button("🚪 Güvenli Çıkış"): st.session_state["giris"] = False; st.rerun()

menu = st.session_state["active_menu"]
st.markdown(f"<h1 style='font-weight: 800; color: #1E293B; margin-bottom: 25px;'>{menu}</h1>", unsafe_allow_html=True)

if st.session_state["rol"] == "admin":
    if menu == "Genel Bakış":
        toplam_alacak = sum(d['borc'] for d in data['daireler'].values())
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"<div class='metric-card'><h3>GÜNCEL KASA</h3><h1 style='color:#0066FF'>{data['kasa_nakit']:,.0f} ₺</h1></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><h3>TOPLAM ALACAK</h3><h1 style='color:#FF3B30'>{toplam_alacak:,.0f} ₺</h1></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-card'><h3>TOPLAM GİDER</h3><h1 style='color:#FF9500'>{sum(g['tutar'] for g in data['giderler']):,.0f} ₺</h1></div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='metric-card'><h3>DAİRE SAYISI</h3><h1 style='color:#1E293B'>{len(data['daireler'])}</h1></div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        cl, cr = st.columns([2, 1])
        with cl:
            df_pie = pd.DataFrame({"Durum": ["Kasa", "Alacak"], "Tutar": [data['kasa_nakit'], toplam_alacak]})
            fig = px.pie(df_pie, values='Tutar', names='Durum', hole=0.75, color_discrete_sequence=["#0066FF", "#FF3B30"])
            # Şeffaf Grafik Entegrasyonu
            fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family="Poppins"))
            st.plotly_chart(fig, use_container_width=True)
        with cr:
            st.subheader("Veri Güvenliği")
            if st.button("💾 VERİLERİ ŞİMDİ YEDEKLE", type="primary", use_container_width=True): 
                kaydet(data); st.success("Tamamlandı")

    elif menu == "Giderler":
        c1, c2 = st.columns([1,2])
        with c1:
            with st.form("g_f"):
                gt = st.selectbox("Tür", ["Enerji", "Personel", "Bakım", "Diğer"]); ga = st.text_input("Açıklama"); gm = st.number_input("Tutar", min_value=0.0)
                if st.form_submit_button("Ekle", type="primary"):
                    data["giderler"].append({"tarih": str(datetime.date.today()), "tur": gt, "aciklama": ga, "tutar": gm})
                    data["kasa_nakit"] -= gm; kaydet(data); st.rerun()
        with c2: st.dataframe(pd.DataFrame(data["giderler"]), use_container_width=True)

    elif menu == "Hesaplar":
        secilen = st.selectbox("Daire Seç", list(data["daireler"].keys()))
        info = data["daireler"][secilen]
        st.markdown(f"<div class='metric-card' style='border-left: 8px solid {'#FF3B30' if info['borc'] > 0 else '#0066FF'};'><h3>{secilen} - {info['sahip']}</h3><h1>{info['borc']:,.2f} ₺</h1></div>", unsafe_allow_html=True)
        t = st.number_input("Tahsilat", min_value=0.0)
        if st.button("Ödeme Onayla", type="primary"):
            info["borc"] -= t; data["kasa_nakit"] += t; info["gecmis"].append(f"{datetime.date.today()}|Ödeme: {t}"); kaydet(data); st.rerun()

    elif menu == "Harita":
        cols = st.columns(4)
        for i, (no, info) in enumerate(sorted(data["daireler"].items())):
            with cols[i % 4]:
                color = "#FF3B30" if info["borc"] > 0 else "#0066FF"
                st.markdown(f"<div class='metric-card' style='border-top: 6px solid {color};'><h3>DAİRE {no}</h3><h2>{info['sahip']}</h2><h1>{info['borc']:,.0f} ₺</h1></div><br>", unsafe_allow_html=True)

    elif menu == "Raporlar":
        st.dataframe(pd.DataFrame.from_dict(data["daireler"], orient='index'), use_container_width=True)

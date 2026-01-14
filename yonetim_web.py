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

# --- CSS: TRUE BLUE TASARIM ---
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap" rel="stylesheet">

<style>
    /* 0. ROOT DEĞİŞKENLERİ (Ana Rengi Zorla Mavi Yap) */
    :root {
        --primary-color: #0066FF;
        --background-color: #F8F9FC;
        --secondary-background-color: #FFFFFF;
        --text-color: #1E293B;
        --font: 'Poppins', sans-serif;
    }

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

    /* 2. INPUT KUTULARI (Tek Renk Gri - Focus Mavi) */
    /* Dış çerçeveyi ve gölgeyi kaldır */
    .stTextInput > div > div {
        border: none !important;
        box-shadow: none !important;
        background-color: transparent !important;
    }
    
    /* İç kutuyu şekillendir */
    .stTextInput input {
        border: 1px solid #cbd5e1 !important;
        border-radius: 12px !important;
        padding: 12px 15px !important;
        background-color: #FFFFFF !important;
        color: #1E293B !important;
        transition: all 0.2s;
    }
    
    /* Tıklayınca Mavi Ol */
    .stTextInput input:focus {
        border-color: #0066FF !important;
        box-shadow: 0 0 0 2px rgba(0, 102, 255, 0.2) !important;
    }

    /* 3. BUTONLAR (MAVİ VE SADE) */
    
    /* Primary Buton (GİRİŞ YAP) - Kırmızı olma ihtimalini yok et */
    button[kind="primary"], [data-testid="baseButton-primary"] {
        background-color: #0066FF !important; /* Kesin Mavi */
        border-color: #0066FF !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 6px rgba(0, 102, 255, 0.2) !important;
        transition: 0.3s;
        width: 100%;
    }
    
    button[kind="primary"]:hover, [data-testid="baseButton-primary"]:hover {
        background-color: #0052CC !important; /* Koyu Mavi Hover */
        border-color: #0052CC !important;
        box-shadow: 0 6px 12px rgba(0, 102, 255, 0.3) !important;
    }

    /* Secondary Buton (ŞİFREMİ UNUTTUM) - Link gibi görünsün */
    button[kind="secondary"], [data-testid="baseButton-secondary"] {
        background-color: transparent !important;
        border: none !important;
        color: #64748b !important;
        box-shadow: none !important;
        font-size: 13px !important;
        margin-top: -10px !important;
    }
    
    button[kind="secondary"]:hover, [data-testid="baseButton-secondary"]:hover {
        color: #0066FF !important;
        background-color: transparent !important;
        border: none !important;
        text-decoration: underline;
    }

    /* 4. GİRİŞ EKRANI KARTI */
    /* Orta sütunu beyaz kart yap */
    div[data-testid="column"]:nth-of-type(2) > div > div {
        background: #FFFFFF;
        padding: 50px;
        border-radius: 24px;
        box-shadow: 0 20px 50px rgba(0,0,0,0.08);
        border: 1px solid #f1f5f9;
    }

    /* 5. ARKA PLAN */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(to bottom, #F0F4F8 0%, #D9E2EC 100%) !important;
        background-image: none !important;
    }
    .block-container {
        padding-top: 50px !important;
    }

    /* 6. SOL MENÜ */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        box-shadow: 4px 0 15px -5px rgba(0,0,0,0.05);
        border-right: none !important;
    }
    [data-testid="stSidebarCollapseButton"] { display: none !important; }

    /* Menü Butonları */
    [data-testid="stSidebar"] .stButton button {
        width: 100%;
        background-color: transparent !important;
        border: none !important;
        color: #64748b !important;
        text-align: left;
        padding: 12px 20px;
        border-radius: 10px !important;
        transition: 0.3s;
        box-shadow: none !important; /* Menü butonunda gölge olmasın */
    }
    
    /* Menü Hover */
    [data-testid="stSidebar"] .stButton button:hover {
        background-color: #F1F5F9 !important;
        color: #0F172A !important;
    }

    /* Menü Aktif */
    [data-testid="stSidebar"] .stButton button:focus {
        background-color: #EBF5FF !important;
        color: #0066FF !important;
        font-weight: 600;
    }

    /* 7. KARTLAR (İçerik Sayfası) */
    .metric-card {
        background: #FFFFFF;
        padding: 24px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    .metric-card h3 { color: #94a3b8; font-size: 13px; font-weight: 600; }
    .metric-card h1 { color: #1e293b; font-size: 28px; font-weight: 700; margin: 0; }

    /* Dosya Yükleme Alanı */
    [data-testid="stFileUploaderDropzone"] div div::before {
        content: "Dosyaları buraya sürükleyin";
        visibility: visible;
        font-weight: 600;
        color: #1E293B;
    }
    [data-testid="stFileUploaderDropzone"] div div { visibility: hidden; }
    [data-testid="stFileUploaderDropzone"] div div svg { visibility: visible !important; }

    .sidebar-divider {
        margin: 20px 0;
        border-bottom: 1px solid #EFF2F7;
    }

</style>
""", unsafe_allow_html=True)

# --- VERİTABANI ---
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
        if raw_data: return json.loads(raw_data)
        else: return demo_veri()
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

# --- YENİ: EXCEL TABANLI ŞİFRE SIFIRLAMA FONKSİYONU ---
def sifre_sifirla_excel(kadi, guvenlik_kodu, yeni_sifre):
    try:
        client = baglanti_kur()
        sheet = client.open(SHEET_DB).worksheet(SHEET_USERS)
        records = sheet.get_all_records()
        for i, user in enumerate(records):
            if str(user['kullanici_adi']) == str(kadi):
                # Excel'deki guvenlik_kodu sütununa bakıyoruz
                if str(user.get('guvenlik_kodu', '')) == str(guvenlik_kodu):
                    # Şifre sütunu 2. sütun (B) varsayıyoruz
                    sheet.update_cell(i + 2, 2, yeni_sifre)
                    return True, "Şifreniz başarıyla güncellendi."
        return False, "Kullanıcı adı veya Güvenlik Kodu hatalı!"
    except Exception as e: return False, f"Sistem Hatası: {e}"

# --- DEMO VERİ ---
def demo_veri():
    return {
        "site_adi": "KoruPark",
        "kasa_nakit": 85000.0, 
        "kasa_banka": 250000.0,
        "giderler": [],
        "loglar": [],
        "daireler": {
            "1": {"sahip": "Ahmet Yılmaz", "blok": "A", "tel": "905551112233", "borc": 0.0, "gecmis": [], "plaka": "46 KM 123", "icra": False, "notlar": [], "aile": []},
            "2": {"sahip": "Yeter Zorlu", "blok": "A", "tel": "905337140212", "borc": 5400.0, "gecmis": ["Aidat x3"], "plaka": "34 ZRL 01", "icra": True, "notlar": ["Avukatta"], "aile": ["Mehmet"]}
        }
    }

if "data" not in st.session_state: st.session_state["data"] = verileri_yukle()
data = st.session_state["data"]

# --- PDF ---
def tr_duzelt(text):
    text = str(text)
    source = "şŞıİğĞüÜöÖçÇ"
    target = "sSiIgGuUoOcC"
    translation = str.maketrans(source, target)
    return text.translate(translation)

def pdf_olustur(daire_no, isim, tutar):
    if not LIB_OK: return None
    pdf = FPDF()
    pdf.add_page()
    pdf.set_line_width(1)
    pdf.rect(5, 5, 200, 287)
    if os.path.exists(LOGO_DOSYA):
        pdf.image(LOGO_DOSYA, 10, 8, 30); pdf.set_xy(40, 20)
    else: pdf.set_xy(10, 20)
    site_adi = tr_duzelt(data['site_adi'].upper())
    isim = tr_duzelt(isim)
    pdf.set_font("Arial", 'B', 24); pdf.cell(0, 10, txt=site_adi, ln=True, align='C')
    pdf.set_y(40); pdf.set_font("Arial", size=10); pdf.cell(0, 5, txt="Yonetim Ofisi: A Blok Zemin Kat", ln=True, align='C'); pdf.ln(10)
    pdf.set_fill_color(200, 220, 255); pdf.set_font("Arial", 'B', 16); pdf.cell(190, 15, txt="TAHSILAT MAKBUZU", ln=True, align='C', fill=True); pdf.ln(10)
    pdf.set_font("Arial", size=14)
    pdf.cell(50, 12, txt="Tarih", border=1); pdf.cell(140, 12, txt=f"{str(datetime.date.today())}", border=1, ln=True)
    pdf.cell(50, 12, txt="Daire No", border=1); pdf.cell(140, 12, txt=f"{str(daire_no)}", border=1, ln=True)
    pdf.cell(50, 12, txt="Sayin", border=1); pdf.cell(140, 12, txt=f"{isim}", border=1, ln=True)
    pdf.cell(50, 12, txt="Tutar", border=1); pdf.cell(140, 12, txt=f"{tutar} TL", border=1, ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- OTURUM ---
if "giris" not in st.session_state: st.session_state["giris"] = False
if "ui_mode" not in st.session_state: st.session_state["ui_mode"] = "login"
if "active_menu" not in st.session_state: st.session_state["active_menu"] = "Genel Bakış"

# --- GİRİŞ EKRANI (SIFIRLAMA DAHİL) ---
if not st.session_state["giris"]:
    st.markdown("""<style>[data-testid="stAppViewContainer"] {
        background-image: linear-gradient(135deg, #f0f2f5 0%, #d9e2ec 100%) !important;
    }</style>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1.4, 1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        
        # MOD 1: GİRİŞ YAP
        if st.session_state["ui_mode"] == "login":
            u = st.text_input("Kullanıcı Kodu", placeholder="Kullanıcı kodunuzu giriniz", key="u_giris")
            p = st.text_input("Şifre", type="password", placeholder="Şifrenizi giriniz", key="p_giris")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("GİRİŞ YAP", type="primary", use_container_width=True):
                user_data = kullanici_dogrula(u, p)
                if user_data:
                    st.session_state["giris"] = True
                    st.session_state["rol"] = str(user_data["rol"])
                    st.session_state["user"] = str(user_data["daire_no"])
                    st.rerun()
                else: st.error("Giriş bilgileri doğrulanamadı.")
            if st.button("🔒 Şifremi Unuttum", type="secondary", use_container_width=True):
                st.session_state["ui_mode"] = "forgot"
                st.rerun()

        # MOD 2: ŞİFRE SIFIRLA
        elif st.session_state["ui_mode"] == "forgot":
            st.markdown("<h4 style='text-align:center; color:#1E293B;'>Şifre Kurtarma</h4>", unsafe_allow_html=True)
            f_u = st.text_input("Kullanıcı Kodu", placeholder="Kullanıcı adınızı giriniz", key="f_u")
            f_k = st.text_input("Güvenlik Kodu", type="password", placeholder="Excel'deki güvenlik kodunuz", key="f_k")
            f_p = st.text_input("Yeni Şifre", type="password", placeholder="Yeni şifrenizi belirleyin", key="f_p")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("EXCEL'DE GÜNCELLE", type="primary", use_container_width=True):
                basari, mesaj = sifre_sifirla_excel(f_u, f_k, f_p)
                if basari:
                    st.success(mesaj); st.session_state["ui_mode"] = "login"; st.rerun()
                else: st.error(mesaj)
            if st.button("⬅️ Giriş Ekranına Dön", type="secondary", use_container_width=True):
                st.session_state["ui_mode"] = "login"
                st.rerun()
            
        st.markdown("<p style='text-align:center; color:#94a3b8; margin-top:20px; font-size:12px; font-weight: 500;'>Zorlu Soft | © 2026 | v70.1</p>", unsafe_allow_html=True)
    st.stop()

def cikis(): st.session_state["giris"] = False; st.rerun()

# ==============================================================================
# ANA YAPI (MENÜ & İÇERİK - GİRİŞ SONRASI)
# ==============================================================================

# Giriş sonrası orta sütun sıfırlama
st.markdown("""
<style>
div[data-testid="column"]:nth-of-type(2) > div > div {
    background: transparent !important;
    padding: 0 !important;
    border: none !important;
    box-shadow: none !important;
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("""
    <div style="padding: 25px 10px 30px 10px; margin-bottom: 15px; text-align: center;">
        <h3 style="color:#1E293B; margin:0; font-size:26px; font-weight:900; letter-spacing:-1px;">KORUPARK</h3>
        <p style="color:#64748b; margin:8px 0 0 0; font-size:13px; font-weight: 600; background: #EBF5FF; color: #0066FF; display: inline-block; padding: 6px 14px; border-radius: 20px; box-shadow: 0 2px 5px rgba(0,102,255,0.1);">Sistem Yöneticisi</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state["rol"] == "admin":
        if st.button("🏠 Genel Bakış", key="nav_genel"): st.session_state["active_menu"] = "Genel Bakış"; st.rerun()
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        st.markdown("<p style='color:#94A3B8; font-size:12px; font-weight:700; margin-left:15px; margin-bottom:8px; letter-spacing:0.5px;'>FİNANSAL İŞLEMLER</p>", unsafe_allow_html=True)
        if st.button("💸 Gider Yönetimi", key="nav_gider"): st.session_state["active_menu"] = "Giderler"; st.rerun()
        if st.button("👥 Hesaplar & Aidat", key="nav_hesap"): st.session_state["active_menu"] = "Hesaplar"; st.rerun()
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        st.markdown("<p style='color:#94A3B8; font-size:12px; font-weight:700; margin-left:15px; margin-bottom:8px; letter-spacing:0.5px;'>YÖNETİM ARAÇLARI</p>", unsafe_allow_html=True)
        if st.button("🏘️ Blok Haritası", key="nav_harita"): st.session_state["active_menu"] = "Harita"; st.rerun()
        if st.button("⚖️ Hukuk & İcra", key="nav_hukuk"): st.session_state["active_menu"] = "Hukuk/İcra"; st.rerun()
        if st.button("☁️ Dijital Arşiv", key="nav_bulut"): st.session_state["active_menu"] = "Bulut Arşiv"; st.rerun()
        if st.button("📄 Raporlar", key="nav_rapor"): st.session_state["active_menu"] = "Raporlar"; st.rerun()
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        if st.button("🚪 Güvenli Çıkış", key="exit"): cikis()

    elif st.session_state["rol"] == "sakin":
        st.markdown("<p style='color:#94A3B8; font-size:12px; font-weight:700; margin-left:15px; margin-bottom:8px;'>DAİRE SAKİNİ MENÜSÜ</p>", unsafe_allow_html=True)
        if st.button("👤 Durum Özeti", key="nav_durum"): st.session_state["active_menu"] = "Durum"; st.rerun()
        if st.button("💳 Ödeme Geçmişi", key="nav_odeme"): st.session_state["active_menu"] = "Ödeme"; st.rerun()
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        if st.button("🚪 Güvenli Çıkış", key="exit_s"): cikis()
    
    st.markdown("<div style='text-align:center; color:#cbd5e1; font-size:11px; margin-top:40px; font-weight: 500;'>Zorlu Soft | v70.1</div>", unsafe_allow_html=True)

# --- SAĞ İÇERİK ---
menu = st.session_state["active_menu"]
st.markdown(f"""<h1 style='font-weight: 800; color: #1E293B; margin-bottom: 25px;'>{menu}</h1>""", unsafe_allow_html=True)

if st.session_state["rol"] == "admin":
    if menu == "Genel Bakış":
        st.markdown("<p style='color:#64748b; font-size:15px; margin-bottom:30px;'>Sitenin finansal ve operasyonel durumunun anlık özeti.</p>", unsafe_allow_html=True)
        toplam_alacak = sum(d['borc'] for d in data['daireler'].values())
        daire_sayisi = len(data["daireler"])
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"<div class='metric-card'><h3>GÜNCEL KASA</h3><h1 style='color:#0066FF'>{data['kasa_nakit']:,.0f} ₺</h1></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><h3>TOPLAM ALACAK</h3><h1 style='color:#FF3B30'>{toplam_alacak:,.0f} ₺</h1></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-card'><h3>TOPLAM GİDER</h3><h1 style='color:#FF9500'>{sum(g['tutar'] for g in data['giderler']):,.0f} ₺</h1></div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='metric-card'><h3>DAİRE SAYISI</h3><h1 style='color:#1E293B'>{daire_sayisi}</h1></div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        cl, cr = st.columns([2, 1])
        with cl:
            st.subheader("Finansal Dağılım")
            df_pie = pd.DataFrame({"Durum": ["Kasa", "Alacak", "Gider"], "Tutar": [data['kasa_nakit'], toplam_alacak, sum(g['tutar'] for g in data['giderler'])]})
            fig = px.pie(df_pie, values='Tutar', names='Durum', hole=0.75, color_discrete_sequence=["#0066FF", "#FF3B30", "#FF9500"])
            fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), paper_bgcolor='rgba(0,0,0,0)', font=dict(family="Poppins"))
            st.plotly_chart(fig, use_container_width=True)
        with cr:
            st.subheader("Veri Güvenliği")
            if st.button("💾 VERİLERİ ŞİMDİ YEDEKLE", type="primary", use_container_width=True): 
                kaydet(data); st.success("Veriler Excel'e yedeklendi.")

    elif menu == "Giderler":
        st.markdown("<p style='color:#64748b; font-size:15px; margin-bottom:30px;'>Site giderlerinin girişi ve takibi.</p>", unsafe_allow_html=True)
        c1, c2 = st.columns([1,2])
        with c1:
            st.subheader("Yeni Gider Ekle")
            with st.form("gider"):
                gt = st.selectbox("Gider Türü", ["Enerji", "Personel", "Bakım", "Demirbaş", "Diğer"])
                ga = st.text_input("Açıklama"); gm = st.number_input("Tutar", min_value=0.0)
                if st.form_submit_button("Kaydet", type="primary"):
                    data["giderler"].append({"tarih": str(datetime.date.today()), "tur": gt, "aciklama": ga, "tutar": gm})
                    data["kasa_nakit"] -= gm; kaydet(data); st.rerun()
        with c2: st.dataframe(pd.DataFrame(data["giderler"]), use_container_width=True, hide_index=True)

    elif menu == "Hesaplar":
        st.markdown("<p style='color:#64748b; font-size:15px; margin-bottom:30px;'>Daire bazlı borç, alacak ve aidat takibi.</p>", unsafe_allow_html=True)
        src = st.text_input("🔍 Daire Ara", placeholder="İsim veya Numara")
        filtre = None
        if src:
            for k,v in data["daireler"].items():
                if src.lower() in v["sahip"].lower() or src == k: filtre = k; break
        secilen = filtre if filtre else st.selectbox("Daire Seçiniz", list(data["daireler"].keys()))
        info = data["daireler"][secilen]
        st.markdown(f"<div class='metric-card' style='border-left: 8px solid {'#FF3B30' if info['borc'] > 0 else '#0066FF'};'><h3>{secilen} - {info['sahip']}</h3><h1>{info['borc']:,.2f} ₺</h1></div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2 = st.columns([2,1])
        with c1:
            st.subheader("İşlem Geçmişi")
            if info["gecmis"]:
                st.dataframe(pd.DataFrame(info["gecmis"]), use_container_width=True, hide_index=True)
            else: st.info("Haraket bulunmuyor.")
        with c2:
            st.subheader("Ödeme Al")
            t = st.number_input("Tutar", min_value=0.0)
            if st.button("Onayla", type="primary", use_container_width=True):
                info["borc"] -= t; data["kasa_nakit"] += t; info["gecmis"].append(f"{datetime.date.today()} | Tahsilat: {t}"); kaydet(data); st.rerun()
            pdf = pdf_olustur(secilen, info["sahip"], t if t > 0 else info["borc"])
            if pdf: st.download_button("📄 PDF Makbuz", pdf, f"makbuz_{secilen}.pdf", "application/pdf", use_container_width=True)

    elif menu == "Harita":
        cols = st.columns(4)
        for i, (no, info) in enumerate(sorted(data["daireler"].items())):
            with cols[i % 4]:
                color = "#FF3B30" if info["borc"] > 0 else "#0066FF"
                st.markdown(f"<div class='metric-card' style='border-top: 6px solid {color};'><h3>DAİRE {no}</h3><h2>{info['sahip']}</h2><h1>{info['borc']:,.0f} ₺</h1></div><br>", unsafe_allow_html=True)

    elif menu == "Hukuk/İcra":
        icraliklar = [v for v in data["daireler"].values() if v["icra"]]
        if icraliklar: st.dataframe(pd.DataFrame(icraliklar), use_container_width=True)
        else: st.success("İcralık daire bulunmuyor.")

    elif menu == "Bulut Arşiv":
        st.file_uploader("Dosyaları Sürükleyin", accept_multiple_files=True)

    elif menu == "Raporlar":
        st.dataframe(pd.DataFrame.from_dict(data["daireler"], orient='index'), use_container_width=True)

# SAKİN EKRANI
elif st.session_state["rol"] == "sakin":
    no = st.session_state["user"]; info = data["daireler"][no]
    if menu == "Durum":
        st.title(f"Sayın {info['sahip']}")
        st.markdown(f"<div class='metric-card'><h3>BORCUNUZ</h3><h1>{info['borc']:,.2f} ₺</h1></div>", unsafe_allow_html=True)
    elif menu == "Ödeme":
        st.dataframe(pd.DataFrame(info["gecmis"]), use_container_width=True)

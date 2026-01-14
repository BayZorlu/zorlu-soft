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

# --- CSS: MAVİ TEMA VE TASARIM ---
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
    footer, 
    #MainMenu {
        display: none !important;
    }
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 0px !important;
        visibility: hidden !important;
    }

    /* 2. DOSYA YÜKLEME ALANI */
    [data-testid="stFileUploaderDropzone"] div div::before {
        content: "Dosyaları buraya sürükleyin veya seçin";
        visibility: visible;
        font-weight: 600;
        color: #1E293B;
    }
    [data-testid="stFileUploaderDropzone"] div div { visibility: hidden; }
    [data-testid="stFileUploaderDropzone"] div div svg { visibility: visible !important; }

    /* 3. INPUT KUTULARI (MAVİ ODAK) */
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
        box-shadow: 0 2px 5px rgba(0,0,0,0.02) !important;
        transition: all 0.3s;
    }
    
    .stTextInput input:focus {
        border-color: #0066FF !important; /* MAVİ ÇİZGİ */
        box-shadow: 0 0 0 3px rgba(0, 102, 255, 0.15) !important; /* MAVİ HALO */
        outline: none !important;
    }

    /* 4. ARKA PLAN */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(to bottom, #F8F9FC 0%, #E2E8F0 100%) !important;
        background-image: none !important;
    }
    .block-container {
        padding-top: 35px !important;
        padding-bottom: 35px !important;
    }

    /* 5. SOL MENÜ */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        box-shadow: 4px 0 15px -5px rgba(0,0,0,0.05);
        border-right: none !important;
    }
    [data-testid="stSidebarCollapseButton"] { display: none !important; }

    /* MENÜ BUTONLARI */
    [data-testid="stSidebar"] .stButton button {
        width: 100%;
        background-color: transparent !important;
        border: none !important;
        color: #64748b !important;
        text-align: left;
        padding: 14px 20px;
        font-size: 15px;
        font-weight: 500;
        margin: 5px 0 !important;
        border-radius: 14px !important;
        display: flex;
        align-items: center;
        transition: all 0.3s;
    }
    [data-testid="stSidebar"] .stButton button span {
        filter: grayscale(100%) opacity(0.6); 
        margin-right: 14px;
        font-size: 19px;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background-color: #F8FAFC !important;
        color: #0F172A !important;
        transform: translateX(5px);
    }
    [data-testid="stSidebar"] .stButton button:focus {
        background-color: #EBF5FF !important;
        color: #0066FF !important;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(0, 102, 255, 0.1) !important;
    }
    [data-testid="stSidebar"] .stButton button:focus span {
        filter: none !important;
    }

    /* 6. GİRİŞ KUTUSU */
    .login-container {
        background: #FFFFFF;
        padding: 50px;
        border-radius: 28px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.1);
        text-align: center;
        margin-top: 80px;
        border: 1px solid rgba(255,255,255,0.5);
    }

    /* 7. BUTON STİLLERİ (MAVİ) */
    
    /* GİRİŞ BUTONU (PRIMARY) */
    div.stButton > button[type="primary"] {
        background: linear-gradient(135deg, #0066FF 0%, #0047AB 100%) !important; /* MAVİ GRADIENT */
        border-radius: 14px !important;
        padding: 16px 24px !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        letter-spacing: 0.5px;
        border: none !important;
        color: white !important;
        box-shadow: 0 10px 20px -10px rgba(0, 102, 255, 0.4);
        transition: all 0.3s;
    }
    div.stButton > button[type="primary"]:hover {
         background: linear-gradient(135deg, #0052CC 0%, #003380 100%) !important;
         box-shadow: 0 15px 30px -12px rgba(0, 102, 255, 0.5);
         transform: translateY(-2px);
    }

    /* ŞİFREMİ UNUTTUM BUTONU (SECONDARY - SADE) */
    div.stButton > button[type="secondary"] {
        background-color: transparent !important;
        border: none !important;
        color: #64748b !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        text-decoration: none !important;
        margin-top: -10px !important;
        padding: 0 !important;
    }
    div.stButton > button[type="secondary"]:hover {
        color: #0066FF !important;
        background-color: transparent !important;
        text-decoration: underline !important;
    }

    /* 8. KARTLAR */
    .metric-card {
        background: #FFFFFF;
        padding: 28px;
        border-radius: 20px;
        box-shadow: 0 10px 20px -10px rgba(0,0,0,0.05);
        border: 1px solid #F1F5F9;
        text-align: left;
        transition: all 0.3s;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 30px -15px rgba(0,0,0,0.1);
        border-color: #E2E8F0;
    }
    .metric-card h3 { 
        color: #94A3B8; 
        font-size: 13px; 
        text-transform: uppercase; 
        letter-spacing: 1.2px; 
        font-weight: 700; 
        margin-bottom: 12px; 
    }
    .metric-card h1 { 
        color: #1E293B; 
        font-size: 34px; 
        font-weight: 800; 
        margin: 0;
        letter-spacing: -1px;
    }
    
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
if "active_menu" not in st.session_state: st.session_state["active_menu"] = "Genel Bakış"

# --- GİRİŞ EKRANI ---
if not st.session_state["giris"]:
    st.markdown("""<style>[data-testid="stAppViewContainer"] {
        background-image: linear-gradient(135deg, #f0f2f5 0%, #d9e2ec 100%) !important;
    }</style>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1.4, 1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        # Giriş Kutuları
        st.text_input("Kullanıcı Kodu", placeholder="Kullanıcı kodunuzu giriniz", key="u_giris")
        st.text_input("Şifre", type="password", placeholder="Şifrenizi giriniz", key="p_giris")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # GİRİŞ YAP BUTONU (MAVİ)
        if st.button("GİRİŞ YAP", type="primary", use_container_width=True):
            u = st.session_state.u_giris
            p = st.session_state.p_giris
            user_data = kullanici_dogrula(u, p)
            if user_data:
                st.session_state["giris"] = True
                st.session_state["rol"] = str(user_data["rol"])
                st.session_state["user"] = str(user_data["daire_no"])
                st.rerun()
            else: st.error("Giriş bilgileri doğrulanamadı.")
        
        # ŞİFREMİ UNUTTUM (BUTON GÖRÜNÜMLÜ LİNK)
        # Secondary type butonu CSS ile link gibi gösteriyoruz
        if st.button("🔒 Şifremi Unuttum", type="secondary", use_container_width=True):
            st.toast("Lütfen güvenlik için site yönetimi ile iletişime geçiniz.", icon="ℹ️")
            
        st.markdown("<p style='text-align:center; color:#94a3b8; margin-top:20px; font-size:12px; font-weight: 500;'>Zorlu Soft | © 2026 | v69.0</p>", unsafe_allow_html=True)
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
    
    st.markdown("<div style='text-align:center; color:#cbd5e1; font-size:11px; margin-top:40px; font-weight: 500;'>Zorlu Soft | Sürüm 69.0</div>", unsafe_allow_html=True)

# --- SAĞ İÇERİK ---
menu = st.session_state["active_menu"]

st.markdown(f"""<h1 style='font-weight: 800; color: #1E293B; margin-bottom: 25px;'>{menu}</h1>""", unsafe_allow_html=True)

if st.session_state["rol"] == "admin":
    if menu == "Genel Bakış":
        st.markdown("<p class='page-subtitle'>Sitenin finansal ve operasyonel durumunun anlık özeti.</p>", unsafe_allow_html=True)
        
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
            df_pie = pd.DataFrame({
                "Durum": ["Kasa Mevudu", "Alacaklar (Borçlu)", "Toplam Giderler"],
                "Tutar": [data['kasa_nakit'], toplam_alacak, sum(g['tutar'] for g in data['giderler'])]
            })
            fig = px.pie(df_pie, values='Tutar', names='Durum', hole=0.75, color_discrete_sequence=["#0066FF", "#FF3B30", "#FF9500"])
            fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family="Poppins"))
            st.plotly_chart(fig, use_container_width=True)
        with cr:
            st.subheader("Veri Güvenliği")
            st.markdown("<div style='background: white; padding: 25px; border-radius: 20px; border: 1px solid #EFF2F7; box-shadow: 0 10px 20px -10px rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
            st.write("Sistem verileri düzenli olarak otomatik yedeklenmektedir. Manuel yedek almak için aşağıdaki butonu kullanabilirsiniz.")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 VERİLERİ GÜVENLE KAYDET", type="primary", use_container_width=True): 
                kaydet(data); st.success("Tüm veriler başarıyla yedeklendi.")
            st.markdown("</div>", unsafe_allow_html=True)

    elif menu == "Giderler":
        st.markdown("<p class='page-subtitle'>Site giderlerinin girişi ve takibi.</p>", unsafe_allow_html=True)
        c1, c2 = st.columns([1,2])
        with c1:
            st.markdown("<div style='background: white; padding: 30px; border-radius: 20px; border: 1px solid #EFF2F7; box-shadow: 0 10px 20px -10px rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
            st.subheader("Yeni Gider Ekle")
            with st.form("gider"):
                gt = st.selectbox("Gider Türü", ["Enerji (Elk/Su/Gaz)", "Personel Maaş/SGK", "Bakım & Onarım", "Demirbaş Alımı", "Diğer"]); 
                ga = st.text_input("Açıklama (Örn: Ocak Ayı Faturası)"); 
                gm = st.number_input("Tutar (TL)", min_value=0.0, format="%.2f")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("Gideri Kaydet", use_container_width=True, type="primary"):
                    data["giderler"].append({"tarih":str(datetime.date.today()),"tur":gt,"aciklama":ga,"tutar":gm})
                    data["kasa_nakit"] -= gm; kaydet(data); st.success("Gider başarıyla işlendi."); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with c2: 
            st.subheader("Gider Geçmişi")
            st.dataframe(pd.DataFrame(data["giderler"]), use_container_width=True, hide_index=True)

    elif menu == "Hesaplar":
        st.markdown("<p class='page-subtitle'>Daire bazlı borç, alacak ve aidat takibi.</p>", unsafe_allow_html=True)
        src = st.text_input("🔍 Daire Ara (İsim veya Numara)", placeholder="Örn: Ahmet veya 1")
        filtre = None
        if src:
            for k,v in data["daireler"].items():
                if src.lower() in v["sahip"].lower() or src == k: 
                    filtre = k
                    break
        secilen = filtre if filtre else st.selectbox("Daire Seçiniz", list(data["daireler"].keys()))
        info = data["daireler"][secilen]
        
        st.markdown(f"""
        <div class='metric-card' style='border-left: 8px solid {"#FF3B30" if info["borc"] > 0 else "#0066FF"}; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 15px 30px -10px rgba(0,0,0,0.1);'>
            <div>
                <h3 style='letter-spacing: 2px;'>DAİRE NO: {secilen}</h3>
                <h1 style='font-size: 40px; margin-top: 10px;'>{info['sahip']}</h1>
            </div>
            <div style='text-align: right;'>
                 <h3 style='letter-spacing: 2px;'>GÜNCEL BORÇ</h3>
                 <h1 style='color: {"#FF3B30" if info["borc"] > 0 else "#0066FF"}; font-size: 48px; margin-top: 10px;'>{info['borc']:,.2f} ₺</h1>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2 = st.columns([2,1])
        with c1:
            st.subheader("Hesap Hareketleri")
            if info["gecmis"]:
                temiz = [x.split("|") if "|" in x else ["-", x] for x in reversed(info["gecmis"])]
                df_gecmis = pd.DataFrame(temiz, columns=["Tarih", "İşlem Açıklaması"])
                st.dataframe(df_gecmis, use_container_width=True, hide_index=True)
            else:
                 st.info("Henüz bir hesap hareketi bulunmuyor.")
        with c2:
            st.markdown("<div style='background: white; padding: 30px; border-radius: 20px; border: 1px solid #EFF2F7; box-shadow: 0 10px 20px -10px rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
            st.subheader("Tahsilat İşlemi")
            t = st.number_input("Tahsil Edilen Tutar (TL)", min_value=0.0, format="%.2f"); 
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Ödemeyi Onayla", use_container_width=True, type="primary"): 
                info["borc"]-=t; data["kasa_nakit"]+=t; info["gecmis"].append(f"{datetime.date.today()} | Ödeme: {t:,.2f} TL"); kaydet(data); st.success("Ödeme alındı."); st.rerun()
            
            st.markdown("---")
            st.subheader("Makbuz")
            pdf_data = pdf_olustur(secilen, info["sahip"], t if t > 0 else info["borc"])
            if pdf_data: st.download_button("📄 PDF Makbuz İndir", pdf_data, f"makbuz_{secilen}.pdf", "application/pdf", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    elif menu == "Harita":
        st.markdown("<p class='page-subtitle'>Tüm dairelerin borç durumunun görsel özeti.</p>", unsafe_allow_html=True)
        cols = st.columns(4)
        for i, (no, info) in enumerate(sorted(data["daireler"].items())):
            with cols[i % 4]:
                color = "#FF3B30" if info["borc"] > 0 else "#0066FF" 
                st.markdown(f"""
                <div class='metric-card' style='border-top: 8px solid {color}; padding: 25px; min-height: 160px;'>
                    <h3 style='margin-bottom: 5px; letter-spacing: 1px;'>DAİRE {no} - BLOK {info['blok']}</h3>
                    <h2 style='font-size: 22px; margin: 0 0 15px 0; font-weight: 700;'>{info['sahip']}</h2>
                    <h3 style='margin-bottom: 0;'>BORÇ DURUMU</h3>
                    <h1 style='color: {color}; font-size: 30px; margin-top: 5px;'>{info['borc']:,.0f} ₺</h1>
                </div>
                <br>
                """, unsafe_allow_html=True)
    
    elif menu == "Hukuk/İcra":
        st.markdown("<p class='page-subtitle'>Yasal süreçteki dairelerin listesi.</p>", unsafe_allow_html=True)
        st.warning("⚠️ Aşağıdaki daireler icra takibindedir veya hukuki süreç başlatılmıştır.")
        icraliklar = [v for v in data["daireler"].values() if v["icra"]]
        if icraliklar:
             st.dataframe(pd.DataFrame(icraliklar), use_container_width=True)
        else:
             st.success("İcralık daire bulunmamaktadır.")

    elif menu == "Bulut Arşiv":
        st.markdown("<p class='page-subtitle'>Site evraklarının bulut depolama alanı.</p>", unsafe_allow_html=True)
        st.info("☁️ Siteye ait önemli evrakları (Proje, Karar Defteri vb.) buradan yükleyip saklayabilirsiniz. (Demo Modu)")
        st.file_uploader("Dosyaları Buraya Sürükleyin", accept_multiple_files=True)

    elif menu == "Raporlar": 
        st.markdown("<p class='page-subtitle'>Tüm sistem verilerinin ham listesi.</p>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame.from_dict(data["daireler"], orient='index'), use_container_width=True)

# SAKİN
elif st.session_state["rol"] == "sakin":
    no = st.session_state["user"]; info = data["daireler"][no]
    if menu == "Durum": 
        st.title(f"Hoş Geldiniz, {info['sahip']}")
        st.markdown("<p class='page-subtitle'>Dairenizin güncel durum özeti.</p>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.markdown(f"<div class='metric-card'><h3>GÜNCEL BORCUNUZ</h3><h1 style='color: {'#FF3B30' if info['borc']>0 else '#0066FF'}'>{info['borc']:,.2f} ₺</h1></div>", unsafe_allow_html=True)
        
    elif menu == "Ödeme": 
        st.title("Ödeme ve Hesap Geçmişi")
        st.markdown("<p class='page-subtitle'>Yaptığınız tüm ödemeler ve aidat tahakkukları.</p>", unsafe_allow_html=True)
        temiz = [x.split("|") if "|" in x else ["-", x] for x in reversed(info["gecmis"])]; 
        st.dataframe(pd.DataFrame(temiz, columns=["Tarih","İşlem"]), use_container_width=True, hide_index=True)

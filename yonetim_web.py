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

# --- CSS: ULTRA-PREMIUM CİLALAMA ---
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap" rel="stylesheet">

<style>
    /* GENEL TİPOGRAFİ */
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }

    /* 1. GEREKSİZLERİ GİZLE */
    .stDeployButton, [data-testid="stHeaderActionElements"], footer, #MainMenu {
        display: none !important;
    }
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 0px !important;
        visibility: hidden !important;
    }

    /* 2. ARKA PLAN (YENİ: DERİNLİKLİ GEÇİŞ) */
    [data-testid="stAppViewContainer"] {
        /* Dümdüz renk yerine çok hafif bir yukarıdan aşağıya geçiş */
        background: linear-gradient(to bottom, #F8F9FC 0%, #F1F5F9 100%) !important;
        background-image: none !important;
    }
    .block-container {
        padding-top: 35px !important;
        padding-bottom: 35px !important;
    }

    /* 3. SOL MENÜ (YENİ: YÜZEN EFEKT) */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        /* Sert çizgi yerine yumuşak gölge ile ayırma */
        border-right: none !important;
        box-shadow: 4px 0 15px -5px rgba(0,0,0,0.05); /* Sağ tarafa hafif gölge */
        z-index: 100; /* İçeriğin üstünde dursun */
    }
    [data-testid="stSidebarCollapseButton"] { display: none !important; }

    /* 4. MENÜ BUTONLARI */
    [data-testid="stSidebar"] .stButton button {
        width: 100%;
        background-color: transparent !important;
        border: none !important;
        color: #64748b !important;
        text-align: left;
        padding: 14px 20px;
        font-size: 15px;
        font-weight: 500;
        margin: 5px 0 !important; /* Biraz daha boşluk */
        border-radius: 14px !important; /* Daha da yuvarlak */
        display: flex;
        align-items: center;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    [data-testid="stSidebar"] .stButton button span {
        filter: grayscale(100%) opacity(0.6); 
        margin-right: 14px;
        font-size: 19px;
    }

    [data-testid="stSidebar"] .stButton button:hover {
        background-color: #F8FAFC !important;
        color: #0F172A !important;
        transform: translateX(6px);
    }

    /* AKTİF BUTON */
    [data-testid="stSidebar"] .stButton button:focus {
        background-color: #EBF5FF !important;
        color: #0066FF !important;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(0, 102, 255, 0.1) !important; /* Hafif mavi gölge */
    }
    [data-testid="stSidebar"] .stButton button:focus span {
        filter: none !important;
    }

    /* 5. GİRİŞ KUTUSU */
    .login-container {
        background: #FFFFFF;
        padding: 50px;
        border-radius: 28px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.1); /* Daha derin gölge */
        text-align: center;
        margin-top: 70px;
        border: 1px solid rgba(255,255,255,0.5); /* Çok ince beyaz çerçeve */
    }

    /* 6. GİRDİLER VE BUTONLAR */
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        border-radius: 14px !important;
        padding: 14px 16px !important;
        border: 1px solid #E2E8F0 !important;
        background-color: #FFFFFF !important;
        color: #1E293B !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02) !important;
        transition: all 0.3s;
    }
    .stTextInput input:focus, .stNumberInput input:focus, .stSelectbox select:focus {
        border-color: #0066FF !important;
        box-shadow: 0 0 0 4px rgba(0, 102, 255, 0.1) !important; /* Daha geniş focus halkası */
    }
    
    div.stButton > button[type="primary"] {
        background: linear-gradient(135deg, #0066FF 0%, #0052CC 100%) !important;
        border-radius: 14px !important;
        padding: 16px 24px !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        letter-spacing: 0.5px;
        border: none;
        box-shadow: 0 10px 20px -10px rgba(0, 102, 255, 0.5);
        transition: all 0.3s;
    }
    div.stButton > button[type="primary"]:hover {
         box-shadow: 0 15px 30px -12px rgba(0, 102, 255, 0.6);
         transform: translateY(-3px);
    }

    /* 7. KARTLAR (YENİ: GELİŞMİŞ HOVER EFEKTİ) */
    .metric-card {
        background: #FFFFFF;
        padding: 28px;
        border-radius: 20px;
        box-shadow: 0 10px 20px -10px rgba(0,0,0,0.05); /* Başlangıçta yumuşak gölge */
        border: 1px solid #F1F5F9;
        text-align: left;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        position: relative;
        overflow: hidden;
    }
    /* Kartın üzerine gelince */
    .metric-card:hover {
        transform: translateY(-7px); /* Biraz daha yukarı */
        box-shadow: 0 20px 30px -15px rgba(0,0,0,0.1); /* Gölge belirginleşir ve yayılır */
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
    
    /* 8. BAŞLIKLAR VE ALTYAZILAR */
    h1 {
        font-weight: 800 !important; 
        color: #1E293B !important; 
        margin-bottom: 10px !important;
        font-size: 32px !important;
    }
    .page-subtitle {
        color: #64748b;
        font-size: 15px;
        margin-bottom: 30px;
        font-weight: 400;
    }
    
    /* 9. TABLOLAR */
    [data-testid="stDataFrame"] {
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid #E2E8F0;
        box-shadow: 0 10px 20px -10px rgba(0,0,0,0.05);
    }

    /* 10. ÖZEL KAYDIRMA ÇUBUKLARI (WEBKIT) */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    ::-webkit-scrollbar-track {
        background: #f1f5f9;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 10px;
        border: 2px solid #f1f5f9; /* Kenarlardan boşluk bırak */
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #94a3b8;
    }

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

# --- GİRİŞ EKRANI (PREMIUM) ---
if not st.session_state["giris"]:
    st.markdown("""<style>[data-testid="stAppViewContainer"] {
        background-image: linear-gradient(135deg, #f0f2f5 0%, #d9e2ec 100%) !important;
    }</style>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1.4, 1])
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""<div class="login-container">""", unsafe_allow_html=True)
        
        st.markdown("""
            <div style="margin-bottom: 30px;">
                <span style='font-size: 60px; filter: drop-shadow(0 10px 10px rgba(0,0,0,0.1));'>🏢</span>
                <h2 style='color:#1e293b; font-weight:900; margin-top:15px; font-size: 32px; letter-spacing:-1px;'>KORUPARK</h2>
                <p style='color:#64748b; font-weight:500; font-size:16px;'>Profesyonel Site Yönetim Paneli</p>
            </div>
        """, unsafe_allow_html=True)

        u = st.text_input("Kullanıcı Kodu", placeholder="Yönetici veya Daire Kodu")
        p = st.text_input("Şifre", type="password", placeholder="••••••••")
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("GÜVENLİ GİRİŞ YAP", type="primary", use_container_width=True):
            user_data = kullanici_dogrula(u, p)
            if user_data:
                st.session_state["giris"] = True
                st.session_state["rol"] = str(user_data["rol"])
                st.session_state["user"] = str(user_data["daire_no"])
                st.rerun()
            else: st.error("Giriş bilgileri doğrulanamadı.")
            
        st.markdown("""</div>""", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#64748b; margin-top:30px; font-size:13px; font-weight: 600; opacity: 0.7;'>Zorlu Soft | © 2026 | Premium Edition v62.0</p>", unsafe_allow_html=True)
    st.stop()

def cikis(): st.session_state["giris"] = False; st.rerun()

# ==============================================================================
# ANA YAPI (PREMIUM MENÜ & İÇERİK)
# ==============================================================================

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
    
    st.markdown("<div style='text-align:center; color:#cbd5e1; font-size:11px; margin-top:40px; font-weight: 500;'>Zorlu Soft Premium v62.0</div>", unsafe_allow_html=True)

# --- SAĞ İÇERİK ---
menu = st.session_state["active_menu"]

if st.session_state["rol"] == "admin":
    if menu == "Genel Bakış":
        # Başlık ve Alt Başlık
        st.title(menu)
        st.markdown("<p class='page-subtitle'>Sitenin finansal ve operasyonel durumunun anlık özeti.</p>", unsafe_allow_html=True)
        
        toplam_alacak = sum(d['borc'] for d in data['daireler'].values())
        daire_sayisi = len(data["daireler"])
        
        # KARTLAR
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
            # Grafiğin arka planını şeffaf yap ki yeni degrade arka planla uyumlu olsun
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
        st.title(menu)
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
        st.title(menu)
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
        
        # Seçili Daire Kartı (Premium)
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
        st.title("Blok Haritası")
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
        st.title("Hukuk & İcra Takibi")
        st.markdown("<p class='page-subtitle'>Yasal süreçteki dairelerin listesi.</p>", unsafe_allow_html=True)
        st.warning("⚠️ Aşağıdaki daireler icra takibindedir veya hukuki süreç başlatılmıştır.")
        icraliklar = [v for v in data["daireler"].values() if v["icra"]]
        if icraliklar:
             st.dataframe(pd.DataFrame(icraliklar), use_container_width=True)
        else:
             st.success("İcralık daire bulunmamaktadır.")

    elif menu == "Bulut Arşiv":
        st.title("Dijital Arşiv")
        st.markdown("<p class='page-subtitle'>Site evraklarının bulut depolama alanı.</p>", unsafe_allow_html=True)
        st.info("☁️ Siteye ait önemli evrakları (Proje, Karar Defteri vb.) buradan yükleyip saklayabilirsiniz. (Demo)")
        st.file_uploader("Dosya Seçiniz", accept_multiple_files=True)

    elif menu == "Raporlar": 
        st.title("Detaylı Raporlar")
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

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

# --- CSS: PREMIUM GÜZELLEŞTİRME ---
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">

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

    /* 2. ARKA PLAN VE ANA YAPI */
    [data-testid="stAppViewContainer"] {
        background-color: #F8F9FC !important; /* Çok açık gri/mavi arka plan */
        background-image: none !important;
    }
    .block-container {
        padding-top: 30px !important;
        padding-bottom: 30px !important;
    }

    /* 3. SOL MENÜ (Modern Beyaz) */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #EFF2F7;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    [data-testid="stSidebarCollapseButton"] { display: none !important; }

    /* 4. MENÜ BUTONLARI (Daha şık) */
    [data-testid="stSidebar"] .stButton button {
        width: 100%;
        background-color: transparent !important;
        border: none !important;
        color: #64748b !important;
        text-align: left;
        padding: 14px 20px;
        font-size: 15px;
        font-weight: 500;
        margin: 4px 0 !important;
        border-radius: 12px !important; /* Daha yuvarlak */
        display: flex;
        align-items: center;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); /* Akıcı geçiş */
    }
    
    [data-testid="stSidebar"] .stButton button span {
        filter: grayscale(100%) opacity(0.6); 
        margin-right: 12px;
        font-size: 18px;
    }

    [data-testid="stSidebar"] .stButton button:hover {
        background-color: #F1F5F9 !important;
        color: #0F172A !important;
        transform: translateX(5px); /* Hafif sağa kayma efekti */
    }

    /* AKTİF BUTON */
    [data-testid="stSidebar"] .stButton button:focus {
        background-color: #EBF5FF !important; /* Çok açık mavi */
        color: #0066FF !important; /* Canlı mavi yazı */
        font-weight: 600;
        box-shadow: none !important;
    }
    [data-testid="stSidebar"] .stButton button:focus span {
        filter: none !important; /* Rengi geri getir */
    }

    /* 5. GİRİŞ KUTUSU (Daha Premium) */
    .login-container {
        background: #FFFFFF;
        padding: 50px;
        border-radius: 24px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.08);
        text-align: center;
        margin-top: 60px;
        border: 1px solid #EFF2F7;
    }

    /* 6. GİRİŞ ALANLARI VE BUTONLAR (Genel Stil) */
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        border-radius: 12px !important;
        padding: 12px 15px !important;
        border: 1px solid #E2E8F0 !important;
        background-color: #FFFFFF !important;
        color: #1E293B !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
        transition: all 0.3s;
    }
    .stTextInput input:focus, .stNumberInput input:focus, .stSelectbox select:focus {
        border-color: #0066FF !important; /* Odaklanınca mavi */
        box-shadow: 0 0 0 3px rgba(0, 102, 255, 0.15) !important;
    }
    
    /* Primary Buton (Giriş, Kaydet vb.) */
    div.stButton > button[type="primary"] {
        background: linear-gradient(135deg, #0066FF 0%, #0052CC 100%) !important;
        border-radius: 12px !important;
        padding: 14px 20px !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px;
        border: none;
        box-shadow: 0 4px 12px rgba(0, 102, 255, 0.2);
        transition: all 0.3s;
    }
    div.stButton > button[type="primary"]:hover {
         box-shadow: 0 8px 16px rgba(0, 102, 255, 0.3);
         transform: translateY(-2px);
    }

    /* 7. KARTLAR (Dashboard Kartları - Modernize Edildi) */
    .metric-card {
        background: #FFFFFF;
        padding: 25px;
        border-radius: 16px;
        box-shadow: 0 6px 15px rgba(0,0,0,0.05);
        border: 1px solid #EFF2F7;
        text-align: left;
        transition: transform 0.3s;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .metric-card:hover {
        transform: translateY(-5px); /* Kartlar üzerine gelince yükselir */
        box-shadow: 0 12px 25px rgba(0,0,0,0.08);
    }
    .metric-card h3 { 
        color: #94A3B8; 
        font-size: 13px; 
        text-transform: uppercase; 
        letter-spacing: 1px; 
        font-weight: 600; 
        margin-bottom: 10px; 
    }
    .metric-card h1 { 
        color: #1E293B; 
        font-size: 32px; 
        font-weight: 800; 
        margin: 0;
        letter-spacing: -1px;
    }
    
    /* Başlıklar */
    h1, h2, h3 {
        color: #1E293B !important;
    }
    
    /* Tablo/Dataframe Güzelleştirme */
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }

    .sidebar-divider {
        margin: 15px 0;
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
    # Arka plana hafif bir görsel veya degrade ekleyelim (CSS ile ezmiştik, şimdi özel bir giriş için açıyoruz)
    st.markdown("""<style>[data-testid="stAppViewContainer"] {
        background-image: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
    }</style>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1.4, 1])
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""<div class="login-container">""", unsafe_allow_html=True)
        
        # Şık bir ikon ve başlık
        st.markdown("""
            <div style="margin-bottom: 25px;">
                <span style='font-size: 50px;'>🏢</span>
                <h2 style='color:#1e293b; font-weight:800; margin-top:10px; font-size: 28px;'>KORUPARK</h2>
                <p style='color:#64748b; font-weight:500;'>Profesyonel Site Yönetim Paneli</p>
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
        st.markdown("<p style='text-align:center; color:#64748b; margin-top:30px; font-size:13px; font-weight: 600; opacity: 0.7;'>Zorlu Soft | © 2026 | Premium Edition v61.0</p>", unsafe_allow_html=True)
    st.stop()

def cikis(): st.session_state["giris"] = False; st.rerun()

# ==============================================================================
# ANA YAPI (PREMIUM MENÜ & İÇERİK)
# ==============================================================================

with st.sidebar:
    st.markdown("""
    <div style="padding: 20px 10px 25px 10px; margin-bottom: 15px; text-align: center;">
        <h3 style="color:#1E293B; margin:0; font-size:24px; font-weight:900; letter-spacing:-0.5px;">KORUPARK</h3>
        <p style="color:#64748b; margin:5px 0 0 0; font-size:13px; font-weight: 600; background: #EBF5FF; color: #0066FF; display: inline-block; padding: 4px 12px; border-radius: 20px;">Sistem Yöneticisi</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state["rol"] == "admin":
        if st.button("🏠 Genel Bakış", key="nav_genel"): st.session_state["active_menu"] = "Genel Bakış"; st.rerun()
        
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        
        st.markdown("<p style='color:#94A3B8; font-size:12px; font-weight:600; margin-left:15px; margin-bottom:5px;'>FİNANS</p>", unsafe_allow_html=True)
        if st.button("💸 Gider Yönetimi", key="nav_gider"): st.session_state["active_menu"] = "Giderler"; st.rerun()
        if st.button("👥 Hesaplar & Aidat", key="nav_hesap"): st.session_state["active_menu"] = "Hesaplar"; st.rerun()
        
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        
        st.markdown("<p style='color:#94A3B8; font-size:12px; font-weight:600; margin-left:15px; margin-bottom:5px;'>YÖNETİM</p>", unsafe_allow_html=True)
        if st.button("🏘️ Blok Haritası", key="nav_harita"): st.session_state["active_menu"] = "Harita"; st.rerun()
        if st.button("⚖️ Hukuk & İcra", key="nav_hukuk"): st.session_state["active_menu"] = "Hukuk/İcra"; st.rerun()
        if st.button("☁️ Dijital Arşiv", key="nav_bulut"): st.session_state["active_menu"] = "Bulut Arşiv"; st.rerun()
        if st.button("📄 Raporlar", key="nav_rapor"): st.session_state["active_menu"] = "Raporlar"; st.rerun()
        
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        if st.button("🚪 Güvenli Çıkış", key="exit"): cikis()

    elif st.session_state["rol"] == "sakin":
        st.markdown("<p style='color:#94A3B8; font-size:12px; font-weight:600; margin-left:15px; margin-bottom:5px;'>DAİRE SAKİNİ</p>", unsafe_allow_html=True)
        if st.button("👤 Durum Özeti", key="nav_durum"): st.session_state["active_menu"] = "Durum"; st.rerun()
        if st.button("💳 Ödeme Geçmişi", key="nav_odeme"): st.session_state["active_menu"] = "Ödeme"; st.rerun()
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        if st.button("🚪 Güvenli Çıkış", key="exit_s"): cikis()
    
    st.markdown("<div style='text-align:center; color:#cbd5e1; font-size:11px; margin-top:30px; font-weight: 500;'>Zorlu Soft Premium v61.0</div>", unsafe_allow_html=True)

# --- SAĞ İÇERİK ---
menu = st.session_state["active_menu"]

# Sayfa başlıklarını daha şık yapalım
st.markdown(f"""<h1 style='font-weight: 800; color: #1E293B; margin-bottom: 25px;'>{menu}</h1>""", unsafe_allow_html=True)

if st.session_state["rol"] == "admin":
    if menu == "Genel Bakış":
        
        toplam_alacak = sum(d['borc'] for d in data['daireler'].values())
        daire_sayisi = len(data["daireler"])
        
        # KARTLAR (PREMIUM GÖRÜNÜM)
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"<div class='metric-card'><h3>GÜNCEL KASA</h3><h1 style='color:#0066FF'>{data['kasa_nakit']:,.0f} ₺</h1></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><h3>TOPLAM ALACAK</h3><h1 style='color:#FF3B30'>{toplam_alacak:,.0f} ₺</h1></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-card'><h3>TOPLAM GİDER</h3><h1 style='color:#FF9500'>{sum(g['tutar'] for g in data['giderler']):,.0f} ₺</h1></div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='metric-card'><h3>DAİRE SAYISI</h3><h1 style='color:#1E293B'>{daire_sayisi}</h1></div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        cl, cr = st.columns([2, 1])
        with cl:
            st.subheader("Finansal Genel Durum")
            df_pie = pd.DataFrame({
                "Durum": ["Kasa Mevudu", "Alacaklar (Borçlu)", "Toplam Giderler"],
                "Tutar": [data['kasa_nakit'], toplam_alacak, sum(g['tutar'] for g in data['giderler'])]
            })
            # Renk paletini güncelledik: Mavi, Kırmızı, Turuncu
            fig = px.pie(df_pie, values='Tutar', names='Durum', hole=0.75, color_discrete_sequence=["#0066FF", "#FF3B30", "#FF9500"])
            fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
        with cr:
            st.subheader("Hızlı İşlemler")
            st.markdown("<div style='background: white; padding: 20px; border-radius: 16px; border: 1px solid #EFF2F7;'>", unsafe_allow_html=True)
            st.write("Sistem verileri düzenli olarak otomatik yedeklenmektedir. Manuel yedek almak için aşağıdaki butonu kullanabilirsiniz.")
            if st.button("💾 VERİLERİ GÜVENLE KAYDET", type="primary", use_container_width=True): 
                kaydet(data); st.success("Tüm veriler başarıyla yedeklendi.")
            st.markdown("</div>", unsafe_allow_html=True)

    elif menu == "Giderler":
        c1, c2 = st.columns([1,2])
        with c1:
            st.markdown("<div style='background: white; padding: 25px; border-radius: 16px; border: 1px solid #EFF2F7; box-shadow: 0 4px 10px rgba(0,0,0,0.03);'>", unsafe_allow_html=True)
            st.subheader("Yeni Gider Ekle")
            with st.form("gider"):
                gt = st.selectbox("Gider Türü", ["Enerji (Elk/Su/Gaz)", "Personel Maaş/SGK", "Bakım & Onarım", "Demirbaş Alımı", "Diğer"]); 
                ga = st.text_input("Açıklama (Örn: Ocak Ayı Faturası)"); 
                gm = st.number_input("Tutar (TL)", min_value=0.0, format="%.2f")
                if st.form_submit_button("Gideri Kaydet", use_container_width=True, type="primary"):
                    data["giderler"].append({"tarih":str(datetime.date.today()),"tur":gt,"aciklama":ga,"tutar":gm})
                    data["kasa_nakit"] -= gm; kaydet(data); st.success("Gider başarıyla işlendi."); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with c2: 
            st.subheader("Gider Geçmişi")
            st.dataframe(pd.DataFrame(data["giderler"]), use_container_width=True, hide_index=True)

    elif menu == "Hesaplar":
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
        <div class='metric-card' style='border-left: 6px solid {"#FF3B30" if info["borc"] > 0 else "#0066FF"}; display: flex; justify-content: space-between; align-items: center;'>
            <div>
                <h3>DAİRE NO: {secilen}</h3>
                <h1 style='font-size: 36px;'>{info['sahip']}</h1>
            </div>
            <div style='text-align: right;'>
                 <h3>GÜNCEL BORÇ</h3>
                 <h1 style='color: {"#FF3B30" if info["borc"] > 0 else "#0066FF"}; font-size: 40px;'>{info['borc']:,.2f} ₺</h1>
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
            st.markdown("<div style='background: white; padding: 25px; border-radius: 16px; border: 1px solid #EFF2F7; box-shadow: 0 4px 10px rgba(0,0,0,0.03);'>", unsafe_allow_html=True)
            st.subheader("Tahsilat İşlemi")
            t = st.number_input("Tahsil Edilen Tutar (TL)", min_value=0.0, format="%.2f"); 
            if st.button("Ödemeyi Onayla", use_container_width=True, type="primary"): 
                info["borc"]-=t; data["kasa_nakit"]+=t; info["gecmis"].append(f"{datetime.date.today()} | Ödeme: {t:,.2f} TL"); kaydet(data); st.success("Ödeme alındı."); st.rerun()
            
            st.markdown("---")
            st.subheader("Makbuz")
            pdf_data = pdf_olustur(secilen, info["sahip"], t if t > 0 else info["borc"])
            if pdf_data: st.download_button("📄 PDF Makbuz İndir", pdf_data, f"makbuz_{secilen}.pdf", "application/pdf", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    elif menu == "Harita":
        cols = st.columns(4)
        for i, (no, info) in enumerate(sorted(data["daireler"].items())):
            with cols[i % 4]:
                # Borçlu ise kırmızı, değilse mavi kenarlık
                color = "#FF3B30" if info["borc"] > 0 else "#0066FF" 
                st.markdown(f"""
                <div class='metric-card' style='border-top: 6px solid {color}; padding: 20px; min-height: 150px;'>
                    <h3 style='margin-bottom: 5px;'>DAİRE {no} - BLOK {info['blok']}</h3>
                    <h2 style='font-size: 20px; margin: 0 0 10px 0;'>{info['sahip']}</h2>
                    <h3 style='margin-bottom: 0;'>BORÇ DURUMU</h3>
                    <h1 style='color: {color}; font-size: 28px;'>{info['borc']:,.0f} ₺</h1>
                </div>
                <br>
                """, unsafe_allow_html=True)
    
    elif menu == "Hukuk/İcra": 
        st.warning("⚠️ Aşağıdaki daireler icra takibindedir veya hukuki süreç başlatılmıştır.")
        icraliklar = [v for v in data["daireler"].values() if v["icra"]]
        if icraliklar:
             st.dataframe(pd.DataFrame(icraliklar), use_container_width=True)
        else:
             st.success("İcralık daire bulunmamaktadır.")

    elif menu == "Bulut Arşiv": 
        st.info("☁️ Siteye ait önemli evrakları (Proje, Karar Defteri vb.) buradan yükleyip saklayabilirsiniz. (Demo)")
        st.file_uploader("Dosya Seçiniz", accept_multiple_files=True)

    elif menu == "Raporlar": 
        st.info("📄 Tüm dairelerin detaylı listesi ve durum raporu.")
        st.dataframe(pd.DataFrame.from_dict(data["daireler"], orient='index'), use_container_width=True)

# SAKİN
elif st.session_state["rol"] == "sakin":
    no = st.session_state["user"]; info = data["daireler"][no]
    if menu == "Durum": 
        st.title(f"Hoş Geldiniz, {info['sahip']}")
        c1, c2 = st.columns(2)
        c1.markdown(f"<div class='metric-card'><h3>GÜNCEL BORCUNUZ</h3><h1 style='color: {'#FF3B30' if info['borc']>0 else '#0066FF'}'>{info['borc']:,.2f} ₺</h1></div>", unsafe_allow_html=True)
        
    elif menu == "Ödeme": 
        st.title("Hesap Geçmişi")
        temiz = [x.split("|") if "|" in x else ["-", x] for x in reversed(info["gecmis"])]; 
        st.dataframe(pd.DataFrame(temiz, columns=["Tarih","İşlem"]), use_container_width=True, hide_index=True)

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
    page_title="Zorlu Soft | PRO", 
    layout="wide", 
    page_icon="🏢",
    initial_sidebar_state="collapsed" 
)

# --- LOGO AYARLARI ---
LOGO_DOSYA = "logo.png" 
LOGO_URL_YEDEK = "https://cdn-icons-png.flaticon.com/512/9203/9203741.png"

def logo_getir():
    if os.path.exists(LOGO_DOSYA): return LOGO_DOSYA
    return LOGO_URL_YEDEK

# --- CSS: HIGH CONTRAST UI (AYRIŞTIRILMIŞ MENÜ) ---
st.markdown("""
<style>
    /* 1. STANDARTLARI GİZLE */
    [data-testid="stSidebar"] {display: none;}
    [data-testid="collapsedControl"] {display: none;}
    #MainMenu {visibility: hidden;} 
    footer {visibility: hidden;} 
    [data-testid="stHeader"] {display: none;}
    .stDeployButton {display:none;}
    
    /* 2. GENEL ARKA PLAN (Açık Gri - İçerik Öne Çıksın) */
    .stApp { background-color: #ecf0f1; margin-top: -50px; }
    
    /* 3. SOL MENÜ (İşte Burası Değişti) */
    div[data-testid="column"]:nth-of-type(1) {
        /* GEÇİŞLİ ARKA PLAN (GRADIENT) - Derinlik Katar */
        background: linear-gradient(180deg, #2c3e50 0%, #000000 100%);
        
        /* KESKİN SINIR ÇİZGİSİ (AYRAÇ) */
        border-right: 5px solid #ff3f34; /* Zorlu Kırmızısı */
        
        /* GÖLGE (Üstte dursun) */
        box-shadow: 10px 0 25px rgba(0,0,0,0.5);
        
        padding-top: 30px;
        text-align: center;
        height: 120vh;
        position: fixed;
        left: 0;
        top: 0;
        width: 100px !important;
        z-index: 9999;
        display: block;
    }
    
    /* 4. SAĞ İÇERİK */
    div[data-testid="column"]:nth-of-type(2) {
        margin-left: 120px !important; /* Menüden uzaklaş */
        width: calc(100% - 130px) !important;
        padding-top: 20px;
    }

    /* 5. MENÜ BUTONLARI (Hayalet Stil Devam) */
    div[data-testid="column"]:nth-of-type(1) .stButton button {
        width: 55px !important;
        height: 55px !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,0.1) !important; /* İnce çerçeve */
        background-color: rgba(255,255,255,0.05) !important; /* Çok hafif beyazlık */
        color: #dfe6e9 !important; /* Açık gri ikon */
        font-size: 24px !important;
        margin: 0 auto 15px auto !important;
        display: block !important;
        transition: all 0.3s ease;
    }
    
    /* Hover Efekti */
    div[data-testid="column"]:nth-of-type(1) .stButton button:hover {
        background-color: #ff3f34 !important;
        border-color: #ff3f34 !important;
        color: white !important;
        transform: scale(1.15); /* Biraz daha büyüsün */
        box-shadow: 0 0 15px rgba(255, 63, 52, 0.6); /* Parlama */
    }

    /* Aktif Buton */
    div[data-testid="column"]:nth-of-type(1) .stButton button:focus {
        background-color: #ff3f34 !important;
        border-color: #ff3f34 !important;
        color: white !important;
    }

    /* DİĞER STİLLER */
    .login-box { background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); width: 100%; max-width: 400px; margin: 80px auto; text-align: center; }
    .galaxy-card { background: white; border-radius: 16px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 15px; border:1px solid white;}
    .profile-header { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); display: flex; align-items: center; gap: 20px; margin-bottom: 20px; }
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

def demo_veri():
    return {
        "site_adi": "Zorlu Cloud",
        "kasa_nakit": 85000.0, "kasa_banka": 250000.0,
        "arizalar": [{"id": 1, "konu": "Garaj Kapısı", "durum": "Bekliyor", "tarih": "2026-01-13"}],
        "anketler": [{"id": 1, "soru": "Güvenlik artsın mı?", "secenekler": {"Evet": 10, "Hayır": 2}, "durum": "Aktif"}],
        "rezervasyonlar": [], "market_siparisleri": [], "loglar": [], "giderler": [],
        "daireler": {
            "1": {"sahip": "Ahmet Yılmaz", "blok": "A", "tel": "905551112233", "borc": 0.0, "gecmis": [], "plaka": "46 KM 123", "icra": False, "notlar": [], "aile": []},
            "2": {"sahip": "Yeter Zorlu", "blok": "A", "tel": "905337140212", "borc": 5400.0, "gecmis": ["Aidat x3"], "plaka": "34 ZRL 01", "icra": True, "notlar": ["Avukatta"], "aile": ["Mehmet"]}
        }
    }

if "data" not in st.session_state: st.session_state["data"] = verileri_yukle()
data = st.session_state["data"]

# --- PDF DÜZELTİCİ ---
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
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        aktif_logo = logo_getir()
        st.markdown(f"<div class='login-box'><img src='{aktif_logo}' width='100'><h2>{data['site_adi']}</h2><p>Giriş v40</p></div>", unsafe_allow_html=True)
        u = st.text_input("Kullanıcı Adı"); p = st.text_input("Şifre", type="password")
        if st.button("GİRİŞ", type="primary", use_container_width=True):
            user_data = kullanici_dogrula(u, p)
            if user_data:
                st.session_state["giris"] = True
                st.session_state["rol"] = str(user_data["rol"])
                st.session_state["user"] = str(user_data["daire_no"])
                st.rerun()
            else: st.error("Hatalı!")
    st.stop()

def cikis(): st.session_state["giris"] = False; st.rerun()

# ==============================================================================
# ANA YAPI
# ==============================================================================

col_nav, col_main = st.columns([1, 20]) 

# --- SOL MENÜ ---
with col_nav:
    if os.path.exists(LOGO_DOSYA): st.image(LOGO_DOSYA, use_container_width=True)
    else: st.markdown("🏢")
    
    st.markdown("---")
    
    if st.session_state["rol"] == "admin":
        menu_items = [
            ("Genel Bakış", "🚀"), ("Giderler", "💸"), ("Hesaplar", "👥"), 
            ("Harita", "🏘️"), ("Otopark", "🚗"), ("Anketler", "📊"),
            ("Rezervasyon", "📅"), ("Market", "🛒"), ("Hukuk/İcra", "⚖️"),
            ("Kanban", "📋"), ("WhatsApp", "💬"), ("Otomasyon", "🤖"),
            ("Bulut Arşiv", "☁️"), ("Raporlar", "📄")
        ]
        for label, icon in menu_items:
            if st.button(icon, key=f"nav_{label}", help=label):
                st.session_state["active_menu"] = label
                st.rerun()
                
        st.markdown("---")
        if st.button("🚪", key="exit", help="Çıkış"): cikis()

    elif st.session_state["rol"] == "sakin":
        menu_items = [("Durum", "👤"), ("Ödeme", "💳"), ("Talep", "📨")]
        for label, icon in menu_items:
            if st.button(icon, key=f"nav_{label}", help=label):
                st.session_state["active_menu"] = label
                st.rerun()
        st.markdown("---")
        if st.button("🚪", key="exit_s", help="Çıkış"): cikis()

# --- SAĞ İÇERİK ---
with col_main:
    menu = st.session_state["active_menu"]
    
    if st.session_state["rol"] == "admin":
        if menu == "Genel Bakış":
            st.title("🚀 Kokpit")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Kasa", f"{data['kasa_nakit']:,.0f} ₺")
            c2.metric("Gider", f"{sum(g['tutar'] for g in data['giderler']):,.0f} ₺")
            c3.metric("Otopark", f"{len([d for d in data['daireler'].values() if d['plaka']!='-'])}")
            c4.metric("Market", len(data['market_siparisleri']))
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            cl, cr = st.columns([2, 1])
            with cl:
                st.subheader("Finansal Durum")
                toplam_alacak = sum(d['borc'] for d in data['daireler'].values())
                df_pie = pd.DataFrame({
                    "Durum": ["Kasadaki Para", "Alacaklar", "Giderler"],
                    "Tutar": [data['kasa_nakit'], toplam_alacak, sum(g['tutar'] for g in data['giderler'])]
                })
                fig = px.pie(df_pie, values='Tutar', names='Durum', hole=0.4, color_discrete_sequence=["#2ecc71", "#f1c40f", "#e74c3c"])
                st.plotly_chart(fig, use_container_width=True)
            
            with cr:
                st.subheader("Hızlı İşlemler")
                if st.button("💾 VERİLERİ KAYDET", type="primary", use_container_width=True): 
                    kaydet(data); st.success("Yedeklendi")
                st.info("Sistem otomatik yedekleme yapıyor ancak işlem bitince basmanız önerilir.")

        elif menu == "Giderler":
            st.title("💸 Giderler")
            c1, c2 = st.columns([1,2])
            with c1:
                with st.form("gider"):
                    gt = st.selectbox("Tür", ["Enerji", "Personel", "Bakım"]); ga = st.text_input("Açıklama"); gm = st.number_input("Tutar")
                    if st.form_submit_button("Ekle", use_container_width=True):
                        data["giderler"].append({"tarih":str(datetime.date.today()),"tur":gt,"aciklama":ga,"tutar":gm})
                        data["kasa_nakit"] -= gm; kaydet(data); st.success("Eklendi"); st.rerun()
            with c2: st.dataframe(pd.DataFrame(data["giderler"]), use_container_width=True)

        elif menu == "Hesaplar":
            st.title("👥 Hesaplar")
            src = st.text_input("🔍 Daire Ara")
            filtre = None
            if src:
                 for k,v in data["daireler"].items():
                    if src.lower() in v["sahip"].lower() or src == k: filtre = k; break
            
            secilen = filtre if filtre else st.selectbox("Daire Seç", list(data["daireler"].keys()))
            info = data["daireler"][secilen]
            st.markdown(f"<div class='profile-header'><h2>{info['sahip']}</h2><h1 style='color:red; margin-left:auto'>{info['borc']} ₺</h1></div>", unsafe_allow_html=True)
            
            c1, c2 = st.columns([2,1])
            with c1:
                 if info["gecmis"]:
                    temiz = [x.split("|") if "|" in x else ["-", x] for x in reversed(info["gecmis"])]
                    st.dataframe(pd.DataFrame(temiz, columns=["Tarih", "İşlem"]), use_container_width=True)
            with c2:
                t = st.number_input("Tahsilat"); 
                if st.button("Ödeme Al", use_container_width=True): 
                    info["borc"]-=t; data["kasa_nakit"]+=t; info["gecmis"].append(f"{datetime.date.today()} | Ödeme: {t}"); kaydet(data); st.success("Tamam"); st.rerun()
                
                pdf_data = pdf_olustur(secilen, info["sahip"], t if t > 0 else info["borc"])
                if pdf_data: st.download_button("📄 Makbuz", pdf_data, f"makbuz_{secilen}.pdf", "application/pdf", use_container_width=True)

        elif menu == "Harita":
            st.title("🏘️ Bloklar")
            cols = st.columns(4)
            for i, (no, info) in enumerate(sorted(data["daireler"].items())):
                with cols[i % 4]:
                    color = "red" if info["borc"] > 0 else "green"
                    st.markdown(f"<div class='galaxy-card' style='border-top:4px solid {color}'><b>Daire {no}</b><br>{info['sahip']}<br><b>{info['borc']} ₺</b></div>", unsafe_allow_html=True)
        
        elif menu == "Otopark": st.title("🚗 Otopark"); st.dataframe(pd.DataFrame([{"Plaka":v["plaka"], "Sahip":v["sahip"]} for v in data["daireler"].values() if v["plaka"]!="-"]), use_container_width=True)
        elif menu == "Anketler":
            st.title("📊 Anketler")
            for a in data["anketler"]:
                st.write(a["soru"])
                st.plotly_chart(px.bar(pd.DataFrame(list(a["secenekler"].items()), columns=["Şık","Oy"]), x="Oy", y="Şık"), use_container_width=True)
        elif menu == "Market":
            st.title("🛒 Siparişler"); 
            if data["market_siparisleri"]:
                st.dataframe(pd.DataFrame(data["market_siparisleri"]), use_container_width=True)
                if st.button("Temizle"): data["market_siparisleri"]=[]; kaydet(data); st.rerun()
            else: st.info("Sipariş yok")
        elif menu == "Hukuk/İcra": st.title("⚖️ İcra"); st.write([v for v in data["daireler"].values() if v["icra"]])
        elif menu == "Kanban": st.title("📋 Arızalar"); st.write(data["arizalar"])
        elif menu == "Rezervasyon": st.title("📅 Rezervasyon"); st.write(data["rezervasyonlar"])
        elif menu == "WhatsApp": st.title("💬 WhatsApp"); st.info("Mesaj servisi aktif.")
        elif menu == "Otomasyon": st.title("🤖 Otomasyon"); st.button("Aidat Dağıt")
        elif menu == "Bulut Arşiv": st.title("☁️ Arşiv"); st.file_uploader("Dosya")
        elif menu == "Raporlar": st.dataframe(pd.DataFrame.from_dict(data["daireler"], orient='index'))

    # SAKİN
    elif st.session_state["rol"] == "sakin":
        no = st.session_state["user"]; info = data["daireler"][no]
        if menu == "Durum": st.title(f"Merhaba, {info['sahip']}"); st.metric("Borcunuz", info["borc"])
        elif menu == "Ödeme": st.title("Geçmiş"); temiz = [x.split("|") if "|" in x else ["-", x] for x in reversed(info["gecmis"])]; st.table(pd.DataFrame(temiz, columns=["Tarih","İşlem"]))
        elif menu == "Talep":
            st.title("Talep")
            if st.button("Su İste"): data["market_siparisleri"].append({"urun":"Su","daire":no}); info["borc"]+=100; kaydet(data); st.success("İstendi")

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

# --- CSS: BIYOS STYLE (AÇIK TEMA MENÜ) ---
st.markdown("""
<style>
    /* 1. GEREKSİZLERİ GİZLE */
    .stDeployButton, [data-testid="stHeaderActionElements"], footer, #MainMenu {
        display: none !important;
    }
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 0px !important;
        visibility: hidden !important;
    }

    /* 2. ANA EKRAN ARKA PLANI (Hafif Gri - Menüden ayrılsın diye) */
    [data-testid="stAppViewContainer"] {
        background-color: #f3f4f6 !important; 
        background-image: none !important; /* Resim varsa kaldır */
    }
    .block-container {
        padding-top: 20px !important;
    }

    /* 3. SOL MENÜ (BEYAZ & FERAH) */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important; /* BEYAZ ZEMİN */
        border-right: 1px solid #e5e7eb; /* İnce gri çizgi */
        box-shadow: 2px 0 10px rgba(0,0,0,0.02); /* Çok hafif gölge */
    }
    
    [data-testid="stSidebarCollapseButton"] { display: none !important; }

    /* 4. MENÜ YAZILARI VE BUTONLARI */
    [data-testid="stSidebar"] .stButton button {
        width: 100%;
        background-color: transparent !important;
        border: none !important;
        color: #64748b !important; /* KOYU GRİ YAZI (Referanstaki gibi) */
        text-align: left;
        padding: 12px 20px;
        font-size: 15px;
        font-weight: 500;
        margin: 2px 0 !important;
        border-radius: 8px !important; /* Hafif yuvarlak köşeler */
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
    }
    
    /* İKONLARI GRİLEŞTİR (Sakin dursunlar) */
    [data-testid="stSidebar"] .stButton button span {
        filter: grayscale(100%) opacity(0.7); 
    }

    /* 5. HOVER (ÜZERİNE GELİNCE) */
    [data-testid="stSidebar"] .stButton button:hover {
        background-color: #f1f5f9 !important; /* Çok açık gri */
        color: #0f172a !important; /* Siyahımsı */
    }

    /* 6. AKTİF BUTON (SEÇİLİ OLAN - Referanstaki Mavi Efekt) */
    [data-testid="stSidebar"] .stButton button:focus {
        background-color: #e0f2fe !important; /* AÇIK MAVİ ZEMİN */
        color: #0284c7 !important; /* MAVİ YAZI */
        font-weight: 600;
        box-shadow: none !important;
    }
    
    /* Aktif olunca ikonu da mavi yap */
    [data-testid="stSidebar"] .stButton button:focus span {
        filter: none !important; /* Rengi geri getir */
    }

    /* 7. GİRİŞ KUTUSU */
    .login-container {
        background: white;
        padding: 40px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        text-align: center;
        margin-top: 60px;
        border: 1px solid #e2e8f0;
    }
    
    /* 8. KARTLAR (Dashboard Kartları) */
    .metric-card {
        background: white;
        padding: 24px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #f1f5f9;
        text-align: left; /* Referanstaki gibi sola dayalı */
    }
    .metric-card h3 { color: #64748b; font-size: 14px; margin-bottom: 5px; font-weight: normal; }
    .metric-card h1 { color: #1e293b; font-size: 28px; font-weight: bold; margin: 0; }

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
        "site_adi": "KoruPark",
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
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""<div class="login-container">""", unsafe_allow_html=True)
        # Giriş ekranı da artık beyaz tema uyumlu (Koyu yazı)
        st.markdown("<h2 style='color:#1e293b; font-weight:800; margin-bottom:10px;'>KORUPARK</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color:#64748b; margin-bottom:30px;'>Site Yönetim Paneli</p>", unsafe_allow_html=True)
        u = st.text_input("Kullanıcı Kodu")
        p = st.text_input("Şifre", type="password")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("GİRİŞ YAP", type="primary", use_container_width=True):
            user_data = kullanici_dogrula(u, p)
            if user_data:
                st.session_state["giris"] = True
                st.session_state["rol"] = str(user_data["rol"])
                st.session_state["user"] = str(user_data["daire_no"])
                st.rerun()
            else: st.error("Hatalı Giriş")
        st.markdown("""</div>""", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#94a3b8; margin-top:20px; font-size:12px;'>Zorlu Soft | © 2026 | v59.0</p>", unsafe_allow_html=True)
    st.stop()

def cikis(): st.session_state["giris"] = False; st.rerun()

# ==============================================================================
# ANA YAPI (BEYAZ MENÜ)
# ==============================================================================

with st.sidebar:
    # MENÜ BAŞLIĞI - ARTIK KOYU RENK (Çünkü zemin beyaz)
    st.markdown("""
    <div style="padding: 10px 0 20px 5px; margin-bottom: 10px;">
        <h3 style="color:#1e293b; margin:0; font-size:22px; font-weight:800; letter-spacing:-0.5px;">KORUPARK</h3>
        <p style="color:#64748b; margin:0; font-size:13px;">Sistem Yöneticisi</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state["rol"] == "admin":
        if st.button("🏠 Genel Bakış", key="nav_genel"): st.session_state["active_menu"] = "Genel Bakış"; st.rerun()
        if st.button("📅 Rezervasyon", key="nav_rez"): st.session_state["active_menu"] = "Rezervasyon"; st.rerun()
        if st.button("📋 Kanban Pano", key="nav_kanban"): st.session_state["active_menu"] = "Kanban"; st.rerun()
        
        st.markdown("<div style='margin:10px 0; border-top:1px solid #f1f5f9;'></div>", unsafe_allow_html=True) # İnce ayraç
        
        if st.button("💸 Giderler", key="nav_gider"): st.session_state["active_menu"] = "Giderler"; st.rerun()
        if st.button("👥 Hesaplar", key="nav_hesap"): st.session_state["active_menu"] = "Hesaplar"; st.rerun()
        if st.button("🏘️ Harita", key="nav_harita"): st.session_state["active_menu"] = "Harita"; st.rerun()
        if st.button("🚗 Otopark", key="nav_oto"): st.session_state["active_menu"] = "Otopark"; st.rerun()
        if st.button("🛒 Market", key="nav_market"): st.session_state["active_menu"] = "Market"; st.rerun()
        
        st.markdown("<div style='margin:10px 0; border-top:1px solid #f1f5f9;'></div>", unsafe_allow_html=True)
        
        if st.button("📊 Anketler", key="nav_anket"): st.session_state["active_menu"] = "Anketler"; st.rerun()
        if st.button("⚖️ Hukuk/İcra", key="nav_hukuk"): st.session_state["active_menu"] = "Hukuk/İcra"; st.rerun()
        if st.button("💬 WhatsApp", key="nav_wa"): st.session_state["active_menu"] = "WhatsApp"; st.rerun()
        if st.button("☁️ Bulut Arşiv", key="nav_bulut"): st.session_state["active_menu"] = "Bulut Arşiv"; st.rerun()
        
        st.markdown("<div style='margin:20px 0;'></div>", unsafe_allow_html=True)
        if st.button("🚪 Çıkış Yap", key="exit"): cikis()

    elif st.session_state["rol"] == "sakin":
        if st.button("👤 Durum", key="nav_durum"): st.session_state["active_menu"] = "Durum"; st.rerun()
        if st.button("💳 Ödeme Geçmişi", key="nav_odeme"): st.session_state["active_menu"] = "Ödeme"; st.rerun()
        if st.button("📨 Talep Oluştur", key="nav_talep"): st.session_state["active_menu"] = "Talep"; st.rerun()
        st.markdown("<div style='margin:20px 0;'></div>", unsafe_allow_html=True)
        if st.button("🚪 Çıkış", key="exit_s"): cikis()
    
    st.markdown("<div style='text-align:left; color:#cbd5e1; font-size:11px; margin-top:20px; padding-left:10px;'>v59.0</div>", unsafe_allow_html=True)

# --- SAĞ İÇERİK ---
menu = st.session_state["active_menu"]

if st.session_state["rol"] == "admin":
    if menu == "Genel Bakış":
        st.title("Genel Bakış") # Başlığı sadeleştir
        
        # Kartlar (Referans Tasarımına Uygun - Sola Dayalı)
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"<div class='metric-card'><h3>KASA</h3><h1>{data['kasa_nakit']:,.0f} ₺</h1></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><h3>GİDER</h3><h1 style='color:#ef4444'>{sum(g['tutar'] for g in data['giderler']):,.0f} ₺</h1></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-card'><h3>OTOPARK</h3><h1>{len([d for d in data['daireler'].values() if d['plaka']!='-'])}</h1></div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='metric-card'><h3>SİPARİŞ</h3><h1>{len(data['market_siparisleri'])}</h1></div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        cl, cr = st.columns([2, 1])
        with cl:
            st.subheader("Mali Durum")
            toplam_alacak = sum(d['borc'] for d in data['daireler'].values())
            df_pie = pd.DataFrame({
                "Durum": ["Kasa", "Alacaklar", "Giderler"],
                "Tutar": [data['kasa_nakit'], toplam_alacak, sum(g['tutar'] for g in data['giderler'])]
            })
            fig = px.pie(df_pie, values='Tutar', names='Durum', hole=0.75, color_discrete_sequence=["#0ea5e9", "#f59e0b", "#ef4444"])
            st.plotly_chart(fig, use_container_width=True)
        with cr:
            st.subheader("Hızlı İşlemler")
            if st.button("💾 VERİLERİ ZORLA KAYDET", type="primary", use_container_width=True): 
                kaydet(data); st.success("Yedeklendi")
            st.info("İşlem bitince basmanız önerilir.")

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
                if src.lower() in v["sahip"].lower() or src == k: 
                    filtre = k
                    break
        secilen = filtre if filtre else st.selectbox("Daire Seç", list(data["daireler"].keys()))
        info = data["daireler"][secilen]
        st.markdown(f"<div class='metric-card'><h2>{info['sahip']}</h2><h1 style='color:#ef4444;'>{info['borc']} ₺</h1></div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
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
                color = "#ef4444" if info["borc"] > 0 else "#10b981" 
                st.markdown(f"<div class='metric-card' style='border-top:5px solid {color};'><b>Daire {no}</b><br>{info['sahip']}<br><b>{info['borc']} ₺</b></div>", unsafe_allow_html=True)
    
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

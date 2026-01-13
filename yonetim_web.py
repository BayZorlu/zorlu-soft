import streamlit as st
import pandas as pd
import plotly.express as px
import json
import datetime
from streamlit_option_menu import option_menu
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
    page_title="Zorlu Soft | PREMIUM", 
    layout="wide", 
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

# --- LOGO AYARLARI ---
LOGO_DOSYA = "logo.png" 
LOGO_URL_YEDEK = "https://cdn-icons-png.flaticon.com/512/9203/9203741.png"

def logo_getir():
    if os.path.exists(LOGO_DOSYA): return LOGO_DOSYA
    return LOGO_URL_YEDEK

# --- CSS: PREMIUM TASARIM ---
st.markdown("""
<style>
    /* 1. SAĞ ÜSTTEKİ GEREKSİZLERİ YOK ET (Share, GitHub vb.) */
    [data-testid="stHeaderActionElements"] {display: none !important;}
    .stDeployButton {display:none !important;}
    
    /* 2. HEADER AYARI (Şeffaf yap ama menü butonunu gizleme) */
    header[data-testid="stHeader"] {
        background-color: transparent;
        z-index: 99;
    }
    
    /* 3. SIDEBAR (SOL MENÜ) TASARIMI - KOYU PREMİUM */
    [data-testid="stSidebar"] {
        background-color: #2c3e50; /* Koyu Lacivert */
    }
    [data-testid="stSidebar"] * {
        color: white !important; /* Tüm yazılar beyaz */
    }
    
    /* 4. GENEL SAYFA */
    .stApp { background-color: #f5f7fa; }
    
    /* 5. GİRİŞ KUTUSU */
    .login-box { 
        background: white; 
        padding: 40px; 
        border-radius: 20px; 
        box-shadow: 0 10px 30px rgba(0,0,0,0.1); 
        width: 100%; 
        max-width: 400px; 
        margin: 80px auto; 
        text-align: center; 
    }
    
    /* 6. KARTLAR VE TABLOLAR */
    .galaxy-card { background: white; border-radius: 16px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 15px; border:1px solid white;}
    .profile-header { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); display: flex; align-items: center; gap: 20px; margin-bottom: 20px; }
    
    /* Menü seçili eleman rengi */
    .nav-link-selected {
        background-color: #e74c3c !important; /* Zorlu Kırmızısı */
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

# --- LOGIN ---
if "giris" not in st.session_state: st.session_state["giris"] = False; st.session_state["rol"] = ""

if not st.session_state["giris"]:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        aktif_logo = logo_getir()
        if aktif_logo.startswith("http"):
            st.markdown(f"<div class='login-box'><img src='{aktif_logo}' width='120'><h2>{data['site_adi']}</h2><p>Premium Giriş</p></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='login-box'>", unsafe_allow_html=True)
            st.image(aktif_logo, width=120)
            st.markdown(f"<h2>{data['site_adi']}</h2><p>Premium Giriş</p></div>", unsafe_allow_html=True)

        u = st.text_input("Kullanıcı Adı")
        p = st.text_input("Şifre", type="password")
        
        if st.button("GİRİŞ", type="primary", use_container_width=True):
            user_data = kullanici_dogrula(u, p)
            if user_data:
                st.session_state["giris"] = True
                st.session_state["rol"] = str(user_data["rol"])
                st.session_state["user"] = str(user_data["daire_no"])
                st.success("Giriş Başarılı!")
                st.rerun()
            else: st.error("Hatalı!")
    st.stop()

def cikis(): st.session_state["giris"] = False; st.rerun()

# ==============================================================================
# YÖNETİCİ EKRANI
# ==============================================================================
if st.session_state["rol"] == "admin":
    with st.sidebar:
        # LOGO
        if os.path.exists(LOGO_DOSYA): st.image(LOGO_DOSYA, width=150)
        else: st.image(LOGO_URL_YEDEK, width=100)
            
        st.markdown("### YÖNETİM PANELİ")
        menu = option_menu(None, ["Genel Bakış", "Giderler", "Hesaplar", "Harita", "Otopark", "Anketler", "Rezervasyon", "Market", "Hukuk/İcra", "Kanban", "WhatsApp", "Otomasyon", "Bulut Arşiv", "Raporlar"], 
            icons=["speedometer2", "wallet2", "person-badge", "grid", "car-front", "bar-chart", "calendar-check", "cart4", "hammer", "kanban", "whatsapp", "robot", "cloud", "file-text"], 
            menu_icon="cast", default_index=0, 
            styles={
                "nav-link": {"font-size": "14px", "text-align": "left", "margin":"0px", "--hover-color": "#34495e"},
                "nav-link-selected": {"background-color": "#e74c3c"}, # Zorlu Kırmızısı
                "container": {"padding": "0!important", "background-color": "transparent"}
            })
        if st.button("🚪 ÇIKIŞ YAP"): cikis()

    filtre = None
    if menu != "Genel Bakış":
        src = st.text_input("🔍 Hızlı Arama")
        if src:
            for k,v in data["daireler"].items():
                if src.lower() in v["sahip"].lower() or src == k: filtre = k; break

    if menu == "Genel Bakış" and not filtre:
        st.title("🚀 Yönetim Kokpiti")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Kasa", f"{data['kasa_nakit']:,.0f}")
        c2.metric("Gider", f"{sum(g['tutar'] for g in data['giderler']):,.0f}")
        c3.metric("Otopark", f"{len([d for d in data['daireler'].values() if d['plaka']!='-'])}")
        c4.metric("Market Sipariş", len(data['market_siparisleri']))
        
        cl, cr = st.columns([2, 1])
        with cl:
            fig = px.pie(names=["Kasa", "Alacak"], values=[data['kasa_nakit'], sum(d['borc'] for d in data['daireler'].values())], hole=0.5, color_discrete_sequence=["#3498db", "#e74c3c"])
            st.plotly_chart(fig, use_container_width=True)
        with cr:
            # BUTON DÜZELDİ: use_container_width=True sayesinde tam yayılacak
            if st.button("💾 VERİLERİ ZORLA KAYDET", type="primary", use_container_width=True): 
                kaydet(data); st.success("Buluta Yazıldı")

    elif menu == "Giderler":
        st.title("💸 Gider Yönetimi")
        c1, c2 = st.columns([1,2])
        with c1:
            with st.form("gider"):
                gt = st.selectbox("Tür", ["Enerji", "Personel", "Bakım"]); ga = st.text_input("Açıklama"); gm = st.number_input("Tutar")
                if st.form_submit_button("Kaydet", use_container_width=True):
                    data["giderler"].append({"tarih":str(datetime.date.today()),"tur":gt,"aciklama":ga,"tutar":gm})
                    data["kasa_nakit"] -= gm; kaydet(data); st.success("İşlendi"); st.rerun()
        with c2: 
            if data["giderler"]: st.dataframe(pd.DataFrame(data["giderler"]), use_container_width=True)
            else: st.info("Harcama yok.")

    elif menu == "Hesaplar" or filtre:
        secilen = filtre if filtre else st.selectbox("Daire", list(data["daireler"].keys()))
        info = data["daireler"][secilen]
        st.markdown(f"<div class='profile-header'><h2>{info['sahip']}</h2><h1 style='color:red; margin-left:auto'>{info['borc']} ₺</h1></div>", unsafe_allow_html=True)
        c1, c2 = st.columns([2,1])
        with c1: 
            if info["gecmis"]: 
                temiz_veri = []
                for x in reversed(info["gecmis"]):
                    if "|" in x: temiz_veri.append(x.split("|"))
                    else: temiz_veri.append(["-", x])
                st.dataframe(pd.DataFrame(temiz_veri, columns=["Tarih", "İşlem"]), use_container_width=True)
            else: st.info("İşlem yok")
        with c2:
            t = st.number_input("Tahsilat"); 
            col_a, col_b = st.columns(2)
            if col_a.button("Ödeme Al", use_container_width=True): 
                info["borc"]-=t; data["kasa_nakit"]+=t; info["gecmis"].append(f"{datetime.date.today()} | Ödeme: {t}"); kaydet(data); st.success("Tamam"); st.rerun()
            
            pdf_data = pdf_olustur(secilen, info["sahip"], t if t > 0 else info["borc"])
            if pdf_data:
                col_b.download_button(label="📄 Makbuz", data=pdf_data, file_name=f"makbuz_{secilen}.pdf", mime="application/pdf", use_container_width=True)

    elif menu == "Harita":
        st.title("🏘️ Bloklar")
        cols = st.columns(4)
        for i, (no, info) in enumerate(sorted(data["daireler"].items())):
            with cols[i % 4]:
                color = "red" if info["borc"] > 0 else "green"
                st.markdown(f"<div class='galaxy-card' style='border-top:4px solid {color}'><b>Daire {no}</b><br>{info['sahip']}<br><b>{info['borc']} ₺</b></div>", unsafe_allow_html=True)

    elif menu == "Otopark":
        st.title("🚗 Araç Listesi")
        df = pd.DataFrame([{"Plaka":v["plaka"], "Sahip":v["sahip"]} for v in data["daireler"].values() if v["plaka"]!="-"])
        st.dataframe(df, use_container_width=True)

    elif menu == "Anketler":
        st.title("🗳️ Anket Sonuçları")
        for a in data["anketler"]:
            st.subheader(a["soru"])
            df = pd.DataFrame(list(a["secenekler"].items()), columns=["Şık", "Oy"])
            st.plotly_chart(px.bar(df, x="Oy", y="Şık", orientation='h'), use_container_width=True)

    elif menu == "Rezervasyon":
        st.title("📅 Rezervasyonlar")
        if data["rezervasyonlar"]: st.dataframe(pd.DataFrame(data["rezervasyonlar"]), use_container_width=True)
        else: st.info("Rezervasyon yok.")

    elif menu == "Market":
        st.title("🛒 Gelen Siparişler")
        if data["market_siparisleri"]: 
            st.dataframe(pd.DataFrame(data["market_siparisleri"]), use_container_width=True)
            if st.button("Listeyi Temizle", use_container_width=True): data["market_siparisleri"] = []; kaydet(data); st.rerun()
        else: st.success("Bekleyen sipariş yok.")

    elif menu == "Hukuk/İcra":
        st.title("⚖️ İcralık Dosyalar")
        icra = [v for v in data["daireler"].values() if v["icra"]]
        if icra:
            for d in icra: st.error(f"⚠️ {d['sahip']} - BORÇ: {d['borc']} TL")
        else: st.success("İcralık daire yok.")

    elif menu == "Kanban":
        st.title("📋 Arızalar")
        c1, c2, c3 = st.columns(3)
        for i, s in enumerate(["Bekliyor", "İşlemde", "Tamamlandı"]):
            [c1,c2,c3][i].subheader(s)
            for t in [x for x in data["arizalar"] if x["durum"]==s]:
                [c1,c2,c3][i].info(f"{t['konu']} ({t['tarih']})")

    elif menu == "WhatsApp":
        st.title("WhatsApp"); 
        for k,v in data["daireler"].items():
            if v["borc"]>0: st.warning(f"{v['sahip']} borçlu -> Mesaj At")

    elif menu == "Otomasyon":
        st.title("Robotlar")
        if st.button("1000 TL Aidat Dağıt", use_container_width=True):
            for d in data["daireler"].values(): d["borc"]+=1000
            kaydet(data); st.success("Eklendi")

    elif menu == "Bulut Arşiv":
        st.title("Arşiv"); st.file_uploader("Dosya Yükle")

    elif menu == "Raporlar":
        st.dataframe(pd.DataFrame.from_dict(data["daireler"], orient='index'), use_container_width=True)

# ==============================================================================
# SAKİN EKRANI
# ==============================================================================
elif st.session_state["rol"] == "sakin":
    no = st.session_state["user"]
    info = data["daireler"][no]
    with st.sidebar:
        # LOGO
        if os.path.exists(LOGO_DOSYA): st.image(LOGO_DOSYA, width=150)
        else: st.image(LOGO_URL_YEDEK, width=100)
        
        st.title(f"Daire {no}"); menu = option_menu(None, ["Durum", "Ödeme", "Talep"], icons=["person", "card", "envelope"])
        if st.button("Çıkış"): cikis()
    
    if menu == "Durum":
        st.metric("Borcunuz", info["borc"])
        if info["borc"] > 0: st.error("Lütfen Ödeyiniz")
    elif menu == "Ödeme": 
        if info["gecmis"]:
            temiz_veri = []
            for x in reversed(info["gecmis"]):
                if "|" in x: temiz_veri.append(x.split("|"))
                else: temiz_veri.append(["-", x])
            st.table(pd.DataFrame(temiz_veri, columns=["Tarih","İşlem"]))
    elif menu == "Talep": 
        if st.button("Su İste (100 TL)", use_container_width=True): 
            data["market_siparisleri"].append({"urun":"Su","daire":no}); info["borc"]+=100; kaydet(data); st.success("İstendi")

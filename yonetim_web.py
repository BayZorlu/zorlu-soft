import streamlit as st
import pandas as pd
import plotly.express as px
import json
import datetime
from streamlit_option_menu import option_menu
from io import BytesIO
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- HATA ÖNLEYİCİ ---
try:
    from fpdf import FPDF
    import xlsxwriter
    LIB_OK = True
except: LIB_OK = False

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Zorlu Soft | PRO", layout="wide", page_icon="🏢")

# --- CSS: HAYALET MODU (HER ŞEYİ GİZLEME) ---
st.markdown("""
<style>
    /* 1. STREAMLIT İMZALARINI YOK ET */
    #MainMenu {visibility: hidden;} 
    header {visibility: hidden;} 
    footer {visibility: hidden;} 
    
    /* Sağ üstteki ve sağ alttaki butonları zorla gizle */
    [data-testid="stToolbar"] {visibility: hidden !important;} 
    [data-testid="stDecoration"] {display: none;}
    .stDeployButton {display:none;}
    
    /* Sayfa Rengi ve Düzeni */
    .stApp { background-color: #f5f7fa; margin-top: -80px; }
    
    /* --- BURADAN AŞAĞISI NORMAL TASARIM --- */
    
    /* LOGIN KUTUSU */
    .login-box { background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); width: 100%; max-width: 400px; margin: 100px auto; text-align: center; }

    /* ROZETLER */
    .badge { padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: bold; margin-right: 5px; }
    .badge-vip { background: #e3f2fd; color: #1565c0; }
    .badge-risk { background: #ffebee; color: #c62828; }
    .badge-legal { background: #212121; color: #fff; border: 1px solid red; }
    
    /* KARTLAR */
    .galaxy-card { background: white; border-radius: 16px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 15px; border:1px solid white;}
    .kanban-card { background: white; padding: 12px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 8px; border-left: 5px solid #3498db; }
    .market-card { background: white; border-radius: 12px; padding: 15px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05); transition: 0.3s; cursor:pointer;}
    .market-card:hover { transform: scale(1.05); border: 1px solid #3498db; }
    .profile-header { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); display: flex; align-items: center; gap: 20px; margin-bottom: 20px; }
    .profile-avatar { width: 60px; height: 60px; background: linear-gradient(45deg, #667eea, #764ba2); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 24px; font-weight: bold; }
    .plaka-box { background: #ffcc00; color: black; font-weight: bold; padding: 3px 10px; border: 2px solid black; border-radius: 5px; }
    .wa-btn { background-color: #25D366; color: white !important; padding: 5px 15px; border-radius: 20px; text-decoration: none; font-weight: bold; font-size: 13px; display:inline-block;}
</style>
""", unsafe_allow_html=True)

# --- VERİTABANI BAĞLANTISI ---
SHEET_NAME = "ZorluDB"

def baglanti_kur():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

def verileri_yukle():
    try:
        client = baglanti_kur()
        sheet = client.open(SHEET_NAME).sheet1
        raw_data = sheet.cell(1, 1).value
        if raw_data: return json.loads(raw_data)
        else: return demo_veri()
    except: return demo_veri()

def kaydet(veri):
    try:
        client = baglanti_kur()
        sheet = client.open(SHEET_NAME).sheet1
        json_data = json.dumps(veri, ensure_ascii=False)
        sheet.update_cell(1, 1, json_data)
    except Exception as e: st.error(f"Kayıt Hatası: {e}")

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

# --- LOGIN ---
if "giris" not in st.session_state: st.session_state["giris"] = False; st.session_state["rol"] = ""

if not st.session_state["giris"]:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown(f"<div class='login-box'><h2>{data['site_adi']}</h2><p>Giriş Paneli</p></div>", unsafe_allow_html=True)
        u = st.text_input("Kullanıcı"); p = st.text_input("Şifre", type="password")
        if st.button("GİRİŞ", type="primary", use_container_width=True):
            if u == "admin" and p == "1234": st.session_state["giris"]=True; st.session_state["rol"]="admin"; st.rerun()
            elif u in data["daireler"] and p == "1234": st.session_state["giris"]=True; st.session_state["rol"]="sakin"; st.session_state["user"]=u; st.rerun()
            else: st.error("Hatalı!")
    st.stop()

def cikis(): st.session_state["giris"] = False; st.rerun()

# ==============================================================================
# YÖNETİCİ EKRANI
# ==============================================================================
if st.session_state["rol"] == "admin":
    with st.sidebar:
        st.title("Yönetici")
        menu = option_menu(None, ["Genel Bakış", "Giderler", "Hesaplar", "Harita", "Otopark", "Anketler", "Rezervasyon", "Market", "Hukuk/İcra", "Kanban", "WhatsApp", "Otomasyon", "Bulut Arşiv", "Raporlar"], 
            icons=["speedometer2", "wallet2", "person-badge", "grid", "car-front", "bar-chart", "calendar-check", "cart4", "hammer", "kanban", "whatsapp", "robot", "cloud", "file-text"], 
            menu_icon="cast", default_index=0, styles={"nav-link-selected": {"background-color": "#e74c3c"}})
        if st.button("Çıkış"): cikis()

    filtre = None
    if menu != "Genel Bakış":
        src = st.text_input("🔍 Hızlı Arama")
        if src:
            for k,v in data["daireler"].items():
                if src.lower() in v["sahip"].lower() or src == k: filtre = k; break

    # --- MENÜ İÇERİKLERİ ---
    
    if menu == "Genel Bakış" and not filtre:
        st.title("🚀 Kokpit")
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
            if st.button("💾 ZORLA KAYDET"): kaydet(data); st.success("Buluta Yazıldı")

    elif menu == "Giderler":
        st.title("💸 Gider Yönetimi")
        c1, c2 = st.columns([1,2])
        with c1:
            with st.form("gider"):
                gt = st.selectbox("Tür", ["Enerji", "Personel", "Bakım"]); ga = st.text_input("Açıklama"); gm = st.number_input("Tutar")
                if st.form_submit_button("Kaydet"):
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
            if info["gecmis"]: st.dataframe(pd.DataFrame([x.split("|") for x in reversed(info["gecmis"])], columns=["Tarih", "İşlem"]), use_container_width=True)
            else: st.info("İşlem yok")
        with c2:
            t = st.number_input("Tahsilat"); 
            if st.button("Ödeme Al"): info["borc"]-=t; data["kasa_nakit"]+=t; info["gecmis"].append(f"{datetime.date.today()} | Ödeme: {t}"); kaydet(data); st.success("Tamam"); st.rerun()

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
            if st.button("Listeyi Temizle"): data["market_siparisleri"] = []; kaydet(data); st.rerun()
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
        if st.button("1000 TL Aidat Dağıt"):
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
        st.title(f"Daire {no}"); menu = option_menu(None, ["Durum", "Ödeme", "Talep"], icons=["person", "card", "envelope"])
        if st.button("Çıkış"): cikis()
    
    if menu == "Durum":
        st.metric("Borcunuz", info["borc"])
        if info["borc"] > 0: st.error("Lütfen Ödeyiniz")
    elif menu == "Ödeme": st.table(pd.DataFrame([x.split("|") for x in reversed(info["gecmis"])], columns=["Tarih","İşlem"]))
    elif menu == "Talep": 
        if st.button("Su İste (100 TL)"): 
            data["market_siparisleri"].append({"urun":"Su","daire":no}); info["borc"]+=100; kaydet(data); st.success("İstendi")

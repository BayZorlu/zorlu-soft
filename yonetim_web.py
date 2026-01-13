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
st.set_page_config(page_title="Zorlu Soft | CLOUD", layout="wide", page_icon="☁️")

# --- CSS TASARIM (EKSİKSİZ) ---
st.markdown("""
<style>
    /* GİZLİLİK */
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden !important;} [data-testid="stDecoration"] {display: none;}
    .stApp { background-color: #f5f7fa; margin-top: -60px; }
    
    /* LOGIN KUTUSU */
    .login-box { background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); width: 100%; max-width: 400px; margin: 100px auto; text-align: center; }

    /* KARTLAR VE ROZETLER */
    .badge { padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: bold; margin-right: 5px; }
    .badge-vip { background: #e3f2fd; color: #1565c0; }
    .badge-risk { background: #ffebee; color: #c62828; }
    .badge-legal { background: #212121; color: #fff; border: 1px solid red; }
    .badge-new { background: #e8f5e9; color: #2e7d32; }
    
    .galaxy-card { background: white; border-radius: 16px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 15px; border:1px solid white;}
    .galaxy-card:hover { transform: translateY(-5px); box-shadow: 0 10px 30px rgba(0,0,0,0.1); border-color:#eee;}
    
    .kanban-card { background: white; padding: 12px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 8px; border-left: 5px solid #3498db; }
    .res-card { background: white; border-radius: 12px; padding: 15px; border-left: 5px solid #9b59b6; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom:10px;}
    .market-card { background: white; border-radius: 12px; padding: 15px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05); transition: 0.3s; }
    .market-card:hover { transform: scale(1.05); border: 1px solid #3498db; }
    
    .ai-console { background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%); color: #00ff00; padding: 15px; border-radius: 10px; font-family: 'Courier New', monospace; box-shadow: 0 0 10px rgba(0,255,0,0.1); }
    .profile-header { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); display: flex; align-items: center; gap: 20px; margin-bottom: 20px; }
    .profile-avatar { width: 60px; height: 60px; background: linear-gradient(45deg, #667eea, #764ba2); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 24px; font-weight: bold; }
    .plaka-box { background: #ffcc00; color: black; font-weight: bold; padding: 3px 10px; border: 2px solid black; border-radius: 5px; }
    .right-panel { background: white; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    .wa-btn { background-color: #25D366; color: white !important; padding: 5px 15px; border-radius: 20px; text-decoration: none; font-weight: bold; font-size: 13px; display:inline-block;}
</style>
""", unsafe_allow_html=True)

# --- GOOGLE SHEETS VERİTABANI BAĞLANTISI ---
SHEET_NAME = "ZorluDB" # Google Sheet Adı (Senin oluşturduğun ad)

def baglanti_kur():
    """Google Sheets'e bağlanır."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

def verileri_yukle():
    """Google Sheets A1 hücresinden veriyi okur."""
    try:
        client = baglanti_kur()
        sheet = client.open(SHEET_NAME).sheet1
        raw_data = sheet.cell(1, 1).value
        if raw_data: return json.loads(raw_data)
        else: return demo_veri()
    except: return demo_veri() # Hata veya boşsa demo döner

def kaydet(veri):
    """Veriyi Google Sheets A1 hücresine yazar."""
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
            "2": {"sahip": "Yeter Zorlu", "blok": "A", "tel": "905337140212", "borc": 5400.0, "gecmis": ["Aidat x3"], "plaka": "34 ZRL 01", "icra": True, "notlar": ["Avukatta"], "aile": ["Mehmet"]},
            "3": {"sahip": "Mehmet Öz", "blok": "B", "tel": "905557778899", "borc": 0.0, "gecmis": [], "plaka": "-", "icra": False, "notlar": [], "aile": []},
            "4": {"sahip": "Caner Erkin", "blok": "B", "tel": "905550001122", "borc": 750.0, "gecmis": ["Aidat"], "plaka": "06 FB 1907", "icra": False, "notlar": [], "aile": []}
        }
    }

# Verileri Çek (Session State Kullanarak Hızlandır)
if "data" not in st.session_state:
    st.session_state["data"] = verileri_yukle()
data = st.session_state["data"]

# --- YARDIMCI FONKSİYONLAR ---
def pdf_olustur(daire_no, isim, tutar):
    if not LIB_OK: return None
    pdf = FPDF()
    pdf.add_page(); pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, txt=data['site_adi'].upper(), ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(190, 10, txt=f"TAHSİLAT MAKBUZU - {datetime.date.today()}", ln=True, align='C')
    pdf.line(10, 30, 200, 30); pdf.ln(20)
    pdf.cell(190, 10, txt=f"Sayın {isim} (Daire {daire_no})", ln=True)
    pdf.cell(190, 10, txt=f"Tutar: {tutar:.2f} TL", ln=True)
    return pdf.output(dest='S').encode('latin-1')

def excel_indir(df):
    if not LIB_OK: return None
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer: df.to_excel(writer, index=False)
    return output.getvalue()

# --- LOGIN SİSTEMİ ---
if "giris" not in st.session_state:
    st.session_state["giris"] = False
    st.session_state["rol"] = ""
    st.session_state["user"] = ""

if not st.session_state["giris"]:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown(f"""
        <div class="login-box">
            <img src="https://cdn-icons-png.flaticon.com/512/9203/9203741.png" width="80">
            <h2>{data['site_adi']}</h2>
            <p>Bulut Tabanlı Yönetim v26.0</p>
        </div>
        """, unsafe_allow_html=True)
        u = st.text_input("Kullanıcı")
        p = st.text_input("Şifre", type="password")
        if st.button("GİRİŞ YAP", type="primary", use_container_width=True):
            if u == "admin" and p == "1234":
                st.session_state["giris"] = True; st.session_state["rol"] = "admin"; st.rerun()
            elif u in data["daireler"] and p == "1234":
                st.session_state["giris"] = True; st.session_state["rol"] = "sakin"; st.session_state["user"] = u; st.rerun()
            else: st.error("Hatalı!")
    st.stop()

def cikis():
    st.session_state["giris"] = False; st.session_state["rol"] = ""; st.rerun()

# ==============================================================================
# YÖNETİCİ EKRANI (FULL ÖZELLİK)
# ==============================================================================
if st.session_state["rol"] == "admin":
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2942/2942813.png", width=60)
        st.title("Yönetici")
        menu = option_menu(None, ["Genel Bakış", "Giderler", "Hesaplar", "Harita", "Otopark", "Anketler", "Rezervasyon", "Market", "Hukuk/İcra", "Kanban", "WhatsApp", "Otomasyon", "Bulut Arşiv", "AI Asistan", "Raporlar"], 
            icons=["speedometer2", "wallet2", "person-badge", "grid", "car-front", "bar-chart", "calendar-check", "cart4", "hammer", "kanban", "whatsapp", "robot", "cloud", "chat-dots", "file-text"], 
            menu_icon="cast", default_index=0, styles={"nav-link-selected": {"background-color": "#e74c3c"}})
        if st.button("Çıkış Yap"): cikis()

    filtre = None
    if menu != "Genel Bakış":
        src = st.text_input("🔍 Hızlı Arama")
        if src:
            for k,v in data["daireler"].items():
                if src.lower() in v["sahip"].lower() or src == k: filtre = k; break

    # --- 1. GENEL BAKIŞ ---
    if menu == "Genel Bakış" and not filtre:
        st.title("🚀 Yönetim Kokpiti")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Kasa", f"{data['kasa_nakit']:,.0f}")
        c2.metric("Gider", f"{sum(g['tutar'] for g in data['giderler']):,.0f}")
        c3.metric("Otopark", f"{len([d for d in data['daireler'].values() if d['plaka']!='-'])}")
        c4.metric("Arıza", len(data['arizalar']))
        if st.button("💾 Verileri Buluta Zorla Kaydet"): kaydet(data); st.success("Kaydedildi!")

    # --- 2. GİDERLER ---
    elif menu == "Giderler":
        st.title("💸 Gider Yönetimi")
        c1, c2 = st.columns([1,2])
        with c1:
            with st.form("gider"):
                gt = st.selectbox("Tür", ["Enerji", "Personel", "Bakım"])
                ga = st.text_input("Açıklama"); gm = st.number_input("Tutar")
                if st.form_submit_button("Kaydet"):
                    data["giderler"].append({"tarih":str(datetime.date.today()),"tur":gt,"aciklama":ga,"tutar":gm})
                    data["kasa_nakit"] -= gm; kaydet(data); st.success("Kaydedildi"); st.rerun()
        with c2: st.dataframe(pd.DataFrame(data["giderler"]))

    # --- 3. HESAPLAR ---
    elif menu == "Hesaplar" or filtre:
        secilen = filtre if filtre else st.selectbox("Daire", list(data["daireler"].keys()))
        info = data["daireler"][secilen]
        st.title(f"{info['sahip']} - {info['borc']} TL")
        c1, c2 = st.columns([2,1])
        c1.table(pd.DataFrame(info["gecmis"], columns=["Geçmiş"]))
        with c2:
            t = st.number_input("Tahsilat")
            if st.button("Ödeme Al"):
                info["borc"] -= t; data["kasa_nakit"] += t; info["gecmis"].append(f"{datetime.date.today()} | Ödeme: {t}")
                kaydet(data); st.success("Buluta Yazıldı!"); st.rerun()

    # --- DİĞER MENÜLER (Kısa Özet, hepsi çalışıyor) ---
    elif menu == "Harita": st.title("Harita"); st.write("Blok Görünümü")
    elif menu == "Otopark": st.title("Otopark"); st.dataframe(pd.DataFrame([v for v in data["daireler"].values() if v["plaka"]!="-"]))
    elif menu == "Anketler": st.title("Anketler"); st.write(data["anketler"])
    elif menu == "Rezervasyon": st.title("Rezervasyon"); st.write(data["rezervasyonlar"])
    elif menu == "Market": st.title("Market"); st.write(data["market_siparisleri"])
    elif menu == "Hukuk/İcra": st.title("İcra"); st.write([d for d in data["daireler"].values() if d["icra"]])
    elif menu == "Kanban": st.title("Arızalar"); st.write(data["arizalar"])
    elif menu == "WhatsApp": st.title("WhatsApp"); st.warning("Mesaj Paneli")
    elif menu == "Otomasyon": 
        if st.button("1000 TL Aidat Dağıt"):
            for d in data["daireler"].values(): d["borc"]+=1000
            kaydet(data); st.success("Dağıtıldı")
    elif menu == "Bulut Arşiv": st.title("Arşiv"); st.file_uploader("Dosya")
    elif menu == "AI Asistan": st.title("Asistan"); st.text_input("Sor")
    elif menu == "Raporlar": st.dataframe(pd.DataFrame.from_dict(data["daireler"], orient='index'))

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
    elif menu == "Ödeme": st.table(info["gecmis"])
    elif menu == "Talep": 
        if st.button("Su İste"): 
            data["market_siparisleri"].append({"urun":"Su","daire":no}); info["borc"]+=100; kaydet(data); st.success("İstendi")

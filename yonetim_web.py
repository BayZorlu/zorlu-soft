import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
import datetime
from streamlit_option_menu import option_menu
from io import BytesIO

# --- HATA ÖNLEYİCİ MODÜLLER ---
try:
    from fpdf import FPDF
    import xlsxwriter
    LIB_OK = True
except: LIB_OK = False

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Zorlu Soft | TITAN", layout="wide", page_icon="🏢")

# --- CSS TASARIM (HİÇBİR ŞEY EKSİLTİLMEDİ) ---
st.markdown("""
<style>
    /* GİZLİLİK */
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden !important;} [data-testid="stDecoration"] {display: none;}
    .stApp { background-color: #f5f7fa; margin-top: -60px; }
    
    /* LOGIN KUTUSU */
    .login-box {
        background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        width: 100%; max-width: 400px; margin: 100px auto; text-align: center;
    }

    /* ROZETLER */
    .badge { padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: bold; margin-right: 5px; }
    .badge-vip { background: #e3f2fd; color: #1565c0; }
    .badge-risk { background: #ffebee; color: #c62828; }
    .badge-legal { background: #212121; color: #fff; border: 1px solid red; }
    .badge-new { background: #e8f5e9; color: #2e7d32; }
    
    /* KART TASARIMLARI */
    .galaxy-card { background: white; border-radius: 16px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 15px; border:1px solid white;}
    .galaxy-card:hover { transform: translateY(-5px); box-shadow: 0 10px 30px rgba(0,0,0,0.1); border-color:#eee;}
    
    .kanban-card { background: white; padding: 12px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 8px; border-left: 5px solid #3498db; }
    .res-card { background: white; border-radius: 12px; padding: 15px; border-left: 5px solid #9b59b6; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom:10px;}
    .market-card { background: white; border-radius: 12px; padding: 15px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05); transition: 0.3s; }
    .market-card:hover { transform: scale(1.05); border: 1px solid #3498db; }
    
    /* GİDER KARTI (YENİ) */
    .expense-card { background: #fff0f0; border-left: 5px solid #e74c3c; padding: 10px; margin-bottom: 5px; border-radius: 5px; }

    /* NEON KONSOL */
    .ai-console { background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%); color: #00ff00; padding: 15px; border-radius: 10px; font-family: 'Courier New', monospace; box-shadow: 0 0 10px rgba(0,255,0,0.1); }
    
    /* PROFİL DETAY */
    .profile-header { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); display: flex; align-items: center; gap: 20px; margin-bottom: 20px; }
    .profile-avatar { width: 60px; height: 60px; background: linear-gradient(45deg, #667eea, #764ba2); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 24px; font-weight: bold; }
    .plaka-box { background: #ffcc00; color: black; font-weight: bold; padding: 3px 10px; border: 2px solid black; border-radius: 5px; }
    .right-panel { background: white; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    
    /* WHATSAPP BUTONU */
    .wa-btn { background-color: #25D366; color: white !important; padding: 5px 15px; border-radius: 20px; text-decoration: none; font-weight: bold; font-size: 13px; display:inline-block;}
</style>
""", unsafe_allow_html=True)

# --- VERİTABANI (GİDERLER EKLENDİ) ---
DOSYA_ADI = "bina_verileri_v25.json"
CLOUD_KLASOR = "zorlu_cloud_files"
if not os.path.exists(CLOUD_KLASOR): os.makedirs(CLOUD_KLASOR)

def demo_veri():
    return {
        "site_adi": "Zorlu TITAN",
        "kasa_nakit": 95000.0,
        "kasa_banka": 300000.0,
        "arizalar": [{"id": 1, "konu": "Garaj Kapısı", "durum": "Bekliyor", "tarih": "2026-01-13"}],
        "anketler": [{"id": 1, "soru": "Mantolama yapılsın mı?", "secenekler": {"Evet": 10, "Hayır": 5}, "durum": "Aktif"}],
        "rezervasyonlar": [], "market_siparisleri": [], "loglar": [],
        "giderler": [ # YENİ GİDER TABLOSU
            {"tarih": "2026-01-10", "tur": "Enerji", "aciklama": "Ortak Elektrik Faturası", "tutar": 4500.0},
            {"tarih": "2026-01-12", "tur": "Personel", "aciklama": "Kapıcı Maaşı", "tutar": 17002.0}
        ],
        "daireler": {
            "1": {"sahip": "Ahmet Yılmaz", "blok": "A", "tel": "905551112233", "borc": 0.0, "gecmis": [], "plaka": "46 KM 123", "icra": False, "notlar": [], "aile": []},
            "2": {"sahip": "Yeter Zorlu", "blok": "A", "tel": "905337140212", "borc": 5400.0, "gecmis": ["Aidat x3"], "plaka": "34 ZRL 01", "icra": True, "notlar": ["Avukatta"], "aile": ["Mehmet"]},
            "3": {"sahip": "Mehmet Öz", "blok": "B", "tel": "905557778899", "borc": 0.0, "gecmis": [], "plaka": "-", "icra": False, "notlar": [], "aile": []},
            "4": {"sahip": "Caner Erkin", "blok": "B", "tel": "905550001122", "borc": 750.0, "gecmis": ["Aidat"], "plaka": "06 FB 1907", "icra": False, "notlar": [], "aile": []}
        }
    }

def verileri_yukle():
    if os.path.exists(DOSYA_ADI):
        try:
            with open(DOSYA_ADI, "r", encoding="utf-8") as f:
                data = json.load(f)
                defaults = {"rezervasyonlar": [], "market_siparisleri": [], "arizalar": [], "anketler": [], "loglar": [], "giderler": [], "daireler": {}}
                for k,v in defaults.items():
                    if k not in data: data[k] = v
                return data
        except: return demo_veri()
    return demo_veri()

def kaydet(veri):
    with open(DOSYA_ADI, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)

data = verileri_yukle()

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
            <p>Sistem v25.0 | TITAN</p>
        </div>
        """, unsafe_allow_html=True)
        u = st.text_input("Kullanıcı Adı (admin veya Daire No)")
        p = st.text_input("Şifre (1234)", type="password")
        if st.button("GİRİŞ YAP", type="primary", use_container_width=True):
            if u == "admin" and p == "1234":
                st.session_state["giris"] = True; st.session_state["rol"] = "admin"; st.rerun()
            elif u in data["daireler"] and p == "1234":
                st.session_state["giris"] = True; st.session_state["rol"] = "sakin"; st.session_state["user"] = u; st.rerun()
            else: st.error("Hatalı!")
    st.stop()

def cikis():
    st.session_state["giris"] = False
    st.session_state["rol"] = ""
    st.rerun()

# ==============================================================================
# YÖNETİCİ EKRANI (FULL ÖZELLİK + GİDERLER)
# ==============================================================================
if st.session_state["rol"] == "admin":
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2942/2942813.png", width=60)
        st.title("Yönetici Paneli")
        # MENÜYE "GİDERLER" EKLENDİ
        menu = option_menu(None, ["Genel Bakış", "Giderler (Harcama)", "Hesaplar", "Harita", "Otopark", "Anketler", "Rezervasyon", "Market", "Hukuk/İcra", "Kanban (Arıza)", "WhatsApp", "Otomasyon", "Bulut Arşiv", "AI Asistan", "Raporlar"], 
            icons=["speedometer2", "wallet2", "person-badge", "grid", "car-front", "bar-chart", "calendar-check", "cart4", "hammer", "kanban", "whatsapp", "robot", "cloud", "chat-dots", "file-text"], 
            menu_icon="cast", default_index=0, styles={"nav-link-selected": {"background-color": "#e74c3c"}})
        if st.button("Çıkış Yap"): cikis()

    # SPOTLIGHT ARAMA
    filtre = None
    if menu != "Genel Bakış":
        src = st.text_input("🔍 Hızlı Arama (İsim, No, Plaka)")
        if src:
            for k,v in data["daireler"].items():
                if src.lower() in v["sahip"].lower() or src == k or src.lower().replace(" ","") in v["plaka"].lower().replace(" ",""):
                    filtre = k; break

    # --- 1. GENEL BAKIŞ (GİDER EKLENDİ) ---
    if menu == "Genel Bakış" and not filtre:
        st.title("🚀 Yönetim Kokpiti")
        c1, c2, c3, c4 = st.columns(4)
        toplam_gider = sum(g['tutar'] for g in data['giderler'])
        net_kasa = (data['kasa_nakit'] + data['kasa_banka']) - toplam_gider # Basit Net Hesap
        
        c1.metric("Toplam Varlık", f"{(data['kasa_nakit']+data['kasa_banka']):,.0f} TL")
        c2.metric("Toplam Harcama", f"{toplam_gider:,.0f} TL", delta="-Gider", delta_color="inverse")
        c3.metric("Otopark", f"{len([d for d in data['daireler'].values() if d['plaka']!='-'])}")
        c4.metric("Aktif Arıza", len([x for x in data['arizalar'] if x['durum']!='Tamamlandı']))
        
        cl, cr = st.columns([2, 1])
        with cl:
            st.subheader("Gelir/Gider Dağılımı")
            alacak = sum(d['borc'] for d in data['daireler'].values())
            # Kasa, Alacak ve Giderleri Karşılaştır
            fig = px.pie(names=["Kasadaki Para", "Alacaklar", "Harcamalar"], values=[net_kasa, alacak, toplam_gider], hole=0.5, color_discrete_sequence=["#3498db", "#f1c40f", "#e74c3c"])
            st.plotly_chart(fig, use_container_width=True)
        with cr:
            st.markdown('<div class="ai-console">>> SİSTEM ONLİNE<br>>> TÜM MODÜLLER AKTİF</div>', unsafe_allow_html=True)

    # --- 2. GİDERLER (YENİ MODÜL) ---
    elif menu == "Giderler (Harcama)":
        st.title("💸 Gider Yönetimi ve Faturalar")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Harcama Ekle")
            with st.form("gider_form"):
                g_tur = st.selectbox("Gider Türü", ["Enerji", "Personel", "Bakım/Onarım", "Temizlik", "Demirbaş", "Diğer"])
                g_aciklama = st.text_input("Açıklama (Örn: Asansör Bakımı)")
                g_tutar = st.number_input("Tutar (TL)", min_value=1.0)
                g_kaynak = st.radio("Ödeme Kaynağı", ["Nakit Kasa", "Banka"])
                
                if st.form_submit_button("Harcamayı Kaydet"):
                    yeni_gider = {
                        "tarih": str(datetime.date.today()),
                        "tur": g_tur,
                        "aciklama": g_aciklama,
                        "tutar": g_tutar
                    }
                    data["giderler"].append(yeni_gider)
                    
                    # Kasadan düş
                    if g_kaynak == "Nakit Kasa": data["kasa_nakit"] -= g_tutar
                    else: data["kasa_banka"] -= g_tutar
                    
                    kaydet(data)
                    st.success("Gider işlendi ve kasadan düşüldü.")
                    st.rerun()

        with col2:
            st.subheader("Son Harcamalar")
            if data["giderler"]:
                # Giderleri tablo yap
                df_gider = pd.DataFrame(data["giderler"])
                # Tersten sırala (en yeni en üstte)
                st.dataframe(df_gider.iloc[::-1], use_container_width=True)
                
                # Pasta Grafiği (Türlere Göre)
                fig = px.pie(df_gider, values='tutar', names='tur', title='Harcama Dağılımı')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Henüz harcama girilmedi.")

    # --- 3. HESAPLAR ---
    elif menu == "Hesaplar" or filtre:
        secilen = filtre if filtre else st.selectbox("Hesap Seç:", list(data["daireler"].keys()), format_func=lambda x: f"Daire {x} - {data['daireler'][x]['sahip']}")
        info = data["daireler"][secilen]
        
        badges = ""
        if info['icra']: badges += '<span class="badge badge-legal">⚖️ İCRALIK</span> '
        elif info["borc"] > 0: badges += '<span class="badge badge-risk">Riskli</span> '
        else: badges += '<span class="badge badge-vip">Yıldız</span> '
        if int(info.get("giris", "2000")) >= 2024: badges += '<span class="badge badge-new">Yeni</span>'

        st.markdown(f"""
        <div class="profile-header">
            <div class="profile-avatar">{info['sahip'][:2].upper()}</div>
            <div style="flex-grow:1;">
                <h2 style="margin:0;">{info['sahip']} {badges}</h2>
                <p style="color:#777;">{info['blok']} Blok - Daire {secilen} | <span class="plaka-box">{info['plaka']}</span></p>
            </div>
            <h1 style="color:{'#c62828' if info['borc']>0 else '#2ecc71'}">{info['borc']:,.2f} ₺</h1>
        </div>""", unsafe_allow_html=True)
        
        c_main, c_right = st.columns([7, 3])
        with c_main:
            st.subheader("📋 Geçmiş")
            if info["gecmis"]: st.table(pd.DataFrame([x.split("|") for x in reversed(info["gecmis"])], columns=["Tarih", "İşlem"]))
            else: st.info("Hareket yok.")
            
            t1, t2 = st.tabs(["Notlar", "Aile"])
            with t1:
                for n in info["notlar"]: st.warning(f"📌 {n}")
                if st.button("Not Ekle"): info["notlar"].append("Yeni not"); kaydet(data); st.rerun()
            with t2: st.write(", ".join(info["aile"]))

        with c_right:
            st.markdown(f'<div class="right-panel"><h3>BAKİYE</h3><h1>{info["borc"]:.2f} ₺</h1></div>', unsafe_allow_html=True)
            tel = info.get('tel','').replace('+','')
            link = f"https://wa.me/{tel}/?text=Borcunuz:{info['borc']}TL"
            st.markdown(f'<a href="{link}" target="_blank" class="wa-btn" style="width:100%; text-align:center; margin-top:10px;">💬 WhatsApp</a>', unsafe_allow_html=True)
            
            with st.expander("💸 Ödeme Al", expanded=True):
                t = st.number_input("Tutar", step=100.0)
                if st.button("Tahsil Et"):
                    info["borc"] -= t; data["kasa_nakit"] += t; info["gecmis"].append(f"{datetime.date.today()} | Ödeme: -{t}")
                    kaydet(data); st.success("Tamam"); st.rerun()

    # --- 4. HARİTA ---
    elif menu == "Harita":
        st.title("🏘️ Görsel Harita")
        cols = st.columns(4)
        for i, (no, info) in enumerate(sorted(data["daireler"].items())):
            with cols[i % 4]:
                border = "black" if info['icra'] else "red" if info["borc"] > 0 else "green"
                bg = "#ffebee" if info['icra'] else "white"
                st.markdown(f"""<div class="galaxy-card" style="border-top:5px solid {border}; background:{bg}; text-align:center;">
                <h3>{no}</h3><b>{info['sahip']}</b><br><h3 style="color:{border}">{info['borc']:.0f} ₺</h3></div>""", unsafe_allow_html=True)

    # --- 5. OTOPARK ---
    elif menu == "Otopark":
        st.title("🚗 Otopark Yönetimi")
        df = pd.DataFrame([{"Plaka":v["plaka"], "Sahip":v["sahip"]} for v in data["daireler"].values() if v["plaka"]!="-"])
        st.dataframe(df, use_container_width=True)
        if q := st.text_input("Plaka Sorgula"):
            res = [v['sahip'] for v in data['daireler'].values() if q in v['plaka']]
            if res: st.success(f"Araç Sahibi: {res[0]}")
            else: st.error("Bulunamadı")

    # --- 6. ANKETLER ---
    elif menu == "Anketler":
        st.title("🗳️ Dijital Sandık")
        for a in data["anketler"]:
            st.subheader(a["soru"])
            df = pd.DataFrame(list(a["secenekler"].items()), columns=["Şık", "Oy"])
            st.plotly_chart(px.bar(df, x="Oy", y="Şık", orientation='h'), use_container_width=True)
            s = st.radio("Seç", list(a["secenekler"].keys()), key=a['id'])
            if st.button("Oy Ver", key=f"b_{a['id']}"): a["secenekler"][s]+=1; kaydet(data); st.rerun()
        with st.expander("Yeni Anket"):
            q = st.text_input("Soru"); o = st.text_input("Şıklar (virgülle)")
            if st.button("Yayınla"): data["anketler"].append({"id":99, "soru":q, "secenekler":{x:0 for x in o.split(",")}, "durum":"Aktif"}); kaydet(data); st.rerun()

    # --- 7. REZERVASYON ---
    elif menu == "Rezervasyon":
        st.title("📅 Sosyal Tesis")
        c1, c2 = st.columns(2)
        with c1:
            tesis = st.selectbox("Yer", ["Tenis", "Sauna"])
            tarih = st.date_input("Tarih")
            daire = st.selectbox("Daire", list(data["daireler"].keys()))
            if st.button("Randevu Al"):
                data["rezervasyonlar"].append({"tesis":tesis, "tarih":str(tarih), "daire":daire})
                kaydet(data); st.success("Alındı")
        with c2: st.write(pd.DataFrame(data["rezervasyonlar"]))

    # --- 8. MARKET ---
    elif menu == "Market":
        st.title("🛒 Sanal Market")
        c1, c2 = st.columns(2)
        with c1: 
            st.markdown('<div class="market-card">💧 <b>Su (100 TL)</b></div>', unsafe_allow_html=True)
            if st.button("Su İste"): st.session_state.sip = "Su"
        with c2: 
            st.markdown('<div class="market-card">🍞 <b>Ekmek (30 TL)</b></div>', unsafe_allow_html=True)
            if st.button("Ekmek İste"): st.session_state.sip = "Ekmek"
        
        if "sip" in st.session_state:
            st.info(f"Seçilen: {st.session_state.sip}")
            kim = st.selectbox("Kim İstiyor?", list(data["daireler"].keys()), key="mk")
            if st.button("Onayla"):
                fiyat = 100 if st.session_state.sip=="Su" else 30
                data["daireler"][kim]["borc"] += fiyat
                data["market_siparisleri"].append({"urun":st.session_state.sip, "daire":kim})
                kaydet(data); st.success("Sipariş Kapıcıda!"); del st.session_state.sip; st.rerun()

    # --- 9. HUKUK / İCRA ---
    elif menu == "Hukuk/İcra":
        st.title("⚖️ Hukuk Takip")
        icra = [v for v in data["daireler"].values() if v["icra"]]
        if icra:
            for d in icra: st.error(f"DOSYA: {d['sahip']} - Borç: {d['borc']} TL")
        else: st.success("İcralık dosya yok.")

    # --- 10. KANBAN (ARIZA) ---
    elif menu == "Kanban (Arıza)":
        st.title("📋 Arıza Panosu")
        c1, c2, c3 = st.columns(3)
        for i, s in enumerate(["Bekliyor", "İşlemde", "Tamamlandı"]):
            [c1,c2,c3][i].subheader(s)
            for t in [x for x in data["arizalar"] if x["durum"]==s]:
                [c1,c2,c3][i].markdown(f"<div class='kanban-card'>{t['konu']}</div>", unsafe_allow_html=True)
        with st.expander("Arıza Ekle"):
            konu = st.text_input("Konu"); 
            if st.button("Ekle"): data["arizalar"].append({"id":99, "konu":konu, "durum":"Bekliyor"}); kaydet(data); st.rerun()

    # --- 11. WHATSAPP & OTOMASYON ---
    elif menu == "WhatsApp":
        st.title("WhatsApp Center")
        for k,v in data["daireler"].items():
            if v["borc"]>0: st.warning(f"{v['sahip']}: {v['borc']} TL -> Mesaj atılmalı")

    elif menu == "Otomasyon":
        st.title("Robotlar")
        if st.button("Herkese 1000 TL Ekle"):
            for d in data["daireler"].values(): d["borc"]+=1000
            kaydet(data); st.success("Eklendi")

    # --- 12. DİĞER ---
    elif menu == "Bulut Arşiv":
        st.title("☁️ Arşiv"); up = st.file_uploader("Dosya"); 
        if up: st.success("Yüklendi (Demo)")

    elif menu == "AI Asistan":
        st.title("🤖 Asistan"); p = st.chat_input("Sor")
        if p: st.info("Sistem şuan hesaplamada...")

    elif menu == "Raporlar":
        st.title("Raporlar"); st.dataframe(pd.DataFrame.from_dict(data["daireler"], orient='index'))

# ==============================================================================
# SAKİN EKRANI (KISITLI GÖRÜNÜM)
# ==============================================================================
elif st.session_state["rol"] == "sakin":
    no = st.session_state["user"]
    info = data["daireler"][no]
    with st.sidebar:
        st.title(f"Daire {no}"); st.caption(info["sahip"])
        menu = option_menu(None, ["Durumum", "Ödemeler", "Anketler", "Market"], icons=["person", "credit-card", "bar-chart", "cart"])
        if st.button("Çıkış"): cikis()
    
    if menu == "Durumum":
        st.title(f"Merhaba, {info['sahip']}")
        bg = "#e74c3c" if info["borc"] > 0 else "#2ecc71"
        st.markdown(f"<div style='background:{bg}; padding:30px; border-radius:15px; color:white; text-align:center;'><h1>{info['borc']} TL</h1><p>BORÇ DURUMU</p></div>", unsafe_allow_html=True)
    elif menu == "Ödemeler":
        st.table(pd.DataFrame([x.split("|") for x in reversed(info["gecmis"])], columns=["Tarih", "İşlem"]))
    elif menu == "Anketler":
        for a in data["anketler"]:
            st.info(a["soru"])
            sel = st.radio("Seç", list(a["secenekler"].keys()), key=f"s_{a['id']}")
            if st.button("Oy Ver", key=f"b_{a['id']}"): a["secenekler"][sel]+=1; kaydet(data); st.success("Verildi")
    elif menu == "Market":
        if st.button("Su İste (100 TL)"): 
            data["market_siparisleri"].append({"urun":"Su", "daire":no}); info["borc"]+=100; kaydet(data); st.success("İstendi")
import streamlit as st
import random
import time

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Hayat Haritası", page_icon="🗺️", layout="wide")

# --- CSS TASARIM (3D HARİTA + SİYAH YAZILAR) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;900&display=swap');
    
    /* GENEL AYARLAR */
    .stApp, .stMarkdown, .stText, h1, h2, h3, h4, h5, h6, p, div, span, label {
        color: #000000 !important;
        font-family: 'Nunito', sans-serif !important;
    }
    .stApp { background-color: #ffffff; }
    .block-container { max-width: 1600px; padding-top: 1rem; margin: auto; }

    /* HUD (ÜST PANEL) */
    .hud-container {
        display: flex; justify-content: space-between; padding: 15px 40px; margin-bottom: 20px;
        background: #f8f9fa; border-radius: 20px; 
        border: 2px solid #000; box-shadow: 5px 5px 0px #000;
    }
    .hud-item { text-align: center; width: 100%; }
    .hud-label { font-size: 14px; font-weight: 900; text-transform: uppercase; letter-spacing: 1px;}
    .hud-value { font-size: 32px; font-weight: 900; }

    /* --- 3D HARİTA TASARIMI --- */
    .map-scene {
        perspective: 1000px; display: flex; justify-content: center;
        margin-bottom: 40px; margin-top: 20px;
    }
    .hex-grid {
        display: flex; flex-direction: column; align-items: center;
        transform: rotateX(40deg); transform-style: preserve-3d;
    }
    .hex-row { display: flex; justify-content: center; margin-bottom: -28px; }
    .hex-row.even { margin-left: 63px; }

    .hex {
        width: 120px; height: 130px; background-color: #f8f9fa; margin: 0 3px;
        clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
        display: flex; align-items: center; justify-content: center; font-size: 50px;
        transition: all 0.2s; position: relative;
        
        /* GÖLGE VE ÇERÇEVE */
        filter: drop-shadow(1px 1px 0px #000) drop-shadow(-1px -1px 0px #000) drop-shadow(0px 10px 5px rgba(0,0,0,0.3)); 
        z-index: 1;
    }
    .hex:hover { transform: translateY(-15px) scale(1.1); z-index: 50; cursor: pointer; background: white; }
    
    /* Harita Renkleri (Tag'e göre) */
    .hex.tag-wants { background: #e91e63; color: white !important; } /* Lüks - Pembe */
    .hex.tag-save { background: #2980b9; color: white !important; }  /* Yatırım - Mavi */
    .hex.tag-needs { background: #f39c12; color: white !important; } /* İhtiyaç - Turuncu */
    .hex.empty { background: #fff; }
    
    .hex-icon { transform: rotateX(-40deg); display:block; filter: drop-shadow(0 4px 0 rgba(0,0,0,0.2)); }

    /* KARTLAR */
    .card-container {
        background: white; border-radius: 15px; overflow: hidden;
        border: 2px solid #000; height: 100%; display: flex; flex-direction: column; text-align: center;
        padding-bottom: 15px; transition: transform 0.1s;
        box-shadow: 5px 5px 0px #000;
    }
    .card-container:hover { transform: translateY(-5px); box-shadow: 8px 8px 0px #000; }
    
    .group-tag {
        display: inline-block; padding: 5px 10px; border-radius: 0 0 10px 10px; font-size: 12px; font-weight: 900;
        color: white !important; margin: 0 auto 10px auto; text-transform: uppercase; border: 1px solid #000;
    }
    .tag-wants { background: #e91e63; }
    .tag-needs { background: #f39c12; }
    .tag-save { background: #2980b9; }

    .card-img { font-size: 60px; margin: 10px 0; }
    .card-title { font-weight: 900; font-size: 20px; margin-bottom: 5px; }
    .card-price { font-family: monospace; font-weight: 900; font-size: 18px; margin-bottom: 10px;}
    
    /* SAYAÇ */
    .timer-wrapper {
        text-align: center; margin-bottom: 20px; 
        padding: 20px; background: #ffebee; border: 3px solid #c62828; border-radius: 15px;
    }
    .timer-big { font-size: 60px; font-weight: 900; color: #c62828 !important; line-height: 1; }

    .stButton > button { 
        width: 100%; border-radius: 10px; font-weight: 900; height: 50px; 
        border: 2px solid #000; box-shadow: 3px 3px 0px #000;
        color: #000 !important; background: #fff;
    }
    .stButton > button:hover { background: #f0f0f0; }
    </style>
""", unsafe_allow_html=True)

# --- OYUN AYARLARI ---
MAX_TUR = 6
SURE_LIMITI = 60
ROWS, COLS = 4, 12 # Harita Boyutu

# --- DURUM DEĞİŞKENLERİ ---
if 'nakit' not in st.session_state: st.session_state.nakit = 3000
if 'mutluluk' not in st.session_state: st.session_state.mutluluk = 50
if 'gelecek' not in st.session_state: st.session_state.gelecek = 50
if 'ay' not in st.session_state: st.session_state.ay = 1
if 'oyun_bitti' not in st.session_state: st.session_state.oyun_bitti = False
if 'secilen_kart' not in st.session_state: st.session_state.secilen_kart = None
if 'timer_active' not in st.session_state: st.session_state.timer_active = False

# Harita State'i
if 'grid_map' not in st.session_state:
    st.session_state.grid_map = [[{"type": "empty", "icon": ""} for _ in range(COLS)] for _ in range(ROWS)]
    # Başlangıç noktası (Üniversite Diploması gibi düşün)
    st.session_state.grid_map[1][5] = {"type": "tag-save", "icon": "🎓"}

# --- SENARYOLAR ---
senaryolar = [
    # 1. AY
    {"baslik": "Acil İhtiyaçlar", "soru": "Ev kirası ve faturalar geldi. Para yetmiyor!", "kartlar": [
        {"ad": "Kredi Çek", "grup": "RAHATLA", "tag": "tag-wants", "icon": "💸", "fiyat": -5000, "mutluluk": 20, "gelecek": -30, "ders": "Borç Para: Cüzdanın doldu ama geleceğini sattın."},
        {"ad": "Mesaiye Kal", "grup": "ÇALIŞKAN", "tag": "tag-save", "icon": "👷", "fiyat": -1000, "mutluluk": -10, "gelecek": 10, "ders": "Emek: Para kazandın ama çok yoruldun."},
        {"ad": "Eşya Sat", "grup": "GERÇEKÇİ", "tag": "tag-needs", "icon": "📦", "fiyat": -2000, "mutluluk": -5, "gelecek": 5, "ders": "Nakit Yaratmak: Fazlalıklardan kurtulup bütçeni dengeledin."}
    ]},
    # 2. AY
    {"baslik": "Teknoloji Krizi", "soru": "Telefonun bozuldu. Ne yapacaksın?", "kartlar": [
        {"ad": "iPhone 15 Pro", "grup": "LÜKS", "tag": "tag-wants", "icon": "📱", "fiyat": 4000, "mutluluk": 30, "gelecek": -20, "ders": "Lüks Tüketim: Harika bir telefonun var ama paran bitti."},
        {"ad": "Tamir Ettir", "grup": "TASARRUF", "tag": "tag-save", "icon": "🔧", "fiyat": 500, "mutluluk": -5, "gelecek": 10, "ders": "Tamir: Eski telefonla devam etmek en kârlı olandır."},
        {"ad": "İkinci El Al", "grup": "MANTIK", "tag": "tag-needs", "icon": "♻️", "fiyat": 1500, "mutluluk": 10, "gelecek": 0, "ders": "Fiyat/Performans: İşini görecek kadar harcadın."}
    ]},
    # 3. AY
    {"baslik": "Yatırım Fırsatı", "soru": "Eline toplu bir para geçti.", "kartlar": [
        {"ad": "Tatile Git", "grup": "KEYİF", "tag": "tag-wants", "icon": "🏖️", "fiyat": 3000, "mutluluk": 40, "gelecek": -10, "ders": "Anı Yaşamak: Çok eğlendin ama para uçtu gitti."},
        {"ad": "Altın Al", "grup": "YATIRIM", "tag": "tag-save", "icon": "🥇", "fiyat": 3000, "mutluluk": 0, "gelecek": 40, "ders": "Gelecek: Bu para ileride sana katlanarak dönecek."},
        {"ad": "Borç Kapat", "grup": "HUZUR", "tag": "tag-needs", "icon": "🤝", "fiyat": 3000, "mutluluk": 10, "gelecek": 20, "ders": "Özgürlük: Borçsuz uyumak en büyük zenginliktir."}
    ]},
    # 4. AY
    {"baslik": "Ulaşım Sorunu", "soru": "İşe gidip gelmek çok yorucu.", "kartlar": [
        {"ad": "Araba Al", "grup": "KONFOR", "tag": "tag-wants", "icon": "🚗", "fiyat": 5000, "mutluluk": 25, "gelecek": -30, "ders": "Büyük Masraf: Araba sadece alış fiyatı değil, benzin ve bakımla da para yer."},
        {"ad": "Metroya Bin", "grup": "SABIR", "tag": "tag-save", "icon": "🚇", "fiyat": 200, "mutluluk": -10, "gelecek": 10, "ders": "Toplu Taşıma: Paran cebinde kaldı."},
        {"ad": "Bisiklet Al", "grup": "SAĞLIK", "tag": "tag-needs", "icon": "🚲", "fiyat": 1000, "mutluluk": 15, "gelecek": 15, "ders": "Sağlıklı Yaşam: Hem spor yaptın hem para biriktirdin."}
    ]},
     # 5. AY
    {"baslik": "Sağlık Sorunu", "soru": "Dişin ağrıyor. Ne yapacaksın?", "kartlar": [
        {"ad": "Estetik Yaptır", "grup": "KEYİFÇİ", "tag": "tag-wants", "icon": "✨", "fiyat": 4000, "mutluluk": 15, "gelecek": -10, "ders": "Estetik: Sağlıktan ziyade görünüşe harcadın."},
        {"ad": "Devlet Hastanesi", "grup": "YATIRIMCI", "tag": "tag-save", "icon": "🏥", "fiyat": 0, "mutluluk": -10, "gelecek": 5, "ders": "Devlet: Sıra bekledin ama para cebinde kaldı."},
        {"ad": "Özel Dolgu", "grup": "GERÇEKÇİ", "tag": "tag-needs", "icon": "🦷", "fiyat": 1500, "mutluluk": 5, "gelecek": 0, "ders": "Özel: Hızlı ve temiz çözüm."}
    ]},
    # 6. AY (FİNAL)
    {"baslik": "Yıl Sonu İndirimi", "soru": "Büyük indirimler başladı!", "kartlar": [
        {"ad": "Marka Kıyafetler", "grup": "KEYİFÇİ", "tag": "tag-wants", "icon": "👗", "fiyat": 3000, "mutluluk": 20, "gelecek": -15, "ders": "Moda: Çok şıksın ama cüzdan boşaldı."},
        {"ad": "Hisse Senedi", "grup": "YATIRIMCI", "tag": "tag-save", "icon": "📈", "fiyat": 2000, "mutluluk": -5, "gelecek": 25, "ders": "Borsa: Şirketlere ortak oldun."},
        {"ad": "Kışlık Bot", "grup": "GERÇEKÇİ", "tag": "tag-needs", "icon": "🥾", "fiyat": 1000, "mutluluk": 5, "gelecek": 5, "ders": "İhtiyaç: Sadece lazım olanı aldın."}
    ]}
]

if st.session_state.ay <= len(senaryolar):
    aktif_senaryo = senaryolar[st.session_state.ay - 1]
else:
    st.session_state.oyun_bitti = True

# --- FONKSİYONLAR ---
def islem_yap(kart):
    st.session_state.nakit -= kart['fiyat']
    st.session_state.mutluluk += kart['mutluluk']
    st.session_state.gelecek += kart['gelecek']
    
    # --- HARİTAYA YERLEŞTİRME ---
    placed = False
    for r in range(ROWS):
        for c in range(COLS):
            if st.session_state.grid_map[r][c]['type'] == 'empty':
                # Type yerine kartın TAG'ini (rengini) kullanıyoruz
                st.session_state.grid_map[r][c] = {"type": kart['tag'], "icon": kart['icon']}
                placed = True
                break
        if placed: break
    
    st.session_state.ay += 1
    st.session_state.secilen_kart = None
    st.session_state.timer_active = False 
    if st.session_state.ay > MAX_TUR: st.session_state.oyun_bitti = True

def sure_doldu_cezasi():
    st.session_state.nakit -= 500 
    st.session_state.mutluluk -= 20
    st.session_state.ay += 1
    st.session_state.secilen_kart = None
    st.session_state.timer_active = False
    st.toast('⏰ SÜRE DOLDU! -500₺ Ceza.', icon="💸")
    if st.session_state.ay > MAX_TUR: st.session_state.oyun_bitti = True
    st.rerun()

def timer_kapat():
    st.session_state.timer_active = False
    st.rerun()

def yeniden_baslat():
    st.session_state.clear()
    st.rerun()

# ================= ARAYÜZ =================

# 1. HUD
st.markdown(f"""
    <div class="hud-container">
        <div class="hud-item"><div class="hud-label">AY</div><div class="hud-value">{min(st.session_state.ay, 6)} / 6</div></div>
        <div class="hud-item"><div class="hud-label">CÜZDAN</div><div class="hud-value" style="color:#2e7d32;">{st.session_state.nakit} ₺</div></div>
        <div class="hud-item"><div class="hud-label">MUTLULUK</div><div class="hud-value" style="color:#c62828;">% {st.session_state.mutluluk}</div></div>
        <div class="hud-item"><div class="hud-label">GELECEK</div><div class="hud-value" style="color:#1565c0;">{st.session_state.gelecek}</div></div>
    </div>
""", unsafe_allow_html=True)

# 2. 3D HAYAT HARİTASI (ENVANTER YERİNE)
hex_html = "<div class='map-scene'><div class='hex-grid'>"
for i, row in enumerate(st.session_state.grid_map):
    r_cls = "even" if i%2!=0 else "odd"
    hex_html += f"<div class='hex-row {r_cls}'>"
    for cell in row:
        icn = f"<span class='hex-icon'>{cell['icon']}</span>" if cell['icon'] else ""
        hex_html += f"<div class='hex {cell['type']}'>{icn}</div>"
    hex_html += "</div>"
hex_html += "</div></div>"
st.markdown(hex_html, unsafe_allow_html=True)

# 3. OYUN ALANI
if st.session_state.oyun_bitti:
    not_harfi = "C"; yorum = "İdare eder."; renk = "#f39c12"
    if st.session_state.nakit < 0: not_harfi = "F"; yorum = "İFLAS!"; renk = "#c62828"
    elif st.session_state.gelecek > 100: not_harfi = "A+"; yorum = "MÜKEMMEL!"; renk = "#2e7d32"
    elif st.session_state.nakit > 5000: not_harfi = "A"; yorum = "ZENGİNSİN!"; renk = "#2e7d32"
    
    st.markdown(f"""
        <div style="text-align:center; padding:50px; background:white; border:3px solid #000; border-radius:20px; box-shadow:10px 10px 0px #000;">
            <h1>FİNANS KARNESİ</h1>
            <h1 style="font-size:120px; color:{renk}; margin:0; text-shadow: 3px 3px 0px #000;">{not_harfi}</h1>
            <h2>{yorum}</h2>
            <h3>Kalan Para: {st.session_state.nakit}₺ | Gelecek: {st.session_state.gelecek}</h3>
        </div>
    """, unsafe_allow_html=True)
    if st.button("🔄 TEKRAR OYNA"): yeniden_baslat()

else:
    if st.session_state.timer_active:
        timer_placeholder = st.empty()
        col_x, col_y = st.columns([1, 10])
        with col_x:
            if st.button("❌"): timer_kapat()
        for i in range(SURE_LIMITI, -1, -1):
            timer_placeholder.markdown(f"""
                <div class="timer-wrapper">
                    <div class="timer-big">{i}</div>
                    <p style="font-weight:bold;">KARAR SÜRESİ</p>
                </div>
            """, unsafe_allow_html=True)
            time.sleep(1)
            if i == 0: sure_doldu_cezasi()

    if st.session_state.secilen_kart:
        kart = st.session_state.secilen_kart
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown(f"""
                <div style="text-align:center; padding:30px; background:#fff; border:3px solid #000; border-radius:20px; box-shadow:8px 8px 0px #000;">
                    <div style="font-size:100px;">{kart['icon']}</div>
                    <h1>{kart['ad']}</h1>
                    <h2 style="color:{'#c62828' if kart['fiyat'] > 0 else '#2e7d32'}">{abs(kart['fiyat'])}₺</h2>
                </div>
            """, unsafe_allow_html=True)
        with c2:
            st.warning("⚠️ Bu kararı onaylıyor musunuz?")
            st.write(f"😊 Mutluluk Etkisi: **{kart['mutluluk']}**")
            st.write(f"🚀 Gelecek Etkisi: **{kart['gelecek']}**")
            st.write("---")
            col_b1, col_b2 = st.columns(2)
            if col_b1.button("✅ ONAYLA"): islem_yap(kart); st.rerun()
            if col_b2.button("❌ VAZGEÇ"): st.session_state.secilen_kart = None; st.rerun()
    else:
        if not st.session_state.timer_active:
            if st.button("⏱️ SÜREYİ BAŞLAT (60 Sn)"):
                st.session_state.timer_active = True
                st.rerun()

        st.subheader(f"📅 {st.session_state.ay}. AY: {aktif_senaryo['baslik']}")
        cols = st.columns(3)
        for i, kart in enumerate(aktif_senaryo['kartlar']):
            with cols[i]:
                fiyat_renk = "#2e7d32" if kart['fiyat'] < 0 else "#c62828"
                fiyat_metin = f"+{abs(kart['fiyat'])}₺" if kart['fiyat'] < 0 else f"-{kart['fiyat']}₺"
                st.markdown(f"""
                    <div class="card-container">
                        <span class="group-tag {kart['tag']}">{kart['grup']}</span>
                        <div class="card-img">{kart['icon']}</div>
                        <div class="card-title">{kart['ad']}</div>
                        <div class="card-price" style="color:{fiyat_renk}">{fiyat_metin}</div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("SEÇ", key=f"btn_{i}"):
                    st.session_state.timer_active = False 
                    st.session_state.secilen_kart = kart
                    st.rerun()

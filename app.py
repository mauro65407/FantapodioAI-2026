import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="FantapodioAI 2026", page_icon="🏁", layout="centered")

# --- CONNESSIONE GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- DATABASE CALENDARIO ---
CALENDARIO_GARE = [
    ("Australia", datetime(2026, 3, 8, 6, 0)),
    ("Cina", datetime(2026, 3, 15, 8, 0)),
    ("Giappone", datetime(2026, 3, 29, 7, 0)),
    ("Bahrain", datetime(2026, 4, 12, 17, 0)),
    ("Arabia Saudita", datetime(2026, 4, 19, 19, 0)),
    ("Miami", datetime(2026, 5, 3, 21, 30)),
    ("Monaco", datetime(2026, 5, 24, 15, 0)),
    ("Spagna", datetime(2026, 6, 7, 15, 0)),
    ("Canada", datetime(2026, 6, 21, 20, 0)),
    ("Italia (Monza)", datetime(2026, 9, 6, 15, 0)),
    ("Abu Dhabi", datetime(2026, 12, 6, 14, 0))
]

PILOTI_SELECT = ["- Seleziona -"] + ["VER", "HAD", "LEC", "HAM", "RUS", "ANT", "NOR", "PIA", "ALO", "STR", "GAS", "COL", "HUL", "BOR", "ALB", "SAI", "LAW", "LIN", "OCO", "BEA", "PER", "BOT"]
PILOTI_REALI = ["VER", "HAD", "LEC", "HAM", "RUS", "ANT", "NOR", "PIA", "ALO", "STR", "GAS", "COL", "HUL", "BOR", "ALB", "SAI", "LAW", "LIN", "OCO", "BEA", "PER", "BOT"]

# --- FUNZIONI DATI (PERSISTENZA) ---
def carica_dati():
    try:
        # Carica Classifica
        df_c = conn.read(worksheet="Classifica", ttl=0)
        st.session_state.classifica = df_c.set_index('Team').to_dict('index')
        
        # Carica Pronostici
        df_p = conn.read(worksheet="Pronostici", ttl=0)
        # Reset archivio locale prima di popolarlo
        st.session_state.archivio_pronostici = {g[0]: {} for g in CALENDARIO_GARE}
        for _, row in df_p.iterrows():
            if row['Gara'] in st.session_state.archivio_pronostici:
                st.session_state.archivio_pronostici[row['Gara']][row['Team']] = row['Podio']
    except Exception:
        # Inizializzazione se il foglio è nuovo
        st.session_state.classifica = {t: {"Punti": 0, "EnPlein": 0} for t in ["TeamCL", "TeamFL", "TeamML"]}
        st.session_state.archivio_pronostici = {g[0]: {} for g in CALENDARIO_GARE}

def salva_dati():
    # Salva Classifica
    df_class = pd.DataFrame(st.session_state.classifica).T.reset_index().rename(columns={'index': 'Team'})
    conn.update(worksheet="Classifica", data=df_class)
    
    # Salva Pronostici
    lista_prono = []
    for gara, team_data in st.session_state.archivio_pronostici.items():
        for team, podio in team_data.items():
            lista_prono.append({"Gara": gara, "Team": team, "Podio": podio})
    
    if lista_prono:
        df_prono = pd.DataFrame(lista_prono)
        conn.update(worksheet="Pronostici", data=df_prono)

# --- INIZIALIZZAZIONE ---
if 'archivio_pronostici' not in st.session_state:
    carica_dati()

st.title("🏁 FantapodioAI 2026")

# --- SIDEBAR ---
st.sidebar.header("🏆 Classifica Generale")
df_display = pd.DataFrame(st.session_state.classifica).T.reset_index().rename(columns={'index': 'Team'})
st.sidebar.table(df_display.sort_values(by="Punti", ascending=False))

# --- LOGICA TEMPORALE ---
adesso = datetime.now()
prossima_gara = next((g for g in CALENDARIO_GARE if g[1] > adesso), ("Fine Campionato", adesso))

# --- SEZIONE PRONOSTICO ---
with st.container(border=True):
    nomi_gare = [g[0] for g in CALENDARIO_GARE]
    idx_p = nomi_gare.index(prossima_gara[0]) if prossima_gara[0] in nomi_gare else 0
    gara_sel = st.selectbox("📂 Seleziona GP:", nomi_gare, index=idx_p)
    
    orario_gara = next(g[1] for g in CALENDARIO_GARE if g[0] == gara_sel)
    gara_scaduta = adesso > orario_gara

    st.subheader(f"📲 Pronostico: {gara_sel}")
    
    if gara_scaduta:
        st.error(f"🚫 Sessione Chiusa (Partenza: {orario_gara.strftime('%d/%m alle %H:%M')})")
    else:
        diff = orario_gara - adesso
        st.success(f"⏳ Tempo rimasto: {diff.days}g {diff.seconds//3600}h {(diff.seconds//60)%60}m")

    t_u = st.selectbox("Il tuo Team", ["- Scegli Team -", "TeamCL", "TeamFL", "TeamML"], key="team_scelto")
    c1, c2, c3 = st.columns(3)
    p1 = c1.selectbox("1° Posizione", PILOTI_SELECT, key="p1")
    p2 = c2.selectbox("2° Posizione", PILOTI_SELECT, key="p2")
    p3 = c3.selectbox("3° Posizione", PILOTI_SELECT, key="p3")
    
    col_save, col_canc = st.columns([3, 1])
    
    with col_save:
        if not gara_scaduta:
            if t_u != "- Scegli Team -" and p1 != "- Seleziona -" and p2 != "- Seleziona -" and p3 != "- Seleziona -":
                if st.button("💾 SALVA PRONOSTICO", use_container_width=True, type="primary"):
                    st.session_state.archivio_pronostici[gara_sel][t_u] = f"{p1}-{p2}-{p3}"
                    salva_dati()
                    st.toast("Salvato su Google Sheets!")
                    
                    msg = f"*FANTAPODIOAI 2026*\n🏁 *GP {gara_sel.upper()}*\n{t_u}: {p1}-{p2}-{p3}"
                    wa_url = f"https://wa.me/?text={urllib.parse.quote(msg)}"
                    st.link_button("🟢 INVIA AL GRUPPO", wa_url, use_container_width=True)
        else:
            st.button("🔒 PRONOSTICI CHIUSI", disabled=True, use_container_width=True)

    with col_canc:
        if st.button("🗑️ CANC", use_container_width=True):
            st.session_state.p1 = "- Seleziona -"
            st.session_state.p2 = "- Seleziona -"
            st.session_state.p3 = "- Seleziona -"
            st.rerun()

    st.divider()
    st.write(f"### 🏁 Podi registrati - {gara_sel}")
    podi_gara = st.session_state.archivio_pronostici.get(gara_sel, {})
    res_c1, res_c2, res_c3 = st.columns(3)
    res_c1.metric("TeamCL", podi_gara.get("TeamCL", "---"))
    res_c2.metric("TeamFL", podi_gara.get("TeamFL", "---"))
    res_c3.metric("TeamML", podi_gara.get("TeamML", "---"))

# --- PANNELLO ADMIN ---
with st.expander("🛠️ Pannello Admin"):
    target = st.selectbox("Assegna punti a:", ["TeamCL", "TeamFL", "TeamML"])
    r1 = st.selectbox("Reale P1", PILOTI_REALI, key="r1")
    r2 = st.selectbox("Reale P2", PILOTI_REALI, key="r2")
    r3 = st.selectbox("Reale P3", PILOTI_REALI, key="r3")
    
    if st.button("🚀 Aggiorna Classifica"):
        podi_admin = st.session_state.archivio_pronostici.get(gara_sel, {})
        scelta = podi_admin.get(target, "").split("-")
        if len(scelta) < 3:
            st.error("Nessun pronostico salvato per questo team!")
        else:
            reale = [r1, r2, r3]
            pts = 0
            for i in range(3):
                if scelta[i] == reale[i]: pts += 25
                elif scelta[i] in reale: pts += 10
            if scelta == reale: 
                pts += 20
                st.session_state.classifica[target]["EnPlein"] += 1
                st.balloons()
            st.session_state.classifica[target]["Punti"] += pts
            salva_dati()
            st.success("Dati aggiornati e salvati online!")
            st.rerun()
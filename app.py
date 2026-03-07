import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import time

# 1. Configurazione Pagina
st.set_page_config(page_title="Fantapodio F1 2026", layout="wide")
st.title("🏎️ Fantapodio F1 - Inserisci il tuo Pronostico")

# 2. Autenticazione (Usa i tuoi vecchi Secrets!)
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)

# 3. Apertura Foglio
try:
    # Apre il foglio usando l'URL nei tuoi Secrets
    sheet = client.open_by_url(st.secrets["spreadsheet"]).worksheet("Classifica")
    data = sheet.get_all_records()
    df_classifica = pd.DataFrame(data)
except Exception as e:
    st.error(f"Errore di collegamento: {e}")
    st.stop()

# --- SIDEBAR: CLASSIFICA ---
st.sidebar.header("🏆 Classifica Generale")
if not df_classifica.empty:
    # Mostriamo solo Team e Punti
    df_display = df_classifica[['Team', 'Punti']].copy()
    # Converte i punti in numeri per l'ordinamento
    df_display['Punti'] = pd.to_numeric(df_display['Punti'], errors='coerce').fillna(0)
    st.sidebar.table(df_display.sort_values(by="Punti", ascending=False))
else:
    st.sidebar.write("In attesa dei primi pronostici...")

# --- FORM DI INSERIMENTO ---
st.subheader("Compila il tuo podio")
piloti = ["- Seleziona -", "Verstappen", "Hamilton", "Leclerc", "Norris", "Piastri", "Russell", "Sainz", "Alonso", "Perez", "Gasly", "Bearman"]

with st.form("form_pronostico", clear_on_submit=False):
    nome_team = st.text_input("Nome del tuo Team:")
    p1 = st.selectbox("1° Posto:", piloti)
    p2 = st.selectbox("2° Posto:", piloti)
    p3 = st.selectbox("3° Posto:", piloti)
    
    submit = st.form_submit_button("Invia Pronostico")

    if submit:
        if nome_team == "" or p1 == "- Seleziona -" or p2 == "- Seleziona -" or p3 == "- Seleziona -":
            st.error("⚠️ Compila tutti i campi!")
        elif p1 == p2 or p1 == p3 or p2 == p3:
            st.error("⚠️ Non puoi scegliere lo stesso pilota due volte!")
        else:
            # Salvataggio riga: Team, Punti (0), EnPlein (0), P1, P2, P3
            nuova_riga = [nome_team, 0, 0, p1, p2, p3]
            sheet.append_row(nuova_riga)
            
            st.success(f"✅ Inviato! Bravo {nome_team}!")
            
            # IL RESET DEFINITIVO: Aspetta e ricarica
            time.sleep(2)
            st.rerun()

import streamlit as st
import pandas as pd
from gspread_pandas import Spread
import time

# 1. Configurazione Pagina
st.set_page_config(page_title="Fantapodio F1 2026", layout="wide")
st.title("🏎️ Fantapodio F1 - Inserisci il tuo Pronostico")

# 2. Collegamento a Google Sheets (Usa i tuoi Secrets già salvati)
try:
    # Il nome 'Classifica' deve corrispondere alla linguetta del tuo foglio
    spread = Spread(st.secrets["spreadsheet"], sheet="Classifica")
    df_classifica = spread.sheet_to_df(index=None)
except Exception as e:
    st.error("Errore di collegamento al foglio Google. Verifica i Secrets!")
    st.stop()

# --- SIDEBAR: CLASSIFICA ---
st.sidebar.header("🏆 Classifica Generale")
if not df_classifica.empty:
    # Ordiniamo per Punti (Assicurati che la colonna si chiami 'Punti' nel foglio)
    df_display = df_classifica[['Team', 'Punti']].copy()
    df_display['Punti'] = pd.to_numeric(df_display['Punti'], errors='coerce').fillna(0)
    st.sidebar.table(df_display.sort_values(by="Punti", ascending=False))
else:
    st.sidebar.write("In attesa dei primi pronostici...")

# --- FORM DI INSERIMENTO ---
st.subheader("Compila il tuo podio")

piloti = ["- Seleziona -", "Verstappen", "Hamilton", "Leclerc", "Norris", "Piastri", "Russell", "Sainz", "Alonso"]

with st.form("form_pronostico"):
    nome_team = st.text_input("Nome del tuo Team:")
    p1 = st.selectbox("1° Posto:", piloti)
    p2 = st.selectbox("2° Posto:", piloti)
    p3 = st.selectbox("3° Posto:", piloti)
    
    submit = st.form_submit_button("Invia Pronostico")

    if submit:
        if nome_team == "" or p1 == "- Seleziona -" or p2 == "- Seleziona -" or p3 == "- Seleziona -":
            st.error("⚠️ Errore: Compila tutti i campi!")
        elif p1 == p2 or p1 == p3 or p2 == p3:
            st.error("⚠️ Errore: Non puoi selezionare lo stesso pilota più volte!")
        else:
            # SALVATAGGIO DATI
            nuova_riga = [nome_team, 0, 0, p1, p2, p3] # Team, Punti, EnPlein, Piloti...
            
            # Aggiungiamo la riga al foglio Google
            spread.df_to_sheet(pd.DataFrame([nuova_riga]), index=False, header=False, start="A2", replace=False)
            
            st.success(f"✅ Ottimo! Pronostico inviato per il team {nome_team}!")
            
            # IL RESET SICURO: Aspetta 2 secondi e ricarica l'app
            time.sleep(2)
            st.rerun()

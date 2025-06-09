# app.py - Progetto Business Plan Pro - versione 1.1 - 2025-06-08
import streamlit as st
import sqlite3
import pandas as pd
import sidebar_filtri 

st.set_page_config(page_title="Business Plan Pro", layout="wide")

sidebar_filtri.display_sidebar_filters()

st.title("📊 Business Plan Pro")
st.markdown("---")

st.markdown("## Benvenuto nell'applicazione per la gestione e analisi del Business Plan")
st.markdown("Usa il menu a sinistra per navigare tra le diverse sezioni:")
st.markdown("- **Inserisci:** Aggiungi nuovi dati al tuo database.")
st.markdown("- **Visualizza:** Esplora i dati esistenti con filtri interattivi.")
st.markdown("- **Modifica:** Aggiorna o elimina record specifici.")
st.markdown("- **Report Conto Economico:** Visualizza il bilancio riclassificato del Conto Economico.")
st.markdown("- **Report Stato Patrimoniale:** Visualizza il bilancio riclassificato dello Stato Patrimoniale.")
st.markdown("I filtri globali nella sidebar a sinistra si applicano a tutte le pagine che li utilizzano.")
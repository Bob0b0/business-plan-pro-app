# app.py - Progetto Business Plan Pro - versione 1.3 - 2025-06-21
import streamlit as st
import sqlite3
import pandas as pd
import sidebar_filtri 

st.set_page_config(page_title="Business Plan Pro", layout="wide")

# --- CSS per abilitare lo scrolling orizzontale in tutta l'app ---
# Questo blocco era presente in sidebar_filtri.py o app.py e lo reintegriamo qui.
st.markdown("""
<style>
/* Abilita scroll orizzontale per l'intera app se il contenuto lo richiede */
.main .block-container {
    max-width: none !important;
    overflow-x: auto !important; /* Questo è il cruciale per lo scrolling orizzontale */
    padding-left: 1rem; /* Manteniamo un padding di base */
    padding-right: 1rem; /* Manteniamo un padding di base */
}

/* Assicura che le tabelle Streamlit native (st.dataframe, st.table) supportino lo scrolling */
.stDataFrame, .stTable {
    overflow-x: auto !important;
    width: 100% !important; /* Rende la tabella larga quanto il contenitore per poi scrollare */
}

/* Miglioramento scroll per data_editor (se deciderai di usarlo in futuro) */
.stDataEditor > div {
    overflow-x: auto !important;
    width: 100% !important;
}

/* Assicura che il contenitore principale dell'app permetta lo scroll se il contenuto va oltre */
.stApp {
    overflow-x: auto !important;
}

/* Puoi decidere di rimettere il font Consolas qui se lo desideri per tutti i report */
/*
.report-font {
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 14px;
    white-space: pre;
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: 5px;
    border: 1px solid #e9ecef;
    overflow-x: auto;
    line-height: 1.2;
}
.stCode > div {
    font-family: 'Consolas', 'Courier New', monospace !important;
    font-size: 14px !important;
}
.stText {
    font-family: 'Consolas', 'Courier New', monospace !important;
}
*/
</style>
""", unsafe_allow_html=True)

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
st.markdown("- **Report Flussi Finanziari:** Analizza i flussi di cassa aziendali.") 
st.markdown("- **Business Plan:** Attraverso una procedura guidata consente la creazione di un business plan prospettico sulla base dei dati storici di partenza e sulle assumption decise dall'utente.") 

st.markdown("I filtri globali nella sidebar a sinistra si applicano a tutte le pagine che li utilizzano.")

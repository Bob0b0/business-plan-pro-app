# app.py - Progetto Business Plan Pro - versione 1.3 - 2025-06-21
import streamlit as st
import sqlite3
import pandas as pd
import sidebar_filtri 
from auth import AuthManager, get_current_database

st.set_page_config(page_title="Business Plan Pro", layout="wide")

# Controllo autenticazione
if 'authenticated' in st.session_state and st.session_state.authenticated:
    
    # --- CSS per abilitare lo scrolling orizzontale in tutta l'app ---
    st.markdown("""
    <style>
    .main .block-container {
        max-width: none !important;
        overflow-x: auto !important;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .stDataFrame, .stTable {
        overflow-x: auto !important;
        width: 100% !important;
    }
    .stDataEditor > div {
        overflow-x: auto !important;
        width: 100% !important;
    }
    .stApp {
        overflow-x: auto !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Info utente in sidebar + logout
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"👤 **Utente:** {st.session_state.username}")
        st.markdown(f"📧 {st.session_state.email}")
        st.markdown(f"🗃️ **Database:** {get_current_database()}")
        
        if st.button("🚪 Logout", use_container_width=True):
            # Pulisce la sessione
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        st.markdown("---")

    # Mostra filtri sidebar
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

    # Mostra statistiche database utente
    with st.expander("📊 I tuoi dati"):
        try:
            conn = sqlite3.connect(get_current_database())
            
            # Conta record nelle tabelle principali
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM righe")
            count_righe = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM bp_scenarios")
            count_scenarios = cursor.fetchone()[0]
            
            conn.close()
            
            st.write(f"📋 Record bilanci: {count_righe}")
            st.write(f"🎯 Scenari business plan: {count_scenarios}")
            
            if count_righe == 0:
                st.info("Il tuo database è vuoto. Inizia aggiungendo alcuni dati nella sezione 'Inserisci'!")
                
        except Exception as e:
            st.error(f"Errore nel leggere il database: {e}")

else:
    # Se non autenticato, mostra sistema di login
    from auth import main_auth
    main_auth()
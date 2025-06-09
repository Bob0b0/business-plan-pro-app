# sidebar_filtri.py - Progetto Business Plan Pro - versione 1.2 - 2025-06-08
import streamlit as st
import sqlite3
import pandas as pd

DATABASE_NAME = "business_plan_pro.db"

def display_sidebar_filters():
    # Inizializza session_state per i filtri se non esistono già
    if 'selected_cliente' not in st.session_state:
        st.session_state.selected_cliente = "Tutti"
    if 'selected_anni' not in st.session_state:
        st.session_state.selected_anni = []
    if 'selected_sezione' not in st.session_state:
        st.session_state.selected_sezione = "Tutti"
    
    # Aggiungi st.session_state.anni_tutti_disponibili
    if 'anni_tutti_disponibili' not in st.session_state:
        st.session_state.anni_tutti_disponibili = []


    conn = sqlite3.connect(DATABASE_NAME)

    try:
        clienti_disponibili = pd.read_sql_query("SELECT DISTINCT cliente FROM righe", conn)["cliente"].tolist()
    except pd.io.sql.DatabaseError:
        clienti_disponibili = []
        st.sidebar.warning("Tabella 'righe' non trovata o vuota per i filtri cliente.")

    try:
        anni_disponibili_from_db = [str(a) for a in pd.read_sql_query("SELECT DISTINCT anno FROM righe", conn)["anno"].tolist()]
        # Unisci anni dal DB e un range fisso per coprire anni futuri/passati
        anni_tutti_disponibili_temp = sorted(list(set(anni_disponibili_from_db + [str(y) for y in range(2022, 2035)]))) # Esteso il range per sicurezza
        st.session_state.anni_tutti_disponibili = anni_tutti_disponibili_temp # SALVA IN SESSION_STATE
    except pd.io.sql.DatabaseError:
        st.session_state.anni_tutti_disponibili = [str(y) for y in range(2022, 2035)] # SALVA IN SESSION_STATE
        st.sidebar.warning("Tabella 'righe' non trovata o vuota per i filtri anno.")

    try:
        sezioni_disponibili = pd.read_sql_query("SELECT DISTINCT Sezione FROM conti", conn)["Sezione"].tolist()
    except pd.io.sql.DatabaseError:
        sezioni_disponibili = []
        st.sidebar.warning("Tabella 'conti' non trovata o vuota per i filtri sezione.")

    conn.close()

    st.sidebar.header("Filtri Globali")

    st.session_state.selected_cliente = st.sidebar.selectbox(
        "Seleziona Cliente",
        ["Tutti"] + sorted(clienti_disponibili),
        key="global_cliente_sidebar"
    )

    st.session_state.selected_anni = st.sidebar.multiselect(
        "Seleziona Anni (per report)",
        options=sorted(st.session_state.anni_tutti_disponibili, reverse=True), # Usa quelli salvati
        default=st.session_state.selected_anni if st.session_state.selected_anni else ([max(st.session_state.anni_tutti_disponibili)] if st.session_state.anni_tutti_disponibili else []) ,
        key="global_anni_sidebar"
    )

    st.session_state.selected_sezione = st.sidebar.selectbox(
        "Seleziona Sezione",
        ["Tutti"] + sorted(sezioni_disponibili),
        key="global_sezione_sidebar"
    )
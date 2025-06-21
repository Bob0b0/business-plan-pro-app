# sidebar_filtri.py - Progetto Business Plan Pro - versione aggiornata
# Sidebar con persistenza filtri e migliorata reattività

import streamlit as st
import sqlite3
import pandas as pd

# Nome del database
DATABASE_NAME = "business_plan_pro.db"

def display_sidebar_filters():
    """
    Mostra i filtri nella sidebar con persistenza dello stato
    """
    # ✅ CSS per abilitare scroll orizzontale in tutta l'app
 
    st.sidebar.title("🔍 Filtri")

    # Inizializza session_state per i filtri se non esistono
    if 'sidebar_initialized' not in st.session_state:
        st.session_state.sidebar_initialized = True
        # Imposta valori di default solo al primo caricamento
        if 'selected_cliente' not in st.session_state:
            st.session_state.selected_cliente = 'Tutti'
        if 'selected_anni' not in st.session_state:
            st.session_state.selected_anni = []
        if 'selected_sezione' not in st.session_state:
            st.session_state.selected_sezione = 'Tutte'

    # Sezione Cliente
    st.sidebar.subheader("👤 Cliente")
    
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        df_clienti = pd.read_sql_query("SELECT DISTINCT cliente FROM righe ORDER BY cliente", conn)
        clienti_list = ['Tutti'] + df_clienti['cliente'].tolist()
        conn.close()
        
        # Trova l'indice del cliente attualmente selezionato
        current_cliente_index = 0
        if st.session_state.selected_cliente in clienti_list:
            current_cliente_index = clienti_list.index(st.session_state.selected_cliente)
        
        # Selectbox con valore persistente
        selected_cliente = st.sidebar.selectbox(
            "Seleziona Cliente:",
            clienti_list,
            index=current_cliente_index,
            key="cliente_selectbox"
        )
        
        # Aggiorna session_state solo se è cambiato
        if selected_cliente != st.session_state.selected_cliente:
            st.session_state.selected_cliente = selected_cliente
            # Reset degli anni quando cambia cliente
            st.session_state.selected_anni = []
        
    except Exception as e:
        st.sidebar.error(f"Errore nel caricamento clienti: {e}")
        st.session_state.selected_cliente = 'Tutti'

    # Sezione Anno con migliorata reattività
    st.sidebar.subheader("📅 Anno")
    
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        
        # Query condizionale per anni in base al cliente selezionato
        if st.session_state.selected_cliente == 'Tutti':
            df_anni = pd.read_sql_query(
                "SELECT DISTINCT anno FROM righe ORDER BY anno DESC", 
                conn
            )
        else:
            df_anni = pd.read_sql_query(
                "SELECT DISTINCT anno FROM righe WHERE cliente = ? ORDER BY anno DESC", 
                conn, 
                params=[st.session_state.selected_cliente]
            )
        
        anni_disponibili = [str(anno) for anno in df_anni['anno'].tolist()]
        conn.close()
        
        if anni_disponibili:
            # Filtra gli anni selezionati per mantenere solo quelli disponibili
            anni_selezionati_validi = [anno for anno in st.session_state.selected_anni if anno in anni_disponibili]
            
            # Se non ci sono anni selezionati validi, seleziona l'anno più recente
            if not anni_selezionati_validi and anni_disponibili:
                anni_selezionati_validi = [anni_disponibili[0]]
            
            # Multiselect con stato persistente e migliorata UX
            selected_anni = st.sidebar.multiselect(
                "Seleziona Anni:",
                anni_disponibili,
                default=anni_selezionati_validi,
                key="anni_multiselect",
                help="💡 Tip: Gli anni più recenti sono in cima alla lista"
            )
            
            # Aggiorna session_state
            st.session_state.selected_anni = selected_anni
            
            # Shortcut per selezione rapida
            col1, col2 = st.sidebar.columns(2)
            
            with col1:
                if st.button("📅 Ultimo", help="Seleziona solo l'anno più recente", use_container_width=True):
                    st.session_state.selected_anni = [anni_disponibili[0]]
                    st.rerun()
            
            with col2:
                if st.button("📊 Tutti", help="Seleziona tutti gli anni disponibili", use_container_width=True):
                    st.session_state.selected_anni = anni_disponibili
                    st.rerun()
        else:
            st.sidebar.warning("⚠️ Nessun anno disponibile")
            st.session_state.selected_anni = []
            
    except Exception as e:
        st.sidebar.error(f"Errore nel caricamento anni: {e}")
        st.session_state.selected_anni = []

    # Sezione Sezione (per retrocompatibilità)
    st.sidebar.subheader("📋 Sezione")
    
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        
        # Query per sezioni
        if st.session_state.selected_cliente == 'Tutti':
            df_sezioni = pd.read_sql_query(
                "SELECT DISTINCT c.Sezione FROM conti c JOIN righe r ON c.id_co = r.Id_co ORDER BY c.Sezione", 
                conn
            )
        else:
            df_sezioni = pd.read_sql_query(
                "SELECT DISTINCT c.Sezione FROM conti c JOIN righe r ON c.id_co = r.Id_co WHERE r.cliente = ? ORDER BY c.Sezione", 
                conn, 
                params=[st.session_state.selected_cliente]
            )
        
        sezioni_list = ['Tutte'] + df_sezioni['Sezione'].tolist()
        conn.close()
        
        # Trova l'indice della sezione attualmente selezionata
        current_sezione_index = 0
        if st.session_state.selected_sezione in sezioni_list:
            current_sezione_index = sezioni_list.index(st.session_state.selected_sezione)
        
        # Selectbox con valore persistente
        selected_sezione = st.sidebar.selectbox(
            "Seleziona Sezione:",
            sezioni_list,
            index=current_sezione_index,
            key="sezione_selectbox"
        )
        
        # Aggiorna session_state solo se è cambiato
        if selected_sezione != st.session_state.selected_sezione:
            st.session_state.selected_sezione = selected_sezione
        
    except Exception as e:
        st.sidebar.error(f"Errore nel caricamento sezioni: {e}")
        st.session_state.selected_sezione = 'Tutte'

    # Informazioni filtri applicati
    st.sidebar.markdown("---")
    st.sidebar.subheader("ℹ️ Filtri Attivi")
    
    # Mostra riepilogo filtri con colori
    if st.session_state.selected_cliente != 'Tutti':
        st.sidebar.success(f"👤 **{st.session_state.selected_cliente}**")
    else:
        st.sidebar.info("👥 **Tutti i clienti**")
    
    if st.session_state.selected_anni:
        anni_str = ", ".join(st.session_state.selected_anni)
        if len(anni_str) > 20:
            anni_str = f"{anni_str[:20]}..."
        st.sidebar.success(f"📅 **{anni_str}**")
    else:
        st.sidebar.warning("⚠️ **Nessun anno**")
    
    if st.session_state.selected_sezione != 'Tutte':
        st.sidebar.success(f"📋 **{st.session_state.selected_sezione}**")
    else:
        st.sidebar.info("📋 **Tutte le sezioni**")
    
    # Pulsante reset filtri
    if st.sidebar.button("🔄 Reset", help="Ripristina tutti i filtri", use_container_width=True):
        st.session_state.selected_cliente = 'Tutti'
        st.session_state.selected_anni = []
        st.session_state.selected_sezione = 'Tutte'
        st.rerun()
    
    # Salva anche in variabili globali per tutti gli anni disponibili
    st.session_state.anni_tutti_disponibili = anni_disponibili


def get_current_filters():
    """
    Restituisce i filtri attualmente selezionati
    """
    return {
        'cliente': st.session_state.get('selected_cliente', 'Tutti'),
        'anni': st.session_state.get('selected_anni', []),
        'sezione': st.session_state.get('selected_sezione', 'Tutte')
    }


def set_filters(cliente=None, anni=None, sezione=None):
    """
    Imposta i filtri programmaticamente
    """
    if cliente is not None:
        st.session_state.selected_cliente = cliente
    if anni is not None:
        st.session_state.selected_anni = anni
    if sezione is not None:
        st.session_state.selected_sezione = sezione

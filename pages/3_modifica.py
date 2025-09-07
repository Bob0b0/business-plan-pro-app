# pages/modifica.py - Progetto Business Plan Pro - versione 1.0 - 2025-06-06
import streamlit as st
import sqlite3
import pandas as pd
import sidebar_filtri # Importa il modulo della sidebar per i filtri globali

# Chiama la funzione per visualizzare i filtri nella sidebar (saranno sempre visibili)
sidebar_filtri.display_sidebar_filters()

# Nome del database
def get_database_name():
    """Restituisce il database dell'utente corrente"""
    username = st.session_state.get('username')
    if username:
        return f"business_plan_{username}.db"
    return "business_plan_pro.db"

DATABASE_NAME = get_database_name()
st.title("✏️ Modifica o Cancella Record")

conn = sqlite3.connect(DATABASE_NAME)

# Recupera l'ID del record dalla session_state, se presente (se veniamo da visualizza.py)
record_id_from_session = st.session_state.get('record_to_modify_id')
current_record_id_selected = None # Variabile per tenere traccia dell'ID effettivamente selezionato nel selectbox

# Recupera tutti i record per il selectbox, ordinati per ID
try:
    # Seleziona anche 'Id_co' perché è un campo del record da modificare
    df_righe_all = pd.read_sql_query("SELECT ID, cliente, anno, importo, Id_co FROM righe ORDER BY ID ASC", conn)
except pd.io.sql.DatabaseError:
    df_righe_all = pd.DataFrame(columns=['ID', 'cliente', 'anno', 'importo', 'Id_co']) # Crea un DataFrame vuoto
    st.warning("Tabella 'righe' non trovata o vuota.")


if not df_righe_all.empty:
    # Prepara le opzioni per il selectbox in un formato leggibile
    # Es: "ID - Cliente (Anno) - € Importo Formattato"
    options_for_selectbox = [
        f"{row['ID']} - {row['cliente']} ({row['anno']}) - € {int(row['importo']):,}".replace(",", "X").replace(".", ",").replace("X", ".")
        for index, row in df_righe_all.iterrows()
    ]
    
    # --- Gestione del default_index per la pre-selezione ---
    default_index_for_selectbox = 0 # Inizializza a 0 (prima opzione: "Seleziona un record...")
    if record_id_from_session is not None:
        # Cerca l'indice della riga nel DataFrame corrispondente all'ID passato dalla sessione
        idx_in_df = df_righe_all[df_righe_all['ID'] == record_id_from_session].index
        if not idx_in_df.empty:
            # L'indice del selectbox sarà l'indice nel DataFrame + 1 (per l'opzione "Seleziona...")
            default_index_for_selectbox = int(idx_in_df[0]) + 1
        else:
            # Se l'ID dalla sessione non è valido (es. record cancellato), resetta la session_state
            st.session_state.record_to_modify_id = None
            default_index_for_selectbox = 0 # Torna alla selezione predefinita
    
    # Aggiungi l'opzione iniziale "Seleziona un record..."
    display_options_with_placeholder = ["Seleziona un record per modificarlo..."] + options_for_selectbox

    selected_option_str = st.selectbox(
        "Scegli un record da modificare o cancellare:",
        display_options_with_placeholder,
        index=default_index_for_selectbox, # Usa l'indice calcolato
        key="mod_record_selection_selectbox",
    )

    if selected_option_str != "Seleziona un record per modificarlo...":
        current_record_id_selected = int(selected_option_str.split(" - ")[0])
    else:
        current_record_id_selected = None

else:
    st.warning("Nessun record disponibile nella tabella 'righe' per la modifica.")
    current_record_id_selected = None

# Procedi solo se un record è stato effettivamente selezionato
if current_record_id_selected:
    # Recupera i dati del record specifico usando l'ID selezionato dal selectbox
    # Usiamo df_righe_all che abbiamo già caricato
    df_record_to_edit = df_righe_all[df_righe_all['ID'] == current_record_id_selected]
    
    if not df_record_to_edit.empty:
        record = df_record_to_edit.iloc[0]

        # Recupera i conti disponibili per il selectbox di Id_co
        try:
            df_conti = pd.read_sql_query("SELECT id_co, Conto, Sezione FROM conti", conn)
            conti_options_map = {row["Conto"]: row["id_co"] for index, row in df_conti.iterrows()}
            conti_names = sorted(conti_options_map.keys())
        except pd.io.sql.DatabaseError:
            conti_names = []
            st.warning("Tabella 'conti' non trovata o vuota.")

        st.subheader(f"Modifica Record ID: {current_record_id_selected}")

        edited_cliente = st.text_input("Cliente", value=record["cliente"], key="mod_cliente")
        edited_anno = st.number_input("Anno", value=int(record["anno"]), step=1, key="mod_anno")
        edited_importo = st.number_input("Importo", value=int(record["importo"]), step=1, format="%d", key="mod_importo") # Importo è INTEGER

        # Selezione del Conto collegato (Id_co)
        current_id_co = record["Id_co"]
        
        # Trova il nome del Conto corrispondente all'id_co corrente del record
        current_conto_name = None
        if not df_conti.empty:
            conto_match = df_conti[df_conti["id_co"] == current_id_co]
            if not conto_match.empty:
                current_conto_name = conto_match["Conto"].iloc[0]

        selected_conto_name = st.selectbox(
            "Collega a Conto",
            conti_names,
            index=conti_names.index(current_conto_name) if current_conto_name in conti_names else 0,
            key="mod_conto_page"
        )
        edited_id_co = conti_options_map.get(selected_conto_name) # Usa .get per sicurezza

        # Pulsante Aggiorna
        if st.button("Aggiorna Record", key="btn_update_page"):
            if edited_id_co is None:
                st.error("Seleziona un Conto valido per l'aggiornamento.")
            else:
                try:
                    conn.execute("UPDATE righe SET cliente=?, anno=?, importo=?, Id_co=? WHERE ID=?",
                                 (edited_cliente, edited_anno, edited_importo, edited_id_co, current_record_id_selected))
                    conn.commit()
                    st.success("Record aggiornato con successo.")
                    st.session_state.record_to_modify_id = None # Resetta l'ID
                    st.switch_page("pages/2_visualizza.py") # Torna alla pagina di visualizzazione
                except sqlite3.Error as e:
                    st.error(f"Errore durante l'aggiornamento: {e}")

        st.markdown("---")
        st.subheader("Cancella Record")
        # Pulsante Elimina
        if st.button("Elimina Record", help="Questa azione non può essere annullata.", key="btn_delete_page"):
            try:
                conn.execute("DELETE FROM righe WHERE ID=?", (current_record_id_selected,))
                conn.commit()
                st.success("Record eliminato con successo.")
                st.session_state.record_to_modify_id = None # Resetta l'ID
                st.switch_page("pages/2_visualizza.py") # Torna alla pagina di visualizzazione
            except sqlite3.Error as e:
                st.error(f"Errore durante l'eliminazione: {e}")
    else:
        st.warning("Il record selezionato non è stato trovato nel database. Potrebbe essere stato eliminato di recente.")
        st.session_state.record_to_modify_id = None # Resetta l'ID per evitare loop
        if st.button("Torna alla Visualizzazione", key="mod_return_to_view"):
            st.switch_page("pages/2_visualizza.py")
else:
    st.info("Seleziona un record dal menu a discesa qui sopra.")
    if st.button("Vai a Visualizza Record", key="mod_go_to_view_if_no_selection"):
        st.switch_page("pages/2_visualizza.py")

conn.close()
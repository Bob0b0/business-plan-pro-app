# pages/inserisci.py - Progetto Business Plan Pro - versione 1.0 - 2025-06-06
import streamlit as st
import sqlite3
import pandas as pd
import sidebar_filtri # Importa il modulo della sidebar per i filtri globali

# Chiama la funzione per visualizzare i filtri nella sidebar (saranno sempre visibili)
sidebar_filtri.display_sidebar_filters()

# Nome del database (deve corrispondere a quello definito in sidebar_filtri.py)
DATABASE_NAME = "business_plan_pro.db"

st.title("➕ Nuovo Inserimento")

conn = sqlite3.connect(DATABASE_NAME)

# --- Recupero dati per i Selectbox ---

# Per Cliente: recupera i clienti esistenti dalla tabella 'righe'
try:
    clienti_esistenti = pd.read_sql_query("SELECT DISTINCT cliente FROM righe", conn)["cliente"].tolist()
    clienti_options = sorted(clienti_esistenti) + ["Aggiungi nuovo cliente..."]
except pd.io.sql.DatabaseError:
    clienti_options = ["Aggiungi nuovo cliente..."] # Se la tabella non esiste
    st.warning("Tabella 'righe' non trovata. Creare record inserirà la prima riga.")

# Per Anno: recupera gli anni esistenti dalla tabella 'righe' e aggiunge un range
try:
    anni_esistenti = pd.read_sql_query("SELECT DISTINCT anno FROM righe", conn)["anno"].tolist()
    anni_options_base = sorted(list(set([str(a) for a in anni_esistenti])))
except pd.io.sql.DatabaseError:
    anni_options_base = [] # Se la tabella non esiste

anni_options_range = [str(year) for year in range(2021, 2035)] # Range ampliato: dal 2021 al 2034
anni_options = sorted(list(set(anni_options_base + anni_options_range)))


# Per Conto: recupera i conti esistenti dalla tabella 'conti'
try:
    # Ordina per id_co
    conti_disponibili = pd.read_sql_query("SELECT id_co, Conto, Sezione FROM conti ORDER BY id_co ASC", conn)
    # Creiamo un dizionario per mappare la stringa visualizzata all'id_co effettivo
    conto_display_to_id_co = {}
    conto_display_options = []
    for index, row in conti_disponibili.iterrows():
        display_string = f"({row['id_co']}) {row['Conto']}"
        conto_display_options.append(display_string)
        conto_display_to_id_co[display_string] = row['id_co']

    conti_names_sorted_by_id = sorted(conto_display_options) # Già ordinato per id_co grazie alla query SQL

except pd.io.sql.DatabaseError:
    conti_names_sorted_by_id = []
    st.warning("Tabella 'conti' non trovata o vuota. Inserire un Conto valido è necessario.")


# --- Form di Inserimento ---
with st.form("inserisci_form"):
    st.subheader("Dati per la riga di bilancio")

    # Selectbox per Cliente
    selected_cliente = st.selectbox("Cliente", clienti_options, key="cliente_input")
    if selected_cliente == "Aggiungi nuovo cliente...":
        cliente_final = st.text_input("Inserisci nuovo nome Cliente", key="new_cliente_text_input")
    else:
        cliente_final = selected_cliente

    # Selectbox per Anno
    selected_anno = st.selectbox("Anno", anni_options, key="anno_input")
    anno_final = int(selected_anno) # Converti in int

    # Selectbox per Conto (collegato a id_co)
    if not conti_names_sorted_by_id:
        st.error("Nessun conto disponibile nel database 'conti'. Assicurati di aver popolato la tabella 'conti'.")
        id_co_final = None
    else:
        selected_conto_display = st.selectbox("Conto", conti_names_sorted_by_id, key="conto_input")
        id_co_final = conto_display_to_id_co.get(selected_conto_display) # Ottieni l'id_co corrispondente

    importo = st.number_input("Importo", step=1, format="%d", key="importo_input") # Importo è INTEGER


    submitted = st.form_submit_button("Inserisci Record")

    if submitted:
        # Validazione finale per il nuovo cliente
        if selected_cliente == "Aggiungi nuovo cliente..." and not cliente_final:
            st.warning("Il campo per il nuovo cliente non può essere vuoto.")
        elif id_co_final is None:
            st.error("Seleziona un Conto valido per l'inserimento.")
        elif cliente_final and anno_final is not None and importo is not None:
            try:
                # Esegui la query per l'inserimento nella tabella 'righe'
                # L'ID (primary key) dovrebbe essere gestito automaticamente dal DB (AUTOINCREMENT)
                # Se il tuo ID non è AUTOINCREMENT, dovrai generarlo qui (es. MAX(ID) + 1)
                conn.execute("INSERT INTO righe (cliente, anno, importo, Id_co) VALUES (?, ?, ?, ?)",
                             (cliente_final, anno_final, importo, id_co_final))
                conn.commit()
                st.success("Record inserito con successo.")
                st.rerun() # Ricarica la pagina per resettare il form e aggiornare i selectbox
            except sqlite3.Error as e:
                st.error(f"Errore nell'inserimento del record: {e}. Assicurati che le tabelle esistano e che i tipi di dato siano corretti.")
        else:
            st.warning("Compila tutti i campi obbligatori.")

conn.close()
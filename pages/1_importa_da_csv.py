# 05_Importa_da_CSV.py - Versione 1 - 2025-06-16

import streamlit as st
import pandas as pd
import sqlite3
import io

st.title("📥 Importa bilancio da file CSV")

st.markdown("""
Carica un file `.csv` generato da ChatGPT o da altri strumenti, contenente le colonne:
- `cliente`
- `anno`
- `codice`
- `descrizione`
- `importo`
""")

file = st.file_uploader("Carica il file CSV", type=["csv"])

if file:
    try:
        df = pd.read_csv(file)
    except Exception as e:
        st.error(f"Errore nella lettura del CSV: {e}")
        st.stop()

    richieste = {"cliente", "anno", "codice", "importo"}
    colonne_presenti = set(df.columns.str.lower())

    if not richieste.issubset(colonne_presenti):
        st.error("Il file deve contenere almeno le colonne: cliente, anno, codice, importo")
        st.stop()

    df.columns = df.columns.str.lower()
    df = df[["cliente", "anno", "codice", "importo"]]

    st.success("✅ File caricato correttamente. Ecco un'anteprima:")
    st.dataframe(df)

    if st.button("✅ Importa nel database"):
        conn = sqlite3.connect("business_plan_pro.db")
        cur = conn.cursor()
        for _, row in df.iterrows():
            cur.execute("""
                INSERT INTO righe (cliente, anno, Id_co, importo)
                VALUES (?, ?, ?, ?)
            """, (row["cliente"], row["anno"], row["codice"], row["importo"]))
        conn.commit()
        conn.close()
        st.success("🎉 Importazione completata con successo!")

# pages/visualizza.py - Progetto Business Plan Pro - versione 2.5 - 2025-06-21
# Obiettivo: Ripristino logica originale click-per-riga per modifica,
# con ottimizzazione layout per leggibilità colonne.

import streamlit as st
import sqlite3
import pandas as pd
import sidebar_filtri # Importa il modulo della sidebar per i filtri globali
import io
from reportlab.lib.pagesizes import letter, A4, landscape 
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# Chiama la funzione per visualizzare i filtri nella sidebar (saranno sempre visibili)
sidebar_filtri.display_sidebar_filters()

# Nome del database
DATABASE_NAME = "business_plan_pro.db"

# Accesso ai valori dei filtri da session_state
selected_cliente = st.session_state.selected_cliente
selected_anni_list = st.session_state.selected_anni 
selected_sezione = st.session_state.selected_sezione

# --- Titolo con filtri selezionati ---
st.title("📋 Visualizza Record")
st.markdown(f"**Filtri applicati:** Cliente: **{selected_cliente}** | Anni: **{', '.join(selected_anni_list) if selected_anni_list else 'Tutti'}** | Sezione: **{selected_sezione}**")
st.markdown("---")

# Connessione al database
conn = None 
df_filtered = pd.DataFrame() 

try:
    conn = sqlite3.connect(DATABASE_NAME)
    query = """
    SELECT r.ID, r.cliente, r.anno, r.importo, c.Conto, c.Sezione, c.Parte
    FROM righe r
    JOIN conti c ON r.Id_co = c.id_co
    WHERE 1=1
    """
    params = []

    if selected_cliente != "Tutti":
        query += " AND r.cliente = ?"
        params.append(selected_cliente)
    
    if selected_anni_list: 
        years_placeholders = ','.join(['?' for _ in selected_anni_list])
        query += f" AND r.anno IN ({years_placeholders})"
        params.extend([str(y) for y in selected_anni_list]) 

    if selected_sezione != "Tutte": 
        query += " AND c.Sezione = ?"
        params.append(selected_sezione)

    df_filtered = pd.read_sql_query(query, conn, params=params)

except pd.io.sql.DatabaseError as e:
    st.error(f"ERRORE GRAVE NEL CARICAMENTO DEI DATI DAL DATABASE (DatabaseError): {e}")
    st.info("Assicurati che il database 'business_plan_pro.db' sia presente nella cartella principale e che le tabelle 'righe', 'conti', 'ricla' esistano e siano popolari.")
    df_filtered = pd.DataFrame()
except Exception as e:
    st.error(f"ERRORE GENERICO NEL CARICAMENTO DEI DATI: {e}")
    df_filtered = pd.DataFrame()
finally:
    if conn:
        conn.close()

# --- Calcolo Subtotale Importo ---
total_importo = 0
if not df_filtered.empty:
    try:
        df_filtered['importo'] = pd.to_numeric(df_filtered['importo'], errors='coerce').fillna(0).astype(int)
        total_importo = df_filtered['importo'].sum()
    except Exception as e:
        st.warning(f"Impossibile calcolare il subtotale Importo: {e}. Controlla i tipi di dato nella colonna 'importo'.")
        total_importo = 0

# Formattazione del subtotale
total_importo_formatted = f"{int(total_importo):,}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- Visualizzazione Subtotale ---
st.markdown(f"**Subtotale Importo Filtrato:** € {total_importo_formatted}")
st.markdown("---")


# --- Sezione Esportazione (codice invariato) ---
st.subheader("Esporta Dati")
if not df_filtered.empty:
    df_export = df_filtered[['ID', 'cliente', 'anno', 'importo', 'Conto', 'Sezione']].copy()
    df_export = df_export.rename(columns={
        'ID': 'ID Record', 'cliente': 'Cliente', 'anno': 'Anno',
        'importo': 'Importo', 'Conto': 'Nome Conto', 'Sezione': 'Sezione Conto'
    })

    col_excel, col_pdf = st.columns(2)

    with col_excel:
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, index=False, sheet_name='Dati Business Plan')
            workbook = writer.book
            worksheet = writer.sheets['Dati Business Plan']
            num_format = workbook.add_format({'num_format': '#,##0'}) 
            worksheet.set_column('D:D', None, num_format) 

        excel_buffer.seek(0)
        st.download_button(
            label="Esporta in Excel", data=excel_buffer, file_name="business_plan_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Esporta i dati filtrati in un file Excel."
        )

    with col_pdf:
        def generate_pdf(df_data, title, filters_applied):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4) 
            styles = getSampleStyleSheet()
            if 'bold_text' not in styles:
                styles.add(ParagraphStyle(name='bold_text', parent=styles['Normal'], fontName='Helvetica-Bold'))
            if 'normal_text' not in styles:
                styles.add(ParagraphStyle(name='normal_text', parent=styles['Normal'], fontName='Helvetica'))
            if 'right_text' not in styles:
                styles.add(ParagraphStyle(name='right_text', parent=styles['Normal'], alignment=2))  # 2 = right align
            if 'right_bold_text' not in styles:
                styles.add(ParagraphStyle(name='right_bold_text', parent=styles['Normal'], alignment=2, fontName='Helvetica-Bold'))

            story = []

            story.append(Paragraph(title, styles['h2']))
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph(f"<b>Filtri applicati:</b> {filters_applied}", styles['Normal']))
            story.append(Spacer(1, 0.2 * inch))
            
            pdf_cols_to_include = ['ID Record', 'Cliente', 'Anno', 'Nome Conto', 'Sezione Conto', 'Importo']
            df_pdf_ready = df_data[pdf_cols_to_include].copy()

            formatted_data_for_pdf = [df_pdf_ready.columns.tolist()] 
            for row_data in df_pdf_ready.values.tolist(): 
                new_row = []
                for c_idx, cell_value in enumerate(row_data):
                    if pdf_cols_to_include[c_idx] == 'Importo': 
                        try:
                            new_row.append(f"{int(cell_value):,}".replace(",", "X").replace(".", ",").replace("X", "."))
                        except (ValueError, TypeError): 
                            new_row.append(str(cell_value)) 
                    else:
                        new_row.append(str(cell_value))
                formatted_data_for_pdf.append(new_row)

            col_widths_pdf = []
            total_cols = len(pdf_cols_to_include) 
            base_width_per_col = doc.width / total_cols 

            for col_name in pdf_cols_to_include:
                if col_name == 'ID Record': col_widths_pdf.append(base_width_per_col * 0.5)
                elif col_name == 'Anno': col_widths_pdf.append(base_width_per_col * 0.6)
                elif col_name == 'Cliente': col_widths_pdf.append(base_width_per_col * 1.5) 
                elif col_name == 'Nome Conto': col_widths_pdf.append(base_width_per_col * 1.5)
                elif col_name == 'Sezione Conto': col_widths_pdf.append(base_width_per_col * 0.8) 
                elif col_name == 'Importo': col_widths_pdf.append(base_width_per_col * 1.0)
                else: col_widths_pdf.append(base_width_per_col * 1.0) 
            
            sum_widths = sum(col_widths_pdf)
            col_widths_pdf = [w * (doc.width / sum_widths) for w in col_widths_pdf]


            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey), 
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'), 
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), 
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white), 
                ('GRID', (0, 0), (-1, -1), 0.25, colors.white), 
                ('ALIGN', (pdf_cols_to_include.index('Importo'), 0), (pdf_cols_to_include.index('Importo'), -1), 'RIGHT'), 
            ])
            
            table = Table(formatted_data_for_pdf, colWidths=col_widths_pdf) 
            table.setStyle(table_style)
            story.append(table)

            doc.build(story)
            buffer.seek(0)
            return buffer

        pdf_buffer = generate_pdf(df_export, "Report Business Plan Dati", 
                                  f"Cliente: {selected_cliente} | Anni: {', '.join(selected_anni_list) if selected_anni_list else 'Tutti'} | Sezione: {selected_sezione}")
        
        st.download_button(
            label="Esporta in PDF", data=pdf_buffer, file_name="business_plan_data.pdf",
            mime="application/pdf", help="Esporta i dati filtrati in un file PDF."
        )
else:
    st.info("Nessun dato da esportare.")

st.markdown("---") 

# --- CSS per la compattazione e allineamento (modificato per una migliore resa) ---
st.markdown("""
<style>
/* Rimuovi spazio (gap) tra le colonne */
div[data-testid="stHorizontalBlock"] {
    gap: 0.1rem !important; /* Ridotto ulteriormente il gap tra le colonne */
}

/* Allinea il testo a destra per gli importi e gestisci il nowrap/ellipsis */
.text-align-right {
    text-align: right;
    padding-right: 0.2rem; /* Leggero padding a destra */
    white-space: nowrap; /* Impedisce al testo di andare a capo */
    overflow: hidden; /* Nasconde il testo che eccede */
    text-overflow: ellipsis; /* Aggiunge "..." se il testo è troppo lungo */
    /* Assicurati che lo spazio verticale sia allineato */
    display: flex; /* Utilizza flexbox per allineamento interno */
    align-items: center; /* Centra verticalmente il contenuto */
    justify-content: flex-end; /* Allinea a destra il contenuto */
    height: 100%; /* Assicura che la div occupi tutta l'altezza della cella */
}

/* Stile per il pulsante Modifica */
.stButton > button {
    padding: 0.1rem 0.2rem; 
    margin: 0;
    line-height: 1;
    height: 28px;
    min-width: 28px;
    font-size: 0.8em;
    display: flex;
    justify-content: center;
    align-items: center;
}

/* Allinea la colonna delle azioni a destra */
div[data-testid^="stColumn"]:last-child > div > div > div {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    padding-right: 0.1rem;
}

/* Stile per le celle di testo per migliorare la gestione dello spazio */
.text-cell-display {
    white-space: nowrap; /* Impedisce al testo di andare a capo */
    overflow: hidden; /* Nasconde il testo che eccede */
    text-overflow: ellipsis; /* Aggiunge "..." se il testo è troppo lungo */
    /* Allineamento e centering verticalmente per le celle di testo */
    display: flex;
    align-items: center;
    justify-content: flex-start; /* Allinea a sinistra */
    height: 100%;
}

/* Forzare l'allineamento verticale al centro per tutti gli elementi nelle colonne */
/* Questo selettore è più generico e potrebbe aiutare a rendere le righe più uniformi. */
/* Attenzione: selettori Streamlit interni (come st-emotion-cache-...) possono cambiare tra versioni. */
[data-testid^="stColumn"] > div > div > div {
    display: flex;
    align-items: center; /* Centra verticalmente tutto il contenuto delle colonne */
    height: 100%; /* Fa sì che il div interno prenda tutta l'altezza */
}


</style>
""", unsafe_allow_html=True)


# --- Intestazioni della Tabella (con larghezze ottimizzate per la visualizzazione) ---
# Obiettivo: Più spazio per Importo, meno per Conto e Sezione.
# Nuove larghezze relative (basate sul tentativo 2.4, ma con piccoli aggiustamenti)
# Ho aumentato Importo (1.8 -> 2.0), ridotto Conto (1.5 -> 1.2), Sezione (0.7 -> 0.6)
# Bilanciamento: ID(0.4), Anno(0.4), Importo(2.0), Conto(1.2), Sezione(0.6), Azioni(0.5)
# Somma totale di 5.1. La larghezza massima disponibile è 6.0 in Streamlit (se `layout="wide"`)
# Questi valori relativi saranno scalati da Streamlit.
cols_widths = [0.4, 0.4, 2.0, 1.2, 0.6, 0.5] 

header_cols = st.columns(cols_widths)

with header_cols[0]: st.markdown("**ID**")
with header_cols[1]: st.markdown("**Anno**")
with header_cols[2]: st.markdown("<div class='text-align-right'>**Importo**</div>", unsafe_allow_html=True)
with header_cols[3]: st.markdown("**Conto**")
with header_cols[4]: st.markdown("**Sezione**")
with header_cols[5]: st.markdown("<div style='text-align: center'>**Azioni**</div>", unsafe_allow_html=True)

st.markdown("---") # Separatore dopo le intestazioni


# --- Visualizzazione Righe della Tabella ---
if 'last_confirmed_delete_id' not in st.session_state:
    st.session_state.last_confirmed_delete_id = None

if df_filtered.empty:
    st.info("Nessun record trovato con i filtri selezionati.")
else:
    for index, row in df_filtered.iterrows():
        importo_formatted = f"{int(row['importo']):,}".replace(",", "X").replace(".", ",").replace("X", ".")

        col1, col2, col3, col4, col5, col6 = st.columns(cols_widths)
        
        with col1:
            st.write(row['ID'])
        with col2:
            st.write(row['anno'])
        with col3:
            # Applica la classe CSS per gli importi alle celle
            st.markdown(f"<div class='text-align-right'>{importo_formatted}</div>", unsafe_allow_html=True)
        with col4:
            # Applica la nuova classe text-cell-display per i campi di testo
            st.markdown(f"<div class='text-cell-display'>{row['Conto']}</div>", unsafe_allow_html=True)
        with col5:
            # Applica la nuova classe text-cell-display per i campi di testo
            st.markdown(f"<div class='text-cell-display'>{row['Sezione']}</div>", unsafe_allow_html=True)
        
        with col6: # Colonna per il solo pulsante Modifica
            if st.button("✏️", key=f"edit_{row['ID']}", help="Modifica record"):
                st.session_state.record_to_modify_id = row['ID']
                st.switch_page("pages/3_modifica.py")  # Reindirizza alla pagina di modifica
                    
# Reset dello stato di conferma se l'ID non corrisponde più a un record visualizzato
# o se l'utente ha navigato via e torna.
if st.session_state.get('last_confirmed_delete_id') and (df_filtered.empty or st.session_state.last_confirmed_delete_id not in df_filtered['ID'].tolist()):
    st.session_state.last_confirmed_delete_id = None
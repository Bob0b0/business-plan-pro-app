# pages/report_conto_economico.py - Progetto Business Plan Pro - versione 4.1 - 2025-06-10
# Correzione: PDF in formato portrait invece di landscape

import streamlit as st
import sqlite3
import pandas as pd
import sidebar_filtri 
import io
from reportlab.lib.pagesizes import A4, landscape, portrait 
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle 
from reportlab.lib.units import inch
from streamlit.components.v1 import html

# Importa il modulo del modello finanziario centrale
import financial_model 

# ✅ AGGIUNTA: Import ASCII
try:
    from ascii_table_generator import create_downloadable_ascii_report
    ASCII_AVAILABLE = True
except ImportError:
    ASCII_AVAILABLE = False

# Chiama la funzione per visualizzare i filtri nella sidebar
sidebar_filtri.display_sidebar_filters()

# Nome del database
DATABASE_NAME = "business_plan_pro.db"

# Accesso ai valori dei filtri da session_state
selected_cliente = st.session_state.selected_cliente
selected_anni = st.session_state.selected_anni 
selected_sezione = st.session_state.selected_sezione 

# --- Titolo e Intestazione Report ---
st.title("📈 Report Conto Economico")
st.markdown(f"**Filtri applicati:** Cliente: **{selected_cliente}** | Anni: **{', '.join(selected_anni) if selected_anni else 'Tutti'}**")
st.markdown("---") 

# --- Logica per la Selezione Anni (Raffronto) ---
years_to_display = []
if selected_anni:
    years_to_display = sorted([int(y) for y in selected_anni])
    if len(years_to_display) == 1:
        prev_year = years_to_display[0] - 1
        if prev_year >= (min([int(y) for y in st.session_state.anni_tutti_disponibili]) if st.session_state.anni_tutti_disponibili else 0) : 
            years_to_display.insert(0, prev_year)
    years_to_display = sorted(list(set(years_to_display))) 

else: 
    years_to_display = sorted([int(y) for y in st.session_state.anni_tutti_disponibili])

if not years_to_display:
    st.info("Nessun anno disponibile o selezionato per il report.")
    st.stop() 


# Connessione al database e caricamento dati grezzi
conn = None
df_full_data = pd.DataFrame() 

try:
    conn = sqlite3.connect(DATABASE_NAME)
    query = """
    SELECT 
        r.ID, r.cliente, r.anno, r.importo, 
        c.id_co, c.Conto, c.Parte, c.Sezione, c.Ord, c.ID_RI,
        rl.Ricla
    FROM righe r
    JOIN conti c ON r.Id_co = c.id_co
    JOIN ricla rl ON c.ID_RI = rl.ID_RI
    WHERE r.anno IN ({})
    """.format(','.join(['?' for _ in years_to_display]))
    
    params = [str(y) for y in years_to_display]

    if selected_cliente != "Tutti":
        query += " AND r.cliente = ?"
        params.append(selected_cliente)
    
    query += " ORDER BY r.anno, c.Ord, c.ID_RI" 

    df_full_data = pd.read_sql_query(query, conn, params=params)

except Exception as e:
    st.error(f"Errore nel caricamento dei dati grezzi: {e}")
    st.info("Verifica che il database sia popolato e che le tabelle 'righe', 'conti', 'ricla' esistano e siano correlate correttamente.")
    df_full_data = pd.DataFrame()
finally:
    if conn:
        conn.close()

# --- CHIAMATA AL MODELLO FINANZIARIO CENTRALE ---
# Qui si ottengono tutti i DataFrame riclassificati e calcolati
all_calculated_reports = financial_model.calculate_all_reports(
    df_full_data, 
    years_to_display,
    financial_model.report_structure_ce, # Passa le strutture definite in financial_model
    financial_model.report_structure_sp,
    financial_model.report_structure_ff
)

# Ottieni il DataFrame del Conto Economico per la visualizzazione
df_final_display = all_calculated_reports['ce'] 

# --- Visualizzazione della Tabella Riclassificata (Rendering HTML personalizzato) ---
if not df_final_display.empty:
    st.markdown("### Visualizzazione Tabellare")
    
    # Soluzione HTML personalizzata per il rendering della tabella (copiata da SP)
    # df è df_final_display, years è years_to_display, structure è financial_model.report_structure_ce
    def display_with_html(df, years, structure): 
        if df.empty:
            return
        
        # Identifica le righe da formattare (Grassetto, Maiuscolo)
        bold_rows = [item['Voce'] for item in structure if item.get('Grassetto', False)]
        
        # Genera l'HTML della tabella
        html_table = """
        <style>
            .custom-table {
                width: 100%;
                border-collapse: collapse;
                font-family: Arial, sans-serif;
                margin: 1em 0;
            }
            .custom-table th, .custom-table td {
                border: 1px solid #e0e0e0;
                padding: 8px 12px;
                text-align: left;
            }
            .custom-table th {
                background-color: #f0f0f0;
                font-weight: bold;
            }
            .custom-table td.numeric {
                text-align: right;
            }
            .custom-table tr.bold-row td {
                font-weight: bold;
            }
            /* Stile per le voci in maiuscolo (se Maiuscolo è True per la Voce) */
            .custom-table td.uppercase-text {
                text-transform: uppercase;
            }
        </style>
        <table class="custom-table">
            <thead>
                <tr>
        """
        # Intestazioni della tabella
        html_table += "<th>Voce</th>" 
        for year in years:
            html_table += f"<th class='numeric'>{year}</th>" # Anni allineati a destra
        html_table += "</tr></thead><tbody>"
        
        # Righe della tabella
        for _, row in df.iterrows(): 
            row_class = ""
            if row['Voce'] in bold_rows:
                row_class += "bold-row "
            
            html_table += f"<tr class='{row_class.strip()}'>"
            for i, col_name in enumerate(df.columns): 
                cell_value = row[col_name]
                
                cell_content = str(cell_value)
                cell_class = ""
                
                if col_name == 'Voce':
                    # Determina se la voce deve essere in maiuscolo (dalla struttura)
                    item_struct = next((item for item in structure if item['Voce'].upper() == row['Voce'].upper() or item['Voce'] == row['Voce']), None)
                    if item_struct and item_struct.get('Maiuscolo', False):
                        cell_class = "uppercase-text"
                        cell_content = str(row['Voce']) 
                    else:
                        cell_content = str(row['Voce'])
                else: # Colonne numeriche (anni)
                    cell_class = "numeric"
                    # cell_content è già formattato da financial_model.calculate_all_reports
                    cell_content = financial_model.format_number(cell_value) # Usa la funzione di formattazione dal modello
                
                html_table += f"<td class='{cell_class}'>{cell_content}</td>"
            html_table += "</tr>"
        
        html_table += "</tbody></table>"
        
        html(html_table, height=len(df) * 40 + 100, scrolling=True)

    # Chiama la funzione display_with_html
    display_with_html(df_final_display, years_to_display, financial_model.report_structure_ce) # Passa la struttura dal modello

    # --- Esportazione Excel e PDF ---
    st.markdown("---")
    st.subheader("Esporta Conto Economico Riclassificato")

    # Per l'esportazione, prendiamo il DataFrame già pronto da financial_model.calculate_all_reports
    df_export_riclassificato_actual = all_calculated_reports['ce_export'] 
    
    # ✅ MODIFICA: 3 colonne invece di 2
    col_excel_riclass, col_pdf_riclass, col_ascii_riclass = st.columns(3)

    with col_excel_riclass:
        excel_buffer_riclass = io.BytesIO()
        with pd.ExcelWriter(excel_buffer_riclass, engine='xlsxwriter') as writer:
            df_export_riclassificato_actual.to_excel(writer, index=False, sheet_name='Conto Eco Riclass') 
            workbook = writer.book
            worksheet = writer.sheets['Conto Eco Riclass'] 
            
            num_format = workbook.add_format({'num_format': '#,##0'})
            for col_idx, year in enumerate(years_to_display): 
                worksheet.set_column(col_idx + 1, col_idx + 1, None, num_format) 

        excel_buffer_riclass.seek(0)
        st.download_button(
            label="Scarica Conto Economico in Excel",
            data=excel_buffer_riclass,
            file_name="conto_economico_riclassificato.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Esporta il Conto Economico riclassificato in un file Excel."
        )

    with col_pdf_riclass:
        # Funzione generate_pdf_riclassified (CORRETTO: formato portrait)
        def generate_pdf_riclassified(df_data, title, filters_applied): 
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)  # CORREZIONE: Portrait invece di landscape
            styles = getSampleStyleSheet()
            
            # Aggiungi stili personalizzati
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
            
            table_data_pdf = []
            # Intestazioni
            header_row_pdf = []
            for col in df_data.columns:
                if col == 'Voce':
                    header_row_pdf.append(Paragraph(col, styles['bold_text'])) 
                else:
                    header_row_pdf.append(Paragraph(col, styles['right_bold_text'])) 
            table_data_pdf.append(header_row_pdf)

            for index, row in df_data.iterrows():
                row_list = []
                # Trova la voce corrispondente nella struttura CE per i flag Grassetto/Maiuscolo
                # Cerca nel financial_model.report_structure_ce
                structure_item_found = next((item for item in financial_model.report_structure_ce if item['Voce'].upper() == row['Voce'].upper() or item['Voce'] == row['Voce']), None)
                is_bold_row = structure_item_found.get('Grassetto', False) if structure_item_found else False
                is_uppercase_row = structure_item_found.get('Maiuscolo', False) if structure_item_found else False
                
                for col_name in df_data.columns:
                    cell_value = row[col_name]
                    
                    if col_name == 'Voce':
                        voce_content = str(cell_value)
                        if is_uppercase_row:
                            voce_content = voce_content.upper()
                        
                        if is_bold_row:
                            row_list.append(Paragraph(voce_content, styles['bold_text']))
                        else:
                            row_list.append(Paragraph(voce_content, styles['normal_text']))
                    else: # Colonne numeriche (anni)
                        formatted_value = financial_model.format_number(cell_value, pdf_format=True) # Usa la funzione di formattazione dal modello
                        if is_bold_row:
                            row_list.append(Paragraph(formatted_value, styles['right_bold_text']))
                        else:
                            row_list.append(Paragraph(formatted_value, styles['right_text']))
                table_data_pdf.append(row_list)

            # CORREZIONE: Larghezze colonne adattate per formato portrait
            col_widths_pdf = [doc.width * 0.5]  # Voce colonna al 50%
            remaining_width = doc.width - col_widths_pdf[0]
            num_columns = len(df_data.columns) - 1 
            if num_columns > 0:
                col_width = remaining_width / num_columns
                col_widths_pdf.extend([col_width] * num_columns)

            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'), 
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'), 
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), 
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.black),  # Solo cornice esterna
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ])
            
            table = Table(table_data_pdf, colWidths=col_widths_pdf)
            table.setStyle(table_style)
            story.append(table)

            doc.build(story)
            buffer.seek(0)
            return buffer

        pdf_buffer_riclass = generate_pdf_riclassified(
            df_export_riclassificato_actual, 
            "Report Conto Economico Riclassificato", 
            f"Cliente: {selected_cliente} | Anno: {', '.join(str(y) for y in years_to_display)}"
        )
        
        st.download_button(
            label="Scarica Conto Economico in PDF",
            data=pdf_buffer_riclass,
            file_name="conto_economico_riclassificato.pdf",
            mime="application/pdf",
            help="Esporta il Conto Economico riclassificato in un file PDF."
        )

    # ✅ AGGIUNTA: Terza colonna per ASCII
    with col_ascii_riclass:
        if ASCII_AVAILABLE:
            try:
                # Identifica righe grassetto per ASCII
                bold_rows_ascii = []
                for item in financial_model.report_structure_ce:
                    if item.get('Grassetto', False):
                        bold_rows_ascii.append(item['Voce'])
                
                # Crea report ASCII completo
                ascii_content, ascii_buffer = create_downloadable_ascii_report(
                    df=df_export_riclassificato_actual,
                    title="REPORT CONTO ECONOMICO",
                    subtitle="Riclassificato per Valore Aggiunto",
                    bold_rows=bold_rows_ascii,
                    report_type="Conto Economico",
                    filters=f"Cliente: {selected_cliente} | Anni: {', '.join(str(y) for y in years_to_display)}",
                    style="grid"
                )
                
                st.download_button(
                    label="Scarica Report ASCII",
                    data=ascii_buffer,
                    file_name="conto_economico.txt",
                    mime="text/plain",
                    help="Export formato testo - Tabelle perfette per email, console, stampa"
                )
                
            except Exception as e:
                st.error(f"Errore generazione ASCII: {e}")
                # Fallback semplice
                try:
                    simple_table = df_export_riclassificato_actual.to_string(index=False)
                    simple_buffer = io.BytesIO()
                    simple_buffer.write(simple_table.encode('utf-8'))
                    simple_buffer.seek(0)
                    
                    st.download_button(
                        label="Scarica Testo Semplice",
                        data=simple_buffer,
                        file_name="conto_economico_simple.txt",
                        mime="text/plain",
                        help="Formato testo semplificato (fallback)"
                    )
                except:
                    st.error("Impossibile generare export testo.")
        else:
            st.info("ASCII non disponibile - Installa ascii_table_generator")

else:
    st.info("Nessun dato da esportare.")
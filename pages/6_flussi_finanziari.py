# pages/report_flussi_finanziari.py - Progetto Business Plan Pro - versione 4.1 - 2025-06-10
# Aggiunto: Grafico a Cascata (Waterfall Chart) per visualizzazione flussi finanziari

import streamlit as st
import sqlite3
import pandas as pd
import sidebar_filtri 
import io
import plotly.graph_objects as go
from reportlab.lib.pagesizes import A4, landscape 
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
st.title("💰 Report Flussi di Cassa")

# ✅ AGGIUNTA: Didascalia
st.markdown("""
**Analisi dei Flussi di Cassa Aziendali**

Il report mostra la conversione dell'EBITDA in flusso monetario disponibile,
evidenziando l'impatto delle variazioni del capitale circolante, degli investimenti 
e della gestione finanziaria sulla liquidità aziendale.
""")

st.markdown(f"**Filtri applicati:** Cliente: **{selected_cliente}** | Anni: **{', '.join(selected_anni) if selected_anni else 'Tutti'}**")
st.markdown("---") 

# --- Logica per la Selezione Anni (Raffronto) ---
years_to_display = []
if selected_anni:
    years_to_display = sorted([int(y) for y in selected_anni])
    if len(years_to_display) == 1:
        selected_year = years_to_display[0]
        prev_year = selected_year - 1
        # Verifica se l'anno precedente è disponibile nei dati
        if prev_year >= (min([int(y) for y in st.session_state.anni_tutti_disponibili]) if st.session_state.anni_tutti_disponibili else 0):
            years_to_display.insert(0, prev_year)
    
    if len(years_to_display) < 2 and len(selected_anni) == 1:
        st.warning(f"Per calcolare i flussi, sono necessari dati per almeno due anni. Disponibile solo {years_to_display[0]} e l'anno precedente non è nei dati.")
        years_to_display = [] 
    
    years_to_display = sorted(list(set(years_to_display))) 

else: 
    all_available_years = sorted([int(y) for y in st.session_state.anni_tutti_disponibili])
    if len(all_available_years) >= 2:
        years_to_display = all_available_years[-2:] 
    elif len(all_available_years) == 1:
        st.warning(f"Per calcolare i flussi, sono necessari dati per almeno due anni. Disponibile solo {all_available_years[0]}.")
        years_to_display = []
    else:
        years_to_display = []

if not years_to_display or len(years_to_display) < 2:
    st.info("Seleziona almeno due anni consecutivi o un anno per vedere il raffronto con il precedente, per il calcolo dei flussi.")
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
    st.error(f"Errore nel caricamento dei dati per i Flussi Finanziari: {e}")
    st.info("Verifica che il database sia popolato e che le tabelle 'righe', 'conti', 'ricla' esistano e siano correlate correttamente.")
    df_full_data = pd.DataFrame()
finally:
    if conn:
        conn.close()

# Controllo se ci sono dati
if df_full_data.empty:
    st.error("Nessun dato trovato per gli anni selezionati. Verifica che ci siano dati nel database per questi anni.")
    st.stop()

# --- CHIAMATA AL MODELLO FINANZIARIO CENTRALE ---
try:
    all_calculated_reports = financial_model.calculate_all_reports(
        df_full_data, 
        years_to_display,
        financial_model.report_structure_ce,
        financial_model.report_structure_sp,
        financial_model.report_structure_ff
    )
    
    # Controllo se ci sono errori
    if 'error' in all_calculated_reports:
        st.error(f"Errore nel calcolo dei report: {all_calculated_reports['error']}")
        st.stop()
    
except Exception as e:
    st.error(f"Errore durante il calcolo dei report: {e}")
    st.stop()

# Ottieni il DataFrame dei Flussi Finanziari per la visualizzazione
df_final_display = all_calculated_reports['ff']

# --- Visualizzazione della Tabella Flussi Finanziari (Rendering HTML personalizzato) ---
if not df_final_display.empty:
    st.markdown("### Visualizzazione Tabellare")
    
    def display_with_html_flows(df, year_col_name, structure):
        if df.empty:
            return
        
        bold_rows = [item['Voce'] for item in structure if item.get('Grassetto', False)]
        
        # Creiamo un nuovo DataFrame per i dati formattati da visualizzare
        df_display_for_html_ff = pd.DataFrame(columns=df.columns) 
        
        # Popola df_display_for_html_ff con i valori formattati come stringhe
        for idx, row_original in df.iterrows():
            row_formatted = row_original.copy()
            # Formatta solo se il valore non è stringa vuota (intestazioni)
            if str(row_original[year_col_name]) != "" and row_original[year_col_name] != 0:
                row_formatted[year_col_name] = financial_model.format_number(row_original[year_col_name])
            else:
                row_formatted[year_col_name] = str(row_original[year_col_name])
            df_display_for_html_ff.loc[idx] = row_formatted

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
            .custom-table td.uppercase-text {
                text-transform: uppercase;
            }
        </style>
        <table class="custom-table">
            <thead>
                <tr>
        """
        # Intestazioni
        html_table += "<th>Voce</th>" 
        html_table += f"<th class='numeric'>{year_col_name}</th>" 
        html_table += "</tr></thead><tbody>"
        
        # Righe
        for _, row in df_display_for_html_ff.iterrows(): 
            row_class = ""
            if row['Voce'] in bold_rows:
                row_class += "bold-row "
            
            html_table += f"<tr class='{row_class.strip()}'>"
            
            # Colonna Voce
            cell_content_voce = str(row['Voce'])
            cell_class_voce = ""
            item_struct = next((item for item in structure if item['Voce'].upper() == row['Voce'].upper() or item['Voce'] == row['Voce']), None)
            if item_struct and item_struct.get('Maiuscolo', False):
                cell_class_voce = "uppercase-text"
            
            html_table += f"<td class='{cell_class_voce}'>{cell_content_voce}</td>"
            
            # Colonna Importo (unica colonna numerica)
            val_to_display = row[year_col_name]
            html_table += f"<td class='numeric'>{val_to_display}</td>" 
            
            html_table += "</tr>"
        
        html_table += "</tbody></table>"
        
        html(html_table, height=len(df) * 40 + 100, scrolling=True)

    # Determina l'anno corrente per la visualizzazione
    current_year_for_display = str(years_to_display[-1]) if years_to_display else ""
    
    # Verifica che la colonna dell'anno esista nel DataFrame
    if current_year_for_display not in df_final_display.columns:
        st.error(f"Colonna '{current_year_for_display}' non trovata nel DataFrame dei flussi. Colonne disponibili: {list(df_final_display.columns)}")
    else:
        display_with_html_flows(df_final_display, current_year_for_display, financial_model.report_structure_ff)

    # --- Grafico a Cascata (Waterfall Chart) ---
    st.markdown("---")
    st.markdown("### 📊 Grafico a Cascata - Conversione EBITDA in Flusso Monetario")
    
    def create_waterfall_chart(df_flussi, year_col):
        """Crea un grafico a cascata per i flussi finanziari usando Plotly"""
        if df_flussi.empty:
            st.info("Nessun dato disponibile per il grafico a cascata.")
            return
        
        if year_col not in df_flussi.columns:
            st.warning(f"Anno {year_col} non trovato nei dati.")
            return
        
        # Estrai i valori per il grafico a cascata dall'EBITDA al flusso netto
        ebitda = 0
        variazioni_ccn = 0
        variazione_tfr = 0
        investimenti = 0
        gestione_finanziaria = 0
        imposte = 0
        flusso_netto = 0
        
        # Funzione per convertire valori formattati
        def parse_value(val):
            if pd.isna(val) or val == 0:
                return 0
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, str):
                try:
                    # Rimuovi formattazione: punti, euro, spazi
                    clean_val = val.replace('.', '').replace('€', '').replace(' ', '').replace(',', '.')
                    return float(clean_val) if clean_val else 0
                except:
                    return 0
            return 0
        
        for _, row in df_flussi.iterrows():
            voce = row['Voce'].strip()
            valore = parse_value(row[year_col])
            voce_upper = voce.upper()
            
            # Identifica le componenti del flusso
            if 'EBITDA' in voce_upper:
                ebitda = valore
            elif 'VARIAZIONI CCN' in voce_upper or 'VARIAZIONE CCN' in voce_upper:
                variazioni_ccn = valore
            elif 'TFR' in voce_upper and 'VARIAZIONE' in voce_upper:
                variazione_tfr = valore
            elif 'INVESTIMENTO' in voce_upper:
                investimenti = valore
            elif 'GESTIONE FINANZIARIA' in voce_upper:
                gestione_finanziaria = valore
            elif 'IMPOSTE' in voce_upper:
                imposte = valore
            elif 'FLUSSO MONETARIO NETTO' in voce_upper or 'FLUSSO NETTO' in voce_upper:
                flusso_netto = valore
        
        # Verifica che abbiamo trovato almeno EBITDA
        if ebitda == 0:
            st.warning("⚠️ Non è stato trovato l'EBITDA. Impossibile creare il grafico a cascata.")
            return
        
        # Crea il grafico a cascata dall'EBITDA al flusso netto
        labels = ["EBITDA"]
        values = [ebitda]
        measures = ["absolute"]
        
        # Aggiungi le componenti se presenti
        if variazioni_ccn != 0:
            labels.append("Variazioni CCN")
            values.append(variazioni_ccn)
            measures.append("relative")
        
        if variazione_tfr != 0:
            labels.append("Variazione TFR")
            values.append(variazione_tfr)
            measures.append("relative")
        
        if investimenti != 0:
            labels.append("Investimenti")
            values.append(investimenti)
            measures.append("relative")
        
        if gestione_finanziaria != 0:
            labels.append("Gestione Finanziaria")
            values.append(gestione_finanziaria)
            measures.append("relative")
        
        if imposte != 0:
            labels.append("Imposte")
            values.append(imposte)
            measures.append("relative")
        
        # Aggiungi il flusso netto finale
        labels.append("Flusso Monetario Netto")
        if flusso_netto != 0:
            values.append(flusso_netto)
        else:
            # Calcola il flusso netto dalla somma
            flusso_calcolato = ebitda + variazioni_ccn + variazione_tfr + investimenti + gestione_finanziaria + imposte
            values.append(flusso_calcolato)
        measures.append("total")
        
        # Crea testi formattati per il grafico
        text_values = []
        for val in values:
            text_values.append(f"€ {val:,.0f}".replace(',', '.'))
        
        # Crea il grafico a cascata
        fig = go.Figure(go.Waterfall(
            name="Conversione EBITDA in Flusso Monetario",
            orientation="v",
            measure=measures,
            x=labels,
            textposition="outside",
            text=text_values,
            y=values,
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            increasing={"marker": {"color": "#2E8B57"}},  # Verde per valori positivi
            decreasing={"marker": {"color": "#DC143C"}},  # Rosso per valori negativi
            totals={"marker": {"color": "#1f77b4"}}       # Blu per totali
        ))
        
        fig.update_layout(
            title=f"Conversione EBITDA in Flusso Monetario - Anno {year_col}",
            showlegend=False,
            height=600,
            xaxis_title="Componenti del Flusso",
            yaxis_title="Importo (€)",
            font=dict(size=12),
            plot_bgcolor='white',
            paper_bgcolor='white',
            yaxis=dict(
                gridcolor='lightgray',
                gridwidth=1,
                zeroline=True,
                zerolinecolor='black',
                zerolinewidth=2
            )
        )
        
        # Mostra il grafico
        st.plotly_chart(fig, use_container_width=True)
        
        # Aggiungi interpretazione
        with st.expander("💡 Come leggere il grafico a cascata"):
            st.markdown("""
            **Il grafico a cascata mostra la conversione dell'EBITDA in flusso monetario:**
            - 🔵 **EBITDA**: Punto di partenza - Risultato operativo prima di ammortamenti
            - 🟢 **Barre verdi**: Componenti che aumentano la liquidità
            - 🔴 **Barre rosse**: Componenti che diminuiscono la liquidità  
            - 🔵 **Flusso Monetario Netto**: Risultato finale disponibile
            
            **Componenti analizzate:**
            - **Variazioni CCN**: Effetto delle variazioni del capitale circolante
            - **Variazione TFR**: Impatto dei fondi per trattamento di fine rapporto
            - **Investimenti**: Flussi per acquisti/vendite di immobilizzazioni
            - **Gestione Finanziaria**: Interessi attivi/passivi e movimenti finanziari
            - **Imposte**: Effetto fiscale sul flusso di cassa
            """)

    # Crea il grafico a cascata
    create_waterfall_chart(df_final_display, current_year_for_display)

    # --- Esportazione Excel e PDF per i Flussi Finanziari ---
    st.markdown("---")
    st.subheader("Esporta Flussi Finanziari")

    # df_export_flussi_actual è già un risultato da all_calculated_reports
    df_export_flussi_actual = all_calculated_reports['ff_export']
    
    # Verifica che ci siano dati da esportare
    if df_export_flussi_actual.empty:
        st.warning("Nessun dato da esportare")
    else:
        # Rinomina le colonne per export se necessario
        if len(df_export_flussi_actual.columns) > 1:
            df_export_flussi_actual.columns = ['Voce', str(current_year_for_display)]

        # ✅ MODIFICA: 3 colonne invece di 2
        col_excel_flows, col_pdf_flows, col_ascii_flows = st.columns(3)

        with col_excel_flows:
            try:
                excel_buffer_flows = io.BytesIO()
                with pd.ExcelWriter(excel_buffer_flows, engine='xlsxwriter') as writer:
                    df_export_flussi_actual.to_excel(writer, index=False, sheet_name='Flussi Finanziari') 
                    workbook = writer.book
                    worksheet = writer.sheets['Flussi Finanziari'] 
                    
                    # Applica formattazione numerica alla colonna dell'anno
                    if len(df_export_flussi_actual.columns) > 1:
                        num_format = workbook.add_format({'num_format': '#,##0'})
                        worksheet.set_column(1, 1, None, num_format)

                excel_buffer_flows.seek(0)
                st.download_button(
                    label="Scarica Flussi Finanziari in Excel",
                    data=excel_buffer_flows,
                    file_name="flussi_finanziari.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Esporta il Report Flussi Finanziari in un file Excel."
                )
            except Exception as e:
                st.error(f"Errore nella generazione del file Excel: {e}")

        with col_pdf_flows:
            try:
                def generate_pdf_flows(df_data, title, filters_applied): 
                    buffer = io.BytesIO()
                    doc = SimpleDocTemplate(buffer, pagesize=A4)
                    styles = getSampleStyleSheet()
                    
                    # Aggiungi stili personalizzati se non esistono
                    if 'bold_text' not in styles:
                        styles.add(ParagraphStyle(name='bold_text', parent=styles['Normal'], fontName='Helvetica-Bold'))
                    if 'normal_text' not in styles:
                        styles.add(ParagraphStyle(name='normal_text', parent=styles['Normal'], fontName='Helvetica'))
                    if 'right_text' not in styles:
                        styles.add(ParagraphStyle(name='right_text', parent=styles['Normal'], alignment=2))
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
                        structure_item_found = next((item for item in financial_model.report_structure_ff if item['Voce'].upper() == row['Voce'].upper() or item['Voce'] == row['Voce']), None)
                        is_bold_row = structure_item_found.get('Grassetto', False) if structure_item_found else False
                        is_uppercase_row = structure_item_found.get('Maiuscolo', False) if structure_item_found else False

                        # Colonna Voce
                        voce_content = str(row['Voce'])
                        if is_uppercase_row:
                            voce_content = voce_content.upper()

                        if is_bold_row:
                            row_list.append(Paragraph(voce_content, styles['bold_text']))
                        else:
                            row_list.append(Paragraph(voce_content, styles['normal_text']))
                        
                        # Colonna Valore (Anno)
                        if len(df_data.columns) > 1:
                            numeric_value = row[df_data.columns[1]]
                            if pd.isna(numeric_value) or numeric_value == "" or numeric_value == 0:
                                formatted_value = ""
                            else:
                                formatted_value = financial_model.format_number(numeric_value, pdf_format=True)

                            if is_bold_row:
                                row_list.append(Paragraph(formatted_value, styles['right_bold_text']))
                            else:
                                row_list.append(Paragraph(formatted_value, styles['right_text']))
                        
                        table_data_pdf.append(row_list)

                    col_widths_pdf = [doc.width * 0.6, doc.width * 0.4]

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

                pdf_buffer_flows = generate_pdf_flows(
                    df_export_flussi_actual, 
                    "Report Flussi Finanziari", 
                    f"Cliente: {selected_cliente} | Anno: {current_year_for_display}"
                )
                
                st.download_button(
                    label="Scarica Flussi Finanziari in PDF",
                    data=pdf_buffer_flows,
                    file_name="flussi_finanziari.pdf",
                    mime="application/pdf",
                    help="Esporta il Report Flussi Finanziari in un file PDF."
                )
            except Exception as e:
                st.error(f"Errore nella generazione del file PDF: {e}")

        # ✅ AGGIUNTA: Terza colonna per ASCII
        with col_ascii_flows:
            if ASCII_AVAILABLE:
                try:
                    # Identifica righe grassetto per ASCII
                    bold_rows_ascii = []
                    for item in financial_model.report_structure_ff:
                        if item.get('Grassetto', False):
                            bold_rows_ascii.append(item['Voce'])
                    
                    # Crea report ASCII completo
                    ascii_content, ascii_buffer = create_downloadable_ascii_report(
                        df=df_export_flussi_actual,
                        title="REPORT FLUSSI FINANZIARI",
                        subtitle="Conversione EBITDA in Flusso Monetario",
                        bold_rows=bold_rows_ascii,
                        report_type="Flussi di Cassa",
                        filters=f"Cliente: {selected_cliente} | Anno: {current_year_for_display}",
                        style="grid"
                    )
                    
                    st.download_button(
                        label="Scarica Report ASCII",
                        data=ascii_buffer,
                        file_name="flussi_finanziari.txt",
                        mime="text/plain",
                        help="Export formato testo - Tabelle perfette per email, console, stampa"
                    )
                    
                except Exception as e:
                    st.error(f"Errore generazione ASCII: {e}")
                    # Fallback semplice
                    try:
                        simple_table = df_export_flussi_actual.to_string(index=False)
                        simple_buffer = io.BytesIO()
                        simple_buffer.write(simple_table.encode('utf-8'))
                        simple_buffer.seek(0)
                        
                        st.download_button(
                            label="Scarica Testo Semplice",
                            data=simple_buffer,
                            file_name="flussi_finanziari_simple.txt",
                            mime="text/plain",
                            help="Formato testo semplificato (fallback)"
                        )
                    except:
                        st.error("Impossibile generare export testo.")
            else:
                st.info("ASCII non disponibile - Installa ascii_table_generator")

else:
    st.info("Nessun dato da visualizzare. Verifica che ci siano dati per gli anni selezionati.")
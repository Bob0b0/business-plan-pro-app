# pages/report_conto_economico.py - Progetto Business Plan Pro - versione 3.2 - 2025-06-09
# Obiettivo: Allineamento PDF e grassetto come report_stato_patrimoniale.py.

import streamlit as st
import sqlite3
import pandas as pd
import sidebar_filtri 
import io
from reportlab.lib.pagesizes import A4, portrait 
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle 
from reportlab.lib.units import inch
from streamlit.components.v1 import html

# Funzione unica per la formattazione dei numeri
def format_number(x, pdf_format=False):
    try:
        num = int(x)
        if pdf_format:
            # Formattazione speciale per PDF (scambio punti e virgole)
            return f"{num:,}".replace(",", "X").replace(".", ",").replace("X", ".")
        # Formattazione standard per HTML/dataframe
        return f"{num:,}".replace(",", ".")
    except (ValueError, TypeError):
        return str(x)

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
        if prev_year >= (min([int(y) for y in st.session_state.anni_tutti_disponibili]) if st.session_state.anni_tutti_disponibili else 0): 
            years_to_display.insert(0, prev_year)
    years_to_display = sorted(list(set(years_to_display))) 
else: 
    years_to_display = sorted([int(y) for y in st.session_state.anni_tutti_disponibili])

if not years_to_display:
    st.info("Nessun anno disponibile o selezionato per el report.")
    st.stop() 

# Connessione al database e caricamento dati
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
    st.error(f"Errore nel caricamento dei dati per il Conto Economico: {e}")
    st.info("Verifica che il database sia popolato e che le tabelle 'righe', 'conti', 'ricla' esistano e siano correlate correttamente.")
    df_full_data = pd.DataFrame()
finally:
    if conn:
        conn.close()

# --- Pre-elaborazione Dati per Riclassificazione ---
if not df_full_data.empty:
    df_full_data['importo'] = pd.to_numeric(df_full_data['importo'], errors='coerce').fillna(0).astype(int)
    
    # Raggruppa gli importi per ID_RI e per anno
    df_pivot_by_id_ri_year = df_full_data.pivot_table(
        index='ID_RI',      
        columns='anno',     
        values='importo',   
        aggfunc='sum'       
    ).fillna(0).astype(int) 

    # Assicurati di avere la mappatura ID_RI -> Ricla (nome della voce)
    id_ri_to_ricla_name = df_full_data[['ID_RI', 'Ricla']].drop_duplicates().set_index('ID_RI')['Ricla'].to_dict()

    # --- Definizione delle Voci del Report e delle Formule (Conto Economico) ---
    report_structure_ce = [
        # CONTO ECONOMICO
        {'Voce': 'CONTO ECONOMICO', 'Tipo': 'Intestazione', 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 100},
        {'Voce': 'Ricavi dalle vendite e prestazioni', 'Tipo': 'Dettaglio', 'ID_RI': 'RI01', 'Ordine': 110},
        {'Voce': 'Variazione rimanenze prodotti finiti', 'Tipo': 'Dettaglio', 'ID_RI': 'RI02', 'Ordine': 120},
        {'Voce': 'Altri ricavi e proventi', 'Tipo': 'Dettaglio', 'ID_RI': 'RI03', 'Ordine': 130},
        {'Voce': 'Costi capitalizzati', 'Tipo': 'Dettaglio', 'ID_RI': 'RI04', 'Ordine': 140}, 
        {'Voce': 'VALORE DELLA PRODUZIONE', 'Tipo': 'Calcolo', 'Formula_Refs': ['RI01', 'RI02', 'RI03', 'RI04'], 'Formula': lambda d: d['RI01'] + d['RI02'] + d['RI03'] + d['RI04'], 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 150},
        {'Voce': 'Acquisti di merci', 'Tipo': 'Dettaglio', 'ID_RI': 'RI05', 'Ordine': 160},
        {'Voce': 'Costi per servizi', 'Tipo': 'Dettaglio', 'ID_RI': 'RI06', 'Ordine': 170},
        {'Voce': 'Godimento di beni di terzi', 'Tipo': 'Dettaglio', 'ID_RI': 'RI07', 'Ordine': 180},
        {'Voce': 'Oneri diversi di gestione', 'Tipo': 'Dettaglio', 'ID_RI': 'RI08', 'Ordine': 190},
        {'Voce': 'Variazione rim. m.p. e merci', 'Tipo': 'Dettaglio', 'ID_RI': 'RI09', 'Ordine': 200},
        {'Voce': 'COSTI DELLA PRODUZIONE', 'Tipo': 'Calcolo', 'Formula_Refs': ['RI05', 'RI06', 'RI07', 'RI08', 'RI09'], 'Formula': lambda d: d['RI05'] + d['RI06'] + d['RI07'] + d['RI08'] + d['RI09'], 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 210},
        {'Voce': 'VALORE AGGIUNTO', 'Tipo': 'Calcolo', 'Formula_Refs': ['VALORE DELLA PRODUZIONE', 'COSTI DELLA PRODUZIONE'], 'Formula': lambda d: d['VALORE DELLA PRODUZIONE'] - d['COSTI DELLA PRODUZIONE'], 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 220},
        {'Voce': 'Personale', 'Tipo': 'Dettaglio', 'ID_RI': 'RI10', 'Ordine': 230},
        {'Voce': 'MARGINE OPERATIVO LORDO (EBITDA)', 'Tipo': 'Calcolo', 'Formula_Refs': ['VALORE AGGIUNTO', 'RI10'], 'Formula': lambda d: d['VALORE AGGIUNTO'] - d['RI10'], 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 240},
        {'Voce': 'Ammortamenti', 'Tipo': 'Dettaglio', 'ID_RI': 'RI11', 'Ordine': 250},
        {'Voce': 'Accantonamenti e sval. attivo corrente', 'Tipo': 'Dettaglio', 'ID_RI': 'RI12', 'Ordine': 260},
        {'Voce': 'RISULTATO OPERATIVO (EBIT)', 'Tipo': 'Calcolo', 'Formula_Refs': ['MARGINE OPERATIVO LORDO (EBITDA)', 'RI11', 'RI12'], 'Formula': lambda d: d['MARGINE OPERATIVO LORDO (EBITDA)'] - d['RI11'] - d['RI12'], 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 270},
        {'Voce': 'Proventi finanziari', 'Tipo': 'Dettaglio', 'ID_RI': 'RI14', 'Ordine': 280},
        {'Voce': 'Oneri finanziari', 'Tipo': 'Dettaglio', 'ID_RI': 'RI13', 'Ordine': 290},
        {'Voce': 'SALDO GESTIONE FINANZIARIA', 'Tipo': 'Calcolo', 'Formula_Refs': ['RI14', 'RI13'], 'Formula': lambda d: d['RI14'] - d['RI13'], 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 300},
        {'Voce': 'Altri ricavi e proventi non operativi', 'Tipo': 'Dettaglio', 'ID_RI': 'RI15', 'Ordine': 310},
        {'Voce': 'Altri costi non operativi', 'Tipo': 'Dettaglio', 'ID_RI': 'RI16', 'Ordine': 320},
        {'Voce': 'SALDO ALTRI RICAVI E PROVENTI NON OPERATIVI', 'Tipo': 'Calcolo', 'Formula_Refs': ['RI15', 'RI16'], 'Formula': lambda d: d['RI15'] - d['RI16'], 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 330},
        {'Voce': 'RISULTATO LORDO (EBT)', 'Tipo': 'Calcolo', 'Formula_Refs': ['RISULTATO OPERATIVO (EBIT)', 'SALDO GESTIONE FINANZIARIA', 'SALDO ALTRI RICAVI E PROVENTI NON OPERATIVI'], 'Formula': lambda d: d['RISULTATO OPERATIVO (EBIT)'] + d['SALDO GESTIONE FINANZIARIA'] + d['SALDO ALTRI RICAVI E PROVENTI NON OPERATIVI'], 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 340},
        {'Voce': 'Imposte di esercizio', 'Tipo': 'Dettaglio', 'ID_RI': 'RI17', 'Ordine': 350},
        {'Voce': 'RISULTATO NETTO', 'Tipo': 'Dettaglio', 'ID_RI': 'RI18', 'Grassetto': True, 'Ordine': 360},
    ]

    # --- Calcolo dei valori per il report ---
    values_by_year = {year: {} for year in years_to_display} 
    
    # Popolare i valori di dettaglio
    for year in years_to_display:
        for item in report_structure_ce: 
            if item['Tipo'] == 'Dettaglio':
                if year in df_pivot_by_id_ri_year.columns and item['ID_RI'] in df_pivot_by_id_ri_year.index:
                    value = df_pivot_by_id_ri_year.loc[item['ID_RI'], year]
                    values_by_year[year][item['ID_RI']] = value
                else:
                    value = 0 
                values_by_year[year][item['ID_RI']] = value 

    # Risolvere le formule di calcolo (iterando sull'ordine)
    for item in sorted(report_structure_ce, key=lambda x: x['Ordine']): 
        if item['Tipo'] == 'Calcolo':
            voce_calcolata_name = item['Voce']
            for year in years_to_display: 
                try:
                    formula_input_dict = {}
                    for ref in item['Formula_Refs']:
                        if ref in values_by_year[year]: 
                            formula_input_dict[ref] = values_by_year[year][ref]
                        elif ref in id_ri_to_ricla_name: 
                             formula_input_dict[ref] = values_by_year[year].get(ref, 0)
                        else:
                            formula_input_dict[ref] = 0 
                        
                    calculated_value = item['Formula'](formula_input_dict)
                    
                    values_by_year[year][voce_calcolata_name] = calculated_value

                except KeyError as ke:
                    st.warning(f"Errore di formula per '{voce_calcolata_name}' nell'anno {year}: Riferimento mancante '{ke}'. (Impostato a 0)")
                    values_by_year[year][voce_calcolata_name] = 0
                except Exception as e:
                    st.error(f"Errore di calcolo per '{voce_calcolata_name}' nell'anno {year}: {e}. (Impostato a 0)")
                    values_by_year[year][voce_calcolata_name] = 0

    # Costruire il DataFrame finale per la visualizzazione
    report_data_for_display = []
    for item in report_structure_ce: 
        row = {'Voce': item['Voce']}
        
        if item.get('Maiuscolo', False):
            row['Voce'] = row['Voce'].upper()
        
        for year in years_to_display:
            val = 0
            if item['Tipo'] == 'Intestazione':
                row[str(year)] = "" 
            elif item['Tipo'] == 'Dettaglio':
                val = values_by_year[year].get(item['ID_RI'], 0)
                row[str(year)] = val
            elif item['Tipo'] == 'Calcolo':
                val = values_by_year[year].get(item['Voce'], 0) 
                row[str(year)] = val
        
        report_data_for_display.append(row)

    df_final_display = pd.DataFrame(report_data_for_display)

else: 
    st.info("Nessun dato trovato per la riclassificazione con i filtri selezionati.")
    df_final_display = pd.DataFrame() 

# --- Visualizzazione della Tabella Riclassificata (Rendering HTML personalizzato) ---
if not df_final_display.empty:
    st.markdown("### Visualizzazione Tabellare")
    
    # Soluzione HTML personalizzata
    def display_with_html(df, years, structure):
        if df.empty:
            return
        
        bold_rows = [item['Voce'] for item in structure if item.get('Grassetto', False)]
        uppercase_rows = [item['Voce'] for item in structure if item.get('Maiuscolo', False)]
        
        df_formatted = df.copy()
        for year in years:
            df_formatted[str(year)] = df_formatted[str(year)].apply(format_number)
        
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
            .custom-table tr.uppercase-row td {
                text-transform: uppercase;
            }
        </style>
        <table class="custom-table">
            <thead>
                <tr>
        """
        
        for col in df_formatted.columns:
            html_table += f"<th>{col}</th>"
        html_table += "</tr></thead><tbody>"
        
        for _, row in df_formatted.iterrows():
            row_class = ""
            if row['Voce'] in bold_rows:
                row_class += "bold-row "
            if row['Voce'] in uppercase_rows:
                row_class += "uppercase-row "
            
            html_table += f"<tr class='{row_class.strip()}'>"
            for i, (col, val) in enumerate(row.items()):
                cell_class = "numeric" if i > 0 else ""
                html_table += f"<td class='{cell_class}'>{val}</td>"
            html_table += "</tr>"
        
        html_table += "</tbody></table>"
        
        html(html_table, height=len(df_formatted) * 40 + 100)

    display_with_html(df_final_display, years_to_display, report_structure_ce)

    # --- Esportazione Excel e PDF ---
    st.markdown("---")
    st.subheader("Esporta Conto Economico Riclassificato")

    df_export_riclassificato_actual = pd.DataFrame()
    export_rows = []
    for item in report_structure_ce:
        if item.get('Visibile', True) == False:
            continue

        row_values = {'Voce': item['Voce']}
        if item.get('Maiuscolo', False):
            row_values['Voce'] = row_values['Voce'].upper()
        
        for year in years_to_display:
            val = 0
            if item['Tipo'] == 'Intestazione':
                row_values[str(year)] = ""
            elif item['Tipo'] == 'Dettaglio':
                val = values_by_year[year].get(item['ID_RI'], 0)
                row_values[str(year)] = val
            elif item['Tipo'] == 'Calcolo':
                val = values_by_year[year].get(item['Voce'], 0)
                row_values[str(year)] = val
        export_rows.append(row_values)
    df_export_riclassificato_actual = pd.DataFrame(export_rows)

    df_export_riclassificato_actual.columns = ['Voce'] + [str(year) for year in years_to_display]

    col_excel_riclass, col_pdf_riclass = st.columns(2)

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
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with col_pdf_riclass:
        def generate_pdf_riclassified(df_data, title, filters_applied):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=portrait(A4))
            styles = getSampleStyleSheet()
            
            # Definizione degli stili aggiuntivi necessari
            if 'bold_text' not in styles:
                styles.add(ParagraphStyle(name='bold_text', parent=styles['Normal'], fontName='Helvetica-Bold'))
            if 'normal_text' not in styles:
                styles.add(ParagraphStyle(name='normal_text', parent=styles['Normal'], fontName='Helvetica'))
            if 'right_bold_text' not in styles:
                styles.add(ParagraphStyle(name='right_bold_text', parent=styles['Normal'], fontName='Helvetica-Bold', alignment=2))
            if 'right_normal_text' not in styles:
                styles.add(ParagraphStyle(name='right_normal_text', parent=styles['Normal'], fontName='Helvetica', alignment=2))

            story = []

            story.append(Paragraph(title, styles['h2']))
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph(f"<b>Filtri applicati:</b> {filters_applied}", styles['Normal']))
            story.append(Spacer(1, 0.2 * inch))
            
            table_data_pdf = []
            header_row_pdf = []
            for col in df_data.columns:
                if col == 'Voce':
                    header_row_pdf.append(Paragraph(col, styles['bold_text']))
                else:
                    header_row_pdf.append(Paragraph(col, styles['right_bold_text']))
            table_data_pdf.append(header_row_pdf)

            for index, row in df_data.iterrows():
                row_list = []
                structure_item_found = next((item for item in report_structure_ce if item['Voce'].upper() == row['Voce'].upper() or item['Voce'] == row['Voce']), None)
                is_bold_row = structure_item_found.get('Grassetto', False) if structure_item_found else False
                
                for col_name in df_data.columns:
                    cell_value = row[col_name]
                    
                    if col_name == 'Voce':
                        if is_bold_row:
                            formatted_cell_value = Paragraph(cell_value, styles['bold_text'])
                        else:
                            formatted_cell_value = Paragraph(cell_value, styles['normal_text'])
                    else:
                        formatted_value = format_number(cell_value, pdf_format=True)
                        if is_bold_row:
                            formatted_cell_value = Paragraph(formatted_value, styles['right_bold_text'])
                        else:
                            formatted_cell_value = Paragraph(formatted_value, styles['right_normal_text'])
                    
                    row_list.append(formatted_cell_value)
                
                table_data_pdf.append(row_list)

            col_widths_pdf = [doc.width / len(df_data.columns)] * len(df_data.columns)
            col_widths_pdf[0] = doc.width * 0.4
            remaining_width = doc.width - col_widths_pdf[0]
            for i in range(1, len(col_widths_pdf)):
                col_widths_pdf[i] = remaining_width / (len(col_widths_pdf) - 1)

            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
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
            f"Cliente: {selected_cliente} | Anni: {', '.join(str(y) for y in years_to_display)}"
        )
        
        st.download_button(
            label="Scarica Conto Economico in PDF",
            data=pdf_buffer_riclass,
            file_name="conto_economico_riclassificato.pdf",
            mime="application/pdf"
        )
else:
    st.info("Nessun dato da esportare.")
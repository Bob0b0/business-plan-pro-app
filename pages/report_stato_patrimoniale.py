# pages/report_stato_patrimoniale.py - Progetto Business Plan Pro - versione 1.7 - 2025-06-08
# Obiettivo: PFN con maiuscolo solo iniziale nel report.

import streamlit as st
import sqlite3
import pandas as pd
import sidebar_filtri
import io
from reportlab.lib.pagesizes import A4, landscape 
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle 
from reportlab.lib.units import inch

# Chiama la funzione per visualizzare i filtri nella sidebar
sidebar_filtri.display_sidebar_filters()

# Nome del database
DATABASE_NAME = "business_plan_pro.db"

# Accesso ai valori dei filtri da session_state
selected_cliente = st.session_state.selected_cliente
selected_anni = st.session_state.selected_anni 
selected_sezione = st.session_state.selected_sezione 

# --- Titolo e Intestazione Report ---
st.title("📈 Report Stato Patrimoniale")
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

else: # Se nessun anno è selezionato, mostra tutti gli anni disponibili
    years_to_display = sorted([int(y) for y in st.session_state.anni_tutti_disponibili])

if not years_to_display:
    st.info("Nessun anno disponibile o selezionato per il report.")
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
    st.error(f"Errore nel caricamento dei dati per lo Stato Patrimoniale: {e}")
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

    # --- Definizione delle Voci del Report e delle Formule (Stato Patrimoniale) ---
    report_structure_sp = [
        # STATO PATRIMONIALE
        {'Voce': 'STATO PATRIMONIALE', 'Tipo': 'Intestazione', 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 400},
        {'Voce': 'Soci c/sottoscrizioni', 'Tipo': 'Dettaglio', 'ID_RI': 'RI19', 'Ordine': 405},
        {'Voce': 'Immobilizzazioni materiali', 'Tipo': 'Dettaglio', 'ID_RI': 'RI20', 'Ordine': 410},
        {'Voce': 'Immobilizzazioni immateriali', 'Tipo': 'Dettaglio', 'ID_RI': 'RI21', 'Ordine': 420},
        {'Voce': 'Immobilizzazioni finanziarie', 'Tipo': 'Dettaglio', 'ID_RI': 'RI22', 'Ordine': 430},
        {'Voce': 'TOTALE IMMOBILIZZAZIONI', 'Tipo': 'Calcolo', 'Formula_Refs': ['RI20', 'RI21', 'RI22'], 'Formula': lambda d: d['RI20'] + d['RI21'] + d['RI22'], 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 440},
        {'Voce': 'Crediti verso clienti', 'Tipo': 'Dettaglio', 'ID_RI': 'RI23', 'Ordine': 450},
        {'Voce': 'Debiti verso fornitori', 'Tipo': 'Dettaglio', 'ID_RI': 'RI24', 'Ordine': 460},
        {'Voce': 'Rimanenze', 'Tipo': 'Dettaglio', 'ID_RI': 'RI25', 'Ordine': 470},
        {'Voce': 'Altri crediti b.t.', 'Tipo': 'Dettaglio', 'ID_RI': 'RI26', 'Ordine': 480},
        {'Voce': 'Altri debiti b.t.', 'Tipo': 'Dettaglio', 'ID_RI': 'RI27', 'Ordine': 490},
        {'Voce': 'CAPITALE CIRCOLANTE NETTO (CCN)', 'Tipo': 'Calcolo', 'Formula_Refs': ['RI23', 'RI24', 'RI25', 'RI26', 'RI27'], 'Formula': lambda d: d['RI23'] - d['RI24'] + d['RI25'] + d['RI26'] - d['RI27'], 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 500},
        {'Voce': 'TFR', 'Tipo': 'Dettaglio', 'ID_RI': 'RI28', 'Ordine': 510},
        {'Voce': 'Fondi rischi e oneri', 'Tipo': 'Dettaglio', 'ID_RI': 'RI29', 'Ordine': 520},
        {'Voce': 'Altri debiti m.l.t.', 'Tipo': 'Dettaglio', 'ID_RI': 'RI30', 'Ordine': 530},
        {'Voce': 'CAPITALE INVESTITO', 'Tipo': 'Calcolo', 'Formula_Refs': ['RI19', 'RI20', 'RI21', 'RI22', 'RI23', 'RI24', 'RI25', 'RI26', 'RI27', 'RI28', 'RI29', 'RI30'], 'Formula': lambda d: d['RI19'] + d['RI20'] + d['RI21'] + d['RI22'] + d['RI23'] - d['RI24'] + d['RI25'] + d['RI26'] - d['RI27'] - d['RI28'] - d['RI29'] - d['RI30'], 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 540},
        # Voci componenti PFN - Nascondile dal report finale
        {'Voce': 'Liquidità', 'Tipo': 'Dettaglio', 'ID_RI': 'RI31', 'Ordine': 550, 'Visibile': False}, 
        {'Voce': 'Banche passive', 'Tipo': 'Dettaglio', 'ID_RI': 'RI33', 'Ordine': 552, 'Visibile': False}, 
        # CORREZIONE QUI: Maiuscolo a False per la voce PFN
        {'Voce': 'Posizione finanziaria netta', 'Tipo': 'Calcolo', 'Formula_Refs': ['RI33', 'RI31'], 'Formula': lambda d: d['RI33'] - d['RI31'], 'Grassetto': True, 'Maiuscolo': False, 'Ordine': 556}, 
        
        {'Voce': 'Patrimonio netto', 'Tipo': 'Dettaglio', 'ID_RI': 'RI32', 'Ordine': 560},
        {'Voce': 'CAPITALE IMPIEGATO', 'Tipo': 'Calcolo', 'Formula_Refs': ['RI31', 'RI32', 'RI33'], 'Formula': lambda d: -d['RI31'] + d['RI32'] + d['RI33'], 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 570}, 
    ]

    # --- Calcolo dei valori per il report ---
    values_by_year = {year: {} for year in years_to_display} 
    
    # Popolare i valori di dettaglio
    for year in years_to_display:
        for item in report_structure_sp: # Per lo SP
            if item['Tipo'] == 'Dettaglio':
                if year in df_pivot_by_id_ri_year.columns and item['ID_RI'] in df_pivot_by_id_ri_year.index:
                    value = df_pivot_by_id_ri_year.loc[item['ID_RI'], year]
                    values_by_year[year][item['ID_RI']] = value
                else:
                    value = 0 
                values_by_year[year][item['ID_RI']] = value 

    # Risolvere le formule di calcolo (iterando sull'ordine)
    for item in sorted(report_structure_sp, key=lambda x: x['Ordine']): # Per lo SP
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
    for item in report_structure_sp: # Per lo SP
        # Usa item.get('Visibile', True) per controllare se la voce deve essere visualizzata
        if item.get('Visibile', True) == False: 
            continue

        row = {'Voce': item['Voce']}
        
        if item.get('Maiuscolo', False):
            row['Voce'] = row['Voce'].upper()
        
        for year in years_to_display:
            val = 0
            if item['Tipo'] == 'Intestazione':
                row[str(year)] = "" 
            elif item['Tipo'] == 'Dettaglio':
                val = values_by_year[year].get(item['ID_RI'], 0)
                row[str(year)] = f"{int(val):,}".replace(",", "X").replace(".", ",").replace("X", ".") if val != 0 else "0" 
            elif item['Tipo'] == 'Calcolo':
                val = values_by_year[year].get(item['Voce'], 0) 
                row[str(year)] = f"{int(val):,}".replace(",", "X").replace(".", ",").replace("X", ".") if val != 0 else "0"
        
        report_data_for_display.append(row)

    df_final_display = pd.DataFrame(report_data_for_display)

else:
    st.info("Nessun dato trovato per la riclassificazione con i filtri selezionati.")
    df_final_display = pd.DataFrame() 


# --- Visualizzazione della Tabella Riclassificata ---
if not df_final_display.empty:
    column_config_riclass = {
        "Voce": st.column_config.TextColumn("Voce", help="Voce di Bilancio Riclassificata", width="large"),
    }
    for year in years_to_display: 
        column_config_riclass[str(year)] = st.column_config.TextColumn(str(year), help=f"Valore per l'anno {year}", width="medium")

    st.dataframe(
        df_final_display, 
        column_config=column_config_riclass,
        hide_index=True, 
        use_container_width=True,
        key="report_riclassificato_stato_patrimoniale_dataframe"
    )

    # --- CSS per allineamento a destra degli importi e grassetto ---
    css_string = """
    <style>
    /* Allinea intestazioni degli anni a destra */
    """
    for i, year in enumerate(years_to_display):
        css_string += f"""
        [data-testid="stDataFrame"] .column-header:has([data-testid="stTextLabel"]:contains("{year}")) div[data-testid="stTextLabel"] {{
            text-align: right !important;
        }}
        """
        # Allinea le celle degli anni a destra
        css_string += f"""
        [data-testid="stDataFrame"] .row-cells > div:nth-child({i+2}) div[data-testid="stCell"] div {{
            text-align: right !important;
            justify-content: flex-end !important;
            padding-right: 12px !important; 
        }}
        """
    css_string += """
    /* Rimuovi la sottolineatura dal testo dell'intestazione di st.dataframe */
    .column-header div[data-testid="stTextLabel"] {
        text_decoration: none !important;
    }
    </style>
    """
    st.markdown(css_string, unsafe_allow_html=True)


    # --- Esportazione Excel e PDF per il Report Riclassificato ---
    st.markdown("---")
    st.subheader("Esporta Stato Patrimoniale Riclassificato")

    df_export_riclassificato_actual = pd.DataFrame()
    export_rows = []
    for item in report_structure_sp: # Per lo SP
        # Controlla se la voce deve essere visualizzata per l'export
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

    df_export_riclassificato_actual.columns = ['Voce'] + [str(year) for year in years_to_display] # Rinomina per export

    col_excel_riclass, col_pdf_riclass = st.columns(2)

    with col_excel_riclass:
        excel_buffer_riclass = io.BytesIO()
        with pd.ExcelWriter(excel_buffer_riclass, engine='xlsxwriter') as writer:
            df_export_riclassificato_actual.to_excel(writer, index=False, sheet_name='Stato Pat Riclass') # NOME PIU' BREVE
            workbook = writer.book
            worksheet = writer.sheets['Stato Pat Riclass'] # NOME PIU' BREVE
            
            num_format = workbook.add_format({'num_format': '#,##0'})
            for col_idx, year in enumerate(years_to_display):
                worksheet.set_column(col_idx + 1, col_idx + 1, None, num_format) 

        excel_buffer_riclass.seek(0)
        st.download_button(
            label="Esporta Stato Patrimoniale in Excel",
            data=excel_buffer_riclass,
            file_name="stato_patrimoniale_riclassificato.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Esporta lo Stato Patrimoniale riclassificato in un file PDF."
        )

    with col_pdf_riclass:
        def generate_pdf_riclassified(df_data, title, filters_applied): 
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=landscape(A4)) 
            styles = getSampleStyleSheet()
            
            if 'h4_bold' not in styles:
                styles.add(ParagraphStyle(name='h4_bold', parent=styles['h4'], fontName='Helvetica-Bold'))
            if 'h4_right' not in styles:
                styles.add(ParagraphStyle(name='h4_right', parent=styles['h4'], alignment=2)) # 2 = TA_RIGHT

            story = []

            story.append(Paragraph(title, styles['h2']))
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph(f"<b>Filtri applicati:</b> {filters_applied}", styles['Normal']))
            story.append(Spacer(1, 0.2 * inch))
            
            table_data_pdf = []
            header_row_pdf = []
            for col in df_data.columns:
                if col == 'Voce':
                    header_row_pdf.append(Paragraph(col, styles['h4_bold'])) 
                else:
                    header_row_pdf.append(Paragraph(col, styles['h4_right'])) 
            table_data_pdf.append(header_row_pdf)

            for index, row in df_data.iterrows():
                row_list = []
                structure_item_found = next((item for item in report_structure_sp if item['Voce'].upper() == row['Voce'].upper() or item['Voce'] == row['Voce']), None) # Per lo SP
                is_bold_row = structure_item_found.get('Grassetto', False) if structure_item_found else False
                
                for col_name in df_data.columns:
                    cell_value = row[col_name]
                    formatted_cell_value = str(cell_value) 
                    
                    if col_name != 'Voce': 
                        try:
                            formatted_cell_value = f"{int(cell_value):,}".replace(",", "X").replace(".", ",").replace("X", ".")
                        except (ValueError, TypeError):
                            pass 
                    
                    if is_bold_row:
                        row_list.append(Paragraph(formatted_cell_value, styles['h4_bold']))
                    elif col_name != 'Voce': 
                        row_list.append(Paragraph(formatted_cell_value, styles['h4_right'])) 
                    else: 
                        row_list.append(Paragraph(formatted_cell_value, styles['Normal']))
                table_data_pdf.append(row_list)


            col_widths_pdf = [doc.width / len(df_data.columns)] * len(df_data.columns)
            col_widths_pdf[0] = doc.width * 0.3 
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
                ('GRID', (0, 0), (-1, -1), 0.25, colors.white), 
            ])
            
            table = Table(table_data_pdf, colWidths=col_widths_pdf)
            table.setStyle(table_style)
            story.append(table)

            doc.build(story)
            buffer.seek(0)
            return buffer

        pdf_buffer_riclass = generate_pdf_riclassified(df_export_riclassificato_actual, "Report Stato Patrimoniale Riclassificato", 
                                                    f"Cliente: {selected_cliente} | Anno: {selected_anni} | Sezione: {selected_sezione}")
        
        st.download_button(
            label="Esporta Stato Patrimoniale in PDF",
            data=pdf_buffer_riclass,
            file_name="stato_patrimoniale_riclassificato.pdf",
            mime="application/pdf",
            help="Esporta lo Stato Patrimoniale riclassificato in un file PDF."
        )
else:
    st.info("Nessun dato da esportare.")
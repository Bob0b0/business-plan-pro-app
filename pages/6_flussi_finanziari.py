# pages/report_flussi_finanziari.py - Business Plan Pro v6.0 - PDF Professionale
# Layout verticale, una pagina, senza fronzoli

import streamlit as st
import sqlite3
import pandas as pd
import sidebar_filtri 
import io
import plotly.graph_objects as go
from reportlab.lib.pagesizes import A4, portrait
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle 
from reportlab.lib.units import inch
from streamlit.components.v1 import html
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import tempfile
import os
from datetime import datetime
import financial_model 

try:
    from ascii_table_generator import create_downloadable_ascii_report
    ASCII_AVAILABLE = True
except ImportError:
    ASCII_AVAILABLE = False

def safe_string_to_float(value):
    """Converte stringhe formattate in float gestendo numeri negativi tra parentesi"""
    if pd.isna(value) or value == "" or value == "0":
        return 0.0
    
    try:
        str_val = str(value).strip()
        is_negative = False
        if str_val.startswith('(') and str_val.endswith(')'):
            is_negative = True
            str_val = str_val[1:-1]
        
        str_val = str_val.replace('.', '').replace('€', '').replace(' ', '').replace(',', '.')
        
        if str_val == '' or str_val == '-':
            return 0.0
        
        float_val = float(str_val)
        return -float_val if is_negative else float_val
        
    except (ValueError, TypeError):
        return 0.0

def generate_waterfall_chart_for_pdf(df_multi, years_list, temp_dir):
    """Genera grafico waterfall pulito per PDF con progressione cumulativa corretta"""
    try:
        # Trova la colonna con il periodo più lungo
        longest_period_col = None
        max_years_span = 0
        
        for col in df_multi.columns:
            if col != 'Voce' and '→' in col:
                years = col.split('→')
                span = int(years[1]) - int(years[0])
                if span > max_years_span:
                    max_years_span = span
                    longest_period_col = col
        
        if not longest_period_col:
            return None
            
        # Estrazione dati con la stessa logica del frontend
        voci_da_escludere_grafico = {
            'FLUSSO MONETARIO OPERATIVO',
            'FLUSSO MONETARIO NETTO', 
            'CALCOLO DI CONFERMA',
            'PFN INIZIO PERIODO',
            'PFN FINE PERIODO',
            'VARIAZIONE'
        }
        
        waterfall_data = {}
        
        for _, row in df_multi.iterrows():
            voce = row['Voce'].strip()
            voce_upper = voce.upper()
            
            if any(exclude_pattern in voce_upper for exclude_pattern in voci_da_escludere_grafico):
                continue
            
            valore = safe_string_to_float(row[longest_period_col])
            
            if 'EBITDA' in voce_upper and 'FLUSSO' not in voce_upper:
                waterfall_data['EBITDA'] = valore
            elif 'VARIAZIONI CCN' in voce_upper or 'VARIAZIONE CCN' in voce_upper:
                waterfall_data['Variazioni CCN'] = valore
            elif 'AMMORTAMENTI' in voce_upper and 'FLUSSO' not in voce_upper:
                waterfall_data['Ammortamenti'] = valore
            elif ('TFR' in voce_upper and 'VARIAZIONE' in voce_upper) or ('FONDI' in voce_upper and 'MLT' in voce_upper):
                waterfall_data['Variazione TFR, fondi e altri MLT'] = valore
            elif 'FLUSSO' in voce_upper and 'INVESTIMENTO' in voce_upper and 'ATTIVITÀ' in voce_upper:
                waterfall_data['Flusso mon. da attività di investimento'] = valore
            elif 'INVESTIMENTO' in voce_upper and 'FLUSSO' not in voce_upper:
                waterfall_data['Investimenti'] = valore
            elif 'GESTIONE FINANZIARIA' in voce_upper and 'FLUSSO' not in voce_upper:
                waterfall_data['Gestione Finanziaria'] = valore
            elif 'IMPOSTE' in voce_upper and 'FLUSSO' not in voce_upper:
                waterfall_data['Imposte'] = valore
            elif 'AUMENTI' in voce_upper and 'CAPITALE' in voce_upper:
                waterfall_data['Aumenti di Capitale'] = valore
            elif 'NON OPERATIVA' in voce_upper or 'ACCANTONAMENTI' in voce_upper:
                waterfall_data['Gestione Non Operativa'] = valore
        
        if 'EBITDA' not in waterfall_data or waterfall_data['EBITDA'] == 0:
            return None
        
        # Preparazione dati per il grafico con progressione cumulativa
        labels = ["EBITDA"]
        values = [waterfall_data.get('EBITDA', 0)]
        cumulative = values[0]
        
        components = [
            ('Ammortamenti', '#32CD32'),
            ('Variazioni CCN', '#DC143C'),
            ('Variazione TFR, fondi e altri MLT', '#FF6347'),
            ('Investimenti', '#8B0000'),
            ('Flusso mon. da attività di investimento', '#4B0082'),
            ('Aumenti di Capitale', '#32CD32'),
            ('Gestione Finanziaria', '#4169E1'),
            ('Gestione Non Operativa', '#9370DB'),
            ('Imposte', '#FF4500')
        ]
        
        for comp_name, color in components:
            if comp_name in waterfall_data and waterfall_data[comp_name] != 0:
                labels.append(comp_name)
                values.append(waterfall_data[comp_name])
                cumulative += waterfall_data[comp_name]
        
        labels.append("Flusso Monetario Netto")
        values.append(cumulative)
        
        # Creazione del grafico con matplotlib
        fig, ax = plt.subplots(figsize=(8, 5))
        
        # Calcolo delle posizioni delle barre
        bottoms = [0]
        for i in range(1, len(values)-1):
            bottoms.append(bottoms[i-1] + values[i-1])
        
        # Barre intermedie (relative)
        for i in range(1, len(values)-1):
            ax.bar(labels[i], values[i], bottom=bottoms[i], 
                  color='#DC143C' if values[i] < 0 else '#2E8B57',
                  alpha=0.8, edgecolor='black', linewidth=0.5)
        
        # Barra iniziale (EBITDA) e finale (Totale)
        ax.bar(labels[0], values[0], color='#2E8B57', alpha=0.8, edgecolor='black', linewidth=0.5)
        ax.bar(labels[-1], values[-1], color='#1f77b4', alpha=0.8, edgecolor='black', linewidth=0.5)
        
        # Aggiunta delle etichette
        for i in range(len(labels)):
            height = values[i]
            y_pos = bottoms[i] + height if height >= 0 else bottoms[i] + height/2
            label = f'{abs(height)/1000:.0f}k' if abs(height) >= 1000 else f'{height:.0f}'
            ax.text(i, y_pos, label, ha='center', va='center',
                   fontsize=9, fontweight='bold')
        
        ax.set_title(f'Analisi Flussi {longest_period_col}', fontsize=12, fontweight='bold')
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=9, rotation=45, ha='right')
        ax.grid(axis='y', alpha=0.3)
        ax.axhline(y=0, color='black', linewidth=1)
        
        # Formattazione asse Y
        max_val = max(abs(min(values)), abs(max(values)))
        if max_val >= 1000000:
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000000:.1f}M'))
        elif max_val >= 1000:
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}k'))
        
        plt.tight_layout()
        
        chart_path = os.path.join(temp_dir, 'waterfall_simple.png')
        plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return chart_path
        
    except Exception as e:
        print(f"Errore grafico PDF: {e}")
        return None

def generate_pdf_flussi_multi_column(df_data, years_list, combinations, title, filters_applied):
    """PDF professionale: una pagina, TUTTE le righe, matematica corretta"""
    buffer = io.BytesIO()
    temp_dir = tempfile.mkdtemp()
    
    try:
        doc = SimpleDocTemplate(buffer, pagesize=portrait(A4), 
                               topMargin=0.4*inch, bottomMargin=0.4*inch,
                               leftMargin=0.6*inch, rightMargin=0.6*inch)
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], 
                                   fontSize=14, spaceAfter=8, alignment=1)
        subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], 
                                      fontSize=9, spaceAfter=12, alignment=1)
        
        story = []

        story.append(Paragraph("REPORT FLUSSI DI CASSA", title_style))
        
        periodo_info = f"{filters_applied} | Periodo: {', '.join([f'{c[0]}→{c[1]}' for c in combinations])}"
        story.append(Paragraph(periodo_info, subtitle_style))

        # === TABELLA CON TUTTE LE RIGHE (non filtrata) ===
        table_data = []
        
        headers = ['Voce']
        for col in df_data.columns[1:]:
            headers.append(col)
        table_data.append(headers)

        # INCLUDI TUTTE LE RIGHE con IMPORTI INTERI
        for _, row in df_data.iterrows():
            voce = str(row['Voce'])
            
            # Salta solo la riga di intestazione "ANALISI DEI FLUSSI FINANZIARI" con valore 0
            if 'ANALISI DEI FLUSSI' in voce.upper() and all(safe_string_to_float(row[col]) == 0 for col in df_data.columns[1:]):
                continue
                
            # Abbrevia solo se necessario per layout
            if len(voce) > 45:
                voce = voce[:42] + "..."
            
            row_data = [voce]
            
            # Formatta valori numerici MANTENENDO IMPORTI INTERI
            for col in df_data.columns[1:]:
                value = safe_string_to_float(row[col])
                if value == 0:
                    formatted = "-"
                else:
                    # FORMATO INTERO come richiesto
                    formatted = f"{value:,.0f}".replace(',', '.')
                row_data.append(formatted)
            
            table_data.append(row_data)

        # Crea tabella con font più piccolo per includere tutto
        table = Table(table_data)
        table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            
            # Corpo tabella
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),      
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),    
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),  # Font più piccolo per più righe
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            
            # Bordi
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.2 * inch))

        # === GRAFICO MATEMATICAMENTE CORRETTO ===
        chart_path = generate_waterfall_chart_for_pdf(df_data, years_list, temp_dir)
        
        if chart_path and os.path.exists(chart_path):
            # Dimensioni ridotte per lasciare spazio alla tabella completa
            chart_width = doc.width * 0.8
            chart_height = chart_width * 0.5  # Più basso per stare in una pagina
            chart_image = Image(chart_path, width=chart_width, height=chart_height)
            story.append(chart_image)

        # Footer
        story.append(Spacer(1, 0.1 * inch))
        footer = Paragraph(f"Generato: {datetime.now().strftime('%d/%m/%Y')}", 
                          ParagraphStyle('Footer', parent=styles['Normal'], 
                                       fontSize=7, alignment=1))
        story.append(footer)

        doc.build(story)
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        print(f"Errore PDF: {e}")
        return None
        
    finally:
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except:
            pass

def generate_simple_table_pdf(df_data, years_list, title, filters_applied):
    """Fallback PDF solo tabella"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=portrait(A4))
    styles = getSampleStyleSheet()
    
    story = []
    story.append(Paragraph(title, styles['Heading1']))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(f"{filters_applied}", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    
    table_data = [df_data.columns.tolist()]
    for _, row in df_data.iterrows():
        formatted_row = []
        for i, val in enumerate(row.tolist()):
            if i == 0:
                formatted_row.append(str(val))
            else:
                numeric_val = safe_string_to_float(val)
                formatted_row.append(f"{numeric_val:,.0f}".replace(',', '.') if numeric_val != 0 else "-")
        table_data.append(formatted_row)
    
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    doc.build(story)
    buffer.seek(0)
    return buffer

sidebar_filtri.display_sidebar_filters()

def get_database_name():
    """Restituisce il database dell'utente corrente"""
    username = st.session_state.get('username')
    if username:
        return f"business_plan_{username}.db"
    return "business_plan_pro.db"

DATABASE_NAME = get_database_name()

selected_cliente = st.session_state.selected_cliente
selected_anni = st.session_state.selected_anni 
selected_sezione = st.session_state.selected_sezione 

st.title("💰 Report Flussi di Cassa Multi-Anno")

st.markdown("""
**Analisi Completa dei Flussi di Cassa Aziendali**

Il report mostra l'evoluzione dei flussi di cassa su più anni con:
- **Colonne multiple**: Confronti 2022→2023, 2023→2024, 2022→2024
- **Grafico a cascata intelligente**: Logica mista per valori assoluti e variazioni
- **Analisi completa**: Dalla conversione EBITDA al flusso monetario disponibile
- **Export PDF professionale**: Formato compatto su una pagina
""")

st.markdown(f"**Filtri applicati:** Cliente: **{selected_cliente}** | Anni: **{', '.join(selected_anni) if selected_anni else 'Tutti'}**")
st.markdown("---") 

years_to_display = []
if selected_anni:
    years_to_display = sorted([int(y) for y in selected_anni])
else: 
    all_available_years = sorted([int(y) for y in st.session_state.anni_tutti_disponibili])
    years_to_display = all_available_years

if len(years_to_display) < 2:
    st.warning(f"Per calcolare i flussi, sono necessari dati per almeno due anni. Disponibili: {years_to_display}")
    st.stop()

st.info(f"📅 **Anni per l'analisi**: {', '.join(map(str, years_to_display))} • **Totale**: {len(years_to_display)} esercizi")

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

if df_full_data.empty:
    st.error("Nessun dato trovato per gli anni selezionati. Verifica che ci siano dati nel database per questi anni.")
    st.stop()

def calculate_multi_column_flows(df_data, years_list):
    """Calcola flussi per tutte le combinazioni di anni"""
    
    flows_results = {}
    flow_combinations = []
    
    for i in range(len(years_list)):
        for j in range(i + 1, len(years_list)):
            year_from = years_list[i]
            year_to = years_list[j]
            combination = (year_from, year_to)
            flow_combinations.append(combination)
    
    for year_from, year_to in flow_combinations:
        try:
            years_pair = [year_from, year_to]
            
            calculated_reports = financial_model.calculate_all_reports(
                df_data, 
                years_pair,
                financial_model.report_structure_ce,
                financial_model.report_structure_sp,
                financial_model.report_structure_ff
            )
            
            if 'error' not in calculated_reports:
                column_name = f"{year_from}→{year_to}"
                flows_results[column_name] = calculated_reports['ff']
                
        except Exception as e:
            st.warning(f"Errore nel calcolo flusso {year_from}→{year_to}: {e}")
            continue
    
    return flows_results, flow_combinations

try:
    flows_multi_results, combinations = calculate_multi_column_flows(df_full_data, years_to_display)
    
    if not flows_multi_results:
        st.error("Impossibile calcolare i flussi per le combinazioni di anni selezionate.")
        st.stop()
        
except Exception as e:
    st.error(f"Errore durante il calcolo dei flussi multi-colonna: {e}")
    st.stop()

def merge_flows_dataframes(flows_dict):
    """Unisce tutti i DataFrame dei flussi in uno con colonne multiple"""
    
    if not flows_dict:
        return pd.DataFrame()
    
    first_key = list(flows_dict.keys())[0]
    df_merged = flows_dict[first_key][['Voce']].copy()
    
    for column_name, df_flow in flows_dict.items():
        if len(df_flow.columns) > 1:
            year_col = df_flow.columns[1]
            df_merged[column_name] = df_flow[year_col]
    
    return df_merged

df_final_multi = merge_flows_dataframes(flows_multi_results)

if not df_final_multi.empty:
    st.markdown("### 📊 Visualizzazione Tabellare Multi-Anno")
    
    def display_multi_column_html(df, structure):
        """Visualizza tabella HTML con colonne multiple"""
        if df.empty:
            return
        
        bold_rows = [item['Voce'] for item in structure if item.get('Grassetto', False)]
        
        df_display = df.copy()
        for col in df_display.columns:
            if col != 'Voce':
                df_display[col] = df_display[col].apply(
                    lambda x: financial_model.format_number(x) if pd.notnull(x) and x != 0 else ""
                )

        html_table = """
        <style>
            .multi-table {
                width: 100%;
                border-collapse: collapse;
                font-family: Arial, sans-serif;
                margin: 1em 0;
                font-size: 0.9em;
            }
            .multi-table th, .multi-table td {
                border: 1px solid #e0e0e0;
                padding: 6px 10px;
                text-align: left;
            }
            .multi-table th {
                background-color: #f8f9fa;
                font-weight: bold;
                color: #2c3e50;
            }
            .multi-table td.numeric {
                text-align: right;
                font-family: inherit;
            }
            .multi-table tr.bold-row td {
                font-weight: bold;
                background-color: #f0f8ff;
            }
            .multi-table td.uppercase-text {
                text-transform: uppercase;
            }
            .multi-table th.year-header {
                background-color: #e3f2fd;
                color: #1565c0;
            }
        </style>
        <table class="multi-table">
            <thead>
                <tr>
        """
        
        html_table += "<th>Voce</th>" 
        for col in df_display.columns:
            if col != 'Voce':
                html_table += f"<th class='numeric year-header'>{col}</th>" 
        html_table += "</tr></thead><tbody>"
        
        for _, row in df_display.iterrows(): 
            row_class = ""
            if row['Voce'] in bold_rows:
                row_class += "bold-row "
            
            html_table += f"<tr class='{row_class.strip()}'>"
            
            cell_content_voce = str(row['Voce'])
            cell_class_voce = ""
            item_struct = next((item for item in structure if item['Voce'].upper() == row['Voce'].upper() or item['Voce'] == row['Voce']), None)
            if item_struct and item_struct.get('Maiuscolo', False):
                cell_class_voce = "uppercase-text"
            
            html_table += f"<td class='{cell_class_voce}'>{cell_content_voce}</td>"
            
            for col in df_display.columns:
                if col != 'Voce':
                    val_to_display = row[col]
                    html_table += f"<td class='numeric'>{val_to_display}</td>" 
            
            html_table += "</tr>"
        
        html_table += "</tbody></table>"
        
        table_height = len(df) * 35 + (len(df.columns) * 5) + 120
        html(html_table, height=min(table_height, 800), scrolling=True)

    display_multi_column_html(df_final_multi, financial_model.report_structure_ff)

    st.markdown("---")
    st.markdown("### 📊 Grafico a Cascata Intelligente - Analisi Triennale")
    
    def create_intelligent_waterfall(df_multi, years_list):
        """Crea grafico a cascata con logica mista per valori assoluti e variazioni"""
        
        if df_multi.empty or len(years_list) < 2:
            st.info("Dati insufficienti per il grafico a cascata intelligente.")
            return
        
        st.markdown("#### 🧮 Logica di Calcolo:")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **📈 Valori Assoluti (Somma):**
            - EBITDA: 2022+2023+2024
            - Ammortamenti: 2022+2023+2024  
            - Investimenti: 2022+2023+2024
            - Imposte: 2022+2023+2024
            """)
        
        with col2:
            st.markdown("""
            **🔄 Variazioni (Differenza):**
            - CCN: 2024-2022
            - TFR e Fondi MLT: 2024-2022
            - Gestione Finanziaria: 2024-2022
            """)
        
        longest_period_col = None
        max_years_span = 0
        
        for col in df_multi.columns:
            if col != 'Voce' and '→' in col:
                years = col.split('→')
                span = int(years[1]) - int(years[0])
                if span > max_years_span:
                    max_years_span = span
                    longest_period_col = col
        
        if not longest_period_col:
            st.warning("Nessuna colonna di flusso trovata per il grafico.")
            return
            
        st.markdown(f"**📊 Grafico basato su periodo:** `{longest_period_col}` (span: {max_years_span} anni)")
        
        voci_da_escludere_grafico = {
            'FLUSSO MONETARIO OPERATIVO',
            'FLUSSO MONETARIO NETTO', 
            'CALCOLO DI CONFERMA',
            'PFN INIZIO PERIODO',
            'PFN FINE PERIODO',
            'VARIAZIONE'
        }
        
        waterfall_data = {}
        
        for _, row in df_multi.iterrows():
            voce = row['Voce'].strip()
            voce_upper = voce.upper()
            
            if any(exclude_pattern in voce_upper for exclude_pattern in voci_da_escludere_grafico):
                continue
            
            valore = safe_string_to_float(row[longest_period_col])
            
            if 'EBITDA' in voce_upper and 'FLUSSO' not in voce_upper:
                waterfall_data['EBITDA'] = valore
            elif 'VARIAZIONI CCN' in voce_upper or 'VARIAZIONE CCN' in voce_upper:
                waterfall_data['Variazioni CCN'] = valore
            elif 'AMMORTAMENTI' in voce_upper and 'FLUSSO' not in voce_upper:
                waterfall_data['Ammortamenti'] = valore
            elif ('TFR' in voce_upper and 'VARIAZIONE' in voce_upper) or ('FONDI' in voce_upper and 'MLT' in voce_upper):
                waterfall_data['Variazione TFR, fondi e altri MLT'] = valore
            elif 'FLUSSO' in voce_upper and 'INVESTIMENTO' in voce_upper and 'ATTIVITÀ' in voce_upper:
                waterfall_data['Flusso mon. da attività di investimento'] = valore
            elif 'INVESTIMENTO' in voce_upper and 'FLUSSO' not in voce_upper:
                waterfall_data['Investimenti'] = valore
            elif 'GESTIONE FINANZIARIA' in voce_upper and 'FLUSSO' not in voce_upper:
                waterfall_data['Gestione Finanziaria'] = valore
            elif 'IMPOSTE' in voce_upper and 'FLUSSO' not in voce_upper:
                waterfall_data['Imposte'] = valore
            elif 'AUMENTI' in voce_upper and 'CAPITALE' in voce_upper:
                waterfall_data['Aumenti di Capitale'] = valore
            elif 'NON OPERATIVA' in voce_upper or 'ACCANTONAMENTI' in voce_upper:
                waterfall_data['Gestione Non Operativa'] = valore
        
        if 'EBITDA' not in waterfall_data or waterfall_data['EBITDA'] == 0:
            st.warning("Non è stato trovato l'EBITDA. Impossibile creare il grafico a cascata.")
            st.info(f"Voci disponibili nel dataframe: {list(df_multi['Voce'].unique())}")
            return
        
        labels = ["EBITDA"]
        values = [waterfall_data.get('EBITDA', 0)]
        measures = ["absolute"]
        colors_list = ["#2E8B57"]
        
        components = [
            ('Ammortamenti', '#32CD32'),
            ('Variazioni CCN', '#DC143C'),
            ('Variazione TFR, fondi e altri MLT', '#FF6347'),
            ('Investimenti', '#8B0000'),
            ('Flusso mon. da attività di investimento', '#4B0082'),
            ('Aumenti di Capitale', '#32CD32'),
            ('Gestione Finanziaria', '#4169E1'),
            ('Gestione Non Operativa', '#9370DB'),
            ('Imposte', '#FF4500')
        ]
        
        for comp_name, color in components:
            if comp_name in waterfall_data and waterfall_data[comp_name] != 0:
                labels.append(comp_name)
                values.append(waterfall_data[comp_name])
                measures.append("relative")
                colors_list.append(color)
        
        flusso_calcolato = values[0]
        for i in range(1, len(values)):
            flusso_calcolato += values[i]
        
        labels.append("Flusso Monetario Netto")
        values.append(flusso_calcolato)
        measures.append("total")
        colors_list.append("#1f77b4")
        
        text_values = []
        for val in values:
            text_values.append(f"€ {val:,.0f}".replace(',', '.'))
        
        fig = go.Figure(go.Waterfall(
            name="Conversione EBITDA in Flusso Monetario",
            orientation="v",
            measure=measures,
            x=labels,
            textposition="outside",
            text=text_values,
            y=values,
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            increasing={"marker": {"color": "#2E8B57"}},
            decreasing={"marker": {"color": "#DC143C"}},
            totals={"marker": {"color": "#1f77b4"}}
        ))
        
        fig.update_layout(
            title=f"Conversione EBITDA → Flusso Monetario • Periodo: {longest_period_col}",
            showlegend=False,
            height=700,
            xaxis_title="Componenti del Flusso",
            yaxis_title="Importo (€)",
            font=dict(size=10),
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(tickangle=45),
            yaxis=dict(
                gridcolor='lightgray',
                gridwidth=1,
                zeroline=True,
                zerolinecolor='black',
                zerolinewidth=2
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("📈 Statistiche del Periodo"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "EBITDA Totale", 
                    f"€ {waterfall_data.get('EBITDA', 0):,.0f}".replace(',', '.'),
                    help=f"Somma EBITDA per periodo {longest_period_col}"
                )
            
            with col2:
                ccn_variation = waterfall_data.get('Variazioni CCN', 0)
                st.metric(
                    "Impatto CCN", 
                    f"€ {ccn_variation:,.0f}".replace(',', '.'),
                    delta=f"{'Positivo' if ccn_variation > 0 else 'Negativo'} per liquidità"
                )
            
            with col3:
                st.metric(
                    "Flusso Netto", 
                    f"€ {flusso_calcolato:,.0f}".replace(',', '.'),
                    delta=f"{'Generazione' if flusso_calcolato > 0 else 'Assorbimento'} liquidità"
                )

    create_intelligent_waterfall(df_final_multi, years_to_display)

    st.markdown("---")
    st.subheader("📥 Esporta Flussi Multi-Anno")

    if not df_final_multi.empty:
        col_excel, col_pdf, col_ascii = st.columns(3)

        with col_excel:
            try:
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                    df_export = df_final_multi.copy()
                    
                    for col in df_export.columns:
                        if col != 'Voce':
                            df_export[col] = df_export[col].apply(safe_string_to_float)
                    
                    df_export.to_excel(writer, index=False, sheet_name='Flussi Multi-Anno')
                    
                    workbook = writer.book
                    worksheet = writer.sheets['Flussi Multi-Anno']
                    
                    num_format = workbook.add_format({'num_format': '#,##0'})
                    for i, col in enumerate(df_export.columns):
                        if col != 'Voce':
                            worksheet.set_column(i, i, 15, num_format)

                excel_buffer.seek(0)
                st.download_button(
                    label="📊 Excel Multi-Colonna",
                    data=excel_buffer,
                    file_name=f"flussi_multi_anno_{'-'.join(map(str, years_to_display))}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Excel con gestione corretta numeri negativi tra parentesi"
                )
                
                st.success("✅ Excel con BUGFIX applicato")
                
            except Exception as e:
                st.error(f"Errore Excel: {e}")

        with col_pdf:
            try:
                if not df_final_multi.empty:
                    pdf_buffer_flussi = generate_pdf_flussi_multi_column(
                        df_final_multi, 
                        years_to_display,
                        combinations,
                        "REPORT FLUSSI DI CASSA", 
                        f"Cliente: {selected_cliente} | Anni: {', '.join(str(y) for y in years_to_display)}"
                    )
                    
                    if pdf_buffer_flussi:
                        st.download_button(
                            label="PDF Professionale",
                            data=pdf_buffer_flussi,
                            file_name=f"flussi_report_{'-'.join(map(str, years_to_display))}.pdf",
                            mime="application/pdf",
                            help="Report professionale: una pagina, layout verticale"
                        )
                        
                        st.success("PDF Professionale - Una pagina")
                        
                    else:
                        st.error("Errore nella generazione del PDF")
                else:
                    st.warning("Nessun dato disponibile per il PDF")
                    
            except Exception as e:
                st.error(f"Errore PDF: {e}")
                try:
                    simple_pdf = generate_simple_table_pdf(
                        df_final_multi, 
                        years_to_display,
                        "REPORT FLUSSI DI CASSA",
                        f"Cliente: {selected_cliente} | Anni: {', '.join(str(y) for y in years_to_display)}"
                    )
                    if simple_pdf:
                        st.download_button(
                            label="PDF Fallback",
                            data=simple_pdf,
                            file_name=f"flussi_simple_{'-'.join(map(str, years_to_display))}.pdf",
                            mime="application/pdf",
                            help="PDF semplificato - solo tabella"
                        )
                        st.info("PDF fallback disponibile")
                except Exception as fallback_error:
                    st.error(f"Impossibile generare PDF: {fallback_error}")

        with col_ascii:
            if ASCII_AVAILABLE:
                try:
                    ascii_content = df_final_multi.to_string(index=False)
                    ascii_buffer = io.BytesIO()
                    ascii_buffer.write(ascii_content.encode('utf-8'))
                    ascii_buffer.seek(0)
                    
                    st.download_button(
                        label="📝 Testo ASCII",
                        data=ascii_buffer,
                        file_name=f"flussi_ascii_{'-'.join(map(str, years_to_display))}.txt",
                        mime="text/plain",
                        help="Formato testo per email/console"
                    )
                except Exception as e:
                    st.error(f"Errore ASCII: {e}")
            else:
                st.info("ASCII non disponibile")

    with st.expander("💡 Come interpretare il Report Multi-Anno"):
        st.markdown("""
        ### 📊 **Lettura delle Colonne Multiple:**
        
        **🔄 Confronti Anno su Anno:**
        - `2022→2023`: Variazione dei flussi dal 2022 al 2023
        - `2023→2024`: Variazione dei flussi dal 2023 al 2024  
        - `2022→2024`: Variazione complessiva biennale
        
        **📈 Analisi Trend:**
        - **Valori positivi**: Miglioramento nella generazione di cassa
        - **Valori negativi**: Assorbimento di liquidità
        - **Confronto colonne**: Identificazione di trend in accelerazione/decelerazione
        
        **🎯 Grafico a Cascata Intelligente:**
        - **Filtrato**: Esclude automaticamente voci di totale 
        - **Solo dettagli**: Mostra solo le componenti base (EBITDA, CCN, Investimenti, etc.)
        - **Interpretazione**: Mostra la conversione dell'EBITDA in flusso disponibile
        - **Focus**: Identifica i principali assorbitori/generatori di liquidità
        
        **📄 Export PDF Professionale:**
        - **Una pagina**: Layout verticale ottimizzato
        - **Tabella essenziale**: Solo voci business-critical
        - **Grafico integrato**: Waterfall semplificato
        - **Zero fronzoli**: Formato pronto per invio esterno
        
        **🚀 Utilizzo Strategico:**
        - **Pianificazione**: Previsione fabbisogni di liquidità
        - **Controllo**: Monitoraggio efficacia gestione del capitale circolante  
        - **Investimenti**: Valutazione sostenibilità piani di sviluppo
        """)

else:
    st.info("Nessun dato da visualizzare per il calcolo dei flussi multi-anno.")

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9em; margin-top: 2em;'>
    <b>🔧 Business Plan Pro v6.0</b> • Flussi Finanziari Multi-Anno<br/>
    ✅ BUGFIX Excel • 📄 PDF Professionale • 📊 Waterfall Ottimizzato<br/>
    <i>Aggiornato: 26 Luglio 2025 - PDF Una Pagina Verticale</i>
</div>
""", unsafe_allow_html=True)
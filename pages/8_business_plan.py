# pages/8_business_plan.py - VERSIONE DEFINITIVA E COMPLETA - 2025-06-21
# Correzione finale: Sistemato l'inserimento dei decimali nella tabella delle assumption.

import streamlit as st
import pandas as pd
import numpy as np
import sidebar_filtri
import io
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from streamlit.components.v1 import html

# Import per PDF professionale
try:
    from reportlab.lib.pagesizes import A4, landscape, portrait
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Import per ASCII professionale
try:
    from ascii_table_generator import create_downloadable_ascii_report
    ASCII_AVAILABLE = True
except ImportError:
    ASCII_AVAILABLE = False

# Import moduli business plan
try:
    from business_plan_assumptions import (
        BusinessPlanAssumptions,
        ASSUMPTION_DEFINITIONS,
        get_anni_disponibili,
        determina_anno_base,
        genera_anni_business_plan
    )
    from business_plan_projections import BusinessPlanProjections
    BP_MODULES_AVAILABLE = True
except ImportError as e:
    BP_MODULES_AVAILABLE = False
    st.error(f"Moduli Business Plan non disponibili: {e}")

# Importa financial_model per i calcoli esistenti
import financial_model

# --- FUNZIONI SUPPORTO SALVATAGGIO ---

def save_assumptions_to_db(cliente: str, scenario_name: str, assumptions: dict, anni_bp: list, durata: int) -> None:
    """Salva le assumption nel database"""
    
    conn = None
    try:
        conn = sqlite3.connect("business_plan_pro.db")
        cursor = conn.cursor()
        
        # Crea tabella se non esiste
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bp_scenarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente TEXT NOT NULL,
                scenario_name TEXT NOT NULL,
                assumptions_json TEXT NOT NULL,
                anni_bp_json TEXT NOT NULL,
                durata INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(cliente, scenario_name)
            )
        """)
        
        # Converte in JSON
        assumptions_json = json.dumps(assumptions)
        anni_bp_json = json.dumps(anni_bp)
        
        # Insert o Update
        cursor.execute("""
            INSERT OR REPLACE INTO bp_scenarios
            (cliente, scenario_name, assumptions_json, anni_bp_json, durata)
            VALUES (?, ?, ?, ?, ?)
        """, (cliente, scenario_name, assumptions_json, anni_bp_json, durata))
        
        conn.commit()
        
    except Exception as e:
        raise Exception(f"Errore nel salvataggio: {e}")
    finally:
        if conn:
            conn.close()


def get_saved_scenarios(cliente: str) -> List[str]:
    """Recupera la lista degli scenari salvati"""
    
    conn = None
    try:
        conn = sqlite3.connect("business_plan_pro.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT scenario_name
            FROM bp_scenarios
            WHERE cliente = ?
            ORDER BY created_at DESC
        """, (cliente,))
        
        results = cursor.fetchall()
        return [row[0] for row in results]
        
    except Exception as e:
        return []
    finally:
        if conn:
            conn.close()


def load_assumptions_from_db(cliente: str, scenario_name: str) -> Tuple[Optional[dict], Optional[list], Optional[int]]:
    """Carica le assumption di uno scenario"""
    
    conn = None
    try:
        conn = sqlite3.connect("business_plan_pro.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT assumptions_json, anni_bp_json, durata
            FROM bp_scenarios
            WHERE cliente = ? AND scenario_name = ?
        """, (cliente, scenario_name))
        
        result = cursor.fetchone()
        
        if result:
            assumptions_json, anni_bp_json, durata = result
            assumptions = json.loads(assumptions_json)
            anni_bp = json.loads(anni_bp_json)
            
            # Converte le chiavi in int
            converted_assumptions = {}
            for ass_id_str, anni_dict in assumptions.items():
                ass_id = int(ass_id_str)
                converted_assumptions[ass_id] = {}
                for anno_str, valore in anni_dict.items():
                    anno = int(anno_str)
                    converted_assumptions[ass_id][anno] = float(valore)
            
            return converted_assumptions, anni_bp, durata
        else:
            return None, None, None
            
    except Exception as e:
        return None, None, None
    finally:
        if conn:
            conn.close()

# --- FUNZIONI FORMATTAZIONE CORRETTE ---

def safe_format_number(value, use_thousands_sep=True):
    """Formatta un numero in modo sicuro con separatori delle migliaia"""
    try:
        if pd.isna(value) or not np.isfinite(value):
            return "0"
        
        num = float(value)
        
        if num == 0:
            return "0"
        
        if use_thousands_sep:
            if num < 0:
                return f"({abs(num):,.0f})".replace(",", ".")
            else:
                return f"{num:,.0f}".replace(",", ".")
        else:
            return f"{num:.0f}"
            
    except (ValueError, TypeError, OverflowError):
        return "0"


def display_with_html_bp(df, years, structure_name="Business Plan"):
    """Rendering HTML personalizzato per Business Plan"""
    if df.empty:
        return
    
    html_table = """
    <style>
        .custom-table-bp { width: 100%; border-collapse: collapse; font-family: Arial, sans-serif; margin: 1em 0; }
        .custom-table-bp th, .custom-table-bp td { border: 1px solid #e0e0e0; padding: 8px 12px; text-align: left; }
        .custom-table-bp th { background-color: #f0f0f0; font-weight: bold; }
        .custom-table-bp td.numeric { text-align: right; }
        .custom-table-bp tr.bold-row td { font-weight: bold; }
        .custom-table-bp td.uppercase-text { text-transform: uppercase; }
        .table-container { max-height: 600px; overflow-y: auto; overflow-x: auto; border: 1px solid #e0e0e0; }
        .custom-table-bp th:first-child, .custom-table-bp td:first-child { width: 40%; min-width: 300px; max-width: 450px; }
        .custom-table-bp th:not(:first-child), .custom-table-bp td:not(:first-child) { width: auto; min-width: 100px; }
    </style>
    <div class="table-container">
        <table class="custom-table-bp">
            <thead><tr>
    """
    html_table += "<th>Voce</th>"
    for year in years:
        html_table += f"<th class='numeric'>{year}</th>"
    html_table += "</tr></thead><tbody>"
    
    for _, row in df.iterrows():
        html_table += f"<tr>"
        for i, col_name in enumerate(df.columns):
            cell_value = row[col_name]
            cell_content = str(cell_value)
            cell_class = ""
            if col_name == 'Voce':
                cell_content = str(row['Voce'])
            else:
                cell_class = "numeric"
                cell_content = financial_model.format_number(cell_value)
            html_table += f"<td class='{cell_class}'>{cell_content}</td>"
        html_table += "</tr>"
    html_table += "</tbody></table></div>"
    html(html_table, height=min(len(df) * 45 + 150, 650), scrolling=True)


# --- FUNZIONE PDF MODIFICATA ---
def generate_professional_pdf_safe(df_data, title, subtitle, cliente, anni_bp):
    """Genera PDF professionale con margini stretti e intestazione minimale"""
    if not REPORTLAB_AVAILABLE:
        return None
    
    try:
        buffer = io.BytesIO()
        
        # ✅ MARGINI STRETTI: Impostazione margini ridotti (in punti: 1 inch = 72 punti)
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=landscape(A4),
            topMargin=20,      # ✅ RIDOTTO: era 72 (1 inch), ora 20 punti (~7mm)
            bottomMargin=20,   # ✅ RIDOTTO: era 72 (1 inch), ora 20 punti (~7mm)
            leftMargin=25,     # ✅ RIDOTTO: era 72 (1 inch), ora 25 punti (~9mm)
            rightMargin=25     # ✅ RIDOTTO: era 72 (1 inch), ora 25 punti (~9mm)
        )
        
        styles = getSampleStyleSheet()
        
        if 'bold_text' not in styles:
            styles.add(ParagraphStyle(name='bold_text', parent=styles['Normal'], fontName='Helvetica-Bold'))
        if 'normal_text' not in styles:
            styles.add(ParagraphStyle(name='normal_text', parent=styles['Normal'], fontName='Helvetica'))
        if 'right_text' not in styles:
            styles.add(ParagraphStyle(name='right_text', parent=styles['Normal'], alignment=2))
        if 'compact_right_text' not in styles:
            styles.add(ParagraphStyle(name='compact_right_text', parent=styles['Normal'],
                                    alignment=2, fontSize=8, fontName='Helvetica'))
        # ✅ NUOVO STILE: Intestazione minimale compatta
        if 'minimal_header' not in styles:
            styles.add(ParagraphStyle(
                name='minimal_header', 
                parent=styles['Normal'], 
                fontSize=10, 
                fontName='Helvetica',
                spaceAfter=6,  # Spazio ridotto dopo l'intestazione
                alignment=0    # Allineamento a sinistra
            ))

        story = []

        # ✅ INTESTAZIONE MINIMALE: Solo client e periodo, font piccolo
        minimal_header_text = f"{cliente} | {anni_bp[0]}-{anni_bp[-1]}"
        story.append(Paragraph(minimal_header_text, styles['minimal_header']))
        story.append(Spacer(1, 0.1 * inch))  # ✅ RIDOTTO: era 0.2 inch
        
        # ✅ ELIMINATA: L'intestazione completa con title e subtitle
        # story.append(Paragraph(title, styles['h2']))
        # story.append(Spacer(1, 0.2 * inch))
        # story.append(Paragraph(subtitle, styles['h3']))
        # story.append(Spacer(1, 0.1 * inch))
        # story.append(Paragraph(f"<b>Cliente:</b> {cliente} | <b>Periodo:</b> {anni_bp[0]}-{anni_bp[-1]}", styles['Normal']))
        # story.append(Spacer(1, 0.2 * inch))
        
        table_data_pdf = []
        
        header_row_pdf = [Paragraph(col, styles['bold_text']) for col in df_data.columns]
        table_data_pdf.append(header_row_pdf)

        for index, row in df_data.iterrows():
            row_list = []
            for col_name in df_data.columns:
                cell_value = row[col_name]
                if col_name == 'Voce':
                    voce_text = str(cell_value) if pd.notnull(cell_value) else ""
                    # ✅ TESTO PIÙ LUNGO: Aumentato da 40 a 55 caratteri per sfruttare meglio lo spazio
                    row_list.append(Paragraph(voce_text[:55], styles['normal_text']))
                else:
                    try:
                        formatted_value = financial_model.format_number(float(cell_value), pdf_format=True) if pd.notnull(cell_value) else "0"
                    except (ValueError, TypeError):
                        formatted_value = "0"
                    row_list.append(Paragraph(formatted_value, styles['compact_right_text']))
            table_data_pdf.append(row_list)

        # ✅ LARGHEZZA OTTIMIZZATA: Usa tutto lo spazio disponibile con margini ridotti
        col_widths_pdf = [doc.width * 0.35] + [(doc.width * 0.65) / (len(df_data.columns) - 1)] * (len(df_data.columns) - 1)

        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey), 
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'), 
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), 
            ('FONTSIZE', (0, 0), (-1, 0), 9),  # ✅ RIDOTTO: da 10 a 9
            ('FONTSIZE', (0, 1), (-1, -1), 7), # ✅ RIDOTTO: da 8 a 7
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),  # ✅ RIDOTTO: da 12 a 8
            ('TOPPADDING', (0, 1), (-1, -1), 3),    # ✅ RIDOTTO: padding interno celle
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3), # ✅ RIDOTTO: padding interno celle
            ('BACKGROUND', (0, 1), (-1, -1), colors.white), 
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'), 
            ('GRID', (0, 0), (-1, -1), 0.25, colors.gray),
        ])
        
        table = Table(table_data_pdf, colWidths=col_widths_pdf)
        table.setStyle(table_style)
        story.append(table)

        doc.build(story)
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        st.error(f"Errore nella generazione PDF: {e}")
        return None
# --- FUNZIONI EXPORT ---
def format_number_for_ascii_safe(value):
    try:
        if pd.isna(value) or not np.isfinite(value) or value == 0: return "0"
        return financial_model.format_number(float(value))
    except (ValueError, TypeError): return "0"

def prepare_export_data_safe(export_tipo, bp_projections):
    df_export = pd.DataFrame()
    title = "Business Plan"
    try:
        df_complete = bp_projections.get_dataframe_proiezioni()
        if df_complete.empty and not export_tipo.startswith('Excel'):
            return pd.DataFrame(), title

        if export_tipo.startswith('Overview'):
            kpi_codes = ['RI01', 'RI10', 'RI18', 'RI23', 'RI24', 'RI25', 'RI31', 'RI32', 'RI33']
            df_export = df_complete[df_complete['Codice'].isin(kpi_codes)].copy()
            df_export['Voce'] = df_export['Descrizione']
            df_export = df_export.drop(['Codice', 'Descrizione'], axis=1)
            title = "Business Plan - Overview KPI"
        elif export_tipo.startswith('Conto Economico'):
            df_export = bp_projections.get_report_ce_proiezioni()
            title = "Business Plan - Conto Economico"
        elif export_tipo.startswith('Stato Patrimoniale'):
            df_export = bp_projections.get_report_sp_proiezioni()
            title = "Business Plan - Stato Patrimoniale"
        else: # Excel
            return None, "Business Plan - Report Completo"

        if df_export is not None:
            for col in df_export.columns:
                if col != 'Voce' and str(col).isdigit():
                    df_export[col] = pd.to_numeric(df_export[col].replace([np.inf, -np.inf], 0).fillna(0), errors='coerce').fillna(0)
    except Exception as e:
        st.error(f"Errore nella preparazione dati export: {e}")
        return pd.DataFrame(), title
    return df_export, title


# --- INIZIO APPLICAZIONE ---

# Chiama la funzione per visualizzare i filtri nella sidebar (versione originale)
sidebar_filtri.display_sidebar_filters()

# --- INTESTAZIONE PRINCIPALE ---
st.title("🚀 Business Plan - Proiezioni Multi-Anno")

if not BP_MODULES_AVAILABLE:
    st.error("⚠️ Impossibile caricare i moduli del Business Plan.")
    st.stop()

st.markdown("""
### 📊 **Pianificazione Strategica e Proiezioni Finanziarie**
Crea proiezioni dettagliate basate su:
- **📈 Analisi storica**: Calcolo automatico delle medie e trend
- **🎯 Assumption personalizzabili**: Parametri chiave per le proiezioni
- **📋 Reports integrati**: Conto Economico, Stato Patrimoniale, Flussi di Cassa
- **⏱️ Durate flessibili**: Da 5 a 20 anni o personalizzata
""")
st.markdown("---")

# --- CONFIGURAZIONE BUSINESS PLAN ---
st.subheader("⚙️ Configurazione Business Plan")

selected_cliente = st.session_state.get('selected_cliente', 'Tutti')
if selected_cliente == 'Tutti':
    st.warning("⚠️ Seleziona un cliente specifico nella sidebar per procedere.")
    st.stop()
st.success(f"✅ **Cliente selezionato**: {selected_cliente}")

try:
    anni_disponibili = get_anni_disponibili(selected_cliente)
    anno_base = determina_anno_base(selected_cliente)
    if not anni_disponibili or not anno_base:
        st.error(f"❌ Nessun dato storico trovato per il cliente {selected_cliente}")
        st.stop()
    st.info(f"📅 **Anno base (N0)**: {anno_base} | **Anni storici disponibili**: {', '.join(map(str, anni_disponibili))}")
except Exception as e:
    st.error(f"Errore nel caricamento dati cliente: {e}")
    st.stop()

col1, col2 = st.columns([1, 2])
with col1:
    durata_tipo = st.selectbox("📅 **Durata Business Plan**:", options=['Standard', 'Personalizzata'])
with col2:
    if durata_tipo == 'Standard':
        durata_anni = st.selectbox("**Anni di proiezione**:", options=[5, 7, 10, 15, 20], index=2)
    else:
        durata_anni = st.number_input("**Anni di proiezione personalizzati**:", min_value=3, max_value=25, value=8)

anni_bp = genera_anni_business_plan(anno_base, durata_anni)
st.info(f"🎯 **Periodo Business Plan**: {anni_bp[0]} → {anni_bp[-1]} ({len(anni_bp)} anni, incluso consuntivo)")
st.markdown("---")

# --- CALCOLO MEDIE STORICHE ---
st.subheader("📊 Analisi Storica e Assumption")
if st.button("🔄 Calcola Medie Storiche", type="primary"):
    with st.spinner("Analizzando dati storici..."):
        try:
            bp_assumptions = BusinessPlanAssumptions(selected_cliente)
            dati_storici = bp_assumptions.carica_dati_storici(anni_disponibili)
            if dati_storici:
                medie_storiche = bp_assumptions.calcola_medie_storiche(anni_disponibili)
                st.session_state['bp_dati_storici'] = dati_storici
                st.session_state['bp_medie_storiche'] = medie_storiche
                st.session_state['bp_assumptions'] = bp_assumptions
                st.session_state['bp_anni_bp'] = anni_bp
                st.session_state['bp_anno_base'] = anno_base
                st.session_state['bp_durata'] = durata_anni
                st.success(f"✅ Analisi completata! Elaborate {len(medie_storiche)} assumption.")
            else:
                st.error("❌ Impossibile caricare i dati storici.")
        except Exception as e:
            st.error(f"Errore nel calcolo delle medie storiche: {e}")

if 'bp_medie_storiche' in st.session_state:
    st.markdown("### 📋 Assumption Calcolate")
    df_assumptions = []
    for assumption in ASSUMPTION_DEFINITIONS:
        ass_id = assumption['id']
        media_storica = st.session_state['bp_medie_storiche'].get(ass_id, assumption['default_value'])
        df_assumptions.append({
            'ID': ass_id, 'Assumption': assumption['nome'], 'Descrizione': assumption['descrizione'],
            'Unità': assumption['unita'], 'Media Storica': f"{media_storica:.2f}",
            'Formula': assumption['formula_storica'] or 'Input manuale'
        })
    st.dataframe(pd.DataFrame(df_assumptions), use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.markdown("### ⚙️ Configurazione Assumption - Layout Orizzontale")
    st.markdown("💡 **Doppio click** sulla cella per modificare.")
    
    saved_key = f'bp_saved_assumptions_{selected_cliente}'
    data_for_edit = []
    for assumption in ASSUMPTION_DEFINITIONS:
        ass_id = assumption['id']
        row = {'Assumption': assumption['nome'], 'Unità': assumption['unita']}
        for anno in anni_bp[1:]:
            default_val = st.session_state['bp_medie_storiche'].get(ass_id, assumption['default_value'])
            # Logic to use saved values if they exist
            if saved_key in st.session_state and str(ass_id) in st.session_state[saved_key] and str(anno) in st.session_state[saved_key][str(ass_id)]:
                 row[str(anno)] = st.session_state[saved_key][str(ass_id)][str(anno)]
            else:
                 row[str(anno)] = default_val
        data_for_edit.append(row)
    df_edit = pd.DataFrame(data_for_edit)
    
    # --- BLOCCO st.data_editor CORRETTO E DEFINITIVO ---

    # 1. Prepara una configurazione dinamica per le colonne
    dynamic_column_config = {
        'Assumption': st.column_config.TextColumn('Assumption', help="Nome dell'assumption (non modificabile)", width='large', disabled=True),
        'Unità': st.column_config.TextColumn('Unità', help="Unità di misura (non modificabile)", width='small', disabled=True),
    }

    # Applica una configurazione che privilegi l'inserimento di decimali
    for anno in anni_bp[1:]:
        dynamic_column_config[str(anno)] = st.column_config.NumberColumn(
            label=str(anno),
            min_value=None,
            max_value=None,
            step=0.1,  # <-- UNICA MODIFICA: step piccolo per permettere i decimali
            format="%.2f", 
            width='small'
        )

    # 2. Crea la tabella modificabile
    edited_df = st.data_editor(
        df_edit,
        use_container_width=True,
        hide_index=True,
        column_config=dynamic_column_config,
        key="assumption_editor_horizontal",
        height=min(len(df_edit) * 36 + 40, 600)
    )
    
    # 3. Salva i valori modificati in modo robusto
    assumptions_by_name = {a['nome']: a for a in ASSUMPTION_DEFINITIONS}
    assumption_inputs = {}
    for i, row in edited_df.iterrows():
        assumption_name = row['Assumption']
        assumption_def = assumptions_by_name.get(assumption_name)
        if assumption_def:
            ass_id = assumption_def['id']
            assumption_inputs[ass_id] = {}
            for anno in anni_bp[1:]:
                try:
                    value = row[str(anno)]
                    assumption_inputs[ass_id][anno] = float(value)
                except (ValueError, KeyError, TypeError):
                    assumption_inputs[ass_id][anno] = assumption_def['default_value']
    st.session_state['bp_assumption_inputs'] = assumption_inputs
    
    # --- FINE BLOCCO CORRETTO ---

    # --- SALVATAGGIO E CARICAMENTO ---
    st.markdown("---")
    col_save, col_load = st.columns(2)
    
    with col_save:
        st.markdown("#### 💾 Salva Scenario")
        scenario_name = st.text_input(
            "Nome scenario:",
            value=f"Scenario_{datetime.now().strftime('%Y%m%d_%H%M')}",
            help="Nome per identificare questo set di assumption"
        )
        if st.button("💾 Salva Assumption", type="secondary"):
            try:
                save_assumptions_to_db(selected_cliente, scenario_name, assumption_inputs, anni_bp, durata_anni)
                st.session_state[saved_key] = {str(k): {str(y): v for y, v in d.items()} for k, d in assumption_inputs.items()}
                st.success(f"✅ Scenario '{scenario_name}' salvato!")
            except Exception as e:
                st.error(f"❌ Errore salvataggio: {e}")
    
    with col_load:
        st.markdown("#### 📁 Carica Scenario")
        try:
            scenari_disponibili = get_saved_scenarios(selected_cliente)
            if scenari_disponibili:
                scenario_selected = st.selectbox("Scenari salvati:", options=scenari_disponibili)
                if st.button("📁 Carica Assumption", type="secondary"):
                    loaded_assumptions, _, _ = load_assumptions_from_db(selected_cliente, scenario_selected)
                    if loaded_assumptions:
                        st.session_state[saved_key] = {str(k): {str(y): v for y, v in d.items()} for k, d in loaded_assumptions.items()}
                        st.success(f"✅ Scenario '{scenario_selected}' caricato! Aggiorna la pagina o ricalcola le medie per visualizzare.")
                        st.rerun()
            else:
                st.info("📝 Nessuno scenario salvato.")
        except Exception as e:
            st.error(f"❌ Errore: {e}")

    # --- GENERAZIONE PROIEZIONI ---
    st.markdown("---")
    st.subheader("🚀 Generazione Proiezioni")
    if st.button("📊 Genera Business Plan", type="primary", use_container_width=True):
        with st.spinner("🔄 Generando proiezioni Business Plan..."):
            try:
                bp_assumptions = st.session_state['bp_assumptions']
                assumption_inputs = st.session_state['bp_assumption_inputs']
                dati_storici = st.session_state['bp_dati_storici']
                anno_base = st.session_state['bp_anno_base']
                durata_anni = st.session_state['bp_durata']
                
                bp_assumptions.imposta_assumptions_manuali(assumption_inputs)
                
                bp_projections = BusinessPlanProjections(selected_cliente, anno_base, durata_anni)
                bp_projections.assumptions = bp_assumptions
                bp_projections.inizializza_con_dati_storici(dati_storici)
                proiezioni_complete = bp_projections.calcola_proiezioni()
                
                st.session_state['bp_proiezioni'] = proiezioni_complete
                st.session_state['bp_projections_obj'] = bp_projections
                
                st.success(f"✅ Business Plan generato!")
            except Exception as e:
                st.error(f"❌ Errore nella generazione: {e}")
                st.exception(e)

    # --- VISUALIZZAZIONE RISULTATI ---
    if 'bp_proiezioni' in st.session_state:
        st.markdown("---")
        st.subheader("📈 Risultati Business Plan")
        bp_projections = st.session_state['bp_projections_obj']
        anni_bp = st.session_state['bp_anni_bp']

        tab_overview, tab_ce, tab_sp, tab_flussi = st.tabs([
            "🔍 Overview", "💰 Conto Economico", "🏦 Stato Patrimoniale", "💸 Flussi di Cassa"
        ])
        
        with tab_overview:
            st.markdown("### 📊 Panoramica Generale Business Plan")
            df_overview, _ = prepare_export_data_safe('Overview', bp_projections)
            display_with_html_bp(df_overview, anni_bp)
        
        with tab_ce:
            st.markdown("### 💰 Conto Economico Business Plan")
            df_ce, _ = prepare_export_data_safe('Conto Economico', bp_projections)
            display_with_html_bp(df_ce, anni_bp)
        
        with tab_sp:
            st.markdown("### 🏦 Stato Patrimoniale Business Plan")
            df_sp, _ = prepare_export_data_safe('Stato Patrimoniale', bp_projections)
            display_with_html_bp(df_sp, anni_bp)
        
        with tab_flussi:
            st.markdown("### 💸 Flussi di Cassa Business Plan")
            st.info("📊 Report Flussi di Cassa in sviluppo...")

    # --- EXPORT ---
    if 'bp_proiezioni' in st.session_state:
        st.markdown("---")
        st.subheader("💾 Export Business Plan")
        
        export_tipo = st.selectbox(
            "📊 **Scegli report da esportare:**",
            options=['Overview (KPI Principali)', 'Conto Economico Completo', 'Stato Patrimoniale Completo', 'Excel Multi-Foglio (Tutti)'],
        )
        
        bp_projections = st.session_state['bp_projections_obj']
        
        col_excel, col_pdf, col_ascii = st.columns(3)
        
        with col_excel:
            if st.button("📊 Export Excel", key="exp_xl"):
                with st.spinner("🔄 Generando file Excel..."):
                    excel_buffer = io.BytesIO()
                    filename = f"business_plan_{selected_cliente}.xlsx"
                    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                        if export_tipo.startswith('Excel'):
                            df_ov, _ = prepare_export_data_safe('Overview', bp_projections)
                            df_ce, _ = prepare_export_data_safe('Conto Economico', bp_projections)
                            df_sp, _ = prepare_export_data_safe('Stato Patrimoniale', bp_projections)
                            df_ov.to_excel(writer, sheet_name='Overview', index=False)
                            df_ce.to_excel(writer, sheet_name='Conto Economico', index=False)
                            df_sp.to_excel(writer, sheet_name='Stato Patrimoniale', index=False)
                        else:
                            df_export, _ = prepare_export_data_safe(export_tipo, bp_projections)
                            df_export.to_excel(writer, sheet_name=export_tipo.split(' (')[0], index=False)
                    st.download_button(label="📥 Scarica Excel", data=excel_buffer.getvalue(), file_name=filename, mime="application/vnd.ms-excel")
                    st.success("✅ Excel pronto!")

        with col_pdf:
            if st.button("📄 Export PDF", key="exp_pdf"):
                if not export_tipo.startswith('Excel'):
                    with st.spinner("🔄 Generando PDF..."):
                        df_export, title = prepare_export_data_safe(export_tipo, bp_projections)
                        pdf_buffer = generate_professional_pdf_safe(df_export, title, "Proiezioni Multi-Anno", selected_cliente, anni_bp)
                        if pdf_buffer:
                            filename = f"business_plan_{export_tipo.split(' (')[0].replace(' ', '_')}_{selected_cliente}.pdf"
                            st.download_button(label="📥 Scarica PDF", data=pdf_buffer, file_name=filename, mime="application/pdf")
                            st.success("✅ PDF pronto!")
                else:
                    st.info("Seleziona un report specifico per il PDF.")
# Sostituisci questa sezione nel file 8_business_plan.py

        with col_ascii:
            if st.button("📝 Export ASCII", key="exp_ascii"):
                if ASCII_AVAILABLE and not export_tipo.startswith('Excel'):
                    with st.spinner("🔄 Generando ASCII..."):
                        try:
                            df_export, title = prepare_export_data_safe(export_tipo, bp_projections)
                            
                            if not df_export.empty:
                                # Parametri per il report ASCII
                                subtitle = f"Proiezioni Multi-Anno - {selected_cliente}"
                                report_type = export_tipo.split(' (')[0]
                                filters = f"Cliente: {selected_cliente} | Anni: {anni_bp[0]}-{anni_bp[-1]} | Durata: {durata_anni} anni"
                                
                                # Genera report ASCII completo
                                ascii_content, ascii_buffer = create_downloadable_ascii_report(
                                    df=df_export,
                                    title=title,
                                    subtitle=subtitle,
                                    bold_rows=None,  # Puoi specificare righe da evidenziare se necessario
                                    report_type=report_type,
                                    filters=filters,
                                    style="grid"  # Opzioni: grid, simple, heavy, double, pipe, plain
                                )
                                
                                # Filename per download
                                safe_cliente = selected_cliente.replace(' ', '_').replace('/', '_')
                                safe_report = report_type.replace(' ', '_').lower()
                                filename = f"business_plan_{safe_report}_{safe_cliente}.txt"
                                
                                # Download button
                                st.download_button(
                                    label="📥 Scarica ASCII", 
                                    data=ascii_buffer, 
                                    file_name=filename, 
                                    mime="text/plain"
                                )
                                
                                # Preview del contenuto (opzionale)
                                with st.expander("👀 Anteprima ASCII"):
                                    st.text(ascii_content[:2000] + "..." if len(ascii_content) > 2000 else ascii_content)
                                
                                st.success("✅ Report ASCII pronto!")
                            else:
                                st.error("❌ Nessun dato da esportare")
                                
                        except Exception as e:
                            st.error(f"❌ Errore nella generazione ASCII: {e}")
                            st.exception(e)
                else:
                    if not ASCII_AVAILABLE:
                        st.error("❌ Modulo ASCII non disponibile. Verifica che ascii_table_generator.py sia presente.")
                    else:
                        st.info("💡 Seleziona un report specifico per l'export ASCII.")
        
        
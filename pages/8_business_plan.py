# pages/8_business_plan.py - VERSIONE 5.0 (STABILE) - 2025-06-26
# VERSIONE FINALE: Wizard a step atomici, stepper visivo robusto,
# codice modernizzato e logica di export completa e funzionante.

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

# --- IMPORT MODULI ---
try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    # Utilizza il modulo fornito dall'utente
    from ascii_table_generator import create_downloadable_ascii_report
    ASCII_AVAILABLE = True
except ImportError:
    ASCII_AVAILABLE = False
    st.sidebar.warning("Modulo 'ascii_table_generator.py' non trovato.")

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

import financial_model

# --- FUNZIONI DI SUPPORTO E UTILITY (INVARIATE) ---
def save_assumptions_to_db(cliente: str, scenario_name: str, assumptions: dict, anni_bp: list, durata: int) -> None:
    conn = None
    try:
        conn = sqlite3.connect("business_plan_pro.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bp_scenarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT NOT NULL, scenario_name TEXT NOT NULL,
                assumptions_json TEXT NOT NULL, anni_bp_json TEXT NOT NULL, durata INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(cliente, scenario_name) )
        """)
        assumptions_json = json.dumps(assumptions)
        anni_bp_json = json.dumps(anni_bp)
        cursor.execute("""
            INSERT OR REPLACE INTO bp_scenarios (cliente, scenario_name, assumptions_json, anni_bp_json, durata)
            VALUES (?, ?, ?, ?, ?)
        """, (cliente, scenario_name, assumptions_json, anni_bp_json, durata))
        conn.commit()
    except Exception as e:
        raise Exception(f"Errore nel salvataggio: {e}")
    finally:
        if conn: conn.close()

def get_saved_scenarios(cliente: str) -> List[str]:
    conn = None
    try:
        conn = sqlite3.connect("business_plan_pro.db")
        cursor = conn.cursor()
        cursor.execute("SELECT scenario_name FROM bp_scenarios WHERE cliente = ? ORDER BY created_at DESC", (cliente,))
        return [row[0] for row in cursor.fetchall()]
    except Exception:
        return []
    finally:
        if conn: conn.close()

def load_assumptions_from_db(cliente: str, scenario_name: str) -> Tuple[Optional[dict], Optional[list], Optional[int]]:
    conn = None
    try:
        conn = sqlite3.connect("business_plan_pro.db")
        cursor = conn.cursor()
        cursor.execute("SELECT assumptions_json, anni_bp_json, durata FROM bp_scenarios WHERE cliente = ? AND scenario_name = ?", (cliente, scenario_name))
        result = cursor.fetchone()
        if result:
            assumptions_json, anni_bp_json, durata = result
            assumptions = {int(k): {int(y): float(v) for y, v in d.items()} for k, d in json.loads(assumptions_json).items()}
            anni_bp = json.loads(anni_bp_json)
            return assumptions, anni_bp, durata
        return None, None, None
    except Exception:
        return None, None, None
    finally:
        if conn: conn.close()

def display_with_html_bp(df, years, structure_name="Business Plan"):
    if df.empty:
        st.warning("Nessun dato da visualizzare per questo report.")
        return
    df_display = df.copy()
    anni_colonne = [col for col in df.columns if col != 'Voce']
    for col in anni_colonne:
        if df_display[col].dtype in ['int64', 'float64', 'int32', 'float32', 'object']:
             df_display[col] = df_display[col].apply(lambda x: financial_model.format_number(x) if pd.api.types.is_number(x) else x)
    html_table = f"""
    <style>
        .custom-table-bp {{ width: 100%; border-collapse: collapse; font-family: Arial, sans-serif; margin: 1em 0; }}
        .custom-table-bp th, .custom-table-bp td {{ border: 1px solid #e0e0e0; padding: 8px 12px; text-align: left; }}
        .custom-table-bp th {{ background-color: #f0f0f0; font-weight: bold; position: sticky; top: 0; z-index: 1;}}
        .custom-table-bp td.numeric {{ text-align: right; }}
    </style>
    <div style="max-height: 600px; overflow-y: auto; border: 1px solid #e0e0e0;">
        <h3>{structure_name}</h3>
        <table class="custom-table-bp"><thead><tr><th>Voce</th>
    """
    for year in anni_colonne:
        html_table += f"<th class='numeric'>{year}</th>"
    html_table += "</tr></thead><tbody>"
    for _, row in df_display.iterrows():
        html_table += f"<tr><td>{row['Voce']}</td>"
        for year in anni_colonne:
            html_table += f"<td class='numeric'>{row.get(year, '')}</td>"
        html_table += "</tr>"
    html_table += "</tbody></table></div>"
    html(html_table, height=min(len(df) * 45 + 50, 650), scrolling=True)

def generate_professional_pdf_safe(df_data, title, subtitle, cliente, anni_bp):
    if not REPORTLAB_AVAILABLE: return None
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=20, bottomMargin=20, leftMargin=25, rightMargin=25)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='right_text', parent=styles['Normal'], alignment=2, fontSize=9, fontName='Helvetica'))
    story = [Paragraph(f"{cliente} | Periodo: {anni_bp[0]}-{anni_bp[-1]}", styles['Normal']), Spacer(1, 0.2 * inch)]
    table_data_pdf = [[Paragraph(f'<b>{col}</b>', styles['Normal']) for col in df_data.columns]]
    for index, row in df_data.iterrows():
        row_list = [Paragraph(str(row.iloc[0]), styles['Normal'])]
        for cell_value in row.iloc[1:]:
            formatted_val = financial_model.format_number(cell_value) if pd.api.types.is_number(cell_value) else str(cell_value)
            row_list.append(Paragraph(formatted_val, styles['right_text']))
        table_data_pdf.append(row_list)
    col_widths = [doc.width * 0.4] + [(doc.width * 0.6) / (len(df_data.columns) - 1)] * (len(df_data.columns) - 1)
    table = Table(table_data_pdf, colWidths=col_widths)
    table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey), ('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(table)
    doc.build(story)
    buffer.seek(0)
    return buffer

def prepare_export_data_safe(export_tipo, bp_projections, anni_bp):
    df_export, title = pd.DataFrame(), "Business Plan"
    try:
        reports = {
            'Overview': ('get_dataframe_proiezioni', "Business Plan - Overview KPI"),
            'Conto Economico': ('get_report_ce_proiezioni', "Business Plan - Conto Economico"),
            'Stato Patrimoniale': ('get_report_sp_proiezioni', "Business Plan - Stato Patrimoniale"),
            'Flussi di Cassa': ('get_report_full_cf_proiezioni', "Business Plan - Flussi di Cassa")
        }
        report_key = next((key for key in reports if export_tipo.startswith(key)), None)
        if report_key:
            method_name, title = reports[report_key]
            df_export = getattr(bp_projections, method_name)()
            if report_key == 'Overview':
                kpi_codes = ['RI01', 'RI10', 'RI18', 'RI23', 'RI24', 'RI25', 'RI31', 'RI32', 'RI33']
                df_export = df_export[df_export['Codice'].isin(kpi_codes)].copy()
                df_export['Voce'] = df_export['Descrizione']
                df_export = df_export.drop(['Codice', 'Descrizione'], axis=1)
    except Exception as e:
        st.error(f"Errore nella preparazione dati export: {e}")
        return pd.DataFrame(), "Business Plan"
    return df_export, title


# --- ARCHITETTURA A STEP (WIZARD) ---

def initialize_state():
    """Inizializza lo stato della sessione per il wizard."""
    if 'bp_current_step' not in st.session_state:
        st.session_state.bp_current_step = 0

def reset_and_go_to_step_0():
    """Pulisce lo stato del BP e torna allo step 0."""
    keys_to_delete = [key for key in st.session_state if key.startswith('bp_')]
    for key in keys_to_delete:
        del st.session_state[key]
    st.session_state.bp_current_step = 0

def go_to_step(step_number: int):
    """Funzione per navigare a uno step specifico. st.rerun() è automatico."""
    st.session_state.bp_current_step = step_number

def render_stepper(current_step_index: int):
    """Disegna un indicatore di progresso visivo (stepper) robusto con Flexbox."""
    steps = ["Configurazione", "Medie Storiche", "Modifica Assumption", "Risultati"]
    
    css = """
    <style>
        .stepper-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            width: 100%;
            margin-bottom: 2rem;
        }
        .step {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            flex-grow: 0;
        }
        .step-circle {
            width: 30px;
            height: 30px;
            line-height: 30px;
            border-radius: 50%;
            background-color: #f0f2f6;
            border: 2px solid #ddd;
            font-weight: bold;
            color: #888;
            margin-bottom: 5px;
        }
        .step-label {
            font-size: 12px;
            color: #888;
        }
        .step.active .step-circle {
            background-color: #0068c9;
            border-color: #0068c9;
            color: white;
        }
        .step.active .step-label {
            color: #0068c9;
            font-weight: bold;
        }
        .step-connector {
            flex-grow: 1;
            height: 2px;
            background-color: #ddd;
            margin: 0 10px;
            transform: translateY(-15px); /* Allinea il connettore con i cerchi */
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

    html_content = '<div class="stepper-container">'
    for i, step_name in enumerate(steps):
        active_class = "active" if i == current_step_index else ""
        html_content += f"""
        <div class="step {active_class}">
            <div class="step-circle">{i+1}</div>
            <div class="step-label">{step_name}</div>
        </div>
        """
        if i < len(steps) - 1:
            html_content += '<div class="step-connector"></div>'
    html_content += '</div>'
    
    st.markdown(html_content, unsafe_allow_html=True)
    st.markdown("<hr style='margin-top:0;'>", unsafe_allow_html=True)

def render_step_0_config():
    """STEP 0: Configurazione iniziale del Business Plan."""
    render_stepper(0)
    st.subheader("Step 1: Configurazione Business Plan")

    selected_cliente = st.session_state.get('selected_cliente', 'Tutti')
    if selected_cliente == 'Tutti':
        st.warning("⚠️ Seleziona un cliente specifico nella sidebar per procedere."); st.stop()
    st.success(f"✅ **Cliente selezionato**: {selected_cliente}")

    try:
        anni_disponibili = get_anni_disponibili(selected_cliente)
        anno_base = determina_anno_base(selected_cliente)
        if not anni_disponibili or not anno_base:
            st.error(f"❌ Nessun dato storico trovato per il cliente {selected_cliente}"); st.stop()
        st.info(f"📅 Anno base (N0): {anno_base} | Storico disponibile: {', '.join(map(str, anni_disponibili))}")
        st.session_state.bp_anno_base = anno_base
        st.session_state.bp_anni_disponibili = anni_disponibili
    except Exception as e:
        st.error(f"Errore caricamento dati cliente: {e}"); st.stop()

    durata_anni = st.number_input("Anni di proiezione:", min_value=3, max_value=25, value=10)
    st.session_state.bp_durata = durata_anni
    anni_bp = genera_anni_business_plan(anno_base, durata_anni)
    st.session_state.bp_anni_bp = anni_bp
    st.info(f"🎯 **Periodo Business Plan**: {anni_bp[0]} → {anni_bp[-1]} ({len(anni_bp)} anni)")
    st.markdown("---")
    
    if st.button("Calcola Medie Storiche e Procedi ➡️", type="primary", use_container_width=True):
        with st.spinner("Analizzando dati storici..."):
            try:
                bp_assumptions = BusinessPlanAssumptions(selected_cliente)
                dati_storici = bp_assumptions.carica_dati_storici(st.session_state.bp_anni_disponibili)
                medie_storiche = bp_assumptions.calcola_medie_storiche(st.session_state.bp_anni_disponibili)
                st.session_state.update({
                    'bp_dati_storici': dati_storici, 'bp_medie_storiche': medie_storiche,
                    'bp_assumptions_obj': bp_assumptions
                })
                go_to_step(1)
            except Exception as e:
                st.error(f"Errore calcolo medie: {e}")

def render_step_1_visualizza_medie():
    """STEP 1: Visualizzazione delle medie storiche calcolate."""
    render_stepper(1)
    st.subheader("Step 2: Verifica Medie Storiche Calcolate")
    
    df_assumptions = pd.DataFrame([{
        'ID': ass['id'], 'Assumption': ass['nome'], 'Descrizione': ass['descrizione'],
        'Unità': ass['unita'], 'Media Storica': f"{st.session_state.bp_medie_storiche.get(ass['id'], ass['default_value']):.2f}",
        'Formula': ass['formula_storica'] or 'Input manuale'
    } for ass in ASSUMPTION_DEFINITIONS])
    st.dataframe(df_assumptions, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    with col1:
        st.button("⬅️ Torna alla Configurazione", on_click=go_to_step, args=[0], use_container_width=True)
    with col2:
        st.button("Procedi alla Modifica delle Assumption ➡️", type="primary", on_click=go_to_step, args=[2], use_container_width=True)

def render_step_2_modifica_assumption():
    """STEP 2: Modifica delle assumption e gestione scenari."""
    render_stepper(2)
    st.subheader("Step 3: Modifica Assumption e Gestisci Scenari")
    
    st.markdown("💡 **Doppio click** sulla cella per modificare i valori di proiezione anno per anno.")
    
    selected_cliente, anni_bp = st.session_state.selected_cliente, st.session_state.bp_anni_bp
    saved_key = f'bp_saved_assumptions_{selected_cliente}'
    
    data_for_edit = []
    for assumption in ASSUMPTION_DEFINITIONS:
        ass_id = assumption['id']
        row = {'Assumption': assumption['nome'], 'Unità': assumption['unita']}
        default_val = st.session_state.bp_medie_storiche.get(ass_id, assumption['default_value'])
        for anno in anni_bp[1:]:
            row[str(anno)] = st.session_state.get(saved_key, {}).get(str(ass_id), {}).get(str(anno), default_val)
        data_for_edit.append(row)
    
    df_edit = pd.DataFrame(data_for_edit)
    edited_df = st.data_editor(df_edit, use_container_width=True, hide_index=True, height=min(len(df_edit) * 36 + 40, 600),
        column_config={'Assumption': st.column_config.TextColumn(disabled=True), 'Unità': st.column_config.TextColumn(disabled=True),
                       **{str(anno): st.column_config.NumberColumn(label=str(anno), step=0.01, format="%.2f") for anno in anni_bp[1:]}})
    
    assumptions_by_name = {a['nome'].strip().lower(): a for a in ASSUMPTION_DEFINITIONS}
    assumption_inputs = {
        assumptions_by_name[row['Assumption'].strip().lower()]['id']: {
            anno: float(row[str(anno)]) for anno in anni_bp[1:]
        } for _, row in edited_df.iterrows() if row['Assumption'].strip().lower() in assumptions_by_name
    }
    st.session_state.bp_assumption_inputs = assumption_inputs
    
    st.markdown("---",)
    with st.expander("💾 Gestione Scenari (Salva/Carica Assumption)"):
        col_save, col_load = st.columns(2)
        with col_save:
            scenario_name = st.text_input("Nome scenario da salvare:", value=f"Scenario_{datetime.now().strftime('%Y%m%d_%H%M')}")
            if st.button("💾 Salva", type="secondary"):
                save_assumptions_to_db(selected_cliente, scenario_name, assumption_inputs, anni_bp, st.session_state.bp_durata)
                st.session_state[saved_key] = {str(k): {str(y): v for y, v in d.items()} for k, d in assumption_inputs.items()}
                st.success(f"Scenario '{scenario_name}' salvato!")
        with col_load:
            scenari_disponibili = get_saved_scenarios(selected_cliente)
            if scenari_disponibili:
                scenario_selected = st.selectbox("Scenari salvati:", options=scenari_disponibili)
                if st.button("📁 Carica", type="secondary"):
                    loaded_assumptions, _, _ = load_assumptions_from_db(selected_cliente, scenario_selected)
                    st.session_state[saved_key] = {str(k): {str(y): v for y, v in d.items()} for k, d in loaded_assumptions.items()}
                    st.success(f"Scenario '{scenario_selected}' caricato!")
                    st.rerun()
            else: st.info("Nessuno scenario salvato.")

    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    with col1:
        st.button("⬅️ Torna alle Medie Storiche", on_click=go_to_step, args=[1], use_container_width=True)
    with col2:
        if st.button("Genera Business Plan ➡️", type="primary", use_container_width=True):
            with st.spinner("🔄 Generando proiezioni..."):
                try:
                    bp_assumptions = st.session_state.bp_assumptions_obj
                    bp_assumptions.imposta_assumptions_manuali(st.session_state.bp_assumption_inputs)
                    bp_projections = BusinessPlanProjections(selected_cliente, st.session_state.bp_anno_base, st.session_state.bp_durata, assumptions=bp_assumptions)
                    bp_projections.inizializza_con_dati_storici(st.session_state.bp_dati_storici)
                    st.session_state.bp_projections_obj = bp_projections
                    bp_projections.calcola_proiezioni()
                    go_to_step(3)
                except Exception as e:
                    st.error(f"Errore generazione proiezioni: {e}"); st.exception(e)

def render_step_3_risultati():
    """STEP 3: Visualizzazione dei risultati finali e opzioni di export."""
    render_stepper(3)
    st.subheader("Step 4: Risultati del Business Plan")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.button("⬅️ Modifica Assumption", on_click=go_to_step, args=[2], use_container_width=True)
    with col2:
        st.button("🔄 Inizia Nuova Analisi", on_click=reset_and_go_to_step_0, use_container_width=True)
    st.markdown("---")

    bp_projections = st.session_state.bp_projections_obj
    anni_bp = st.session_state.bp_anni_bp
    selected_cliente = st.session_state.selected_cliente
    
    tab_overview, tab_ce, tab_sp, tab_flussi = st.tabs(["🔍 Overview", "💰 C. Economico", "🏦 S. Patrimoniale", "💸 Flussi di Cassa"])
    with tab_overview:
        df_o, _ = prepare_export_data_safe('Overview', bp_projections, anni_bp)
        display_with_html_bp(df_o, anni_bp, "Panoramica Generale")
    with tab_ce:
        df_ce, _ = prepare_export_data_safe('Conto Economico', bp_projections, anni_bp)
        display_with_html_bp(df_ce, anni_bp, "Conto Economico Proiettato")
    with tab_sp:
        df_sp, _ = prepare_export_data_safe('Stato Patrimoniale', bp_projections, anni_bp)
        display_with_html_bp(df_sp, anni_bp, "Stato Patrimoniale Proiettato")
    with tab_flussi:
        df_cf, _ = prepare_export_data_safe('Flussi di Cassa', bp_projections, anni_bp)
        display_with_html_bp(df_cf, anni_bp, "Flussi di Cassa Proiettati")

    st.markdown("---")
    st.subheader("💾 Export Report")
    export_tipo = st.selectbox("Scegli report da esportare:",
        ['Overview (KPI Principali)', 'Conto Economico Completo', 'Stato Patrimoniale Completo', 'Flussi di Cassa Completo', 'Excel Multi-Foglio (Tutti)'])
    
    col_excel, col_pdf, col_ascii = st.columns(3)
    
    with col_excel:
        if st.button("📊 Export Excel", key="exp_xl_bp"):
            with st.spinner("🔄 Generando file Excel..."):
                excel_buffer = io.BytesIO()
                filename = f"business_plan_{selected_cliente}.xlsx"
                with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                    if export_tipo.startswith('Excel'):
                        df_ov, _ = prepare_export_data_safe('Overview', bp_projections, anni_bp)
                        df_ce, _ = prepare_export_data_safe('Conto Economico', bp_projections, anni_bp)
                        df_sp, _ = prepare_export_data_safe('Stato Patrimoniale', bp_projections, anni_bp)
                        df_cf, _ = prepare_export_data_safe('Flussi di Cassa', bp_projections, anni_bp)
                        if not df_ov.empty: df_ov.to_excel(writer, sheet_name='Overview', index=False)
                        if not df_ce.empty: df_ce.to_excel(writer, sheet_name='Conto Economico', index=False)
                        if not df_sp.empty: df_sp.to_excel(writer, sheet_name='Stato Patrimoniale', index=False)
                        if not df_cf.empty: df_cf.to_excel(writer, sheet_name='Flussi di Cassa', index=False)
                    else:
                        df_export, _ = prepare_export_data_safe(export_tipo, bp_projections, anni_bp)
                        if not df_export.empty: df_export.to_excel(writer, sheet_name=export_tipo.split(' (')[0], index=False)
                st.download_button(label="📥 Scarica Excel", data=excel_buffer.getvalue(), file_name=filename, mime="application/vnd.ms-excel")

    with col_pdf:
        if st.button("📄 Export PDF", key="exp_pdf_bp"):
            if not export_tipo.startswith('Excel'):
                with st.spinner("🔄 Generando PDF..."):
                    df_export, title = prepare_export_data_safe(export_tipo, bp_projections, anni_bp)
                    if not df_export.empty:
                        pdf_buffer = generate_professional_pdf_safe(df_export, title, "Proiezioni Multi-Anno", selected_cliente, anni_bp)
                        if pdf_buffer:
                            filename = f"business_plan_{export_tipo.split(' (')[0].replace(' ', '_')}_{selected_cliente}.pdf"
                            st.download_button(label="📥 Scarica PDF", data=pdf_buffer, file_name=filename, mime="application/pdf")
                    else:
                        st.warning("Nessun dato da esportare per questo report.")
            else:
                st.info("Seleziona un report specifico (non multi-foglio) per l'export PDF.")

    with col_ascii:
        if st.button("📝 Export ASCII", key="exp_ascii_bp"):
            if ASCII_AVAILABLE and not export_tipo.startswith('Excel'):
                with st.spinner("🔄 Generando ASCII..."):
                    df_export, title = prepare_export_data_safe(export_tipo, bp_projections, anni_bp)
                    if not df_export.empty:
                        subtitle = f"Proiezioni Multi-Anno - {selected_cliente}"
                        filters = f"Cliente: {selected_cliente} | Anni: {anni_bp[0]}-{anni_bp[-1]}"
                        
                        content, ascii_buffer = create_downloadable_ascii_report(
                            df=df_export, 
                            title=title, 
                            subtitle=subtitle, 
                            filters=filters,
                            report_type="Business Plan"
                        )
                        
                        filename = f"business_plan_{export_tipo.split(' (')[0].replace(' ', '_')}_{selected_cliente}.txt"
                        st.download_button(label="📥 Scarica ASCII", 
                                           data=ascii_buffer, 
                                           file_name=filename, 
                                           mime="text/plain")
                    else:
                        st.warning("Nessun dato da esportare per questo report.")
            else:
                st.info("Modulo ASCII non disponibile o export non valido.")


# --- CONTROLLO PRINCIPALE DELL'APPLICAZIONE ---
def main():
    """Funzione principale che orchestra la visualizzazione degli step."""
    sidebar_filtri.display_sidebar_filters()

    st.title("🚀 Business Plan - Proiezioni Multi-Anno")
    st.markdown("Crea proiezioni finanziarie dettagliate attraverso un processo guidato.")
    
    initialize_state()
    
    step_functions = {
        0: render_step_0_config,
        1: render_step_1_visualizza_medie,
        2: render_step_2_modifica_assumption,
        3: render_step_3_risultati
    }
    current_step = st.session_state.get('bp_current_step', 0)
    
    # Router per visualizzare lo step corretto, con fallback di sicurezza
    if current_step == 0:
        step_functions[current_step]()
    elif current_step > 0 and 'bp_assumptions_obj' in st.session_state:
        if current_step < 3 or 'bp_projections_obj' in st.session_state:
             step_functions[current_step]()
        else:
             st.warning("Dati delle proiezioni non trovati. Torno alla modifica delle assumption.")
             go_to_step(2)
    elif current_step > 0 and 'bp_assumptions_obj' not in st.session_state:
        # Se l'utente ricarica la pagina e perde lo stato, lo riportiamo all'inizio.
        reset_and_go_to_step_0()
    else:
        # Fallback generico
        step_functions[0]()


if __name__ == "__main__":
    main()

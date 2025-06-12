# indicatori.py - Progetto Business Plan Pro - versione corretta - 2025-06-12
import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import sidebar_filtri
from financial_model import calculate_all_reports, report_structure_ce, report_structure_sp, report_structure_ff

# Nome del database
DATABASE_NAME = "business_plan_pro.db"

# Inizializzazione dei filtri nella sidebar
sidebar_filtri.display_sidebar_filters()

# Accesso ai valori dei filtri da session_state
selected_cliente = st.session_state.selected_cliente
selected_anni = st.session_state.selected_anni 

st.title("📈 Indicatori e KPI")
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
    st.info("Nessun anno disponibile o selezionato per il report.")
    st.stop()

# --- Caricamento dati dal database ---
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

# --- Calcolo dei report ---
all_calculated_reports = calculate_all_reports(
    df_full_data, 
    years_to_display,
    report_structure_ce,
    report_structure_sp,
    report_structure_ff
)

# Estrazione dei DataFrame necessari
ce_df = all_calculated_reports['ce']
sp_df = all_calculated_reports['sp']
ff_df = all_calculated_reports['ff']

if ce_df.empty or sp_df.empty:
    st.warning("Nessun dato disponibile per il cliente/anno selezionato.")
    st.stop()

# --- Funzione per il calcolo dei KPI ---
def calcola_kpi(ce_df, sp_df, years):
    kpi_data = []
    
    for year in years:
        # Estrazione valori dal Conto Economico
        try:
            ricavi = ce_df.loc[ce_df['Voce'] == 'Ricavi dalle vendite e prestazioni', str(year)].values[0]
            ricavi = int(ricavi.replace('.', '')) if isinstance(ricavi, str) else ricavi
        except:
            ricavi = 0
            
        try:
            ebit = ce_df.loc[ce_df['Voce'] == 'RISULTATO OPERATIVO (EBIT)', str(year)].values[0]
            ebit = int(ebit.replace('.', '')) if isinstance(ebit, str) else ebit
        except:
            ebit = 0
            
        try:
            utile = ce_df.loc[ce_df['Voce'] == 'RISULTATO NETTO', str(year)].values[0]
            utile = int(utile.replace('.', '')) if isinstance(utile, str) else utile
        except:
            utile = 0
        
        # Estrazione valori dallo Stato Patrimoniale
        try:
            attivo_tot = sp_df.loc[sp_df['Voce'] == 'TOTALE IMMOBILIZZAZIONI', str(year)].values[0]
            attivo_tot = int(attivo_tot.replace('.', '')) if isinstance(attivo_tot, str) else attivo_tot
        except:
            attivo_tot = 0
            
        try:
            patrimonio = sp_df.loc[sp_df['Voce'] == 'Patrimonio netto', str(year)].values[0]
            patrimonio = int(patrimonio.replace('.', '')) if isinstance(patrimonio, str) else patrimonio
        except:
            patrimonio = 0
        
        # Calcolo indicatori
        roe = (utile / patrimonio * 100) if patrimonio != 0 else 0
        roa = (utile / attivo_tot * 100) if attivo_tot != 0 else 0
        ebit_margin = (ebit / ricavi * 100) if ricavi != 0 else 0
        
        kpi_data.append({
            "Anno": year,
            "ROE %": round(roe, 2),
            "ROA %": round(roa, 2),
            "EBIT Margin %": round(ebit_margin, 2),
            "Utile Netto": utile,
            "EBIT": ebit,
            "Ricavi": ricavi
        })
    
    return pd.DataFrame(kpi_data)

# Calcolo e visualizzazione KPI
kpi_df = calcola_kpi(ce_df, sp_df, years_to_display)

st.subheader("📌 Indicatori sintetici")
st.dataframe(kpi_df.style.format({
    "ROE %": "{:.2f}%",
    "ROA %": "{:.2f}%", 
    "EBIT Margin %": "{:.2f}%",
    "Utile Netto": "{:,.0f}",
    "EBIT": "{:,.0f}",
    "Ricavi": "{:,.0f}"
}), use_container_width=True)

# Grafici
st.subheader("📊 Grafici di performance")

# Seleziona KPI da visualizzare
kpi_selezionati = st.multiselect(
    "Seleziona indicatori da visualizzare",
    options=["ROE %", "ROA %", "EBIT Margin %"],
    default=["ROE %", "EBIT Margin %"]
)

if kpi_selezionati:
    fig = px.line(kpi_df, x="Anno", y=kpi_selezionati, 
                 title="Andamento indicatori chiave",
                 markers=True)
    st.plotly_chart(fig, use_container_width=True)

# Grafico a barre per valori assoluti
valori_selezionati = st.multiselect(
    "Seleziona valori assoluti da visualizzare",
    options=["Utile Netto", "EBIT", "Ricavi"],
    default=["Utile Netto", "Ricavi"]
)

if valori_selezionati:
    fig_bar = px.bar(kpi_df, x="Anno", y=valori_selezionati,
                    title="Valori assoluti",
                    barmode='group')
    st.plotly_chart(fig_bar, use_container_width=True)
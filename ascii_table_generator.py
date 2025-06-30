# ascii_table_generator.py (VERSIONE FINALE E AUTOCONSISTENTE)

import pandas as pd
import io
from datetime import datetime
from tabulate import tabulate

def format_monetary_value(value):
    """
    Formatta un valore monetario in modo sicuro.
    I numeri negativi vengono messi tra parentesi ().
    Questa è una funzione a sé stante (non un metodo di una classe).
    """
    if pd.isna(value) or value == "":
        return ""
    
    try:
        numeric_value = float(value)
    except (ValueError, TypeError):
        return str(value).strip()

    # Arrotonda a 0 per evitare valori come "0" per numeri piccoli
    if -0.5 < numeric_value < 0.5:
        return ""
    
    is_negative = numeric_value < 0
    abs_value = abs(numeric_value)

    try:
        formatted_abs_string = f"{int(round(abs_value, 0)):,}".replace(',', '.')
    except (OverflowError, ValueError):
        formatted_abs_string = f"{abs_value:,.0f}".replace(',', '.')

    if is_negative:
        return f"({formatted_abs_string})"
    else:
        return formatted_abs_string

def create_downloadable_ascii_report(df, title, subtitle="", filters="", **kwargs):
    """
    Funzione principale per creare report ASCII completo pronto per download
    utilizzando la libreria robusta `tabulate`.
    """
    if df.empty:
        table_content = "Nessun dato disponibile."
    else:
        df_copy = df.copy()
        
        # Determina gli allineamenti: sinistra per la prima colonna, destra per le altre
        colalign = ["left"] + ["right"] * (len(df.columns) - 1)
        
        # Formatta i dati numerici, lasciando la prima colonna così com'è
        # Chiama la funzione 'format_monetary_value' definita in questo stesso file
        for col in df_copy.columns[1:]:
            df_copy[col] = df_copy[col].apply(format_monetary_value)
            
        # Genera la tabella usando lo stile 'psql' per un look professionale e pulito
        table_content = tabulate(
            df_copy,
            headers='keys',
            tablefmt='psql',
            showindex=False,
            colalign=colalign
        )
    
    timestamp = datetime.now().strftime('%d/%m/%Y alle %H:%M')
    
    full_report = f"""{title}
{'=' * len(title)}
{subtitle}

{table_content}

{'-' * 70}
📊 Report generato il {timestamp}
📋 Filtri: {filters}
{'-' * 70}
"""
    
    buffer = io.BytesIO(full_report.encode('utf-8'))
    buffer.seek(0)
    return full_report, buffer
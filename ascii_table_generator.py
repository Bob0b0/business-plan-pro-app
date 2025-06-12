# ascii_table_generator.py
# PRIMO FILE DA CREARE - Metti questo nella stessa cartella del tuo main.py

import pandas as pd
import io
from datetime import datetime

try:
    from tabulate import tabulate
    TABULATE_AVAILABLE = True
except ImportError:
    TABULATE_AVAILABLE = False

class ASCIITableGenerator:
    """Generatore di tabelle ASCII professionali"""
    
    def __init__(self, style="grid"):
        self.style = style
        self.tabulate_styles = {
            'grid': 'grid',
            'simple': 'simple', 
            'heavy': 'fancy_grid',
            'double': 'fancy_grid',
            'pipe': 'pipe',
            'plain': 'plain'
        }
    
    def format_monetary_value(self, value):
        """Formatta un valore monetario per visualizzazione ASCII"""
        if pd.isna(value) or value == "" or value == 0:
            return ""
        
        # Se è già una stringa, puliscila completamente da asterischi e formattazione
        if isinstance(value, str):
            # Rimuovi TUTTI gli asterischi e formattazione esistente
            clean_value = value.replace('**', '').replace('*', '').replace('.', '').replace(',', '.').replace('€', '').replace(' ', '').strip()
            try:
                numeric_value = float(clean_value)
            except:
                # Se non è convertibile, restituisci stringa pulita da asterischi
                return str(value).replace('**', '').replace('*', '').strip()
        else:
            try:
                numeric_value = float(value)
            except:
                return str(value).replace('**', '').replace('*', '').strip()
        
        # Formatta con separatori di migliaia
        if numeric_value == 0:
            return ""
        elif numeric_value > 0:
            return f"{int(numeric_value):,}".replace(',', '.')
        else:
            return f"{int(numeric_value):,}".replace(',', '.')
    
    def detect_numeric_columns(self, df):
        """Identifica automaticamente colonne numeriche per formattazione"""
        numeric_cols = []
        
        for col in df.columns:
            # Skip colonna descrittiva
            if col.lower() in ['voce', 'descrizione', 'nome', 'conto']:
                continue
                
            # Controlla tipo dati
            if df[col].dtype in ['int64', 'float64']:
                numeric_cols.append(col)
                continue
            
            # Controlla contenuto per valori monetari/numerici
            if not df.empty:
                numeric_count = 0
                total_count = len(df[col].dropna())
                
                if total_count > 0:
                    for val in df[col].dropna():
                        # Pulisci il valore per testare se è numerico
                        val_clean = str(val).replace('.', '').replace(',', '.').replace('€', '').replace(' ', '').replace('-', '').strip()
                        try:
                            float(val_clean)
                            numeric_count += 1
                        except:
                            continue
                    
                    # Se 60%+ sono numeri, tratta come colonna numerica
                    if numeric_count / total_count > 0.6:
                        numeric_cols.append(col)
        
        return numeric_cols
    
    def prepare_dataframe_for_ascii(self, df, bold_rows=None):
        """Prepara DataFrame per output ASCII con formattazione ottimale"""
        if df.empty:
            return df
            
        df_prepared = df.copy()
        bold_rows = bold_rows or []
        
        # PULIZIA ATTIVA: Rimuovi tutti gli asterischi dai dati esistenti
        for col in df_prepared.columns:
            if df_prepared[col].dtype == 'object':  # Colonne testuali
                df_prepared[col] = df_prepared[col].astype(str).str.replace(r'\*\*\s*', '', regex=True).str.replace(r'\s*\*\*', '', regex=True).str.strip()
        
        # Identifica colonne numeriche
        numeric_cols = self.detect_numeric_columns(df_prepared)
        
        # Formatta valori numerici/monetari
        for col in numeric_cols:
            df_prepared[col] = df_prepared[col].apply(self.format_monetary_value)
        
        return df_prepared
    
    def calculate_optimal_widths(self, df):
        """Calcola larghezze ottimali per ogni colonna"""
        widths = {}
        
        for col in df.columns:
            # Larghezza header
            header_width = len(str(col))
            
            # Larghezza contenuto massimo
            if not df.empty:
                content_widths = []
                for val in df[col]:
                    if pd.notna(val):
                        content_widths.append(len(str(val)))
                max_content_width = max(content_widths) if content_widths else 0
            else:
                max_content_width = 0
            
            # Calcola larghezza finale
            if col.lower() in ['voce', 'descrizione', 'nome', 'conto']:
                # Colonne descrittive: più spazio
                min_width = 25
                max_width = 50
            else:
                # Colonne numeriche: spazio moderato
                min_width = 12
                max_width = 20
            
            width = max(header_width, max_content_width, min_width)
            width = min(width, max_width)
            
            widths[col] = width
        
        return widths
    
    def generate_table_with_tabulate(self, df, bold_rows=None):
        """Genera tabella usando la libreria tabulate"""
        if df.empty:
            return "Nessun dato disponibile."
        
        # Prepara dati con formattazione
        df_prepared = self.prepare_dataframe_for_ascii(df, bold_rows)
        
        # Identifica colonne numeriche per allineamento
        numeric_cols = self.detect_numeric_columns(df)
        
        # Crea lista di allineamenti
        colalign = []
        for col in df_prepared.columns:
            if col in numeric_cols:
                colalign.append("right")
            else:
                colalign.append("left")
        
        # Stile tabulate
        tablefmt = self.tabulate_styles.get(self.style, 'grid')
        
        # Genera tabella con parametri ottimizzati
        table = tabulate(
            df_prepared.values,
            headers=df_prepared.columns,
            tablefmt=tablefmt,
            colalign=colalign,
            numalign="right",
            stralign="left",
            floatfmt=".0f"
        )
        
        return table
    
    def generate_table_fallback(self, df, bold_rows=None):
        """Generatore fallback migliorato con allineamento perfetto"""
        if df.empty:
            return "Nessun dato disponibile."
        
        # Prepara dati
        df_prepared = self.prepare_dataframe_for_ascii(df, bold_rows)
        numeric_cols = self.detect_numeric_columns(df)
        
        # Calcola larghezze ottimali
        widths = self.calculate_optimal_widths(df_prepared)
        
        lines = []
        
        # Separatore superiore
        separator_parts = ["+"]
        for col in df_prepared.columns:
            separator_parts.append("-" * (widths[col] + 2))  # +2 per padding
            separator_parts.append("+")
        separator = "".join(separator_parts)
        
        lines.append(separator)
        
        # Header
        header_parts = ["|"]
        for col in df_prepared.columns:
            header_content = f" {str(col).center(widths[col])} "
            header_parts.append(header_content)
            header_parts.append("|")
        lines.append("".join(header_parts))
        
        # Separatore header-dati  
        lines.append(separator)
        
        # Righe dati
        for _, row in df_prepared.iterrows():
            row_parts = ["|"]
            
            for col in df_prepared.columns:
                value = str(row[col]) if pd.notna(row[col]) else ""
                
                # Determina allineamento
                if col in numeric_cols:
                    # Numeri: allineamento a destra
                    cell_content = f" {value.rjust(widths[col])} "
                else:
                    # Testo: allineamento a sinistra
                    # Tronca se necessario
                    if len(value) > widths[col]:
                        value = value[:widths[col]-3] + "..."
                    cell_content = f" {value.ljust(widths[col])} "
                
                row_parts.append(cell_content)
                row_parts.append("|")
            
            lines.append("".join(row_parts))
        
        # Separatore inferiore
        lines.append(separator)
        
        return "\n".join(lines)
    
    def generate_table(self, df, title="", subtitle="", bold_rows=None):
        """Genera tabella ASCII"""
        if df.empty:
            return f"\n{title}\n{'='*len(title)}\nNessun dato disponibile.\n"
        
        # Genera tabella
        if TABULATE_AVAILABLE:
            table = self.generate_table_with_tabulate(df, bold_rows)
        else:
            table = self.generate_table_fallback(df, bold_rows)
        
        # Aggiungi titolo e sottotitolo
        result = []
        if title:
            result.append(f"\n{title}")
            result.append("=" * len(title))
            if subtitle:
                result.append(subtitle)
            result.append("")
        
        result.append(table)
        return "\n".join(result)
    
    def create_report_with_footer(self, df, title, subtitle="", bold_rows=None, 
                                 report_type="Report", filters=""):
        """Crea report completo con header e footer informativi"""
        # Genera tabella principale
        table = self.generate_table(df, title, subtitle, bold_rows)
        
        # Footer informativo
        timestamp = datetime.now().strftime('%d/%m/%Y alle %H:%M')
        engine = "tabulate" if TABULATE_AVAILABLE else "custom"
        
        footer = f"""
{'-' * 70}
📊 Business Plan Pro - {report_type}
🕒 Generato il {timestamp}
📋 Filtri: {filters}
🔧 Engine: {engine} (stile: {self.style})
{'-' * 70}

💡 Note:
   • Tabella con formattazione professionale e allineamento ottimale
   • Totali e subtotali organizzati per sezioni logiche
   • Importi formattati con separatori di migliaia (es: 579.620)
   • Valori in Euro (€) salvo diversa indicazione
   • Perfetta per email, console, stampa

⚠️  Per migliore visualizzazione usare font monospace:
    Courier New, Consolas, Monaco, Liberation Mono
"""
        
        return table + footer
    
    def export_to_buffer(self, content, filename="report.txt"):
        """Esporta contenuto in buffer per download Streamlit"""
        buffer = io.BytesIO()
        buffer.write(content.encode('utf-8'))
        buffer.seek(0)
        return buffer

def create_downloadable_ascii_report(df, title, subtitle="", bold_rows=None, 
                                   report_type="Report", filters="", style="grid"):
    """
    Funzione principale per creare report ASCII completo pronto per download
    
    Args:
        df (pd.DataFrame): Dati
        title (str): Titolo
        subtitle (str): Sottotitolo  
        bold_rows (list): Righe da evidenziare
        report_type (str): Tipo report
        filters (str): Filtri applicati
        style (str): Stile tabella
        
    Returns:
        tuple: (contenuto_str, buffer_download)
    """
    generator = ASCIITableGenerator(style)
    content = generator.create_report_with_footer(
        df, title, subtitle, bold_rows, report_type, filters
    )
    buffer = generator.export_to_buffer(content)
    return content, buffer
# auth.py - Sistema di autenticazione con database separati per utente
import streamlit as st
import hashlib
import sqlite3
import os
import shutil
from datetime import datetime

class AuthManager:
    def __init__(self, users_db="users.db"):
        self.users_db = users_db
        self.init_users_database()
    
    def init_users_database(self):
        """Inizializza il database degli utenti"""
        conn = sqlite3.connect(self.users_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        """Hash della password con salt"""
        salt = "business_plan_pro_2025_secret!"
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def get_user_db_name(self, username):
        """Restituisce il nome del database per un utente"""
        return f"business_plan_{username}.db"
    
    def create_user_database(self, username):
        """Crea database personale per un nuovo utente"""
        user_db = self.get_user_db_name(username)
        
        if os.path.exists(user_db):
            return user_db
        
        # Copia il database principale come template
        if os.path.exists("business_plan_pro.db"):
            shutil.copy2("business_plan_pro.db", user_db)
            
            # Svuota le tabelle dati ma mantieni struttura e configurazioni
            conn = sqlite3.connect(user_db)
            cursor = conn.cursor()
            
            # Svuota solo le tabelle con dati utente
            try:
                cursor.execute("DELETE FROM righe")
                cursor.execute("DELETE FROM bp_scenarios") 
                # Le tabelle conti, ricla rimangono invariate (configurazione)
            except sqlite3.OperationalError:
                pass  # Tabelle potrebbero non esistere
            
            conn.commit()
            conn.close()
            
            print(f"Database creato per utente: {username}")
        else:
            print("ERRORE: Database template business_plan_pro.db non trovato!")
        
        return user_db
    
    def register_user(self, username, email, password):
        """Registra un nuovo utente e crea il suo database"""
        try:
            conn = sqlite3.connect(self.users_db)
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, password_hash)
            )
            
            conn.commit()
            conn.close()
            
            # Crea database personale
            self.create_user_database(username)
            
            return True, "Registrazione completata! Database personale creato."
        
        except sqlite3.IntegrityError:
            return False, "Username o email già esistenti"
        except Exception as e:
            return False, f"Errore durante la registrazione: {str(e)}"
    
    def authenticate_user(self, username, password):
        """Autentica un utente"""
        conn = sqlite3.connect(self.users_db)
        cursor = conn.cursor()
        
        password_hash = self.hash_password(password)
        cursor.execute(
            "SELECT id, username, email FROM users WHERE username = ? AND password_hash = ?",
            (username, password_hash)
        )
        
        user = cursor.fetchone()
        
        if user:
            # Aggiorna ultimo accesso
            cursor.execute(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.now(), user[0])
            )
            conn.commit()
            
            # Verifica che il database utente esista
            user_db = self.get_user_db_name(username)
            if not os.path.exists(user_db):
                self.create_user_database(username)
        
        conn.close()
        return user

def login_form():
    """Form di login"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h1>🏢 Business Plan Pro</h1>
        <h3>Accesso Riservato</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("🔐 Login")
        
        username = st.text_input("Username", placeholder="Inserisci username")
        password = st.text_input("Password", type="password", placeholder="Inserisci password")
        
        col_login, col_register = st.columns(2)
        
        with col_login:
            if st.button("🚀 Accedi", use_container_width=True, type="primary"):
                if username and password:
                    auth = AuthManager()
                    user = auth.authenticate_user(username, password)
                    
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user_id = user[0]
                        st.session_state.username = user[1]
                        st.session_state.email = user[2]
                        st.success("Login effettuato!")
                        st.rerun()
                    else:
                        st.error("Credenziali non valide")
                else:
                    st.error("Compila tutti i campi")
        
        with col_register:
            if st.button("📝 Registrati", use_container_width=True):
                st.session_state.show_register = True
                st.rerun()

def register_form():
    """Form di registrazione"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h1>🏢 Business Plan Pro</h1>
        <h3>Registrazione Nuovo Utente</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("📝 Crea Account")
        
        username = st.text_input("Username", placeholder="Scegli username")
        email = st.text_input("Email", placeholder="La tua email")
        password = st.text_input("Password", type="password", placeholder="Scegli password")
        password_confirm = st.text_input("Conferma Password", type="password", placeholder="Ripeti password")
        
        col_register, col_back = st.columns(2)
        
        with col_register:
            if st.button("✅ Registrati", use_container_width=True, type="primary"):
                if username and email and password and password_confirm:
                    if password == password_confirm:
                        if len(password) >= 6:
                            if "@" in email:
                                auth = AuthManager()
                                success, message = auth.register_user(username, email, password)
                                
                                if success:
                                    st.success(message)
                                    st.info("Ora puoi fare il login!")
                                    st.session_state.show_register = False
                                    st.rerun()
                                else:
                                    st.error(message)
                            else:
                                st.error("Email non valida")
                        else:
                            st.error("Password minimo 6 caratteri")
                    else:
                        st.error("Le password non coincidono")
                else:
                    st.error("Compila tutti i campi")
        
        with col_back:
            if st.button("⬅️ Torna al Login", use_container_width=True):
                st.session_state.show_register = False
                st.rerun()

def get_current_database():
    """Restituisce il database dell'utente corrente"""
    username = st.session_state.get('username')
    if username:
        return f"business_plan_{username}.db"
    return "business_plan_pro.db"

def main_auth():
    """Gestisce autenticazione principale"""
    st.set_page_config(page_title="Business Plan Pro - Login", page_icon="🏢")
    
    # Inizializza session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'show_register' not in st.session_state:
        st.session_state.show_register = False
    
    # CSS
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .stButton > button {
        border-radius: 10px;
        transition: all 0.3s;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Routing
    if st.session_state.show_register:
        register_form()
    else:
        login_form()

if __name__ == "__main__":
    main_auth()
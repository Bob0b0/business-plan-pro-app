@echo off
echo.
echo --- Aggiornamento App Business Plan Pro su GitHub ---
echo.

REM Vai alla directory del progetto
cd "C:\Users\robertomellone\Dropbox\business_plan_pro\"

REM Verifica se l'operazione precedente ha avuto successo
IF %ERRORLEVEL% NEQ 0 (
    echo ERRORE: Non e' stato possibile accedere alla cartella del progetto. Controlla il percorso.
    echo Premi un tasto per uscire...
    pause
    exit /b %ERRORLEVEL%
)

echo 1. Aggiungo tutti i file modificati al repository locale...
git add .
IF %ERRORLEVEL% NEQ 0 (
    echo ERRORE: git add fallito.
    echo Premi un tasto per uscire...
    pause
    exit /b %ERRORLEVEL%
)
echo.

echo 2. Creo un commit con le modifiche...
set /p commit_message="Inserisci un messaggio per il commit (es. 'Aggiornamento funzionalita X'): "
git commit -m "%commit_message%"
IF %ERRORLEVEL% NEQ 0 (
    echo ERRORE: git commit fallito. Potrebbe non esserci nulla da committare o l'identita' non e' configurata.
    echo Premi un tasto per uscire...
    pause
    exit /b %ERRORLEVEL%
)
echo.

echo 3. Carico le modifiche su GitHub...
git push origin main
IF %ERRORLEVEL% NEQ 0 (
    echo ERRORE: git push fallito. Verifica la connessione a internet o le credenziali.
    echo Premi un tasto per uscire...
    pause
    exit /b %ERRORLEVEL%
)
echo.

echo --- Operazione completata con successo! ---
echo L'app su Streamlit Community Cloud si aggiornera' automaticamente.
echo.
pause
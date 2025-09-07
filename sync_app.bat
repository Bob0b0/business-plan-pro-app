@echo off
echo.
echo === SINCRONIZZAZIONE AUTOMATICA APP ===
echo.

cd "C:\Users\rober\Dropbox\app\business_plan_pro\"

REM Verifica se ci sono modifiche locali
git status --porcelain > temp_status.txt
set /p local_changes=<temp_status.txt
del temp_status.txt

REM Controlla se ci sono aggiornamenti dal cloud
git fetch origin
git rev-list HEAD..origin/main --count > temp_behind.txt
set /p behind_count=<temp_behind.txt
del temp_behind.txt

echo --- STATO ATTUALE ---
if "%local_changes%"=="" (
    echo Modifiche locali: NESSUNA
) else (
    echo Modifiche locali: PRESENTI
)

if "%behind_count%"=="0" (
    echo Aggiornamenti cloud: NESSUNO
) else (
    echo Aggiornamenti cloud: %behind_count% commit disponibili
)
echo.

REM Gestione automatica sincronizzazione
if "%behind_count%"=="0" (
    if "%local_changes%"=="" (
        echo ✅ Tutto sincronizzato - nessuna azione necessaria.
        goto :fine
    ) else (
        echo 📤 Caricando modifiche locali sul cloud...
        goto :push_local
    )
) else (
    if "%local_changes%"=="" (
        echo 📥 Scaricando aggiornamenti dal cloud...
        goto :pull_cloud
    ) else (
        echo ⚠️ SITUAZIONE COMPLESSA: modifiche sia locali che remote
        goto :resolve_conflict
    )
)

:pull_cloud
echo.
echo Scarico aggiornamenti dal cloud...
git pull origin main
if %ERRORLEVEL% EQU 0 (
    echo ✅ Aggiornamento completato!
) else (
    echo ❌ Errore nell'aggiornamento!
)
goto :fine

:push_local
echo.
echo Salvando modifiche locali...
git add .
set timestamp=%date:~-4%-%date:~3,2%-%date:~0,2%_%time:~0,2%-%time:~3,2%
set timestamp=%timestamp: =0%
git commit -m "Auto-sync %timestamp%"
git push origin main
if %ERRORLEVEL% EQU 0 (
    echo ✅ Modifiche caricate sul cloud!
    echo L'app Streamlit si aggiornerà automaticamente.
) else (
    echo ❌ Errore nel caricamento!
)
goto :fine

:resolve_conflict
echo.
echo GESTIONE CONFLITTI:
echo 1. Hai modifiche locali non salvate
echo 2. Ci sono aggiornamenti nel cloud
echo.
echo Scegli un'opzione:
echo [1] Priorità al CLOUD (perdi modifiche locali)
echo [2] Priorità al PC (forzi le tue modifiche)
echo [3] Annulla (gestisci manualmente)
echo.
set /p choice="Inserisci 1, 2 o 3: "

if "%choice%"=="1" (
    echo.
    echo Salvando backup delle modifiche locali...
    git stash
    echo Scaricando dal cloud...
    git pull origin main
    echo ✅ Cloud sincronizzato. Modifiche locali salvate in stash.
    echo Usa 'git stash pop' per recuperarle se necessario.
)

if "%choice%"=="2" (
    echo.
    echo Forzando priorità alle modifiche locali...
    git add .
    git commit -m "Force sync - priorità locale %timestamp%"
    git push origin main --force
    echo ✅ Modifiche locali forzate sul cloud!
)

if "%choice%"=="3" (
    echo.
    echo Operazione annullata. Gestisci manualmente:
    echo - git stash (salva modifiche locali)
    echo - git pull (scarica cloud)
    echo - git stash pop (ripristina modifiche)
)

:fine
echo.
echo --- OPERAZIONE COMPLETATA ---
echo.
pause
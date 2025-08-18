@echo off
set "source_folder=c:\users\rober\dropbox\business_plan_pro"
set "destination_folder=c:\users\rober\dropbox\backupBP"

:: Ottiene la data corrente nel formato DD-MM-YYYY
for /f "tokens=1-3 delims=/ " %%a in ("%date%") do (
    set "day=%%a"
    set "month=%%b"
    set "year=%%c"
)
:: Aggiusta il giorno e il mese se sono a singola cifra (es. 1 diventa 01)
if "%day:~0,1%"==" " set "day=0%day:~1,1%"
if "%month:~0,1%"==" " set "month=0%month:~1,1%"

:: %year% in Windows italiano di solito è già a 4 cifre (es. 2025).
:: Se per qualche motivo fosse a 2 cifre (es. 25), decomenta la riga qui sotto:
:: if "%year:~0,2%"=="20" set "year=20%year%"

set "current_date=%day%-%month%-%year%"

:: Ottiene l'ora corrente nel formato HH.MM (senza secondi)
for /f "tokens=1-2 delims=:" %%a in ("%time%") do (
    set "hour=%%a"
    set "minute=%%b"
)
:: Aggiusta l'ora se è a singola cifra (es. 1 diventa 01)
if "%hour:~0,1%"==" " set "hour=0%hour:~1,1%"
set "current_time=%hour%.%minute%"

:: Crea il nome della cartella di destinazione
set "backup_name=business_plan_pro_%current_date%_h%current_time%"
set "full_destination_path=%destination_folder%\%backup_name%"

:: Controlla se la cartella sorgente esiste
if not exist "%source_folder%" (
    echo Errore: La cartella sorgente "%source_folder%" non esiste.
    goto :eof
)

:: Crea la cartella di destinazione se non esiste
if not exist "%destination_folder%" (
    mkdir "%destination_folder%"
)

:: Copia la cartella
echo Copia di "%source_folder%" in "%full_destination_path%"...
xcopy "%source_folder%" "%full_destination_path%\" /E /I /H /K /Y

echo Backup completato!
echo La cartella e' stata salvata come: "%backup_name%"
pause
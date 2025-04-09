@echo off
echo Setting up Tsipster environment...
echo.

REM Activate the virtual environment
call .\.venv\Scripts\activate

REM Run the directory setup script
python setup_directories.py
echo.

REM Ask if user wants to run the scraper
SET /P SCRAPE=Do you want to run the Winmasters scraper to get fresh data? (y/n): 
IF /I "%SCRAPE%"=="y" (
    echo Running Winmasters scraper...
    python scrapers/winmasters_scraper.py
    echo.
)

REM Start the Flask server (API)
echo Starting Flask backend server...
start cmd /k "call .\.venv\Scripts\activate && python app.py"

REM Wait for server to start
echo Waiting for server to start...
timeout /t 5 /nobreak > nul

REM Run Flutter in Chrome (not just build)
echo Starting Flutter frontend...
if exist flutter_tsipster (
    cd flutter_tsipster
    start cmd /k "flutter run -d chrome"
    cd ..
) else (
    echo Error: flutter_tsipster directory not found.
    echo Please create it by running: flutter create flutter_tsipster
)

echo.
echo Tsipster is now running!
echo Flask API: http://localhost:5000 (backend)
echo Flutter Web: Running in Chrome (should open automatically)
echo.
echo Press any key to exit this window...
pause > nul
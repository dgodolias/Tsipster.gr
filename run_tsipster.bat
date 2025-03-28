@echo off
echo Setting up Tsipster environment...
echo.

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

REM Start the Flask server
echo Starting Flask backend server...
start cmd /k "python app.py && echo Flask server running at http://localhost:5000"

REM Wait a moment for the server to start
echo Waiting for server to start...
timeout /t 5 /nobreak > nul

REM Ask if user wants to run the Flutter app
SET /P FLUTTER=Do you want to run the Flutter app? (y/n): 
IF /I "%FLUTTER%"=="y" (
    echo Starting Flutter frontend...
    cd flutter_tsipster
    start cmd /k "flutter run -d chrome"
    
    REM Wait for Flutter to start
    echo Waiting for Flutter to launch...
    timeout /t 3 /nobreak > nul
    
    REM Open the browser automatically if Flutter doesn't
    echo Opening browser if needed...
    start http://localhost:5000
) ELSE (
    echo.
    echo Opening browser to view web interface...
    start http://localhost:5000
)

echo.
echo Tsipster is now running!
echo Flask API: http://localhost:5000
echo Flutter Web (if selected): http://localhost:8080 or similar
echo.
echo Press any key to exit this window...
pause > nul

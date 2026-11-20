@echo off
REM Double-click this file to start the ETF Analysis demo.
REM It opens the app in your web browser. Close this black window to stop the demo.

REM go to the folder that holds this file, so the app finds its own files
cd /d "%~dp0"

echo.
echo   Starting the Vanguard ETF Analysis demo...
echo   Your browser will open in a few seconds.
echo.
echo   Keep this window open while you use the demo.
echo   Close it, or press Ctrl+C, when you are finished.
echo.

REM start Streamlit, which opens the browser by itself
python -m streamlit run app.py

REM if the app stops because of an error, keep the window open so the message can be read
echo.
echo   The demo has stopped.
pause

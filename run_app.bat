@echo off
rem This batch file launches the Industrial Gauge Reader application.

title Gauge Reader App Launcher

echo.
echo =======================================================
echo  Launching the Industrial Gauge Reader App...
echo =======================================================
echo.
echo  A web browser will open with the application shortly.
echo.
echo  Do NOT close this window. It is the server for the app.
echo  To shut down the app, press Ctrl + C in this window.
echo.

rem Changes directory to the location of this batch file.
rem This ensures it runs correctly from anywhere.
cd /d "%~dp0"

rem Starts the Streamlit application using Python.
python -m streamlit run gauge_reader_app.py
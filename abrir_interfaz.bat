@echo off
rem Doble clic aqui para abrir la interfaz visual en el navegador.
rem No cierre esta ventana negra mientras use la pagina.
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py app.py
) else (
    python app.py
)
if errorlevel 1 (
    echo.
    echo No se pudo iniciar. Verifique que Python 3.8+ este instalado: https://www.python.org/downloads/
)
pause

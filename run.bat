@echo off
rem CSU digital twin local launcher. venv is kept outside OneDrive.
set VENV=%LOCALAPPDATA%\csu_venv
if not exist "%VENV%\Scripts\python.exe" (
    echo [setup] creating virtual environment...
    python -m venv "%VENV%" || goto :err
)
"%VENV%\Scripts\python.exe" -m pip install -q -r "%~dp0requirements.txt" || goto :err
"%VENV%\Scripts\python.exe" -m streamlit run "%~dp0streamlit_app.py" --server.port 8501
goto :eof
:err
echo Failed. Check that Python is installed.
pause

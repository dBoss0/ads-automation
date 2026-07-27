@echo off
REM Use this to start the app instead of "streamlit run streamlit_app.py"
REM PYTHONDONTWRITEBYTECODE prevents stale .pyc files (OneDrive resets timestamps)
set PYTHONDONTWRITEBYTECODE=1
streamlit run streamlit_app.py

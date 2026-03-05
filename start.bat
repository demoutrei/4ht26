@echo off
cd "D:\github\demoutrei\4ht26"
@REM cd /d "c:\Users\user\Documents\HACKATHON SHIT\4ht26"
start cmd /c "fastapi dev api/api.py"
@REM start cmd /c "python -m uvicorn api.api:app --host 127.0.0.1 --port 8000 --reload"
timeout /t 3
node app.js
pause
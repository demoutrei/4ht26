@echo off
cd "D:\github\demoutrei\4ht26"
start cmd /c "fastapi dev src/api.py"
node app.js
pause
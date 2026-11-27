$env:RESTRO_DEMO = '1'
if (-not $env:DATABASE_URL) { $env:DATABASE_URL = 'sqlite:///restroiq_demo_v5.db' }
if (Test-Path '.venv/Scripts/python.exe') { & ./.venv/Scripts/python.exe run.py } else { python run.py }

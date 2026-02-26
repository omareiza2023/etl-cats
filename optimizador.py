import schedule
import time
import subprocess
import sys  # <--- Asegúrate de que esto esté
from datetime import datetime

def tarea_etl():
    print(f"\n[{datetime.now()}] 🕒 Iniciando proceso ETL automático...")
    try:
        # CAMBIO AQUÍ: sys.executable detecta automáticamente tu venv activo
        subprocess.run([sys.executable, "scripts/extractor.py"], check=True)
        print(f"[{datetime.now()}] ✅ Proceso completado exitosamente.")
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error: {e}")

schedule.every(1).minutes.do(tarea_etl)

print("🚀 Programador activo (Usando venv dinámico).")
tarea_etl() 

while True:
    schedule.run_pending()
    time.sleep(1)
import schedule
import time
import subprocess
import sys
from datetime import datetime

def tarea_etl():
    print(f"\n[{datetime.now()}] 🕒 Iniciando proceso ETL automático...")
    try:
        # 1. Ejecutar extractor
        print(f"[{datetime.now()}] 📡 Ejecutando extractor...")
        subprocess.run([sys.executable, "-m", "scripts.extractor"], check=True)
        print(f"[{datetime.now()}] ✅ Extractor completado.")

        # 2. Ejecutar loader
        print(f"[{datetime.now()}] 📦 Ejecutando loader...")
        subprocess.run([sys.executable, "-m", "scripts.loader"], check=True)
        print(f"[{datetime.now()}] ✅ Loader completado.")

        print(f"[{datetime.now()}] 🐱 Pipeline ETL finalizado exitosamente.")

    except subprocess.CalledProcessError as e:
        print(f"[{datetime.now()}] ❌ Error en el pipeline: {e}")
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error inesperado: {e}")

# Programar cada 1 minuto
schedule.every(1).minutes.do(tarea_etl)

print("🚀 Programador activo. Ejecutando extractor + loader cada 1 minuto.")
tarea_etl()

while True:
    schedule.run_pending()
    time.sleep(1)
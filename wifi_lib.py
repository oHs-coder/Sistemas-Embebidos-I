# ==========================================
# wifi_lib.py
# Librería para conexión WiFi desde archivo .txt
# ==========================================

import network
import time

def cargar_config(nombre_archivo):
    """
    Lee el archivo de configuración .txt con formato CLAVE=VALOR
    y devuelve un diccionario con los datos.
    """
    config = {}
    try:
        with open(nombre_archivo, "r") as f:
            for linea in f:
                linea = linea.strip()
                if not linea or linea.startswith("#"):
                    continue
                if "=" in linea:
                    clave, valor = linea.split("=", 1)
                    config[clave.strip()] = valor.strip()
        print(f"✅ Configuración cargada desde {nombre_archivo}")
    except Exception as e:
        print(f"⚠️ Error leyendo {nombre_archivo}: {e}")
    return config


def conectar_wifi(nombre_archivo):
    """
    Conecta la Pico W al WiFi usando los datos del archivo de configuración.
    Retorna el objeto wlan ya conectado.
    """
    cfg = cargar_config(nombre_archivo)
    ssid = cfg.get("WIFI_SSID", "")
    password = cfg.get("WIFI_PASS", "")

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    print(f"🔌 Conectando al WiFi '{ssid}'...")
    t0 = time.time()
    while not wlan.isconnected():
        if time.time() - t0 > 15:
            print("❌ Error: no se pudo conectar al WiFi.")
            return None
        time.sleep(0.5)

    print("✅ Conectado al WiFi:", wlan.ifconfig())
    return wlan

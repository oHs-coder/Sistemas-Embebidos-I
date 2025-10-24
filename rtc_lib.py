# ==========================================
# rtc_lib.py
# Librería para sincronizar y obtener hora UTC y local (Colombia)
# ==========================================

import ntptime
import time
from machine import RTC
import wifi_lib

# ------------------------------------------
# Sincronización con NTP
# ------------------------------------------
def sincronizar_rtc():
    """
    Sincroniza el RTC con un servidor NTP.
    El RTC queda en hora UTC (no local).
    """
    try:
        wifi_lib.conectar_wifi()
        print("🌐 Sincronizando con NTP...")
        ntptime.host = "pool.ntp.org"
        ntptime.settime()
        print("✅ RTC sincronizado en UTC.")
    except Exception as e:
        print("⚠️ Error sincronizando RTC:", e)

# ------------------------------------------
# Hora LOCAL (Colombia UTC-5)
# ------------------------------------------
def obtener_fecha_hora_local():
    """
    Devuelve (fecha, hora) ajustada a Colombia (UTC-5).
    Ejemplo -> ('2025-10-12', '19:22:45')
    """
    t = time.localtime(time.time())
    fecha = "{:04d}-{:02d}-{:02d}".format(t[0], t[1], t[2])
    hora = "{:02d}:{:02d}:{:02d}".format(t[3], t[4], t[5])
    return fecha, hora
# ------------------------------------------
# Convertir ISO a epoch UTC
# ------------------------------------------
def convertir_a_timestamp_utc(tiempo_iso):
    """
    Convierte un tiempo ISO (ej: '2025-10-12T20:00:00Z')
    a timestamp (epoch) en segundos UTC.
    """
    try:
        s = tiempo_iso.strip().replace("Z", "")
        fecha, hora = s.split("T")
        anio, mes, dia = [int(x) for x in fecha.split("-")]
        h, m, sec = [int(x) for x in hora.split(":")]
        tm = (anio, mes, dia, h, m, sec, 0, 0)
        epoch_utc = time.mktime(tm)  # mktime usa local pero RTC está en UTC, así que es válido
        return int(epoch_utc)
    except Exception as e:
        print("⚠️ Error convirtiendo timestamp UTC:", e)
        return None

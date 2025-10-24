import socket
import json
import time
import robot_servos    # ✅ usamos la librería para los servos
import wifi_lib  # ✅ usamos la librería para WiFi
import rtc_lib   # ✅ usamos la librería RTC
import utime
from robot_pid import mover_recto, girar# ✅ usamos la librería para los motores y encoders
from machine import Pin  # ✅ para el LED integrado

# -----------------------------
# CONFIGURACIÓN DE LED
# -----------------------------
led = Pin("LED", Pin.OUT)
led.value(1)  # 💡 Se energizó la frambuesa, LED encendido fijo

# -----------------------------
# CONFIGURACIÓN DE RED
# -----------------------------
config = wifi_lib.cargar_config("Conexion4.txt")
BROKER_IP   = config.get("BROKER_IP", "")
print(BROKER_IP)
BROKER_PORT = int(config.get("BROKER_PORT", 5051))

# -----------------------------
# TOPICS (fijos)
# -----------------------------
TOPIC_SUB_1 = "UDFJC/emb1/robot2/RPi/state"
TOPIC_SUB_2 = "UDFJC/emb1/+/RPi/sequence"

# -----------------------------
# INICIALIZACIÓN
# -----------------------------
robot_servos.mover_servos(0, 45, -90, 1)
datos_recibidos = []
secuencias = {}

# -----------------------------
# FUNCIÓN CONEXIÓN BROKER
# -----------------------------
def conectar_broker():
    s = socket.socket()
    s.connect((BROKER_IP, BROKER_PORT))
    print(f"✅ Conectado al broker {BROKER_IP}:{BROKER_PORT}")
    led.value(0)
    return s

def enviar_json(sock, obj):
    msg = json.dumps(obj) + "\n"
    sock.send(msg.encode())
#------------------------------
#Definicion de ejecucion de secuencia
#------------------------------
def ejecutar_secuencia(nombre):
    """
    Ejecuta la secuencia indicada por su nombre paso a paso.
    """
    if nombre not in secuencias:
        print(f"⚠️ Secuencia '{nombre}' no existe.")
        return

    print(f"🚀 Ejecutando secuencia '{nombre}'...")
    for i, paso in enumerate(secuencias[nombre], 1):
        try:
            v = paso["v"]; w = paso["w"]
            n1 = paso["alfa0"]; n2 = paso["alfa1"]; n3 = paso["alfa2"]; dur = paso["duration"]
            print(f"▶️ Paso {i}: v={v}, w={w}, α0={n1}, α1={n2}, α2={n3}, dur={dur}")
            robot_servos.mover_servos(n1, n2, n3, float(dur))
            if v != 0:
                print(f"🚗 Ejecutando movimiento recto: v={v} dm/s durante {dur}s")
                mover_recto(float(v), float(dur))
            if w != 0:
                print(f"🔄 Ejecutando giro: ω={w} durante {dur}s")
                girar(w, dur)
        except Exception as e:
            print(f"⚠️ Error en paso {i}: {e}")
    print(f"✅ Secuencia '{nombre}' completada.")
    robot_servos.mover_servos(0, 45, -90, 1)

# -----------------------------
# INTERPRETACIÓN DE MENSAJES
# -----------------------------
def procesar_mensaje(obj):
    try:
        topic = obj.get("topic", None)
        data = obj.get("data", None)

        if not topic:
            print("⚠️ Mensaje sin campo 'topic'. Ignorado.")
            return
        if not isinstance(data, dict):
            print("⚠️ Mensaje sin campo 'data' tipo dict. Ignorado.")
            return

        # 💡 Encender LED 1s al recibir mensaje
        led.value(1)
        utime.sleep(0.5)
        led.value(0)
        print(f"\n📨 Mensaje recibido del topic: {topic}")

        # --- TOPIC STATE ---
        if topic == "UDFJC/emb1/robot2/RPi/state":
            v = data.get("v")
            w = data.get("w")
            n1 = data.get("alfa0")
            n2 = data.get("alfa1")
            n3 = data.get("alfa2")
            dur = data.get("duration")

            if None in (v, w, n1, n2, n3, dur):
                print("⚠️ Datos incompletos.")
                return

            robot_servos.mover_servos(float(n1), float(n2), float(n3), float(dur))
            # --- Ejecución condicional ---
            if v != 0:
                print(f"🚗 Ejecutando movimiento recto: v={v} dm/s durante {dur}s")
                mover_recto(v, dur)
            if w != 0:
                print(f"🔄 Ejecutando giro: ω={w} durante {dur}s")
                girar(w, dur)
            return

        # --- TOPIC SEQUENCE ---
        elif topic.startswith("UDFJC/emb1/") and topic.endswith("/RPi/sequence"):
            action = data.get("action", "").lower()
            acciones_validas = ["create", "delete", "add_state", "execute_now", "schedule"]

            # 🕒 Mostrar hora local en cada acción
            fecha, hora = rtc_lib.obtener_fecha_hora_local()

            print(f"🕒 Hora local: {fecha} {hora}")

            if action not in acciones_validas:
                print(f"⚠️ Acción inválida: {action}")
                return

            if action == "create":
                secuencia = data.get("sequence", {})
                nombre = secuencia.get("name", None)
                estados = secuencia.get("states", [])
                if not nombre or not isinstance(estados, list):
                    print("⚠️ Secuencia inválida.")
                    return
                secuencias[nombre] = estados
                print(f"🧩 Secuencia '{nombre}' creada con {len(estados)} estados.")
                for i, e in enumerate(estados, 1):
                    print(f"   [{i}] {e}")

            elif action == "delete":
                nombre = data.get("name", None)
                if nombre in secuencias:
                    del secuencias[nombre]
                    print(f"🗑️ Secuencia '{nombre}' eliminada.")
                else:
                    print(f"⚠️ Secuencia '{nombre}' no encontrada.")

            elif action == "add_state":
                nombre = data.get("name", None)
                nuevo = data.get("state", None)
                if nombre not in secuencias or not isinstance(nuevo, dict):
                    print(f"⚠️ No se puede agregar: secuencia '{nombre}' no encontrada.")
                    return
                secuencias[nombre].append(nuevo)
                print(f"➕ Estado agregado a '{nombre}': {nuevo}")

            elif action == "execute_now":
                nombre = data.get("name", "")
                ejecutar_secuencia(nombre)
            # -----------------------------
            # SCHEDULE
            # -----------------------------
            elif action == "schedule":
                nombre = data.get("name", "")
                hora_prog_str = data.get("time", "")
                if not nombre or not hora_prog_str:
                    print("⚠️ Faltan campos 'name' o 'time'.")
                    return
                try:
                    fecha_str, hora_str = hora_prog_str.strip().split("T")
                    anio, mes, dia = [int(x) for x in fecha_str.split("-")]
                    h, m, sec = [int(x) for x in hora_str.split(":")]
                    epoch_programado = time.mktime((anio, mes, dia, h, m, sec, 0, 0))

                    if time.time() >= epoch_programado:
                        print("⏰ La hora ya pasó")
                        return

                    tareas_programadas.append((nombre, epoch_programado))
                    print(f"📅 Secuencia '{nombre}' agregada a la agenda")
                except Exception as e:
                    print("⚠️ Error procesando 'schedule':", e)

    except Exception as e:
        print("⚠️ Error procesando mensaje:", e)

# -----------------------------
# RECEPCIÓN CONTINUA
# -----------------------------
tareas_programadas = []  # lista de tuplas (nombre, epoch_programado)
import usocket as socket
import uselect as select

def recibir_loop(sock):
    buf = b""
    print("📡 Esperando mensajes del broker...")
    poller = select.poll()
    poller.register(sock, select.POLLIN)

    while True:
        # 1️⃣ Esperar datos con timeout de 0.1s
        events = poller.poll(100)  # timeout en ms
        if events:
            try:
                data = sock.recv(1024)
                if not data:
                    print("❌ Desconectado del broker")
                    break
                buf += data
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    if line:
                        obj = json.loads(line.decode().strip())
                        procesar_mensaje(obj)
            except OSError as e:
                print("⚠️ Error de socket:", e)
                continue

        # 2️⃣ Revisar tareas pendientes aunque no lleguen mensajes
        ahora = time.time()
        for tarea in list(tareas_programadas):
            nombre, t_prog = tarea
            if ahora >= t_prog:
                print(f"🚀 Ejecutando secuencia programada: {nombre}")
                ejecutar_secuencia(nombre)
                tareas_programadas.remove(tarea)

# -----------------------------
# PROGRAMA PRINCIPAL
# -----------------------------

wifi_lib.conectar_wifi("Conexion4.txt")  # ✅ conexión WiFi directa
               # ✅ sincroniza hora con NTP

sock = conectar_broker()

# Suscribirse
enviar_json(sock, {"action": "SUB", "topic": TOPIC_SUB_1})
print(f"📝 Suscrito al tópico: {TOPIC_SUB_1}")
enviar_json(sock, {"action": "SUB", "topic": TOPIC_SUB_2})
print(f"📝 Suscrito al tópico: {TOPIC_SUB_2}")

# Escuchar mensajes
recibir_loop(sock)




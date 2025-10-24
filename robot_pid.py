from picozero import DigitalInputDevice, Robot, DigitalOutputDevice
from time import sleep, time

import math

# ====================================
# ======== CLASE ENCODER =============
# ====================================
class Encoder:
    def __init__(self, pin):
        self._value = 0
        self.encoder = DigitalInputDevice(pin)
        self.encoder.when_activated = self._increment
        self.encoder.when_deactivated = self._increment

    def reset(self):
        self._value = 0

    def _increment(self):
        self._value += 1

    @property
    def value(self):
        return self._value


# ====================================
# ======== CONFIGURACIÓN GLOBAL ======
# ====================================
SAMPLETIME = 0.1     # segundos
KP = 0.02
KD = 0.001
KI = 0.0005

RANURAS_DISCO = 20        # número de ranuras del disco encoder
RADIO_LLANTA_CM = 7     # distancia del eje a la llanta
RADIO_LLANTA_M = RADIO_LLANTA_CM / 100.0
CIRCUNFERENCIA_M = 2 * 3.1416 * RADIO_LLANTA_M


# ====================================
# ======== CONFIGURACIÓN HARDWARE ====
# ====================================
# Pines: Robot((IN1, IN2), (IN3, IN4))
r = Robot((2, 3), (5, 4))
e1 = Encoder(16)
e2 = Encoder(17)

# Pines enable motores
enable_m1 = DigitalOutputDevice(6)
enable_m2 = DigitalOutputDevice(7)
enable_m1.on()
enable_m2.on()


# ====================================
# ======== FUNCIÓN PRINCIPAL =========
# ====================================
def mover_recto(velocidad_dm_s, tiempo_s):
    """
    Mueve el robot recto a una velocidad (dm/s) durante un tiempo (s),
    con control PID. Si la velocidad es negativa, el robot va hacia atrás.
    """

    # Convertimos velocidad de dm/s a m/s
    velocidad_m_s = velocidad_dm_s / 10.0

    # Detectamos dirección
    direccion = 1 if velocidad_m_s >= 0 else -1
    velocidad_m_s = abs(velocidad_m_s)  # Solo trabajamos con magnitud

    # Calcula distancia total esperada
    distancia_objetivo = velocidad_m_s * tiempo_s

    # Calcula pulsos esperados
    vueltas_necesarias = distancia_objetivo / CIRCUNFERENCIA_M
    pulsos_objetivo = vueltas_necesarias * RANURAS_DISCO

    # Inicializa variables PID
    e1.reset()
    e2.reset()
    e1_prev_error = 0
    e2_prev_error = 0
    e1_sum_error = 0
    e2_sum_error = 0

    # Velocidades iniciales base
    m1_speed = 0.6
    m2_speed = 0.8

    # Aplicar dirección (hacia adelante o atrás)
    if direccion == 1:
        r.value = (m1_speed, m2_speed)
        print("🟩 Dirección: hacia adelante")
    else:
        r.value = (-m1_speed, -m2_speed)
        print("🟥 Dirección: hacia atrás")

    print(f"Objetivo: {distancia_objetivo:.2f} m en {tiempo_s:.2f}s ({pulsos_objetivo:.0f} pulsos esperados)")

    inicio = time()

    while (time() - inicio) < tiempo_s:
        # Medir pulsos en el sample
        e1_pulsos = e1.value
        e2_pulsos = e2.value

        # Calcular distancia por rueda
        dist_e1 = (e1_pulsos / RANURAS_DISCO) * CIRCUNFERENCIA_M
        dist_e2 = (e2_pulsos / RANURAS_DISCO) * CIRCUNFERENCIA_M

        # Calcular velocidad instantánea
        v_e1 = dist_e1 / SAMPLETIME
        v_e2 = dist_e2 / SAMPLETIME

        # Calcular errores PID
        e1_error = velocidad_m_s - v_e1
        e2_error = velocidad_m_s - v_e2

        # Control PID
        m1_speed += (e1_error * KP) + (e1_prev_error * KD) + (e1_sum_error * KI)
        m2_speed += (e2_error * KP) + (e2_prev_error * KD) + (e2_sum_error * KI)

        # Limitar entre 0 y 1
        m1_speed = max(min(1, m1_speed), 0)
        m2_speed = max(min(1, m2_speed), 0)

        # Aplicar dirección a la señal final
        if direccion == 1:
            r.value = (m1_speed, m2_speed)
        else:
            r.value = (-m1_speed, -m2_speed)

        # Mostrar datos
        print(f"v_e1={v_e1:.3f} | v_e2={v_e2:.3f} | m1={direccion*m1_speed:.2f} | m2={direccion*m2_speed:.2f}")

        # Reset para siguiente iteración
        e1.reset()
        e2.reset()
        e1_prev_error = e1_error
        e2_prev_error = e2_error
        e1_sum_error += e1_error
        e2_sum_error += e2_error

        sleep(SAMPLETIME)

    # Detener robot
    r.stop()
    print("✅ Movimiento completado")

def girar(velocidad_angular, tiempo_s):
    """
    Gira el robot a una velocidad angular (°/s) durante un tiempo dado (s).
    Internamente convierte a rad/s para usar el control existente.
    Giro positivo = antihorario, Giro negativo = horario.
    """
    # --- Conversión a rad/s ---
    velocidad_angular = math.radians(velocidad_angular)

    # --- Parámetros físicos ---
    L = 0.136  # distancia entre ruedas (m)
    R = RADIO_LLANTA_M
    perimetro = CIRCUNFERENCIA_M

    # --- Inicialización ---
    e1.reset()
    e2.reset()
    prev_error = 0
    sum_error = 0

    # Determina el sentido del giro
    sentido = 1 if velocidad_angular >= 0 else -1
    velocidad_angular = abs(velocidad_angular)

    m1_speed = 0.5
    m2_speed = 0.5
    # Una rueda avanza, otra retrocede según el sentido
    if sentido > 0:
        r.value = (m1_speed, -m2_speed)
    else:
        r.value = (-m1_speed, m2_speed)

    print(f"🌀 Girando a {sentido * velocidad_angular:.2f} rad/s durante {tiempo_s:.2f}s")

    inicio = time()
    while (time() - inicio) < tiempo_s:
        e1_pulsos = e1.value
        e2_pulsos = e2.value

        dist_e1 = (e1_pulsos / RANURAS_DISCO) * perimetro
        dist_e2 = (e2_pulsos / RANURAS_DISCO) * perimetro

        v_e1 = dist_e1 / SAMPLETIME
        v_e2 = dist_e2 / SAMPLETIME

        vel_ang_real = (v_e2 - v_e1) / L

        error = velocidad_angular - abs(vel_ang_real)
        ajuste = (error * KP) + ((error - prev_error) * KD) + (sum_error * KI)

        m1_speed = 0.5 - ajuste
        m2_speed = 0.5 + ajuste

        # Aplica el sentido
        if sentido > 0:
            r.value = (m1_speed, -m2_speed)
        else:
            r.value = (-m1_speed, m2_speed)

        print(f"ω_real={vel_ang_real:.3f} | ω_target={sentido * velocidad_angular:.3f} | m1={m1_speed:.2f} | m2={m2_speed:.2f}")

        e1.reset()
        e2.reset()
        prev_error = error
        sum_error += error
        sleep(SAMPLETIME)

    r.stop()
    print("✅ Giro completado")

def reset_encoders():
    """Reinicia los contadores de los encoders."""
    e1.reset()
    e2.reset()
    print("Encoders reiniciados.")

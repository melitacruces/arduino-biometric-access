"""Carga automática de sketches al Arduino mediante arduino-cli.

Compila y sube el firmware correspondiente (ingresar / insertar) a la placa,
usando el binario ``arduino-cli.exe`` incluido en la carpeta ``tools/``.
"""

import os
import subprocess

# Rutas dinámicas basadas en la estructura del repositorio.
# __file__ está en app/, así que la raíz del repo es un nivel hacia arriba.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARDUINO_CLI = os.path.join(BASE_DIR, "tools", "arduino-cli.exe")

FQBN = "arduino:avr:uno"
PUERTO = "COM6"  # Cambia si usas otro puerto


def cargar_sketch(nombre_sketch):
    """Compila y sube el sketch indicado (carpeta dentro de ``arduino/``)."""
    path = os.path.join(BASE_DIR, "arduino", nombre_sketch)
    try:
        print(f"[INFO] Compilando {path}...")
        subprocess.run([ARDUINO_CLI, "compile", "--fqbn", FQBN, path], check=True)

        print(f"[INFO] Subiendo a {PUERTO}...")
        subprocess.run([ARDUINO_CLI, "upload", "-p", PUERTO, "--fqbn", FQBN, path], check=True)

        print("[✅] Sketch cargado con éxito.")
    except subprocess.CalledProcessError as e:
        print(f"[❌] Error al cargar el sketch:\n{e}")
        raise RuntimeError("No se pudo cargar el sketch al Arduino.")

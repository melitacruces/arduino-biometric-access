# 🛠️ Herramientas del Sensor de Huellas

Esta carpeta contiene **sketches utilitarios** para gestionar el sensor biométrico AS608 usando un Arduino Uno. Estas herramientas permiten eliminar huellas, vaciar toda la memoria del sensor o registrar huellas manualmente, sin depender del software Python.

---

## 🗃️ Contenido

### `delete.ino`

Elimina una huella específica almacenada en el sensor.

- 📥 **Entrada esperada**: ID de huella (1–127), enviado por monitor serial.
- ✅ **Mensajes esperados**: `Deleted OK`, `Delete failed`, `ID not found`, etc.
- 🧠 **Uso típico**: Borrar una huella específica de forma manual.

---

### `empty.ino`

Elimina **todas las huellas** del sensor.

- ⚠️ **Advertencia**: Esta acción es irreversible.
- 🔁 **Uso recomendado**: Cuando se requiere limpiar completamente el sensor.
- 📤 **Resultado**: El sensor quedará sin huellas registradas.

---

### `enroll.ino`

Registra manualmente una nueva huella directamente desde Arduino.

- 👆 **Proceso guiado**: El usuario debe colocar y retirar el dedo dos veces.
- 📥 **Entrada esperada**: ID de huella deseado (1–127), por monitor serie.
- ✅ **Mensajes esperados**: `Enrolling ID`, `Remove finger`, `Stored!`, `Enrollment failed`.
- 🧠 **Uso típico**: Cargar huellas sin usar la interfaz Python, útil para pruebas o cuando se trabaja sin base de datos.

---

## 🛠️ Requisitos Técnicos

- Librería necesaria: [`Adafruit_Fingerprint_Sensor_Library`](https://github.com/adafruit/Adafruit-Fingerprint-Sensor-Library).
- Sensor: AS608 (o similar compatible).
- Placa: Arduino Uno R3 (o similar compatible).
- Comunicación: Pines 10 y 11 con `SoftwareSerial`.
- Monitor serie configurado a **9600 baudios** y **"Nueva línea" o "Ambos NL y CR"**.

"""Interfaz de ingreso (verificación de acceso).

Sube el sketch ``ingresar`` al Arduino y actúa como puente entre la placa y la
base de datos: escucha el puerto serial y responde a las peticiones del firmware
(``CONSULTAR_ID:`` y ``VERIFICAR:``) consultando MySQL en un hilo en segundo plano.
"""

import threading

import customtkinter as ctk
import serial
import mysql.connector

from arduino_uploader import cargar_sketch


class InterfazIngreso(ctk.CTk):
    def __init__(self, volver_al_menu=None):
        super().__init__()
        self.title("Ingreso de Usuarios")
        self.geometry("600x400")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.volver_al_menu = volver_al_menu

        self.textbox = ctk.CTkTextbox(self, width=580, height=300)
        self.textbox.pack(padx=10, pady=10)

        self.boton_salir = ctk.CTkButton(self, text="Salir", command=self.salir)
        self.boton_salir.pack(pady=10)

        self.running = True
        try:
            cargar_sketch("ingresar")  # Asume carpeta ./ingresar/ con ingresar.ino dentro
        except RuntimeError as e:
            self.mostrar_log(str(e))
            return
        self.iniciar_hilo()

    def iniciar_hilo(self):
        self.hilo = threading.Thread(target=self.procesar_serial, daemon=True)
        self.hilo.start()

    def procesar_serial(self):
        try:
            arduino = serial.Serial('COM6', 9600)
        except Exception as e:
            self.mostrar_log(f"[ERROR] No se pudo conectar al Arduino: {e}")
            return

        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="proyecto_huella",
        )
        cursor = db.cursor()

        self.mostrar_log("Esperando datos del Arduino...")

        while self.running:
            try:
                if arduino.in_waiting:
                    line = arduino.readline().decode().strip()

                    # El Arduino pregunta el nombre asociado a una huella detectada
                    if line.startswith("CONSULTAR_ID:"):
                        huella_id = int(line.replace("CONSULTAR_ID:", ""))
                        cursor.execute(
                            "SELECT nombre FROM usuarios WHERE huella_id = %s AND estado = 'activo'",
                            (huella_id,),
                        )
                        result = cursor.fetchone()
                        if result:
                            nombre = result[0]
                            arduino.write(f'nombre:{nombre}\n'.encode())
                            self.mostrar_log(f"[INFO] Nombre enviado: {nombre}")
                        else:
                            arduino.write(b'nombre:desconocido\n')
                            self.mostrar_log(f"[WARN] ID {huella_id} no registrado o inactivo")

                    # El Arduino pide validar la combinación huella + PIN
                    elif line.startswith("VERIFICAR:"):
                        partes = line.replace("VERIFICAR:", "").split(":")
                        huella_id = int(partes[0])
                        pin = partes[1]

                        cursor.execute(
                            "SELECT nombre FROM usuarios "
                            "WHERE huella_id = %s AND pin = %s AND estado = 'activo'",
                            (huella_id, pin),
                        )
                        result = cursor.fetchone()
                        if result:
                            nombre = result[0]
                            arduino.write(f'permitido:{nombre}\n'.encode())
                            self.mostrar_log(f"[ACCESO] Permitido para {nombre}")
                            self.mostrar_permitido(nombre)
                        else:
                            arduino.write(b'denegado\n')
                            self.mostrar_log(f"[ACCESO] Denegado para ID {huella_id}")
            except Exception as e:
                self.mostrar_log(f"[ERROR] {e}")
                arduino.write(b'denegado\n')

    def mostrar_log(self, mensaje):
        self.textbox.insert("end", mensaje + "\n")
        self.textbox.see("end")

    def mostrar_permitido(self, nombre):
        popup = ctk.CTkToplevel(self)
        popup.title("Acceso Permitido")
        popup.geometry("350x150")
        popup.attributes("-topmost", True)
        popup.grab_set()
        ctk.CTkLabel(
            popup,
            text=f"Acceso permitido para\n{nombre}",
            font=("Arial", 16),
            justify="center",
        ).pack(pady=20)
        ctk.CTkButton(
            popup,
            text="Aceptar",
            width=100,
            height=35,
            command=lambda: (popup.destroy(), self.salir()),
        ).pack(pady=10)

    def salir(self):
        self.running = False
        self.destroy()
        if self.volver_al_menu:
            self.volver_al_menu()


if __name__ == "__main__":
    app = InterfazIngreso()
    app.mainloop()

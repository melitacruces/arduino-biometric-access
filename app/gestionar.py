"""Gestión de usuarios (panel de administración).

CRUD completo sobre la tabla ``usuarios`` con interfaz gráfica:
    - Registrar huellas a través del Arduino (sketch ``insertar``).
    - Insertar, editar y eliminar usuarios en MySQL.
    - Exportar el padrón de usuarios a CSV.
"""

import csv
import time
from datetime import datetime
from tkinter import messagebox
from tkinter.ttk import Treeview, Style

import customtkinter as ctk
import serial
import mysql.connector


# ============================
# CONEXIÓN A LA BASE DE DATOS
# ============================

def conectar():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="proyecto_huella",
    )


# ============================
# FUNCIONES DE VALIDACIÓN
# ============================

def huella_id_existe(cursor, hid):
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE huella_id = %s", (hid,))
    return cursor.fetchone()[0] > 0


def rut_existe(cursor, rut):
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE rut = %s", (rut,))
    return cursor.fetchone()[0] > 0


def validar_huella_id(hid):
    return isinstance(hid, int) and 1 <= hid <= 127


def validar_pin(pin):
    return pin.isdigit() and len(pin) == 5


def validar_rol(rol):
    return rol.lower() in ['admin', 'empleado']


def validar_rut_partes(numero, dv):
    return numero.isdigit() and len(numero) >= 7 and len(dv) == 1 and (dv.isdigit() or dv.lower() == 'k')


def registrar_log(mensaje):
    with open("registro.log", "a") as log:
        log.write(f"{datetime.now()} - {mensaje}\n")


# ============================
# INTERFAZ GRÁFICA (GUI)
# ============================

class App(ctk.CTk):
    def __init__(self, volver_al_menu):
        super().__init__()
        self.volver_al_menu = volver_al_menu
        self.title("Gestión de Usuarios - Proyecto Huella")
        self.geometry("1100x650")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.conn = conectar()
        self.cursor = self.conn.cursor()

        self.estilo_treeview()
        self.crear_interfaz()
        self.actualizar_treeview()

    def registrar_huella_con_arduino(self, huella_id):
        ventana_proceso = ctk.CTkToplevel(self)
        ventana_proceso.title("Registro de Huella")
        ventana_proceso.geometry("400x150")
        ventana_proceso.grab_set()

        mensaje_label = ctk.CTkLabel(
            ventana_proceso, text="Esperando al Arduino...", font=("Segoe UI", 16)
        )
        mensaje_label.pack(pady=20)

        self.update()

        try:
            with serial.Serial('COM6', 9600, timeout=10) as arduino:
                time.sleep(2)
                arduino.flushInput()

                # Esperar a que el firmware indique que está listo
                while True:
                    if arduino.in_waiting > 0:
                        mensaje = arduino.readline().decode().strip()
                        print("Arduino:", mensaje)
                        mensaje_label.configure(text=mensaje)
                        self.update()
                        if mensaje == "READY":
                            break

                arduino.write(f"{huella_id}\n".encode())

                # Esperar el resultado del enrolamiento
                while True:
                    if arduino.in_waiting > 0:
                        mensaje = arduino.readline().decode().strip()
                        print("Arduino:", mensaje)
                        mensaje_label.configure(text=mensaje)
                        self.update()
                        if mensaje == "ENROLL_OK":
                            ventana_proceso.destroy()
                            return True
                        elif mensaje == "ENROLL_FAIL":
                            ventana_proceso.destroy()
                            return False
        except Exception as e:
            print("Error comunicando con Arduino:", e)
            mensaje_label.configure(text=f"Error: {e}")
            self.update()
            time.sleep(3)
            ventana_proceso.destroy()
            return False

    def mostrar_formulario_usuario(self, huella_id):
        ventana = ctk.CTkToplevel(self)
        ventana.title("Insertar Usuario")
        ventana.grab_set()

        campos = {}
        orden = ["Nombre", "RUT", "PIN", "Rol", "Estado"]

        for i, label in enumerate(orden):
            if label == "RUT":
                ctk.CTkLabel(ventana, text=label).grid(row=i, column=0, padx=10, pady=5)
                frame_rut = ctk.CTkFrame(ventana)
                frame_rut.grid(row=i, column=1, padx=10, pady=5)
                campos["RUT Número"] = ctk.CTkEntry(frame_rut, width=100)
                campos["RUT Número"].pack(side="left")
                ctk.CTkLabel(frame_rut, text=" - ").pack(side="left")
                campos["RUT DV"] = ctk.CTkEntry(frame_rut, width=30)
                campos["RUT DV"].pack(side="left")
            else:
                ctk.CTkLabel(ventana, text=label).grid(row=i, column=0, padx=10, pady=5)
                if label in ["Rol", "Estado"]:
                    opciones = ["admin", "empleado"] if label == "Rol" else ["activo", "inactivo"]
                    campos[label] = ctk.CTkComboBox(ventana, values=opciones)
                    campos[label].set(opciones[0])
                else:
                    campos[label] = ctk.CTkEntry(ventana)
                campos[label].grid(row=i, column=1, padx=10, pady=5)

        def guardar():
            try:
                nombre = campos["Nombre"].get().strip()
                rut_num = campos["RUT Número"].get().strip()
                rut_dv = campos["RUT DV"].get().strip().lower()
                if not validar_rut_partes(rut_num, rut_dv):
                    raise ValueError("RUT inválido")
                rut = f"{rut_num}-{rut_dv}"
                if rut_existe(self.cursor, rut):
                    raise ValueError("RUT ya existe")
                pin = campos["PIN"].get().strip()
                if not validar_pin(pin):
                    raise ValueError("PIN inválido")
                rol = campos["Rol"].get()
                estado = campos["Estado"].get()
                self.cursor.execute(
                    "INSERT INTO usuarios (huella_id, nombre, rut, pin, rol, estado) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (huella_id, nombre, rut, pin, rol, estado),
                )
                self.conn.commit()
                registrar_log(f"Insertado usuario: {nombre} (ID: {huella_id})")
                messagebox.showinfo("Éxito", "Usuario insertado")
                ventana.destroy()
                self.actualizar_treeview()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(ventana, text="Guardar", command=guardar).grid(
            row=len(orden), column=0, columnspan=2, pady=10
        )

    def estilo_treeview(self):
        style = Style()
        style.configure(
            "Treeview",
            background="#2a2d2e",
            foreground="white",
            rowheight=28,
            fieldbackground="#2a2d2e",
            font=("Segoe UI", 11),
        )
        style.configure("Treeview.Heading", font=("Segoe UI", 12, "bold"))

    def crear_interfaz(self):
        contenedor = ctk.CTkFrame(self, corner_radius=15)
        contenedor.pack(expand=True, fill="both", padx=20, pady=20)

        titulo = ctk.CTkLabel(contenedor, text="Gestión de Usuarios", font=("Segoe UI", 26, "bold"))
        titulo.pack(pady=(10, 20))

        self.tree = Treeview(
            contenedor,
            columns=("ID", "Nombre", "RUT", "Rol", "Estado", "Creado en"),
            show="headings",
        )
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=170)
        self.tree.pack(padx=10, pady=10, fill="both", expand=True)

        botones = ctk.CTkFrame(contenedor)
        botones.pack(pady=20)

        botones_info = [
            ("➕ Insertar", self.insertar_usuario, "#3b82f6"),
            ("✏️ Editar", self.editar_usuario, "#10b981"),
            ("❌ Eliminar", self.eliminar_usuario, "#ef4444"),
            ("⬇️ Exportar CSV", self.exportar_usuarios, "#f59e0b"),
            ("⬅️ Regresar", self.salir, "#64748b"),
        ]

        for i, (texto, comando, color) in enumerate(botones_info):
            btn = ctk.CTkButton(
                botones, text=texto, command=comando, width=140, height=40,
                corner_radius=10, fg_color=color, hover_color=color,
            )
            btn.grid(row=0, column=i, padx=10)

    def actualizar_treeview(self):
        self.cursor.execute(
            "SELECT huella_id, nombre, rut, rol, estado, creado_en FROM usuarios ORDER BY huella_id"
        )
        resultados = self.cursor.fetchall()
        for i in self.tree.get_children():
            self.tree.delete(i)
        for u in resultados:
            self.tree.insert("", "end", values=u)

    def insertar_usuario(self):
        from arduino_uploader import cargar_sketch
        try:
            cargar_sketch("insertar")  # Asume carpeta ./insertar/ con insertar.ino dentro
        except RuntimeError as e:
            messagebox.showerror("Arduino", str(e))
            return

        def pedir_huella_id():
            pid_ventana = ctk.CTkToplevel(self)
            pid_ventana.title("Registrar Huella")
            pid_ventana.grab_set()

            ctk.CTkLabel(pid_ventana, text="Ingrese Huella ID (1-127):").pack(pady=10)
            entry = ctk.CTkEntry(pid_ventana)
            entry.pack(pady=5)

            def continuar():
                try:
                    hid = int(entry.get())
                    if not validar_huella_id(hid):
                        raise ValueError("ID fuera de rango.")
                    if huella_id_existe(self.cursor, hid):
                        raise ValueError("ID ya existe.")
                    resultado = self.registrar_huella_con_arduino(hid)
                    if resultado:
                        messagebox.showinfo("Éxito", f"Huella registrada con ID {hid}")
                        pid_ventana.destroy()
                        self.mostrar_formulario_usuario(hid)
                    else:
                        messagebox.showerror("Error", "Falló el registro de huella")
                except Exception as e:
                    messagebox.showerror("Error", str(e))

            ctk.CTkButton(pid_ventana, text="Registrar", command=continuar).pack(pady=10)

        pedir_huella_id()

    def eliminar_usuario(self):
        item = self.tree.focus()
        if not item:
            messagebox.showwarning("Atención", "Seleccione un usuario")
            return
        hid = self.tree.item(item)['values'][0]
        confirm = messagebox.askyesno("Confirmar", f"¿Eliminar usuario ID {hid}?")
        if confirm:
            self.cursor.execute("DELETE FROM usuarios WHERE huella_id = %s", (hid,))
            self.conn.commit()
            registrar_log(f"Eliminado usuario ID: {hid}")
            self.actualizar_treeview()

    def exportar_usuarios(self):
        self.cursor.execute("SELECT * FROM usuarios")
        with open("usuarios.csv", "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow([i[0] for i in self.cursor.description])
            writer.writerows(self.cursor.fetchall())
        registrar_log("Usuarios exportados")
        messagebox.showinfo("Exportado", "Usuarios exportados a CSV")

    def editar_usuario(self):
        item = self.tree.focus()
        if not item:
            messagebox.showwarning("Atención", "Seleccione un usuario")
            return
        valores = self.tree.item(item)['values']
        hid_original = valores[0]

        ventana = ctk.CTkToplevel(self)
        ventana.title("Editar Usuario")
        ventana.grab_set()

        campos = {}

        orden = ["Nombre", "RUT", "PIN", "Rol", "Estado"]
        datos = {
            "Nombre": valores[1],
            "RUT Número": valores[2].split('-')[0],
            "RUT DV": valores[2].split('-')[1],
            "PIN": "",
            "Rol": valores[3],
            "Estado": valores[4],
        }

        ctk.CTkLabel(ventana, text=f"Huella ID (no editable) = {hid_original}").grid(
            row=0, column=0, columnspan=2, padx=10, pady=5
        )

        for i, label in enumerate(orden, start=1):
            if label == "RUT":
                ctk.CTkLabel(ventana, text=label).grid(row=i, column=0, padx=10, pady=5)
                frame_rut = ctk.CTkFrame(ventana)
                frame_rut.grid(row=i, column=1, padx=10, pady=5)
                campos["RUT Número"] = ctk.CTkEntry(frame_rut, width=100)
                campos["RUT Número"].pack(side="left")
                ctk.CTkLabel(frame_rut, text=" - ").pack(side="left")
                campos["RUT DV"] = ctk.CTkEntry(frame_rut, width=30)
                campos["RUT DV"].pack(side="left")
                campos["RUT Número"].insert(0, datos["RUT Número"])
                campos["RUT DV"].insert(0, datos["RUT DV"])
            else:
                ctk.CTkLabel(ventana, text=label).grid(row=i, column=0, padx=10, pady=5)
                if label in ["Rol", "Estado"]:
                    opciones = ["admin", "empleado"] if label == "Rol" else ["activo", "inactivo"]
                    campos[label] = ctk.CTkComboBox(ventana, values=opciones)
                    campos[label].set(datos[label])
                else:
                    campos[label] = ctk.CTkEntry(ventana)
                    campos[label].insert(0, datos[label])
                campos[label].grid(row=i, column=1, padx=10, pady=5)

        def guardar():
            try:
                nombre = campos["Nombre"].get().strip()
                rut_num = campos["RUT Número"].get().strip()
                rut_dv = campos["RUT DV"].get().strip().lower()
                if not validar_rut_partes(rut_num, rut_dv):
                    raise ValueError("RUT inválido")
                rut = f"{rut_num}-{rut_dv}"
                pin = campos["PIN"].get().strip()
                if pin and not validar_pin(pin):
                    raise ValueError("PIN inválido")
                rol = campos["Rol"].get()
                estado = campos["Estado"].get()
                query = "UPDATE usuarios SET nombre=%s, rut=%s, rol=%s, estado=%s"
                valores = [nombre, rut, rol, estado]
                if pin:
                    query += ", pin=%s"
                    valores.append(pin)
                query += " WHERE huella_id=%s"
                valores.append(hid_original)
                self.cursor.execute(query, tuple(valores))
                self.conn.commit()
                registrar_log(f"Editado usuario ID: {hid_original}")
                messagebox.showinfo("Éxito", "Usuario actualizado")
                ventana.destroy()
                self.actualizar_treeview()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(ventana, text="Guardar", command=guardar).grid(
            row=len(orden) + 1, column=0, columnspan=2, pady=10
        )

    def salir(self):
        self.cursor.close()
        self.conn.close()
        self.destroy()
        if self.volver_al_menu:
            self.volver_al_menu()


def ejecutar_gestionar(volver_al_menu):
    app = App(volver_al_menu)
    app.mainloop()

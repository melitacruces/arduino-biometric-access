"""Ventana de autenticación de administrador.

Valida el acceso a la sección "Gestionar" de dos formas:
    1. Credenciales maestras definidas en el archivo .env (ADMIN_USER / ADMIN_PIN).
    2. Un administrador activo registrado en la base de datos MySQL.
"""

import os
from tkinter import messagebox

import customtkinter as ctk
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def verificar_maestro(usuario, pin):
    """Comprueba las credenciales maestras cargadas desde el .env."""
    return (
        usuario == os.getenv("ADMIN_USER") and
        pin == os.getenv("ADMIN_PIN")
    )


class LoginVentana(ctk.CTkToplevel):
    def __init__(self, on_login_exitoso):
        super().__init__()
        self.title("Autenticación de Administrador")
        self.geometry("450x400")
        self.resizable(False, False)
        self.on_login_exitoso = on_login_exitoso

        self.frame = ctk.CTkFrame(self, corner_radius=15)
        self.frame.pack(expand=True, fill="both", padx=30, pady=30)

        ctk.CTkLabel(
            self.frame, text="Inicio de Sesión", font=("Arial", 20, "bold")
        ).pack(pady=(15, 25))

        ctk.CTkLabel(self.frame, text="👤 Usuario:", font=("Arial", 14)).pack(pady=(5, 2))
        self.entry_user = ctk.CTkEntry(self.frame, width=250)
        self.entry_user.pack(pady=5)

        ctk.CTkLabel(self.frame, text="🔑 PIN:", font=("Arial", 14)).pack(pady=(10, 2))
        self.entry_pass = ctk.CTkEntry(self.frame, show="*", width=250)
        self.entry_pass.pack(pady=5)

        self.label_estado = ctk.CTkLabel(self.frame, text="", font=("Arial", 13))
        self.label_estado.pack(pady=(10, 5))

        self.boton_ingresar = ctk.CTkButton(
            self.frame,
            text="🔐 Ingresar",
            font=("Arial", 15),
            height=40,
            width=150,
            command=self.validar_credenciales,
        )
        self.boton_ingresar.pack(pady=(5, 5))

    def validar_credenciales(self):
        usuario = self.entry_user.get().strip()
        pin = self.entry_pass.get().strip()

        # 1) Credenciales maestras (.env)
        if verificar_maestro(usuario, pin):
            self.label_estado.configure(text="✅ Acceso maestro permitido", text_color="green")
            self.after(500, lambda: self.abrir_gestionar("Administrador"))
            return

        # 2) Administrador activo en la base de datos
        try:
            db = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="proyecto_huella",
            )
            cursor = db.cursor()
            cursor.execute(
                "SELECT nombre FROM usuarios "
                "WHERE rut = %s AND pin = %s AND rol = 'admin' AND estado = 'activo'",
                (usuario, pin),
            )
            result = cursor.fetchone()
            if result:
                nombre = result[0]
                self.label_estado.configure(text=f"✅ Bienvenido {nombre}", text_color="green")
                self.after(500, lambda: self.abrir_gestionar(nombre))
            else:
                self.label_estado.configure(text="❌ Acceso denegado", text_color="red")
        except Exception as e:
            self.label_estado.configure(text=f"⚠️ Error: {e}", text_color="orange")

    def abrir_gestionar(self, nombre):
        self.destroy()
        self.on_login_exitoso(nombre)

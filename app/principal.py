"""Menú principal de la aplicación.

Punto de entrada de la interfaz gráfica. Ofrece dos accesos:
    - Ingresar:  verificación de acceso por huella + PIN.
    - Gestionar: administración de usuarios (requiere login de administrador).
"""

from tkinter import messagebox

import customtkinter as ctk

from ingresar import InterfazIngreso
from login import LoginVentana
from gestionar import ejecutar_gestionar


class MenuPrincipal(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Menú Principal")
        self.geometry("500x400")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.usuario = None  # Se llenará si accede a gestionar

        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.pack(expand=True, fill="both", padx=40, pady=40)

        self.titulo = ctk.CTkLabel(
            self.main_frame,
            text="Proyecto Huella",
            font=("Arial", 24, "bold"),
        )
        self.titulo.pack(pady=(20, 40))

        self.boton_ingresar = ctk.CTkButton(
            self.main_frame,
            text="🔐 Ingresar",
            font=("Arial", 18),
            height=50,
            width=200,
            command=self.abrir_ingresar,
        )
        self.boton_ingresar.pack(pady=20)

        self.boton_gestionar = ctk.CTkButton(
            self.main_frame,
            text="⚙️ Gestionar",
            font=("Arial", 15),
            height=40,
            width=150,
            command=self.validar_gestionar,
        )
        self.boton_gestionar.pack(pady=(40, 10))

    def abrir_ingresar(self):
        self.withdraw()
        ingreso = InterfazIngreso(volver_al_menu=self.deiconify)
        ingreso.mainloop()

    def validar_gestionar(self):
        def on_login_ok(nombre):
            self.usuario = nombre
            ctk.CTkToplevel(self).withdraw()
            self.withdraw()
            messagebox.showinfo("Acceso", f"Bienvenido {nombre}")
            ejecutar_gestionar(self.deiconify)

        login = LoginVentana(on_login_exitoso=on_login_ok)
        login.grab_set()


if __name__ == "__main__":
    app = MenuPrincipal()
    app.mainloop()

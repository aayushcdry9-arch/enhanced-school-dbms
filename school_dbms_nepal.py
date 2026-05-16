import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import hashlib
import csv
from datetime import datetime

# PDF Generation
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.units import inch

# Charts
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ============================================
# SCHOOL CUSTOMIZATION (TRIYUGA, NEPAL)
# ============================================

SCHOOL_NAME = "Triyuga Secondary School"
SCHOOL_ADDRESS = "Triyuga, Koshi Province, Nepal"
SCHOOL_PHONE = "+977-1-4567890"
SCHOOL_EMAIL = "info@triyugaschool.edu.np"
ACADEMIC_YEAR = "2082/2083 (2025/2026)"

PRIMARY_COLOR = "#DC143C"     # Red
SECONDARY_COLOR = "#003893"   # Blue
ACCENT_COLOR = "#FFD700"      # Gold
SUCCESS_COLOR = "#008000"     # Green

# ============================================
# LOGIN WINDOW
# ============================================

class LoginWindow:
    def __init__(self, root, database=None):
        self.root = root
        self.db = database
        self.root.title(f"🔐 {SCHOOL_NAME} - Login")
        self.root.geometry("450x420")
        self.root.resizable(False, False)

        self.create_login_ui()

    def create_login_ui(self):
        # Header with school name
        title_frame = tk.Frame(self.root, bg=PRIMARY_COLOR, height=120)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        tk.Label(
            title_frame,
            text=f"🏫 {SCHOOL_NAME}",
            font=("Arial", 18, "bold"),
            bg=PRIMARY_COLOR,
            fg="white"
        ).pack(pady=5)

        tk.Label(
            title_frame,
            text=SCHOOL_ADDRESS,
            font=("Arial", 11),
            bg=PRIMARY_COLOR,
            fg="white"
        ).pack(pady=2)

        # Body frame for login form
        body = tk.Frame(self.root, padx=20, pady=20)
        body.pack(fill=tk.BOTH, expand=True)

        tk.Label(body, text="Username:", font=("Arial", 11)).grid(row=0, column=0, sticky="w", pady=5)
        self.username_entry = tk.Entry(body, font=("Arial", 11))
        self.username_entry.grid(row=0, column=1, pady=5)

        tk.Label(body, text="Password:", font=("Arial", 11)).grid(row=1, column=0, sticky="w", pady=5)
        self.password_entry = tk.Entry(body, font=("Arial", 11), show="*")
        self.password_entry.grid(row=1, column=1, pady=5)

        login_btn = tk.Button(
            body,
            text="Login",
            font=("Arial", 11, "bold"),
            bg=SECONDARY_COLOR,
            fg="white",
            command=self.login
        )
        login_btn.grid(row=2, column=0, columnspan=2, pady=15)

        # Center the grid columns
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        # For now, simple dummy check – replace with DB lookup
        if username == "admin" and password == "admin123":
            messagebox.showinfo("Login", "Login successful!")
            # Here you can open the main dashboard window
        else:
            messagebox.showerror("Login", "Invalid username or password.")


if __name__ == "__main__":
    root = tk.Tk()
    app = LoginWindow(root, database=None)
    root.mainloop()
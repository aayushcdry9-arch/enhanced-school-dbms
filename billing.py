# ============================================
# 🧾 One‑File Billing Window for School DBMS
# Connects directly to school_dbms.db
# ============================================

import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import hashlib
from datetime import datetime
import re


PRIMARY_COLOR = "#DC143C"
SECONDARY_COLOR = "#003893"
SUCCESS_COLOR = "#008000"
WARNING_COLOR = "#FF9800"
NEUTRAL_COLOR = "#2196F3"


# ---------------------------- Billing DB Logic ----------------------------


def init_billing_tables(db_path="school_dbms.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fee structure (tuition, bus, lab, other per class)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fee_structure (
            class_name TEXT PRIMARY KEY,
            tuition REAL NOT NULL,
            bus REAL NOT NULL,
            lab REAL NOT NULL,
            other REAL NOT NULL
        )
    """)

    # Invoices per student per month/year
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            class_name TEXT NOT NULL,
            month TEXT NOT NULL,
            year INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            paid_amount REAL DEFAULT 0,
            due_amount REAL DEFAULT 0,
            due_date TEXT,
            status TEXT DEFAULT 'Unpaid',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Payments for each invoice
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            method TEXT NOT NULL,
            transaction_ref TEXT,
            payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id)
        )
    """)

    conn.commit()
    conn.close()


def set_fee_structure(db_path, class_name, tuition, bus, lab, other):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO fee_structure
        (class_name, tuition, bus, lab, other)
        VALUES (?, ?, ?, ?, ?)
    """, (class_name, tuition, bus, lab, other))
    conn.commit()
    conn.close()


def get_fee_structure(db_path, class_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT tuition, bus, lab, other FROM fee_structure WHERE class_name = ?",
                   (class_name,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "tuition": row[0],
            "bus": row[1],
            "lab": row[2],
            "other": row[3]
        }
    return None


def calculate_total_fees(db_path, class_name):
    fees = get_fee_structure(db_path, class_name)
    if fees:
        return sum(fees.values())
    return 0.0


def generate_invoice(db_path, student_id, class_name, month, year, due_date=None):
    total = calculate_total_fees(db_path, class_name)
    if total <= 0:
        raise ValueError("Fee structure not found or total is zero.")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO invoices (
            student_id, class_name, month, year, total_amount, due_amount, due_date, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (student_id, class_name, month, year, total, total, due_date, "Unpaid"))
    invoice_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return invoice_id


def get_invoice(db_path, invoice_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, student_id, class_name, month, year, total_amount, paid_amount, due_amount, status
        FROM invoices WHERE id = ?
    """, (invoice_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "student_id": row[1],
            "class_name": row[2],
            "month": row[3],
            "year": row[4],
            "total_amount": row[5],
            "paid_amount": row[6],
            "due_amount": row[7],
            "status": row[8]
        }
    return None


def record_payment(db_path, invoice_id, amount, method, txn_ref=None):
    if amount <= 0:
        raise ValueError("Amount must be positive.")
    if method not in ["cash", "bank", "online"]:
        raise ValueError("Method must be 'cash', 'bank', or 'online'.")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT total_amount, paid_amount, due_amount FROM invoices WHERE id = ?",
                   (invoice_id,))
    row = cursor.fetchone()
    if not row:
        raise ValueError("Invoice not found.")

    total, paid, due = row
    if amount > due:
        raise ValueError("Payment exceeds due amount.")

    new_paid = paid + amount
    new_due = due - amount
    new_status = "Paid" if new_due <= 0 else "Partially Paid"

    cursor.execute("""
        UPDATE invoices
        SET paid_amount = ?, due_amount = ?, status = ?
        WHERE id = ?
    """, (new_paid, new_due, new_status, invoice_id))

    cursor.execute("""
        INSERT INTO payments (invoice_id, amount, method, transaction_ref)
        VALUES (?, ?, ?, ?)
    """, (invoice_id, amount, method, txn_ref))

    conn.commit()
    conn.close()


def get_payment_history(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT invoice_id, amount, method, payment_date
        FROM payments
        ORDER BY payment_date DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [
        {"invoice_id": row[0], "amount": row[1], "method": row[2], "payment_date": row[3]}
        for row in rows
    ]



# ---------------------------- Validation helpers ----------------------------


def validate_date(date_str):
    if not date_str:
        return True
    pattern = r"^\d{4}-\d{2}-\d{2}$"
    if not re.match(pattern, date_str):
        return False
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def is_name_valid(name):
    return name and name.replace(" ", "").isalpha()



# ---------------------------- Billing GUI Window (Toplevel) ----------------------------


class BillingWindow:
    def __init__(self, parent, db_path="school_dbms.db"):
        self.parent = parent
        self.db_path = db_path
        self.top = tk.Toplevel(parent)
        self.top.title("School Billing System")
        self.top.geometry("550x700")
        self.top.transient(parent)  # stay on top
        self.top.resizable(True, True)

        # Status
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = tk.Label(
            self.top, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W
        )
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=2, pady=2)

        # Tabs
        self.notebook = ttk.Notebook(self.top)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.frame_fee = tk.Frame(self.notebook, padx=10, pady=10)
        self.frame_invoice = tk.Frame(self.notebook, padx=10, pady=10)
        self.frame_payment = tk.Frame(self.notebook, padx=10, pady=10)

        self.notebook.add(self.frame_fee, text="Fee Structure")
        self.notebook.add(self.frame_invoice, text="Generate Invoice")
        self.notebook.add(self.frame_payment, text="Record Payment")

        self.init_fee_frame()
        self.init_invoice_frame()
        self.init_payment_frame()

        # Initialize tables (run once per app, not each time BillingWindow opens)
        try:
            init_billing_tables(db_path)
            self.status_var.set("Billing DB ready (school_dbms.db)")
        except Exception as e:
            messagebox.showerror("DB Error", str(e))


    def set_status(self, msg):
        self.status_var.set(f"{msg} – {datetime.now().strftime('%H:%M:%S')}")


    # ---------------- Fee Structure Tab ----------------

    def init_fee_frame(self):
        frame = self.frame_fee
        frame.columnconfigure(1, weight=1)

        tk.Label(frame, text="Class:").grid(row=0, column=0, sticky="e", pady=5)
        self.class_fee = tk.Entry(frame, width=20)
        self.class_fee.grid(row=0, column=1, pady=5)

        tk.Label(frame, text="Tuition (Rs.):").grid(row=1, column=0, sticky="e", pady=5)
        self.tuition = tk.Entry(frame, width=20)
        self.tuition.grid(row=1, column=1, pady=5)

        tk.Label(frame, text="Bus (Rs.):").grid(row=2, column=0, sticky="e", pady=5)
        self.bus = tk.Entry(frame, width=20)
        self.bus.grid(row=2, column=1, pady=5)

        tk.Label(frame, text="Lab (Rs.):").grid(row=3, column=0, sticky="e", pady=5)
        self.lab = tk.Entry(frame, width=20)
        self.lab.grid(row=3, column=1, pady=5)

        tk.Label(frame, text="Other (Rs.):").grid(row=4, column=0, sticky="e", pady=5)
        self.other = tk.Entry(frame, width=20)
        self.other.grid(row=4, column=1, pady=5)

        tk.Button(frame, text="Save Fee", bg=SUCCESS_COLOR, fg="white",
                  command=self.save_fee, width=20).grid(row=5, column=0, columnspan=2, pady=5)
        tk.Button(frame, text="View Fee", bg=NEUTRAL_COLOR, fg="white",
                  command=self.view_fee, width=20).grid(row=6, column=0, pady=5)
        tk.Button(frame, text="Clear", bg=WARNING_COLOR, fg="white",
                  command=self.clear_fee, width=20).grid(row=6, column=1, pady=5)


    def save_fee(self):
        class_name = self.class_fee.get().strip()
        if not class_name or not is_name_valid(class_name):
            messagebox.showerror("Error", "Class name must be letters only.")
            return

        try:
            tuition = float(self.tuition.get())
            bus = float(self.bus.get() or 0)
            lab = float(self.lab.get() or 0)
            other = float(self.other.get() or 0)
            if any(f < 0 for f in [tuition, bus, lab, other]):
                messagebox.showerror("Error", "Fees cannot be negative.")
                return
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for fees.")
            return

        try:
            set_fee_structure(self.db_path, class_name, tuition, bus, lab, other)
            self.set_status(f"Fee structure saved for {class_name}")
            messagebox.showinfo("Success", f"Fee structure saved for {class_name}")
        except Exception as e:
            messagebox.showerror("Error", str(e))


    def view_fee(self):
        class_name = self.class_fee.get().strip()
        if not class_name:
            messagebox.showerror("Error", "Enter class name.")
            return

        try:
            fees = get_fee_structure(self.db_path, class_name)
            if fees:
                msg = f"Fee for {class_name}:\n"
                msg += f"Tuition: Rs. {fees['tuition']:.2f}\n"
                msg += f"Bus: Rs. {fees['bus']:.2f}\n"
                msg += f"Lab: Rs. {fees['lab']:.2f}\n"
                msg += f"Other: Rs. {fees['other']:.2f}\n"
                msg += f"Total: Rs. {sum(fees.values()):.2f}"
                messagebox.showinfo("Fee", msg)
                self.set_status(f"Viewed fee for {class_name}")
            else:
                messagebox.showinfo("Not Found", f"No fee found for {class_name}")
        except Exception as e:
            messagebox.showerror("Error", str(e))


    def clear_fee(self):
        self.class_fee.delete(0, tk.END)
        self.tuition.delete(0, tk.END)
        self.bus.delete(0, tk.END)
        self.lab.delete(0, tk.END)
        self.other.delete(0, tk.END)
        self.set_status("Fee form cleared")


    # ---------------- Invoice Tab ----------------

    def init_invoice_frame(self):
        frame = self.frame_invoice
        frame.columnconfigure(1, weight=1)

        tk.Label(frame, text="Student ID:").grid(row=0, column=0, sticky="e", pady=5)
        self.student_id_inv = tk.Entry(frame, width=20)
        self.student_id_inv.grid(row=0, column=1, pady=5)

        tk.Label(frame, text="Class:").grid(row=1, column=0, sticky="e", pady=5)
        self.class_inv = tk.Entry(frame, width=20)
        self.class_inv.grid(row=1, column=1, pady=5)

        tk.Label(frame, text="Month:").grid(row=2, column=0, sticky="e", pady=5)
        self.month = tk.Entry(frame, width=20)
        self.month.grid(row=2, column=1, pady=5)

        tk.Label(frame, text="Year:").grid(row=3, column=0, sticky="e", pady=5)
        self.year = tk.Entry(frame, width=20)
        self.year.grid(row=3, column=1, pady=5)

        tk.Label(frame, text="Due Date (YYYY-MM-DD):").grid(row=4, column=0, sticky="e", pady=5)
        self.due_date = tk.Entry(frame, width=20)
        self.due_date.grid(row=4, column=1, pady=5)

        tk.Button(frame, text="Create Invoice", bg=SUCCESS_COLOR, fg="white",
                  command=self.create_invoice, width=20).grid(row=5, column=0, columnspan=2, pady=5)
        tk.Button(frame, text="Clear", bg=WARNING_COLOR, fg="white",
                  command=self.clear_invoice, width=20).grid(row=6, column=0, columnspan=2, pady=5)


    def create_invoice(self):
        try:
            sid = int(self.student_id_inv.get())
        except ValueError:
            messagebox.showerror("Error", "Student ID must be a number.")
            return

        class_name = self.class_inv.get().strip()
        month = self.month.get().strip()
        year_text = self.year.get().strip()
        if not (sid and class_name and month and year_text):
            messagebox.showerror("Error", "Student ID, class, month, and year required.")
            return

        try:
            year = int(year_text)
        except ValueError:
            messagebox.showerror("Error", "Year must be a number.")
            return

        due = self.due_date.get().strip()
        if due and not validate_date(due):
            messagebox.showerror("Error", "Due date must be YYYY-MM-DD.")
            return

        try:
            invoice_id = generate_invoice(self.db_path, sid, class_name, month, year, due)
            self.set_status(f"Invoice {invoice_id} created for Student {sid}")
            messagebox.showinfo("Success", f"Invoice created. ID: {invoice_id}")
        except Exception as e:
            messagebox.showerror("Error", str(e))


    def clear_invoice(self):
        self.student_id_inv.delete(0, tk.END)
        self.class_inv.delete(0, tk.END)
        self.month.delete(0, tk.END)
        self.year.delete(0, tk.END)
        self.due_date.delete(0, tk.END)
        self.set_status("Invoice form cleared")


    # ---------------- Payment Tab ----------------

    def init_payment_frame(self):
        frame = self.frame_payment
        frame.columnconfigure(1, weight=1)

        tk.Label(frame, text="Invoice ID:").grid(row=0, column=0, sticky="e", pady=5)
        self.invoice_id_pay = tk.Entry(frame, width=20)
        self.invoice_id_pay.grid(row=0, column=1, pady=5)

        tk.Label(frame, text="Amount (Rs.):").grid(row=1, column=0, sticky="e", pady=5)
        self.amount = tk.Entry(frame, width=20)
        self.amount.grid(row=1, column=1, pady=5)

        tk.Label(frame, text="Method (cash/bank/online):").grid(row=2, column=0, sticky="e", pady=5)
        self.method = tk.Entry(frame, width=20)
        self.method.insert(0, "cash")
        self.method.grid(row=2, column=1, pady=5)

        tk.Label(frame, text="Transaction Ref:").grid(row=3, column=0, sticky="e", pady=5)
        self.txn = tk.Entry(frame, width=20)
        self.txn.grid(row=3, column=1, pady=5)

        tk.Button(frame, text="View Invoice", bg=NEUTRAL_COLOR, fg="white",
                  command=self.view_invoice, width=20).grid(row=4, column=0, pady=5)
        tk.Button(frame, text="Record Payment", bg=SUCCESS_COLOR, fg="white",
                  command=self.record_payment_action, width=20).grid(row=4, column=1, pady=5)

        tk.Button(frame, text="History (Last 10)", bg=WARNING_COLOR, fg="white",
                  command=self.show_history, width=20).grid(row=5, column=0, columnspan=2, pady=5)
        tk.Button(frame, text="Clear", bg="#f44336", fg="white",
                  command=self.clear_payment, width=20).grid(row=6, column=0, columnspan=2, pady=5)


    def view_invoice(self):
        try:
            inv_id = int(self.invoice_id_pay.get())
        except ValueError:
            messagebox.showerror("Error", "Invoice ID must be a number.")
            return

        try:
            inv = get_invoice(self.db_path, inv_id)
            if inv:
                msg = f"Invoice {inv['id']}:\n"
                msg += f"Student ID: {inv['student_id']}\n"
                msg += f"Class: {inv['class_name']}\n"
                msg += f"{inv['month']}/{inv['year']}\n"
                msg += f"Total: Rs. {inv['total_amount']:.2f}\n"
                msg += f"Paid: Rs. {inv['paid_amount']:.2f}\n"
                msg += f"Due: Rs. {inv['due_amount']:.2f}\n"
                msg += f"Status: {inv['status']}"
                messagebox.showinfo("Invoice", msg)
                self.set_status(f"Viewed invoice {inv_id}")
            else:
                messagebox.showinfo("Not Found", "Invoice not found.")
        except Exception as e:
            messagebox.showerror("Error", str(e))


    def record_payment_action(self):
        try:
            inv_id = int(self.invoice_id_pay.get())
            amount = float(self.amount.get())
        except ValueError:
            messagebox.showerror("Error", "Invoice ID and amount must be numbers.")
            return

        if amount <= 0:
            messagebox.showerror("Error", "Amount must be positive.")
            return

        method = self.method.get().strip().lower()
        if method not in ["cash", "bank", "online"]:
            messagebox.showerror("Error", "Method must be cash, bank, or online.")
            return

        txn = self.txn.get().strip() or None

        try:
            record_payment(self.db_path, inv_id, amount, method, txn)
            self.set_status(f"Payment of Rs. {amount:.2f} recorded for invoice {inv_id}")
            messagebox.showinfo("Success", f"Payment recorded for invoice {inv_id}")
        except Exception as e:
            messagebox.showerror("Error", str(e))


    def show_history(self):
        try:
            history = get_payment_history(self.db_path)
            if history:
                msg = "Payment History (Last 10):\n"
                msg += "-" * 50 + "\n"
                for item in history[:10]:
                    msg += f"Inv {item['invoice_id']} | Rs. {item['amount']:.2f} | "
                    msg += f"{item['method']} | {item['payment_date']}\n"
                messagebox.showinfo("History", msg)
                self.set_status("Payment history shown")
            else:
                messagebox.showinfo("Empty", "No payment history.")
        except Exception as e:
            messagebox.showerror("Error", str(e))


    def clear_payment(self):
        self.invoice_id_pay.delete(0, tk.END)
        self.amount.delete(0, tk.END)
        self.method.delete(0, tk.END)
        self.method.insert(0, "cash")
        self.txn.delete(0, tk.END)
        self.set_status("Payment form cleared")


# =====================================================================
# Now inside your school_dbms.py → in MainApplication
# =====================================================================

# In MainApplication class, add:
#
#   def open_billing(self):
#       BillingWindow(self.root, db_path="school_dbms.db")
#
# and in buttons:
#
#   ("💰 Billing", self.open_billing, WARNING_COLOR)
# =====================================================================
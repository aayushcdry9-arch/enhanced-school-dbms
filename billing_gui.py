# billing_gui.py - Enhanced Scrollable GUI for School Billing

import tkinter as tk
from tkinter import messagebox, ttk
import re
from datetime import datetime
import billing

# -------------------- Configuration --------------------
COLORS = {
    'primary': '#4CAF50',
    'primary_dark': '#43A047',
    'secondary': '#2196F3',
    'accent': '#FF9800',
    'danger': '#f44336',
    'success': '#4CAF50',
    'warning': '#FF9800',
    'bg_light': '#f4f6fb',
    'text_dark': '#333',
    'text_gray': '#777'
}

FONT_HEADINGS = ("Segoe UI", 11, "bold")
FONT_LABELS = ("Segoe UI", 10)
FONT_BUTTONS = ("Segoe UI", 9, "bold")

# -------------------- Helper functions --------------------

def validate_date(date_str):
    """Validate YYYY-MM-DD format"""
    if not date_str:
        return True
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    if not re.match(pattern, date_str):
        return False
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def validate_positive_number(value, field_name=""):
    """Validate that value is a positive number"""
    try:
        num = float(value)
        return num >= 0, num
    except (ValueError, TypeError):
        return False, None

def init_db():
    try:
        billing.init_billing_tables()
        return True, "Database initialized successfully"
    except Exception as e:
        return False, f"Failed to initialize database: {str(e)}"

# -------------------- Fee structure functions --------------------

def save_fee_structure():
    class_name = entry_class.get().strip()

    if not class_name:
        messagebox.showerror("Validation Error", "Class name is required.")
        entry_class.focus()
        return

    if not class_name.replace(" ", "").isalpha():
        messagebox.showerror("Validation Error", "Class name must contain only letters and spaces.")
        entry_class.focus()
        return

    fields = [
        ('Tuition', entry_tuition),
        ('Bus', entry_bus),
        ('Lab', entry_lab),
        ('Other', entry_other)
    ]

    fees = {}
    for name, entry_widget in fields:
        valid, value = validate_positive_number(entry_widget.get(), name)
        if not valid:
            messagebox.showerror("Validation Error", f"Please enter a valid number for {name} Fee.")
            entry_widget.focus()
            return
        fees[name.lower()] = value

    try:
        billing.set_fee_structure(class_name, fees['tuition'], fees['bus'], fees['lab'], fees['other'])
        messagebox.showinfo("Success", f"✓ Fee structure saved for {class_name}")
        status_var.set(f"Fee structure saved for {class_name} at {datetime.now().strftime('%H:%M:%S')}")
        clear_fee()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save fee structure: {str(e)}")

def view_fee_structure():
    class_name = entry_class.get().strip()
    if not class_name:
        messagebox.showerror("Error", "Enter class name to view fee structure.")
        entry_class.focus()
        return

    try:
        fees = billing.get_fee_structure(class_name)
        if fees:
            message = f"📋 Fee Structure for {class_name}:\n\n"
            message += f"Tuition Fee: Rs. {fees['tuition']:.2f}\n"
            message += f"Bus Fee: Rs. {fees['bus']:.2f}\n"
            message += f"Lab Fee: Rs. {fees['lab']:.2f}\n"
            message += f"Other Fee: Rs. {fees['other']:.2f}\n"
            message += f"{'─' * 30}\n"
            message += f"TOTAL: Rs. {sum(fees.values()):.2f}"
            messagebox.showinfo("Fee Structure Details", message)
            status_var.set(f"Viewed fee structure for {class_name}")
        else:
            messagebox.showinfo("Not Found", f"No fee structure found for {class_name}. Please save it first.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# -------------------- Invoice preview & creation --------------------

def preview_invoice():
    class_name = entry_class_invoice.get().strip()
    month = entry_month.get().strip()
    year_text = entry_year.get().strip()
    student_text = entry_student_id.get().strip()

    if not all([class_name, month, year_text, student_text]):
        messagebox.showerror("Validation Error", "Student ID, class, month, and year are required.")
        return

    try:
        student_id = int(student_text)
        if student_id <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Validation Error", "Student ID must be a positive number.")
        entry_student_id.focus()
        return

    try:
        year = int(year_text)
        if year < 2000 or year > 2100:
            raise ValueError
    except ValueError:
        messagebox.showerror("Validation Error", "Year must be a valid number (2000-2100).")
        entry_year.focus()
        return

    try:
        total = billing.calculate_total_fees(class_name)
        fees = billing.get_fee_structure(class_name)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to calculate fees: {str(e)}")
        return

    preview = tk.Toplevel(root)
    preview.title("Invoice Preview")
    preview.geometry("450x380")
    preview.resizable(False, False)
    preview.configure(bg=COLORS['bg_light'])
    preview.transient(root)
    preview.grab_set()

    card = tk.Frame(preview, bg="white", bd=0, relief="flat", padx=20, pady=15)
    card.pack(fill="both", expand=True, padx=20, pady=15)

    header = tk.Frame(card, bg=COLORS['primary'], height=40)
    header.pack(fill="x")
    header.pack_propagate(False)
    tk.Label(
        header,
        text="🏫 School Invoice Preview",
        bg=COLORS['primary'],
        fg="white",
        font=("Segoe UI", 12, "bold"),
    ).pack(side="left", padx=10, pady=8)

    body = tk.Frame(card, bg="white")
    body.pack(fill="both", expand=True, pady=(15, 5))

    info_frame = tk.Frame(body, bg="white")
    info_frame.pack(fill="x", pady=(0, 10))

    tk.Label(info_frame, text=f"Student ID: {student_id}", bg="white",
             fg=COLORS['text_dark'], font=FONT_LABELS, anchor="w").pack(fill="x", pady=2)
    tk.Label(info_frame, text=f"Class: {class_name}", bg="white",
             fg=COLORS['text_gray'], font=FONT_LABELS, anchor="w").pack(fill="x", pady=2)
    tk.Label(info_frame, text=f"Month/Year: {month} {year}", bg="white",
             fg=COLORS['text_gray'], font=FONT_LABELS, anchor="w").pack(fill="x", pady=2)

    tk.Frame(body, bg="#e0e0e0", height=2).pack(fill="x", pady=(10, 10))

    if fees:
        tk.Label(body, text="💰 Fee Breakdown", bg="white",
                 fg=COLORS['text_dark'], font=FONT_HEADINGS, anchor="w").pack(fill="x", pady=(0, 8))

        breakdown_frame = tk.Frame(body, bg="white")
        breakdown_frame.pack(fill="x")

        for i, (label, amount) in enumerate([
            ("Tuition Fee", fees["tuition"]),
            ("Bus Fee", fees["bus"]),
            ("Lab Fee", fees["lab"]),
            ("Other Fee", fees["other"])
        ]):
            row = i + 1
            tk.Label(breakdown_frame, text=label, bg="white",
                     fg=COLORS['text_gray'], font=FONT_LABELS, anchor="w").grid(row=row, column=0, sticky="w", pady=2)
            tk.Label(breakdown_frame, text=f"Rs. {amount:.2f}", bg="white",
                     fg=COLORS['text_dark'], font=FONT_LABELS, anchor="e").grid(row=row, column=1, sticky="e", padx=(20, 0))

        tk.Frame(body, bg="#e0e0e0", height=2).pack(fill="x", pady=(10, 10))

    total_frame = tk.Frame(body, bg="white")
    total_frame.pack(fill="x")

    tk.Label(total_frame, text="💵 Total Payable", bg="white",
             fg=COLORS['text_dark'], font=("Segoe UI", 12, "bold"), anchor="w").pack(side="left")
    tk.Label(total_frame, text=f"Rs. {total:.2f}", bg="white",
             fg=COLORS['primary'], font=("Segoe UI", 14, "bold"), anchor="e").pack(side="right")

    footer = tk.Frame(card, bg="white")
    footer.pack(fill="x", pady=(15, 0))

    def confirm_and_create():
        preview.destroy()
        create_invoice()

    btn_cancel = tk.Button(
        footer, text="❌ Cancel",
        command=preview.destroy,
        bg="#f5f5f5", fg="#555",
        activebackground="#e0e0e0",
        relief="flat",
        font=FONT_BUTTONS,
        padx=15, pady=8
    )
    btn_cancel.pack(side="right", padx=5)

    btn_confirm = tk.Button(
        footer,
        text=f"✅ Create Invoice (Rs. {total:.2f})",
        command=confirm_and_create,
        bg=COLORS['primary'], fg="white",
        activebackground=COLORS['primary_dark'],
        relief="flat",
        font=FONT_BUTTONS,
        padx=15, pady=8
    )
    btn_confirm.pack(side="right", padx=5)

    status_var.set(f"Previewed invoice for Student {student_id}")

def create_invoice():
    try:
        student_id = int(entry_student_id.get())
        if student_id <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Validation Error", "Student ID must be a positive number.")
        return

    class_name = entry_class_invoice.get().strip()
    month = entry_month.get().strip()
    year_text = entry_year.get().strip()
    due_date = entry_due_date.get().strip() or None

    if not all([class_name, month, year_text]):
        messagebox.showerror("Validation Error", "Class, month, and year are required.")
        return

    if due_date and not validate_date(due_date):
        messagebox.showerror("Validation Error", "Due date must be in YYYY-MM-DD format.")
        entry_due_date.focus()
        return

    try:
        year = int(year_text)
    except ValueError:
        messagebox.showerror("Validation Error", "Year must be a number.")
        return

    try:
        invoice_id = billing.generate_invoice(
            student_id=student_id,
            class_name=class_name,
            month=month,
            year=year,
            due_date=due_date
        )
        messagebox.showinfo("✓ Success", f"Invoice created successfully!\nInvoice ID: {invoice_id}")
        entry_invoice_id_payment.delete(0, tk.END)
        entry_invoice_id_payment.insert(0, str(invoice_id))
        status_var.set(f"Invoice {invoice_id} created for Student {student_id} at {datetime.now().strftime('%H:%M:%S')}")
        clear_invoice()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to create invoice: {str(e)}")

# -------------------- Invoice view, payment, history --------------------

def view_invoice():
    try:
        invoice_id = int(entry_invoice_id_payment.get())
        if invoice_id <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Validation Error", "Enter a valid Invoice ID.")
        entry_invoice_id_payment.focus()
        return

    try:
        invoice = billing.get_invoice(invoice_id)
        if invoice:
            message = f"📄 Invoice Details\n{'═' * 40}\n"
            message += f"Invoice ID: {invoice['id']}\n"
            message += f"Student ID: {invoice['student_id']}\n"
            message += f"Class: {invoice['class_name']}\n"
            message += f"Month/Year: {invoice['month']}/{invoice['year']}\n"
            message += f"{'─' * 40}\n"
            message += f"Total Amount: Rs. {invoice['total_amount']:.2f}\n"
            message += f"Paid Amount: Rs. {invoice['paid_amount']:.2f}\n"
            message += f"Due Amount: Rs. {invoice['due_amount']:.2f}\n"
            message += f"Status: {invoice['status'].upper()}\n"
            if invoice.get('due_date'):
                message += f"Due Date: {invoice['due_date']}"
            messagebox.showinfo(f"Invoice #{invoice_id}", message)
            status_var.set(f"Viewed invoice {invoice_id}")
        else:
            messagebox.showinfo("Not Found", f"Invoice #{invoice_id} not found.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def make_payment():
    try:
        invoice_id = int(entry_invoice_id_payment.get())
        if invoice_id <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Validation Error", "Enter a valid Invoice ID.")
        entry_invoice_id_payment.focus()
        return

    try:
        amount = float(entry_amount.get())
        if amount <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Validation Error", "Enter a valid positive amount.")
        entry_amount.focus()
        return

    method = entry_method.get().strip().lower() or "cash"
    if method not in ["cash", "bank", "online"]:
        messagebox.showerror("Validation Error", "Method must be cash, bank, or online.")
        entry_method.focus()
        return

    txn = entry_txn.get().strip() or None

    try:
        billing.record_payment(invoice_id, amount, method, txn)
        messagebox.showinfo("✓ Payment Recorded", f"Payment of Rs. {amount:.2f} recorded successfully for Invoice #{invoice_id}")
        status_var.set(f"Payment of Rs. {amount} recorded for invoice {invoice_id} at {datetime.now().strftime('%H:%M:%S')}")
        clear_payment()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to record payment: {str(e)}")

def show_payment_history():
    try:
        history = billing.get_payment_history()
        if history:
            report = "📊 Payment History (Last 10)\n"
            report += "═" * 60 + "\n"
            for payment in history[-10:][::-1]:
                report += f"ID:{payment['invoice_id']} | Rs.{payment['amount']:.2f} | {payment['method']:.6} | {payment['payment_date']}\n"
            report += "═" * 60
            messagebox.showinfo("Payment History", report)
            status_var.set("Viewed payment history")
        else:
            messagebox.showinfo("No Data", "No payment history found.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# -------------------- Clear helpers --------------------

def clear_fee():
    entry_class.delete(0, tk.END)
    entry_tuition.delete(0, tk.END)
    entry_bus.delete(0, tk.END)
    entry_lab.delete(0, tk.END)
    entry_other.delete(0, tk.END)
    entry_class.focus()
    status_var.set("Fee structure form cleared")

def clear_invoice():
    entry_student_id.delete(0, tk.END)
    entry_class_invoice.delete(0, tk.END)
    entry_month.delete(0, tk.END)
    entry_year.delete(0, tk.END)
    entry_due_date.delete(0, tk.END)
    entry_student_id.focus()
    status_var.set("Invoice form cleared")

def clear_payment():
    entry_invoice_id_payment.delete(0, tk.END)
    entry_amount.delete(0, tk.END)
    entry_method.delete(0, tk.END)
    entry_method.set("cash")
    entry_txn.delete(0, tk.END)
    entry_invoice_id_payment.focus()
    status_var.set("Payment form cleared")

# -------------------- Scrollable Canvas Helper --------------------

def create_scrollable_frame(parent):
    """Create a scrollable frame with scrollbar"""
    container = tk.Frame(parent, bg=COLORS['bg_light'])
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container, bg=COLORS['bg_light'], highlightthickness=0)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    scrollable_frame = tk.Frame(canvas, bg=COLORS['bg_light'])
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    # Bind mousewheel to scroll
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    # Update scroll region when frame size changes
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    return container, canvas, scrollable_frame

# -------------------- GUI setup --------------------

db_success, db_message = init_db()
if not db_success:
    messagebox.showerror("Database Error", db_message)
    raise SystemExit

root = tk.Tk()
root.title("🏫 School Billing System")
root.geometry("520x700")
root.configure(bg=COLORS['bg_light'])

# Create scrollable frame
container, canvas, scrollable_frame = create_scrollable_frame(root)

# Status bar at bottom (outside scrollable area)
status_var = tk.StringVar()
status_var.set("✓ Ready - Database initialized successfully")
status_bar = tk.Label(
    root, textvariable=status_var,
    bd=1, relief=tk.SUNKEN, anchor=tk.W,
    padx=10, pady=5,
    bg=COLORS['primary'], fg="white",
    font=("Segoe UI", 9)
)
status_bar.pack(side="bottom", fill="x", padx=5, pady=(0, 5))

def create_styled_frame(parent, title):
    frame = tk.LabelFrame(
        parent, text=title,
        padx=15, pady=15,
        font=FONT_HEADINGS,
        bg="white", fg=COLORS['text_dark'],
        relief="flat", bd=2
    )
    frame.columnconfigure(1, weight=1)
    return frame

# Fee structure frame
frame_fee = create_styled_frame(scrollable_frame, "💰 Fee Structure")
frame_fee.pack(fill="x", padx=15, pady=10)

tk.Label(frame_fee, text="Class Name:", font=FONT_LABELS, bg="white", anchor="e").grid(row=0, column=0, sticky="e", pady=5)
entry_class = tk.Entry(frame_fee, width=25, font=FONT_LABELS)
entry_class.grid(row=0, column=1, padx=5, pady=5, sticky="we")

tk.Label(frame_fee, text="Tuition Fee (Rs.):", font=FONT_LABELS, bg="white", anchor="e").grid(row=1, column=0, sticky="e", pady=5)
entry_tuition = tk.Entry(frame_fee, width=25, font=FONT_LABELS)
entry_tuition.grid(row=1, column=1, padx=5, pady=5, sticky="we")

tk.Label(frame_fee, text="Bus Fee (Rs.):", font=FONT_LABELS, bg="white", anchor="e").grid(row=2, column=0, sticky="e", pady=5)
entry_bus = tk.Entry(frame_fee, width=25, font=FONT_LABELS)
entry_bus.grid(row=2, column=1, padx=5, pady=5, sticky="we")

tk.Label(frame_fee, text="Lab Fee (Rs.):", font=FONT_LABELS, bg="white", anchor="e").grid(row=3, column=0, sticky="e", pady=5)
entry_lab = tk.Entry(frame_fee, width=25, font=FONT_LABELS)
entry_lab.grid(row=3, column=1, padx=5, pady=5, sticky="we")

tk.Label(frame_fee, text="Other Fee (Rs.):", font=FONT_LABELS, bg="white", anchor="e").grid(row=4, column=0, sticky="e", pady=5)
entry_other = tk.Entry(frame_fee, width=25, font=FONT_LABELS)
entry_other.grid(row=4, column=1, padx=5, pady=5, sticky="we")

btn_save_fee = tk.Button(
    frame_fee, text="💾 Save Fee Structure", command=save_fee_structure,
    bg=COLORS['primary'], fg="white",
    activebackground=COLORS['primary_dark'],
    relief="flat", font=FONT_BUTTONS, padx=15, pady=8
)
btn_save_fee.grid(row=5, column=0, columnspan=2, pady=10, sticky="we")

btn_view_fee = tk.Button(
    frame_fee, text="👁️ View Fee", command=view_fee_structure,
    bg=COLORS['secondary'], fg="white",
    activebackground="#1976D2",
    relief="flat", font=FONT_BUTTONS, padx=10, pady=6
)
btn_view_fee.grid(row=6, column=0, pady=5, sticky="we")

btn_clear_fee = tk.Button(
    frame_fee, text="🗑️ Clear", command=clear_fee,
    bg=COLORS['danger'], fg="white",
    activebackground="#d32f2f",
    relief="flat", font=FONT_BUTTONS, padx=10, pady=6
)
btn_clear_fee.grid(row=6, column=1, pady=5, sticky="we")

# Invoice frame
frame_invoice = create_styled_frame(scrollable_frame, "📄 Generate Invoice")
frame_invoice.pack(fill="x", padx=15, pady=10)

tk.Label(frame_invoice, text="Student ID:", font=FONT_LABELS, bg="white", anchor="e").grid(row=0, column=0, sticky="e", pady=5)
entry_student_id = tk.Entry(frame_invoice, width=25, font=FONT_LABELS)
entry_student_id.grid(row=0, column=1, padx=5, pady=5, sticky="we")

tk.Label(frame_invoice, text="Class:", font=FONT_LABELS, bg="white", anchor="e").grid(row=1, column=0, sticky="e", pady=5)
entry_class_invoice = tk.Entry(frame_invoice, width=25, font=FONT_LABELS)
entry_class_invoice.grid(row=1, column=1, padx=5, pady=5, sticky="we")

tk.Label(frame_invoice, text="Month:", font=FONT_LABELS, bg="white", anchor="e").grid(row=2, column=0, sticky="e", pady=5)
entry_month = tk.Entry(frame_invoice, width=25, font=FONT_LABELS)
entry_month.grid(row=2, column=1, padx=5, pady=5, sticky="we")

tk.Label(frame_invoice, text="Year:", font=FONT_LABELS, bg="white", anchor="e").grid(row=3, column=0, sticky="e", pady=5)
entry_year = tk.Entry(frame_invoice, width=25, font=FONT_LABELS)
entry_year.grid(row=3, column=1, padx=5, pady=5, sticky="we")

tk.Label(frame_invoice, text="Due Date (YYYY-MM-DD):", font=FONT_LABELS, bg="white", anchor="e").grid(row=4, column=0, sticky="e", pady=5)
entry_due_date = tk.Entry(frame_invoice, width=25, font=FONT_LABELS)
entry_due_date.grid(row=4, column=1, padx=5, pady=5, sticky="we")

btn_preview_inv = tk.Button(
    frame_invoice, text="🔍 Preview Invoice", command=preview_invoice,
    bg=COLORS['accent'], fg="white",
    activebackground="#F57C00",
    relief="flat", font=FONT_BUTTONS, padx=15, pady=8
)
btn_preview_inv.grid(row=5, column=0, columnspan=2, pady=10, sticky="we")

btn_create_invoice = tk.Button(
    frame_invoice, text="✅ Create Invoice", command=create_invoice,
    bg=COLORS['primary'], fg="white",
    activebackground=COLORS['primary_dark'],
    relief="flat", font=FONT_BUTTONS, padx=15, pady=6
)
btn_create_invoice.grid(row=6, column=0, pady=5, sticky="we")

btn_clear_invoice = tk.Button(
    frame_invoice, text="🗑️ Clear", command=clear_invoice,
    bg=COLORS['danger'], fg="white",
    activebackground="#d32f2f",
    relief="flat", font=FONT_BUTTONS, padx=15, pady=6
)
btn_clear_invoice.grid(row=6, column=1, pady=5, sticky="we")

# Payment frame
frame_payment = create_styled_frame(scrollable_frame, "💳 Record Payment")
frame_payment.pack(fill="x", padx=15, pady=10)

tk.Label(frame_payment, text="Invoice ID:", font=FONT_LABELS, bg="white", anchor="e").grid(row=0, column=0, sticky="e", pady=5)
entry_invoice_id_payment = tk.Entry(frame_payment, width=25, font=FONT_LABELS)
entry_invoice_id_payment.grid(row=0, column=1, padx=5, pady=5, sticky="we")

tk.Label(frame_payment, text="Amount (Rs.):", font=FONT_LABELS, bg="white", anchor="e").grid(row=1, column=0, sticky="e", pady=5)
entry_amount = tk.Entry(frame_payment, width=25, font=FONT_LABELS)
entry_amount.grid(row=1, column=1, padx=5, pady=5, sticky="we")

tk.Label(frame_payment, text="Method:", font=FONT_LABELS, bg="white", anchor="e").grid(row=2, column=0, sticky="e", pady=5)
entry_method = ttk.Combobox(frame_payment, width=22, font=FONT_LABELS, values=["cash", "bank", "online"], state="readonly")
entry_method.set("cash")
entry_method.grid(row=2, column=1, padx=5, pady=5, sticky="we")

tk.Label(frame_payment, text="Transaction Ref:", font=FONT_LABELS, bg="white", anchor="e").grid(row=3, column=0, sticky="e", pady=5)
entry_txn = tk.Entry(frame_payment, width=25, font=FONT_LABELS)
entry_txn.grid(row=3, column=1, padx=5, pady=5, sticky="we")

btn_view_inv = tk.Button(
    frame_payment, text="👁️ View Invoice", command=view_invoice,
    bg=COLORS['secondary'], fg="white",
    activebackground="#1976D2",
    relief="flat", font=FONT_BUTTONS, padx=10, pady=6
)
btn_view_inv.grid(row=4, column=0, pady=5, sticky="we")

btn_payment = tk.Button(
    frame_payment, text="✅ Record Payment", command=make_payment,
    bg=COLORS['primary'], fg="white",
    activebackground=COLORS['primary_dark'],
    relief="flat", font=FONT_BUTTONS, padx=10, pady=6
)
btn_payment.grid(row=4, column=1, pady=5, sticky="we")

btn_history = tk.Button(
    frame_payment, text="📊 Payment History", command=show_payment_history,
    bg=COLORS['secondary'], fg="white",
    activebackground="#1976D2",
    relief="flat", font=FONT_BUTTONS, padx=15, pady=8
)
btn_history.grid(row=5, column=0, columnspan=2, pady=10, sticky="we")

btn_clear_payment = tk.Button(
    frame_payment, text="🗑️ Clear", command=clear_payment,
    bg=COLORS['danger'], fg="white",
    activebackground="#d32f2f",
    relief="flat", font=FONT_BUTTONS, padx=15, pady=6
)
btn_clear_payment.grid(row=6, column=0, columnspan=2, pady=5, sticky="we")

# Keyboard shortcuts
root.bind('<Control-s>', lambda e: save_fee_structure())
root.bind('<Control-v>', lambda e: view_fee_structure())
root.bind('<Control-i>', lambda e: preview_invoice())
root.bind('<Control-p>', lambda e: make_payment())
root.bind('<Control-h>', lambda e: show_payment_history())
root.bind('<Control-c>', lambda e: clear_fee())

# Instruction label
tk.Label(
    scrollable_frame,
    text="⌨️ Shortcuts: Ctrl+S=Save | Ctrl+V=View | Ctrl+I=Preview | Ctrl+P=Pay | Ctrl+H=History | Ctrl+C=Clear",
    fg=COLORS['text_gray'],
    font=("Segoe UI", 8),
    bg=COLORS['bg_light']
).pack(pady=10)

# Focus first field
root.after(100, entry_class.focus)

root.mainloop()
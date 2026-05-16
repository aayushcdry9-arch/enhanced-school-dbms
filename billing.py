# billing.py - Database logic for School Billing System

import sqlite3
from datetime import datetime

# Database configuration
DB_NAME = "school_billing.db"

def get_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_billing_tables():
    """Initialize database tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create fee_structure table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fee_structure (
            class_name TEXT PRIMARY KEY,
            tuition REAL NOT NULL,
            bus REAL NOT NULL,
            lab REAL NOT NULL,
            other REAL NOT NULL
        )
    ''')
    
    # Create invoice table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoice (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            class_name TEXT NOT NULL,
            month TEXT NOT NULL,
            year INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            paid_amount REAL DEFAULT 0,
            due_amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            due_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create payment_history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            method TEXT NOT NULL,
            transaction_ref TEXT,
            payment_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (invoice_id) REFERENCES invoice(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def set_fee_structure(class_name, tuition, bus, lab, other):
    """Save or update fee structure for a class"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO fee_structure (class_name, tuition, bus, lab, other)
        VALUES (?, ?, ?, ?, ?)
    ''', (class_name, tuition, bus, lab, other))
    
    conn.commit()
    conn.close()

def get_fee_structure(class_name):
    """Get fee structure for a class"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT class_name, tuition, bus, lab, other
        FROM fee_structure
        WHERE class_name = ?
    ''', (class_name,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'class_name': row['class_name'],
            'tuition': row['tuition'],
            'bus': row['bus'],
            'lab': row['lab'],
            'other': row['other']
        }
    return None

def calculate_total_fees(class_name):
    """Calculate total fees for a class"""
    fees = get_fee_structure(class_name)
    if fees:
        return fees['tuition'] + fees['bus'] + fees['lab'] + fees['other']
    return 0

def generate_invoice(student_id, class_name, month, year, due_date=None):
    """Create a new invoice"""
    total = calculate_total_fees(class_name)
    
    if total == 0:
        raise Exception(f"No fee structure found for class {class_name}")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO invoice (student_id, class_name, month, year, total_amount, paid_amount, due_amount, status, due_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (student_id, class_name, month, year, total, 0, total, 'pending', due_date))
    
    invoice_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return invoice_id

def get_invoice(invoice_id):
    """Get invoice details by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, student_id, class_name, month, year, total_amount, paid_amount, due_amount, status, due_date
        FROM invoice
        WHERE id = ?
    ''', (invoice_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'id': row['id'],
            'student_id': row['student_id'],
            'class_name': row['class_name'],
            'month': row['month'],
            'year': row['year'],
            'total_amount': row['total_amount'],
            'paid_amount': row['paid_amount'],
            'due_amount': row['due_amount'],
            'status': row['status'],
            'due_date': row['due_date']
        }
    return None

def record_payment(invoice_id, amount, method, transaction_ref=None):
    """Record a payment for an invoice"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get current invoice details
    cursor.execute('''
        SELECT paid_amount, total_amount FROM invoice WHERE id = ?
    ''', (invoice_id,))
    
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise Exception(f"Invoice {invoice_id} not found")
    
    current_paid = row['paid_amount']
    total = row['total_amount']
    
    # Check if payment exceeds remaining balance
    new_paid = current_paid + amount
    if new_paid > total:
        conn.close()
        raise Exception(f"Payment amount exceeds remaining balance. Due: Rs. {total - current_paid:.2f}")
    
    # Update invoice
    new_due = total - new_paid
    status = 'paid' if new_due <= 0 else 'pending'
    
    cursor.execute('''
        UPDATE invoice 
        SET paid_amount = ?, due_amount = ?, status = ?
        WHERE id = ?
    ''', (new_paid, new_due, status, invoice_id))
    
    # Record payment history
    cursor.execute('''
        INSERT INTO payment_history (invoice_id, amount, method, transaction_ref)
        VALUES (?, ?, ?, ?)
    ''', (invoice_id, amount, method, transaction_ref))
    
    conn.commit()
    conn.close()

def get_payment_history():
    """Get payment history"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT invoice_id, amount, method, payment_date
        FROM payment_history
        ORDER BY payment_date DESC
        LIMIT 10
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            'invoice_id': row['invoice_id'],
            'amount': row['amount'],
            'method': row['method'],
            'payment_date': row['payment_date']
        })
    
    return history
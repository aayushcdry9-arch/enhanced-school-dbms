import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import hashlib
import csv
from datetime import datetime
import os

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.units import inch

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    import billing
except ImportError:
    billing = None


class Database:
    def __init__(self, db_name="school_dbms_complete.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.create_default_admin()
        if billing and hasattr(billing, "init_billing_tables"):
            billing.init_billing_tables()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                father_name TEXT,
                mother_name TEXT,
                date_of_birth TEXT,
                gender TEXT,
                class TEXT NOT NULL,
                section TEXT,
                roll_number INTEGER,
                address TEXT,
                phone TEXT,
                email TEXT,
                enrollment_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS teachers (
                teacher_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                subject_specialization TEXT,
                qualification TEXT,
                phone TEXT,
                email TEXT,
                hiring_date TEXT DEFAULT CURRENT_TIMESTAMP,
                salary REAL
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                date TEXT NOT NULL,
                status TEXT CHECK(status IN ('Present', 'Absent', 'Late', 'Leave')),
                FOREIGN KEY(student_id) REFERENCES students(student_id)
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS marks (
                mark_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                subject TEXT,
                exam_type TEXT,
                marks_obtained REAL,
                total_marks REAL DEFAULT 100,
                grade TEXT,
                exam_date TEXT,
                FOREIGN KEY(student_id) REFERENCES students(student_id)
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS fees (
                fee_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                fee_type TEXT,
                amount REAL,
                paid_amount REAL DEFAULT 0,
                due_date TEXT,
                payment_date TEXT,
                status TEXT CHECK(status IN ('Paid', 'Pending', 'Partial')),
                FOREIGN KEY(student_id) REFERENCES students(student_id)
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT CHECK(role IN ('admin', 'teacher', 'staff')),
                full_name TEXT
            )
        """)
        self.conn.commit()

    def create_default_admin(self):
        try:
            password_hash = self.hash_password("admin123")
            self.cursor.execute("""
                INSERT INTO users (username, password, role, full_name)
                VALUES (?, ?, ?, ?)
            """, ("admin", password_hash, "admin", "Administrator"))
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass

    def hash_password(self, password):
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def close(self):
        self.conn.close()


class PDFReporter:
    def __init__(self, database):
        self.db = database

    def generate_report(self, student_id, output_file="student_report.pdf"):
        self.db.cursor.execute("SELECT * FROM students WHERE student_id=?", (student_id,))
        student = self.db.cursor.fetchone()
        if not student:
            return None

        c = canvas.Canvas(output_file, pagesize=A4)
        width, height = A4

        c.setFillColor(colors.HexColor("#4CAF50"))
        c.rect(0, height - 1.5 * inch, width, 1.5 * inch, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(width / 2, height - 0.75 * inch, "SCHOOL REPORT CARD")

        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(1 * inch, height - 2.0 * inch, "STUDENT INFORMATION")

        info_data = [
            ["Name:", student[1]],
            ["Father:", student[2] or ""],
            ["Mother:", student[3] or ""],
            ["Class:", f"{student[6]} - {student[7] or ''}"],
            ["Roll:", str(student[8] or "")],
            ["DOB:", student[4] or ""],
            ["Gender:", student[5] or ""],
            ["Phone:", student[10] or ""],
        ]

        info_table = Table(info_data, colWidths=[2 * inch, 3.5 * inch])
        info_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        info_table.wrapOn(c, width, height)
        info_table.drawOn(c, 1 * inch, height - 4.0 * inch)

        self.db.cursor.execute("""
            SELECT subject, exam_type, marks_obtained, total_marks, grade
            FROM marks WHERE student_id=?
        """, (student_id,))
        marks = self.db.cursor.fetchall()

        if marks:
            total_obtained = sum(m[2] for m in marks)
            total_possible = sum(m[3] for m in marks)
            percentage = (total_obtained / total_possible * 100) if total_possible else 0

            marks_data = [["Subject", "Exam", "Obtained", "Total", "Grade"]]
            for m in marks:
                marks_data.append([m[0], m[1], str(m[2]), str(m[3]), m[4] or ""])
            marks_data.append(["TOTAL", "", f"{total_obtained:.1f}", f"{total_possible:.1f}", f"{percentage:.1f}%"])

            marks_table = Table(marks_data, colWidths=[1.7 * inch, 1.2 * inch, 1 * inch, 1 * inch, 1 * inch])
            marks_table.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4CAF50")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]))
            marks_table.wrapOn(c, width, height)
            marks_table.drawOn(c, 1 * inch, height - 6.2 * inch)

        c.setFont("Helvetica-Oblique", 9)
        c.setFillColor(colors.grey)
        c.drawCentredString(width / 2, 25, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        c.save()
        return output_file


class ChartGenerator:
    def __init__(self, database):
        self.db = database

    def create_performance_chart(self, student_id, save_file="performance_chart.png"):
        self.db.cursor.execute("""
            SELECT subject, AVG(marks_obtained)
            FROM marks
            WHERE student_id=?
            GROUP BY subject
        """, (student_id,))
        data = self.db.cursor.fetchall()
        if not data:
            return None

        subjects = [r[0] for r in data]
        marks = [r[1] for r in data]
        colors_list = [
            "#4CAF50" if m >= 90 else
            "#8BC34A" if m >= 80 else
            "#FFC107" if m >= 70 else
            "#FF9800" if m >= 60 else "#F44336"
            for m in marks
        ]

        plt.figure(figsize=(12, 6))
        bars = plt.bar(subjects, marks, color=colors_list, edgecolor="black")
        for bar, mark in zip(bars, marks):
            plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1, f"{mark:.1f}", ha="center", fontweight="bold")

        plt.xlabel("Subject", fontweight="bold")
        plt.ylabel("Marks", fontweight="bold")
        plt.title(f"Student {student_id} - Performance", fontweight="bold")
        plt.ylim(0, 110)
        plt.grid(axis="y", alpha=0.3)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(save_file, dpi=300, bbox_inches="tight")
        plt.close()
        return save_file


class MainApplication:
    def __init__(self, root, user_info, database):
        self.root = root
        self.user_info = user_info
        self.db = database
        self.pdf_reporter = PDFReporter(database)
        self.chart_gen = ChartGenerator(database)
        self.root.title(f"School DBMS - {user_info[1]}")
        self.root.geometry("1000x700")
        self.create_menu()

    def create_menu(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        header = tk.Frame(self.root, bg="#4CAF50", height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="SCHOOL DBMS SYSTEM", font=("Arial", 24, "bold"), bg="#4CAF50", fg="white").pack(pady=15)

        user_bar = tk.Label(self.root, text=f"Logged in: {self.user_info[1]} ({self.user_info[2]})", font=("Arial", 10), bg="#f0f0f0")
        user_bar.pack(fill=tk.X)

        btn_frame = tk.Frame(self.root, padx=30, pady=30)
        btn_frame.pack(fill=tk.BOTH, expand=True)
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)

        buttons = [
            ("Add Student", self.add_student, "#2196F3"),
            ("View Students", self.view_students, "#2196F3"),
            ("Add Attendance", self.add_attendance, "#9C27B0"),
            ("Add Marks", self.add_marks, "#9C27B0"),
            ("PDF Report", self.generate_pdf, "#FF9800"),
            ("Chart", self.show_chart, "#FF9800"),
            ("Fees", self.fee_management, "#795548"),
            ("Export CSV", self.export_excel, "#4CAF50"),
            ("Search", self.search_student, "#607D8B"),
            ("Exit", self.exit_system, "#F44336"),
        ]

        for i, (text, command, color) in enumerate(buttons):
            tk.Button(btn_frame, text=text, font=("Arial", 12, "bold"), command=command,
                      width=28, height=2, bg=color, fg="white").grid(row=i // 2, column=i % 2, padx=15, pady=15, sticky="ew")

    def add_student(self):
        w = tk.Toplevel(self.root)
        w.title("Add New Student")
        w.geometry("500x600")
        fields = ["Name", "Father", "Mother", "DOB", "Gender", "Class", "Section", "Roll", "Phone"]
        entries = {}
        for f in fields:
            tk.Label(w, text=f).pack()
            e = tk.Entry(w)
            e.pack(fill=tk.X, padx=20)
            entries[f.lower()] = e

        def save():
            try:
                self.db.cursor.execute("""
                    INSERT INTO students (name, father_name, mother_name, date_of_birth, gender, class, section, roll_number, phone)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entries["name"].get(),
                    entries["father"].get(),
                    entries["mother"].get(),
                    entries["dob"].get(),
                    entries["gender"].get(),
                    entries["class"].get(),
                    entries["section"].get(),
                    int(entries["roll"].get()),
                    entries["phone"].get()
                ))
                self.db.conn.commit()
                messagebox.showinfo("Success", "Student added.")
                w.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(w, text="Save", command=save).pack(pady=20)

    def view_students(self):
        w = tk.Toplevel(self.root)
        w.title("All Students")
        tree = ttk.Treeview(w, columns=("ID", "Name", "Class", "Roll", "Phone"), show="headings")
        for col in ("ID", "Name", "Class", "Roll", "Phone"):
            tree.heading(col, text=col)
            tree.column(col, width=120)
        tree.pack(fill=tk.BOTH, expand=True)
        self.db.cursor.execute("SELECT student_id, name, class, roll_number, phone FROM students")
        for row in self.db.cursor.fetchall():
            tree.insert("", tk.END, values=row)

    def add_attendance(self):
        w = tk.Toplevel(self.root)
        w.title("Add Attendance")
        sid = tk.Entry(w)
        date = tk.Entry(w)
        status = ttk.Combobox(w, values=["Present", "Absent", "Late", "Leave"], state="readonly")
        for label, widget in [("Student ID", sid), ("Date", date), ("Status", status)]:
            tk.Label(w, text=label).pack()
            widget.pack()

        def save():
            try:
                self.db.cursor.execute("INSERT INTO attendance (student_id, date, status) VALUES (?, ?, ?)",
                                       (int(sid.get()), date.get(), status.get()))
                self.db.conn.commit()
                messagebox.showinfo("Success", "Attendance recorded.")
                w.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(w, text="Save", command=save).pack(pady=10)

    def add_marks(self):
        w = tk.Toplevel(self.root)
        w.title("Add Marks")
        fields = ["Student ID", "Subject", "Exam Type", "Marks", "Grade"]
        entries = {}
        for f in fields:
            tk.Label(w, text=f).pack()
            e = tk.Entry(w)
            e.pack()
            entries[f] = e

        def save():
            try:
                self.db.cursor.execute("""
                    INSERT INTO marks (student_id, subject, exam_type, marks_obtained, grade)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    int(entries["Student ID"].get()),
                    entries["Subject"].get(),
                    entries["Exam Type"].get(),
                    float(entries["Marks"].get()),
                    entries["Grade"].get()
                ))
                self.db.conn.commit()
                messagebox.showinfo("Success", "Marks added.")
                w.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(w, text="Save", command=save).pack(pady=10)

    def generate_pdf(self):
        sid = simpledialog.askinteger("Student ID", "Enter Student ID:")
        if sid:
            result = self.pdf_reporter.generate_report(sid)
            messagebox.showinfo("Success", f"Saved: {result}" if result else "Student not found.")

    def show_chart(self):
        sid = simpledialog.askinteger("Student ID", "Enter Student ID:")
        if sid:
            result = self.chart_gen.create_performance_chart(sid)
            messagebox.showinfo("Success", f"Saved: {result}" if result else "No marks found.")

    def fee_management(self):
        w = tk.Toplevel(self.root)
        w.title("Fee Management")
        tk.Label(w, text="Fee Management").pack()

    def export_excel(self):
        try:
            self.db.cursor.execute("SELECT student_id, name, father_name, mother_name, date_of_birth, gender, class, section, roll_number, phone FROM students")
            students = self.db.cursor.fetchall()
            with open("students_export.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Name", "Father", "Mother", "DOB", "Gender", "Class", "Section", "Roll", "Phone"])
                writer.writerows(students)
            messagebox.showinfo("Success", "Exported to students_export.csv")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def search_student(self):
        s = simpledialog.askstring("Search", "Enter name or ID:")
        if s:
            self.db.cursor.execute("""
                SELECT student_id, name, class, roll_number
                FROM students
                WHERE name LIKE ? OR CAST(student_id AS TEXT) LIKE ?
            """, (f"%{s}%", f"%{s}%"))
            rows = self.db.cursor.fetchall()
            w = tk.Toplevel(self.root)
            w.title("Search Results")
            tree = ttk.Treeview(w, columns=("ID", "Name", "Class", "Roll"), show="headings")
            for col in ("ID", "Name", "Class", "Roll"):
                tree.heading(col, text=col)
                tree.column(col, width=120)
            tree.pack(fill=tk.BOTH, expand=True)
            for row in rows:
                tree.insert("", tk.END, values=row)

    def exit_system(self):
        if messagebox.askyesno("Exit", "Are you sure?"):
            self.db.close()
            self.root.destroy()


class LoginWindow:
    def __init__(self, root, database):
        self.root = root
        self.db = database
        self.login_win = tk.Toplevel(root)
        self.login_win.title("School DBMS Login")
        self.login_win.geometry("450x400")
        self.login_win.resizable(False, False)
        self.create_login_ui()

    def create_login_ui(self):
        tk.Label(self.login_win, text="SCHOOL DBMS", font=("Arial", 24, "bold"), bg="#4CAF50", fg="white").pack(fill=tk.X)
        frame = tk.Frame(self.login_win, padx=30, pady=30, bg="#f5f5f5")
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Username:", bg="#f5f5f5").grid(row=0, column=0, sticky="w", pady=10)
        self.username_entry = tk.Entry(frame, width=28)
        self.username_entry.grid(row=0, column=1)

        tk.Label(frame, text="Password:", bg="#f5f5f5").grid(row=1, column=0, sticky="w", pady=10)
        self.password_entry = tk.Entry(frame, width=28, show="•")
        self.password_entry.grid(row=1, column=1)

        tk.Label(frame, text="Role:", bg="#f5f5f5").grid(row=2, column=0, sticky="w", pady=10)
        self.role_combo = ttk.Combobox(frame, values=["admin", "teacher", "staff"], state="readonly", width=25)
        self.role_combo.grid(row=2, column=1)
        self.role_combo.current(0)

        tk.Button(frame, text="Login", command=self.login, bg="#4CAF50", fg="white", width=20).grid(row=3, column=0, columnspan=2, pady=25)

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        role = self.role_combo.get()

        if not username or not password:
            messagebox.showerror("Login Error", "Please enter username and password.")
            return

        password_hash = self.db.hash_password(password)
        self.db.cursor.execute("""
            SELECT user_id, full_name, role
            FROM users
            WHERE username=? AND password=? AND role=?
        """, (username, password_hash, role))
        user = self.db.cursor.fetchone()

        if user:
            messagebox.showinfo("Login Success", f"Welcome, {user[1]}!")
            self.login_win.destroy()
            self.root.deiconify()
            MainApplication(self.root, user, self.db)
        else:
            messagebox.showerror("Login Failed", "Invalid username, password, or role.")


if __name__ == "__main__":
    db = Database()
    root = tk.Tk()
    root.withdraw()
    app = LoginWindow(root, db)
    root.mainloop()
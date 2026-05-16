# ============================================
# 🏫 COMPLETE SCHOOL DBMS - TRIYUGA SECONDARY SCHOOL
# For Class 10 & Bachelor‑level learning
# ============================================

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import hashlib
import csv
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.units import inch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


SCHOOL_NAME = "Triyuga Secondary School"
SCHOOL_ADDRESS = "Triyuga, Koshi Province, Nepal"
SCHOOL_PHONE = "+977-1-4567890"
SCHOOL_EMAIL = "info@triyugaschool.edu.np"
ACADEMIC_YEAR = "2082/2083"
PRIMARY_COLOR = "#DC143C"
SECONDARY_COLOR = "#003893"
ACCENT_COLOR = "#FFD700"
SUCCESS_COLOR = "#008000"


class Database:
    def __init__(self, db_name='school_dbms.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.create_default_admin()
        self.create_sample_data_button()

    def create_tables(self):
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            father_name TEXT,
            mother_name TEXT,
            date_of_birth TEXT,
            gender TEXT,
            class TEXT NOT NULL,
            section TEXT,
            roll_number INTEGER UNIQUE NOT NULL,
            address TEXT,
            phone TEXT,
            email TEXT,
            nationality TEXT,
            religion TEXT,
            blood_group TEXT,
            enrollment_date TEXT DEFAULT (date('now')))""")

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS teachers (
            teacher_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            subject_specialization TEXT,
            qualification TEXT,
            phone TEXT,
            email TEXT,
            salary REAL)""")

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS attendance (
            attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            date TEXT NOT NULL,
            status TEXT,
            FOREIGN KEY (student_id) REFERENCES students(student_id))""")

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS marks (
            mark_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject TEXT,
            exam_type TEXT,
            marks_obtained REAL,
            total_marks REAL DEFAULT 100,
            grade TEXT,
            exam_date TEXT,
            FOREIGN KEY (student_id) REFERENCES students(student_id))""")

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS fees (
            fee_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            fee_type TEXT,
            amount REAL,
            paid_amount REAL DEFAULT 0,
            due_date TEXT,
            payment_date TEXT,
            status TEXT,
            FOREIGN KEY (student_id) REFERENCES students(student_id))""")

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT,
            full_name TEXT)""")

        # Indexes for performance
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_name ON students(name)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_roll ON students(roll_number)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_marks_sid ON marks(student_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_sid ON attendance(student_id)")

        self.conn.commit()

    def create_default_admin(self):
        self.cursor.execute("SELECT 1 FROM users WHERE username='admin'")
        if self.cursor.fetchone() is None:
            password_hash = self.hash_password("admin123")
            self.cursor.execute(
                "INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)",
                ("admin", password_hash, "admin", "Administrator"))
            self.conn.commit()

    def create_sample_data_button(self):
        self.cursor.execute("SELECT COUNT(*) FROM students")
        if self.cursor.fetchone()[0] == 0:
            # Sample Class 10 students
            samples = [
                ("Ramesh Thapa", "Hari Thapa", "Gita Thapa", "2015-01-10", "Male", "10", "A", 1, "+977-9812345678"),
                ("Sita Magar", "Bishnu Magar", "Sunita Magar", "2015-02-15", "Female", "10", "A", 2, "+977-9812345679"),
                ("Bikash Shrestha", "Bhola Shrestha", "Sushma Shrestha", "2015-03-20", "Male", "10", "B", 3, "+977-9812345680"),
            ]
            for s in samples:
                self.cursor.execute("""
                    INSERT INTO students (name, father_name, mother_name, date_of_birth,
                        gender, class, section, roll_number, phone)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, s)
            self.conn.commit()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def close(self):
        self.conn.close()


class PDFReporter:
    def __init__(self, database):
        self.db = database

    def generate_report(self, student_id, output_file="report.pdf"):
        self.db.cursor.execute("SELECT * FROM students WHERE student_id=?", (student_id,))
        student = self.db.cursor.fetchone()
        if not student:
            return None

        c = canvas.Canvas(output_file, pagesize=A4)
        width, height = A4

        c.setFillColor(colors.HexColor(PRIMARY_COLOR))
        c.rect(0, height - 2*inch, width, 2*inch, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(width/2, height - 0.7*inch, SCHOOL_NAME)
        c.setFont("Helvetica", 11)
        c.drawCentredString(width/2, height - 1*inch, SCHOOL_ADDRESS)

        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(1*inch, height - 2.5*inch, "STUDENT INFORMATION")
        c.setFont("Helvetica", 10)

        info_data = [
            ["Name:", student[1]],
            ["Class:", f"{student[6]} - {student[7]}"],
            ["Roll:", str(student[8])],
            ["Father:", student[2] or ""],
            ["Mother:", student[3] or ""],
            ["DOB:", student[4] or ""],
            ["Phone:", student[10] or ""],
        ]
        info_table = Table(info_data, colWidths=[1.8*inch, 3.5*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ]))
        info_table.wrapOn(c, width, height)
        info_table.drawOn(c, 1*inch, height - 4.5*inch)

        # Marks table
        c.setFont("Helvetica-Bold", 14)
        c.drawString(1*inch, height - 6*inch, "MARKS DETAILS")
        self.db.cursor.execute("""
            SELECT subject, exam_type, marks_obtained, total_marks, grade, exam_date
            FROM marks WHERE student_id=? ORDER BY exam_date
        """, (student_id,))
        marks_data = [["Subject", "Exam", "Obtained", "Total", "Grade", "Date"]]
        for row in self.db.cursor.fetchall():
            marks_data.append([row[0], row[1], str(row[2]), str(row[3]), row[4], row[5]])
        marks_table = Table(marks_data, colWidths=[1.2*inch]*6)
        marks_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        marks_table.wrapOn(c, width, height)
        marks_table.drawOn(c, 1*inch, height - 8.5*inch)

        c.save()
        return output_file


class ChartGenerator:
    def __init__(self, database):
        self.db = database

    def create_performance_chart(self, student_id, save_file="chart.png"):
        self.db.cursor.execute("""
            SELECT subject, AVG(marks_obtained) FROM marks
            WHERE student_id=? GROUP BY subject
        """, (student_id,))
        data = self.db.cursor.fetchall()
        if not data:
            return None

        subjects = [row[0] for row in data]
        marks = [row[1] for row in data]

        plt.figure(figsize=(12, 6))
        plt.bar(subjects, marks, color=PRIMARY_COLOR, edgecolor='black')
        plt.xlabel('Subject', fontweight='bold')
        plt.ylabel('Marks', fontweight='bold')
        plt.title(f'Student {student_id} - Performance', fontweight='bold')
        plt.ylim(0, 110)
        plt.grid(axis='y', alpha=0.3)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(save_file, dpi=300)
        plt.close()
        return save_file


class LoginWindow:
    def __init__(self, root, database):
        self.root = root
        self.db = database
        self.root.title(f"🔐 {SCHOOL_NAME} - Login")
        self.root.geometry("450x400")
        self.root.resizable(False, False)
        self.create_login_ui()

    def create_login_ui(self):
        title = tk.Label(self.root, text=f"🏫 {SCHOOL_NAME}", font=("Arial", 20, "bold"),
                         bg=PRIMARY_COLOR, fg="white", pady=20)
        title.pack(fill=tk.X)

        tk.Label(self.root, text=SCHOOL_ADDRESS, bg=PRIMARY_COLOR, fg="white").pack()

        login_frame = tk.Frame(self.root, padx=30, pady=30)
        login_frame.pack()

        tk.Label(login_frame, text="Username:", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w", pady=10)
        self.username_entry = tk.Entry(login_frame, font=("Arial", 12), width=28)
        self.username_entry.grid(row=0, column=1, pady=10)

        tk.Label(login_frame, text="Password:", font=("Arial", 12, "bold")).grid(row=1, column=0, sticky="w", pady=10)
        self.password_entry = tk.Entry(login_frame, font=("Arial", 12), width=28, show="•")
        self.password_entry.grid(row=1, column=1, pady=10)

        tk.Label(login_frame, text="Role:", font=("Arial", 12, "bold")).grid(row=2, column=0, sticky="w", pady=10)
        self.role_combo = ttk.Combobox(login_frame, values=["admin", "teacher", "staff"], width=25, state="readonly")
        self.role_combo.grid(row=2, column=1, pady=10)
        self.role_combo.current(0)

        tk.Button(login_frame, text="🔓 Login", command=self.login, font=("Arial", 13, "bold"),
                  bg=PRIMARY_COLOR, fg="white", width=22, height=2).grid(row=3, column=0, columnspan=2, pady=25)

        tk.Label(login_frame, text="Default: admin / admin123", font=("Arial", 9), fg="grey").grid(row=4, column=0, columnspan=2)

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        role = self.role_combo.get()

        if not username or not password:
            messagebox.showerror("Error", "❌ Please enter username and password!")
            return

        password_hash = self.db.hash_password(password)

        self.db.cursor.execute("""
            SELECT user_id, full_name, role FROM users
            WHERE username=? AND password=? AND role=?
        """, (username, password_hash, role))

        user = self.db.cursor.fetchone()

        if user:
            messagebox.showinfo("Success", f"✅ Welcome, {user[1]}!")
            self.root.destroy()
            main_window = tk.Tk()
            app = MainApplication(main_window, user, self.db)
            main_window.mainloop()
        else:
            messagebox.showerror("Login Failed", "❌ Invalid credentials!")


class MainApplication:
    def __init__(self, root, user_info, database):
        self.root = root
        self.user_info = user_info
        self.db = database
        self.pdf_reporter = PDFReporter(database)
        self.chart_gen = ChartGenerator(database)

        self.root.title(f"🏫 {SCHOOL_NAME} - DBMS")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)

        self.create_menu()
        self.create_dashboard()

    def create_menu(self):
        header = tk.Frame(self.root, bg=PRIMARY_COLOR, height=100)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text=f"🏫 {SCHOOL_NAME}", font=("Arial", 20, "bold"),
                 bg=PRIMARY_COLOR, fg="white").pack()
        tk.Label(header, text=SCHOOL_ADDRESS, font=("Arial", 11), bg=PRIMARY_COLOR, fg="white").pack()
        tk.Label(header, text=f"Academic Year: {ACADEMIC_YEAR}", font=("Arial", 10), bg=PRIMARY_COLOR, fg="white").pack()

        user_bar = tk.Label(self.root, text=f"Logged in: {self.user_info[1]} ({self.user_info[2]})",
                           font=("Arial", 10), bg="#f0f0f0")
        user_bar.pack(fill=tk.X)

    def create_dashboard(self):
        db = tk.Frame(self.root, padx=30, pady=10)
        db.pack(fill=tk.X)

        self.db.cursor.execute("SELECT COUNT(*) FROM students")
        num_stud = self.db.cursor.fetchone()[0]

        self.db.cursor.execute("SELECT COUNT(*) FROM marks WHERE exam_type='First Term'")
        num_marks = self.db.cursor.fetchone()[0]

        tk.Label(db, text=f"📊 Dashboard | Students: {num_stud} | Marks Records: {num_marks}",
                 font=("Arial", 10, "bold"), bg="#e0e0e0").pack(fill=tk.X)

    def create_button_area(self):
        btn_frame = tk.Frame(self.root, padx=30, pady=30)
        btn_frame.pack(fill=tk.BOTH, expand=True)

        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)

        buttons = [
            ("➕ Add Student", self.add_student, SECONDARY_COLOR),
            ("👀 View/Edit Students", self.view_students, SECONDARY_COLOR),
            ("📝 Add Attendance", self.add_attendance, ACCENT_COLOR),
            ("📊 Add Marks", self.add_marks, ACCENT_COLOR),
            ("📄 PDF Report", self.generate_pdf, SUCCESS_COLOR),
            ("📈 Chart", self.show_chart, SUCCESS_COLOR),
            ("💰 Fees", self.fee_management, "#795548"),
            ("📤 Export Excel", self.export_excel, "#4CAF50"),
            ("🔍 Search", self.search_student, "#607D8B"),
            ("❌ Exit", self.exit_system, "#F44336"),
        ]

        for i, (text, command, color) in enumerate(buttons):
            btn = tk.Button(btn_frame, text=text, font=("Arial", 12, "bold"), command=command,
                            width=26, height=2, bg=color, fg="white")
            btn.grid(row=i//2, column=i%2, padx=15, pady=15, sticky="ew")

        status = tk.Label(self.root, text=f"✅ Ready | {SCHOOL_ADDRESS}",
                         font=("Arial", 9), bg="#e0e0e0")
        status.pack(side=tk.BOTTOM, fill=tk.X)

    def add_student(self):
        window = tk.Toplevel(self.root)
        window.title("➕ Add New Student")
        window.geometry("500x650")

        tk.Label(window, text="➕ ADD NEW STUDENT", font=("Arial", 16, "bold"), pady=15).pack()

        entries = {}
        fields = [
            ("Name:", "name"),
            ("Father's Name:", "father"),
            ("Mother's Name:", "mother"),
            ("Date of Birth (YYYY-MM-DD):", "dob"),
            ("Gender (Male/Female/Other):", "gender"),
            ("Class (e.g. 10, 11, 12):", "class"),
            ("Section (e.g. A, B):", "section"),
            ("Roll Number:", "roll"),
            ("Phone:", "phone"),
            ("Nationality:", "nationality"),
            ("Religion:", "religion"),
            ("Blood Group:", "blood_group"),
        ]

        for label, key in fields:
            frame = tk.Frame(window)
            frame.pack(fill=tk.X, padx=30, pady=5)
            tk.Label(frame, text=label, font=("Arial", 11), width=22, anchor="w").pack(side=tk.LEFT)
            entry = tk.Entry(frame, font=("Arial", 11))
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            entries[key] = entry

        def save():
            name = entries["name"].get().strip()
            if not name:
                messagebox.showerror("Error", "Name is required.")
                return

            father = entries["father"].get().strip()
            mother = entries["mother"].get().strip()
            dob = entries["dob"].get().strip()
            gender = entries["gender"].get().strip()
            class_ = entries["class"].get().strip()
            section = entries["section"].get().strip()
            phone = entries["phone"].get().strip()
            nationality = entries["nationality"].get().strip()
            religion = entries["religion"].get().strip()
            blood_group = entries["blood_group"].get().strip()

            try:
                roll = int(entries["roll"].get())
            except ValueError:
                messagebox.showerror("Error", "Roll must be a number.")
                return

            try:
                self.db.cursor.execute("""
                    INSERT INTO students (
                        name, father_name, mother_name, date_of_birth,
                        gender, class, section, roll_number, phone,
                        nationality, religion, blood_group
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (name, father, mother, dob, gender, class_, section, roll, phone,
                      nationality, religion, blood_group))
                self.db.conn.commit()
                messagebox.showinfo("Success", "✅ Student added successfully!")
                window.destroy()
            except sqlite3.IntegrityError as e:
                self.db.conn.rollback()
                messagebox.showerror("Database Error", f"Roll number must be unique: {str(e)}")
            except Exception as e:
                self.db.conn.rollback()
                messagebox.showerror("Error", f"Database error: {str(e)}")

        tk.Button(window, text="💾 Save Student", command=save,
                  bg=SUCCESS_COLOR, fg="white", font=("Arial", 12, "bold"),
                  width=20, height=2).pack(pady=20)

    def view_students(self):
        window = tk.Toplevel(self.root)
        window.title("👀 View / Edit Students")
        window.geometry("900x500")

        tk.Label(window, text="👀 VIEW / EDIT STUDENTS", font=("Arial", 14, "bold"), pady=10).pack()

        frame = tk.Frame(window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("ID", "Name", "Class", "Section", "Roll", "Phone")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=20)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=scrollbar.set)

        self.db.cursor.execute("""
            SELECT student_id, name, class, section, roll_number, phone
            FROM students ORDER BY class, section, roll_number
        """)
        for student in self.db.cursor.fetchall():
            tree.insert("", tk.END, values=student, tags=(student[0],))

        # Edit and Delete buttons
        btn_frame = tk.Frame(window)
        btn_frame.pack(pady=10)

        def edit():
            selected = tree.selection()
            if not selected:
                messagebox.showinfo("Info", "Please select a student to edit.")
                return
            values = tree.item(selected[0], "values")
            student_id = int(values[0])
            self.open_edit_student_window(student_id)

        def delete():
            selected = tree.selection()
            if not selected:
                messagebox.showinfo("Info", "Please select a student to delete.")
                return
            values = tree.item(selected[0], "values")
            student_id = int(values[0])
            if messagebox.askyesno("Confirm Delete", "Delete this student? This action cannot be undone."):
                self.db.cursor.execute("DELETE FROM students WHERE student_id=?", (student_id,))
                self.db.cursor.execute("DELETE FROM attendance WHERE student_id=?", (student_id,))
                self.db.cursor.execute("DELETE FROM marks WHERE student_id=?", (student_id,))
                self.db.cursor.execute("DELETE FROM fees WHERE student_id=?", (student_id,))
                self.db.conn.commit()
                tree.delete(selected)
                messagebox.showinfo("Deleted", "Student deleted.")

        tk.Button(btn_frame, text="✏️ Edit Selected", command=edit,
                  bg="#FF9800", fg="white", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🗑️ Delete Selected", command=delete,
                  bg="#F44336", fg="white", width=15).pack(side=tk.LEFT, padx=5)

    def open_edit_student_window(self, student_id):
        self.db.cursor.execute("SELECT * FROM students WHERE student_id=?", (student_id,))
        rec = self.db.cursor.fetchone()
        if not rec:
            messagebox.showerror("Error", "Student not found.")
            return

        window = tk.Toplevel(self.root)
        window.title("✏️ Edit Student")
        window.geometry("500x650")

        tk.Label(window, text="✏️ EDIT STUDENT", font=("Arial", 16, "bold"), pady=15).pack()

        entries = {}
        fields = ["Name", "Father's Name", "Mother's Name", "DOB", "Gender", "Class",
                  "Section", "Roll", "Phone", "Nationality", "Religion", "Blood Group"]

        current = {
            "Name": rec[1],
            "Father's Name": rec[2] or "",
            "Mother's Name": rec[3] or "",
            "DOB": rec[4] or "",
            "Gender": rec[5] or "",
            "Class": rec[6],
            "Section": rec[7] or "",
            "Roll": str(rec[8]),
            "Phone": rec[10] or "",
            "Nationality": rec[11] or "",
            "Religion": rec[12] or "",
            "Blood Group": rec[13] or "",
        }

        for label in fields:
            frame = tk.Frame(window)
            frame.pack(fill=tk.X, padx=30, pady=5)
            tk.Label(frame, text=f"{label}:", font=("Arial", 11), width=18, anchor="w").pack(side=tk.LEFT)
            entry = tk.Entry(frame, font=("Arial", 11))
            entry.insert(0, current[label])
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            entries[label] = entry

        def save():
            name = entries["Name"].get().strip()
            if not name:
                messagebox.showerror("Error", "Name is required.")
                return

            try:
                roll = int(entries["Roll"].get())
            except ValueError:
                messagebox.showerror("Error", "Roll must be a number.")
                return

            try:
                self.db.cursor.execute("""
                    UPDATE students SET
                        name=?, father_name=?, mother_name=?, date_of_birth=?,
                        gender=?, class=?, section=?, roll_number=?, phone=?,
                        nationality=?, religion=?, blood_group=?
                    WHERE student_id=?
                """, (
                    name,
                    entries["Father's Name"].get().strip(),
                    entries["Mother's Name"].get().strip(),
                    entries["DOB"].get().strip(),
                    entries["Gender"].get().strip(),
                    entries["Class"].get().strip(),
                    entries["Section"].get().strip(),
                    roll,
                    entries["Phone"].get().strip(),
                    entries["Nationality"].get().strip(),
                    entries["Religion"].get().strip(),
                    entries["Blood Group"].get().strip(),
                    student_id
                ))
                self.db.conn.commit()
                messagebox.showinfo("Updated", "Student updated.")
                window.destroy()
            except Exception as e:
                self.db.conn.rollback()
                messagebox.showerror("Error", f"Database error: {str(e)}")

        tk.Button(window, text="💾 Update Student", command=save,
                  bg=SUCCESS_COLOR, fg="white", font=("Arial", 12, "bold"),
                  width=20, height=2).pack(pady=20)

    def add_attendance(self):
        window = tk.Toplevel(self.root)
        window.title("📝 Add Attendance")
        window.geometry("400x300")

        tk.Label(window, text="📝 ADD ATTENDANCE", font=("Arial", 16, "bold"), pady=15).pack()

        tk.Label(window, text="Student ID:", font=("Arial", 11)).pack()
        sid = tk.Entry(window, font=("Arial", 11))
        sid.pack()

        tk.Label(window, text="Date (YYYY-MM-DD):", font=("Arial", 11)).pack(pady=(10, 0))
        date = tk.Entry(window, font=("Arial", 11))
        date.pack()

        tk.Label(window, text="Status:", font=("Arial", 11)).pack(pady=(10, 0))
        status = ttk.Combobox(window, values=["Present", "Absent", "Late", "Leave"], state="readonly")
        status.pack()
        status.current(0)

        def save():
            try:
                student_id = int(sid.get())
                the_date = date.get().strip()
                the_status = status.get().strip()
                if not the_date:
                    messagebox.showerror("Error", "Date is required.")
                    return
                self.db.cursor.execute("""
                    INSERT INTO attendance (student_id, date, status)
                    VALUES (?, ?, ?)
                """, (student_id, the_date, the_status))
                self.db.conn.commit()
                messagebox.showinfo("Success", "✅ Attendance recorded!")
                window.destroy()
            except ValueError:
                messagebox.showerror("Error", "Student ID must be a number.")
            except Exception as e:
                self.db.conn.rollback()
                messagebox.showerror("Error", f"Database error: {str(e)}")

        tk.Button(window, text="💾 Save", command=save,
                  bg=SUCCESS_COLOR, fg="white", font=("Arial", 12), width=15).pack(pady=20)

    def add_marks(self):
        window = tk.Toplevel(self.root)
        window.title("📊 Add Marks")
        window.geometry("400x450")

        tk.Label(window, text="📊 ADD MARKS", font=("Arial", 16, "bold"), pady=15).pack()

        entries = {}
        for label, key in [("Student ID:", "sid"),
                           ("Subject:", "subject"),
                           ("Exam Type:", "exam"),
                           ("Marks Obtained:", "marks"),
                           ("Total Marks:", "total"),
                           ("Grade:", "grade")]:
            tk.Label(window, text=label, font=("Arial", 11)).pack(pady=(5, 0))
            entry = tk.Entry(window, font=("Arial", 11))
            entry.pack()
            entries[key] = entry

        def save():
            try:
                student_id = int(entries["sid"].get())
                subject = entries["subject"].get().strip()
                exam_type = entries["exam"].get().strip()
                marks_obtained = float(entries["marks"].get())
                total_marks = float(entries["total"].get())
                grade = entries["grade"].get().strip() or "NULL"
                exam_date = datetime.now().strftime("%Y-%m-%d")

                if not subject:
                    messagebox.showerror("Error", "Subject is required.")
                    return
                if not exam_type:
                    messagebox.showerror("Error", "Exam type is required.")
                    return
                if marks_obtained < 0 or marks_obtained > total_marks:
                    messagebox.showerror("Error", "Marks must be between 0 and total marks.")
                    return

                self.db.cursor.execute("""
                    INSERT INTO marks (
                        student_id, subject, exam_type,
                        marks_obtained, total_marks, grade, exam_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (student_id, subject, exam_type, marks_obtained, total_marks, grade, exam_date))
                self.db.conn.commit()
                messagebox.showinfo("Success", "✅ Marks added!")
                window.destroy()
            except ValueError:
                messagebox.showerror("Error", "Student ID or marks must be numbers.")
            except Exception as e:
                self.db.conn.rollback()
                messagebox.showerror("Error", f"Database error: {str(e)}")

        tk.Button(window, text="💾 Save", command=save,
                  bg=SUCCESS_COLOR, fg="white", font=("Arial", 12), width=15).pack(pady=20)

    def generate_pdf(self):
        student_id = simpledialog.askinteger("Student ID", "Enter Student ID:")
        if not student_id:
            return
        result = self.pdf_reporter.generate_report(student_id)
        if result:
            messagebox.showinfo("Success", f"✅ PDF saved as: {result}")
        else:
            messagebox.showerror("Error", "❌ Student not found!")

    def show_chart(self):
        student_id = simpledialog.askinteger("Student ID", "Enter Student ID:")
        if not student_id:
            return
        result = self.chart_gen.create_performance_chart(student_id)
        if result:
            messagebox.showinfo("Success", f"✅ Chart saved as: {result}")
        else:
            messagebox.showerror("Error", "❌ No marks data found!")

    def fee_management(self):
        window = tk.Toplevel(self.root)
        window.title("💰 Fee Management")
        window.geometry("400x350")

        tk.Label(window, text="💰 FEE MANAGEMENT", font=("Arial", 16, "bold"), pady=15).pack()

        def add_fee():
            fw = tk.Toplevel(window)
            fw.title("➕ Add Fee")
            fw.geometry("350x300")

            entries = {}
            for label, key in [("Student ID:", "sid"),
                               ("Fee Type:", "ftype"),
                               ("Amount (Rs):", "amount"),
                               ("Due Date (YYYY-MM-DD):", "due")]:
                tk.Label(fw, text=label, font=("Arial", 11)).pack()
                entry = tk.Entry(fw, font=("Arial", 11))
                entry.pack()
                entries[key] = entry

            def save():
                try:
                    sid = int(entries["sid"].get())
                    ftype = entries["ftype"].get().strip()
                    amount = float(entries["amount"].get())
                    due = entries["due"].get().strip()
                    if not ftype or amount <= 0 or not due:
                        messagebox.showerror("Error", "Please fill all fields correctly.")
                        return

                    self.db.cursor.execute("""
                        INSERT INTO fees (
                            student_id, fee_type, amount, due_date, status
                        ) VALUES (?, ?, ?, ?, 'Pending')
                    """, (sid, ftype, amount, due))
                    self.db.conn.commit()
                    messagebox.showinfo("Success", "✅ Fee added!")
                    fw.destroy()
                except ValueError:
                    messagebox.showerror("Error", "Student ID or amount must be numbers.")
                except Exception as e:
                    self.db.conn.rollback()
                    messagebox.showerror("Error", f"Database error: {str(e)}")

            tk.Button(fw, text="💾 Save", command=save,
                      bg="#FF9800", fg="white", width=15).pack(pady=20)

        tk.Button(window, text="➕ Add Fee", command=add_fee,
                  bg="#FF9800", fg="white", font=("Arial", 12), width=20).pack(pady=10)

        def view_fees():
            self.db.cursor.execute("""
                SELECT s.name, f.fee_type, f.amount, f.status
                FROM fees f
                JOIN students s ON f.student_id = s.student_id
            """)
            fees = self.db.cursor.fetchall()

            fw = tk.Toplevel(window)
            fw.title("📄 Fee Records")
            fw.geometry("550x400")

            text = tk.Text(fw, font=("Courier", 10))
            text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            text.insert(tk.END, "NAME              | FEE TYPE      | AMOUNT (Rs) | STATUS\n")
            text.insert(tk.END, "-" * 70 + "\n")
            for f in fees:
                text.insert(tk.END, f"{f[0]:<15} | {f[1]:<12} | {f[2]:<12} | {f[3]}\n")

        tk.Button(window, text="👁️ View Fees", command=view_fees,
                  bg="#2196F3", fg="white", font=("Arial", 12), width=20).pack(pady=10)

    def export_excel(self):
        try:
            self.db.cursor.execute("""
                SELECT student_id, name, father_name, mother_name, date_of_birth,
                       gender, class, section, roll_number, address, phone
                FROM students
            """)
            students = self.db.cursor.fetchall()

            with open('students_export.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Name", "Father", "Mother", "DOB", "Gender",
                                 "Class", "Section", "Roll", "Address", "Phone"])
                for s in students:
                    writer.writerow(s)
            messagebox.showinfo("Success", "✅ Exported to students_export.csv")
        except Exception as e:
            messagebox.showerror("Error", f"❌ {str(e)}")

    def search_student(self):
        search = simpledialog.askstring("Search", "Enter name or student ID (number):")
        if not search:
            return

        try:
            # Search by name (partial match) or by ID
            if search.isdigit():
                self.db.cursor.execute("""
                    SELECT student_id, name, class, section, roll_number
                    FROM students WHERE student_id = ?
                """, (int(search),))
            else:
                self.db.cursor.execute("""
                    SELECT student_id, name, class, section, roll_number
                    FROM students WHERE name LIKE ?
                """, (f"%{search}%",))
            results = self.db.cursor.fetchall()

            if results:
                window = tk.Toplevel(self.root)
                window.title("🔍 Search Results")
                window.geometry("600x300")

                tk.Label(window, text="Search Results", font=("Arial", 14, "bold")).pack(pady=10)

                columns = ("ID", "Name", "Class", "Section", "Roll")
                tree = ttk.Treeview(window, columns=columns, show="headings", height=15)
                for col in columns:
                    tree.heading(col, text=col)
                    tree.column(col, width=100)
                tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

                for r in results:
                    tree.insert("", tk.END, values=r)
            else:
                messagebox.showinfo("No Results", "❌ No student found.")
        except Exception as e:
            messagebox.showerror("Error", f"Database error: {str(e)}")

    def exit_system(self):
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.db.close()
            self.root.destroy()


if __name__ == "__main__":
    print("="*60)
    print("🏫 TRIYUGA SECONDARY SCHOOL - DBMS SYSTEM")
    print("="*60)
    print("Starting application...")

    db = Database()
    root = tk.Tk()
    app = LoginWindow(root, db)
    root.mainloop()
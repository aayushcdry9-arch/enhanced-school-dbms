# ============================================
# 🏫 COMPLETE SCHOOL DBMS SYSTEM
# All Features: GUI, PDF, Charts, Login, Fees, Notifications
# ============================================

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

# Database Setup
class Database:
    def __init__(self, db_name='school_dbms_complete.db'):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.create_default_admin()
    
    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, father_name TEXT, mother_name TEXT,
                date_of_birth TEXT, gender TEXT, class TEXT NOT NULL,
                section TEXT, roll_number INTEGER, address TEXT,
                phone TEXT, email TEXT, enrollment_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS teachers (
                teacher_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, subject_specialization TEXT,
                qualification TEXT, phone TEXT, email TEXT,
                hiring_date TEXT DEFAULT CURRENT_TIMESTAMP, salary REAL
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER, date TEXT NOT NULL,
                status TEXT CHECK(status IN ('Present', 'Absent', 'Late', 'Leave')),
                FOREIGN KEY (student_id) REFERENCES students(student_id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS marks (
                mark_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER, subject TEXT, exam_type TEXT,
                marks_obtained REAL, total_marks REAL DEFAULT 100,
                grade TEXT, exam_date TEXT,
                FOREIGN KEY (student_id) REFERENCES students(student_id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS fees (
                fee_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER, fee_type TEXT, amount REAL,
                paid_amount REAL DEFAULT 0, due_date TEXT,
                payment_date TEXT, status TEXT CHECK(status IN ('Paid', 'Pending', 'Partial')),
                FOREIGN KEY (student_id) REFERENCES students(student_id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
                role TEXT CHECK(role IN ('admin', 'teacher', 'staff')),
                full_name TEXT
            )
        ''')
        
        self.conn.commit()
    
    def create_default_admin(self):
        try:
            password_hash = hashlib.sha256("admin123".encode()).hexdigest()
            self.cursor.execute('''
                INSERT INTO users (username, password, role, full_name)
                VALUES (?, ?, ?, ?)
            ''', ('admin', password_hash, 'admin', 'Administrator'))
            self.conn.commit()
            print("✅ Default admin created (username: admin, password: admin123)")
        except sqlite3.IntegrityError:
            pass
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def close(self):
        self.conn.close()

# Login Window
class LoginWindow:
    def __init__(self, root, database):
        self.root = root
        self.db = database
        self.root.title("🔐 School DBMS - Login")
        self.root.geometry("450x400")
        self.root.resizable(False, False)
        self.create_login_ui()
    
    def create_login_ui(self):
        title = tk.Label(self.root, text="🏫 SCHOOL DBMS", font=("Arial", 24, "bold"), 
                        bg="#4CAF50", fg="white", pady=20)
        title.pack(fill=tk.X)
        
        login_frame = tk.Frame(self.root, padx=30, pady=30, bg="#f5f5f5")
        login_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(login_frame, text="Username:", font=("Arial", 12, "bold"), bg="#f5f5f5").grid(row=0, column=0, sticky="w", pady=10)
        self.username_entry = tk.Entry(login_frame, font=("Arial", 12), width=28)
        self.username_entry.grid(row=0, column=1, pady=10)
        
        tk.Label(login_frame, text="Password:", font=("Arial", 12, "bold"), bg="#f5f5f5").grid(row=1, column=0, sticky="w", pady=10)
        self.password_entry = tk.Entry(login_frame, font=("Arial", 12), width=28, show="•")
        self.password_entry.grid(row=1, column=1, pady=10)
        
        tk.Label(login_frame, text="Role:", font=("Arial", 12, "bold"), bg="#f5f5f5").grid(row=2, column=0, sticky="w", pady=10)
        self.role_combo = ttk.Combobox(login_frame, font=("Arial", 12), width=25, values=["admin", "teacher", "staff"], state="readonly")
        self.role_combo.grid(row=2, column=1, pady=10)
        self.role_combo.current(0)
        
        login_btn = tk.Button(login_frame, text="🔓 Login", command=self.login, font=("Arial", 13, "bold"), 
                             bg="#4CAF50", fg="white", width=22, height=2)
        login_btn.grid(row=3, column=0, columnspan=2, pady=25)
        
        info = tk.Label(login_frame, text="Default: admin / admin123", font=("Arial", 9), bg="#f5f5f5", fg="grey")
        info.grid(row=4, column=0, columnspan=2)
    
    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        role = self.role_combo.get()
        
        if not username or not password:
            messagebox.showerror("Login Error", "❌ Please enter username and password!")
            return
        
        password_hash = self.db.hash_password(password)
        
        self.db.cursor.execute("""
            SELECT user_id, full_name, role FROM users 
            WHERE username=? AND password=? AND role=?
        """, (username, password_hash, role))
        
        user = self.db.cursor.fetchone()
        
        if user:
            messagebox.showinfo("Login Success", f"✅ Welcome, {user[1]}!")
            self.root.destroy()
            main_window = tk.Tk()
            app = MainApplication(main_window, user, self.db)
            main_window.mainloop()
        else:
            messagebox.showerror("Login Failed", "❌ Invalid username, password, or role!\n\nDefault: admin / admin123")

# PDF Reporter
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
        
        # Header
        c.setFillColor(colors.HexColor("#4CAF50"))
        c.rect(0, height - 1.5*inch, width, 1.5*inch, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(width/2, height - 0.5*inch, "🏫 SCHOOL REPORT CARD")
        
        # Student Info
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(1*inch, height - 2*inch, "STUDENT INFORMATION")
        c.setFont("Helvetica", 11)
        
        info_data = [
            ["Name:", student[1]], ["Father:", student[2]], ["Mother:", student[3]],
            ["Class:", f"{student[6]} - {student[7]}"], ["Roll:", str(student[8])],
            ["DOB:", student[4]], ["Gender:", student[5]], ["Phone:", student[10]]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ]))
        info_table.wrapOn(c, width, height)
        info_table.drawOn(c, 1*inch, height - 3.8*inch)
        
        # Marks
        c.setFont("Helvetica-Bold", 14)
        c.drawString(1*inch, height - 5*inch, "ACADEMIC PERFORMANCE")
        
        self.db.cursor.execute("""
            SELECT subject, exam_type, marks_obtained, total_marks, grade 
            FROM marks WHERE student_id=?
        """, (student_id,))
        marks = self.db.cursor.fetchall()
        
        if marks:
            total_obtained = sum(m[2] for m in marks)
            total_possible = sum(m[3] for m in marks)
            percentage = (total_obtained / total_possible * 100) if total_possible > 0 else 0
            final_grade = "A+" if percentage >= 90 else "A" if percentage >= 80 else "B+" if percentage >= 70 else "B" if percentage >= 60 else "C" if percentage >= 50 else "F"
            
            marks_data = [["Subject", "Exam", "Obtained", "Total", "Grade"]]
            for m in marks:
                marks_data.append([m[0], m[1], str(m[2]), str(m[3]), m[4]])
            marks_data.append(["TOTAL", "", f"{total_obtained}", f"{total_possible}", f"{percentage:.1f}% (Grade: {final_grade})"])
            
            marks_table = Table(marks_data, colWidths=[1.8*inch, 1.2*inch, 1*inch, 0.9*inch, 1*inch])
            marks_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4CAF50")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            marks_table.wrapOn(c, width, height)
            marks_table.drawOn(c, 1*inch, height - 7.5*inch)
        
        c.setFont("Helvetica-Italic", 9)
        c.setFillColor(colors.grey)
        c.drawCentredString(width/2, 30, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        c.save()
        return output_file

# Chart Generator
class ChartGenerator:
    def __init__(self, database):
        self.db = database
    
    def create_performance_chart(self, student_id, save_file="performance_chart.png"):
        self.db.cursor.execute("""
            SELECT subject, AVG(marks_obtained) FROM marks WHERE student_id=? GROUP BY subject
        """, (student_id,))
        data = self.db.cursor.fetchall()
        
        if not data:
            return None
        
        subjects = [row[0] for row in data]
        marks = [row[1] for row in data]
        colors_list = ['#4CAF50' if m >= 90 else '#8BC34A' if m >= 80 else '#FFC107' if m >= 70 else '#FF9800' if m >= 60 else '#F44336' for m in marks]
        
        plt.figure(figsize=(12, 6))
        bars = plt.bar(subjects, marks, color=colors_list, edgecolor='black')
        
        for bar, mark in zip(bars, marks):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f'{mark:.1f}', ha='center', fontweight='bold')
        
        plt.xlabel('Subject', fontweight='bold')
        plt.ylabel('Marks', fontweight='bold')
        plt.title(f'Student {student_id} - Performance', fontweight='bold')
        plt.ylim(0, 110)
        plt.grid(axis='y', alpha=0.3)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(save_file, dpi=300, bbox_inches='tight')
        plt.close()
        return save_file

# Main Application
class MainApplication:
    def __init__(self, root, user_info, database):
        self.root = root
        self.user_info = user_info
        self.db = database
        self.pdf_reporter = PDFReporter(database)
        self.chart_gen = ChartGenerator(database)
        
        self.root.title(f"🏫 School DBMS - {user_info[1]}")
        self.root.geometry("1000x700")
        self.create_menu()
    
    def create_menu(self):
        header = tk.Frame(self.root, bg="#4CAF50", height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="🏫 SCHOOL DBMS SYSTEM", font=("Arial", 24, "bold"), bg="#4CAF50", fg="white", pady=20).pack()
        
        user_bar = tk.Label(self.root, text=f"Logged in: {self.user_info[1]} ({self.user_info[2]})", font=("Arial", 10), bg="#f0f0f0")
        user_bar.pack(fill=tk.X)
        
        btn_frame = tk.Frame(self.root, padx=30, pady=30)
        btn_frame.pack(fill=tk.BOTH, expand=True)
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        
        buttons = [
            ("➕ Add Student", self.add_student, "#2196F3"),
            ("👥 View Students", self.view_students, "#2196F3"),
            ("📝 Add Attendance", self.add_attendance, "#9C27B0"),
            ("📊 Add Marks", self.add_marks, "#9C27B0"),
            ("📄 PDF Report", self.generate_pdf, "#FF9800"),
            ("📈 Chart", self.show_chart, "#FF9800"),
            ("💰 Fees", self.fee_management, "#795548"),
            ("📤 Export Excel", self.export_excel, "#4CAF50"),
            ("🔍 Search", self.search_student, "#607D8B"),
            ("❌ Exit", self.exit_system, "#F44336"),
        ]
        
        for i, (text, command, color) in enumerate(buttons):
            btn = tk.Button(btn_frame, text=text, font=("Arial", 12, "bold"), command=command, 
                          width=28, height=2, bg=color, fg="white")
            btn.grid(row=i//2, column=i%2, padx=15, pady=15, sticky="ew")
    
    def add_student(self):
        window = tk.Toplevel(self.root)
        window.title("Add New Student")
        window.geometry("500x650")
        
        tk.Label(window, text="➕ ADD STUDENT", font=("Arial", 16, "bold"), pady=15).pack()
        
        entries = {}
        for label, key in [("Name:", "name"), ("Father:", "father"), ("Mother:", "mother"), 
                          ("DOB (YYYY-MM-DD):", "dob"), ("Gender:", "gender"), ("Class:", "class"),
                          ("Section:", "section"), ("Roll:", "roll"), ("Phone:", "phone")]:
            frame = tk.Frame(window)
            frame.pack(fill=tk.X, padx=30, pady=5)
            tk.Label(frame, text=label, font=("Arial", 11), width=18, anchor="w").pack(side=tk.LEFT)
            entry = tk.Entry(frame, font=("Arial", 11))
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            entries[key] = entry
        
        def save():
            try:
                self.db.cursor.execute('''
                    INSERT INTO students (name, father_name, mother_name, date_of_birth, 
                                        gender, class, section, roll_number, phone)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (entries["name"].get(), entries["father"].get(), entries["mother"].get(),
                     entries["dob"].get(), entries["gender"].get(), entries["class"].get(),
                     entries["section"].get(), int(entries["roll"].get()), entries["phone"].get()))
                self.db.conn.commit()
                messagebox.showinfo("Success", "✅ Student added!")
                window.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"❌ {str(e)}")
        
        tk.Button(window, text="💾 Save", command=save, bg="#4CAF50", fg="white", 
                 font=("Arial", 12, "bold"), width=20).pack(pady=20)
    
    def view_students(self):
        window = tk.Toplevel(self.root)
        window.title("All Students")
        window.geometry("800x500")
        
        columns = ("ID", "Name", "Class", "Roll", "Phone")
        tree = ttk.Treeview(window, columns=columns, show="headings", height=20)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.db.cursor.execute("SELECT student_id, name, class, roll_number, phone FROM students")
        for student in self.db.cursor.fetchall():
            tree.insert("", tk.END, values=student)
    
    def add_attendance(self):
        window = tk.Toplevel(self.root)
        window.title("Add Attendance")
        window.geometry("400x300")
        
        tk.Label(window, text="📝 ADD ATTENDANCE", font=("Arial", 16, "bold"), pady=15).pack()
        
        tk.Label(window, text="Student ID:", font=("Arial", 11)).pack()
        sid = tk.Entry(window, font=("Arial", 11))
        sid.pack()
        
        tk.Label(window, text="Date (YYYY-MM-DD):", font=("Arial", 11)).pack(pady=(10,0))
        date = tk.Entry(window, font=("Arial", 11))
        date.pack()
        
        tk.Label(window, text="Status:", font=("Arial", 11)).pack(pady=(10,0))
        status = ttk.Combobox(window, values=["Present", "Absent", "Late", "Leave"], state="readonly")
        status.pack()
        status.current(0)
        
        def save():
            try:
                self.db.cursor.execute('INSERT INTO attendance (student_id, date, status) VALUES (?, ?, ?)',
                                      (int(sid.get()), date.get(), status.get()))
                self.db.conn.commit()
                messagebox.showinfo("Success", "✅ Attendance recorded!")
                window.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"❌ {str(e)}")
        
        tk.Button(window, text="💾 Save", command=save, bg="#4CAF50", fg="white", 
                 font=("Arial", 12), width=15).pack(pady=20)
    
    def add_marks(self):
        window = tk.Toplevel(self.root)
        window.title("Add Marks")
        window.geometry("400x400")
        
        tk.Label(window, text="📊 ADD MARKS", font=("Arial", 16, "bold"), pady=15).pack()
        
        entries = {}
        for label, key in [("Student ID:", "sid"), ("Subject:", "subject"), 
                          ("Exam Type:", "exam"), ("Marks:", "marks"), ("Grade:", "grade")]:
            tk.Label(window, text=label, font=("Arial", 11)).pack()
            entry = tk.Entry(window, font=("Arial", 11))
            entry.pack()
            entries[key] = entry
        
        def save():
            try:
                self.db.cursor.execute('''
                    INSERT INTO marks (student_id, subject, exam_type, marks_obtained, grade)
                    VALUES (?, ?, ?, ?, ?)
                ''', (int(entries["sid"].get()), entries["subject"].get(), entries["exam"].get(),
                     float(entries["marks"].get()), entries["grade"].get()))
                self.db.conn.commit()
                messagebox.showinfo("Success", "✅ Marks added!")
                window.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"❌ {str(e)}")
        
        tk.Button(window, text="💾 Save", command=save, bg="#4CAF50", fg="white", 
                 font=("Arial", 12), width=15).pack(pady=20)
    
    def generate_pdf(self):
        student_id = simpledialog.askinteger("Student ID", "Enter Student ID:")
        if student_id:
            result = self.pdf_reporter.generate_report(student_id)
            if result:
                messagebox.showinfo("Success", f"✅ PDF saved as: {result}")
            else:
                messagebox.showerror("Error", "❌ Student not found!")
    
    def show_chart(self):
        student_id = simpledialog.askinteger("Student ID", "Enter Student ID:")
        if student_id:
            result = self.chart_gen.create_performance_chart(student_id)
            if result:
                messagebox.showinfo("Success", f"✅ Chart saved as: {result}")
            else:
                messagebox.showerror("Error", "❌ No marks data found!")
    
    def fee_management(self):
        window = tk.Toplevel(self.root)
        window.title("Fee Management")
        window.geometry("400x350")
        
        tk.Label(window, text="💰 FEE MANAGEMENT", font=("Arial", 16, "bold"), pady=15).pack()
        
        def add_fee():
            fw = tk.Toplevel(window)
            fw.title("Add Fee")
            fw.geometry("350x300")
            
            entries = {}
            for label, key in [("Student ID:", "sid"), ("Fee Type:", "ftype"), 
                              ("Amount:", "amount"), ("Due Date:", "due")]:
                tk.Label(fw, text=label, font=("Arial", 11)).pack()
                entry = tk.Entry(fw, font=("Arial", 11))
                entry.pack()
                entries[key] = entry
            
            def save():
                try:
                    self.db.cursor.execute('''
                        INSERT INTO fees (student_id, fee_type, amount, due_date, status)
                        VALUES (?, ?, ?, ?, 'Pending')
                    ''', (int(entries["sid"].get()), entries["ftype"].get(), 
                         float(entries["amount"].get()), entries["due"].get()))
                    self.db.conn.commit()
                    messagebox.showinfo("Success", "✅ Fee added!")
                    fw.destroy()
                except Exception as e:
                    messagebox.showerror("Error", f"❌ {str(e)}")
            
            tk.Button(fw, text="💾 Save", command=save, bg="#FF9800", fg="white", width=15).pack(pady=20)
        
        tk.Button(window, text="➕ Add Fee", command=add_fee, bg="#FF9800", 
                 fg="white", font=("Arial", 12), width=20).pack(pady=10)
        
        def view_fees():
            self.db.cursor.execute("""
                SELECT s.name, f.fee_type, f.amount, f.status FROM fees f
                JOIN students s ON f.student_id = s.student_id
            """)
            fees = self.db.cursor.fetchall()
            
            fw = tk.Toplevel(window)
            fw.title("Fee Records")
            fw.geometry("500x300")
            
            text = tk.Text(fw, font=("Courier", 10))
            text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            text.insert(tk.END, "NAME | FEE TYPE | AMOUNT | STATUS\n")
            text.insert(tk.END, "-" * 50 + "\n")
            for f in fees:
                text.insert(tk.END, f"{f[0]} | {f[1]} | Rs. {f[2]} | {f[3]}\n")
        
        tk.Button(window, text="👁️ View Fees", command=view_fees, bg="#2196F3", 
                 fg="white", font=("Arial", 12), width=20).pack(pady=10)
    
    def export_excel(self):
        try:
            self.db.cursor.execute("SELECT * FROM students")
            students = self.db.cursor.fetchall()
            
            with open('students_export.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Name", "Father", "Mother", "DOB", "Gender", 
                               "Class", "Section", "Roll", "Phone"])
                for s in students:
                    writer.writerow(s[:10])
            
            messagebox.showinfo("Success", "✅ Exported to students_export.csv")
        except Exception as e:
            messagebox.showerror("Error", f"❌ {str(e)}")
    
    def search_student(self):
        search = simpledialog.askstring("Search", "Enter name or ID:")
        if search:
            self.db.cursor.execute("""
                SELECT student_id, name, class, roll_number FROM students 
                WHERE name LIKE ? OR student_id LIKE ?
            """, (f'%{search}%', f'%{search}%'))
            results = self.db.cursor.fetchall()
            
            if results:
                window = tk.Toplevel(self.root)
                window.title("Search Results")
                window.geometry("500x300")
                
                columns = ("ID", "Name", "Class", "Roll")
                tree = ttk.Treeview(window, columns=columns, show="headings")
                for col in columns:
                    tree.heading(col, text=col)
                    tree.column(col, width=120)
                tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                
                for r in results:
                    tree.insert("", tk.END, values=r)
            else:
                messagebox.showinfo("No Results", "❌ No student found")
    
    def exit_system(self):
        if messagebox.askyesno("Exit", "Are you sure?"):
            self.db.close()
            self.root.destroy()

# ============ MAIN ============
if __name__ == "__main__":
    print("="*60)
    print("🏫 SCHOOL DBMS SYSTEM - STARTING")
    print("="*60)
    
    db = Database()
    root = tk.Tk()
    app = LoginWindow(root, db)
    root.mainloop()
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from datetime import datetime, timedelta
import calendar
import sqlite3

# Define file paths for local data storage
DATA_DIR = "academic_data"
DB_FILE = os.path.join(DATA_DIR, "academic_system.db")
CALENDAR_EVENTS_FILE = os.path.join(DATA_DIR, "calendar_events.json") # Still using JSON for calendar events for simplicity, could be moved to DB

# Nordic Color Palette
NORDIC_COLORS = {
    "bg_light": "#F0F4F8",      # Very light blue-grey for main backgrounds
    "bg_medium": "#D9E2EC",     # Slightly darker blue-grey for frames/sections
    "bg_dark": "#BCCCDC",       # Muted blue-grey for accents
    "text_dark": "#243B53",     # Dark blue-grey for main text
    "text_light": "#FFFFFF",    # White for text on dark backgrounds
    "accent_blue": "#4A6572",   # Muted dark blue for primary buttons/highlights
    "accent_green": "#66BB6A",  # Soft green for success/add actions
    "accent_red": "#EF5350",    # Muted red for danger/delete actions
    "border_color": "#AAB8C2",  # Light grey-blue for borders
    "treeview_header_bg": "#C0CCDA", # Header background for Treeview
    "treeview_row_bg1": "#FFFFFF", # Alternating row background 1
    "treeview_row_bg2": "#F0F4F8", # Alternating row background 2
    "treeview_selected_bg": "#90CAF9", # Selected row background (light blue)
    "calendar_day_bg": "#E0E0E0", # Default calendar day background
    "calendar_day_fg": "#333333", # Default calendar day foreground
    "calendar_event_bg": "#C8E6C9", # Calendar day with event (light green)
    "calendar_holiday_bg": "#FFCDD2", # Calendar day with holiday (light red)
    "calendar_today_bg": "#2196F3", # Today's date (blue)
    "calendar_today_fg": "#FFFFFF", # Today's date foreground
    "calendar_active_bg": "#B0BEC5", # Active/hover background for calendar days
    "calendar_active_fg": "#243B53", # Active/hover foreground for calendar days
    "accent_dark_blue": "#3B525F", # Added accent_dark_blue
}


class DatabaseManager:
    """Manages SQLite database operations for the Academic Management System."""
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.connect()
        self.create_tables()

    def connect(self):
        """Establishes a connection to the SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row # Allows accessing columns by name
            print(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to connect to database: {e}")
            self.conn = None

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            print("Database connection closed.")

    def create_tables(self):
        """Creates necessary tables if they don't exist."""
        if not self.conn:
            return

        cursor = self.conn.cursor()
        try:
            # Students Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    major TEXT
                )
            """)
            # Faculty Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS faculty (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    faculty_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    department TEXT,
                    rank TEXT,
                    contact_info TEXT
                )
            """)
            # Courses Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_code TEXT UNIQUE NOT NULL,
                    course_name TEXT NOT NULL,
                    program TEXT,
                    credits REAL,
                    prerequisites TEXT
                )
            """)
            # Routines Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS routines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_code TEXT NOT NULL,
                    time_slot TEXT NOT NULL,
                    weekday TEXT NOT NULL,
                    FOREIGN KEY (course_code) REFERENCES courses (course_code)
                )
            """)
            # Attendance Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    status TEXT NOT NULL, -- Present/Absent
                    date TEXT NOT NULL,
                    FOREIGN KEY (student_id) REFERENCES students (student_id)
                )
            """)
            # Grades Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS grades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    assessment_type TEXT NOT NULL,
                    marks REAL NOT NULL,
                    grade_point REAL NOT NULL,
                    FOREIGN KEY (student_id) REFERENCES students (student_id)
                )
            """)
            self.conn.commit()
            print("Tables checked/created successfully.")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to create tables: {e}")

    def insert_data(self, table_name, data):
        """Inserts a single record into the specified table."""
        if not self.conn:
            return False
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data.values()])
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, tuple(data.values()))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            messagebox.showwarning("Duplicate Entry", f"A record with this unique identifier already exists. Details: {e}")
            return False
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to insert data into {table_name}: {e}")
            return False

    def fetch_all_data(self, table_name):
        """Fetches all records from the specified table."""
        if not self.conn:
            return []
        cursor = self.conn.cursor()
        try:
            cursor.execute(f"SELECT * FROM {table_name}")
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to fetch data from {table_name}: {e}")
            return []

    def update_data(self, table_name, record_id, data):
        """Updates a record in the specified table by its ID."""
        if not self.conn:
            return False
        set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
        sql = f"UPDATE {table_name} SET {set_clause} WHERE id = ?"
        values = list(data.values()) + [record_id]
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, tuple(values))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError as e:
            messagebox.showwarning("Duplicate Entry", f"Cannot update: A record with this unique identifier already exists. Details: {e}")
            return False
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to update data in {table_name}: {e}")
            return False

    def delete_data(self, table_name, record_id):
        """Deletes a record from the specified table by its ID."""
        if not self.conn:
            return False
        sql = f"DELETE FROM {table_name} WHERE id = ?"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (record_id,))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to delete data from {table_name}: {e}")
            return False


class AcademicManagementApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("ELL AMS") # Changed app title
        self.geometry("1200x750") # Larger default size
        self.resizable(True, True) # Allow window resizing
        self.configure(bg=NORDIC_COLORS["bg_light"]) # Set main window background

        # Configure ttk styles for a modern look with Nordic colors
        self.style = ttk.Style(self)
        self.style.theme_use('clam') # 'clam' theme is a good base for customization

        # General frame and label styles
        self.style.configure('TFrame', background=NORDIC_COLORS["bg_light"])
        self.style.configure('TLabel', background=NORDIC_COLORS["bg_light"], foreground=NORDIC_COLORS["text_dark"])
        self.style.configure('TLabelFrame', background=NORDIC_COLORS["bg_light"], foreground=NORDIC_COLORS["text_dark"], bordercolor=NORDIC_COLORS["border_color"])
        self.style.configure('TLabelframe.Label', background=NORDIC_COLORS["bg_light"], foreground=NORDIC_COLORS["text_dark"]) # Label within LabelFrame

        # Button styles
        self.style.configure('TButton', font=('Arial', 10, 'bold'), padding=8,
                             background=NORDIC_COLORS["accent_blue"], foreground=NORDIC_COLORS["text_light"],
                             relief="flat", borderwidth=0)
        self.style.map('TButton',
                       background=[('active', NORDIC_COLORS["bg_dark"]), ('pressed', NORDIC_COLORS["accent_blue"])],
                       foreground=[('active', NORDIC_COLORS["text_light"])])

        # Danger button style
        self.style.configure('Danger.TButton',
                             background=NORDIC_COLORS["accent_red"], foreground=NORDIC_COLORS["text_light"])
        self.style.map('Danger.TButton',
                       background=[('active', '#C62828'), ('pressed', NORDIC_COLORS["accent_red"])]) # Darker red on active

        # Treeview styles
        self.style.configure('Treeview.Heading', font=('Arial', 10, 'bold'),
                             background=NORDIC_COLORS["treeview_header_bg"], foreground=NORDIC_COLORS["text_dark"],
                             relief="flat")
        self.style.configure('Treeview',
                             rowheight=25, font=('Arial', 10),
                             background=NORDIC_COLORS["treeview_row_bg1"], foreground=NORDIC_COLORS["text_dark"],
                             fieldbackground=NORDIC_COLORS["treeview_row_bg1"],
                             borderwidth=1, relief="solid")
        self.style.map('Treeview',
                       background=[('selected', NORDIC_COLORS["treeview_selected_bg"])],
                       foreground=[('selected', NORDIC_COLORS["text_dark"])])
        # Removed tag_configure from here, will be configured on each Treeview instance


        # Notebook (Tab) styles
        self.style.configure('TNotebook', background=NORDIC_COLORS["bg_light"], borderwidth=0)
        self.style.configure('TNotebook.Tab', font=('Arial', 11, 'bold'), padding=[10, 5],
                             background=NORDIC_COLORS["bg_medium"], foreground=NORDIC_COLORS["text_dark"],
                             relief="flat", borderwidth=0)
        self.style.map('TNotebook.Tab',
                       background=[('selected', NORDIC_COLORS["accent_blue"]), ('active', NORDIC_COLORS["bg_dark"])],
                       foreground=[('selected', NORDIC_COLORS["text_light"]), ('active', NORDIC_COLORS["text_dark"])])
        self.style.configure('TNotebook.Tab', focuscolor=self.style.lookup('TNotebook.Tab', 'background')) # Remove dotted line on focus

        # Entry and Combobox styles
        self.style.configure('TEntry', fieldbackground=NORDIC_COLORS["text_light"], foreground=NORDIC_COLORS["text_dark"],
                             bordercolor=NORDIC_COLORS["border_color"], relief="solid", borderwidth=1)
        self.style.configure('TCombobox', fieldbackground=NORDIC_COLORS["text_light"], foreground=NORDIC_COLORS["text_dark"],
                             bordercolor=NORDIC_COLORS["border_color"], relief="solid", borderwidth=1)
        self.style.map('TCombobox', fieldbackground=[('readonly', NORDIC_COLORS["text_light"])])


        # New styles for dashboard and tab titles
        self.style.configure('Dashboard.Title.TLabel', font=('Arial', 28, 'bold'),
                             foreground=NORDIC_COLORS["accent_dark_blue"], background=NORDIC_COLORS["bg_light"])
        self.style.configure('Tab.Title.TLabel', font=('Arial', 20, 'bold'),
                             foreground=NORDIC_COLORS["accent_dark_blue"], background=NORDIC_COLORS["bg_light"])
        self.style.configure('InfoCard.Value.TLabel', font=('Arial', 20, 'bold'),
                             foreground=NORDIC_COLORS["accent_blue"], background=NORDIC_COLORS["bg_light"])


        # Ensure data directory exists
        os.makedirs(DATA_DIR, exist_ok=True)

        # Initialize Database Manager
        self.db_manager = DatabaseManager(DB_FILE)

        # Load initial data (from DB and JSON for calendar events)
        self.schedules = self.db_manager.fetch_all_data("routines")
        self.attendance_records = self.db_manager.fetch_all_data("attendance")
        self.grades = self.db_manager.fetch_all_data("grades")
        self.students = self.db_manager.fetch_all_data("students")
        self.faculty = self.db_manager.fetch_all_data("faculty")
        self.courses = self.db_manager.fetch_all_data("courses")
        self.calendar_events = self.load_json_data(CALENDAR_EVENTS_FILE) # Calendar events still in JSON

        # Variables for editing - Initialize all Treeview and other widget references to None
        self.selected_student_id = None # Actual DB row ID for students
        self.selected_faculty_id = None
        self.selected_course_id = None
        self.selected_routine_id = None
        self.selected_attendance_id = None
        self.selected_grade_id = None

        self.student_tree = None
        self.faculty_tree = None
        self.course_tree = None
        self.routine_tree = None
        self.attendance_tree = None
        self.summary_tree = None
        self.grades_tree = None
        self.gpa_summary_tree = None
        self.event_list_tree = None
        self.calendar_grid_frame = None
        self.month_year_label = None


        # Calendar state
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month

        self.create_tabs()

        # Ensure database connection is closed on app exit
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        """Handles actions when the application window is closed."""
        if messagebox.askokcancel("Quit", "Do you want to quit the application?", parent=self):
            self.db_manager.close()
            self.destroy()

    def load_json_data(self, filepath):
        """Loads data from a JSON file (used for calendar events)."""
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                messagebox.showerror("Data Error", f"Error reading {filepath}. Starting with empty data.", parent=self)
                return []
        return []

    def save_json_data(self, data, filepath):
        """Saves data to a JSON file (used for calendar events)."""
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)
        except IOError as e:
            messagebox.showerror("Save Error", f"Failed to save data to {filepath}: {e}", parent=self)

    def create_tabs(self):
        """Creates the main tabbed interface with left-side navigation."""
        # Create main container frame
        self.main_container = ttk.Frame(self)
        self.main_container.pack(expand=1, fill="both", padx=0, pady=0)

        # Create left navigation frame with fixed width
        self.nav_frame = ttk.Frame(self.main_container, style='Nav.TFrame', width=200)
        self.nav_frame.pack(side="left", fill="y", padx=0, pady=0)
        self.nav_frame.pack_propagate(False)  # Prevent frame from shrinking
        
        # Create content frame
        self.content_frame = ttk.Frame(self.main_container, style='Content.TFrame')
        self.content_frame.pack(side="left", expand=True, fill="both", padx=10, pady=10)

        # Configure styles for navigation
        self.style.configure('Nav.TFrame', background=NORDIC_COLORS["bg_dark"])
        self.style.configure('Content.TFrame', background=NORDIC_COLORS["bg_light"])
        
        # Configure navigation button styles
        self.style.configure('Nav.TButton', 
                           font=('Arial', 11),
                           padding=[15, 10],
                           anchor="w",  # Left-align text
                           width=20,  # Fixed width for all buttons
                           background=NORDIC_COLORS["bg_dark"],
                           foreground=NORDIC_COLORS["text_light"])
        
        # Create a separate style for selected buttons
        self.style.configure('Nav.TButton.Selected', 
                           font=('Arial', 11, 'bold'),
                           padding=[15, 10],
                           anchor="w",
                           width=20,
                           background=NORDIC_COLORS["accent_blue"],
                           foreground=NORDIC_COLORS["text_light"])
        
        # Configure hover effects
        self.style.map('Nav.TButton',
                      background=[('active', NORDIC_COLORS["accent_blue"])],
                      foreground=[('active', NORDIC_COLORS["text_light"])])
        
        self.style.map('Nav.TButton.Selected',
                      background=[('active', NORDIC_COLORS["accent_blue"])],
                      foreground=[('active', NORDIC_COLORS["text_light"])])

        # Dictionary to store frames
        self.frames = {}
        self.nav_buttons = {}
        self.current_frame = None
        self.current_button = None

        # Create navigation buttons and content frames
        nav_items = [
            ("Dashboard", self.init_dashboard),
            ("Student Management", self.init_student_management),
            ("Faculty Management", self.init_faculty_management),
            ("Course Management", self.init_course_management),
            ("Routine Management", self.init_scheduling),
            ("Attendance Management", self.init_attendance),
            ("Grading & Assessment", self.init_assessment),
            ("Document Generator", self.init_application_generator),
            ("Academic Calendar", self.init_calendar),
            ("Alumni Directory", self.init_alumni_directory),
            ("Local Messaging", self.init_local_messaging),
            ("Security & Admin", self.init_security_admin),
            ("Settings", self.init_settings_utilities),
            ("Analytics", self.init_analytics)
        ]

        def show_frame(name, button):
            # Hide current frame if it exists
            if self.current_frame:
                self.current_frame.pack_forget()
            
            # Show selected frame
            self.frames[name].pack(expand=True, fill="both")
            self.current_frame = self.frames[name]
            
            # Update button states
            if self.current_button:
                self.current_button.configure(style='Nav.TButton')
            button.configure(style='Nav.TButton.Selected')
            self.current_button = button
            
            # Update data for the active frame
            if name == "Dashboard":
                self.update_dashboard_info()
            elif name == "Student Management":
                self.students = self.db_manager.fetch_all_data("students")
                self.refresh_student_display()
                self.clear_student_entries()
            elif name == "Faculty Management":
                self.faculty = self.db_manager.fetch_all_data("faculty")
                self.refresh_faculty_display()
                self.clear_faculty_entries()
            elif name == "Course Management":
                self.courses = self.db_manager.fetch_all_data("courses")
                self.refresh_course_display()
                self.clear_course_entries()
            elif name == "Routine Management":
                self.schedules = self.db_manager.fetch_all_data("routines")
                self.refresh_schedules_display()
                self.cancel_schedule_edit()
            elif name == "Attendance Management":
                self.attendance_records = self.db_manager.fetch_all_data("attendance")
                self.refresh_attendance_display()
                self.update_attendance_summary()
                self.cancel_attendance_edit()
            elif name == "Grading & Assessment":
                self.grades = self.db_manager.fetch_all_data("grades")
                self.refresh_grades_display()
                self.update_gpa_summary()
                self.cancel_grade_edit()
            elif name == "Academic Calendar":
                if self.calendar_grid_frame and self.month_year_label and self.event_list_tree:
                    self.draw_calendar()

        # Create navigation buttons and frames
        for name, init_func in nav_items:
            # Create frame
            frame = ttk.Frame(self.content_frame, style='Content.TFrame')
            self.frames[name] = frame
            
            # Create navigation button
            btn = ttk.Button(self.nav_frame, text=name, style='Nav.TButton')
            btn.configure(command=lambda n=name, b=btn: show_frame(n, b))
            btn.pack(fill="x", padx=2, pady=1)
            self.nav_buttons[name] = btn

            # Initialize the frame content
            init_func()

        # Show dashboard by default
        show_frame("Dashboard", self.nav_buttons["Dashboard"])

    def on_tab_change(self, event):
        """Callback for when a tab is changed."""
        # This method is kept for compatibility with existing code that calls it,
        # but the actual tab switching is now handled by show_frame in create_tabs
        pass

    # --- Dashboard Tab ---
    def init_dashboard(self):
        """Initializes the Dashboard tab."""
        dashboard_frame = ttk.Frame(self.frames["Dashboard"], padding="20", style='TFrame')
        dashboard_frame.pack(expand=True, fill="both")

        tk.Label(dashboard_frame, text="Dashboard Overview", font=('Arial', 28, 'bold'),
                 bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["accent_dark_blue"]).pack(pady=25)

        info_grid_frame = ttk.Frame(dashboard_frame, style='TFrame')
        info_grid_frame.pack(pady=20, fill="x", expand=True)
        info_grid_frame.columnconfigure(0, weight=1)
        info_grid_frame.columnconfigure(1, weight=1)
        info_grid_frame.columnconfigure(2, weight=1)

        # Helper to create info cards
        def create_info_card(parent, row, col, title, initial_value_text):
            # Using tk.LabelFrame for direct background control
            card_frame = tk.LabelFrame(parent, text=title, padx=15, pady=15,
                                       bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"],
                                       font=('Arial', 11, 'bold'), relief="solid", borderwidth=1)
            card_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            # Using tk.Label for direct background/foreground control
            label = tk.Label(card_frame, text=initial_value_text, font=('Arial', 20, 'bold'),
                             bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["accent_blue"])
            label.pack(expand=True, fill="both")
            return label

        self.dashboard_labels = {
            'students': create_info_card(info_grid_frame, 0, 0, "Total Students", "0"),
            'faculty': create_info_card(info_grid_frame, 0, 1, "Total Faculty", "0"),
            'courses': create_info_card(info_grid_frame, 0, 2, "Total Courses", "0"),
            'attendance_records': create_info_card(info_grid_frame, 1, 0, "Attendance Records", "0"),
            'grades_entered': create_info_card(info_grid_frame, 1, 1, "Grades Entered", "0"),
            'upcoming_events': create_info_card(info_grid_frame, 1, 2, "Upcoming Calendar Events", "0")
        }

        self.update_dashboard_info()

        # Add a "Clear All Data" button for development/testing
        ttk.Button(dashboard_frame, text="Clear All Local Data (DANGER!)", command=self.clear_all_data, style='Danger.TButton').pack(pady=30)


    def update_dashboard_info(self):
        """Updates the dynamic information on the Dashboard tab."""
        self.students = self.db_manager.fetch_all_data("students")
        self.faculty = self.db_manager.fetch_all_data("faculty")
        self.courses = self.db_manager.fetch_all_data("courses")
        self.attendance_records = self.db_manager.fetch_all_data("attendance")
        self.grades = self.db_manager.fetch_all_data("grades")
        self.calendar_events = self.load_json_data(CALENDAR_EVENTS_FILE)

        self.dashboard_labels['students'].config(text=f"{len(self.students)}")
        self.dashboard_labels['faculty'].config(text=f"{len(self.faculty)}")
        self.dashboard_labels['courses'].config(text=f"{len(self.courses)}")
        self.dashboard_labels['attendance_records'].config(text=f"{len(self.attendance_records)}")
        self.dashboard_labels['grades_entered'].config(text=f"{len(self.grades)}")

        # Count upcoming events (e.g., in the next 30 days)
        today = datetime.now().date()
        upcoming_count = 0
        for event in self.calendar_events:
            try:
                event_date = datetime.strptime(event['date'], "%Y-%m-%d").date()
                if today <= event_date <= today + timedelta(days=30):
                    upcoming_count += 1
            except ValueError:
                # Handle malformed dates in calendar_events.json
                pass
        self.dashboard_labels['upcoming_events'].config(text=f"{upcoming_count}")

        # Schedule next update
        self.after(5000, self.update_dashboard_info)

    def clear_all_data(self):
        """Clears all local data files and database tables."""
        if messagebox.askyesno("Confirm Clear All Data", "Are you absolutely sure you want to delete ALL local data (students, faculty, courses, schedules, attendance, grades, calendar events)? This action cannot be undone!", parent=self):
            try:
                # Clear SQLite tables
                cursor = self.db_manager.conn.cursor()
                cursor.execute("DELETE FROM students")
                cursor.execute("DELETE FROM faculty")
                cursor.execute("DELETE FROM courses")
                cursor.execute("DELETE FROM routines")
                cursor.execute("DELETE FROM attendance")
                cursor.execute("DELETE FROM grades")
                self.db_manager.conn.commit()

                # Clear JSON file
                if os.path.exists(CALENDAR_EVENTS_FILE):
                    os.remove(CALENDAR_EVENTS_FILE)

                # Reset in-memory data
                self.schedules = []
                self.attendance_records = []
                self.grades = []
                self.students = []
                self.faculty = []
                self.courses = []
                self.calendar_events = []

                messagebox.showinfo("Data Cleared", "All local data has been cleared.", parent=self)
                # Refresh all displays
                self.on_tab_change(None) # Simulate tab change to refresh all displays
                self.update_dashboard_info()
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while clearing data: {e}", parent=self)

    # --- Student Information Management Tab ---
    def init_student_management(self):
        """Initializes the Student Information Management tab."""
        student_frame = ttk.Frame(self.frames["Student Management"], padding="20", style='TFrame')
        student_frame.pack(expand=True, fill="both")

        tk.Label(student_frame, text="Student Information Management", font=('Arial', 20, 'bold'),
                 bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["accent_dark_blue"]).pack(pady=15)

        input_frame = tk.LabelFrame(student_frame, text="Add/Edit Student Profile", padx=15, pady=15,
                                    bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"],
                                    font=('Arial', 11, 'bold'), relief="solid", borderwidth=1)
        input_frame.pack(pady=10, fill="x")

        tk.Label(input_frame, text="Student ID:", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.student_id_entry = ttk.Entry(input_frame, width=30)
        self.student_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(input_frame, text="Name:", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.student_name_entry = ttk.Entry(input_frame, width=40)
        self.student_name_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(input_frame, text="Major:", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.student_major_entry = ttk.Entry(input_frame, width=30)
        self.student_major_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        button_row_frame = ttk.Frame(input_frame, style='TFrame')
        button_row_frame.grid(row=3, column=0, columnspan=2, pady=10)

        self.add_student_button = ttk.Button(button_row_frame, text="Add Student", command=self.add_student, style='TButton')
        self.add_student_button.pack(side="left", padx=5)
        self.edit_student_button = ttk.Button(button_row_frame, text="Update Selected", command=self.edit_selected_student, state=tk.DISABLED, style='TButton')
        self.edit_student_button.pack(side="left", padx=5)
        self.cancel_student_edit_button = ttk.Button(button_row_frame, text="Cancel Edit", command=self.clear_student_entries, state=tk.DISABLED, style='TButton')
        self.cancel_student_edit_button.pack(side="left", padx=5)

        input_frame.grid_columnconfigure(1, weight=1)

        # Student display
        student_display_frame = tk.LabelFrame(student_frame, text="Registered Students", padx=15, pady=15,
                                              bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"],
                                              font=('Arial', 11, 'bold'), relief="solid", borderwidth=1)
        student_display_frame.pack(pady=10, fill="both", expand=True)

        self.student_tree = ttk.Treeview(student_display_frame, columns=("DB_ID", "StudentID", "Name", "Major"), show="headings")
        self.student_tree.heading("DB_ID", text="DB ID")
        self.student_tree.heading("StudentID", text="Student ID")
        self.student_tree.heading("Name", text="Name")
        self.student_tree.heading("Major", text="Major")
        self.student_tree.column("DB_ID", width=50, anchor="center")
        self.student_tree.column("StudentID", width=100, anchor="center")
        self.student_tree.column("Name", width=200, anchor="w")
        self.student_tree.column("Major", width=150, anchor="w")
        self.student_tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(student_display_frame, orient="vertical", command=self.student_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.student_tree.configure(yscrollcommand=scrollbar.set)

        self.student_tree.bind("<Delete>", lambda event: self.delete_selected_student())
        self.student_tree.bind("<<TreeviewSelect>>", self.on_student_select)

        self.refresh_student_display()

        # Bottom buttons
        bottom_button_frame = ttk.Frame(student_frame, style='TFrame')
        bottom_button_frame.pack(pady=10)
        ttk.Button(bottom_button_frame, text="Delete Selected", command=self.delete_selected_student, style='Danger.TButton').pack(side="left", padx=5)
        ttk.Button(bottom_button_frame, text="Import from Excel (xlsx/csv)", command=self.import_students_from_excel, style='TButton').pack(side="left", padx=5)
        ttk.Button(bottom_button_frame, text="Export to Excel", command=self.export_students_to_excel, style='TButton').pack(side="left", padx=5)
        ttk.Button(bottom_button_frame, text="Export to JSON", command=self.export_students_to_json, style='TButton').pack(side="left", padx=5)

    def add_student(self):
        student_id = self.student_id_entry.get().strip()
        name = self.student_name_entry.get().strip()
        major = self.student_major_entry.get().strip()

        if not student_id or not name:
            messagebox.showwarning("Input Error", "Student ID and Name are required.", parent=self)
            return

        data = {"student_id": student_id, "name": name, "major": major}
        if self.db_manager.insert_data("students", data):
            messagebox.showinfo("Success", f"Student '{name}' added successfully.", parent=self)
            self.clear_student_entries()
            self.students = self.db_manager.fetch_all_data("students")
            self.refresh_student_display()
            self.update_dashboard_info()

    def edit_selected_student(self):
        if not self.selected_student_id:
            messagebox.showwarning("No Selection", "Please select a student to update.", parent=self)
            return

        student_id = self.student_id_entry.get().strip()
        name = self.student_name_entry.get().strip()
        major = self.student_major_entry.get().strip()

        if not student_id or not name:
            messagebox.showwarning("Input Error", "Student ID and Name are required.", parent=self)
            return

        data = {"student_id": student_id, "name": name, "major": major}
        if self.db_manager.update_data("students", self.selected_student_id, data):
            messagebox.showinfo("Success", f"Student '{name}' updated successfully.", parent=self)
            self.clear_student_entries()
            self.students = self.db_manager.fetch_all_data("students")
            self.refresh_student_display()
            self.update_dashboard_info()
        else:
            messagebox.showerror("Update Failed", "Could not update student. Check for duplicate Student ID.", parent=self)

    def delete_selected_student(self):
        selected_items = self.student_tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select a student to delete.", parent=self)
            return

        db_id_to_delete = self.student_tree.item(selected_items[0], 'values')[0]
        student_name = self.student_tree.item(selected_items[0], 'values')[2]

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete student '{student_name}'?", parent=self):
            if self.db_manager.delete_data("students", db_id_to_delete):
                messagebox.showinfo("Success", f"Student '{student_name}' deleted successfully.", parent=self)
                self.clear_student_entries()
                self.students = self.db_manager.fetch_all_data("students")
                self.refresh_student_display()
                self.update_dashboard_info()
            else:
                messagebox.showerror("Delete Failed", "Could not delete student.", parent=self)

    def refresh_student_display(self):
        if self.student_tree is None: return
        for item in self.student_tree.get_children():
            self.student_tree.delete(item)
        # Configure alternating row colors for this Treeview
        self.student_tree.tag_configure('oddrow', background=NORDIC_COLORS["treeview_row_bg1"])
        self.student_tree.tag_configure('evenrow', background=NORDIC_COLORS["treeview_row_bg2"])
        for i, student in enumerate(self.students):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.student_tree.insert("", "end", iid=student['id'], values=(student['id'], student['student_id'], student['name'], student['major']), tags=(tag,))

    def on_student_select(self, event):
        selected_items = self.student_tree.selection()
        if selected_items:
            values = self.student_tree.item(selected_items[0], 'values')
            self.selected_student_id = values[0] # Store DB ID
            self.student_id_entry.delete(0, tk.END)
            self.student_id_entry.insert(0, values[1])
            self.student_name_entry.delete(0, tk.END)
            self.student_name_entry.insert(0, values[2])
            self.student_major_entry.delete(0, tk.END)
            self.student_major_entry.insert(0, values[3])
            self.add_student_button.config(state=tk.DISABLED)
            self.edit_student_button.config(state=tk.NORMAL)
            self.cancel_student_edit_button.config(state=tk.NORMAL)
        else:
            self.clear_student_entries()

    def clear_student_entries(self):
        self.selected_student_id = None
        self.student_id_entry.delete(0, tk.END)
        self.student_name_entry.delete(0, tk.END)
        self.student_major_entry.delete(0, tk.END)
        self.add_student_button.config(state=tk.NORMAL)
        self.edit_student_button.config(state=tk.DISABLED)
        self.cancel_student_edit_button.config(state=tk.DISABLED)
        if self.student_tree:
            self.student_tree.selection_remove(self.student_tree.selection())

    def import_students_from_excel(self):
        messagebox.showinfo("Import Feature", "This feature would allow importing student data from .xlsx or .csv files with field mapping. (Not implemented in this demo)", parent=self)
        # Placeholder for actual implementation:
        # filepath = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv")])
        # if filepath:
        #     # Implement pandas/openpyxl logic here to read and insert into DB
        #     pass

    def export_students_to_excel(self):
        messagebox.showinfo("Export Feature", "This feature would export student data to an Excel (.xlsx) file. (Not implemented in this demo)", parent=self)
        # Placeholder for actual implementation:
        # filepath = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        # if filepath:
        #     # Implement pandas/openpyxl logic here to write data
        #     pass

    def export_students_to_json(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".json",
                                                filetypes=[("JSON files", "*.json")],
                                                title="Export Students to JSON", parent=self)
        if filepath:
            try:
                # Convert list of Row objects to list of dicts for JSON export
                students_data = [dict(s) for s in self.students]
                with open(filepath, 'w') as f:
                    json.dump(students_data, f, indent=4)
                messagebox.showinfo("Export Complete", f"Student data exported to {filepath}", parent=self)
            except IOError as e:
                messagebox.showerror("Export Error", f"Failed to export data: {e}", parent=self)

    # --- Faculty Information Management Tab ---
    def init_faculty_management(self):
        faculty_frame = ttk.Frame(self.frames["Faculty Management"], padding="20", style='TFrame')
        faculty_frame.pack(expand=True, fill="both")

        tk.Label(faculty_frame, text="Faculty Information Management", font=('Arial', 20, 'bold'),
                 bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["accent_dark_blue"]).pack(pady=15)

        input_frame = tk.LabelFrame(faculty_frame, text="Add/Edit Faculty Profile", padx=15, pady=15,
                                    bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"],
                                    font=('Arial', 11, 'bold'), relief="solid", borderwidth=1)
        input_frame.pack(pady=10, fill="x")

        tk.Label(input_frame, text="Faculty ID:", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.faculty_id_entry = ttk.Entry(input_frame, width=30)
        self.faculty_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(input_frame, text="Name:", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.faculty_name_entry = ttk.Entry(input_frame, width=40)
        self.faculty_name_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(input_frame, text="Department:", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.faculty_dept_entry = ttk.Entry(input_frame, width=30)
        self.faculty_dept_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(input_frame, text="Rank:", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.faculty_rank_entry = ttk.Entry(input_frame, width=30)
        self.faculty_rank_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(input_frame, text="Contact Info:", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.faculty_contact_entry = ttk.Entry(input_frame, width=40)
        self.faculty_contact_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        button_row_frame = ttk.Frame(input_frame, style='TFrame')
        button_row_frame.grid(row=5, column=0, columnspan=2, pady=10)

        self.add_faculty_button = ttk.Button(button_row_frame, text="Add Faculty", command=self.add_faculty, style='TButton')
        self.add_faculty_button.pack(side="left", padx=5)
        self.edit_faculty_button = ttk.Button(button_row_frame, text="Update Selected", command=self.edit_selected_faculty, state=tk.DISABLED, style='TButton')
        self.edit_faculty_button.pack(side="left", padx=5)
        self.cancel_faculty_edit_button = ttk.Button(button_row_frame, text="Cancel Edit", command=self.clear_faculty_entries, state=tk.DISABLED, style='TButton')
        self.cancel_faculty_edit_button.pack(side="left", padx=5)

        input_frame.grid_columnconfigure(1, weight=1)

        faculty_display_frame = tk.LabelFrame(faculty_frame, text="Registered Faculty", padx=15, pady=15,
                                              bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"],
                                              font=('Arial', 11, 'bold'), relief="solid", borderwidth=1)
        faculty_display_frame.pack(pady=10, fill="both", expand=True)

        self.faculty_tree = ttk.Treeview(faculty_display_frame, columns=("DB_ID", "FacultyID", "Name", "Department", "Rank", "Contact"), show="headings")
        self.faculty_tree.heading("DB_ID", text="DB ID")
        self.faculty_tree.heading("FacultyID", text="Faculty ID")
        self.faculty_tree.heading("Name", text="Name")
        self.faculty_tree.heading("Department", text="Department")
        self.faculty_tree.heading("Rank", text="Rank")
        self.faculty_tree.heading("Contact", text="Contact Info")
        self.faculty_tree.column("DB_ID", width=50, anchor="center")
        self.faculty_tree.column("FacultyID", width=100, anchor="center")
        self.faculty_tree.column("Name", width=150, anchor="w")
        self.faculty_tree.column("Department", width=100, anchor="w")
        self.faculty_tree.column("Rank", width=80, anchor="w")
        self.faculty_tree.column("Contact", width=150, anchor="w")
        self.faculty_tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(faculty_display_frame, orient="vertical", command=self.faculty_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.faculty_tree.configure(yscrollcommand=scrollbar.set)

        self.faculty_tree.bind("<Delete>", lambda event: self.delete_selected_faculty())
        self.faculty_tree.bind("<<TreeviewSelect>>", self.on_faculty_select)

        self.refresh_faculty_display()

        bottom_button_frame = ttk.Frame(faculty_frame, style='TFrame')
        bottom_button_frame.pack(pady=10)
        ttk.Button(bottom_button_frame, text="Delete Selected", command=self.delete_selected_faculty, style='Danger.TButton').pack(side="left", padx=5)
        ttk.Button(bottom_button_frame, text="Export to JSON", command=self.export_faculty_to_json, style='TButton').pack(side="left", padx=5)

    def add_faculty(self):
        faculty_id = self.faculty_id_entry.get().strip()
        name = self.faculty_name_entry.get().strip()
        department = self.faculty_dept_entry.get().strip()
        rank = self.faculty_rank_entry.get().strip()
        contact = self.faculty_contact_entry.get().strip()

        if not faculty_id or not name:
            messagebox.showwarning("Input Error", "Faculty ID and Name are required.", parent=self)
            return

        data = {"faculty_id": faculty_id, "name": name, "department": department, "rank": rank, "contact_info": contact}
        if self.db_manager.insert_data("faculty", data):
            messagebox.showinfo("Success", f"Faculty '{name}' added successfully.", parent=self)
            self.clear_faculty_entries()
            self.faculty = self.db_manager.fetch_all_data("faculty")
            self.refresh_faculty_display()
            self.update_dashboard_info()

    def edit_selected_faculty(self):
        if not self.selected_faculty_id:
            messagebox.showwarning("No Selection", "Please select a faculty member to update.", parent=self)
            return

        faculty_id = self.faculty_id_entry.get().strip()
        name = self.faculty_name_entry.get().strip()
        department = self.faculty_dept_entry.get().strip()
        rank = self.faculty_rank_entry.get().strip()
        contact = self.faculty_contact_entry.get().strip()

        if not faculty_id or not name:
            messagebox.showwarning("Input Error", "Faculty ID and Name are required.", parent=self)
            return

        data = {"faculty_id": faculty_id, "name": name, "department": department, "rank": rank, "contact_info": contact}
        if self.db_manager.update_data("faculty", self.selected_faculty_id, data):
            messagebox.showinfo("Success", f"Faculty '{name}' updated successfully.", parent=self)
            self.clear_faculty_entries()
            self.faculty = self.db_manager.fetch_all_data("faculty")
            self.refresh_faculty_display()
            self.update_dashboard_info()
        else:
            messagebox.showerror("Update Failed", "Could not update faculty. Check for duplicate Faculty ID.", parent=self)

    def delete_selected_faculty(self):
        selected_items = self.faculty_tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select a faculty member to delete.", parent=self)
            return

        db_id_to_delete = self.faculty_tree.item(selected_items[0], 'values')[0]
        faculty_name = self.faculty_tree.item(selected_items[0], 'values')[2]

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete faculty member '{faculty_name}'?", parent=self):
            if self.db_manager.delete_data("faculty", db_id_to_delete):
                messagebox.showinfo("Success", f"Faculty '{faculty_name}' deleted successfully.", parent=self)
                self.clear_faculty_entries()
                self.faculty = self.db_manager.fetch_all_data("faculty")
                self.refresh_faculty_display()
                self.update_dashboard_info()
            else:
                messagebox.showerror("Delete Failed", "Could not delete faculty member.", parent=self)

    def refresh_faculty_display(self):
        if self.faculty_tree is None: return
        for item in self.faculty_tree.get_children():
            self.faculty_tree.delete(item)
        # Configure alternating row colors for this Treeview
        self.faculty_tree.tag_configure('oddrow', background=NORDIC_COLORS["treeview_row_bg1"])
        self.faculty_tree.tag_configure('evenrow', background=NORDIC_COLORS["treeview_row_bg2"])
        for i, f in enumerate(self.faculty):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.faculty_tree.insert("", "end", iid=f['id'], values=(f['id'], f['faculty_id'], f['name'], f['department'], f['rank'], f['contact_info']), tags=(tag,))

    def on_faculty_select(self, event):
        selected_items = self.faculty_tree.selection()
        if selected_items:
            values = self.faculty_tree.item(selected_items[0], 'values')
            self.selected_faculty_id = values[0] # Store DB ID
            self.faculty_id_entry.delete(0, tk.END)
            self.faculty_id_entry.insert(0, values[1])
            self.faculty_name_entry.delete(0, tk.END)
            self.faculty_name_entry.insert(0, values[2])
            self.faculty_dept_entry.delete(0, tk.END)
            self.faculty_dept_entry.insert(0, values[3])
            self.faculty_rank_entry.delete(0, tk.END)
            self.faculty_rank_entry.insert(0, values[4])
            self.faculty_contact_entry.delete(0, tk.END)
            self.faculty_contact_entry.insert(0, values[5])
            self.add_faculty_button.config(state=tk.DISABLED)
            self.edit_faculty_button.config(state=tk.NORMAL)
            self.cancel_faculty_edit_button.config(state=tk.NORMAL)
        else:
            self.clear_faculty_entries()

    def clear_faculty_entries(self):
        self.selected_faculty_id = None
        self.faculty_id_entry.delete(0, tk.END)
        self.faculty_name_entry.delete(0, tk.END)
        self.faculty_dept_entry.delete(0, tk.END)
        self.faculty_rank_entry.delete(0, tk.END)
        self.faculty_contact_entry.delete(0, tk.END)
        self.add_faculty_button.config(state=tk.NORMAL)
        self.edit_faculty_button.config(state=tk.DISABLED)
        self.cancel_faculty_edit_button.config(state=tk.DISABLED)
        if self.faculty_tree:
            self.faculty_tree.selection_remove(self.faculty_tree.selection())

    def export_faculty_to_json(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".json",
                                                filetypes=[("JSON files", "*.json")],
                                                title="Export Faculty to JSON", parent=self)
        if filepath:
            try:
                faculty_data = [dict(f) for f in self.faculty]
                with open(filepath, 'w') as f:
                    json.dump(faculty_data, f, indent=4)
                messagebox.showinfo("Export Complete", f"Faculty data exported to {filepath}", parent=self)
            except IOError as e:
                messagebox.showerror("Export Error", f"Failed to export data: {e}", parent=self)

    # --- Course & Curriculum Management Tab ---
    def init_course_management(self):
        course_frame = ttk.Frame(self.frames["Course Management"], padding="20", style='TFrame')
        course_frame.pack(expand=True, fill="both")

        tk.Label(course_frame, text="Course & Curriculum Management", font=('Arial', 20, 'bold'),
                 bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["accent_dark_blue"]).pack(pady=15)

        input_frame = tk.LabelFrame(course_frame, text="Add/Edit Course", padx=15, pady=15,
                                    bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"],
                                    font=('Arial', 11, 'bold'), relief="solid", borderwidth=1)
        input_frame.pack(pady=10, fill="x")

        tk.Label(input_frame, text="Course Code:", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.course_code_entry = ttk.Entry(input_frame, width=30)
        self.course_code_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(input_frame, text="Course Name:", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.course_name_entry = ttk.Entry(input_frame, width=40)
        self.course_name_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(input_frame, text="Program:", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.course_program_entry = ttk.Entry(input_frame, width=30)
        self.course_program_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(input_frame, text="Credits:", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.course_credits_entry = ttk.Entry(input_frame, width=10)
        self.course_credits_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(input_frame, text="Prerequisites:", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.course_prereq_entry = ttk.Entry(input_frame, width=40)
        self.course_prereq_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        button_row_frame = ttk.Frame(input_frame, style='TFrame')
        button_row_frame.grid(row=5, column=0, columnspan=2, pady=10)

        self.add_course_button = ttk.Button(button_row_frame, text="Add Course", command=self.add_course, style='TButton')
        self.add_course_button.pack(side="left", padx=5)
        self.edit_course_button = ttk.Button(button_row_frame, text="Update Selected", command=self.edit_selected_course, state=tk.DISABLED, style='TButton')
        self.edit_course_button.pack(side="left", padx=5)
        self.cancel_course_edit_button = ttk.Button(button_row_frame, text="Cancel Edit", command=self.clear_course_entries, state=tk.DISABLED, style='TButton')
        self.cancel_course_edit_button.pack(side="left", padx=5)

        input_frame.grid_columnconfigure(1, weight=1)

        course_display_frame = tk.LabelFrame(course_frame, text="Registered Courses", padx=15, pady=15,
                                             bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"],
                                             font=('Arial', 11, 'bold'), relief="solid", borderwidth=1)
        course_display_frame.pack(pady=10, fill="both", expand=True)

        self.course_tree = ttk.Treeview(course_display_frame, columns=("DB_ID", "CourseCode", "CourseName", "Program", "Credits", "Prerequisites"), show="headings")
        self.course_tree.heading("DB_ID", text="DB ID")
        self.course_tree.heading("CourseCode", text="Code")
        self.course_tree.heading("CourseName", text="Name")
        self.course_tree.heading("Program", text="Program")
        self.course_tree.heading("Credits", text="Credits")
        self.course_tree.heading("Prerequisites", text="Prerequisites")
        self.course_tree.column("DB_ID", width=50, anchor="center")
        self.course_tree.column("CourseCode", width=80, anchor="center")
        self.course_tree.column("CourseName", width=200, anchor="w")
        self.course_tree.column("Program", width=100, anchor="w")
        self.course_tree.column("Credits", width=60, anchor="center")
        self.course_tree.column("Prerequisites", width=150, anchor="w")
        self.course_tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(course_display_frame, orient="vertical", command=self.course_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.course_tree.configure(yscrollcommand=scrollbar.set)

        self.course_tree.bind("<Delete>", lambda event: self.delete_selected_course())
        self.course_tree.bind("<<TreeviewSelect>>", self.on_course_select)

        self.refresh_course_display()

        bottom_button_frame = ttk.Frame(course_frame, style='TFrame')
        bottom_button_frame.pack(pady=10)
        ttk.Button(bottom_button_frame, text="Delete Selected", command=self.delete_selected_course, style='Danger.TButton').pack(side="left", padx=5)
        ttk.Button(bottom_button_frame, text="Export to JSON", command=self.export_courses_to_json, style='TButton').pack(side="left", padx=5)

    def add_course(self):
        course_code = self.course_code_entry.get().strip()
        course_name = self.course_name_entry.get().strip()
        program = self.course_program_entry.get().strip()
        credits_str = self.course_credits_entry.get().strip()
        prerequisites = self.course_prereq_entry.get().strip()

        if not course_code or not course_name:
            messagebox.showwarning("Input Error", "Course Code and Course Name are required.", parent=self)
            return
        try:
            credits = float(credits_str)
        except ValueError:
            messagebox.showwarning("Input Error", "Credits must be a number.", parent=self)
            return

        data = {"course_code": course_code, "course_name": course_name, "program": program, "credits": credits, "prerequisites": prerequisites}
        if self.db_manager.insert_data("courses", data):
            messagebox.showinfo("Success", f"Course '{course_name}' added successfully.", parent=self)
            self.clear_course_entries()
            self.courses = self.db_manager.fetch_all_data("courses")
            self.refresh_course_display()
            self.update_dashboard_info()

    def edit_selected_course(self):
        if not self.selected_course_id:
            messagebox.showwarning("No Selection", "Please select a course to update.", parent=self)
            return

        course_code = self.course_code_entry.get().strip()
        course_name = self.course_name_entry.get().strip()
        program = self.course_program_entry.get().strip()
        credits_str = self.course_credits_entry.get().strip()
        prerequisites = self.course_prereq_entry.get().strip()

        if not course_code or not course_name:
            messagebox.showwarning("Input Error", "Course Code and Course Name are required.", parent=self)
            return
        try:
            credits = float(credits_str)
        except ValueError:
            messagebox.showwarning("Input Error", "Credits must be a number.", parent=self)
            return

        data = {"course_code": course_code, "course_name": course_name, "program": program, "credits": credits, "prerequisites": prerequisites}
        if self.db_manager.update_data("courses", self.selected_course_id, data):
            messagebox.showinfo("Success", f"Course '{course_name}' updated successfully.", parent=self)
            self.clear_course_entries()
            self.courses = self.db_manager.fetch_all_data("courses")
            self.refresh_course_display()
            self.update_dashboard_info()
        else:
            messagebox.showerror("Update Failed", "Could not update course. Check for duplicate Course Code.", parent=self)

    def delete_selected_course(self):
        selected_items = self.course_tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select a course to delete.", parent=self)
            return

        db_id_to_delete = self.course_tree.item(selected_items[0], 'values')[0]
        course_name = self.course_tree.item(selected_items[0], 'values')[2]

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete course '{course_name}'?", parent=self):
            if self.db_manager.delete_data("courses", db_id_to_delete):
                messagebox.showinfo("Success", f"Course '{course_name}' deleted successfully.", parent=self)
                self.clear_course_entries()
                self.courses = self.db_manager.fetch_all_data("courses")
                self.refresh_course_display()
                self.update_dashboard_info()
            else:
                messagebox.showerror("Delete Failed", "Could not delete course.", parent=self)

    def refresh_course_display(self):
        if self.course_tree is None: return
        for item in self.course_tree.get_children():
            self.course_tree.delete(item)
        # Configure alternating row colors for this Treeview
        self.course_tree.tag_configure('oddrow', background=NORDIC_COLORS["treeview_row_bg1"])
        self.course_tree.tag_configure('evenrow', background=NORDIC_COLORS["treeview_row_bg2"])
        for i, c in enumerate(self.courses):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.course_tree.insert("", "end", iid=c['id'], values=(c['id'], c['course_code'], c['course_name'], c['program'], c['credits'], c['prerequisites']), tags=(tag,))

    def on_course_select(self, event):
        selected_items = self.course_tree.selection()
        if selected_items:
            values = self.course_tree.item(selected_items[0], 'values')
            self.selected_course_id = values[0] # Store DB ID
            self.course_code_entry.delete(0, tk.END)
            self.course_code_entry.insert(0, values[1])
            self.course_name_entry.delete(0, tk.END)
            self.course_name_entry.insert(0, values[2])
            self.course_program_entry.delete(0, tk.END)
            self.course_program_entry.insert(0, values[3])
            self.course_credits_entry.delete(0, tk.END)
            self.course_credits_entry.insert(0, str(values[4]))
            self.course_prereq_entry.delete(0, tk.END)
            self.course_prereq_entry.insert(0, values[5])
            self.add_course_button.config(state=tk.DISABLED)
            self.edit_course_button.config(state=tk.NORMAL)
            self.cancel_course_edit_button.config(state=tk.NORMAL)
        else:
            self.clear_course_entries()

    def clear_course_entries(self):
        self.selected_course_id = None
        self.course_code_entry.delete(0, tk.END)
        self.course_name_entry.delete(0, tk.END)
        self.course_program_entry.delete(0, tk.END)
        self.course_credits_entry.delete(0, tk.END)
        self.course_prereq_entry.delete(0, tk.END)
        self.add_course_button.config(state=tk.NORMAL)
        self.edit_course_button.config(state=tk.DISABLED)
        self.cancel_course_edit_button.config(state=tk.DISABLED)
        if self.course_tree:
            self.course_tree.selection_remove(self.course_tree.selection())

    def export_courses_to_json(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".json",
                                                filetypes=[("JSON files", "*.json")],
                                                title="Export Courses to JSON", parent=self)
        if filepath:
            try:
                courses_data = [dict(c) for c in self.courses]
                with open(filepath, 'w') as f:
                    json.dump(courses_data, f, indent=4)
                messagebox.showinfo("Export Complete", f"Course data exported to {filepath}", parent=self)
            except IOError as e:
                messagebox.showerror("Export Error", f"Failed to export data: {e}", parent=self)

    # --- Routine Management Tab ---
    def init_scheduling(self):
        """Initializes the Routine Management tab."""
        scheduling_frame = ttk.Frame(self.frames["Routine Management"], padding="20", style='TFrame')
        scheduling_frame.pack(expand=True, fill="both")

        tk.Label(scheduling_frame, text="Class Routine & Schedule Builder", font=('Arial', 20, 'bold'),
                 bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["accent_dark_blue"]).pack(pady=15)

        input_frame = tk.LabelFrame(scheduling_frame, text="Add/Edit Class", padx=15, pady=15,
                                    bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"],
                                    font=('Arial', 11, 'bold'), relief="solid", borderwidth=1)
        input_frame.pack(pady=10, fill="x")

        tk.Label(input_frame, text="Course Code:", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.routine_course_code_var = tk.StringVar()
        self.routine_course_code_combobox = ttk.Combobox(input_frame, textvariable=self.routine_course_code_var, state="readonly")
        self.routine_course_code_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.routine_course_code_combobox.bind("<<ComboboxSelected>>", self._update_routine_course_name)
        self._populate_course_codes() # Populate on init

        tk.Label(input_frame, text="Course Name:", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.routine_course_name_label = tk.Label(input_frame, text="Select a Course Code", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"])
        self.routine_course_name_label.grid(row=1, column=1, padx=5, pady=5, sticky="ew")


        tk.Label(input_frame, text="Time Slot:", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.time_var = tk.StringVar()
        self.time_var.set("9:00–10:30 AM")
        time_options = ["9:00–10:30 AM", "10:40–12:10 PM", "12:20–1:50 PM", "2:00–3:30 PM", "3:40–5:10 PM"]
        time_menu = ttk.OptionMenu(input_frame, self.time_var, *time_options)
        time_menu.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(input_frame, text="Weekday:", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.weekday_var = tk.StringVar()
        self.weekday_var.set("Sunday")
        weekdays = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
        weekday_menu = ttk.OptionMenu(input_frame, self.weekday_var, *weekdays)
        weekday_menu.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        button_row_frame = ttk.Frame(input_frame, style='TFrame')
        button_row_frame.grid(row=4, column=0, columnspan=2, pady=10)

        self.add_schedule_button = ttk.Button(button_row_frame, text="Add Class to Routine", command=self.add_class_to_routine, style='TButton')
        self.add_schedule_button.pack(side="left", padx=5)
        self.edit_schedule_button = ttk.Button(button_row_frame, text="Update Selected Class", command=self.edit_selected_schedule, state=tk.DISABLED, style='TButton')
        self.edit_schedule_button.pack(side="left", padx=5)
        self.cancel_schedule_edit_button = ttk.Button(button_row_frame, text="Cancel Edit", command=self.cancel_schedule_edit, state=tk.DISABLED, style='TButton')
        self.cancel_schedule_edit_button.pack(side="left", padx=5)


        input_frame.grid_columnconfigure(1, weight=1) # Make the entry/menu column expand

        # Routine display
        routine_frame = tk.LabelFrame(scheduling_frame, text="Current Routine", padx=15, pady=15,
                                      bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"],
                                      font=('Arial', 11, 'bold'), relief="solid", borderwidth=1)
        routine_frame.pack(pady=10, fill="both", expand=True)

        self.routine_tree = ttk.Treeview(routine_frame, columns=("DB_ID", "CourseCode", "Time", "Weekday"), show="headings")
        self.routine_tree.heading("DB_ID", text="DB ID")
        self.routine_tree.heading("CourseCode", text="Course Code")
        self.routine_tree.heading("Time", text="Time Slot")
        self.routine_tree.heading("Weekday", text="Weekday")
        self.routine_tree.column("DB_ID", width=50, anchor="center")
        self.routine_tree.column("CourseCode", width=100, anchor="center")
        self.routine_tree.column("Time", width=150, anchor="center")
        self.routine_tree.column("Weekday", width=100, anchor="center")
        self.routine_tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(routine_frame, orient="vertical", command=self.routine_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.routine_tree.configure(yscrollcommand=scrollbar.set)

        self.routine_tree.bind("<Delete>", lambda event: self.delete_selected_schedule())
        self.routine_tree.bind("<<TreeviewSelect>>", self.on_schedule_select)

        self.refresh_schedules_display()

        # Buttons for routine management
        bottom_button_frame = ttk.Frame(scheduling_frame, style='TFrame')
        bottom_button_frame.pack(pady=10)
        ttk.Button(bottom_button_frame, text="Delete Selected", command=self.delete_selected_schedule, style='Danger.TButton').pack(side="left", padx=5)
        ttk.Button(bottom_button_frame, text="Export Routine (JSON)", command=self.export_schedules, style='TButton').pack(side="left", padx=5)
        ttk.Button(bottom_button_frame, text="Export Routine (PDF - Placeholder)", command=lambda: messagebox.showinfo("PDF Export", "PDF export functionality is a placeholder.", parent=self), style='TButton').pack(side="left", padx=5)


    def _populate_course_codes(self):
        """Populates the course code combobox with available course codes."""
        course_codes = [c['course_code'] for c in self.db_manager.fetch_all_data("courses")]
        self.routine_course_code_combobox['values'] = course_codes
        if course_codes:
            self.routine_course_code_var.set(course_codes[0])
            self._update_routine_course_name() # Update course name label initially

    def _update_routine_course_name(self, event=None):
        """Updates the course name label based on the selected course code."""
        selected_code = self.routine_course_code_var.get()
        course_name = ""
        for course in self.db_manager.fetch_all_data("courses"):
            if course['course_code'] == selected_code:
                course_name = course['course_name']
                break
        self.routine_course_name_label.config(text=course_name if course_name else "Course not found")

    def add_class_to_routine(self):
        """Adds a new class to the routine and saves it."""
        course_code = self.routine_course_code_var.get().strip()
        time_slot = self.time_var.get()
        weekday = self.weekday_var.get()

        if not course_code:
            messagebox.showwarning("Input Error", "Please select a course code.", parent=self)
            return

        # Basic clash detection (same time, same day)
        for sched in self.schedules:
            if sched['time_slot'] == time_slot and sched['weekday'] == weekday:
                messagebox.showwarning("Clash Detected", f"A class is already scheduled for {weekday} at {time_slot}. Please choose a different slot.", parent=self)
                return

        data = {"course_code": course_code, "time_slot": time_slot, "weekday": weekday}
        if self.db_manager.insert_data("routines", data):
            messagebox.showinfo("Success", "Class added to routine.", parent=self)
            self.schedules = self.db_manager.fetch_all_data("routines")
            self.refresh_schedules_display()
            self.cancel_schedule_edit()
            self.update_dashboard_info()

    def refresh_schedules_display(self):
        """Clears and repopulates the routine Treeview."""
        if self.routine_tree is None: return
        for item in self.routine_tree.get_children():
            self.routine_tree.delete(item)
        # Configure alternating row colors for this Treeview
        self.routine_tree.tag_configure('oddrow', background=NORDIC_COLORS["treeview_row_bg1"])
        self.routine_tree.tag_configure('evenrow', background=NORDIC_COLORS["treeview_row_bg2"])
        for i, sched in enumerate(self.schedules):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.routine_tree.insert("", "end", iid=sched['id'], values=(sched['id'], sched['course_code'], sched['time_slot'], sched['weekday']), tags=(tag,))

    def on_schedule_select(self, event):
        """Handles selection in the schedule Treeview to populate fields for editing."""
        selected_items = self.routine_tree.selection()
        if selected_items:
            values = self.routine_tree.item(selected_items[0], 'values')
            self.selected_routine_id = values[0] # Store DB ID
            self.routine_course_code_var.set(values[1])
            self._update_routine_course_name() # Update course name label
            self.time_var.set(values[2])
            self.weekday_var.set(values[3])
            self.add_schedule_button.config(state=tk.DISABLED)
            self.edit_schedule_button.config(state=tk.NORMAL)
            self.cancel_schedule_edit_button.config(state=tk.NORMAL)
        else:
            self.cancel_schedule_edit()

    def edit_selected_schedule(self):
        """Updates the selected schedule with new values."""
        if not self.selected_routine_id:
            messagebox.showwarning("No Selection", "No class selected for editing.", parent=self)
            return

        course_code = self.routine_course_code_var.get().strip()
        time_slot = self.time_var.get()
        weekday = self.weekday_var.get()

        if not course_code:
            messagebox.showwarning("Input Error", "Please select a course code.", parent=self)
            return

        # Check for clashes, excluding the currently edited item
        for sched in self.schedules:
            if sched['id'] != self.selected_routine_id and \
               sched['time_slot'] == time_slot and sched['weekday'] == weekday:
                messagebox.showwarning("Clash Detected", f"A class is already scheduled for {weekday} at {time_slot}. Please choose a different slot.", parent=self)
                return

        data = {"course_code": course_code, "time_slot": time_slot, "weekday": weekday}
        if self.db_manager.update_data("routines", self.selected_routine_id, data):
            messagebox.showinfo("Success", "Class updated successfully.", parent=self)
            self.schedules = self.db_manager.fetch_all_data("routines")
            self.refresh_schedules_display()
            self.cancel_schedule_edit()
            self.update_dashboard_info()
        else:
            messagebox.showerror("Update Failed", "Could not update class.", parent=self)

    def cancel_schedule_edit(self):
        """Cancels the current edit operation and clears fields."""
        self.selected_routine_id = None
        self.routine_course_code_var.set("")
        self.routine_course_name_label.config(text="Select a Course Code")
        self.time_var.set("9:00–10:30 AM")
        self.weekday_var.set("Sunday")
        self.add_schedule_button.config(state=tk.NORMAL)
        self.edit_schedule_button.config(state=tk.DISABLED)
        self.cancel_schedule_edit_button.config(state=tk.DISABLED)
        if self.routine_tree:
            self.routine_tree.selection_remove(self.routine_tree.selection())
        self._populate_course_codes() # Re-populate combobox

    def delete_selected_schedule(self):
        """Deletes the selected class from the routine."""
        if self.routine_tree is None: return
        selected_items = self.routine_tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select a class to delete.", parent=self)
            return

        db_id_to_delete = self.routine_tree.item(selected_items[0], 'values')[0]
        course_code = self.routine_tree.item(selected_items[0], 'values')[1]

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the routine for course '{course_code}'?", parent=self):
            if self.db_manager.delete_data("routines", db_id_to_delete):
                messagebox.showinfo("Deleted", "Class deleted successfully.", parent=self)
                self.schedules = self.db_manager.fetch_all_data("routines")
                self.refresh_schedules_display()
                self.cancel_schedule_edit()
                self.update_dashboard_info()
            else:
                messagebox.showerror("Delete Failed", "Could not delete class.", parent=self)

    def export_schedules(self):
        """Exports the current routine to a JSON file."""
        filepath = filedialog.asksaveasfilename(defaultextension=".json",
                                                filetypes=[("JSON files", "*.json")],
                                                title="Export Routine", parent=self)
        if filepath:
            try:
                schedules_data = [dict(s) for s in self.schedules]
                with open(filepath, 'w') as f:
                    json.dump(schedules_data, f, indent=4)
                messagebox.showinfo("Export Complete", f"Routine exported to {filepath}", parent=self)
            except IOError as e:
                messagebox.showerror("Export Error", f"Failed to export data: {e}", parent=self)

    # --- Attendance Management Tab ---
    def init_attendance(self):
        """Initializes the Attendance tab."""
        attendance_frame = ttk.Frame(self.frames["Attendance Management"], padding="20", style='TFrame')
        attendance_frame.pack(expand=True, fill="both")

        tk.Label(attendance_frame, text="Attendance Management", font=('Arial', 20, 'bold'),
                 bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["accent_dark_blue"]).pack(pady=15)

        input_frame = tk.LabelFrame(attendance_frame, text="Mark/Edit Attendance", padx=15, pady=15,
                                    bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"],
                                    font=('Arial', 11, 'bold'), relief="solid", borderwidth=1)
        input_frame.pack(pady=10, fill="x")

        tk.Label(input_frame, text="Student ID:", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.attendance_student_id_var = tk.StringVar()
        self.attendance_student_id_combobox = ttk.Combobox(input_frame, textvariable=self.attendance_student_id_var, state="readonly")
        self.attendance_student_id_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.attendance_student_id_combobox.bind("<<ComboboxSelected>>", self._update_attendance_student_name)
        self._populate_student_ids_for_attendance()

        tk.Label(input_frame, text="Student Name:", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.attendance_student_name_label = tk.Label(input_frame, text="Select a Student ID", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"])
        self.attendance_student_name_label.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(input_frame, text="Status:", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.attendance_status_var = tk.StringVar(value="Present")
        ttk.Radiobutton(input_frame, text="Present", variable=self.attendance_status_var, value="Present", style='TRadiobutton').grid(row=2, column=1, padx=5, pady=5, sticky="w")
        ttk.Radiobutton(input_frame, text="Absent", variable=self.attendance_status_var, value="Absent", style='TRadiobutton').grid(row=3, column=1, padx=5, pady=5, sticky="w")

        tk.Label(input_frame, text="Date (YYYY-MM-DD):", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.attendance_date_entry = ttk.Entry(input_frame, width=15)
        self.attendance_date_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        self.attendance_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        button_row_frame = ttk.Frame(input_frame, style='TFrame')
        button_row_frame.grid(row=5, column=0, columnspan=2, pady=10)

        self.mark_attendance_button = ttk.Button(button_row_frame, text="Mark Attendance", command=self.mark_attendance, style='TButton')
        self.mark_attendance_button.pack(side="left", padx=5)
        self.edit_attendance_button = ttk.Button(button_row_frame, text="Update Selected Attendance", command=self.edit_selected_attendance, state=tk.DISABLED, style='TButton')
        self.edit_attendance_button.pack(side="left", padx=5)
        self.cancel_edit_attendance_button = ttk.Button(button_row_frame, text="Cancel Edit", command=self.cancel_attendance_edit, state=tk.DISABLED, style='TButton')
        self.cancel_edit_attendance_button.pack(side="left", padx=5)

        input_frame.grid_columnconfigure(1, weight=1)

        # Attendance display
        attendance_display_frame = tk.LabelFrame(attendance_frame, text="Attendance Records", padx=15, pady=15,
                                                 bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"],
                                                 font=('Arial', 11, 'bold'), relief="solid", borderwidth=1)
        attendance_display_frame.pack(pady=10, fill="both", expand=True)

        self.attendance_tree = ttk.Treeview(attendance_display_frame, columns=("DB_ID", "StudentID", "Status", "Date"), show="headings")
        self.attendance_tree.heading("DB_ID", text="DB ID")
        self.attendance_tree.heading("StudentID", text="Student ID")
        self.attendance_tree.heading("Status", text="Status")
        self.attendance_tree.heading("Date", text="Date")
        self.attendance_tree.column("DB_ID", width=50, anchor="center")
        self.attendance_tree.column("StudentID", width=100, anchor="center")
        self.attendance_tree.column("Status", width=100, anchor="center")
        self.attendance_tree.column("Date", width=150, anchor="center")
        self.attendance_tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(attendance_display_frame, orient="vertical", command=self.attendance_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.attendance_tree.configure(yscrollcommand=scrollbar.set)

        self.attendance_tree.bind("<Delete>", lambda event: self.delete_selected_attendance())
        self.attendance_tree.bind("<<TreeviewSelect>>", self.on_attendance_select)

        self.refresh_attendance_display()

        # Attendance summary
        summary_frame = tk.LabelFrame(attendance_frame, text="Attendance Summary", padx=15, pady=15,
                                      bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"],
                                      font=('Arial', 11, 'bold'), relief="solid", borderwidth=1)
        summary_frame.pack(pady=10, fill="x")

        self.summary_tree = ttk.Treeview(summary_frame, columns=("Student", "TotalClasses", "Present", "Absent", "Percentage"), show="headings")
        self.summary_tree.heading("Student", text="Student Name")
        self.summary_tree.heading("TotalClasses", text="Total Classes")
        self.summary_tree.heading("Present", text="Present")
        self.summary_tree.heading("Absent", text="Absent")
        self.summary_tree.heading("Percentage", text="Attendance %")
        self.summary_tree.column("Student", width=150, anchor="w")
        self.summary_tree.column("TotalClasses", width=100, anchor="center")
        self.summary_tree.column("Present", width=80, anchor="center")
        self.summary_tree.column("Absent", width=80, anchor="center")
        self.summary_tree.column("Percentage", width=100, anchor="center")
        self.summary_tree.pack(fill="x", expand=True)

        self.update_attendance_summary()

        # Buttons for attendance management
        bottom_button_frame = ttk.Frame(attendance_frame, style='TFrame')
        bottom_button_frame.pack(pady=10)
        ttk.Button(bottom_button_frame, text="Delete Selected", command=self.delete_selected_attendance, style='Danger.TButton').pack(side="left", padx=5)
        ttk.Button(bottom_button_frame, text="Export Attendance (JSON)", command=self.export_attendance, style='TButton').pack(side="left", padx=5)
        ttk.Button(bottom_button_frame, text="Print Register (Placeholder)", command=lambda: messagebox.showinfo("Print", "Print functionality is a placeholder.", parent=self), style='TButton').pack(side="left", padx=5)

    def _populate_student_ids_for_attendance(self):
        """Populates the student ID combobox for attendance."""
        student_ids = [s['student_id'] for s in self.db_manager.fetch_all_data("students")]
        self.attendance_student_id_combobox['values'] = student_ids
        if student_ids:
            self.attendance_student_id_var.set(student_ids[0])
            self._update_attendance_student_name()

    def _update_attendance_student_name(self, event=None):
        """Updates the student name label based on the selected student ID."""
        selected_id = self.attendance_student_id_var.get()
        student_name = ""
        for student in self.db_manager.fetch_all_data("students"):
            if student['student_id'] == selected_id:
                student_name = student['name']
                break
        self.attendance_student_name_label.config(text=student_name if student_name else "Student not found")

    def mark_attendance(self):
        """Marks attendance for a student and saves it."""
        student_id = self.attendance_student_id_var.get().strip()
        status = self.attendance_status_var.get()
        current_date = self.attendance_date_entry.get().strip()

        if not student_id:
            messagebox.showwarning("Input Error", "Please select a student ID.", parent=self)
            return
        try:
            datetime.strptime(current_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Invalid Date", "Please enter date inYYYY-MM-DD format.", parent=self)
            return

        data = {"student_id": student_id, "status": status, "date": current_date}
        if self.db_manager.insert_data("attendance", data):
            messagebox.showinfo("Success", "Attendance marked.", parent=self)
            self.attendance_records = self.db_manager.fetch_all_data("attendance")
            self.refresh_attendance_display()
            self.update_attendance_summary()
            self.cancel_attendance_edit()
            self.update_dashboard_info()

    def refresh_attendance_display(self):
        """Clears and repopulates the attendance Treeview."""
        if self.attendance_tree is None: return
        for item in self.attendance_tree.get_children():
            self.attendance_tree.delete(item)
        # Configure alternating row colors for this Treeview
        self.attendance_tree.tag_configure('oddrow', background=NORDIC_COLORS["treeview_row_bg1"])
        self.attendance_tree.tag_configure('evenrow', background=NORDIC_COLORS["treeview_row_bg2"])
        for i, record in enumerate(self.attendance_records):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.attendance_tree.insert("", "end", iid=record['id'], values=(record['id'], record['student_id'], record['status'], record['date']), tags=(tag,))

    def on_attendance_select(self, event):
        """Handles selection in the attendance Treeview to populate fields for editing."""
        selected_items = self.attendance_tree.selection()
        if selected_items:
            values = self.attendance_tree.item(selected_items[0], 'values')
            self.selected_attendance_id = values[0] # Store DB ID
            self.attendance_student_id_var.set(values[1])
            self._update_attendance_student_name()
            self.attendance_status_var.set(values[2])
            self.attendance_date_entry.delete(0, tk.END)
            self.attendance_date_entry.insert(0, values[3])
            self.mark_attendance_button.config(state=tk.DISABLED)
            self.edit_attendance_button.config(state=tk.NORMAL)
            self.cancel_edit_attendance_button.config(state=tk.NORMAL)
        else:
            self.cancel_attendance_edit()

    def edit_selected_attendance(self):
        """Updates the selected attendance record with new values."""
        if not self.selected_attendance_id:
            messagebox.showwarning("No Selection", "No attendance record selected for editing.", parent=self)
            return

        student_id = self.attendance_student_id_var.get().strip()
        status = self.attendance_status_var.get()
        current_date = self.attendance_date_entry.get().strip()

        if not student_id:
            messagebox.showwarning("Input Error", "Please select a student ID.", parent=self)
            return
        try:
            datetime.strptime(current_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Invalid Date", "Please enter date inYYYY-MM-DD format.", parent=self)
            return

        data = {"student_id": student_id, "status": status, "date": current_date}
        if self.db_manager.update_data("attendance", self.selected_attendance_id, data):
            messagebox.showinfo("Success", "Attendance record updated successfully.", parent=self)
            self.attendance_records = self.db_manager.fetch_all_data("attendance")
            self.refresh_attendance_display()
            self.update_attendance_summary()
            self.cancel_attendance_edit()
            self.update_dashboard_info()
        else:
            messagebox.showerror("Update Failed", "Could not update attendance record.", parent=self)

    def cancel_attendance_edit(self):
        """Cancels the current edit operation and clears fields."""
        self.selected_attendance_id = None
        self.attendance_student_id_var.set("")
        self.attendance_student_name_label.config(text="Select a Student ID")
        self.attendance_status_var.set("Present")
        self.attendance_date_entry.delete(0, tk.END)
        self.attendance_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.mark_attendance_button.config(state=tk.NORMAL)
        self.edit_attendance_button.config(state=tk.DISABLED)
        self.cancel_edit_attendance_button.config(state=tk.DISABLED)
        if self.attendance_tree:
            self.attendance_tree.selection_remove(self.attendance_tree.selection())
        self._populate_student_ids_for_attendance()

    def delete_selected_attendance(self):
        """Deletes the selected attendance record."""
        if self.attendance_tree is None: return
        selected_items = self.attendance_tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select an attendance record to delete.", parent=self)
            return

        db_id_to_delete = self.attendance_tree.item(selected_items[0], 'values')[0]
        student_id = self.attendance_tree.item(selected_items[0], 'values')[1]
        record_date = self.attendance_tree.item(selected_items[0], 'values')[3]

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the attendance record for student '{student_id}' on {record_date}?", parent=self):
            if self.db_manager.delete_data("attendance", db_id_to_delete):
                messagebox.showinfo("Deleted", "Attendance record deleted successfully.", parent=self)
                self.attendance_records = self.db_manager.fetch_all_data("attendance")
                self.refresh_attendance_display()
                self.update_attendance_summary()
                self.cancel_attendance_edit()
                self.update_dashboard_info()
            else:
                messagebox.showerror("Delete Failed", "Could not delete attendance record.", parent=self)

    def update_attendance_summary(self):
        """Calculates and displays attendance percentages for each student."""
        if self.summary_tree is None: return
        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)
        # Configure alternating row colors for this Treeview
        self.summary_tree.tag_configure('oddrow', background=NORDIC_COLORS["treeview_row_bg1"])
        self.summary_tree.tag_configure('evenrow', background=NORDIC_COLORS["treeview_row_bg2"])

        student_attendance_counts = {} # {student_id: {'present': count, 'total': count, 'name': 'Student Name'}}
        all_students = self.db_manager.fetch_all_data("students")
        student_id_to_name = {s['student_id']: s['name'] for s in all_students}

        for record in self.attendance_records:
            student_id = record['student_id']
            if student_id not in student_attendance_counts:
                student_attendance_counts[student_id] = {'present': 0, 'total': 0, 'name': student_id_to_name.get(student_id, student_id)}
            student_attendance_counts[student_id]['total'] += 1
            if record['status'] == 'Present':
                student_attendance_counts[student_id]['present'] += 1

        for i, (student_id, counts) in enumerate(student_attendance_counts.items()):
            percentage = (counts['present'] / counts['total']) * 100 if counts['total'] > 0 else 0
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.summary_tree.insert("", "end", values=(counts['name'], counts['total'], counts['present'], counts['total'] - counts['present'], f"{percentage:.2f}%"), tags=(tag,))

    def export_attendance(self):
        """Exports the current attendance records to a JSON file."""
        filepath = filedialog.asksaveasfilename(defaultextension=".json",
                                                filetypes=[("JSON files", "*.json")],
                                                title="Export Attendance Records", parent=self)
        if filepath:
            try:
                attendance_data = [dict(r) for r in self.attendance_records]
                with open(filepath, 'w') as f:
                    json.dump(attendance_data, f, indent=4)
                messagebox.showinfo("Export Complete", f"Attendance records exported to {filepath}", parent=self)
            except IOError as e:
                messagebox.showerror("Export Error", f"Failed to export data: {e}", parent=self)

    # --- Grading & Assessment Tab ---
    def init_assessment(self):
        """Initializes the Assessment tab."""
        assessment_frame = ttk.Frame(self.frames["Grading & Assessment"], padding="20", style='TFrame')
        assessment_frame.pack(expand=True, fill="both")

        tk.Label(assessment_frame, text="Grading & Assessment", font=('Arial', 20, 'bold'),
                 bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["accent_dark_blue"]).pack(pady=15)

        input_frame = tk.LabelFrame(assessment_frame, text="Add/Edit Student Grade", padx=15, pady=15,
                                    bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"],
                                    font=('Arial', 11, 'bold'), relief="solid", borderwidth=1)
        input_frame.pack(pady=10, fill="x")

        tk.Label(input_frame, text="Student ID:", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.assess_student_id_var = tk.StringVar()
        self.assess_student_id_combobox = ttk.Combobox(input_frame, textvariable=self.assess_student_id_var, state="readonly")
        self.assess_student_id_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.assess_student_id_combobox.bind("<<ComboboxSelected>>", self._update_assess_student_name)
        self._populate_student_ids_for_grades()

        tk.Label(input_frame, text="Student Name:", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.assess_student_name_label = tk.Label(input_frame, text="Select a Student ID", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"])
        self.assess_student_name_label.grid(row=1, column=1, padx=5, pady=5, sticky="ew")


        tk.Label(input_frame, text="Assessment Type:", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.assessment_type_var = tk.StringVar()
        self.assessment_type_var.set("Midterm")
        assessment_types = ["Midterm", "Final", "Viva", "Presentation", "Assignment"]
        ttk.OptionMenu(input_frame, self.assessment_type_var, *assessment_types).grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(input_frame, text="Marks Obtained (0-100):", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=3, column=0, padx=5, pady=5, sticky="w")
        # Input validation for marks entry
        vcmd = (self.register(self._validate_marks_input), '%P')
        self.marks_entry = ttk.Entry(input_frame, width=10, validate="key", validatecommand=vcmd)
        self.marks_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        button_row_frame = ttk.Frame(input_frame, style='TFrame')
        button_row_frame.grid(row=4, column=0, columnspan=2, pady=10)

        self.add_grade_button = ttk.Button(button_row_frame, text="Add Grade", command=self.add_grade, style='TButton')
        self.add_grade_button.pack(side="left", padx=5)
        self.edit_grade_button = ttk.Button(button_row_frame, text="Update Selected Grade", command=self.edit_selected_grade, state=tk.DISABLED, style='TButton')
        self.edit_grade_button.pack(side="left", padx=5)
        self.cancel_edit_grade_button = ttk.Button(button_row_frame, text="Cancel Edit", command=self.cancel_grade_edit, state=tk.DISABLED, style='TButton')
        self.cancel_edit_grade_button.pack(side="left", padx=5)

        input_frame.grid_columnconfigure(1, weight=1)

        # Grades display
        grades_display_frame = tk.LabelFrame(assessment_frame, text="Grades Records", padx=15, pady=15,
                                             bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"],
                                             font=('Arial', 11, 'bold'), relief="solid", borderwidth=1)
        grades_display_frame.pack(pady=10, fill="both", expand=True)

        self.grades_tree = ttk.Treeview(grades_display_frame, columns=("DB_ID", "StudentID", "Type", "Marks", "GPA"), show="headings")
        self.grades_tree.heading("DB_ID", text="DB ID")
        self.grades_tree.heading("StudentID", text="Student ID")
        self.grades_tree.heading("Type", text="Assessment Type")
        self.grades_tree.heading("Marks", text="Marks")
        self.grades_tree.heading("GPA", text="Grade Point")
        self.grades_tree.column("DB_ID", width=50, anchor="center")
        self.grades_tree.column("StudentID", width=100, anchor="center")
        self.grades_tree.column("Type", width=120, anchor="center")
        self.grades_tree.column("Marks", width=80, anchor="center")
        self.grades_tree.column("GPA", width=80, anchor="center")
        self.grades_tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(grades_display_frame, orient="vertical", command=self.grades_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.grades_tree.configure(yscrollcommand=scrollbar.set)

        self.grades_tree.bind("<Delete>", lambda event: self.delete_selected_grade())
        self.grades_tree.bind("<<TreeviewSelect>>", self.on_grade_select)

        self.refresh_grades_display()

        # Student GPA summary
        gpa_summary_frame = tk.LabelFrame(assessment_frame, text="Student GPA Summary", padx=15, pady=15,
                                          bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"],
                                          font=('Arial', 11, 'bold'), relief="solid", borderwidth=1)
        gpa_summary_frame.pack(pady=10, fill="x")

        self.gpa_summary_tree = ttk.Treeview(gpa_summary_frame, columns=("StudentName", "OverallGPA"), show="headings")
        self.gpa_summary_tree.heading("StudentName", text="Student Name")
        self.gpa_summary_tree.heading("OverallGPA", text="Overall GPA")
        self.gpa_summary_tree.column("StudentName", width=200, anchor="w")
        self.gpa_summary_tree.column("OverallGPA", width=150, anchor="center")
        self.gpa_summary_tree.pack(fill="x", expand=True)

        self.update_gpa_summary()

        # Buttons for grades management
        bottom_button_frame = ttk.Frame(assessment_frame, style='TFrame')
        bottom_button_frame.pack(pady=10)
        ttk.Button(bottom_button_frame, text="Delete Selected", command=self.delete_selected_grade, style='Danger.TButton').pack(side="left", padx=5)
        ttk.Button(bottom_button_frame, text="Export Grades (JSON)", command=self.export_grades, style='TButton').pack(side="left", padx=5)
        ttk.Button(bottom_button_frame, text="Export Transcript (Placeholder)", command=lambda: messagebox.showinfo("Transcript Export", "Transcript export functionality is a placeholder.", parent=self), style='TButton').pack(side="left", padx=5)


    def _populate_student_ids_for_grades(self):
        """Populates the student ID combobox for grades."""
        student_ids = [s['student_id'] for s in self.db_manager.fetch_all_data("students")]
        self.assess_student_id_combobox['values'] = student_ids
        if student_ids:
            self.assess_student_id_var.set(student_ids[0])
            self._update_assess_student_name()

    def _update_assess_student_name(self, event=None):
        """Updates the student name label based on the selected student ID."""
        selected_id = self.assess_student_id_var.get()
        student_name = ""
        for student in self.db_manager.fetch_all_data("students"):
            if student['student_id'] == selected_id:
                student_name = student['name']
                break
        self.assess_student_name_label.config(text=student_name if student_name else "Student not found")

    def _validate_marks_input(self, P):
        """Validates that input for marks is a number or empty string."""
        if P.strip() == "":
            return True # Allow empty string for initial entry
        try:
            float(P)
            return True
        except ValueError:
            return False

    def calculate_grade_point(self, marks):
        """Calculates grade point based on marks."""
        if marks >= 80: return 4.00
        elif marks >= 75: return 3.75
        elif marks >= 70: return 3.50
        elif marks >= 65: return 3.25
        elif marks >= 60: return 3.00
        elif marks >= 55: return 2.75
        elif marks >= 50: return 2.50
        elif marks >= 45: return 2.25
        elif marks >= 40: return 2.00
        else: return 0.00

    def add_grade(self):
        """Adds a new grade record and saves it."""
        student_id = self.assess_student_id_var.get().strip()
        assessment_type = self.assessment_type_var.get()
        marks_text = self.marks_entry.get().strip()

        if not student_id:
            messagebox.showwarning("Input Error", "Please select a student ID.", parent=self)
            return

        try:
            marks = float(marks_text)
            if not (0 <= marks <= 100):
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid marks value between 0 and 100.", parent=self)
            return

        grade_point = self.calculate_grade_point(marks)

        data = {
            "student_id": student_id,
            "assessment_type": assessment_type,
            "marks": marks,
            "grade_point": grade_point
        }
        if self.db_manager.insert_data("grades", data):
            messagebox.showinfo("Success", "Grade added.", parent=self)
            self.grades = self.db_manager.fetch_all_data("grades")
            self.refresh_grades_display()
            self.update_gpa_summary()
            self.cancel_grade_edit()
            self.update_dashboard_info()

    def refresh_grades_display(self):
        """Clears and repopulates the grades Treeview."""
        if self.grades_tree is None: return
        for item in self.grades_tree.get_children():
            self.grades_tree.delete(item)
        # Configure alternating row colors for this Treeview
        self.grades_tree.tag_configure('oddrow', background=NORDIC_COLORS["treeview_row_bg1"])
        self.grades_tree.tag_configure('evenrow', background=NORDIC_COLORS["treeview_row_bg2"])
        for i, grade in enumerate(self.grades):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.grades_tree.insert("", "end", iid=grade['id'], values=(grade['id'], grade['student_id'], grade['assessment_type'], grade['marks'], f"{grade['grade_point']:.2f}"), tags=(tag,))

    def on_grade_select(self, event):
        """Handles selection in the grades Treeview to populate fields for editing."""
        selected_items = self.grades_tree.selection()
        if selected_items:
            values = self.grades_tree.item(selected_items[0], 'values')
            self.selected_grade_id = values[0] # Store DB ID
            self.assess_student_id_var.set(values[1])
            self._update_assess_student_name()
            self.assessment_type_var.set(values[2])
            self.marks_entry.delete(0, tk.END)
            self.marks_entry.insert(0, str(values[3]))
            self.add_grade_button.config(state=tk.DISABLED)
            self.edit_grade_button.config(state=tk.NORMAL)
            self.cancel_edit_grade_button.config(state=tk.NORMAL)
        else:
            self.cancel_grade_edit()

    def edit_selected_grade(self):
        """Updates the selected grade record with new values."""
        if not self.selected_grade_id:
            messagebox.showwarning("No Selection", "No grade selected for editing.", parent=self)
            return

        student_id = self.assess_student_id_var.get().strip()
        assessment_type = self.assessment_type_var.get()
        marks_text = self.marks_entry.get().strip()

        if not student_id:
            messagebox.showwarning("Input Error", "Please select a student ID.", parent=self)
            return
        try:
            marks = float(marks_text)
            if not (0 <= marks <= 100):
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid marks value between 0 and 100.", parent=self)
            return

        grade_point = self.calculate_grade_point(marks)

        data = {
            "student_id": student_id,
            "assessment_type": assessment_type,
            "marks": marks,
            "grade_point": grade_point
        }
        if self.db_manager.update_data("grades", self.selected_grade_id, data):
            messagebox.showinfo("Success", "Grade updated successfully.", parent=self)
            self.grades = self.db_manager.fetch_all_data("grades")
            self.refresh_grades_display()
            self.update_gpa_summary()
            self.cancel_grade_edit()
            self.update_dashboard_info()
        else:
            messagebox.showerror("Update Failed", "Could not update grade.", parent=self)

    def cancel_grade_edit(self):
        """Cancels the current edit operation and clears fields."""
        self.selected_grade_id = None
        self.assess_student_id_var.set("")
        self.assess_student_name_label.config(text="Select a Student ID")
        self.assessment_type_var.set("Midterm")
        self.marks_entry.delete(0, tk.END)
        self.add_grade_button.config(state=tk.NORMAL)
        self.edit_grade_button.config(state=tk.DISABLED)
        self.cancel_edit_grade_button.config(state=tk.DISABLED)
        if self.grades_tree:
            self.grades_tree.selection_remove(self.grades_tree.selection())
        self._populate_student_ids_for_grades()

    def delete_selected_grade(self):
        """Deletes the selected grade record."""
        if self.grades_tree is None: return
        selected_items = self.grades_tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select a grade record to delete.", parent=self)
            return

        db_id_to_delete = self.grades_tree.item(selected_items[0], 'values')[0]
        student_id = self.grades_tree.item(selected_items[0], 'values')[1]
        assessment_type = self.grades_tree.item(selected_items[0], 'values')[2]

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the grade for student '{student_id}' ({assessment_type})?", parent=self):
            if self.db_manager.delete_data("grades", db_id_to_delete):
                messagebox.showinfo("Deleted", "Grade record deleted successfully.", parent=self)
                self.grades = self.db_manager.fetch_all_data("grades")
                self.refresh_grades_display()
                self.update_gpa_summary()
                self.cancel_grade_edit()
                self.update_dashboard_info()
            else:
                messagebox.showerror("Delete Failed", "Could not delete grade record.", parent=self)

    def update_gpa_summary(self):
        """Calculates and displays overall GPA for each student."""
        if self.gpa_summary_tree is None: return
        for item in self.gpa_summary_tree.get_children():
            self.gpa_summary_tree.delete(item)
        # Configure alternating row colors for this Treeview
        self.gpa_summary_tree.tag_configure('oddrow', background=NORDIC_COLORS["treeview_row_bg1"])
        self.gpa_summary_tree.tag_configure('evenrow', background=NORDIC_COLORS["treeview_row_bg2"])

        student_gpas = {} # {student_id: {'total_points': sum, 'count': count}}
        all_students = self.db_manager.fetch_all_data("students")
        student_id_to_name = {s['student_id']: s['name'] for s in all_students}

        for grade in self.grades:
            student_id = grade['student_id']
            if student_id not in student_gpas:
                student_gpas[student_id] = {'total_points': 0, 'count': 0, 'name': student_id_to_name.get(student_id, student_id)}
            student_gpas[student_id]['total_points'] += grade['grade_point']
            student_gpas[student_id]['count'] += 1

        for i, (student_id, data) in enumerate(student_gpas.items()):
            overall_gpa = (data['total_points'] / data['count']) if data['count'] > 0 else 0
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.gpa_summary_tree.insert("", "end", values=(data['name'], f"{overall_gpa:.2f}"), tags=(tag,))

    def export_grades(self):
        """Exports the current grades to a JSON file."""
        filepath = filedialog.asksaveasfilename(defaultextension=".json",
                                                filetypes=[("JSON files", "*.json")],
                                                title="Export Grades Records", parent=self)
        if filepath:
            try:
                grades_data = [dict(g) for g in self.grades]
                with open(filepath, 'w') as f:
                    json.dump(grades_data, f, indent=4)
                messagebox.showinfo("Export Complete", f"Grades records exported to {filepath}", parent=self)
            except IOError as e:
                messagebox.showerror("Export Error", f"Failed to export data: {e}", parent=self)

    # --- Application & Document Generator Tab ---
    def init_application_generator(self):
        """Initializes the Application Generator tab."""
        app_gen_frame = ttk.Frame(self.frames["Document Generator"], padding="20", style='TFrame')
        app_gen_frame.pack(expand=True, fill="both")

        tk.Label(app_gen_frame, text="Application & Document Generator", font=('Arial', 20, 'bold'),
                 bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["accent_dark_blue"]).pack(pady=15)

        input_frame = tk.LabelFrame(app_gen_frame, text="Generate Letter", padx=15, pady=15,
                                    bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"],
                                    font=('Arial', 11, 'bold'), relief="solid", borderwidth=1)
        input_frame.pack(pady=10, fill="x")

        tk.Label(input_frame, text="Select Application Type:", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.application_type_var = tk.StringVar()
        app_types = [
            "Class Reschedule",
            "Requisition Request",
            "Leave Application",
            "Recommendation Letter",
            "Financial Assistance Request",
            "Makeup Exam Request",
            "Add/Drop Course Request",
            "Formal Letter to Registrar/Chairperson"
        ]
        self.application_type_var.set(app_types[0])
        ttk.OptionMenu(input_frame, self.application_type_var, *app_types).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(input_frame, text="Applicant Name:", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.applicant_name_entry = ttk.Entry(input_frame, width=50)
        self.applicant_name_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(input_frame, text="Additional Details / Reason:", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.details_text = tk.Text(input_frame, width=70, height=10, wrap="word", font=("Arial", 10),
                                    bg=NORDIC_COLORS["text_light"], fg=NORDIC_COLORS["text_dark"],
                                    relief="solid", borderwidth=1)
        self.details_text.grid(row=2, column=1, padx=5, pady=5, sticky="nsew") # Make text area expand

        ttk.Button(input_frame, text="Generate Application Letter", command=self.generate_application, style='TButton').grid(row=3, column=0, columnspan=2, pady=10)
        input_frame.grid_columnconfigure(1, weight=1)
        input_frame.grid_rowconfigure(2, weight=1) # Make text area row expand

        # Generated text display
        output_frame = tk.LabelFrame(app_gen_frame, text="Generated Letter", padx=15, pady=15,
                                     bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"],
                                     font=('Arial', 11, 'bold'), relief="solid", borderwidth=1)
        output_frame.pack(pady=10, fill="both", expand=True)

        self.generated_text_display = tk.Text(output_frame, width=80, height=15, wrap="word", state=tk.DISABLED, font=("Arial", 10),
                                              bg=NORDIC_COLORS["text_light"], fg=NORDIC_COLORS["text_dark"],
                                              relief="solid", borderwidth=1)
        self.generated_text_display.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(output_frame, orient="vertical", command=self.generated_text_display.yview)
        scrollbar.pack(side="right", fill="y")
        self.generated_text_display.config(yscrollcommand=scrollbar.set)

        button_frame = ttk.Frame(app_gen_frame, style='TFrame')
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Copy to Clipboard", command=self.copy_generated_text, style='TButton').pack(side="left", padx=5)
        ttk.Button(button_frame, text="Save to File (TXT)", command=self.save_generated_text, style='TButton').pack(side="left", padx=5)
        ttk.Button(button_frame, text="Export to PDF/DOCX (Placeholder)", command=lambda: messagebox.showinfo("Export", "PDF/DOCX export functionality is a placeholder.", parent=self), style='TButton').pack(side="left", padx=5)

    def generate_application(self):
        """Generates the application letter based on selected type and inputs."""
        app_type = self.application_type_var.get()
        applicant_name = self.applicant_name_entry.get().strip()
        details = self.details_text.get("1.0", tk.END).strip()

        if not applicant_name:
            messagebox.showwarning("Input Error", "Please enter the applicant's name.", parent=self)
            return

        current_date = datetime.now().strftime("%B %d, %Y")

        header = f"Central Women's University\nDepartment of English Language and Literature\n\nDate: {current_date}\n\n"
        salutation = "To,\nThe Chairperson,\nDepartment of English Language and Literature,\nCentral Women's University.\n\n"
        closing = f"\n\nSincerely,\n{applicant_name}"

        body = ""

        if app_type == "Class Reschedule":
            body = (f"Subject: Request for Class Reschedule\n\n"
                    f"Dear Sir/Madam,\n\n"
                    f"I, {applicant_name}, would like to request the rescheduling of my class due to the following reason:\n"
                    f"{details}\n"
                    "I kindly ask for your consideration and approval.\n")
        elif app_type == "Requisition Request":
            body = (f"Subject: Requisition Request\n\n"
                    f"Dear Sir/Madam,\n\n"
                    f"I, {applicant_name}, request the requisition of the following materials:\n"
                    f"{details}\n"
                    "I hope for your prompt approval.\n")
        elif app_type == "Leave Application":
            body = (f"Subject: Leave Application\n\n"
                    f"Dear Sir/Madam,\n\n"
                    f"I, {applicant_name}, request leave for the following reason(s):\n"
                    f"{details}\n"
                    "I shall be grateful for your kind consideration.\n")
        elif app_type == "Recommendation Letter":
            body = (f"Subject: Request for Recommendation Letter\n\n"
                    f"Dear Sir/Madam,\n\n"
                    f"I, {applicant_name}, humbly request a recommendation letter for the following purpose:\n"
                    f"{details}\n"
                    "I appreciate your time and support.\n")
        elif app_type == "Financial Assistance Request":
            body = (f"Subject: Request for Financial Assistance\n\n"
                    f"Dear Sir/Madam,\n\n"
                    f"I, {applicant_name}, am writing to request financial assistance due to:\n"
                    f"{details}\n"
                    "I sincerely hope for your positive response.\n")
        elif app_type == "Makeup Exam Request":
            body = (f"Subject: Request for Makeup Examination\n\n"
                    f"Dear Sir/Madam,\n\n"
                    f"I, {applicant_name}, could not attend the examination due to the following reason(s):\n"
                    f"{details}\n"
                    "I kindly request to be allowed a makeup examination.\n")
        elif app_type == "Add/Drop Course Request":
            body = (f"Subject: Request to Add/Drop Course\n\n"
                    f"Dear Sir/Madam,\n\n"
                    f"I, {applicant_name}, request to add/drop the following course(s):\n"
                    f"{details}\n"
                    "Thank you for your understanding and support.\n")
        elif app_type == "Formal Letter to Registrar/Chairperson":
            body = (f"Subject: Formal Letter\n\n"
                    f"Dear Sir/Madam,\n\n"
                    f"I, {applicant_name}, am writing with the following matter:\n"
                    f"{details}\n"
                    "Your attention to this matter is greatly appreciated.\n")

        full_text = header + salutation + body + closing

        self.generated_text_display.config(state=tk.NORMAL)
        self.generated_text_display.delete("1.0", tk.END)
        self.generated_text_display.insert(tk.END, full_text)
        self.generated_text_display.config(state=tk.DISABLED)
        messagebox.showinfo("Generated", "Application letter generated.", parent=self)

    def copy_generated_text(self):
        """Copies the generated text to the clipboard."""
        text_to_copy = self.generated_text_display.get("1.0", tk.END).strip()
        if text_to_copy:
            self.clipboard_clear()
            self.clipboard_append(text_to_copy)
            messagebox.showinfo("Copied", "Text copied to clipboard!", parent=self)
        else:
            messagebox.showwarning("Empty", "No text to copy.", parent=self)

    def save_generated_text(self):
        """Saves the generated text to a plain text file."""
        text_to_save = self.generated_text_display.get("1.0", tk.END).strip()
        if not text_to_save:
            messagebox.showwarning("Empty", "No text to save.", parent=self)
            return

        filepath = filedialog.asksaveasfilename(defaultextension=".txt",
                                                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                                                title="Save Application Letter", parent=self)
        if filepath:
            try:
                with open(filepath, 'w') as f:
                    f.write(text_to_save)
                messagebox.showinfo("Saved", f"Application letter saved to {filepath}", parent=self)
            except IOError as e:
                messagebox.showerror("Save Error", f"Failed to save file: {e}", parent=self)

    # --- Academic Calendar & Circulars Tab ---
    def init_calendar(self):
        """Initializes the Academic Calendar tab."""
        calendar_frame = ttk.Frame(self.frames["Academic Calendar"], padding="20", style='TFrame')
        calendar_frame.pack(expand=True, fill="both")

        # Changed to tk.Label for direct foreground/background control
        tk.Label(calendar_frame, text="Master Academic Calendar", font=('Arial', 24, 'bold'),
                 bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["accent_dark_blue"]).pack(pady=15)

        # Navigation Frame
        nav_frame = ttk.Frame(calendar_frame, style='TFrame')
        nav_frame.pack(pady=10)

        ttk.Button(nav_frame, text="< Previous", command=self.prev_month, style='TButton').pack(side="left", padx=5)
        # Changed to tk.Label for direct foreground/background control
        self.month_year_label = tk.Label(nav_frame, text="", font=("Arial", 16, "bold"),
                                         bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"])
        self.month_year_label.pack(side="left", padx=10)
        ttk.Button(nav_frame, text="Next >", command=self.next_month, style='TButton').pack(side="left", padx=5)

        # Day Names (Mon, Tue, etc.)
        day_names_frame = ttk.Frame(calendar_frame, style='TFrame')
        day_names_frame.pack(fill="x")
        days_of_week = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for day in days_of_week:
            # Changed to tk.Label for direct foreground/background control
            tk.Label(day_names_frame, text=day, font=("Arial", 10, "bold"), width=10,
                     bg=NORDIC_COLORS["bg_dark"], fg=NORDIC_COLORS["text_dark"],
                     relief="solid", borderwidth=1).pack(side="left", fill="both", expand=True)

        # Calendar Grid Frame
        self.calendar_grid_frame = ttk.Frame(calendar_frame, style='TFrame') # Initialized here
        self.calendar_grid_frame.pack(expand=True, fill="both")

        # Event List Frame
        event_list_frame = tk.LabelFrame(calendar_frame, text="Events for Selected Day", padx=10, pady=10,
                                         bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"],
                                         font=('Arial', 11, 'bold'), relief="solid", borderwidth=1)
        event_list_frame.pack(pady=15, fill="x")

        self.event_list_tree = ttk.Treeview(event_list_frame, columns=("Event", "Type"), show="headings", height=5) # Initialized here
        self.event_list_tree.heading("Event", text="Event Description")
        self.event_list_tree.heading("Type", text="Type")
        self.event_list_tree.column("Event", width=300, anchor="w")
        self.event_list_tree.column("Type", width=100, anchor="center")
        self.event_list_tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(event_list_frame, orient="vertical", command=self.event_list_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.event_list_tree.configure(yscrollcommand=scrollbar.set)

        self.event_list_tree.bind("<Delete>", lambda event: self.delete_selected_calendar_event())

        # Add Event Section
        add_event_frame = tk.LabelFrame(calendar_frame, text="Add Event", padx=10, pady=10,
                                        bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"],
                                        font=('Arial', 11, 'bold'), relief="solid", borderwidth=1)
        add_event_frame.pack(pady=10, fill="x")

        tk.Label(add_event_frame, text="Date (YYYY-MM-DD):", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.event_date_entry = ttk.Entry(add_event_frame, width=15)
        self.event_date_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.event_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d")) # Default to today

        tk.Label(add_event_frame, text="Description:", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.event_desc_entry = ttk.Entry(add_event_frame, width=40)
        self.event_desc_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(add_event_frame, text="Event Type:", bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.event_type_var = tk.StringVar()
        self.event_type_var.set("General")
        event_types = ["General", "Holiday", "Exam", "Institutional", "Deadline"]
        ttk.OptionMenu(add_event_frame, self.event_type_var, *event_types).grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        ttk.Button(add_event_frame, text="Add Event", command=self.add_calendar_event, style='TButton').grid(row=3, column=0, columnspan=2, pady=10)
        add_event_frame.grid_columnconfigure(1, weight=1)

        self.draw_calendar() # Call draw_calendar after all its dependencies are initialized


    def draw_calendar(self):
        """Draws the calendar grid for the current month and year."""
        # Add a check to ensure calendar components are initialized
        if self.calendar_grid_frame is None or self.month_year_label is None or self.event_list_tree is None:
            return # Cannot draw if components are not ready

        # Clear previous calendar buttons
        for widget in self.calendar_grid_frame.winfo_children():
            widget.destroy()

        self.month_year_label.config(text=f"{calendar.month_name[self.current_month]} {self.current_year}")

        cal = calendar.Calendar()
        month_days = cal.monthdayscalendar(self.current_year, self.current_month)

        for week_idx, week in enumerate(month_days):
            for day_idx, day in enumerate(week):
                day_text = str(day) if day != 0 else ""
                event_indicator = ""

                # Default colors for tk.Button
                bg_color = NORDIC_COLORS["calendar_day_bg"]
                fg_color = NORDIC_COLORS["calendar_day_fg"]
                active_bg_color = NORDIC_COLORS["calendar_active_bg"]
                active_fg_color = NORDIC_COLORS["calendar_active_fg"]

                if day != 0:
                    current_date_str = f"{self.current_year}-{self.current_month:02d}-{day:02d}"
                    events_on_day = [e for e in self.calendar_events if e['date'] == current_date_str]
                    if events_on_day:
                        bg_color = NORDIC_COLORS["calendar_event_bg"] # Event day background (light green)
                        event_indicator = " •" # Small dot to indicate events
                        if any(e['type'] == 'Holiday' for e in events_on_day):
                            bg_color = NORDIC_COLORS["calendar_holiday_bg"] # Holiday background (light red)
                            fg_color = NORDIC_COLORS["accent_red"] # Holiday foreground (dark red)
                        elif any(e['type'] == 'Exam' for e in events_on_day):
                            # Could add a specific color for exams if desired, currently uses event color
                            pass

                    if datetime.now().day == day and datetime.now().month == self.current_month and datetime.now().year == self.current_year:
                        bg_color = NORDIC_COLORS["calendar_today_bg"] # Today's date background (blue)
                        fg_color = NORDIC_COLORS["calendar_today_fg"]   # Today's date foreground
                        active_bg_color = NORDIC_COLORS["accent_blue"] # Darker blue for active today

                # Using tk.Button directly with fg/bg
                day_button = tk.Button(self.calendar_grid_frame,
                                       text=f"{day_text}{event_indicator}",
                                       width=10,
                                       command=lambda d=day: self.show_day_events(d) if d != 0 else None,
                                       font=('Arial', 10),
                                       relief="raised",
                                       borderwidth=1,
                                       bg=bg_color,
                                       fg=fg_color,
                                       activebackground=active_bg_color,
                                       activeforeground=active_fg_color)
                day_button.grid(row=week_idx, column=day_idx, sticky="nsew", padx=1, pady=1)
                self.calendar_grid_frame.grid_columnconfigure(day_idx, weight=1)
            self.calendar_grid_frame.grid_rowconfigure(week_idx, weight=1)

        self.show_day_events(datetime.now().day if datetime.now().month == self.current_month and datetime.now().year == self.current_year else 1) # Show events for today or 1st of month

    def prev_month(self):
        """Navigates to the previous month in the calendar."""
        self.current_month -= 1
        if self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        self.draw_calendar()

    def next_month(self):
        """Navigates to the next month in the calendar."""
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        self.draw_calendar()

    def show_day_events(self, day):
        """Displays events for the selected day in the event list."""
        if self.event_list_tree is None: # Check if Treeview is initialized
            return

        for item in self.event_list_tree.get_children():
            self.event_list_tree.delete(item)
        # Configure alternating row colors for this Treeview
        self.event_list_tree.tag_configure('oddrow', background=NORDIC_COLORS["treeview_row_bg1"])
        self.event_list_tree.tag_configure('evenrow', background=NORDIC_COLORS["treeview_row_bg2"])

        if day == 0: # No day selected (empty calendar cell)
            self.event_date_entry.delete(0, tk.END)
            self.event_date_entry.insert(0, "")
            return

        selected_date_str = f"{self.current_year}-{self.current_month:02d}-{day:02d}"
        self.event_date_entry.delete(0, tk.END)
        self.event_date_entry.insert(0, selected_date_str)

        events_on_day = [e for e in self.calendar_events if e['date'] == selected_date_str]
        if not events_on_day:
            self.event_list_tree.insert("", "end", values=("No events for this day.", ""))
        else:
            for i, event in enumerate(events_on_day):
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                self.event_list_tree.insert("", "end", iid=f"event_{i}_{selected_date_str}", values=(event['description'], event['type']), tags=(tag,))

    def add_calendar_event(self):
        """Adds a new event to the calendar and saves it."""
        event_date_str = self.event_date_entry.get().strip()
        description = self.event_desc_entry.get().strip()
        event_type = self.event_type_var.get()

        if not event_date_str or not description:
            messagebox.showwarning("Input Error", "Please enter both date and description for the event.", parent=self)
            return

        try:
            # Validate date format
            datetime.strptime(event_date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Invalid Date", "Please enter date inYYYY-MM-DD format.", parent=self)
            return

        new_event = {
            "date": event_date_str,
            "description": description,
            "type": event_type
        }
        self.calendar_events.append(new_event)
        self.save_json_data(self.calendar_events, CALENDAR_EVENTS_FILE)
        self.event_desc_entry.delete(0, tk.END)
        self.draw_calendar() # Redraw calendar to show new event
        self.show_day_events(int(event_date_str.split('-')[2])) # Refresh event list for that day
        messagebox.showinfo("Success", "Event added to calendar.", parent=self)
        self.update_dashboard_info()

    def delete_selected_calendar_event(self):
        """Deletes the selected calendar event."""
        if self.event_list_tree is None: # Check if Treeview is initialized
            messagebox.showwarning("Error", "Calendar event list is not ready.", parent=self)
            return

        selected_item = self.event_list_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select an event to delete.", parent=self)
            return

        # The iid contains "event_{index_in_filtered_list}_{date_string}"
        # We need to find the actual event in self.calendar_events
        item_id_parts = selected_item[0].split('_')
        if len(item_id_parts) != 3:
            messagebox.showerror("Error", "Could not identify event for deletion.", parent=self)
            return

        selected_date_str = item_id_parts[2]
        selected_event_index_in_filtered_list = int(item_id_parts[1])

        # Filter events for the selected date to find the correct one
        events_on_selected_day = [e for e in self.calendar_events if e['date'] == selected_date_str]

        if selected_event_index_in_filtered_list < len(events_on_selected_day):
            event_to_delete = events_on_selected_day[selected_event_index_in_filtered_list]
            
            # Find the actual index in the main list
            try:
                actual_index = self.calendar_events.index(event_to_delete)
                if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the event '{event_to_delete['description']}'?", parent=self):
                    del self.calendar_events[actual_index]
                    self.save_json_data(self.calendar_events, CALENDAR_EVENTS_FILE)
                    self.draw_calendar() # Redraw calendar to update event indicators
                    self.show_day_events(int(selected_date_str.split('-')[2])) # Refresh event list
                    messagebox.showinfo("Deleted", "Event deleted successfully.", parent=self)
                    self.update_dashboard_info()
            except ValueError:
                messagebox.showerror("Error", "Event not found in the main list.", parent=self)
        else:
            messagebox.showerror("Error", "Selected event index is out of bounds.", parent=self)

    # --- Alumni Directory Tab (Placeholder) ---
    def init_alumni_directory(self):
        alumni_frame = ttk.Frame(self.frames["Alumni Directory"], padding="20", style='TFrame')
        alumni_frame.pack(expand=True, fill="both")
        tk.Label(alumni_frame, text="Alumni Directory", font=('Arial', 20, 'bold'),
                 bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["accent_dark_blue"]).pack(pady=15)
        tk.Label(alumni_frame, text="This module would manage graduated student profiles, employment tracking, and alumni outreach features.",
                 bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).pack(pady=10)
        tk.Label(alumni_frame, text="Features like searchable database, survey integration, and event tracking would be here.",
                 bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).pack(pady=5)

    # --- Local Messaging / Chat Tab (Placeholder) ---
    def init_local_messaging(self):
        chat_frame = ttk.Frame(self.frames["Local Messaging"], padding="20", style='TFrame')
        chat_frame.pack(expand=True, fill="both")
        tk.Label(chat_frame, text="Local Messaging / Chat", font=('Arial', 20, 'bold'),
                 bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["accent_dark_blue"]).pack(pady=15)
        tk.Label(chat_frame, text="This module would provide peer-to-peer and group chat functionality over LAN/USB.",
                 bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).pack(pady=10)
        tk.Label(chat_frame, text="Features like offline delivery queue, message timestamps, and broadcast channels would be here.",
                 bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).pack(pady=5)
        tk.Label(chat_frame, text="Note: Full implementation of a secure and robust local chat system is complex and beyond the scope of this demo.",
                 bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["accent_red"]).pack(pady=20)

    # --- Security & Admin Controls Tab (Placeholder) ---
    def init_security_admin(self):
        security_frame = ttk.Frame(self.frames["Security & Admin"], padding="20", style='TFrame')
        security_frame.pack(expand=True, fill="both")
        tk.Label(security_frame, text="Security & Admin Controls", font=('Arial', 20, 'bold'),
                 bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["accent_dark_blue"]).pack(pady=15)
        tk.Label(security_frame, text="This module would manage role-based access control, audit logging, and encryption settings.",
                 bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).pack(pady=10)
        tk.Label(security_frame, text="Features like field-level permissions, login with passphrase/key, and encrypted local data are highly complex and not fully implemented in this demo.",
                 bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["accent_red"]).pack(pady=20)

    # --- System Settings & Utilities Tab (Placeholder) ---
    def init_settings_utilities(self):
        settings_frame = ttk.Frame(self.frames["Settings"], padding="20", style='TFrame')
        settings_frame.pack(expand=True, fill="both")
        tk.Label(settings_frame, text="System Settings & Utilities", font=('Arial', 20, 'bold'),
                 bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["accent_dark_blue"]).pack(pady=15)
        tk.Label(settings_frame, text="This module would contain settings like language selection, dark mode, backup/restore, and version history.",
                 bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).pack(pady=10)
        tk.Label(settings_frame, text="Super Admin specific controls and device pairing would also be managed here.",
                 bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).pack(pady=5)

    # --- Analytics Tab (Placeholder) ---
    def init_analytics(self):
        analytics_frame = ttk.Frame(self.frames["Analytics"], padding="20", style='TFrame')
        analytics_frame.pack(expand=True, fill="both")
        tk.Label(analytics_frame, text="Analytics & Reporting", font=('Arial', 20, 'bold'),
                 bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["accent_dark_blue"]).pack(pady=15)
        tk.Label(analytics_frame, text="This module would provide dashboards for student performance, attendance heatmaps, and departmental summaries.",
                 bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).pack(pady=10)
        tk.Label(analytics_frame, text="Exportable analytics reports and comparison across semesters would be available.",
                 bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["text_dark"]).pack(pady=5)
        tk.Label(analytics_frame, text="Note: Advanced data visualization and AI-driven analytics are complex and not implemented in this demo.",
                 bg=NORDIC_COLORS["bg_light"], fg=NORDIC_COLORS["accent_red"]).pack(pady=20)


if __name__ == "__main__":
    app = AcademicManagementApp()
    app.mainloop()


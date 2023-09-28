import sys
import sqlite3
import hashlib
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QFileDialog, QLabel, QInputDialog, QMessageBox, QDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QTextBrowser

def create_database(path):
    try:
        conn = sqlite3.connect(path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS otp_secrets (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                secret TEXT NOT NULL,
                otp_type TEXT NOT NULL,
                refresh_time INTEGER NOT NULL,
                company_id INTEGER,
                FOREIGN KEY (company_id) REFERENCES companies (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            )
        """)

        cursor.execute("INSERT INTO companies (name) VALUES ('unbekannt')")
        hashed_password = hashlib.sha256("1234".encode()).hexdigest()
        cursor.execute("INSERT INTO users (username, password) VALUES ('admin', ?)", (hashed_password,))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(e)
        return False

def create_empty_database():
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    file_name, _ = QFileDialog.getSaveFileName(None, "Save Empty Database", "otp.db", "SQLite Database Files (*.db);;All Files (*)", options=options)

    if not file_name:
        return False

    if not file_name.endswith('.db'):
        file_name += '.db'

    try:
        conn = sqlite3.connect(file_name)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS otp_secrets (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                secret TEXT NOT NULL,
                otp_type TEXT NOT NULL,
                refresh_time INTEGER NOT NULL,
                company_id INTEGER,
                FOREIGN KEY (company_id) REFERENCES companies (id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            )
        """)

        cursor.execute("INSERT INTO companies (name) VALUES ('Unknown')")
        hashed_password = hashlib.sha256("1234".encode()).hexdigest()
        cursor.execute("INSERT INTO users (username, password) VALUES ('admin', ?)", (hashed_password,))

        conn.commit()
        conn.close()
        print(f"Empty database created at {file_name}")
        return True
    except Exception as e:
        print(e)
        return False

def fetch_existing_companies(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM companies")
    return [row[0] for row in cursor.fetchall()]

def fetch_existing_users(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users")
    return [row[0] for row in cursor.fetchall()]

def format_list_for_display(items, per_line=3):
    formatted_lines = []
    for i in range(0, len(items), per_line):
        formatted_lines.append(", ".join(items[i:i + per_line]))
    return '\n'.join(formatted_lines)

def clear_database():
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    file_name, _ = QFileDialog.getOpenFileName(None, "Open SQLite Database", "", "SQLite Database Files (*.db);;All Files (*)", options=options)
    
    if not file_name:
        return False

    try:
        conn = sqlite3.connect(file_name)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM otp_secrets")
        cursor.execute("DELETE FROM users")
        cursor.execute("DELETE FROM companies")
        
        conn.commit()
        conn.close()
        print(f"Database cleared at {file_name}")
        return True
    except Exception as e:
        print(e)
        return False

def show_about_dialog():
    dialog = QDialog()
    dialog.setWindowTitle("About TOTP Manager")
    
    dialog.setWindowFlags(Qt.FramelessWindowHint)
    
    dialog.setStyleSheet("background-color: #2E2E2E; color: #FFFFFF;")
    
    layout = QVBoxLayout()
    
    text_browser = QTextBrowser()
    text_browser.setOpenExternalLinks(True)
    text_browser.setStyleSheet("text-align: center;")
    
    text_browser.setHtml(
        '<div style="text-align: center; color: white;">' +
        '<p><strong>SQLite Management Utility for TOTP Manager</strong></p>' +
        '<p>© 2023 Sebastian Junginger. Licensed under Creative Commons.</p>' +
        '<p>For further details and source code, visit the <a href="https://github.com/Migrim/OTP-Manager">TOTP Manager GitHub Repository</a>.</p>' +
        '</div>'
    )
    
    layout.addWidget(text_browser)
    
    h_layout = QHBoxLayout()
    h_layout.addStretch(1)
    
    close_button = QPushButton("Close")
    close_button.setFixedWidth(60) 
    close_button.setFixedHeight(20) 
    close_button.setStyleSheet("background-color: #292D26; color: #77713B;")
    close_button.clicked.connect(dialog.accept)
    
    h_layout.addWidget(close_button)
    
    h_layout.addStretch(1)
    
    layout.addLayout(h_layout)
    
    dialog.setLayout(layout)
    
    dialog.setFixedSize(300, 150)
    
    dialog.exec_()

def add_initial_data(path):
    conn = sqlite3.connect(path)

    add_companies = QMessageBox.question(None, 'Add Companies', 'Do you want to add companies?', QMessageBox.Yes | QMessageBox.No)
    if add_companies == QMessageBox.Yes:
        while True:
            existing_companies = format_list_for_display(fetch_existing_companies(conn))
            company, ok = QInputDialog.getText(None, 'Input', f'Existing companies:\n{existing_companies}\nEnter the company name:')
            if ok and company:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO companies (name) VALUES (?)", (company,))
                conn.commit()
            else:
                break

    add_users = QMessageBox.question(None, 'Add Users', 'Do you want to add users?', QMessageBox.Yes | QMessageBox.No)
    if add_users == QMessageBox.Yes:
        while True:
            existing_users = format_list_for_display(fetch_existing_users(conn))
            username, ok1 = QInputDialog.getText(None, 'Input', f'Existing users:\n{existing_users}\nEnter the username:')
            if ok1 and username:
                password, ok2 = QInputDialog.getText(None, 'Input', 'Enter the password:')
                if ok2 and password:
                    hashed_password = hashlib.sha256(password.encode()).hexdigest()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
                    conn.commit()
                else:
                    break
            else:
                break

    conn.close()

class CustomTitleBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor("#292D26"))
        self.setPalette(palette)

        layout = QHBoxLayout()
        self.title = QLabel("SQLite Database Creator")
        self.title.setStyleSheet("color: #77713B")

        self.close_button = QPushButton("X")
        self.close_button.setStyleSheet("background-color: #292D26; color: #77713B")
        self.close_button.clicked.connect(self.close_app)

        layout.addWidget(self.title)
        layout.addStretch(1)
        layout.addWidget(self.close_button)

        self.setLayout(layout)

    def close_app(self):
        self.parent().close()

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = 'SQLite Database Creator'
        self.initUI()
        self.moving = False
        self.offset = None

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setStyleSheet("background-color: #2E2E2E; color: #FFFFFF")

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.custom_title_bar = CustomTitleBar()
        self.custom_title_bar.setParent(self)
        layout = QVBoxLayout()
        layout.addWidget(self.custom_title_bar)

        self.label = QLabel("Create a new SQL-Database by selecting an option")
        layout.addWidget(self.label)

        self.info_label = QLabel()
        self.info_label.setText('<font color="#FF5252">please make sure the Database is named "OTP.db"</font>')
        layout.addWidget(self.info_label)

        self.button = QPushButton('Create SQLite Database')
        self.button.setStyleSheet("background-color: #292D26; color: #77713B")
        self.button.clicked.connect(self.showDialog)
        layout.addWidget(self.button)

        self.empty_db_button = QPushButton('Create Empty Database')
        self.empty_db_button.setStyleSheet("background-color: #292D26; color: #77713B")
        self.empty_db_button.clicked.connect(create_empty_database)
        layout.addWidget(self.empty_db_button)

        self.clear_db_button = QPushButton('Clear Database')
        self.clear_db_button.setStyleSheet("background-color: #292D26; color: #77713B")
        self.clear_db_button.clicked.connect(clear_database)
        layout.addWidget(self.clear_db_button)

        self.about_button = QPushButton('About')
        self.about_button.setStyleSheet("background-color: #292D26; color: #77713B")
        self.about_button.clicked.connect(show_about_dialog)
        layout.addWidget(self.about_button)
        
        self.setLayout(layout)

    def mousePressEvent(self, event):
        self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.offset is not None:
            self.move(self.pos() + event.pos() - self.offset)

    def mouseReleaseEvent(self, event):
        self.offset = None

    def showDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Database", "otp.db", "SQLite Database Files (*.db);;All Files (*)", options=options)

        if file_name:
            if not file_name.endswith('.db'):
                file_name += '.db'

            if create_database(file_name):
                self.label.setText(f"Database created successfully at {file_name}")
                add_initial_data(file_name)
            else:
                self.label.setText("Failed to create the database.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)

    app.setPalette(dark_palette)
    ex = App()
    ex.show()
    sys.exit(app.exec_())
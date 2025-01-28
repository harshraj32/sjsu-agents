import sys
import subprocess
import webbrowser
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QTextEdit, QLineEdit, QPushButton, QLabel, QTabWidget, QFrame)
from PyQt6.QtCore import Qt, QThread, Signal, QUrl
from PyQt6.QtGui import QFont, QTextCursor, QColor, QAction
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings

STYLESHEET = """
QMainWindow {
    background-color: #2b2b2b;
}

QTextEdit, QLineEdit, QPlainTextEdit {
    background-color: #3c3f41;
    color: #a9b7c6;
    border: 1px solid #4d4d4d;
    border-radius: 4px;
    padding: 8px;
    font-family: 'Consolas', monospace;
}

QPushButton {
    background-color: #4CAF50;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #45a049;
}

QTabWidget::pane {
    border: none;
    background-color: #2b2b2b;
}

QTabBar::tab {
    background: #3c3f41;
    color: #a9b7c6;
    padding: 8px 12px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background: #2b2b2b;
    border-bottom: 2px solid #4CAF50;
}

QLabel {
    color: #a9b7c6;
}
"""

class CommandWorker(QThread):
    command_executed = Signal(str, str)

    def __init__(self, command):
        super().__init__()
        self.command = command

    def run(self):
        try:
            result = subprocess.run(
                self.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=15
            )
            output = result.stdout if result.stdout else result.stderr
        except Exception as e:
            output = str(e)
        
        self.command_executed.emit(self.command, output)

class BrowserWindow(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings().setAttribute(QWebEngineSettings.PluginsEnabled, True)
        self.settings().setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        self.load(QUrl("https://www.google.com"))

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Terminal Assistant")
        self.resize(1400, 900)
        self.setStyleSheet(STYLESHEET)
        
        # Main layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # Chat Section
        chat_frame = QFrame()
        chat_layout = QVBoxLayout(chat_frame)
        chat_layout.setContentsMargins(5, 5, 5, 5)
        
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_input = QLineEdit()
        self.send_button = QPushButton("Send")
        
        chat_layout.addWidget(QLabel("Chat with AI Agent"))
        chat_layout.addWidget(self.chat_history)
        chat_layout.addWidget(self.chat_input)
        chat_layout.addWidget(self.send_button)
        
        # Right Side Tabs
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        
        # Terminal Output Tab
        terminal_tab = QWidget()
        terminal_layout = QVBoxLayout(terminal_tab)
        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        terminal_layout.addWidget(self.output_display)
        
        # Browser Tab
        browser_tab = QWidget()
        browser_layout = QVBoxLayout(browser_tab)
        self.browser = BrowserWindow()
        browser_layout.addWidget(self.browser)
        
        # Add tabs
        self.tabs.addTab(terminal_tab, "Terminal")
        self.tabs.addTab(browser_tab, "Browser")
        
        # Split the window
        layout.addWidget(chat_frame, 40)
        layout.addWidget(self.tabs, 60)
        
        # Connect signals
        self.send_button.clicked.connect(self.process_input)
        self.chat_input.returnPressed.connect(self.process_input)
        
        # Configure fonts
        mono_font = QFont("Consolas", 10)
        self.chat_history.setFont(mono_font)
        self.output_display.setFont(mono_font)
        
        # Initial message
        self.add_chat_message("System", "Welcome to AI Terminal Assistant!", QColor("#4CAF50"))

    def add_chat_message(self, sender, message, color=QColor("#a9b7c6")):
        self.chat_history.setTextColor(color)
        self.chat_history.append(f"{sender}: {message}")
        self.chat_history.moveCursor(QTextCursor.End)

    def add_output(self, command, output):
        self.output_display.setTextColor(QColor("#4CAF50"))
        self.output_display.append(f"$ {command}")
        self.output_display.setTextColor(QColor("#a9b7c6"))
        self.output_display.append(output + "\n")
        self.output_display.moveCursor(QTextCursor.End)

    def process_input(self):
        user_input = self.chat_input.text().strip()
        if not user_input:
            return
        
        self.add_chat_message("You", user_input)
        self.chat_input.clear()
        
        # Handle browser requests
        if any(keyword in user_input.lower() for keyword in ["google", "search", "browse"]):
            self.handle_browser_request(user_input)
            return
        
        # Execute command in background thread
        self.worker = CommandWorker(user_input)
        self.worker.command_executed.connect(self.handle_command_result)
        self.worker.start()

    def handle_command_result(self, command, output):
        self.add_output(command, output)
        self.add_chat_message("AI Agent", output, QColor("#2196F3"))

    def handle_browser_request(self, query):
        self.tabs.setCurrentIndex(1)  # Switch to browser tab
        
        if "search" in query.lower():
            search_terms = query.lower().split("search")[1].strip()
            url = f"https://www.google.com/search?q={search_terms}"
        elif "browse" in query.lower():
            url = query.split("browse")[1].strip()
            if not url.startswith("http"):
                url = f"https://{url}"
        else:
            url = "https://www.google.com"
        
        self.browser.load(QUrl(url))
        self.add_chat_message("System", f"Loading: {url}", QColor("#FFC107"))

if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())
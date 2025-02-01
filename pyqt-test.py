import sys
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QMessageBox, QVBoxLayout

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyQt6 Example")
        self.setGeometry(100, 100, 300, 200)

        self.button = QPushButton("Click Me", self)
        self.button.clicked.connect(self.show_message)

        layout = QVBoxLayout()
        layout.addWidget(self.button)
        self.setLayout(layout)

    def show_message(self):
        QMessageBox.information(self, "Message", "Hello, PyQt6!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec())

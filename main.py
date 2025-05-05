# main.py

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton
from PyQt6.QtCore import Qt

from PyQt6_JsonTextEdit import QJsonTextEdit


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QJsonTextEdit Demo")
        self.resize(600, 400)

        self.text_edit = QJsonTextEdit()

        # Set default JSON
        self.text_edit.setJson({
            "name": "Alice",
            "age": 30,
            "admin": True,
            "roles": ["editor", "moderator"],
            "registered": "2023-04-01T12:00:00Z"
        })

        format_button = QPushButton("Format")
        format_button.clicked.connect(self.text_edit.formatJson)

        minify_button = QPushButton("Minify")
        minify_button.clicked.connect(self.text_edit.minifyJson)

        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        layout.addWidget(format_button)
        layout.addWidget(minify_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

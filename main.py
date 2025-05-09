# main.py

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton

from PyQt6_JsonTextEdit._text_edit import QJsonTextEdit


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QJsonTextEdit Demo")
        self.resize(600, 400)

        self.text_edit = QJsonTextEdit()
        self.text_edit.highlighter()

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

        self.text_edit.jsonFormattingErrorOccurred.connect(
            lambda error: print(f"Formatting error: {error}")
        )
        self.text_edit.jsonValidityChanged.connect(
            lambda is_valid: print(f"JSON validity changed: {is_valid}")
        )

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

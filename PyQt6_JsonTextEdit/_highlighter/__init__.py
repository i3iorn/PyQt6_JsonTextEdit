from PyQt6.QtGui import QSyntaxHighlighter


class QJsonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

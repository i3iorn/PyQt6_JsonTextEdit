from contextlib import contextmanager
from typing import Optional, Type, Union

from PyQt6.QtCore import pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QSyntaxHighlighter, QKeyEvent, QTextCursor
from PyQt6.QtWidgets import QTextEdit

from PyQt6_JsonTextEdit._constants import *
from PyQt6_JsonTextEdit._formatter import QJsonFormatter, JsonFormattingException, QAbstractJsonFormatter
from PyQt6_JsonTextEdit._highlighter import QJsonHighlighter


class QJsonTextEdit(QTextEdit):
    jsonValidityChanged = pyqtSignal(bool)
    jsonFormattingErrorOccurred = pyqtSignal(str)
    jsonChanged = pyqtSignal(str)

    def __init__(self, parent=None, formatter: "QAbstractJsonFormatter" = None, highlighter: QSyntaxHighlighter = None ):
        super().__init__(parent)
        self._previous_state = None
        self._indentation = DEFAULT_INDENTATION
        self._textChangeDelay = DEFAULT_TEXT_CHANGE_DELAY

        self._formatter = formatter or QJsonFormatter()
        self._highlighter = highlighter or QJsonHighlighter()
        self._init_formatter()
        self._init_highlighter()
        self._connect_signals()
        self.jsonValidityChanged.emit(lambda: self.isValid())

    def _init_formatter(self):
        pass

    def _connect_signals(self):
        self._format_timer = QTimer()
        self._format_timer.setSingleShot(True)
        self._format_timer.setInterval(self._textChangeDelay)
        self._format_timer.timeout.connect(self._check_format)
        self.textChanged.connect(self._format_timer.start)
        QTimer.singleShot(0, self._check_format)

    def _init_highlighter(self):
        self._highlighter.setDocument(self.document())

    def formatter(self):
        return self._formatter

    def isValid(self):
        return self._formatter.isValid(self.plainTextJson())

    def plainTextJson(self):
        return self.toPlainText()

    def indentation(self):
        return self._indentation

    def _check_format(self):
        if self.isValid != self._previous_state:
            self.jsonValidityChanged.emit(self.isValid)
            self._previous_state = self.isValid

    def minifyJson(self):
        if self.isValid:
            self.setText(self.minifiedJson())

    def minifiedJson(self):
        try:
            body = self.formatter.format(
                self.plainTextJson, separators=(',', ':')
            ).splitlines()
            body = ''.join(line.strip() for line in body)
            return body
        except JsonFormattingException as e:
            self.jsonFormattingErrorOccurred.emit(str(e))
            return None

    def formatJson(self):
        if self.isValid:
            self.setText(self.formattedJson())

    def formattedJson(self) -> Optional[str]:
        try:
            return self._formatter.format(self.plainTextJson)
        except JsonFormattingException as e:
            self.jsonFormattingErrorOccurred.emit(str(e))
            return None

    def setFormatter(self, formatter: Type[QAbstractJsonFormatter]):
        if not issubclass(formatter, QAbstractJsonFormatter):
            raise JsonFormattingException(f"Formatter must be a subclass of QAbstractJsonFormatter")
        self._formatter = formatter
        self._init_formatter()

    def setHighlighter(self, highlighter: Type[QSyntaxHighlighter]):
        if not issubclass(highlighter, QSyntaxHighlighter):
            raise JsonFormattingException(f"Highlighter must be a subclass of QSyntaxHighlighter")
        self._highlighter = highlighter
        self._init_highlighter()

    def setJson(self, json_object: Union[dict, list]) -> None:
        if not isinstance(json_object, (dict, list)):
            raise TypeError("Only dict or list are valid JSON roots")

        try:
            string = self.formatter.format(json_object)
            self.setText(string)
        except JsonFormattingException as e:
            self.jsonFormattingErrorOccurred.emit(str(e))

    def setJsonFromFile(self, file_path: str) -> None:
        try:
            with open(file_path, "r") as f:
                self.setText(f.read())
        except IOError as e:
            self.jsonFormattingErrorOccurred.emit(str(e))

    def setTextChangeDelay(self, delay: int) -> None:
        if MIN_TEXT_CHANGE_DELAY <= delay <= MAX_TEXT_CHANGE_DELAY:
            self._textChangeDelay = delay
            self._format_timer.setInterval(delay)
        else:
            raise ValueError(TEXT_CHANGE_DELAY_ERR_MSG)

    @contextmanager
    def suppressSignals(self):
        old = self.blockSignals(True)
        try:
            yield
        finally:
            self.blockSignals(old)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()

        if self._maybe_insert_pair(event):
            return

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._handle_newline_indent()
            return

        if key == Qt.Key.Key_Tab:
            self._handle_tab()
            return

        super().keyPressEvent(event)

    def _maybe_insert_pair(self, event: QKeyEvent) -> bool:
        key = event.key()
        pairs = {ord('{'): '}', ord('['): ']', ord('('): ')', ord('"'): '"'}
        if key not in pairs:
            return False

        cursor = self.textCursor()
        opening, closing = chr(key), pairs[key]
        selection = cursor.selectedText()

        # Handle special case: opening brace inserts a block with newline
        if opening == '{' and not selection:
            leading = self._current_line_indent()
            inner_indent = leading + self.indentation()

            snippet = (
                f"{opening}\n"
                f"{' ' * inner_indent}\n"
                f"{' ' * leading}{closing}"
            )

            cursor.insertText(snippet)
            # Move cursor to inner indentation line
            cursor.movePosition(QTextCursor.MoveOperation.Up)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
            self.setTextCursor(cursor)
            return True

        # General case: insert pair and place cursor inside
        cursor.insertText(f"{opening}{selection}{closing}")
        if not selection:
            cursor.movePosition(QTextCursor.MoveOperation.Left)
            self.setTextCursor(cursor)
        return True

    def _handle_newline_indent(self):
        cursor = self.textCursor()
        indent = self._current_line_indent()
        cursor.insertText('\n' + ' ' * indent)

    def _handle_tab(self):
        self.textCursor().insertText(' ' * self.indentation())

    def _current_line_indent(self) -> int:
        cursor = self.textCursor()
        block_text = cursor.block().text()
        return len(block_text) - len(block_text.lstrip(' '))

from contextlib import contextmanager
from typing import Optional, Type, Union

from PyQt6.QtCore import pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QSyntaxHighlighter, QKeyEvent, QTextCursor
from PyQt6.QtWidgets import QTextEdit

from PyQt6_JsonTextEdit._constants import *
from PyQt6_JsonTextEdit._formatter import QJsonFormatter, JsonFormattingException, QAbstractJsonFormatter
from PyQt6_JsonTextEdit._highlighter import QJsonHighlighter

PAIRS = {ord('{'): '}', ord('['): ']', ord('('): ')', ord('"'): '"'}

class QJsonTextEdit(QTextEdit):
    jsonValidityChanged = pyqtSignal(bool)
    jsonFormattingErrorOccurred = pyqtSignal(str)
    jsonChanged = pyqtSignal(str)


    def __init__(
            self,
            parent=None,
            formatter_class: Type["QAbstractJsonFormatter"] = None,
            highlighter_class: Type[QSyntaxHighlighter] = None
    ):
        super().__init__(parent)
        self._highlighter = None
        self._formatterClass = formatter_class or QJsonFormatter
        self._highlighterClass = highlighter_class or QJsonHighlighter
        self._previous_state = None
        self._indentation = DEFAULT_INDENTATION
        self._textChangeDelay = DEFAULT_TEXT_CHANGE_DELAY
        self._init_formatter()
        self._init_highlighter()
        self._connect_signals()
        self.jsonValidityChanged.emit(self.isValid)

    def _init_formatter(self):
        self._formatter = self._formatterClass()

    def _connect_signals(self):
        self._format_timer = QTimer()
        self._format_timer.setSingleShot(True)
        self._format_timer.setInterval(self._textChangeDelay)
        self._format_timer.timeout.connect(self._check_format)
        self.textChanged.connect(self._format_timer.start)
        QTimer.singleShot(0, self._check_format)

    def _init_highlighter(self):
        self._highlighter = self._highlighterClass()
        self._highlighter.setDocument(self.document())

    @property
    def formatter(self) -> QJsonFormatter:
        return self._formatter

    @property
    def isValid(self):
        return self.formatter.isValid(self.plainTextJson())

    def plainTextJson(self):
        return self.toPlainText()

    def indentation(self):
        return self._indentation

    def _check_format(self):
        new_state = self.isValid
        if new_state != self._previous_state:
            self.jsonValidityChanged.emit(new_state)
            self._previous_state = new_state

    def minifyJson(self, *args, **kwargs):
        if self.isValid:
            self.setText(self.minifiedJson())

    def minifiedJson(self):
        try:
            body = self.formatter.format(
                self.plainTextJson(), separators=(',', ':')
            ).splitlines()
            body = ''.join(line.strip() for line in body)
            return body
        except JsonFormattingException as e:
            self.jsonFormattingErrorOccurred.emit(str(e))
            return None
        except Exception as e:
            self.jsonFormattingErrorOccurred.emit(str(e))
            raise e

    def formatJson(self, *args, **kwargs):
        if self.isValid:
            self.setText(self.formattedJson())

    def formattedJson(self) -> Optional[str]:
        try:
            return self.formatter.format(self.plainTextJson())
        except JsonFormattingException as e:
            self.jsonFormattingErrorOccurred.emit(str(e))
            return None

    def setFormatterClass(self, formatter: Type[QAbstractJsonFormatter]):
        if not issubclass(formatter, QAbstractJsonFormatter):
            raise JsonFormattingException(f"Formatter must be a subclass of QAbstractJsonFormatter")
        self._formatterClass = formatter
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
            if self._handle_newline_indent():
                return

        if key == Qt.Key.Key_Tab:
            if self._handle_tab():
                return

        if key == Qt.Key.Key_Space:
            if self._handle_space():
                return

        if key == Qt.Key.Key_Backspace:
            if self._handle_backspace():
                return

        super().keyPressEvent(event)

    def _maybe_insert_pair(self, event: QKeyEvent) -> bool:
        """
        Handles auto-insertion of matching pairs (braces, brackets, parentheses, quotes).

        Returns:
            bool: True if pair was inserted and event handled.
        """
        key = event.key()
        if key not in PAIRS:
            return False

        cursor = self.textCursor()
        opening, closing = chr(key), PAIRS[key]
        selection = cursor.selectedText()

        if opening == '{' and not selection:
            # Insert multi-line brace block with proper indentation
            base_indent = self._current_line_indent()
            indent_str = ' ' * self._indentation
            snippet = (
                f"{opening}\n"
                f"{indent_str * (base_indent // self._indentation + 1)}\n"
                f"{' ' * base_indent}{closing}"
            )
            cursor.insertText(snippet)

            # Move cursor to empty inner line
            cursor.movePosition(QTextCursor.MoveOperation.Up)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
            self.setTextCursor(cursor)
            self._highlighter.rehighlight()
            return True

        # Insert pair around selection or insert empty pair
        cursor.insertText(f"{opening}{selection}{closing}")
        if not selection:
            cursor.movePosition(QTextCursor.MoveOperation.Left)
            self.setTextCursor(cursor)

        self._highlighter.rehighlight()
        return True

    def _handle_newline_indent(self):
        """
        Inserts newline with smart indentation based on the preceding character context.
        """
        cursor = self.textCursor()
        block_text = cursor.block().text()
        current_indent = self._current_line_indent()

        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine,
                            QTextCursor.MoveMode.KeepAnchor)
        line_text = cursor.selectedText().rstrip()
        cursor.clearSelection()

        trailing_char = line_text[-1] if line_text else ''

        if trailing_char == '"':
            cursor.insertText(',\n' + ' ' * current_indent)
        elif trailing_char in '{[(':
            cursor.insertText('\n' + ' ' * (current_indent + self._indentation))
        else:
            cursor.insertText('\n' + ' ' * current_indent)

        self.setTextCursor(cursor)

        return True

    def _handle_tab(self):
        """
        Inserts spaces equal to indentation level instead of a literal tab character.
        """
        cursor = self.textCursor()
        cursor.insertText(' ' * self._indentation)
        self.setTextCursor(cursor)
        return True

    def _handle_space(self):
        """
        Handles intelligent space insertion — moves over closing brackets if space precedes them.
        """
        cursor = self.textCursor()

        # Peek at next character after cursor
        doc = self.document()
        pos = cursor.position()
        next_char = doc.characterAt(pos)

        if next_char in PAIRS.values() or next_char == '"':
            # Skip over closing symbol, insert space
            cursor.movePosition(QTextCursor.MoveOperation.Right)
            cursor.insertText(' ')
            self.setTextCursor(cursor)
            return True
        return False

    def _handle_backspace(self):
        cursor = self.textCursor()

        if not cursor.atStart():
            # If there is only whitespace before the cursor, remove it
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine, QTextCursor.MoveMode.KeepAnchor)
            selected_text = cursor.selectedText()
            if selected_text.isspace():
                cursor.insertText("")
                self.setTextCursor(cursor)
                return True

        return False

    def _current_line_indent(self) -> int:
        cursor = self.textCursor()
        block_text = cursor.block().text()
        return len(block_text) - len(block_text.lstrip(' '))

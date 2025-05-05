import functools
import json
from contextlib import contextmanager
from typing import Union, Optional, Type

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtGui import QSyntaxHighlighter, QTextFormat
from PyQt6.QtWidgets import QTextEdit

from PyQt6_JsonTextEdit._formatter import QJsonFormatter, JsonFormattingException
from PyQt6_JsonTextEdit._highlighter import QJsonHighlighter


_MIN_INDENTATION = 0
_MAX_INDENTATION = 10
_INDENTATION_ERR_MSG = "Indentation is out of range"

_MIN_TEXT_CHANGE_DELAY = 0
_MAX_TEXT_CHANGE_DELAY = 1000
_DEFAULT_TEXT_CHANGE_DELAY = 100
_TEXT_CHANGE_DELAY_ERR_MSG = "Text change delay is out of range"


class QJsonTextEdit(QTextEdit):
    jsonValidityChanged = pyqtSignal(bool)
    jsonFormattingErrorOccurred = pyqtSignal(str)
    jsonChanged = pyqtSignal(str)

    def __init__(self, parent=None, formatter: "QAbstractJsonFormatter" = None, highlighter: QSyntaxHighlighter = None ):
        super().__init__(parent)
        self._previous_state = None
        self._textChangeDelay = _DEFAULT_TEXT_CHANGE_DELAY

        self._formatter = formatter or QJsonFormatter()
        self._highlighter = highlighter or QJsonHighlighter()
        self._init_formatter()
        self._init_highlighter()
        self._connect_signals()
        self.jsonValidityChanged.emit()

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

    @property
    def formatter(self):
        return self._formatter

    @property
    def isValid(self):
        return self._formatter.isValid(self.plainTextJson)

    @property
    def plainTextJson(self):
        return self.toPlainText()

    def _check_format(self):
        if self.isValid != self._previous_state:
            self.jsonValidityChanged.emit(self.isValid)
            self._previous_state = self.isValid

    def minifyJson(self):
        if self.isValid:
            self.setText(self.minifiedJson)

    @property
    def minifiedJson(self):
        try:
            return self.formatter.format(self.plainTextJson, separators=(',', ':')).replace("\n", "")
        except JsonFormattingException as e:
            self.jsonFormattingErrorOccurred.emit(str(e))
            return None

    def formatJson(self):
        if self.isValid:
            self.setText(self.formattedJson)

    @property
    def formattedJson(self) -> Optional[str]:
        try:
            return self._formatter.format(self.plainTextJson)
        except JsonFormattingException as e:
            self.jsonFormattingErrorOccurred.emit(str(e))
            return None

    def setHighlighter(self, highlighter: Type[QSyntaxHighlighter]):
        if not issubclass(highlighter, QSyntaxHighlighter):
            raise JsonFormattingException(_TEXT_CHANGE_DELAY_ERR_MSG)

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
        if _MIN_TEXT_CHANGE_DELAY <= delay <= _MAX_TEXT_CHANGE_DELAY:
            self._textChangeDelay = delay
            self._format_timer.setInterval(delay)
        else:
            raise ValueError(_TEXT_CHANGE_DELAY_ERR_MSG)

    @contextmanager
    def suppressSignals(self):
        old = self.blockSignals(True)
        try:
            yield
        finally:
            self.blockSignals(old)

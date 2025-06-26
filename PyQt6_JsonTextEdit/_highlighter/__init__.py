import re
from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import (
    QColor, QFont, QTextCharFormat, QSyntaxHighlighter, QTextDocument, QPalette
)
from PyQt6.QtWidgets import QApplication


class QJsonHighlighter(QSyntaxHighlighter):
    """
    Robust JSON syntax highlighter that supports minified and formatted JSON.
    Prioritizes rule order and avoids overlapping matches.
    """

    def __init__(self, document: QTextDocument = None) -> None:
        super().__init__(document)
        self._rules = []

        app = QApplication.instance()
        base = (app.palette() if app else QPalette()).color(QPalette.ColorRole.Base)
        dark = base.lightness() < 128

        pal = {
            'brace':    '#acacac' if dark else '#888888',
            'quote':    '#cccccc' if dark else '#888888',
            'sep':      '#acacac' if dark else '#707070',
            'key':      '#f0a966' if dark else '#b03060',
            'datetime': '#56b6c2' if dark else '#008b8b',
            'date':     '#98c379' if dark else '#006400',
            'upper':    '#ffb86c' if dark else '#b22222',
            'string':   '#a9dc76' if dark else '#006400',
            'number':   '#f8f802' if dark else '#00008b',
            'bool':     '#ff79c6' if dark else '#8b008b',
        }

        # 1. Keys: "key":
        self._add(r'"([^"\\]*(?:\\.[^"\\]*)*)"\s*:', pal['key'], group=1, bold=True)

        # 2. ISO 8601 datetime
        iso_dt = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?'
        self._add(rf'"({iso_dt})"', pal['datetime'], group=1)

        # 3. ISO Date only
        iso_d = r'\d{4}-\d{2}-\d{2}'
        self._add(rf'"({iso_d})"', pal['date'], group=1)

        # 4. UPPERCASE constants
        self._add(r'"([A-Z0-9_]{2,})"', pal['upper'], group=1)

        # 5. Strings: match only those NOT followed by colon (avoid matching keys again)
        self._add(r'"([^"\\]*(?:\\.[^"\\]*)*)"\s*(?=[,\]}])', pal['string'], group=1)

        # 6. Numbers
        self._add(r'-?\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b', pal['number'])

        # 7. true/false/null
        self._add(r'\b(?:true|false|null)\b', pal['bool'], case_insensitive=True)

        # 8. Quotes (punctuation)
        self._add(r'"', pal['quote'])

        # 9. Commas and colons
        self._add(r'[,:]', pal['sep'])

        # 10. Braces/brackets
        self._add(r'[\{\}\[\]]', pal['brace'])

        # 11. Match anything else (fallback)
        self._add(r'.', pal["string"], group=0, bold=False, case_insensitive=True)

    def _add(
        self,
        pattern: str,
        color: str,
        group: int = 0,
        bold: bool = False,
        case_insensitive: bool = False,
    ) -> None:
        """
        Add a syntax highlighting rule.

        Args:
            pattern: Regex pattern string.
            color: Hex color string.
            group: Capturing group to highlight.
            bold: Whether to apply bold styling.
            case_insensitive: Case insensitive matching.
        """
        regex = QRegularExpression(pattern)
        opts = QRegularExpression.PatternOption.NoPatternOption
        if case_insensitive:
            opts |= QRegularExpression.PatternOption.CaseInsensitiveOption
        regex.setPatternOptions(opts)

        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Weight.DemiBold)

        self._rules.append((regex, fmt, group))

    def highlightBlock(self, text: str) -> None:
        """
        Override to enforce rule priority and prevent overlapping formatting.
        """
        matched_spans = []

        def overlaps(start: int, length: int) -> bool:
            return any(s <= start < s + l or start <= s < start + length for s, l in matched_spans)

        for regex, fmt, group in self._rules:
            it = regex.globalMatch(text)
            while it.hasNext():
                match = it.next()
                start = match.capturedStart(group)
                length = match.capturedLength(group)
                if start >= 0 and length > 0 and not overlaps(start, length):
                    self.setFormat(start, length, fmt)
                    matched_spans.append((start, length))

    def setEnabled(self, enabled: bool) -> None:
        """Enable or disable the highlighter."""
        if enabled:
            self.rehighlight()
        else:
            self.setCurrentBlockState(-1)
            self.setFormat(0, len(self.document().toPlainText()), QTextCharFormat())

    def setDisabled(self, disabled: bool) -> None:
        """Convenience wrapper."""
        self.setEnabled(not disabled)

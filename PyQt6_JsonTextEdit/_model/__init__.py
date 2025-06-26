import logging
from typing import Any, Optional, List

from PyQt6.QtCore import QAbstractItemModel, QModelIndex, QObject, Qt
from PyQt6_JsonTextEdit._model.tree_item import TreeItem

logger = logging.getLogger(__name__)


class QJsonModel(QAbstractItemModel):
    """An editable model of JSON data using TreeItem as backing nodes."""

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self._rootItem = TreeItem()
        self._headers = ("key", "value")

    def appendRows(self, items: list[TreeItem], parent: QModelIndex = QModelIndex()) -> None:
        """Append multiple TreeItems as children of the given parent index."""
        parent_item = parent.internalPointer() if parent.isValid() else self._rootItem
        position = parent_item.childCount()

        self.beginInsertRows(parent, position, position + len(items) - 1)
        for i, item in enumerate(items):
            item.setParent(parent_item)
            parent_item.appendChild(item)

            for col, value in enumerate((item.key, item.value)):
                index = self.index(position + i, col, parent)
                self.setData(index, value, Qt.ItemDataRole.EditRole)
        self.endInsertRows()

    def appendRow(self, item_candidate: List[str] | TreeItem, parent: QModelIndex = QModelIndex()) -> None:
        """Append a single item (TreeItem or [key, value] list) under the given parent index."""
        parent_item = parent.internalPointer() if parent.isValid() else self._rootItem
        position = parent_item.childCount()

        self.beginInsertRows(parent, position, position)

        if isinstance(item_candidate, list):
            if len(item_candidate) != 2:
                raise ValueError("Row must be [key, value]")
            item = TreeItem()
            item.setParent(parent_item)
            parent_item.appendChild(item)
        elif isinstance(item_candidate, TreeItem):
            item = item_candidate
            item.setParent(parent_item)
            parent_item.appendChild(item)
        else:
            raise TypeError("item_candidate must be list[str] or TreeItem")

        self.endInsertRows()

        # Trigger display update via setData()
        for col, value in enumerate((item.key, item.value)):
            index = self.index(position, col, parent)
            self.setData(index, value, Qt.ItemDataRole.EditRole)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        parent_item = parent.internalPointer() if parent.isValid() else self._rootItem
        return parent_item.childCount()

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._headers)

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        parent_item = parent.internalPointer() if parent.isValid() else self._rootItem
        child_item = parent_item.child(row)
        return self.createIndex(row, column, child_item) if child_item else QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()
        child_item = index.internalPointer()
        parent_item = child_item.parent()
        if parent_item is None or parent_item == self._rootItem:
            return QModelIndex()
        return self.createIndex(parent_item.row(), 0, parent_item)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        item = index.internalPointer()
        if role == Qt.ItemDataRole.DisplayRole:
            return item.key if index.column() == 0 else item.display_value()
        return None

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        if not index.isValid():
            return False
        item = index.internalPointer()
        if index.column() == 0:
            item.key = value
        elif index.column() == 1:
            item.value = value
        else:
            return False
        self.dataChanged.emit(index, index, [role])
        return True

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._headers[section]
        return None

    def setHorizontalHeaderLabels(self, labels: list[str]) -> None:
        self._headers = labels
        self.headerDataChanged.emit(Qt.Orientation.Horizontal, 0, len(labels) - 1)

    def load_json(self, data: Any) -> bool:
        """Reset the entire model to represent the new JSON data."""
        self.beginResetModel()
        logger.debug("Loading JSON data into model. Type: %s", type(data))
        self._rootItem = TreeItem.parse(value=data)
        self.endResetModel()
        return True

    def setStringList(self, string_list: list[str]) -> None:
        """Replace model with one string per item."""
        self.beginResetModel()
        self._rootItem = TreeItem()
        for string in string_list:
            item = TreeItem(parent=self._rootItem)
            item.value = string
            self._rootItem.appendChild(item)
        self.endResetModel()

    def to_json(self, item: Optional[TreeItem] = None) -> Any:
        """Convert the tree back into native Python JSON types."""
        item = item or self._rootItem
        if item.value_type is dict:
            return {ch.key: self.to_json(ch) for ch in item._children}
        elif item.value_type is list:
            return [self.to_json(ch) for ch in item._children]
        else:
            return item.value

    def invisibleRootItem(self) -> TreeItem:
        """Expose the invisible root item."""
        return self._rootItem

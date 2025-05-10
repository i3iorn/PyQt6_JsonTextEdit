from PyQt6.QtWidgets import QTreeView
from PyQt6.QtCore import Qt

class QJsonTreeView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.setHeaderHidden(False)
        self.setUniformRowHeights(True)
        self.setExpandsOnDoubleClick(True)
        self.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
        self.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)
        self.setSortingEnabled(False)
        self.setRootIsDecorated(True)

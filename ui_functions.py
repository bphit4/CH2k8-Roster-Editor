import sys
import struct
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QTableWidget,
                             QTableWidgetItem, QMenuBar, QMenu, QAction,
                             QFileDialog, QMessageBox, QLabel, QUndoStack, QUndoCommand)
from PyQt5.QtCore import Qt
import chardet
import csv

class CustomTableWidget(QTableWidget):
    def __init__(self, *args, **kwargs):
        super(CustomTableWidget, self).__init__(*args, **kwargs)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)
        self.clipboard_data = []

    def context_menu(self, pos):
        menu = QMenu()

        undo_action = menu.addAction("Undo")
        redo_action = menu.addAction("Redo")
        menu.addSeparator()
        cut_action = menu.addAction("Cut")
        copy_action = menu.addAction("Copy")
        paste_action = menu.addAction("Paste")
        delete_action = menu.addAction("Delete")
        menu.addSeparator()
        select_all_action = menu.addAction("Select All")
        menu.addSeparator()
        hide_columns_action = menu.addAction("Hide Columns")
        show_all_columns_action = menu.addAction("Show All Columns")

        action = menu.exec_(self.viewport().mapToGlobal(pos))

        if action == undo_action:
            self.undo()
        elif action == redo_action:
            self.redo()
        elif action == cut_action:
            self.cut()
        elif action == copy_action:
            self.copy()
        elif action == paste_action:
            self.paste()
        elif action == delete_action:
            self.delete()
        elif action == select_all_action:
            self.selectAll()
        elif action == hide_columns_action:
            self.hideColumns()
        elif action == show_all_columns_action:
            self.showAllColumns()

    def undo(self):
        self.parent().undo_stack.undo()

    def redo(self):
        self.parent().undo_stack.redo()

    def cut(self):
        self.copy()
        self.delete()

    def copy(self):
        self.clipboard_data.clear()
        for cell_range in self.selectedRanges():
            for row in range(cell_range.topRow(), cell_range.bottomRow() + 1):
                for col in range(cell_range.leftColumn(), cell_range.rightColumn() + 1):
                    item = self.item(row, col)
                    if item:
                        self.clipboard_data.append(((row, col), item.text()))

    def paste(self):
        if self.clipboard_data:
            row_offset = self.currentRow() - self.clipboard_data[0][0][0]
            col_offset = self.currentColumn() - self.clipboard_data[0][0][1]
            for (row, col), text in self.clipboard_data:
                new_row = row + row_offset
                new_col = col + col_offset
                if 0 <= new_row < self.rowCount() and 0 <= new_col < self.columnCount():
                    existing_item = self.item(new_row, new_col)
                    if existing_item is None:
                        existing_item = QTableWidgetItem("")
                        existing_item.setData(Qt.UserRole, "")
                        self.setItem(new_row, new_col, existing_item)
                    elif existing_item.data(Qt.UserRole) is None:
                        existing_item.setData(Qt.UserRole, existing_item.text())
                    existing_item.setText(text)

    def delete(self):
        for cell_range in self.selectedRanges():
            for row in range(cell_range.topRow(), cell_range.bottomRow() + 1):
                for col in range(cell_range.leftColumn(), cell_range.rightColumn() + 1):
                    existing_item = self.item(row, col)
                    if existing_item is None:
                        existing_item = QTableWidgetItem("")
                        existing_item.setData(Qt.UserRole, "")
                        self.setItem(row, col, existing_item)
                    elif existing_item.data(Qt.UserRole) is None:
                        existing_item.setData(Qt.UserRole, existing_item.text())
                    existing_item.setText("")

    def hideColumns(self):
        selected_columns = set()
        for cell_range in self.selectedRanges():
            for col in range(cell_range.leftColumn(), cell_range.rightColumn() + 1):
                selected_columns.add(col)
        for col in selected_columns:
            self.setColumnHidden(col, True)

    def showAllColumns(self):
        for col in range(self.columnCount()):
            self.setColumnHidden(col, False)

class MultiEditCommand(QUndoCommand):
    def __init__(self, table, changes):
        super().__init__()
        self.table = table
        self.changes = changes

    def undo(self):
        for row, col, old_value, _ in self.changes:
            item = QTableWidgetItem(old_value)
            item.setData(Qt.UserRole, old_value)
            self.table.setItem(row, col, item)

    def redo(self):
        for row, col, _, new_value in self.changes:
            item = QTableWidgetItem(new_value)
            item.setData(Qt.UserRole, new_value)
            self.table.setItem(row, col, item)

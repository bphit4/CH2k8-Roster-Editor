import sys
import struct
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QTableWidget,
                             QTableWidgetItem, QMenuBar, QMenu, QAction,
                             QFileDialog, QMessageBox, QLabel, QUndoStack, QUndoCommand)
from PyQt5.QtCore import Qt
import chardet
import csv
from PyQt5.QtWidgets import QComboBox
from Conference_Offsets import conference_offsets

class RosterEditor(QWidget):
    def __init__(self, *args, **kwargs):
        super(RosterEditor, self).__init__(*args, **kwargs)
        self.initUI()
        self.roster_file_path = None
        self.team_data = []
        self.table.itemChanged.connect(self.cell_changed)

    def initUI(self):
        self.setGeometry(100, 100, 1200, 1000)
        self.setWindowTitle("College Hoops 2k8 Roster Editor")

        vbox = QVBoxLayout()

        # Create a menu bar
        menu_bar = QMenuBar()

        file_menu = QMenu("File", self)
        menu_bar.addMenu(file_menu)

        open_action = QAction("Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_roster_file)
        file_menu.addAction(open_action)

        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_roster_file)
        file_menu.addAction(save_action)

        close_action = QAction("Close", self)
        close_action.setShortcut("Ctrl+W")
        close_action.triggered.connect(self.close_roster_file)
        file_menu.addAction(close_action)

        vbox.setMenuBar(menu_bar)

        # Create a label to display the file name
        self.file_label = QLabel()
        vbox.addWidget(self.file_label)

        # Create an empty table
        self.table = CustomTableWidget()
        vbox.addWidget(self.table)

        # Create the context menu for the table
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.create_context_menu)

        # Edit menu
        edit_menu = QMenu("Edit", self)
        menu_bar.addMenu(edit_menu)
        
        undo_action = QAction("Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("Redo", self)
        redo_action.setShortcut("Ctrl+Shift+Z")
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        cut_action = QAction("Cut", self)
        cut_action.setShortcut("Ctrl+X")
        cut_action.triggered.connect(self.cut)
        edit_menu.addAction(cut_action)
        
        copy_action = QAction("Copy", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy)
        edit_menu.addAction(copy_action)
        
        paste_action = QAction("Paste", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.paste)
        edit_menu.addAction(paste_action)

        self.undo_stack = QUndoStack(self)

        file_menu.addSeparator()  # Add this line to insert a separator
        import_action = file_menu.addAction("Import")
        import_action.triggered.connect(self.import_data)
        import_action.setShortcut("Ctrl+I")
        export_action = file_menu.addAction("Export")
        export_action.triggered.connect(self.export_data)
        export_action.setShortcut("Ctrl+E")

        header_labels = ["Team Name", "Team Abbr", "Team Name 2", "Team Nickname", "Team Mascot", "Conference"]
        self.table.setHorizontalHeaderLabels(header_labels)

        self.setLayout(vbox)

    def open_roster_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file, _ = QFileDialog.getOpenFileName(self, "Open Roster File", "", "All Files (*)", options=options)

        if file:
            self.roster_file_path = file
            self.team_data = self.read_roster_file(self.roster_file_path)
            self.display_team_data(self.team_data)
            self.file_label.setText(self.roster_file_path)

    def save_roster_file(self):
        if self.roster_file_path:
            self.write_roster_file(self.roster_file_path, self.team_data)
        else:
            self.save_roster_file_as()

    def save_roster_file_as(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file, _ = QFileDialog.getSaveFileName(self, "Save Roster File As", "", "All Files (*)", options=options)

        if file:
            self.roster_file_path = file
            self.write_roster_file(self.roster_file_path)

    def close_roster_file(self):
        if self.roster_file_path:
            if any(self.is_item_changed(QTableWidgetItem(team_data[col]), self.table.item(row, col)) for row, team_data in enumerate(self.team_data) for col in range(6)):
                reply = QMessageBox.question(self, "Close Roster File", "There are unsaved changes. Are you sure you want to close the roster file?", QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.roster_file_path = None
                    self.table.clear()
                    self.table.setRowCount(0)
                    self.table.setColumnCount(0)
                    self.file_label.setText("")
            else:
                self.roster_file_path = None
                self.table.clear()
                self.table.setRowCount(0)
                self.table.setColumnCount(0)
                self.file_label.setText("")

    def create_context_menu(self, position):
        menu = QMenu()
        cut_action = menu.addAction("Cut")
        copy_action = menu.addAction("Copy")
        paste_action = menu.addAction("Paste")
        delete_action = menu.addAction("Delete")

        cut_action.triggered.connect(self.cut_item)
        copy_action.triggered.connect(self.copy_item)
        paste_action.triggered.connect(self.paste_item)
        delete_action.triggered.connect(self.delete_item)

        menu.exec_(self.table.viewport().mapToGlobal(position))

    def cut_item(self):
        self.copy_item()
        self.delete_item()

    def copy_item(self):
        self.clipboard_item = self.table.currentItem()

    def paste_item(self):
        if self.clipboard_item:
            row = self.table.currentRow()
            col = self.table.currentColumn()
            if row != -1 and col != -1:
                self.table.setItem(row, col, QTableWidgetItem(self.clipboard_item))

    def delete_item(self):
        row = self.table.currentRow()
        col = self.table.currentColumn()
        if row != -1 and col != -1:
            self.table.setItem(row, col, QTableWidgetItem(""))

    def cut(self):
        selected_items = self.table.selectedItems()
        if selected_items:
            clipboard = QApplication.clipboard()
            clipboard.clear()
            clipboard.setText(selected_items[0].text())
            selected_items[0].setText("")

    def copy(self):
        selected_items = self.table.selectedItems()
        if selected_items:
            clipboard = QApplication.clipboard()
            clipboard.clear()
            clipboard.setText(selected_items[0].text())

    def paste(self):
        selected_items = self.table.selectedItems()
        if selected_items:
            clipboard = QApplication.clipboard()
            selected_items[0].setText(clipboard.text())

    def undo(self):
        self.undo_stack.undo()

    def redo(self):
        self.undo_stack.redo()

    # Override mousePressEvent and keyPressEvent to handle right-clicks and hotkeys
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            index = self.table.indexAt(event.pos())
            if index.isValid():
                self.table.setCurrentIndex(index)
                self.create_context_menu(event.pos())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_C and (event.modifiers() & Qt.ControlModifier):
            self.copy_item()
        elif event.key() == Qt.Key_X and (event.modifiers() & Qt.ControlModifier):
            self.cut_item()
        elif event.key() == Qt.Key_V and (event.modifiers() & Qt.ControlModifier):
            self.paste_item()
        elif event.key() == Qt.Key_Delete:
            self.delete_item()
        elif event.key() == Qt.Key_O:
            self.open_item()
        elif event.key() == Qt.Key_S:
            self.save_item()
        elif event.key() == Qt.Key_W:
            self.close_item()
        elif event.key() == Qt.Key_E:
            self.export_item()
        elif event.key() == Qt.Key_I:
            self.import_item()
        else:
            super().keyPressEvent(event)

    def cell_changed(self, item):
        old_value = item.data(Qt.UserRole)
        new_value = item.text()
        if old_value is None or old_value == new_value:
            return
        command = EditCommand(self.table, item.row(), item.column(), old_value, new_value)
        self.table.undo_stack.push(command)
        item.setData(Qt.UserRole, new_value)

    def load_conference_data(self):
        for name, offset in conference_offsets.items():
            self.conference_data[name] = offset

    def read_roster_file(self, file_path):
        with open(file_path, "rb") as file:
            data = file.read()

        file_length = struct.unpack(">I", data[0:4])[0]
        team_info_start = 0x1D8614
        team_info_end = 0x224860
        team_info_length = 0x2C0

        team_count = (team_info_end - team_info_start) // team_info_length
        team_data = []

        for i in range(team_count):
            team_offset = team_info_start + (i * team_info_length)
            team_name_ptr = team_offset + struct.unpack(">I", data[team_offset:team_offset+4])[0]
            team_abbr_ptr = team_offset + struct.unpack(">I", data[team_offset+4:team_offset+8])[0] + 4
            team_name2_ptr = team_offset + struct.unpack(">I", data[team_offset+8:team_offset+12])[0] + 8
            team_nickname_ptr = team_offset + struct.unpack(">I", data[team_offset+12:team_offset+16])[0] + 12
            team_mascot_ptr = team_offset + struct.unpack(">I", data[team_offset+16:team_offset+20])[0] + 16
            
            team_name = self.read_string(data, team_name_ptr)
            team_abbr = self.read_string(data, team_abbr_ptr)
            team_name2 = self.read_string(data, team_name2_ptr)
            team_nickname = self.read_string(data, team_nickname_ptr)
            team_mascot = self.read_string(data, team_mascot_ptr)

            conference_pointer_offset = team_offset + 24
            conference_pointer = struct.unpack(">I", data[conference_pointer_offset:conference_pointer_offset + 4])[0]
            conference_offset = team_offset + conference_pointer
            conference_name = self.read_string(data, conference_offset)

            team_data.append((team_name, team_abbr, team_name2, team_nickname, team_mascot, conference_name))

        return team_data

    def read_string(self, data, pointer):
        string = b""
        while data[pointer:pointer+2] != b'\x00\x00':
            string += data[pointer:pointer+2]
            pointer += 2
        string += b'\x00\x00'
        return string.decode("utf-16-le", errors="surrogatepass").rstrip('\x00')

    def display_team_data(self, team_data):
        self.table.setColumnCount(6)
        self.table.setRowCount(len(team_data))
        self.table.setHorizontalHeaderLabels(["Team Name", "Abbreviation", "Team Name 2", "Nickname", "Mascot Name", "Conference"])

        for i, (team_name, team_abbr, team_name2, team_nickname, team_mascot, conference_name) in enumerate(team_data):
            self.table.setItem(i, 0, QTableWidgetItem(team_name))
            self.table.setItem(i, 1, QTableWidgetItem(team_abbr))
            self.table.setItem(i, 2, QTableWidgetItem(team_name2))
            self.table.setItem(i, 3, QTableWidgetItem(team_nickname))
            self.table.setItem(i, 4, QTableWidgetItem(team_mascot))

        # Set the column widths
        self.table.setColumnWidth(0, 170)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 170)
        self.table.setColumnWidth(3, 170)
        self.table.setColumnWidth(4, 170)

            # Add a QTableWidgetItem with a QComboBox for the Conference column
        conference_item = QTableWidgetItem()
        conference_combobox = QComboBox()

        for name, offset in self.conference_data.items():
            conference_combobox.addItem(name, userData=offset)
            conference_combobox.setCurrentText(conference_name)
            self.table.setCellWidget(i, 5, conference_combobox)
            self.table.setItem(i, 5, conference_item)

    def is_item_changed(self, original_item, edited_item):
        return original_item.text() != edited_item.text()

    # Add this new function to the RosterEditor class
    def is_string_used_elsewhere(self, data, team_info_start, team_info_end, team_info_length, old_string_pointer, i, j):
        for search_offset in range(team_info_start, team_info_end, team_info_length):
            for search_col in range(6):
                if search_col == j:
                    continue
                pointer = struct.unpack(">I", data[search_offset + search_col * 4:search_offset + (search_col + 1) * 4])[0]
                if old_string_pointer == (search_offset + pointer):
                    return True

        # Search the table in the editor for a duplicate string
        for row in range(self.table.rowCount()):
            for col in range(6):
                if row == i and col == j:
                    continue
                cell_text = self.table.item(row, col).text()
                if cell_text == self.table.item(i, j).text():
                    return True

        return False

    def find_string_in_pool(self, data, string_pool_start, string_to_find):
        pointer = string_pool_start
        while pointer < len(data):
            current_string = self.read_string(data, pointer)
            if current_string.encode("utf-16-le") + b'\x00\x00' == string_to_find:
                return pointer
            pointer += (len(current_string) + 1) * 2
        return -1

    def write_roster_file(self, file_path, team_data):
        with open(file_path, "rb") as file:
            data = bytearray(file.read())

        team_info_start = 0x1D8614
        team_info_length = 0x2C0
        data_offset = 0x3CBFE0
        string_pool_start = 0x362CF8

        team_count = len(team_data)
        team_info_end = team_info_start + team_count * team_info_length

        # Find a space with at least 10 null bytes after data_offset
        consecutive_null_bytes = 0
        while consecutive_null_bytes < 10:
            if data[data_offset:data_offset + 2] == b'\x00\x00':
                consecutive_null_bytes += 2
            else:
                consecutive_null_bytes = 0
            data_offset += 2

        # Move back to the start of the 10 null bytes sequence
        data_offset -= 10

        # Add 2 null bytes as a separator if there is data at data_offset
        if data_offset > 0x3CBFE0:
            data_offset += 2

        for i, (team_name, team_abbr, team_name2, team_nickname, team_mascot) in enumerate(team_data):
            team_offset = team_info_start + (i * team_info_length)

            # Check if the Conference column is changed
            new_conference_combobox = self.table.cellWidget(i, 5)
            new_conference_name = new_conference_combobox.currentText()
            if conference_name != new_conference_name:
                # Calculate the new length for the conference pointer and update the value
                new_conference_offset = new_conference_combobox.currentData()
                new_pointer_value = new_conference_offset - (team_offset + 24)
                struct.pack_into(">I", data, team_offset + 24, new_pointer_value)

            items_changed = [self.is_item_changed(QTableWidgetItem(name), self.table.item(i, j)) for j, name in enumerate((team_name, team_abbr, team_name2, team_nickname, team_mascot))]

            if any(items_changed):
                pointers = [struct.unpack(">I", data[team_offset + j * 4:team_offset + (j + 1) * 4])[0] for j in range(6)]

                for j, changed in enumerate(items_changed):
                    if changed:
                        new_string = self.table.item(i, j).text().encode("utf-16-le") + b'\x00\x00'
                        old_string_pointer = team_offset + pointers[j]
                        old_string = self.read_string(data, old_string_pointer).encode("utf-16-le") + b'\x00\x00'
                        old_value = QTableWidgetItem(os.name)
                        new_value = self.table.item(i, j)
                        command = EditCommand(self.table, i, j, old_value.text(), new_value.text())
                        self.undo_stack.push(command)

                        # Check if the new string already exists
                        new_string_pointer = self.find_string_in_pool(data, string_pool_start, new_string)
                        if new_string_pointer != -1:
                            pointer_difference = new_string_pointer - (team_offset + j * 4)
                            struct.pack_into(">I", data, team_offset + j * 4, pointer_difference)
                        else:
                            pointer_difference = old_string_pointer - (team_offset + j * 4)

                            # Check if the original string is used elsewhere in the team info section
                            is_original_string_used_elsewhere = False
                            for search_offset in range(team_info_start, team_info_end, 4):
                                if search_offset != team_offset + j * 4:
                                    found_pointer_difference = struct.unpack(">I", data[search_offset:search_offset + 4])[0]
                                    if found_pointer_difference == pointer_difference:
                                        is_original_string_used_elsewhere = True
                                        break

                            if len(new_string) == len(old_string) and not self.is_string_used_elsewhere(data, team_info_start, team_info_end, team_info_length, old_string_pointer, i, j):
                                data[old_string_pointer:old_string_pointer + len(new_string)] = new_string
                            else:
                                data[data_offset:data_offset + len(new_string)] = new_string
                                pointer_difference = data_offset - (team_offset + j * 4)
                                struct.pack_into(">I", data, team_offset + j * 4, pointer_difference)
                                data_offset += len(new_string)

                                # Find the next empty space after data_offset
                                consecutive_null_bytes = 0
                                while consecutive_null_bytes < 10:
                                    if data[data_offset:data_offset + 2] == b'\x00\x00':
                                        consecutive_null_bytes += 2
                                    else:
                                        consecutive_null_bytes = 0
                                    data_offset += 2

                                data_offset -= 10
                                if data_offset > 0x3CBFE0:
                                    data_offset += 2

        with open(file_path, "wb") as file:
            file.write(data)

    def import_data(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Import Data", "", "CSV Files (*.csv);;All Files (*)", options=options)
        if file_name:
            with open(file_name, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                self.table.setRowCount(0)
                for row_data in reader:
                    row = self.table.rowCount()
                    self.table.insertRow(row)
                    for column, data in enumerate(row_data):
                        item = QTableWidgetItem(data)
                        self.table.setItem(row, column, item)

    def export_data(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Export Data", "", "CSV Files (*.csv);;All Files (*)", options=options)
        if file_name:
            with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                for row in range(self.table.rowCount()):
                    row_data = []
                    for column in range(self.table.columnCount()):
                        item = self.table.item(row, column)
                        if item is not None:
                            row_data.append(item.text())
                        else:
                            row_data.append('')
                    writer.writerow(row_data)

class EditCommand(QUndoCommand):
    def __init__(self, table, row, col, old_value, new_value):
        super().__init__()
        self.table = table
        self.row = row
        self.col = col
        self.old_value = old_value
        self.new_value = new_value

    def undo(self):
        self.table.item(self.row, self.col).setText(self.old_value)

    def redo(self):
        self.table.item(self.row, self.col).setText(self.new_value)

class CustomTableWidget(QTableWidget):
    def __init__(self, *args, **kwargs):
        super(CustomTableWidget, self).__init__(*args, **kwargs)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)
        self.undo_stack = QUndoStack(self)

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
            self.select_all()

    def undo(self):
        self.undo_stack.undo()

    def redo(self):
        self.undo_stack.redo()

class EditCommand(QUndoCommand):
    def __init__(self, table, row, column, old_value, new_value):
        super().__init__()
        self.table = table
        self.row = row
        self.column = column
        self.old_value = old_value
        self.new_value = new_value

    def undo(self):
        self.table.item(self.row, self.column).setText(self.old_value)

    def redo(self):
        self.table.item(self.row, self.column).setText(self.new_value)
        
if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        roster_editor = RosterEditor()
        roster_editor.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Error: {e}")

import tkinter as tk
from tkinter import ttk

class RadioTreeview(ttk.Treeview):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.selected_iid = []
        self.bind("<1>", self.on_click)  # Alternative for left click
    
    def add_radio_item(self, level, pos, text):
        iid = self.insert(level, pos, text="○ " + text)
        return iid

    def on_click(self, event):
        region = self.identify("region", event.x, event.y)
        if region == "tree":
            row = self.identify_row(event.y)
            if row:
                self.toggle_radio(row)
                return row
        return -1

    def toggle_radio(self, iid):
        if iid in self.selected_iid:
            # Unselect
            old_text = self.item(iid, "text")[2:]
            self.item(iid, text="○ " + old_text)
            self.selected_iid.remove(iid)
        else:
            # Select
            new_text = self.item(iid, "text")[2:]
            self.item(iid, text="⊙ " + new_text)
            self.selected_iid.append(iid)


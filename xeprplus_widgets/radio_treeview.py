import tkinter as tk
from tkinter import ttk

class RadioTreeview(ttk.Treeview):
    def __init__(self, parent=None, **kwargs):

        # # ensure both columns exist
        # cols = list(kwargs.get("columns", ()))
        # for c in ("radio", "name"):
        #     if c not in cols:
        #         cols.append(c)
        # kwargs["columns"] = tuple(cols)

        super().__init__(parent, **kwargs)

        # #0 is the tree column → radio symbol (small)
        self.heading("#0", text="")  # no header text
        self.column("#0", width=25, anchor="center", stretch=False)

        # 'name' is a data column (#1) → wide
        self.heading("name", text="Name")
        self.column("name", width=200, anchor="w", stretch=True)

        # for example, in your RadioTreeview __init__
        self.tag_configure(
            "parent_item", background="#f0f0f0")
        self.tag_configure(
            "child_item")
        
        self.selected_iids = []
        self.bind("<Button-1>", self.on_click)  # Alternative for left click
        self.logo_selected = "⊙ "
        self.logo_deselected = "○ "
        # For children under a folder
        self.tab_spaces = "    "
    
    def add_radio_item(self, parent, pos, text):
        radio_text = self.logo_deselected + text
        if parent in ("", None):
            tags = ("parent_item",)
        else:
            tags = ("child_item",)
            radio_text = self.tab_spaces + radio_text
        iid = self.insert(
            parent, pos, text="", values=(radio_text,), tags=tags)
        return iid


    def deselect_radio(self, iid):
        (text,) = self.item(iid, "values")
        if self.logo_selected in text:
            text = text.replace(self.logo_selected, self.logo_deselected)
            self.set(iid, "#1", text)
            self.selected_iids.remove(iid)


    def on_click(self, event):
        region = self.identify("region", event.x, event.y)
        if not region == "cell":
            return -1
        col = self.identify_column(event.x)
        row = self.identify_row(event.y)
        if not row:
            return -1
        if col == "#1":
            self.toggle_radio(row)
        return row


    def select_radio(self, iid):
        (text,) = self.item(iid, "values")
        if self.logo_deselected in text:
            text = text.replace(self.logo_deselected, self.logo_selected)
            self.set(iid, "#1", text)
            self.selected_iids.append(iid)


    def toggle_radio(self, iid):
        childrens = self.get_children(iid)
        if not childrens:
            # Single item, no children
            if iid in self.selected_iids:
                # Deselect
                self.deselect_radio(iid)
            else:
                # Select
                self.select_radio(iid)
            return
        are_selected = [self.logo_selected in self.item(c, "values")[0]
                        for c in childrens]
        
        if all(are_selected):
            # All selected -> deselect all
            for c in self.get_children(iid):
                self.deselect_radio(c)
        else:
            # At least one deselected -> select all
            for c in self.get_children(iid):
                self.select_radio(c)
        return


            

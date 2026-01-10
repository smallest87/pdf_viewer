import tkinter as tk
from tksheet import Sheet

class CSVTableView(tk.Toplevel):
    """Window child modular untuk menampilkan data CSV menggunakan tksheet"""
    def __init__(self, parent, title, headers, data):
        super().__init__(parent)
        self.title(f"Data Inspector - {title}")
        self.geometry("900x500")
        
        # Inisialisasi Frame Utama
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Inisialisasi tksheet
        self.sheet = Sheet(
            self,
            data=data,
            headers=headers,
            show_row_index=True,
            header_height=30,
            row_height=25,
            # Fitur Lebar Kolom Dinamis & Manual
            column_width=120,
            all_columns_resizable=True, 
            row_resizable=True
        )
        
        self.sheet.grid(row=0, column=0, sticky="nsew")
        
        # Enable Bindings (Scroll, Selection, Copy)
        self.sheet.enable_bindings((
            "single_select",
            "row_select",
            "column_width_resize",
            "arrowkeys",
            "right_click_menu",
            "copy",
            "rc_select"
        ))

    def refresh_data(self, headers, data):
        """Memperbarui isi tabel jika file CSV berubah"""
        self.sheet.headers(headers)
        self.sheet.set_sheet_data(data)
        self.sheet.refresh()
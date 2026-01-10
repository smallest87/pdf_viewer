import tkinter as tk
from tksheet import Sheet

class CSVTableView(tk.Toplevel):
    """Window child modular untuk menampilkan data CSV menggunakan tksheet"""
    def __init__(self, parent, title, headers, data, on_row_select_callback=None):
        super().__init__(parent)
        self.title(f"Data Inspector - {title}")
        self.geometry("900x500")
        
        # Simpan callback untuk interaksi dua arah
        self.on_row_select = on_row_select_callback
        
        # Konfigurasi Grid
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
            column_width=120,
            all_columns_resizable=True, 
            row_resizable=True
        )
        self.sheet.grid(row=0, column=0, sticky="nsew")
        
        # Aktifkan fitur standar tksheet
        self.sheet.enable_bindings((
            "single_select",
            "row_select",
            "column_width_resize",
            "arrowkeys",
            "right_click_menu",
            "copy",
            "rc_select"
        ))

        # Binding Event: Kirim data ke Controller saat baris dipilih
        self.sheet.extra_bindings([("row_select", self._row_selected)])

    def _row_selected(self, event):
        """Trigger callback saat pengguna mengklik baris di tabel"""
        if self.on_row_select:
            # Ambil set baris yang sedang dipilih langsung dari objek sheet
            selected_rows = self.sheet.get_selected_rows()
            
            if selected_rows:
                # Ambil baris pertama dari set (karena tksheet mengembalikan set)
                row_idx = list(selected_rows)[0]
                
                # Ambil data baris berdasarkan indeks tersebut
                row_data = self.sheet.get_row_data(row_idx)
                
                # Kirim ke controller
                self.on_row_select(row_data)

    def select_row_by_index(self, index):
        """Menyorot baris secara otomatis (PDF -> Table)"""
        if 0 <= index < self.sheet.get_total_rows():
            self.sheet.select_row(index)
            self.sheet.see(row=index) # Otomatis scroll ke baris tujuan
            self.sheet.refresh()

    def refresh_data(self, headers, data):
        """Memperbarui isi tabel tanpa menutup jendela"""
        self.sheet.headers(headers)
        self.sheet.set_sheet_data(data)
        self.sheet.refresh()
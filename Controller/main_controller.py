import fitz
import os
import csv
from View.csv_table_view import CSVTableView

class PDFController:
    def __init__(self, view, model):
        self.view = view
        self.model = model
        
        # Inisialisasi Manager Spesialis
        from Controller.document_mgr import DocumentManager
        from Controller.overlay_mgr import OverlayManager
        from Controller.export_mgr import ExportManager
        
        self.doc_mgr = DocumentManager(self.model)
        self.overlay_mgr = OverlayManager()
        self.export_mgr = ExportManager()

    def open_document(self, path):
        fname = self.doc_mgr.open_pdf(path)
        if fname:
            self.model.file_name = fname
            self.model.file_path = path
            self.model.csv_path = path.rsplit('.', 1)[0] + ".csv"
            self.view.set_application_title(fname)
            self.refresh()

    def open_csv_table(self):
        """Membuka window child tksheet dengan data CSV dinamis"""
        if not self.model.has_csv: return

        headers, data = [], []
        try:
            with open(self.model.csv_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.reader(f, delimiter=';')
                headers = next(reader)
                data = [row for row in reader]
            
            # Panggil View Child Modular
            CSVTableView(self.view.root, self.model.file_name, headers, data)
        except Exception as e:
            print(f"Error loading CSV Table: {e}")

    def refresh(self):
        if not self.model.doc: return

        page = self.model.doc[self.model.current_page]
        vw, _ = self.view.get_viewport_size()
        z = self.model.zoom_level

        # 1. Kalkulasi Rasterisasi & Centering
        mat = fitz.Matrix(z, z)
        pix = page.get_pixmap(matrix=mat)
        ox = max(0, (vw - pix.width) / 2)
        oy = self.model.padding
        region = (0, 0, max(vw, pix.width), pix.height + (oy * 2))

        # 2. Render ke Canvas
        self.view.display_page(pix, ox, oy, region)

        # 3. Render Overlay Layers
        if self.overlay_mgr.show_text_layer:
            self.view.draw_text_layer(page.get_text("words"), ox, oy, z)

        if self.overlay_mgr.show_csv_layer:
            self.overlay_mgr.csv_path = self.model.csv_path
            data = self.overlay_mgr.get_csv_data(self.model.current_page + 1)
            self.view.draw_csv_layer(data, ox, oy, z)

        # 4. Audit & Update UI
        self.model.is_sandwich = bool(page.get_text().strip())
        self.model.has_csv = os.path.exists(self.model.csv_path or "")
        
        self.view.update_ui_info(
            self.model.current_page + 1, len(self.model.doc), z, 
            self.model.is_sandwich, page.rect.width, page.rect.height, 
            self.model.has_csv
        )

    def change_page(self, d):
        if self.doc_mgr.move_page(d): self.refresh()

    def jump_to_page(self, n):
        if self.model.doc and 0 < n <= len(self.model.doc):
            self.model.current_page = n - 1
            self.refresh()

    def set_zoom(self, d):
        self.doc_mgr.set_zoom(d)
        self.refresh()

    def toggle_text_layer(self, v):
        self.overlay_mgr.show_text_layer = v
        self.refresh()

    def toggle_csv_layer(self, v):
        self.overlay_mgr.show_csv_layer = v
        self.refresh()

    def export_text_to_csv(self, f, i):
        self.export_mgr.to_csv(self.model.doc, f, i, self.view)

    def parse_page_ranges(self, s, t):
        return self.export_mgr.parse_ranges(s, t)
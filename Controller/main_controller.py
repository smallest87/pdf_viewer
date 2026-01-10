import fitz
import os

class PDFController:
    def __init__(self, view, model):
        self.view = view
        self.model = model
        # Import lokal untuk menghindari circular import
        from Controller.document_mgr import DocumentManager
        from Controller.overlay_mgr import OverlayManager
        from Controller.export_mgr import ExportManager
        
        self.doc_mgr = DocumentManager(self.model)
        self.overlay_mgr = OverlayManager()
        self.export_mgr = ExportManager()

    def open_document(self, path):
        """Proses pembukaan dokumen melalui Manager dan pembaharuan Model"""
        fname = self.doc_mgr.open_pdf(path)
        if fname:
            self.model.file_path = path
            self.model.csv_path = path.rsplit('.', 1)[0] + ".csv"
            self.view.set_application_title(fname)
            self.refresh()

    def refresh(self):
        """Sinkronisasi Model ke View dengan kalkulasi koordinat"""
        if not self.model.doc: return

        page = self.model.doc[self.model.current_page]
        vw, _ = self.view.get_viewport_size()
        z = self.model.zoom_level

        # Kalkulasi Rendering
        mat = fitz.Matrix(z, z)
        pix = page.get_pixmap(matrix=mat)
        
        ox = max(0, (vw - pix.width) / 2)
        oy = self.model.padding
        region = (0, 0, max(vw, pix.width), pix.height + (oy * 2))

        # Update Tampilan Dasar
        self.view.display_page(pix, ox, oy, region)

        # Logika Layering (Overlay)
        if self.overlay_mgr.show_text_layer:
            self.view.draw_text_layer(page.get_text("words"), ox, oy, z)

        if self.overlay_mgr.show_csv_layer:
            self.overlay_mgr.csv_path = self.model.csv_path
            data = self.overlay_mgr.get_csv_data(self.model.current_page + 1)
            self.view.draw_csv_layer(data, ox, oy, z)

        # Update Status & Audit
        self.model.is_sandwich = bool(page.get_text().strip())
        self.model.has_csv = os.path.exists(self.model.csv_path or "")
        
        self.view.update_ui_info(
            self.model.current_page + 1, len(self.model.doc), z, 
            self.model.is_sandwich, page.rect.width, page.rect.height, 
            self.model.has_csv
        )

    def change_page(self, delta):
        if self.doc_mgr.move_page(delta): self.refresh()

    def set_zoom(self, d):
        self.doc_mgr.set_zoom(d)
        self.refresh()

    def toggle_text_layer(self, val):
        self.overlay_mgr.show_text_layer = val
        self.refresh()

    def toggle_csv_layer(self, val):
        self.overlay_mgr.show_csv_layer = val
        self.refresh()

    def export_text_to_csv(self, f, i):
        self.export_mgr.to_csv(self.model.doc, f, i, self.view)
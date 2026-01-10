import fitz

class PDFController:
    def __init__(self, view):
        self.view = view
        self.doc = None
        self.current_page = 0
        self.zoom_level = 1.0
        self.padding = 30
        self.show_text_layer = False # State toggle

    def open_document(self, path):
        if not path: return
        self.doc = fitz.open(path)
        self.current_page = 0
        self.refresh()

    def toggle_text_layer(self, value):
        self.show_text_layer = value
        self.refresh()

    def refresh(self):
        if not self.doc: return
        page = self.doc[self.current_page]
        
        vw, _ = self.view.get_viewport_size()
        mat = fitz.Matrix(self.zoom_level, self.zoom_level)
        pix = page.get_pixmap(matrix=mat)
        
        ox = max(0, (vw - pix.width) / 2)
        oy = self.padding
        region = (0, 0, max(vw, pix.width), pix.height + (self.padding * 2))
        
        # 1. Tampilkan Halaman Utama
        self.view.display_page(pix, ox, oy, region)
        
        # 2. Gambar Layer Teks jika aktif
        if self.show_text_layer:
            words = page.get_text("words")
            self.view.draw_text_layer(words, ox, oy, self.zoom_level)
        
        # 3. Update Rulers & UI
        self.view.draw_rulers(page.rect.width, page.rect.height, ox, oy, self.zoom_level)
        is_sandwich = bool(page.get_text().strip())
        self.view.update_ui_info(self.current_page+1, len(self.doc), self.zoom_level, is_sandwich)

    def change_page(self, delta):
        if self.doc and 0 <= self.current_page + delta < len(self.doc):
            self.current_page += delta
            self.refresh()

    def jump_to_page(self, page_num):
        if self.doc and 0 <= page_num - 1 < len(self.doc):
            self.current_page = page_num - 1
            self.refresh()

    def set_zoom(self, direction):
        if direction == "in": self.zoom_level = min(5.0, self.zoom_level + 0.2)
        else: self.zoom_level = max(0.1, self.zoom_level - 0.2)
        self.refresh()
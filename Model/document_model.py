class PDFDocumentModel:
    """Pusat penyimpanan data dan status aplikasi (State Management)"""
    def __init__(self):
        # Data Dokumen Dasar
        self.doc = None
        self.file_name = ""
        self.file_path = ""
        
        # Status Navigasi & Tampilan
        self.current_page = 0
        self.total_pages = 0
        self.zoom_level = 1.0
        self.padding = 30
        
        # Status Overlay & Audit
        self.csv_path = None
        self.is_sandwich = False
        self.has_csv = False
        
        # State Seleksi (Untuk interaksi dua arah)
        self.selected_row_id = None 

    def reset(self):
        """Mengembalikan state ke kondisi awal"""
        self.doc = None
        self.current_page = 0
        self.zoom_level = 1.0
        self.selected_row_id = None
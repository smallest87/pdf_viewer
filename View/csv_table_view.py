from PyQt6.QtWidgets import (QWidget, QTableView, QVBoxLayout, QHeaderView, 
                             QAbstractItemView, QSizePolicy, QStyledItemDelegate, QStyle)
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QTimer, QEvent
from PyQt6.QtGui import (QFont, QColor, QBrush, QTextDocument, QTextCursor, QTextCharFormat)

# =============================================================================
# 1. DELEGATE: LOGIKA PEWARNAAN KARAKTER & WORDWRAP DINAMIS
# =============================================================================
class OCRTextDelegate(QStyledItemDelegate):
    """
    Delegate ini bertanggung jawab merender isi cell kolom 'teks'.
    Fitur utama: Pewarnaan angka vs huruf (deteksi OCR) dan WordWrap.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # Caching: Menyimpan objek QTextDocument yang sudah dirender.
        # Tanpa cache, navigasi (scroll/panah) akan lag karena CPU terus membedah string.
        self._doc_cache = {} 

    def _get_document(self, text, width, font):
        """
        Alur Logika:
        1. Cek apakah teks dengan lebar kolom ini sudah ada di cache.
        2. Jika belum, buat QTextDocument baru.
        3. Gunakan QTextCursor untuk menyisipkan karakter satu per satu.
        4. Jika karakter = Angka -> Biru, selain itu -> Cokelat.
        """
        cache_key = (text, width)
        if cache_key in self._doc_cache:
            return self._doc_cache[cache_key]

        doc = QTextDocument()
        doc.setDefaultFont(font)
        doc.setTextWidth(width) # Kunci WordWrap: Dokumen harus tahu batas lebarnya.
        
        cursor = QTextCursor(doc)
        
        # Format Karakter
        format_num = QTextCharFormat()
        format_num.setForeground(QColor("#0000FF")) # Biru untuk Angka
        format_text = QTextCharFormat()
        format_text.setForeground(QColor("#8B4513")) # Cokelat untuk Huruf

        for char in text:
            # Masukkan teks dengan format berbeda berdasarkan jenis karakter
            cursor.insertText(char, format_num if char.isdigit() else format_text)
        
        # Manajemen Cache: Bersihkan jika terlalu besar (>500 entri) untuk hemat RAM.
        if len(self._doc_cache) > 500: self._doc_cache.clear() 
        self._doc_cache[cache_key] = doc
        return doc

    def paint(self, painter, option, index):
        """Menggambar isi sel ke layar."""
        text = str(index.data(Qt.ItemDataRole.DisplayRole))
        if not text: return super().paint(painter, option, index)

        painter.save()
        
        # Render background biru jika baris sedang dipilih (Selected)
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        # Ambil dokumen dari cache (Efisiensi 60 FPS)
        doc = self._get_document(text, option.rect.width(), option.font)
        
        # Pindahkan koordinat painter ke posisi sel saat ini
        painter.translate(option.rect.x(), option.rect.y())
        # Batasi area gambar agar teks tidak 'lubere' ke kolom/baris sebelah
        painter.setClipRect(0, 0, option.rect.width(), option.rect.height())
        doc.drawContents(painter)
        
        painter.restore()

    def sizeHint(self, option, index):
        """Memberitahu tabel berapa tinggi yang dibutuhkan agar teks tidak terpotong."""
        text = str(index.data(Qt.ItemDataRole.DisplayRole))
        view = option.widget
        # Ambil lebar aktual kolom saat ini dari view
        width = view.columnWidth(index.column()) if view else 200
        doc = self._get_document(text, width, option.font)
        
        # Tinggi sel akan mengikuti tinggi dokumen hasil wrapping
        return doc.size().toSize()

# =============================================================================
# 2. MODEL: PENGELOLA DATA (MVC PATTERN)
# =============================================================================
class CSVModel(QAbstractTableModel):
    """
    Model ini menyimpan data asli dan menangani interaksi data.
    """
    def __init__(self, headers, data):
        super().__init__()
        self._headers = headers
        self._data = data
        self.marked_ids = set() # ID baris yang masuk dalam grup (warna kuning)

    def rowCount(self, parent=QModelIndex()): return len(self._data)
    def columnCount(self, parent=QModelIndex()): return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid(): return None
        row_idx, col_idx = index.row(), index.column()
        
        # Role Display/Edit: Mengembalikan teks mentah
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return str(self._data[row_idx][col_idx])
            
        # Role Background: Memberi warna kuning jika ID baris ada di marked_ids
        if role == Qt.ItemDataRole.BackgroundRole:
            if str(self._data[row_idx][0]) in self.marked_ids:
                return QBrush(QColor(255, 243, 176))
        return None

    def flags(self, index):
        # Mengaktifkan fitur double-click untuk edit cell
        return super().flags(index) | Qt.ItemFlag.ItemIsEditable

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        """Menyimpan data hasil editan user kembali ke list internal."""
        if index.isValid() and role == Qt.ItemDataRole.EditRole:
            self._data[index.row()][index.column()] = value
            # Emit dataChanged hanya pada cell tersebut agar UI refresh
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
            return True
        return False

    def set_marked_ids(self, ids):
        """
        Update warna grup secara efisien.
        Alur: Update set ID -> Beritahu view agar gambar ulang (dataChanged).
        Kunci: Jangan pakai beginResetModel agar kursor tidak melompat.
        """
        self.marked_ids = set(ids) if ids else set()
        self.dataChanged.emit(self.index(0, 0), 
                              self.index(self.rowCount()-1, self.columnCount()-1), 
                              [Qt.ItemDataRole.BackgroundRole])

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._headers[section]
        return None

# =============================================================================
# 3. VIEW: KOMPONEN TABEL DENGAN OPTIMASI UI
# =============================================================================
class PyQt6CSVTableView(QWidget):
    def __init__(self, parent, headers, data, on_row_select_callback=None):
        super().__init__(parent)
        self.on_row_select = on_row_select_callback
        # Deteksi otomatis indeks kolom teks/text
        self.text_col_index = next((i for i, h in enumerate(headers) if "teks" in h.lower() or "text" in h.lower()), -1)
        self._setup_ui(headers, data)

    def _setup_ui(self, headers, data):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.table_view = QTableView(self)
        self.table_view.setWordWrap(True)
        
        # Optimasi Vertical Header: Gunakan ukuran tetap agar tidak freeze di awal
        v_header = self.table_view.verticalHeader()
        v_header.setDefaultSectionSize(25)
        v_header.hide()

        self.model = CSVModel(headers, data)
        self.table_view.setModel(self.model)

        # Pasang delegate khusus untuk kolom teks agar berwarna biru/cokelat
        if self.text_col_index != -1:
            self.delegate = OCRTextDelegate(self)
            self.table_view.setItemDelegateForColumn(self.text_col_index, self.delegate)
        
        h_header = self.table_view.horizontalHeader()
        # Hubungkan sinyal geser kolom ke fungsi resize baris (Excel-style)
        h_header.sectionResized.connect(self._on_column_resized)

        # Setup Lebar Kolom
        for i in range(len(headers)):
            # Pakai Interactive agar Docker samping tidak kaku (Bug Resize Docker Fixed)
            h_header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
            if i == self.text_col_index:
                self.table_view.setColumnWidth(i, 150) # Lebar default teks
            else:
                # Fit To Content hanya dipanggil sekali di awal untuk performa
                self.table_view.resizeColumnToContents(i)
                self.table_view.setColumnWidth(i, self.table_view.columnWidth(i) + 15)
        
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.selectionModel().selectionChanged.connect(self._row_selected)
        layout.addWidget(self.table_view)

    def _on_column_resized(self, logicalIndex, oldSize, newSize):
        """Dipanggil saat kolom di-resize manual."""
        if logicalIndex == self.text_col_index:
            # Kosongkan cache dokumen karena lebar berubah, wordwrap harus dihitung ulang
            if hasattr(self, 'delegate'): self.delegate._doc_cache.clear()
            # Gunakan timer singkat (Debouncing) agar tidak berat saat ditarik cepat
            QTimer.singleShot(10, self._resize_visible_rows_only)

    def _resize_visible_rows_only(self):
        """
        STRATEGI KRUSIAL: Hanya resize baris yang tampak di layar.
        Mencegah aplikasi Freeze jika data berjumlah ribuan.
        """
        rect = self.table_view.viewport().rect()
        top, bottom = self.table_view.rowAt(rect.top()), self.table_view.rowAt(rect.bottom())
        
        if top == -1: top = 0
        if bottom == -1: bottom = self.model.rowCount() - 1

        # Matikan update visual sementara (Performa)
        self.table_view.setUpdatesEnabled(False)
        for row in range(top, bottom + 1):
            self.table_view.resizeRowToContents(row)
        self.table_view.setUpdatesEnabled(True)

    def _row_selected(self):
        """Mengirim data baris yang dipilih ke callback luar (Controller)."""
        if self.on_row_select:
            indexes = self.table_view.selectionModel().selectedRows()
            if indexes: self.on_row_select(self.model._data[indexes[0].row()])

    def select_row_and_mark_group(self, target_sid, group_ids):
        """
        Logika pindah baris otomatis (Sync dari navigasi luar).
        Mencegah kursor melompat ke kolom 0 dengan teknik pengecekan row aktif.
        """
        self.model.set_marked_ids(group_ids)
        if target_sid:
            row_idx = int(target_sid) - 1
            if 0 <= row_idx < self.model.rowCount():
                curr = self.table_view.currentIndex()
                # Jika sudah di baris yang benar, jangan paksa selectRow (Mencegah kursor reset)
                if curr.isValid() and curr.row() == row_idx: return
                
                # Pertahankan posisi kolom saat ini
                idx = self.model.index(row_idx, curr.column() if curr.isValid() else 0)
                self.table_view.selectionModel().blockSignals(True)
                self.table_view.setCurrentIndex(idx)
                self.table_view.selectRow(row_idx)
                self.table_view.scrollTo(idx)
                self.table_view.selectionModel().blockSignals(False)
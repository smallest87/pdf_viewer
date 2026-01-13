# Modifikasi File: View/components/child_nav_bar.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLineEdit, QLabel
from PyQt6.QtCore import Qt

class ChildNavBar(QWidget):
    def __init__(self, parent_child):
        super().__init__()
        self.child = parent_child
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 2, 10, 2)
        layout.setSpacing(8)
        self.setFixedHeight(30)
        self.setStyleSheet("""
            background-color: #f8f9fa; 
            border-top: 1px solid #dee2e6;
        """)

        # --- BAGIAN ZOOM (BARU) ---
        self.btn_zoom_out = QPushButton("−")
        self.btn_zoom_out.setFixedWidth(25)
        self.btn_zoom_out.setStyleSheet("border: none; font-weight: bold; color: #495057;")
        self.btn_zoom_out.clicked.connect(lambda: self.child.controller.set_zoom("out"))

        self.lbl_zoom = QLabel("100%")
        self.lbl_zoom.setFixedWidth(40)
        self.lbl_zoom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_zoom.setStyleSheet("font-size: 10px; color: #6c757d;")

        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_in.setFixedWidth(25)
        self.btn_zoom_in.setStyleSheet("border: none; font-weight: bold; color: #495057;")
        self.btn_zoom_in.clicked.connect(lambda: self.child.controller.set_zoom("in"))

        # --- BAGIAN NAVIGASI HALAMAN (TETAP) ---
        self.btn_prev = QPushButton("◀")
        self.btn_prev.setFixedWidth(25)
        self.btn_prev.setStyleSheet("border: none; color: #495057;")
        self.btn_prev.clicked.connect(lambda: self.child.controller.change_page(-1))

        self.pg_ent = QLineEdit()
        self.pg_ent.setFixedWidth(35)
        self.pg_ent.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pg_ent.returnPressed.connect(self._on_jump)

        self.lbl_total = QLabel("/ 0")
        self.btn_next = QPushButton("▶")
        self.btn_next.setFixedWidth(25)
        self.btn_next.clicked.connect(lambda: self.child.controller.change_page(1))

        # Tata Letak: Zoom di kiri, Navigasi di kanan
        layout.addWidget(self.btn_zoom_out)
        layout.addWidget(self.lbl_zoom)
        layout.addWidget(self.btn_zoom_in)
        layout.addStretch()
        layout.addWidget(self.btn_prev)
        layout.addWidget(self.pg_ent)
        layout.addWidget(self.lbl_total)
        layout.addWidget(self.btn_next)

    def _on_jump(self):
        try:
            val = int(self.pg_ent.text())
            self.child.controller.jump_to_page(val)
        except: pass

    def update_info(self, current, total, zoom):
        """Memperbarui tampilan angka halaman dan level zoom secara lokal."""
        self.pg_ent.setText(str(current))
        self.lbl_total.setText(f"/ {total}")
        # Tampilkan persentase zoom (misal: 1.2 -> 120%)
        self.lbl_zoom.setText(f"{int(zoom * 100)}%")
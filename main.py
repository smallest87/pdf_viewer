"""Titik masuk utama (Entry Point) untuk aplikasi PDF-Nexus.

Modul ini bertanggung jawab untuk melakukan bootstrap aplikasi dengan
menginisialisasi komponen Model, View, dan mengaitkan Controller menggunakan
mekanisme Dependency Injection melalui lambda factory.
"""

import sys

from PyQt6.QtWidgets import QApplication

from controller.main_controller import PDFController
from model.document_model import PDFDocumentModel
from view.main_view import PyQt6PDFView


def main() -> None:
    """Menginisialisasi komponen inti dan menjalankan event loop aplikasi.

    Fungsi ini menyusun arsitektur Model-View-Controller (MVC) aplikasi:
    1. Membuat instansi QApplication.
    2. Menyiapkan Model untuk manajemen state dokumen.
    3. Menginisialisasi View dengan menyuntikkan Controller factory.
    4. Memulai siklus hidup aplikasi Qt.
    """
    # 1. Inisialisasi Aplikasi Qt
    # sys.argv digunakan agar aplikasi mendukung argumen baris perintah OS
    app: QApplication = QApplication(sys.argv)

    # 2. Inisialisasi Model (State Management)
    # Model tetap menggunakan struktur lama karena bersifat UI-Agnostic
    model: PDFDocumentModel = PDFDocumentModel()

    # 3. Inisialisasi View dengan Controller Factory
    # Lambda digunakan untuk injeksi ketergantungan (Dependency Injection)
    # View akan membuat Controller, dan Controller akan mereferensi View tersebut
    view: PyQt6PDFView = PyQt6PDFView(app, lambda v: PDFController(v, model))

    # 4. Tampilkan Antarmuka
    view.show()

    # 5. Jalankan Event Loop Utama
    # sys.exit memastikan aplikasi tertutup bersih saat window di-close
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

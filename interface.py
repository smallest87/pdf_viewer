"""Modul interface untuk abstraksi antarmuka pengguna PDF Viewer.

Modul ini mendefinisikan kontrak yang harus dipenuhi oleh kelas View agar dapat
berkomunikasi dengan Controller tanpa adanya ketergantungan langsung pada
framework GUI tertentu (seperti PyQt6 atau PySide).
"""

from __future__ import annotations

from typing import Any


class PDFViewInterface:
    """Kontrak Abstraksi untuk GUI PDF Viewer.

    Kelas ini berfungsi sebagai base class untuk memastikan semua metode yang
    diperlukan oleh Controller tersedia pada implementasi View.
    """

    def display_page(
        self, pix: Any, ox: float, oy: float, region: tuple[float, float, float, float]
    ) -> None:
        """Menampilkan pixmap halaman PDF pada area viewport.

        Args:
            pix (Any): Objek pixmap hasil render (biasanya fitz.Pixmap).
            ox (float): Offset horizontal (X) untuk posisi halaman.
            oy (float): Offset vertikal (Y) untuk posisi halaman.
            region (Tuple[float, float, float, float]): Area render (x, y, w, h).

        """
        raise NotImplementedError()

    def draw_rulers(
        self, doc_w: float, doc_h: float, ox: float, oy: float, zoom: float
    ) -> None:
        """Menggambar penggaris (rulers) panduan pada antarmuka.

        Args:
            doc_w (float): Lebar asli dokumen.
            doc_h (float): Tinggi asli dokumen.
            ox (float): Offset horizontal halaman saat ini.
            oy (float): Offset vertikal halaman saat ini.
            zoom (float): Tingkat zoom saat ini.

        """
        raise NotImplementedError()

    def draw_text_layer(
        self, words: list[Any], ox: float, oy: float, zoom: float
    ) -> None:
        """Menggambar lapisan teks transparan di atas halaman PDF.

        Args:
            words (List[Any]): Daftar data kata (koordinat dan teks) dari PDF.
            ox (float): Offset horizontal halaman.
            oy (float): Offset vertikal halaman.
            zoom (float): Tingkat zoom saat ini.

        """
        raise NotImplementedError()

    def draw_csv_layer(
        self, data: list[Any], ox: float, oy: float, zoom: float
    ) -> None:
        """Menggambar lapisan overlay berdasarkan data CSV.

        Args:
            data (List[Any]): Daftar data koordinat dari cache CSV.
            ox (float): Offset horizontal halaman.
            oy (float): Offset vertikal halaman.
            zoom (float): Tingkat zoom saat ini.

        """
        raise NotImplementedError()

    def clear_overlay_layer(self, tag: str) -> None:
        """Menghapus lapisan overlay tertentu secara selektif.

        Args:
            tag (str): Identitas layer yang akan dihapus (misal: "text_layer").

        """
        raise NotImplementedError()

    def update_ui_info(
        self,
        page_num: int,
        total: int,
        zoom: float,
        is_sandwich: bool,
        width: float,
        height: float,
        has_csv: bool,
    ) -> None:
        """Memperbarui informasi status dokumen pada bilah antarmuka.

        Args:
            page_num (int): Nomor halaman saat ini.
            total (int): Total halaman dokumen.
            zoom (float): Tingkat zoom saat ini.
            is_sandwich (bool): Status apakah halaman memiliki teks (sandwich PDF).
            width (float): Lebar halaman dalam poin.
            height (float): Tinggi halaman dalam poin.
            has_csv (bool): Status keberadaan file CSV terkait.

        """
        raise NotImplementedError()

    def get_viewport_size(self) -> tuple[int, int]:
        """Mengambil ukuran dimensi area tampilan (viewport) saat ini.

        Returns:
            Tuple[int, int]: Lebar dan tinggi viewport dalam piksel.

        """
        raise NotImplementedError()

    def update_progress(self, value: int) -> None:
        """Memperbarui nilai indikator progres pada UI.

        Args:
            value (int): Nilai progres (0-100).

        """
        raise NotImplementedError()

    def set_application_title(self, filename: str) -> None:
        """Mengubah judul aplikasi berdasarkan dokumen yang sedang aktif.

        Args:
            filename (str): Nama file dokumen.

        """
        raise NotImplementedError()

    def update_highlight_only(self, selected_id: str | int) -> None:
        """Memperbarui sorotan (highlight) visual tanpa merender ulang halaman.

        Args:
            selected_id (Union[str, int]): ID elemen yang dipilih untuk disorot.

        """
        raise NotImplementedError()

    def set_grouping_control_state(self, active: bool) -> None:
        """Mengatur status aktif/nonaktif tombol kontrol pengelompokan.

        Args:
            active (bool): True jika kontrol harus diaktifkan.

        """
        raise NotImplementedError()

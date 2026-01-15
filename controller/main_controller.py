"""Modul pengontrol utama yang mengintegrasikan logika bisnis dan manajemen dokumen.

Modul ini berfungsi sebagai koordinator antara berbagai komponen manajer seperti
DocumentManager, ExportManager, dan OverlayManager untuk memastikan sinkronisasi
antara pemrosesan PDF dan tampilan antarmuka pengguna.
"""

from __future__ import annotations

import csv
import os
from typing import Any

import fitz  # PyMuPDF

from .app_state import app_state
from .document_mgr import DocumentManager
from .export_mgr import ExportManager
from .overlay_mgr import OverlayManager


class PDFController:
    """Controller utama untuk mengelola logika viewer PDF.

    Mengatur integrasi antara View dan Model, serta menginisialisasi manajer
    subsistem untuk operasi dokumen, overlay, dan ekspor. Menghubungkan
    controller ke status aplikasi global untuk sinkronisasi visibilitas layer.

    Attributes:
        view (Any): Instansi dari komponen antarmuka pengguna (View).
        model (Any): Instansi dari logika data PDF (Model).
        _doc_mgr (DocumentManager): Manajer untuk operasi manipulasi dokumen.
        _overlay_mgr (OverlayManager): Manajer untuk kontrol lapisan overlay visual.
        _export_mgr (ExportManager): Manajer untuk fungsionalitas ekspor data.
        _group_tolerance (float): Nilai toleransi jarak untuk pengelompokan elemen teks.
        _page_data_cache (List[List[Any]]): Penyimpanan sementara data CSV per halaman.
        _words_cache (Dict[int, List[Any]]): Penyimpanan sementara koordinat kata PDF.

    """

    def __init__(self, view: Any, model: Any) -> None:
        """Inisialisasi controller utama dan subsistem pendukung.

        Args:
            view (Any): Instansi dari komponen antarmuka pengguna (View).
            model (Any): Instansi dari logika data PDF (Model).

        """
        self.view: Any = view
        self.model: Any = model

        self._doc_mgr: DocumentManager = DocumentManager(self.model)
        self._overlay_mgr: OverlayManager = OverlayManager()
        self._export_mgr: ExportManager = ExportManager()

        # Konfigurasi Internal
        self._group_tolerance: float = 2.0
        self._page_data_cache: list[list[Any]] = []  # Cache data CSV per halaman
        self._words_cache: dict[int, list[Any]] = (
            {}
        )  # Cache teks PDF: {page_index: words_list}

        # SINKRONISASI GLOBAL
        app_state.visibility_changed.connect(self._on_global_state_changed)

    def _refresh(self, full_refresh: bool = True) -> None:
        """Memperbarui tampilan viewer PDF dan lapisan overlay secara komprehensif.

        Args:
            full_refresh (bool): Jika True, melakukan rendering ulang pixmap.

        """
        if not self.model.doc:
            return

        p_idx: int = self.model.current_page
        page: fitz.Page = self.model.doc[p_idx]
        vw: float
        vw, _ = self.view.get_viewport_size()
        z: float = self.model.zoom_level

        # SINKRONISASI STATUS LAYER
        self._overlay_mgr.show_text_layer = app_state.get_visibility("text_layer")
        self._overlay_mgr.show_csv_layer = app_state.get_visibility("csv_layer")

        # TAHAP 1: RENDERING RASTER (PIXMAP)
        ox: float
        oy: float
        if full_refresh:
            pix: fitz.Pixmap = page.get_pixmap(matrix=fitz.Matrix(z, z))
            ox, oy = max(0, (vw - pix.width) / 2), self.model.padding
            region: tuple[float, float, float, float] = (
                0,
                0,
                max(vw, pix.width),
                pix.height + (oy * 2),
            )
            self.view.display_page(pix, ox, oy, region)
            self.view.draw_rulers(page.rect.width, page.rect.height, ox, oy, z)

            # Ambil data CSV dari cache memori
            self._page_data_cache = self._overlay_mgr.get_csv_data(p_idx + 1)
        else:
            ox = max(0, (vw - (page.rect.width * z)) / 2)
            oy = self.model.padding

        # TAHAP 2: RENDERING TEXT LAYER (CACHING)
        if p_idx not in self._words_cache:
            self._words_cache[p_idx] = page.get_text("words")

        if self._overlay_mgr.show_text_layer:
            self.view.draw_text_layer(self._words_cache[p_idx], ox, oy, z)
        else:
            self.view.clear_overlay_layer("text_layer")

        # TAHAP 3: RENDERING CSV OVERLAY
        if self._overlay_mgr.show_csv_layer:
            self.view.draw_csv_layer(self._page_data_cache, ox, oy, z)
        else:
            self.view.clear_overlay_layer("csv_layer")

        # TAHAP 4: SINKRONISASI UI & STATE
        self.model.has_csv = os.path.exists(self.model.csv_path or "")
        self.view.update_ui_info(
            p_idx + 1,
            self.model.total_pages,
            z,
            bool(page.get_text().strip()),
            page.rect.width,
            page.rect.height,
            self.model.has_csv,
        )
        self.view.set_grouping_control_state(self.model.doc is not None)

        if self.model.selected_row_id:
            self.view.update_highlight_only(self.model.selected_row_id)

    def _on_global_state_changed(self, tag: str, is_visible: bool) -> None:
        """Update visibilitas layer berdasarkan sinyal dari App State.

        Args:
            tag (str): Identifikasi layer yang akan diubah.
            is_visible (bool): Status visibilitas layer yang diinginkan.

        """
        if tag == "text_layer":
            self._overlay_mgr.show_text_layer = is_visible
        elif tag == "csv_layer":
            self._overlay_mgr.show_csv_layer = is_visible
        self._refresh(full_refresh=False)
        print(f"[DEBUG] Global state changed: {tag} set to {is_visible}")

    def open_document(self, path: str) -> None:
        """Memuat dokumen dan melakukan pre-indexing CSV untuk performa.

        Args:
            path (str): Jalur file dokumen PDF yang akan dibuka.

        """
        fname: str | None = self._doc_mgr.open_pdf(path)
        if fname:
            self.model.file_name = fname
            self.model.file_path = path
            self.model.csv_path = path.rsplit(".", 1)[0] + ".csv"
            self._words_cache = {}

            if os.path.exists(self.model.csv_path):
                self._overlay_mgr.load_csv_to_cache(self.model.csv_path)

            self.view.set_application_title(fname)
            self._refresh(full_refresh=True)

    def save_csv_data(self, headers: list[str], data: list[list[Any]]) -> None:
        """Menyimpan data dan langsung memperbarui cache overlay.

        Args:
            headers (List[str]): Daftar nama kolom untuk header CSV.
            data (List[List[Any]]): Sekumpulan data baris yang akan ditulis.

        """
        if not self.model.csv_path:
            return
        try:
            with open(
                self.model.csv_path, mode="w", encoding="utf-8-sig", newline=""
            ) as f:
                writer = csv.writer(
                    f, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL
                )
                writer.writerow(headers)
                writer.writerows(data)

            self._overlay_mgr.load_csv_to_cache(self.model.csv_path)
            self._page_data_cache = self._overlay_mgr.get_csv_data(
                self.model.current_page + 1
            )
            self._refresh(full_refresh=False)
        except Exception as e:
            print(f"[ERROR] Auto-save gagal: {e}")

    def change_page(self, delta: int) -> None:
        """Mengubah halaman dokumen berdasarkan selisih (delta) tertentu.

        Args:
            delta (int): Jumlah perubahan halaman.

        """
        if self._doc_mgr.move_page(delta):
            self.model.selected_row_id = None
            self._refresh(full_refresh=True)

    def jump_to_page(self, page_num: int) -> None:
        """Berpindah ke nomor halaman tertentu secara spesifik.

        Args:
            page_num (int): Nomor halaman target (dimulai dari 1).

        """
        if self.model.doc and 0 < page_num <= self.model.total_pages:
            self.model.current_page = page_num - 1
            self.model.selected_row_id = None
            self._refresh(full_refresh=True)

    def set_zoom(self, direction: str) -> None:
        """Mengatur level zoom dokumen berdasarkan arah yang diberikan.

        Args:
            direction (str): Arah zoom, 'in' atau 'out'.

        """
        self._doc_mgr.set_zoom(direction)
        self._refresh(full_refresh=True)
        print(f"Zoom level sekarang: {self.model.zoom_level}")

    def open_csv_table(self) -> None:
        """Membaca data dari file CSV dan menampilkannya pada panel tabel di UI."""
        if not self.model.has_csv:
            return
        try:
            with open(self.model.csv_path, encoding="utf-8-sig", newline="") as f:
                reader = csv.reader(f, delimiter=";", quotechar='"')
                headers: list[str] = next(reader)
                data: list[list[str]] = [list(row) for row in reader]
            self.view.show_csv_panel(headers, data)
        except Exception as e:
            print(f"Gagal memuat tabel: {e}")

    def _handle_table_click(self, row_data: list[Any]) -> None:
        """Sinkronisasi tampilan PDF saat baris pada tabel di klik.

        Args:
            row_data (List[Any]): Data lengkap dari baris tabel.

        """
        try:
            row_id: str = str(row_data[0])
            if self.model.selected_row_id == row_id:
                return
            target_page: int = int(row_data[1]) - 1
            self.model.selected_row_id = row_id

            if target_page == self.model.current_page:
                self.view.update_highlight_only(row_id)
            else:
                self.model.current_page = target_page
                self._refresh(full_refresh=True)
        except Exception as e:
            print(f"Error sinkronisasi tabel: {e}")

    def _on_overlay_click(self, row_id: str | int) -> None:
        """Menangani aksi klik pada kotak overlay di halaman PDF.

        Args:
            row_id (Union[str, int]): Identifier unik dari elemen overlay.

        """
        self.model.selected_row_id = str(row_id)
        self.view.update_highlight_only(row_id)

    def _get_grouped_ids(self) -> set[str]:
        """Menghitung ID baris yang masuk dalam kelompok horizontal yang sama.

        Returns:
            Set[str]: Kumpulan ID yang berada dalam satu baris horizontal.

        """
        if (
            not hasattr(self.view, "parent_view")
            or not self.view.parent_view.toolbar.chk_group.isChecked()
        ):
            return set()
        if not self.model.selected_row_id:
            return set()

        target: list[Any] | None = next(
            (
                d
                for d in self._page_data_cache
                if str(d[5]) == str(self.model.selected_row_id)
            ),
            None,
        )
        if not target:
            return set()

        t_sumbu: float = (target[1] + target[3]) / 2
        grouped_ids: set[str] = set()
        for d in self._page_data_cache:
            curr_sumbu: float = (d[1] + d[3]) / 2
            if abs(curr_sumbu - t_sumbu) <= self._group_tolerance:
                grouped_ids.add(str(d[5]))
        return grouped_ids

    def _on_toggle_line_grouping(self) -> None:
        """Memperbarui highlight saat fitur pengelompokan baris diaktifkan."""
        if self.model.selected_row_id:
            self.view.update_highlight_only(self.model.selected_row_id)

    def _on_update_tolerance(self, val: str | float | int) -> None:
        """Memperbarui nilai toleransi untuk perhitungan pengelompokan baris.

        Args:
            val (Union[str, float, int]): Nilai toleransi baru.

        """
        try:
            self._group_tolerance = float(str(val).replace(",", "."))
            if self.model.selected_row_id:
                self.view.update_highlight_only(self.model.selected_row_id)
        except ValueError:
            pass

    def start_export(self, path: str, range_str: str) -> None:
        """Memulai proses ekstraksi teks dari PDF ke file CSV.

        Args:
            path (str): Lokasi penyimpanan file CSV hasil ekspor.
            range_str (str): String format rentang halaman.

        """
        if not self.model.doc:
            return
        indices: list[int] | None = self._export_mgr.parse_ranges(
            range_str, self.model.total_pages
        )
        if indices is not None:
            self._export_mgr.to_csv(self.model.doc, path, indices, self.view)
            self._refresh(full_refresh=False)

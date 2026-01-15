"""Modul antarmuka utama aplikasi PDF-Nexus.

Modul ini mendefinisikan jendela utama aplikasi menggunakan PyQt6, mengelola
area Multi-Document Interface (MDI), toolbar, menu bar, status bar, serta
berbagai panel dock (Docker) untuk inspeksi data.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QResizeEvent
from PyQt6.QtWidgets import (
    QApplication,
    QDockWidget,
    QFileDialog,
    QInputDialog,
    QLineEdit,
    QMainWindow,
    QMdiArea,
    QMdiSubWindow,
    QVBoxLayout,
    QWidget,
)

from interface import PDFViewInterface
from model.document_model import PDFDocumentModel

from .dockers.coordinate_dock import CoordinateDock
from .dockers.csv_table_view import PyQt6CSVTableView
from .dockers.layer_manager import LayerManagerWidget
from .mdi_child import PDFMdiChild
from .status_bar import PyQt6StatusBar
from .toolbar import PyQt6Toolbar


class PyQt6PDFView(QMainWindow, PDFViewInterface):
    """Komponen View utama aplikasi berbasis PyQt6.

    Bertanggung jawab atas tata letak visual, manajemen jendela MDI, dan
    penyediaan interface bagi Controller untuk memperbarui status UI.

    Attributes:
        app (QApplication): Instansi aplikasi utama.
        base_title (str): Judul dasar aplikasi.
        controller_factory (Callable): Pabrik untuk membuat instansi controller.
        csv_table_widget (Optional[PyQt6CSVTableView]): Widget tabel CSV aktif.
        mdi_area (QMdiArea): Area utama untuk jendela dokumen PDF.
        toolbar (PyQt6Toolbar): Bilah alat navigasi dan aksi.
        status_bar (PyQt6StatusBar): Bilah status informasi aplikasi.
        csv_dock (QDockWidget): Panel dock untuk inspeksi data CSV.
        dock_coords (QDockWidget): Panel dock untuk koordinat real-time.
        layer_dock (QDockWidget): Panel dock untuk manajemen layer.

    """

    def __init__(self, root_app: QApplication, controller_factory: Callable) -> None:
        """Inisialisasi jendela utama aplikasi.

        Args:
            root_app (QApplication): Instansi root aplikasi Qt.
            controller_factory (Callable): Fungsi atau class untuk membuat controller.

        """
        super().__init__()
        self.app: QApplication = root_app
        self.base_title: str = "PDF-Nexus Ultimate V4"
        self.setWindowTitle(self.base_title)
        self.resize(1280, 800)

        self.controller_factory: Callable = controller_factory
        self.csv_table_widget: PyQt6CSVTableView | None = None

        self._setup_ui()
        self._setup_dock_widget()

    def _setup_ui(self) -> None:
        """Mengonfigurasi elemen dasar antarmuka pengguna."""
        self.central_widget: QWidget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout: QVBoxLayout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.toolbar: PyQt6Toolbar = PyQt6Toolbar(self)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)

        self.mdi_area: QMdiArea = QMdiArea()
        self.mdi_area.setViewMode(QMdiArea.ViewMode.SubWindowView)
        self.mdi_area.subWindowActivated.connect(self._on_subwindow_activated)
        self.main_layout.addWidget(self.mdi_area)

        self._setup_menus()

        self.status_bar: PyQt6StatusBar = PyQt6StatusBar(self)
        self.setStatusBar(self.status_bar)

    def _setup_menus(self) -> None:
        """Mengonfigurasi sistem menu bar."""
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self.toolbar.open_act)
        file_menu.addAction(self.toolbar.export_act)

        self.window_menu = menubar.addMenu("&Window")
        self.window_menu.aboutToShow.connect(self._update_window_menu)

    def _update_window_menu(self) -> None:
        """Memperbarui daftar jendela aktif di menu Window secara dinamis."""
        self.window_menu.clear()
        tile_act: QAction = QAction("Tile Windows", self)
        tile_act.triggered.connect(self.mdi_area.tileSubWindows)
        self.window_menu.addAction(tile_act)

        cascade_act: QAction = QAction("Cascade Windows", self)
        cascade_act.triggered.connect(self.mdi_area.cascadeSubWindows)
        self.window_menu.addAction(cascade_act)

        self.window_menu.addSeparator()

        windows: list[QMdiSubWindow] = self.mdi_area.subWindowList()
        if not windows:
            empty_act: QAction = QAction("No Documents Open", self)
            empty_act.setEnabled(False)
            self.window_menu.addAction(empty_act)
            return

        for i, window in enumerate(windows):
            action: QAction = QAction(f"{i+1}. {window.windowTitle()}", self)
            action.setCheckable(True)
            action.setChecked(window == self.mdi_area.activeSubWindow())
            # Menggunakan default argument pada lambda untuk menangkap nilai loop
            action.triggered.connect(
                lambda checked, w=window: self.mdi_area.setActiveSubWindow(w)
            )
            self.window_menu.addAction(action)

    def _get_active_child(self) -> PDFMdiChild | None:
        """Mendapatkan dokumen (MDI Child) yang sedang aktif.

        Returns:
            Optional[PDFMdiChild]: Instansi child aktif atau None jika tidak ada.

        """
        active_sub = self.mdi_area.activeSubWindow()
        if active_sub and isinstance(active_sub, PDFMdiChild):
            return active_sub
        return None

    def _on_subwindow_activated(self, window: QMdiSubWindow | None) -> None:
        """Menangani aktivasi jendela sub-MDI.

        Args:
            window (Optional[QMdiSubWindow]): Jendela yang baru saja diaktifkan.

        """
        if window and isinstance(window, PDFMdiChild):
            window.controller._refresh(full_refresh=False)

    def _setup_dock_widget(self) -> None:
        """Menginisialisasi seluruh panel dock (panel samping)."""
        self.csv_dock: QDockWidget = QDockWidget("CSV Data Inspector", self)
        self.csv_dock.setVisible(False)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.csv_dock)

        self.dock_coords: QDockWidget = QDockWidget("Live Coordinates", self)
        self.coord_widget: CoordinateDock = CoordinateDock()
        self.dock_coords.setWidget(self.coord_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_coords)

        self.layer_dock: QDockWidget = QDockWidget("Layers", self)
        self.layer_manager: LayerManagerWidget = LayerManagerWidget(self)
        self.layer_dock.setWidget(self.layer_manager)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.layer_dock)

    def _update_coord_display(self, x0: float, top: float) -> None:
        """Memperbarui tampilan koordinat pada panel samping.

        Args:
            x0 (float): Posisi horizontal.
            top (float): Posisi vertikal.

        """
        self.coord_widget.update_coords(x0, top)
        print(f"[DEBUG] Updated coord display to ({x0}, {top}) from MainView")

    def show_csv_panel(self, headers: list[str], data: list[list[Any]]) -> None:
        """Menampilkan panel inspeksi data CSV.

        Args:
            headers (List[str]): Header kolom CSV.
            data (List[List[Any]]): Data baris CSV.

        """
        child = self._get_active_child()
        if not child:
            return
        self.csv_table_widget = PyQt6CSVTableView(
            self, headers, data, child.controller._handle_table_click
        )
        self.csv_dock.setWidget(self.csv_table_widget)
        self.csv_dock.setVisible(True)

    # --- IMPLEMENTASI PDFViewInterface ---

    def update_progress(self, v: int) -> None:
        """Memperbarui nilai pada progress bar di status bar.

        Args:
            v (int): Nilai progress (0-100).

        """
        self.status_bar.set_progress(v)
        self.app.processEvents()

    def set_application_title(self, f: str) -> None:
        """Mengatur judul jendela aplikasi berdasarkan file yang dibuka.

        Args:
            f (str): Nama file yang aktif.

        """
        self.setWindowTitle(f"{self.base_title} - {f}")

    def set_grouping_control_state(self, a: bool) -> None:
        """Mengaktifkan atau menonaktifkan kontrol pengelompokan pada toolbar.

        Args:
            a (bool): True untuk mengaktifkan, False untuk menonaktifkan.

        """
        self.toolbar.set_grouping_enabled(a)

    # --- SLOT EVENT ---

    def _on_open(self) -> None:
        """Membuka dialog pemilihan file PDF dan membuat jendela MDI baru."""
        print("[DEBUG] Triggered Open File Dialog")
        path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF Files (*.pdf)")
        if path:
            new_sub: PDFMdiChild = PDFMdiChild(self, PDFDocumentModel)
            self.mdi_area.addSubWindow(new_sub)
            new_sub.show()
            new_sub.controller.open_document(path)

    def _on_view_csv_table(self) -> None:
        """Memicu Controller untuk membuka data tabel CSV dokumen aktif."""
        print("[DEBUG] Triggered View CSV Table")
        child = self._get_active_child()
        if child:
            child.controller.open_csv_table()

    def _on_export_csv(self) -> None:
        """Menangani dialog ekspor rentang halaman PDF ke CSV."""
        print("[DEBUG] Triggered Export CSV Dialog")
        child = self._get_active_child()
        if not child or not child.model.doc:
            return
        total: int = child.model.total_pages
        range_str, ok = QInputDialog.getText(
            self,
            "Export Range",
            f"Halaman (1-{total}):",
            QLineEdit.EchoMode.Normal,
            f"1-{total}",
        )
        if ok:
            path, _ = QFileDialog.getSaveFileName(
                self, "Export CSV", "", "CSV Files (*.csv)"
            )
            if path:
                child.controller.start_export(path, range_str)

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Menangani perubahan ukuran jendela aplikasi.

        Args:
            event (QResizeEvent): Objek event resize.

        """
        print("[DEBUG] Window Resize Event Triggered")
        super().resizeEvent(event)
        if self.csv_dock.isVisible():
            child = self._get_active_child()
            vp_w: int = child.viewport.width() if child else 0
            print(
                f"[DEBUG] Window Resize -> [Dock: {self.csv_dock.width()}px] "
                f"vs [Active Viewport: {vp_w}px]"
            )

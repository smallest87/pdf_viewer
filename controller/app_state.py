"""Modul definisi sinyal dan manajemen state aplikasi.

Modul ini berfungsi sebagai penyedia basis komunikasi antar-komponen
menggunakan mekanisme Signal-Slot PyQt6 untuk memastikan sinkronisasi
antara logika bisnis dan antarmuka pengguna.
"""

from PyQt6.QtCore import QObject, pyqtSignal


class GlobalAppState(QObject):
    """Pusat data status aplikasi (Single Source of Truth)."""

    # Definisi signal
    visibility_changed = pyqtSignal(str, bool)
    """
    Sinyal untuk memberitahu UI bahwa status berubah.
    
    :param tag: Nama layer (str)
    :param status: Status visibilitas (bool)
    """

    def __init__(self):
        """Inisialisasi objek dan pengaturan status visibilitas layer awal.

        Attributes:
            _layers (dict): Kamus yang menyimpan status aktif/nonaktif untuk
                berbagai layer aplikasi, mencakup layer teks, layer CSV,
                serta visibilitas koordinat real-time.

        """
        super().__init__()
        # 2. Status disimpan di variabel pusat
        self._layers = {
            "text_layer": False,
            "csv_layer": False,
            "live_coords": True,  # Default: Aktif sesuai inisialisasi di UI
        }

    def set_visibility(self, tag, is_visible):
        """Update status visibilitas layer dan informasikan ke seluruh UI.

        Args:
            tag (str): Identitas layer (contoh: 'text_layer', 'csv_layer').
            is_visible (bool): True jika layer harus ditampilkan, False jika disembunyikan.

        Returns:
            None

        """
        if tag in self._layers:
            self._layers[tag] = is_visible
            # Memancarkan sinyal agar semua UI ter-update
            self.visibility_changed.emit(tag, is_visible)

    def get_visibility(self, tag):
        """Mengambil status visibilitas layer tertentu dari state pusat.

        Args:
            tag (str): Nama atau identitas layer yang ingin diperiksa statusnya.

        Returns:
            bool: True jika layer diset terlihat, False jika tidak terlihat atau tag tidak ditemukan.

        """
        return self._layers.get(tag, False)


# Instance tunggal yang akan digunakan semua komponen
app_state = GlobalAppState()

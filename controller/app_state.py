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
        super().__init__()
        # 2. Status disimpan di variabel pusat
        self._layers = {
            "text_layer": False,
            "csv_layer": False,
            "live_coords": True,  # Default: Aktif sesuai inisialisasi di UI
        }

    def set_visibility(self, tag, is_visible):
        """
        Update status visibilitas layer dan informasikan ke seluruh UI.

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
        """Ambil nilai status dari variabel pusat."""
        return self._layers.get(tag, False)


# Instance tunggal yang akan digunakan semua komponen
app_state = GlobalAppState()

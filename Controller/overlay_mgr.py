import os
import csv

class OverlayManager:
    def __init__(self):
        self.show_text_layer = False
        self.show_csv_layer = False
        self.csv_path = None

    def get_csv_data(self, page_num):
        """Parsing koordinat dari CSV termasuk kolom 'nomor' untuk interaksi"""
        if not self.csv_path or not os.path.exists(self.csv_path): return []
        data = []
        try:
            with open(self.csv_path, mode='r', encoding='utf-8-sig', newline='') as f:
                reader = csv.DictReader(f, delimiter=';', quotechar='"')
                for row in reader:
                    if int(row['halaman']) == page_num:
                        # Konversi koordinat float
                        x0 = float(row['x0'].replace(',', '.'))
                        y0 = float(row['top'].replace(',', '.'))
                        x1 = float(row['x1'].replace(',', '.'))
                        y1 = float(row['bottom'].replace(',', '.'))
                        
                        # WAJIB: Tambahkan row['nomor'] sebagai elemen ke-6
                        data.append((x0, y0, x1, y1, row['teks'], row['nomor']))
        except: pass
        return data
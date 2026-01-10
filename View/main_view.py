import tkinter as tk
from tkinter import filedialog, messagebox
import os
from PIL import Image, ImageTk
from interface import PDFViewInterface
from View.toolbar import ToolbarComponent
from View.viewport import ViewportComponent
from View.status_bar import StatusBarComponent
from View.tooltip import TooltipManager

class TkinterPDFView(PDFViewInterface):
    def __init__(self, root, controller_factory):
        self.root = root
        self.base_title = "Modular PDF Viewer Pro (MVC)"
        self.root.title(self.base_title)
        
        # Inisialisasi Controller melalui factory
        self.controller = controller_factory(self)
        self.tooltip = TooltipManager(self.root)
        
        # Variabel kontrol UI
        self.text_layer_var = tk.BooleanVar(value=False)
        self.csv_overlay_var = tk.BooleanVar(value=False)
        
        self._setup_ui()

    def _setup_ui(self):
        """Menyusun layout utama"""
        self.toolbar = ToolbarComponent(self.root, self)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        self.status_bar = StatusBarComponent(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.viewport = ViewportComponent(self.root)
        self.viewport.pack(fill=tk.BOTH, expand=True)
        
        # Bindings event
        self.viewport.canvas.bind("<Configure>", lambda e: self.controller.refresh())
        self.viewport.canvas.bind_all("<MouseWheel>", self._on_wheel)

    # --- IMPLEMENTASI PDFViewInterface (WAJIB ADA) ---

    def draw_rulers(self, doc_w, doc_h, ox, oy, zoom):
        """Implementasi wajib untuk menggambar penggaris pada kanvas"""
        self.viewport.h_rule.delete("all")
        self.viewport.v_rule.delete("all")
        
        # Interval angka penggaris (dinamis berdasarkan zoom)
        step = 100 if zoom < 1.0 else 50
        
        # Horizontal Ruler
        for u in range(0, int(doc_w) + 1, 10):
            x = u * zoom + ox
            if u % step == 0:
                self.viewport.h_rule.create_line(x, 25, x, 0, fill="#333333")
                self.viewport.h_rule.create_text(x + 2, 2, text=str(u), anchor=tk.NW, font=("Arial", 7))
            elif u % 10 == 0:
                self.viewport.h_rule.create_line(x, 25, x, 15, fill="#999999")

        # Vertical Ruler
        for u in range(0, int(doc_h) + 1, 10):
            y = u * zoom + oy
            if u % step == 0:
                self.viewport.v_rule.create_line(25, y, 0, y, fill="#333333")
                self.viewport.v_rule.create_text(2, y + 2, text=str(u), anchor=tk.NW, font=("Arial", 7))
            elif u % 10 == 0:
                self.viewport.v_rule.create_line(25, y, 15, y, fill="#999999")

    def display_page(self, pix, ox, oy, region):
        """Render pixmap ke kanvas utama"""
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.viewport.tk_img = ImageTk.PhotoImage(img)
        self.viewport.canvas.delete("all")
        self.viewport.canvas.create_image(ox, oy, anchor=tk.NW, image=self.viewport.tk_img)
        self.viewport.canvas.config(scrollregion=region)
        self.viewport.h_rule.config(scrollregion=region)
        self.viewport.v_rule.config(scrollregion=region)

    def draw_text_layer(self, words, ox, oy, zoom):
        self._draw_overlay(words, ox, oy, zoom, "#0078d7", "text_layer")

    def draw_csv_layer(self, words, ox, oy, zoom):
        self._draw_overlay(words, ox, oy, zoom, "#28a745", "csv_layer")

    def update_ui_info(self, page_num, total, zoom, is_sandwich, width, height, has_csv):
        """Sinkronisasi status bar dan toolbar"""
        self.toolbar.pg_ent.delete(0, tk.END)
        self.toolbar.pg_ent.insert(0, str(page_num))
        self.toolbar.lbl_total.config(text=f"/ {total}")
        
        self.toolbar.text_toggle.config(state="normal" if is_sandwich else "disabled")
        self.toolbar.csv_toggle.config(state="normal" if has_csv else "disabled")
        self.toolbar.btn_table.config(state="normal" if has_csv else "disabled")
        
        status_txt = "Sandwich" if is_sandwich else "Image Only"
        self.status_bar.lbl_status.config(text=f"Status: {status_txt}")
        self.status_bar.lbl_dims.config(text=f"Dimensi: {int(width)}x{int(height)} pt")
        self.status_bar.lbl_zoom.config(text=f"Zoom: {int(zoom*100)}%")
        self.tooltip.hide()

    def set_application_title(self, filename):
        self.root.title(f"{self.base_title} - {filename}")

    def update_progress(self, value):
        self.status_bar.progress['value'] = value
        self.root.update()

    def get_viewport_size(self):
        self.root.update_idletasks()
        return self.viewport.canvas.winfo_width(), self.viewport.canvas.winfo_height()

    # --- PRIVATE HELPERS ---

    def _draw_overlay(self, words, ox, oy, zoom, color, tag):
        """Logika penggambaran kotak dengan deteksi highlight aktif"""
        selected_id = self.controller.model.selected_row_id

        for w in words:
            x0, y0, x1, y1 = w[0], w[1], w[2], w[3]
            txt, row_id = w[4], w[5] if len(w) > 5 else None

            # Highlight jika ID cocok dengan Model
            is_active = (str(row_id) == str(selected_id))
            l_width = 4 if is_active else 1
            o_color = "red" if is_active else color

            r_id = self.viewport.canvas.create_rectangle(
                x0*zoom+ox, y0*zoom+oy, x1*zoom+ox, y1*zoom+oy, 
                outline=o_color, width=l_width, fill=color, stipple="gray25", tags=tag
            )
            
            # Tooltip & Event Binding
            self.viewport.canvas.tag_bind(r_id, "<Enter>", lambda e, t=txt, c=(x0,y0,x1,y1): self.tooltip.show(e,t,c))
            self.viewport.canvas.tag_bind(r_id, "<Leave>", lambda e: self.tooltip.hide())
            self.viewport.canvas.tag_bind(r_id, "<Motion>", self.tooltip.move)

            if tag == "csv_layer" and row_id:
                self.viewport.canvas.tag_bind(r_id, "<Button-1>", lambda e, rid=row_id: self.controller.handle_overlay_click(rid))

    def _on_open(self):
        p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if p: self.controller.open_document(p)

    def _on_view_csv_table(self):
        self.controller.open_csv_table()

    def _on_export_csv(self):
        # Dialog ekspor tetap menggunakan logika sebelumnya
        pass

    def _on_wheel(self, e):
        if e.state & 0x0004: self.controller.set_zoom("in" if e.delta > 0 else "out")
        else: self.viewport.canvas.yview_scroll(int(-1*(e.delta/120)), "units")
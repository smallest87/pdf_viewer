import tkinter as tk
from tkinter import filedialog, ttk
import fitz  # PyMuPDF
from PIL import Image, ImageTk

class ProfessionalPDFViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Viewer Pro - Text Layer Toggle")
        self.root.geometry("1200x900")

        # State Management
        self.pdf_doc = None
        self.current_page = 0
        self.zoom_level = 1.0
        self.ruler_size = 25
        self.page_padding = 30
        self.tk_img = None
        
        # Toggle State
        self.show_text_layer = tk.BooleanVar(value=False)
        self.is_sandwich = False

        self._setup_ui()

    def _setup_ui(self):
        # --- Toolbar ---
        self.toolbar = ttk.Frame(self.root, padding="5")
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        
        ttk.Button(self.toolbar, text="Buka PDF", command=self.open_pdf).pack(side=tk.LEFT, padx=2)
        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Navigasi
        ttk.Button(self.toolbar, text="<", command=lambda: self._change_page(-1)).pack(side=tk.LEFT)
        self.pg_input = ttk.Entry(self.toolbar, width=5, justify="center")
        self.pg_input.pack(side=tk.LEFT, padx=2)
        self.pg_input.bind("<Return>", self._jump_page)
        self.pg_total_lbl = ttk.Label(self.toolbar, text="/ 0")
        self.pg_total_lbl.pack(side=tk.LEFT, padx=2)
        ttk.Button(self.toolbar, text=">", command=lambda: self._change_page(1)).pack(side=tk.LEFT)

        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # TOGGLE CONTROL (Hanya aktif jika sandwich terdeteksi)
        self.toggle_btn = ttk.Checkbutton(
            self.toolbar, 
            text="Tampilkan Layer Teks", 
            variable=self.show_text_layer,
            command=self.render_page,
            state="disabled" # Default mati
        )
        self.toggle_btn.pack(side=tk.LEFT, padx=5)

        # Zoom
        ttk.Button(self.toolbar, text="Zoom +", command=self.zoom_in).pack(side=tk.RIGHT, padx=2)
        ttk.Button(self.toolbar, text="Zoom -", command=self.zoom_out).pack(side=tk.RIGHT, padx=2)

        # --- Status Bar ---
        self.status_var = tk.StringVar(value="Siap")
        ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X)

        # --- Main Viewport ---
        self.container = tk.Frame(self.root, bg="#323639")
        self.container.pack(fill=tk.BOTH, expand=True)
        self.container.grid_columnconfigure(1, weight=1)
        self.container.grid_rowconfigure(1, weight=1)

        self.h_ruler = tk.Canvas(self.container, height=self.ruler_size, bg="#e0e0e0", bd=0, highlightthickness=0)
        self.v_ruler = tk.Canvas(self.container, width=self.ruler_size, bg="#e0e0e0", bd=0, highlightthickness=0)
        self.viewport = tk.Canvas(self.container, bg="#323639", bd=0, highlightthickness=0)
        self.corner = tk.Frame(self.container, width=self.ruler_size, height=self.ruler_size, bg="#bdbdbd")
        
        self.corner.grid(row=0, column=0)
        self.h_ruler.grid(row=0, column=1, sticky="ew")
        self.v_ruler.grid(row=1, column=0, sticky="ns")
        self.viewport.grid(row=1, column=1, sticky="nsew")

        # Scrollbars
        self.v_scroll = ttk.Scrollbar(self.container, orient=tk.VERTICAL, command=self._sync_v_scroll)
        self.v_scroll.grid(row=1, column=2, sticky="ns")
        self.h_scroll = ttk.Scrollbar(self.container, orient=tk.HORIZONTAL, command=self._sync_h_scroll)
        self.h_scroll.grid(row=2, column=1, sticky="ew")

        self.viewport.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)
        self.viewport.bind("<Configure>", lambda e: self.render_page())
        self.viewport.bind_all("<MouseWheel>", self._on_mouse_wheel)

    def render_page(self):
        if not self.pdf_doc: return

        page = self.pdf_doc[self.current_page]
        doc_w, doc_h = page.rect.width, page.rect.height
        
        # Render Gambar
        matrix = fitz.Matrix(self.zoom_level, self.zoom_level)
        pix = page.get_pixmap(matrix=matrix)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.tk_img = ImageTk.PhotoImage(img)

        vw = self.viewport.winfo_width()
        offset_x = max(0, (vw - pix.width) / 2)
        offset_y = self.page_padding

        self.viewport.delete("all")
        self.viewport.create_image(offset_x, offset_y, anchor=tk.NW, image=self.tk_img, tags="pdf_img")
        
        # DRAW TEXT LAYER (Jika aktif)
        if self.show_text_layer.get():
            self._draw_text_overlay(page, offset_x, offset_y)
        
        # Update Rulers & Scrollregion
        region = (0, 0, max(vw, pix.width), pix.height + (offset_y * 2))
        self.viewport.config(scrollregion=region)
        self.h_ruler.config(scrollregion=region)
        self.v_ruler.config(scrollregion=region)

        self._draw_fixed_rulers(doc_w, doc_h, offset_x, offset_y)
        self._update_ui_state(page)

    def _draw_text_overlay(self, page, ox, oy):
        """Menggambar kotak area teks di atas canvas"""
        words = page.get_text("words") # Ambil list (x0, y0, x1, y1, "word", block_no, line_no, word_no)
        for w in words:
            # Skalakan koordinat sesuai zoom dan tambahkan offset
            x0 = (w[0] * self.zoom_level) + ox
            y0 = (w[1] * self.zoom_level) + oy
            x1 = (w[2] * self.zoom_level) + ox
            y1 = (w[3] * self.zoom_level) + oy
            
            # Gambar kotak semi-transparan (outline kuning/biru khas PDF viewer)
            self.viewport.create_rectangle(
                x0, y0, x1, y1, 
                outline="#0078d7", 
                fill="#0078d7", 
                stipple="gray25", # Efek transparansi di Tkinter
                tags="text_layer"
            )

    def _update_ui_state(self, page):
        self.pg_input.delete(0, tk.END)
        self.pg_input.insert(0, str(self.current_page + 1))
        
        # Deteksi Sandwich
        self.is_sandwich = bool(page.get_text().strip())
        if self.is_sandwich:
            self.toggle_btn.config(state="normal")
            status = "Sandwich (Searchable)"
        else:
            self.toggle_btn.config(state="disabled")
            self.show_text_layer.set(False)
            status = "Image-only"
        
        self.status_var.set(f"Status: {status} | Zoom: {int(self.zoom_level*100)}%")

    # --- FUNGSI PENDUKUNG (RULER, NAVIGASI, DLL) ---
    def _draw_fixed_rulers(self, doc_w, doc_h, ox, oy):
        self.h_ruler.delete("all")
        self.v_ruler.delete("all")
        step = 200 if self.zoom_level < 0.5 else 100 if self.zoom_level < 1.0 else 50
        for unit in range(0, int(doc_w) + 1, 10):
            sx = (unit * self.zoom_level) + ox
            if unit % step == 0:
                self.h_ruler.create_line(sx, self.ruler_size, sx, 0, fill="#444")
                self.h_ruler.create_text(sx + 2, 2, text=str(unit), anchor=tk.NW, font=("Consolas", 8))
            elif unit % (step/2) == 0:
                self.h_ruler.create_line(sx, self.ruler_size, sx, self.ruler_size/2, fill="#888")

        for unit in range(0, int(doc_h) + 1, 10):
            sy = (unit * self.zoom_level) + oy
            if unit % step == 0:
                self.v_ruler.create_line(self.ruler_size, sy, 0, sy, fill="#444")
                self.v_ruler.create_text(2, sy + 2, text=str(unit), anchor=tk.NW, font=("Consolas", 8))
            elif unit % (step/2) == 0:
                self.v_ruler.create_line(self.ruler_size, sy, self.ruler_size/2, sy, fill="#888")

    def open_pdf(self):
        f = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if f:
            self.pdf_doc = fitz.open(f)
            self.current_page = 0
            self.pg_total_lbl.config(text=f"/ {len(self.pdf_doc)}")
            self.render_page()

    def _change_page(self, delta):
        if self.pdf_doc:
            p = self.current_page + delta
            if 0 <= p < len(self.pdf_doc): self.current_page = p; self.render_page()

    def _jump_page(self, event):
        try:
            p = int(self.pg_input.get()) - 1
            if 0 <= p < len(self.pdf_doc): self.current_page = p; self.render_page()
        except: pass

    def zoom_in(self): self.zoom_level = min(self.zoom_level + 0.2, 5.0); self.render_page()
    def zoom_out(self): self.zoom_level = max(self.zoom_level - 0.2, 0.1); self.render_page()
    def _sync_v_scroll(self, *args): self.viewport.yview(*args); self.v_ruler.yview(*args)
    def _sync_h_scroll(self, *args): self.viewport.xview(*args); self.h_ruler.xview(*args)
    def _on_mouse_wheel(self, event):
        if event.state & 0x0004:
            if event.delta > 0: self.zoom_in()
            else: self.zoom_out()
        else:
            d = int(-1 * (event.delta / 120))
            self.viewport.yview_scroll(d, "units"); self.v_ruler.yview_scroll(d, "units")

if __name__ == "__main__":
    root = tk.Tk()
    app = ProfessionalPDFViewer(root)
    root.mainloop()
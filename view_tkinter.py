import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk
from interface import PDFViewInterface

class TkinterPDFView(PDFViewInterface):
    def __init__(self, root, controller_class):
        self.root = root
        self.controller = controller_class(self)
        self.tk_img = None
        self.text_layer_var = tk.BooleanVar(value=False)
        self._setup_ui()

    def _setup_ui(self):
        tbar = ttk.Frame(self.root, padding=5)
        tbar.pack(side=tk.TOP, fill=tk.X)
        
        ttk.Button(tbar, text="Open", command=self._on_open).pack(side=tk.LEFT)
        ttk.Separator(tbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Navigasi
        ttk.Button(tbar, text="<", command=lambda: self.controller.change_page(-1)).pack(side=tk.LEFT)
        self.pg_ent = ttk.Entry(tbar, width=5, justify="center")
        self.pg_ent.pack(side=tk.LEFT, padx=5)
        self.pg_ent.bind("<Return>", lambda e: self.controller.jump_to_page(int(self.pg_ent.get())))
        self.lbl_total = ttk.Label(tbar, text="/ 0")
        self.lbl_total.pack(side=tk.LEFT)
        ttk.Button(tbar, text=">", command=lambda: self.controller.change_page(1)).pack(side=tk.LEFT)
        
        ttk.Separator(tbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # TOGGLE LAYER TEKS
        self.text_toggle = ttk.Checkbutton(
            tbar, text="Text Layer", 
            variable=self.text_layer_var,
            command=lambda: self.controller.toggle_text_layer(self.text_layer_var.get()),
            state="disabled"
        )
        self.text_toggle.pack(side=tk.LEFT)

        ttk.Button(tbar, text="Zoom +", command=lambda: self.controller.set_zoom("in")).pack(side=tk.RIGHT)
        ttk.Button(tbar, text="Zoom -", command=lambda: self.controller.set_zoom("out")).pack(side=tk.RIGHT)

        # Viewport
        container = tk.Frame(self.root, bg="#323639")
        container.pack(fill=tk.BOTH, expand=True)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(1, weight=1)

        self.h_rule = tk.Canvas(container, height=25, bg="#e0e0e0", bd=0, highlightthickness=0)
        self.v_rule = tk.Canvas(container, width=25, bg="#e0e0e0", bd=0, highlightthickness=0)
        self.viewport = tk.Canvas(container, bg="#323639", bd=0, highlightthickness=0)
        
        self.h_rule.grid(row=0, column=1, sticky="ew")
        self.v_rule.grid(row=1, column=0, sticky="ns")
        self.viewport.grid(row=1, column=1, sticky="nsew")

        v_scr = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self._sync_v)
        v_scr.grid(row=1, column=2, sticky="ns")
        self.viewport.configure(yscrollcommand=v_scr.set)

        self.viewport.bind("<Configure>", lambda e: self.controller.refresh())
        self.viewport.bind_all("<MouseWheel>", self._on_wheel)

    # --- Implementasi Interface ---
    def get_viewport_size(self):
        self.root.update_idletasks()
        return self.viewport.winfo_width(), self.viewport.winfo_height()

    def display_page(self, pix, ox, oy, region):
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.tk_img = ImageTk.PhotoImage(img)
        self.viewport.delete("all")
        self.viewport.create_image(ox, oy, anchor=tk.NW, image=self.tk_img)
        self.viewport.config(scrollregion=region)
        self.h_rule.config(scrollregion=region)
        self.v_rule.config(scrollregion=region)

    def draw_text_layer(self, words, ox, oy, zoom):
        for w in words:
            self.viewport.create_rectangle(
                w[0]*zoom + ox, w[1]*zoom + oy, 
                w[2]*zoom + ox, w[3]*zoom + oy,
                outline="#0078d7", fill="#0078d7", stipple="gray25"
            )

    def draw_rulers(self, doc_w, doc_h, ox, oy, zoom):
        self.h_rule.delete("all")
        self.v_rule.delete("all")
        step = 100 if zoom < 1.0 else 50
        for u in range(0, int(doc_w)+1, 10):
            x = (u * zoom) + ox
            if u % step == 0:
                self.h_rule.create_line(x, 25, x, 0)
                self.h_rule.create_text(x+2, 2, text=str(u), anchor=tk.NW, font=("Arial", 7))
        for u in range(0, int(doc_h)+1, 10):
            y = (u * zoom) + oy
            if u % step == 0:
                self.v_rule.create_line(25, y, 0, y)
                self.v_rule.create_text(2, y+2, text=str(u), anchor=tk.NW, font=("Arial", 7))

    def update_ui_info(self, page_num, total, zoom, is_sandwich):
        self.pg_ent.delete(0, tk.END)
        self.pg_ent.insert(0, str(page_num))
        self.lbl_total.config(text=f"/ {total}")
        self.text_toggle.config(state="normal" if is_sandwich else "disabled")
        if not is_sandwich: self.text_layer_var.set(False)

    def _on_open(self):
        p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        self.controller.open_document(p)

    def _sync_v(self, *args):
        self.viewport.yview(*args); self.v_rule.yview(*args)

    def _on_wheel(self, e):
        if e.state & 0x0004: self.controller.set_zoom("in" if e.delta > 0 else "out")
        else: 
            d = int(-1*(e.delta/120))
            self.viewport.yview_scroll(d, "units"); self.v_rule.yview_scroll(d, "units")
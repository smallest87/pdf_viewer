import tkinter as tk
from Model.document_model import PDFDocumentModel
from View.main_view import TkinterPDFView
from Controller.main_controller import PDFController

def main():
    root = tk.Tk()
    root.title("Modular PDF Viewer Pro - MVC Version")
    root.geometry("1100x850")
    
    # 1. Inisialisasi Model (Data)
    model = PDFDocumentModel()
    
    # 2. Inisialisasi View & Controller via Dependency Injection
    # Kita menggunakan lambda agar View bisa menginstansiasi Controller 
    # dengan referensi ke dirinya sendiri dan Model.
    app = TkinterPDFView(root, lambda v: PDFController(v, model))
    
    root.mainloop()

if __name__ == "__main__":
    main()
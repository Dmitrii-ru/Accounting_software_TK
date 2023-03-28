import tkinter

import tkinter as tk
from tkinter import CENTER

import Nalog



class App_Main(tk.Frame):
    def __init__(self, root):
        super().__init__(root)
        self.init_app()

    def init_app(self):

        toolbar = tk.Frame()
        toolbar.pack(side=tk.TOP, fill=tk.X)

        btn_NalogClass = tk.Button(text='Отчет по налогам', command=self.open_nalog)
        btn_NalogClass.pack(padx=120, pady=30)

    def open_nalog(self):
        Nalog.Child_Nalog(root)





if __name__ == "__main__":
    root = tk.Tk()
    app = App_Main(root)
    root.title('СуперБухгалтер')

    root.wait_window()

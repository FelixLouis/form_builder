import tkinter as tk


class ScrollableFrame(tk.Frame):
    def __init__(self, master):
        self.outer = tk.Frame(master)
        self.canvas = tk.Canvas(self.outer)
        self.scroll = tk.Scrollbar(self.outer, command=self.canvas.yview)
        tk.Frame.__init__(self, self.canvas)
        self.contentWindow = self.canvas.create_window((0, 0), window=self, anchor=tk.NW)

        self.canvas.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.config(yscrollcommand=self.scroll.set)
        self.bind("<Configure>", self.resize_canvas)

        self.pack = self.outer.pack
        self.place = self.outer.place
        self.grid = self.outer.grid

        self.bind("<Enter>", self.enable_scroll_canvas)
        self.bind("<Leave>", self.disable_scroll_canvas)

    def scroll_canvas(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def enable_scroll_canvas(self, event):
        self.canvas.bind_all("<MouseWheel>", self.scroll_canvas)

    def disable_scroll_canvas(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def resize_canvas(self, event):
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.canvas.itemconfig(self.contentWindow, width=self.canvas.winfo_width())

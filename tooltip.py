import tkinter as tk


class ToolTip(object):
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None

        def enter(event): self.show_tooltip()
        widget.bind('<Enter>', enter)

        def leave(event): self.hide_tooltip()
        widget.bind('<Leave>', leave)

    def show_tooltip(self):
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1) # window without border and no normal means of closing

        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx()
        y = y + self.widget.winfo_rooty() - 20
        tw.wm_geometry(f"+{x}+{y}")

        tk.Label(tw, text=self.text, background="#ffffe0", relief='solid', borderwidth=1).pack()

    def hide_tooltip(self):
        tw = self.tooltip_window
        tw.destroy()
        self.tooltip_window = None

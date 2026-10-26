"""Native Tk visual theme: white type, violet neon accents and Sowilo rune."""
import tkinter as tk
from tkinter import font as tkfont
from tkinter.scrolledtext import ScrolledText

BG = "#090710"
PANEL = "#141020"
SURFACE = "#1d142e"
FG = "#faf7ff"
MUTED = "#b9accd"
PURPLE = "#7436cf"
NEON = "#c481ff"
BORDER = "#44305f"
FONT = "DejaVu Sans"


def draw_rune(canvas, x=0, y=0, scale=1):
    """Draw the same Sowilo zigzag at any size; no image or font dependency."""
    points = [x + v * scale if i % 2 == 0 else y + v * scale
              for i, v in enumerate((44, 10, 18, 30, 42, 48, 16, 70))]
    for color, width in (("#27123f", 17), ("#482069", 11), ("#8e43cd", 6), (NEON, 3), (FG, 1)):
        canvas.create_line(*points, fill=color, width=max(1, width * scale), capstyle="round", joinstyle="round")


def rune(parent, size=80, background=PANEL):
    canvas = tk.Canvas(parent, width=size, height=size, bg=background, highlightthickness=0)
    draw_rune(canvas, size * .12, size * .02, size / 90)
    return canvas


def rounded_panel(canvas, left, top, right, bottom, radius=20, **options):
    points = (left+radius, top, right-radius, top, right, top,
              right, top+radius, right, bottom-radius, right, bottom,
              right-radius, bottom, left+radius, bottom, left, bottom,
              left, bottom-radius, left, top+radius, left, top)
    return canvas.create_polygon(*points, smooth=True, splinesteps=30, **options)


class RoundedPanel(tk.Frame):
    """A rounded, resizable surface containing ordinary Tk widgets."""
    def __init__(self, parent, width=300, height=180, padding=16):
        super().__init__(parent, bg=parent.cget("bg"), width=width, height=height)
        self.pack_propagate(False)
        canvas = tk.Canvas(self, bg=parent.cget("bg"), highlightthickness=0,
                           width=width, height=height)
        canvas.pack(fill="both", expand=True)
        self.body = tk.Frame(canvas, bg=PANEL)
        window = canvas.create_window(padding, padding, window=self.body, anchor="nw")
        def resize(event):
            canvas.delete("surface")
            rounded_panel(canvas, 1, 1, event.width-1, event.height-1,
                          fill=PANEL, outline=BORDER, tags="surface")
            canvas.tag_lower("surface")
            canvas.itemconfigure(window, width=max(1, event.width-2*padding),
                                 height=max(1, event.height-2*padding))
        canvas.bind("<Configure>", resize)


class WelcomeBanner(tk.Canvas):
    """Responsive vector scene: luminous rune and quiet orbital geometry."""
    def __init__(self, parent):
        super().__init__(parent, bg=parent.cget("bg"), height=158,
                         highlightthickness=0, borderwidth=0)
        self.bind("<Configure>", lambda event: self._draw_banner())

    def _draw_banner(self):
        self.delete("all")
        width = max(520, self.winfo_width())
        rounded_panel(self, 1, 1, width-1, 155, fill="#171023", outline="#55356e")
        cx, cy = width-110, 78
        for offset in range(-3, 4):
            x = cx + offset*32
            self.create_line(x, 12, x, 144, fill="#241630")
        for y in (24, 56, 88, 120):
            self.create_line(width-250, y, width-18, y, fill="#241630")
        for radius, color in ((68, "#1c112c"), (57, "#241536"), (46, "#301d46"), (34, "#3b2354")):
            self.create_oval(cx-radius, cy-radius, cx+radius, cy+radius,
                             fill=color, outline=color)
        self.create_oval(cx-65, cy-65, cx+65, cy+65, outline="#654083")
        self.create_arc(cx-72, cy-72, cx+72, cy+72, start=25, extent=72,
                        style="arc", outline=NEON, width=2)
        self.create_arc(cx-72, cy-72, cx+72, cy+72, start=205, extent=45,
                        style="arc", outline="#8b49bf", width=2)
        self.create_oval(cx+57, cy-45, cx+63, cy-39, fill=FG, outline=NEON)
        draw_rune(self, cx-35, cy-48, 1.2)
        self.create_text(24, 24, text="S O W I L O   C O M M U N I T Y", anchor="w",
                         font=(FONT, 8, "bold"), fill=NEON)
        self.create_text(24, 72, text="Votre espace. Votre élan.", anchor="w",
                         font=(FONT, 23 if width >= 750 else 18, "bold"), fill=FG)
        self.create_text(25, 110, text="Une idée. Une action. Un pas de plus.",
                         anchor="w", font=(FONT, 10), fill=MUTED)
        self.create_line(25, 135, 85, 135, fill=NEON, width=2)
        self.create_line(90, 135, 140, 135, fill="#503168", width=2)


class RoundedButton(tk.Canvas):
    """Rounded native canvas control with mouse, keyboard and focus handling."""
    def __init__(self, parent, text, command, primary=False):
        self._button_options = {
            "text": text, "command": command, "bg": PURPLE if primary else SURFACE,
            "fg": FG, "anchor": "center", "padx": 16, "pady": 10,
            "highlightbackground": NEON if primary else BORDER, "state": "normal",
        }
        self._hover = self._pressed = self._focused = False
        self._font = tkfont.Font(root=parent, family=FONT, size=10, weight="bold")
        super().__init__(parent, bg=parent.cget("bg"), highlightthickness=0,
                         borderwidth=0, takefocus=True, cursor="hand2",
                         width=self._font.measure(text) + 36,
                         height=max(42, self._font.metrics("linespace") + 22))
        self.bind("<Configure>", lambda event: self._draw())
        self.bind("<Enter>", lambda event: self._interaction(hover=True))
        self.bind("<Leave>", lambda event: self._interaction(hover=False))
        self.bind("<FocusIn>", lambda event: self._interaction(focused=True))
        self.bind("<FocusOut>", lambda event: self._interaction(focused=False, pressed=False))
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<KeyPress-space>", self._key_press)
        self.bind("<KeyRelease-space>", self._key_release)
        self.bind("<Return>", lambda event: self.invoke())
        self.bind("<Escape>", lambda event: self._interaction(pressed=False))
        self._draw()

    def _interaction(self, **values):
        for name, value in values.items():
            setattr(self, "_" + name, value)
        self._draw()

    def _press(self, event):
        if self._button_options["state"] != "disabled":
            self.focus_set()
            self._interaction(pressed=True)

    def _release(self, event):
        activate = self._pressed and 0 <= event.x < self.winfo_width() and 0 <= event.y < self.winfo_height()
        self._interaction(pressed=False)
        if activate:
            self.invoke()

    def _key_press(self, event):
        if self._button_options["state"] != "disabled":
            self._interaction(pressed=True)
        return "break"

    def _key_release(self, event):
        pressed = self._pressed
        self._interaction(pressed=False)
        if pressed:
            self.invoke()
        return "break"

    def invoke(self):
        if self._button_options["state"] != "disabled" and callable(self._button_options["command"]):
            return self._button_options["command"]()

    def configure(self, cnf=None, **kwargs):
        options = dict(cnf or {})
        options.update(kwargs)
        geometry_changed = any(key in options for key in ("text", "padx", "pady"))
        for key in list(options):
            if key in self._button_options:
                self._button_options[key] = options.pop(key)
        if options:
            super().configure(**options)
        if geometry_changed:
            super().configure(width=self._font.measure(self._button_options["text"]) + 2 * self._button_options["padx"] + 4,
                              height=max(42, self._font.metrics("linespace") + 2 * self._button_options["pady"] + 2))
        self._draw()

    config = configure

    def cget(self, key):
        return self._button_options[key] if key in self._button_options else super().cget(key)

    def _draw(self):
        self.delete("all")
        width = max(self.winfo_width(), int(super().cget("width"))) if self.winfo_width() <= 1 else self.winfo_width()
        height = max(self.winfo_height(), int(super().cget("height"))) if self.winfo_height() <= 1 else self.winfo_height()
        radius = min(16, height / 2 - 2, width / 2 - 2)
        left, top, right, bottom = 2, 2, width - 2, height - 2
        points = (left+radius, top, right-radius, top, right, top,
                  right, top+radius, right, bottom-radius, right, bottom,
                  right-radius, bottom, left+radius, bottom, left, bottom,
                  left, bottom-radius, left, top+radius, left, top)
        disabled = self._button_options["state"] == "disabled"
        fill = self._button_options["bg"]
        if not disabled and self._pressed:
            fill = "#582790"
        elif not disabled and self._hover:
            fill = "#8b43dc" if fill == PURPLE else "#2b1c40"
        outline = "#e7ccff" if self._focused else NEON if self._hover and not disabled else self._button_options["highlightbackground"]
        self.create_polygon(*points, smooth=True, splinesteps=24, fill=fill,
                            outline=BORDER if disabled else outline, width=2 if self._focused else 1)
        anchor = self._button_options["anchor"]
        x = self._button_options["padx"] + 3 if anchor == "w" else width / 2
        self.create_text(x, height / 2, text=self._button_options["text"], font=self._font,
                         anchor="w" if anchor == "w" else "center",
                         fill=MUTED if disabled else self._button_options["fg"])


class NeonTheme:
    BG, PANEL, FG, MUTED, PURPLE = BG, PANEL, FG, MUTED, PURPLE

    def label(self, parent, text, size=11, bold=False, muted=False):
        return tk.Label(parent, text=text, bg=parent.cget("bg"),
                        fg=MUTED if muted else FG,
                        font=(FONT, size, "bold" if bold else "normal"), anchor="w")

    def button(self, parent, text, command, primary=False):
        return RoundedButton(parent, text, command, primary)

    def text_area(self, parent, height=12):
        widget = ScrolledText(parent, height=height, wrap="word", bg=PANEL, fg=FG,
                              insertbackground=NEON, selectbackground="#653398", selectforeground=FG,
                              exportselection=False, relief="flat", padx=16, pady=12,
                              font=(FONT, 11), undo=True, spacing1=2, spacing3=4,
                              highlightthickness=1, highlightbackground=BORDER, highlightcolor=NEON)
        widget.vbar.configure(bg=SURFACE, troughcolor=BG, activebackground=PURPLE,
                              borderwidth=0, highlightthickness=0, width=11)
        return widget

    def entry(self, parent, variable):
        return tk.Entry(parent, textvariable=variable, bg=PANEL, fg=FG,
                        font=(FONT, 11), insertbackground=NEON, selectbackground=PURPLE,
                        relief="flat", highlightthickness=1, highlightbackground=BORDER,
                        highlightcolor=NEON)

    def listbox(self, parent):
        return tk.Listbox(parent, bg=PANEL, fg=FG, font=(FONT, 11),
                          selectbackground="#54277e", selectforeground=FG,
                          exportselection=False, relief="flat", activestyle="none",
                          width=25, highlightthickness=1, highlightbackground=BORDER,
                          highlightcolor=NEON)

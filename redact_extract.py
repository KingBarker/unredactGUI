import os
import sys
import platform
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pdfplumber
import fitz  # PyMuPDF
from datetime import datetime
from pathlib import Path

# Embedded 24x24 Transparent PNG GitHub Icon (Base64)
GITHUB_ICON_B64 = """
iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAAsTAAALEwEAmpwYAAAB
mElEQVR4nO2UPU/CQBjH/++l5aOtqCgSRwcTjR8G42OMiQ66+RUc/QhuXsVYdGCDiYszk0wcjIqA
D9DCoRfa8/RYaCtYqPfQ5J7m0v/9P8/13t0D/msI+d9QSiWICL2MMtom7OzsiD2Tye5+fX01hRD6
dx9DKZUkEundcRx7Q0S0ZaSiiLaM49gHmdzuna7r8r9+4P695/F44kU0mncsy3IQEW0ZSimVMC3r
NJpI7MRjscTz/L17z/N3AvT03Mzy8tO5UCh0L5VKSQD+K6lUSgqFQvfLr9/O9PTczHR03Ar+GoFh
GNli8bGs67oilFJ4/vwJ+vpuwDCM3951XVcssfhc1jCMbGdnx8ArgbG+vn4qnU6/MwzD14XneUin
0wiFQvB8A4lEAn6//0/HMAxfOp1+V1tbO4HOzssz3Qi3tx+PrK+/f/X5fKd+vx+O48BxXCil4PP5
4Pf7EQolkEg8Q6MRYGTkUklEvDbQ2dnRt7Awk/P5fKf+gB/b2x2NVguNRgOvX79GIpFAKvUcz3Ox
tDSbFxHPG+jq6rg0OTn+MhgMnvD7/ahW61BKQSkF3/eVa9uv4rEns57nvRERz38I+d43f6q9HW1R
04kAAAAASUVORK5CYII=
"""

class ProfessionalUnredactApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Professional PDF Unredactor & Viewer")
        self.root.geometry("1200x900")
        
        # Core State
        self.files_to_process = []
        self.output_dir = tk.StringVar()
        self.mode = tk.StringVar(value="side_by_side")
        self.include_subdirs = tk.BooleanVar(value=True)
        self.current_theme = tk.StringVar(value="Professional White")
        
        # Viewer State
        self.viewer_dir = None
        self.current_pdf_doc = None
        self.current_page_num = 0
        self.zoom_level = 1.0
        self.tk_image_ref = None
        self.is_fullscreen = False
        
        # Sidebar Animation State
        self.sidebar_expanded = True
        self.sidebar_width = 280
        self.animation_step = 40

        # Assets
        try:
            self.github_icon = tk.PhotoImage(data=GITHUB_ICON_B64)
        except Exception:
            self.github_icon = None

        # Theme Configuration
        self.themes = {
            "Professional White": {
                "bg_window": "#FFFFFF", "bg_panel": "#F4F4F4",
                "border": "#888888", "accent": "#0067C0", "text": "#202020",
                "entry_bg": "#FFFFFF", "list_bg": "#FFFFFF", "canvas_bg": "#505050"
            },
            "Soft Vanilla": {
                "bg_window": "#FFFDF5", "bg_panel": "#F9F3E5",
                "border": "#D4C5A5", "accent": "#C5A028", "text": "#4A4238",
                "entry_bg": "#FFFEFA", "list_bg": "#FFFEFA", "canvas_bg": "#5C554B"
            },
            "Soft Sky": {
                "bg_window": "#F0F8FF", "bg_panel": "#E1EFFE",
                "border": "#B0C4DE", "accent": "#3B82F6", "text": "#1E3A8A",
                "entry_bg": "#FAFDFF", "list_bg": "#FAFDFF", "canvas_bg": "#475569"
            },
            "Soft Mint": {
                "bg_window": "#F5FFFA", "bg_panel": "#E6F7EF",
                "border": "#A5D6A7", "accent": "#2E7D32", "text": "#1B4D3E",
                "entry_bg": "#FDFFFE", "list_bg": "#FDFFFE", "canvas_bg": "#3E5C4B"
            },
            "Soft Lavender": {
                "bg_window": "#FAF5FF", "bg_panel": "#F3E8FF",
                "border": "#D8B4FE", "accent": "#9333EA", "text": "#581C87",
                "entry_bg": "#FCFAFF", "list_bg": "#FCFAFF", "canvas_bg": "#4C1D95"
            },
            "Soft Rose": {
                "bg_window": "#FFF5F7", "bg_panel": "#FFE4E6",
                "border": "#FECDD3", "accent": "#E11D48", "text": "#881337",
                "entry_bg": "#FFF0F3", "list_bg": "#FFF0F3", "canvas_bg": "#831843"
            }
        }

        self._init_style_engine()
        self._build_layout()
        self._bind_shortcuts()
        self.apply_theme("Professional White")

    def _init_style_engine(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

    def apply_theme(self, theme_name):
        t = self.themes.get(theme_name, self.themes["Professional White"])
        
        # Root & Container Backgrounds
        self.root.configure(bg=t["bg_window"])
        
        if hasattr(self, 'top_bar_frame'):
            self.top_bar_frame.configure(bg=t["bg_window"])
            for widget in self.top_bar_frame.winfo_children():
                if isinstance(widget, tk.Frame): widget.configure(bg=t["bg_window"])
                if isinstance(widget, tk.Label): widget.configure(bg=t["bg_window"], fg=t["text"])

        if hasattr(self, 'footer_frame'):
            self.footer_frame.configure(bg=t["bg_window"])
            self.footer_label.configure(bg=t["bg_window"], fg=t["text"])

        if hasattr(self, 'canvas_container'):
            self.canvas_container.configure(bg=t["canvas_bg"], bd=1, relief="solid")

        # TTK Styles
        s = self.style
        s.configure(".", background=t["bg_window"], foreground=t["text"], font=("Segoe UI", 10))
        s.configure("TFrame", background=t["bg_window"])
        s.configure("Panel.TFrame", background=t["bg_panel"], bordercolor=t["border"], borderwidth=1, relief="solid")
        s.configure("TLabelframe", background=t["bg_window"], bordercolor=t["border"], borderwidth=1, relief="solid")
        s.configure("TLabelframe.Label", background=t["bg_window"], foreground=t["accent"], font=("Segoe UI", 11, "bold"))

        s.configure("TNotebook", background=t["bg_panel"], borderwidth=0)
        s.configure("TNotebook.Tab", padding=[20, 10], font=("Segoe UI", 10, "bold"), background=t["bg_panel"], foreground=t["border"])
        s.map("TNotebook.Tab", background=[("selected", t["bg_window"])], foreground=[("selected", t["accent"])])

        s.configure("Action.TButton", font=("Segoe UI", 9, "bold"), background=t["bg_panel"], foreground=t["text"], borderwidth=1, bordercolor=t["border"], relief="solid")
        s.map("Action.TButton", background=[("active", t["border"])], bordercolor=[("active", t["accent"])])
        
        s.configure("Primary.TButton", font=("Segoe UI", 11, "bold"), foreground="white", background=t["accent"], borderwidth=1, bordercolor=t["accent"], relief="flat")
        s.map("Primary.TButton", background=[("active", t["border"])], bordercolor=[("active", t["border"])])

        s.configure("Toggle.TButton", font=("Segoe UI", 12, "bold"), background=t["bg_panel"], foreground=t["text"], borderwidth=1, relief="solid")
        s.map("Toggle.TButton", background=[("active", t["accent"])], foreground=[("active", "white")])

        s.configure("TEntry", fieldbackground=t["entry_bg"], bordercolor=t["border"], borderwidth=1, relief="solid")
        s.configure("TCheckbutton", background=t["bg_window"], foreground=t["text"])
        s.configure("TRadiobutton", background=t["bg_window"], foreground=t["text"])

        # Native Widgets
        if hasattr(self, 'queue_list'):
            self.queue_list.config(bg=t["list_bg"], fg=t["text"], selectbackground=t["accent"], selectforeground="white", highlightbackground=t["border"])
        
        if hasattr(self, 'file_listbox'):
            self.file_listbox.config(bg=t["list_bg"], fg=t["text"], selectbackground=t["accent"], selectforeground="white", highlightbackground=t["border"])
            
        if hasattr(self, 'log_text'):
            self.log_text.config(bg=t["list_bg"], fg=t["text"], highlightbackground=t["border"])

        if hasattr(self, 'preview_canvas'):
            self.preview_canvas.config(bg=t["canvas_bg"])

        self.root.update_idletasks()

    def _bind_shortcuts(self):
        self.root.bind("<Left>", self.prev_file)
        self.root.bind("<Right>", self.next_file)
        self.root.bind("<Control-plus>", lambda e: self.zoom_in())
        self.root.bind("<Control-minus>", lambda e: self.zoom_out())
        self.root.bind("<F11>", lambda e: self.toggle_fullscreen())
        self.root.bind("<Escape>", lambda e: self.exit_fullscreen())

    def _build_layout(self):
        # Top Bar
        self.top_bar_frame = tk.Frame(self.root, height=40)
        self.top_bar_frame.pack(side="top", fill="x", padx=15, pady=(10, 0))
        
        theme_frame = tk.Frame(self.top_bar_frame)
        theme_frame.pack(side="right")
        
        tk.Label(theme_frame, text="THEME:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
        self.theme_combo = ttk.Combobox(theme_frame, textvariable=self.current_theme, values=list(self.themes.keys()), state="readonly", width=20)
        self.theme_combo.pack(side="left")
        self.theme_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_theme(self.current_theme.get()))

        # Tabs
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(side="top", fill="both", expand=True, padx=15, pady=10)

        self.tab_process = ttk.Frame(self.tabs)
        self.tab_viewer = ttk.Frame(self.tabs)
        
        self.tabs.add(self.tab_process, text=" DASHBOARD / PROCESSOR ")
        self.tabs.add(self.tab_viewer, text=" RESULTS VIEWER ")
        
        self._build_process_tab(self.tab_process)
        self._build_viewer_tab(self.tab_viewer)

        # Footer
        self.footer_frame = tk.Frame(self.root)
        self.footer_frame.pack(side="bottom", fill="x", pady=(0, 5))
        
        self.footer_label = tk.Label(
            self.footer_frame, 
            text="  GUI created by KingBarker | Credits to Leedrake5", 
            font=("Segoe UI", 10, "italic"),
            image=self.github_icon,
            compound="left"
        )
        self.footer_label.pack(side="bottom")

    def _build_process_tab(self, parent):
        container = ttk.Frame(parent, padding=20)
        container.pack(fill="both", expand=True)

        # Inputs
        in_frame = ttk.LabelFrame(container, text=" 1. INPUT FILES ", padding=15)
        in_frame.pack(fill="x", pady=(0, 15))

        btn_box = ttk.Frame(in_frame)
        btn_box.pack(fill="x", pady=(0, 10))
        ttk.Button(btn_box, text="+ ADD FILES", style="Action.TButton", command=self.add_files).pack(side="left", padx=(0, 5))
        ttk.Button(btn_box, text="+ ADD FOLDER", style="Action.TButton", command=self.add_folder).pack(side="left", padx=5)
        ttk.Checkbutton(btn_box, text="Include Subfolders", variable=self.include_subdirs).pack(side="left", padx=20)
        ttk.Button(btn_box, text="CLEAR LIST", style="Action.TButton", command=self.clear_queue).pack(side="right")

        self.queue_list = tk.Listbox(in_frame, height=8, bd=1, relief="solid", highlightthickness=1)
        self.queue_list.pack(fill="x", pady=5)
        self.lbl_count = ttk.Label(in_frame, text="Queue Empty", font=("Segoe UI", 9, "bold"))
        self.lbl_count.pack(anchor="e")

        # Settings
        out_frame = ttk.LabelFrame(container, text=" 2. SETTINGS ", padding=15)
        out_frame.pack(fill="x", pady=(0, 15))

        path_row = ttk.Frame(out_frame)
        path_row.pack(fill="x", pady=(0, 15))
        ttk.Label(path_row, text="Save Location:").pack(side="left")
        ttk.Entry(path_row, textvariable=self.output_dir).pack(side="left", fill="x", expand=True, padx=10)
        ttk.Button(path_row, text="BROWSE...", style="Action.TButton", command=self.browse_output).pack(side="left")

        opt_row = ttk.Frame(out_frame)
        opt_row.pack(fill="x")
        ttk.Label(opt_row, text="Recovery Mode:").pack(side="left", padx=(0, 10))
        ttk.Radiobutton(opt_row, text="Side-by-Side (Comparison)", variable=self.mode, value="side_by_side").pack(side="left", padx=10)
        ttk.Radiobutton(opt_row, text="Overlay (White Text)", variable=self.mode, value="overlay_white").pack(side="left", padx=10)

        # Execute
        run_frame = ttk.LabelFrame(container, text=" 3. EXECUTE ", padding=15)
        run_frame.pack(fill="both", expand=True)

        self.btn_run = ttk.Button(run_frame, text="RUN BATCH PROCESS", style="Primary.TButton", command=self.start_processing)
        self.btn_run.pack(fill="x", pady=(0, 15), ipady=5)

        self.progress = ttk.Progressbar(run_frame, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", pady=(0, 10))

        self.log_text = tk.Text(run_frame, height=8, bd=1, relief="solid", highlightthickness=0)
        self.log_text.pack(fill="both", expand=True)

    def _build_viewer_tab(self, parent):
        self.viewer_container = ttk.Frame(parent)
        self.viewer_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Sidebar
        self.viewer_left = ttk.Frame(self.viewer_container, style="Panel.TFrame", padding=10, width=self.sidebar_width)
        self.viewer_left.pack_propagate(False) 
        self.viewer_left.pack(side="left", fill="y")

        ttk.Label(self.viewer_left, text="FILE BROWSER", style="Header.TLabel", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))

        l_tools = ttk.Frame(self.viewer_left, style="Panel.TFrame")
        l_tools.pack(fill="x", pady=(0, 10))
        ttk.Button(l_tools, text="SELECT FOLDER", style="Action.TButton", command=self.browse_viewer_folder).pack(side="top", fill="x", pady=(0, 5))
        
        row2 = ttk.Frame(l_tools, style="Panel.TFrame")
        row2.pack(fill="x")
        ttk.Button(row2, text="REFRESH", style="Action.TButton", command=self.refresh_file_list).pack(side="left", fill="x", expand=True, padx=(0,2))
        ttk.Button(row2, text="OPEN DIR", style="Action.TButton", command=self.open_current_folder).pack(side="left", fill="x", expand=True, padx=(2,0))
        
        self.file_listbox = tk.Listbox(self.viewer_left, bd=1, relief="solid", highlightthickness=0, activestyle="none")
        self.file_listbox.pack(fill="both", expand=True)
        self.file_listbox.bind("<<ListboxSelect>>", self.on_file_select)

        # Preview Area
        self.viewer_right = ttk.Frame(self.viewer_container, padding=(10, 0, 0, 0))
        self.viewer_right.pack(side="left", fill="both", expand=True)

        top_bar = ttk.Frame(self.viewer_right, style="Panel.TFrame", padding=5)
        top_bar.pack(fill="x", pady=(0, 10))
        
        self.btn_show_sidebar = ttk.Button(top_bar, text="SHOW LIST >>", style="Action.TButton", command=self.toggle_sidebar)

        ttk.Label(top_bar, text="ZOOM:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(5,5))
        ttk.Button(top_bar, text="-", width=3, style="Action.TButton", command=self.zoom_out).pack(side="left")
        self.lbl_zoom = ttk.Label(top_bar, text="100%", width=6, anchor="center")
        self.lbl_zoom.pack(side="left", padx=5)
        ttk.Button(top_bar, text="+", width=3, style="Action.TButton", command=self.zoom_in).pack(side="left")
        ttk.Button(top_bar, text="FIT WIDTH", style="Action.TButton", command=self.fit_width).pack(side="left", padx=(10, 0))
        
        ttk.Button(top_bar, text="OPEN IN SYSTEM", style="Action.TButton", command=self.open_current_in_system).pack(side="right", padx=5)
        ttk.Button(top_bar, text="FULLSCREEN", style="Action.TButton", command=self.toggle_fullscreen).pack(side="right", padx=5)

        self.canvas_container = tk.Frame(self.viewer_right, bd=1, relief="solid")
        self.canvas_container.pack(fill="both", expand=True)

        self.preview_canvas = tk.Canvas(self.canvas_container, bd=0, highlightthickness=0)
        self.preview_canvas.pack(side="left", fill="both", expand=True)

        vs = ttk.Scrollbar(self.canvas_container, orient="vertical", command=self.preview_canvas.yview)
        vs.pack(side="right", fill="y")
        hs = ttk.Scrollbar(self.viewer_right, orient="horizontal", command=self.preview_canvas.xview)
        hs.pack(side="bottom", fill="x")
        self.preview_canvas.config(yscrollcommand=vs.set, xscrollcommand=hs.set)
        self.preview_canvas.bind("<Control-MouseWheel>", self.on_mousewheel_zoom)

        nav_bar = ttk.Frame(self.viewer_right, padding=5)
        nav_bar.pack(side="bottom", fill="x")
        self.btn_prev_p = ttk.Button(nav_bar, text="< PREV PAGE", style="Action.TButton", command=self.prev_page, state="disabled")
        self.btn_prev_p.pack(side="left")
        self.lbl_page = ttk.Label(nav_bar, text="Page 0 of 0", font=("Segoe UI", 10, "bold"))
        self.lbl_page.pack(side="left", padx=20)
        self.btn_next_p = ttk.Button(nav_bar, text="NEXT PAGE >", style="Action.TButton", command=self.next_page, state="disabled")
        self.btn_next_p.pack(side="left")

        # Sliding Handle
        self.btn_toggle = ttk.Button(self.viewer_right, text="◄", style="Toggle.TButton", command=self.animate_sidebar_toggle, width=2)
        self.btn_toggle.place(relx=0, rely=0.5, anchor="w")

    # --- ANIMATION LOGIC ---
    def toggle_sidebar(self):
        if not self.sidebar_expanded:
            self.viewer_left.pack(side="left", fill="y", before=self.viewer_right)
            self._animate_open(0)
            self.btn_show_sidebar.pack_forget()

    def animate_sidebar_toggle(self):
        if self.sidebar_expanded:
            self._animate_close(self.sidebar_width)
        else:
            self.viewer_left.pack(side="left", fill="y", before=self.viewer_right)
            self._animate_open(0)

    def _animate_close(self, current_w):
        if current_w > 0:
            new_w = max(0, current_w - self.animation_step)
            self.viewer_left.config(width=new_w)
            self.root.after(10, lambda: self._animate_close(new_w))
        else:
            self.viewer_left.pack_forget()
            self.sidebar_expanded = False
            self.btn_toggle.config(text="►")
            self.btn_show_sidebar.pack(side="left", padx=(0, 10), before=self.lbl_zoom)

    def _animate_open(self, current_w):
        if current_w < self.sidebar_width:
            new_w = min(self.sidebar_width, current_w + self.animation_step)
            self.viewer_left.config(width=new_w)
            self.root.after(10, lambda: self._animate_open(new_w))
        else:
            self.sidebar_expanded = True
            self.btn_toggle.config(text="◄")
            self.btn_show_sidebar.pack_forget()

    # --- UTILS ---
    def log(self, msg):
        self.log_text.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.log_text.see("end")
        self.root.update_idletasks()

    def add_files(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF Documents", "*.pdf")])
        if files:
            for f in files:
                if f not in self.files_to_process:
                    self.files_to_process.append(f)
                    self.queue_list.insert("end", os.path.basename(f))
            self.lbl_count.config(text=f"{len(self.files_to_process)} FILES QUEUED")

    def add_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            p = Path(folder)
            found = p.rglob("*.pdf") if self.include_subdirs.get() else p.glob("*.pdf")
            c = 0
            for f in found:
                if f.is_file() and str(f) not in self.files_to_process:
                    self.files_to_process.append(str(f))
                    self.queue_list.insert("end", f.name)
                    c += 1
            self.lbl_count.config(text=f"{len(self.files_to_process)} FILES QUEUED")

    def browse_output(self):
        d = filedialog.askdirectory()
        if d: 
            self.output_dir.set(d)
            if not self.viewer_dir:
                self.viewer_dir = d
                self.refresh_file_list()

    def clear_queue(self):
        self.files_to_process = []
        self.queue_list.delete(0, "end")
        self.lbl_count.config(text="QUEUE EMPTY")

    def browse_viewer_folder(self):
        d = filedialog.askdirectory()
        if d:
            self.viewer_dir = d
            self.refresh_file_list()

    def open_current_folder(self):
        path = self.viewer_dir if self.viewer_dir else self.output_dir.get()
        if not path or not os.path.exists(path): return
        try:
            if platform.system() == "Windows": os.startfile(path)
            elif platform.system() == "Darwin": subprocess.Popen(["open", path])
            else: subprocess.Popen(["xdg-open", path])
        except: pass

    # --- PDF ENGINE ---
    def start_processing(self):
        if not self.files_to_process or not self.output_dir.get():
            messagebox.showwarning("Incomplete", "Please add files and select output.")
            return

        self.btn_run.config(state="disabled")
        dest = self.output_dir.get()
        self.progress["value"] = 0
        self.progress["maximum"] = len(self.files_to_process)
        
        try:
            for i, f_path in enumerate(self.files_to_process):
                fname = os.path.basename(f_path)
                self.log(f"Processing: {fname}")
                try:
                    self.process_pdf(f_path, dest)
                except Exception as e:
                    self.log(f"Error: {e}")
                self.progress["value"] = i + 1
            
            self.log("BATCH COMPLETE.")
            messagebox.showinfo("Success", "All files processed.")
            self.viewer_dir = dest
            self.refresh_file_list()
            self.tabs.select(self.tab_viewer)
        finally:
            self.btn_run.config(state="normal")

    def process_pdf(self, input_path, output_dir):
        extracted_data = []
        with pdfplumber.open(input_path) as pdf:
            for page in pdf.pages:
                words = page.extract_words(extra_attrs=["size"])
                words.sort(key=lambda w: (float(w["top"]), float(w["x0"])))
                lines = []
                if words:
                    curr, curr_top = [words[0]], float(words[0]["top"])
                    for w in words[1:]:
                        top = float(w["top"])
                        if abs(top - curr_top) <= 3.0: curr.append(w)
                        else:
                            lines.append(curr)
                            curr, curr_top = [w], top
                    lines.append(curr)
                p_data = []
                for line in lines:
                    line.sort(key=lambda w: float(w["x0"]))
                    txt = " ".join(w["text"] for w in line)
                    if txt.strip():
                        p_data.append((txt, float(line[0]["x0"]), float(line[0]["top"]), float(line[0].get("size", 10))))
                extracted_data.append(p_data)

        doc = fitz.open(input_path)
        out = fitz.open()
        for i, page in enumerate(doc):
            w, h = page.rect.width, page.rect.height
            if self.mode.get() == "side_by_side":
                np = out.new_page(width=w*2, height=h)
                np.show_pdf_page(fitz.Rect(0, 0, w, h), doc, i)
                off = w
            else:
                np = out.new_page(width=w, height=h)
                np.show_pdf_page(fitz.Rect(0, 0, w, h), doc, i)
                off = 0
            if i < len(extracted_data):
                col = (1, 1, 1) if self.mode.get() == "overlay_white" else (0, 0, 0)
                for (t, x, y, s) in extracted_data[i]:
                    np.insert_text(fitz.Point(x + off, y + s), t, fontsize=s, fontname="helv", color=col)
        
        out.save(os.path.join(output_dir, f"UNREDACTED_{os.path.basename(input_path)}"))

    # --- VIEWER ---
    def refresh_file_list(self):
        target_dir = self.viewer_dir if self.viewer_dir else self.output_dir.get()
        self.file_listbox.delete(0, "end")
        if not target_dir or not os.path.exists(target_dir): return
        files = sorted([f for f in os.listdir(target_dir) if f.lower().endswith(".pdf")])
        for f in files: self.file_listbox.insert("end", f)

    def on_file_select(self, event):
        sel = self.file_listbox.curselection()
        if not sel: return
        self.load_pdf_from_list(sel[0])

    def load_pdf_from_list(self, index):
        self.file_listbox.selection_clear(0, "end")
        self.file_listbox.selection_set(index)
        self.file_listbox.see(index)
        fname = self.file_listbox.get(index)
        target_dir = self.viewer_dir if self.viewer_dir else self.output_dir.get()
        fpath = os.path.join(target_dir, fname)
        if self.current_pdf_doc: self.current_pdf_doc.close()
        try:
            self.current_pdf_doc = fitz.open(fpath)
            self.current_page_num = 0
            self.render_page()
            self.update_nav_buttons()
        except: pass

    # --- PREV/NEXT FILE ---
    def prev_file(self, event=None):
        if self.tabs.select() != self.tab_viewer._w: return
        sel = self.file_listbox.curselection()
        if not sel: return
        idx = sel[0]
        if idx > 0: self.load_pdf_from_list(idx - 1)

    def next_file(self, event=None):
        if self.tabs.select() != self.tab_viewer._w: return
        sel = self.file_listbox.curselection()
        if not sel: return
        idx = sel[0]
        if idx < self.file_listbox.size() - 1: self.load_pdf_from_list(idx + 1)

    # --- PAGE RENDER ---
    def render_page(self):
        if not self.current_pdf_doc: return
        page = self.current_pdf_doc.load_page(self.current_page_num)
        mat = fitz.Matrix(self.zoom_level, self.zoom_level)
        pix = page.get_pixmap(matrix=mat)
        self.tk_image_ref = tk.PhotoImage(data=pix.tobytes("ppm"))
        self.preview_canvas.delete("all")
        cw = int(self.preview_canvas.winfo_width())
        cx = max(0, (cw - pix.width) // 2)
        self.preview_canvas.create_image(cx, 10, image=self.tk_image_ref, anchor="nw")
        self.preview_canvas.config(scrollregion=self.preview_canvas.bbox("all"))
        self.lbl_page.config(text=f"Page {self.current_page_num + 1} of {self.current_pdf_doc.page_count}")
        self.lbl_zoom.config(text=f"{int(self.zoom_level * 100)}%")

    def zoom_in(self):
        self.zoom_level *= 1.2
        self.render_page()
    def zoom_out(self):
        self.zoom_level /= 1.2
        self.render_page()
    def fit_width(self):
        if not self.current_pdf_doc: return
        page = self.current_pdf_doc.load_page(self.current_page_num)
        canvas_width = self.preview_canvas.winfo_width()
        if canvas_width > 50:
            self.zoom_level = (canvas_width - 40) / page.rect.width
            self.render_page()
    def on_mousewheel_zoom(self, event):
        if event.delta > 0: self.zoom_in()
        else: self.zoom_out()

    def next_page(self):
        if self.current_pdf_doc and self.current_page_num < self.current_pdf_doc.page_count - 1:
            self.current_page_num += 1
            self.render_page()
            self.update_nav_buttons()

    def prev_page(self):
        if self.current_pdf_doc and self.current_page_num > 0:
            self.current_page_num -= 1
            self.render_page()
            self.update_nav_buttons()

    def update_nav_buttons(self):
        if not self.current_pdf_doc: return
        self.btn_prev_p.config(state="normal" if self.current_page_num > 0 else "disabled")
        self.btn_next_p.config(state="normal" if self.current_page_num < self.current_pdf_doc.page_count - 1 else "disabled")

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)
        if not self.is_fullscreen: self.root.geometry("1200x900")
    def exit_fullscreen(self):
        self.is_fullscreen = False
        self.root.attributes("-fullscreen", False)
    def open_current_in_system(self):
        sel = self.file_listbox.curselection()
        if not sel: return
        target_dir = self.viewer_dir if self.viewer_dir else self.output_dir.get()
        path = os.path.join(target_dir, self.file_listbox.get(sel[0]))
        try:
            if platform.system() == "Windows": os.startfile(path)
            elif platform.system() == "Darwin": subprocess.Popen(["open", path])
            else: subprocess.Popen(["xdg-open", path])
        except: pass

if __name__ == "__main__":
    root = tk.Tk()
    app = ProfessionalUnredactApp(root)
    root.mainloop()

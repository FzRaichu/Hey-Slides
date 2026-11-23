"""Presentation-friendly CustomTkinter layout; recognition and navigation stay in main/session.

Layout (top to bottom):
  header   - title, subtitle, microphone status badge + input level meter
  toolbar  - start/stop, target (Demo slides | PowerPoint), connect, settings
  status   - one-line status text
  body     - left: slide preview (largest) + "last command" banner
             right: live transcript + action history
  MFCC     - compact strip: manual feature info + heatmap (analysis only)
"""

import tkinter as tk

import customtkinter as ctk

from app import config

THEME = {
    "bg": "#eef2f6", "card": "#ffffff", "ink": "#14273c", "muted": "#5b6f84",
    "accent": "#0b8a80", "accent_hover": "#09706a", "soft": "#e1f3f0", "soft_hover": "#cdebe6",
    "line": "#dbe3ea", "neutral": "#e3e9ef", "neutral_hover": "#cfd8e1",
    "slide": "#14273c", "slide_soft": "#22395a", "slide_soft_hover": "#2d4a70",
    "slide_caption": "#6dd8ca", "slide_kicker": "#a7bbcf", "slide_body": "#d4e1ec",
    "idle": "#8a9bb0", "field": "#f5f8fa", "ok": "#15803d", "warn": "#b45309", "danger": "#c2410c",
}

# Command banner look per result kind: (background, caption colour, caption text).
COMMAND_STYLES = {
    "info": ("#e1f3f0", "#0b8a80", "PERINTAH"),
    "ok": ("#dcf3e5", "#15803d", "PERINTAH DIJALANKAN"),
    "warn": ("#fdf0dc", "#b45309", "TIDAK ADA AKSI"),
    "error": ("#fbe4de", "#c2410c", "AKSI GAGAL"),
}


class ActionLog:
    """Read-only action history with the small Listbox API main.py uses.

    insert(0, text) adds a row on top, size() counts rows, delete(first, "end") trims.
    Rows containing "gagal" are shown in red, others in green.
    """

    def __init__(self, parent):
        self.box = ctk.CTkTextbox(parent, height=70, corner_radius=8, fg_color=THEME["card"],
                                  text_color=THEME["ink"], font=font(12), border_width=0, wrap="none")
        self.box.tag_config("ok", foreground=THEME["ok"])
        self.box.tag_config("fail", foreground=THEME["danger"])
        self.box.tag_config("empty", foreground=THEME["idle"])
        self.rows = []
        self._render()

    def __getattr__(self, name):  # pack/grid/winfo_* go to the textbox
        return getattr(self.box, name)

    def __str__(self):
        return str(self.box)

    def insert(self, index, text):
        self.rows.insert(0 if index == 0 else len(self.rows), text)
        self._render()

    def size(self):
        return len(self.rows)

    def delete(self, first, last=None):
        end = len(self.rows) if last == "end" else (first + 1 if last is None else last + 1)
        del self.rows[first:end]
        self._render()

    def _render(self):
        self.box.configure(state="normal")
        self.box.delete("1.0", "end")
        if not self.rows:
            self.box.insert("end", "Belum ada aksi. Ucapkan perintah atau klik Next.", "empty")
        for row in self.rows:
            self.box.insert("end", row + "\n", "fail" if "gagal" in row else "ok")
        self.box.configure(state="disabled")


def font(size, weight="normal", slant="roman", family="Segoe UI"):
    return ctk.CTkFont(family=family, size=size, weight=weight, slant=slant)


def _card(parent, color=None, radius=14):
    return ctk.CTkFrame(parent, fg_color=color or THEME["card"], corner_radius=radius)


def _wrap_on_resize(container, labels, margin):
    """Keep label text wrapped to the container width (CTk wraplength is in unscaled units)."""
    def update(event):
        scale = ctk.ScalingTracker.get_widget_scaling(container)
        width = max(180, event.width / scale - margin)
        for label in labels:
            label.configure(wraplength=width)
    container.bind("<Configure>", update, add="+")


def _neutral_button(parent, **kwargs):
    options = dict(height=36, corner_radius=10, font=font(13), fg_color=THEME["neutral"],
                   hover_color=THEME["neutral_hover"], text_color=THEME["ink"],
                   text_color_disabled=THEME["idle"])
    options.update(kwargs)
    return ctk.CTkButton(parent, **options)


def _option_menu(parent, variable, values, command=None, width=360):
    return ctk.CTkOptionMenu(parent, variable=variable, values=values, command=command, width=width,
                             height=34, corner_radius=8, font=font(13), dropdown_font=font(13),
                             fg_color=THEME["field"], button_color=THEME["neutral"],
                             button_hover_color=THEME["neutral_hover"], text_color=THEME["ink"],
                             text_color_disabled=THEME["idle"], dropdown_fg_color=THEME["card"],
                             dropdown_text_color=THEME["ink"], dropdown_hover_color=THEME["soft"])


def build_demo_view(ui):
    t = THEME
    ctk.set_appearance_mode("light")
    root = ui.root
    pad = 20

    outer = ctk.CTkFrame(root, fg_color=t["bg"], corner_radius=0)
    outer.pack(fill="both", expand=True)
    outer.grid_columnconfigure(0, weight=1)
    outer.grid_rowconfigure(3, weight=1)

    # ---- header ---------------------------------------------------------------
    header = ctk.CTkFrame(outer, fg_color="transparent")
    header.grid(row=0, column=0, sticky="ew", padx=pad, pady=(14, 0))
    header.grid_columnconfigure(0, weight=1)
    titles = ctk.CTkFrame(header, fg_color="transparent")
    titles.grid(row=0, column=0, sticky="w")
    ctk.CTkLabel(titles, text="Hey Slides", font=font(26, "bold"),
                 text_color=t["ink"]).pack(anchor="w")
    ctk.CTkLabel(titles, text="Voice Slide Control  ·  kendali slide lewat suara, pengenalan lokal dengan Vosk",
                 font=font(13), text_color=t["muted"]).pack(anchor="w")

    mic = _card(header, radius=12)
    mic.grid(row=0, column=1, sticky="e")
    ui.listen_badge = ctk.CTkLabel(mic, text="●  Mikrofon nonaktif", font=font(13, "bold"),
                                   text_color=t["idle"], anchor="w")
    ui.listen_badge.grid(row=0, column=0, sticky="ew", padx=14, pady=(8, 2))
    ui.mic_meter = ctk.CTkProgressBar(mic, width=190, height=8, corner_radius=1,
                                      progress_color=t["accent"], fg_color=t["line"])
    ui.mic_meter.set(0)
    ui.mic_meter.grid(row=1, column=0, sticky="ew", padx=14)
    ctk.CTkLabel(mic, textvariable=ui.audio_quality, font=font(11), text_color=t["muted"],
                 anchor="w").grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 6))

    # ---- toolbar --------------------------------------------------------------
    toolbar = ctk.CTkFrame(outer, fg_color="transparent")
    toolbar.grid(row=1, column=0, sticky="ew", padx=pad, pady=(12, 0))
    ui.start_button = ctk.CTkButton(toolbar, text="Mulai mendengarkan", command=ui.start, height=38,
                                    corner_radius=10, font=font(14, "bold"), fg_color=t["accent"],
                                    hover_color=t["accent_hover"], text_color_disabled="#cfe9e5")
    ui.start_button.pack(side="left")
    ui.stop_button = _neutral_button(toolbar, text="Stop", command=ui.stop, state="disabled",
                                     width=80, height=38)
    ui.stop_button.pack(side="left", padx=(8, 22))
    ctk.CTkLabel(toolbar, text="Target", font=font(13), text_color=t["muted"]).pack(side="left", padx=(0, 8))
    ui.target_box = ctk.CTkSegmentedButton(
        toolbar, values=["Demo slides", "PowerPoint"], variable=ui.target,
        command=lambda value: ui.change_target(), height=34, font=font(13),
        fg_color=t["line"], selected_color="#b6e2dc", selected_hover_color="#a3d9d1",
        unselected_color=t["card"], unselected_hover_color=t["soft"], text_color=t["ink"])
    ui.target_box.pack(side="left")
    # Only shown for the PowerPoint target by show_slide().
    ui.connect_button = ctk.CTkButton(toolbar, text="Hubungkan PowerPoint", command=ui.connect_powerpoint,
                                      height=34, corner_radius=10, font=font(13), fg_color="transparent",
                                      border_width=2, border_color=t["accent"], text_color=t["accent"],
                                      hover_color=t["soft"])
    ui.settings_button = _neutral_button(toolbar, text="Pengaturan", command=ui.show_settings, width=120)
    ui.settings_button.pack(side="right")

    ui.status_label = ctk.CTkLabel(outer, textvariable=ui.status, font=font(13), text_color=t["accent"],
                                   anchor="w", justify="left")
    ui.status_label.grid(row=2, column=0, sticky="ew", padx=pad, pady=(6, 6))
    _wrap_on_resize(outer, [ui.status_label], 2 * pad + 10)

    # ---- body -----------------------------------------------------------------
    body = ctk.CTkFrame(outer, fg_color="transparent")
    body.grid(row=3, column=0, sticky="nsew", padx=pad)
    body.grid_columnconfigure(0, weight=3, uniform="body")
    body.grid_columnconfigure(1, weight=2, uniform="body")
    body.grid_rowconfigure(0, weight=1)
    left = ctk.CTkFrame(body, fg_color="transparent")
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
    left.grid_columnconfigure(0, weight=1)
    left.grid_rowconfigure(0, weight=1)
    right = ctk.CTkFrame(body, fg_color="transparent")
    right.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
    right.grid_columnconfigure(0, weight=1)
    right.grid_rowconfigure(0, weight=1)

    # Slide preview: the thing the audience cares about, so it gets the most space.
    preview = _card(left, t["slide"], radius=16)
    preview.grid(row=0, column=0, sticky="nsew")
    preview.grid_columnconfigure(0, weight=1)
    preview.grid_rowconfigure(2, weight=1)
    ui.preview_caption = ctk.CTkLabel(preview, text="", font=font(11, "bold"),
                                      text_color=t["slide_caption"], anchor="w")
    ui.preview_caption.grid(row=0, column=0, sticky="w", padx=(22, 0), pady=(14, 0))
    ui.slide_kicker = ctk.CTkLabel(preview, text="", font=font(11), text_color=t["slide_kicker"], anchor="e")
    ui.slide_kicker.grid(row=0, column=1, sticky="e", padx=(0, 22), pady=(14, 0))
    ui.slide_title = ctk.CTkLabel(preview, text="", font=font(28, "bold"), text_color="white",
                                  anchor="w", justify="left")
    ui.slide_title.grid(row=1, column=0, columnspan=2, sticky="ew", padx=22, pady=(6, 2))
    ui.slide_body = ctk.CTkLabel(preview, text="", font=font(14), text_color=t["slide_body"],
                                 anchor="nw", justify="left")
    ui.slide_body.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=22)
    nav = ctk.CTkFrame(preview, fg_color="transparent")
    nav.grid(row=3, column=0, columnspan=2, sticky="ew", padx=18, pady=(4, 14))
    nav_style = dict(width=110, height=34, corner_radius=10, font=font(13), fg_color=t["slide_soft"],
                     hover_color=t["slide_soft_hover"], text_color="white")
    ui.previous_button = ctk.CTkButton(nav, text="‹  Previous", command=lambda: ui.manual_action("previous"),
                                       **nav_style)
    ui.previous_button.pack(side="left")
    ctk.CTkLabel(nav, textvariable=ui.slide_number, font=font(17, "bold"),
                 text_color="white").pack(side="left", expand=True)
    ui.next_button = ctk.CTkButton(nav, text="Next  ›", command=lambda: ui.manual_action("next"), **nav_style)
    ui.next_button.pack(side="right")
    _wrap_on_resize(preview, [ui.slide_title, ui.slide_body], 50)

    # Last command banner: large, so the result of a voice command is readable from afar.
    ui.command_panel = _card(left, t["soft"])
    ui.command_panel.grid(row=1, column=0, sticky="ew", pady=(12, 0))
    ui.command_panel.grid_columnconfigure(0, weight=1)
    ui.command_caption = ctk.CTkLabel(ui.command_panel, text=COMMAND_STYLES["info"][2], font=font(11, "bold"),
                                      text_color=t["accent"], anchor="w")
    ui.command_caption.grid(row=0, column=0, sticky="ew", padx=18, pady=(10, 0))
    ui.command_label = ctk.CTkLabel(ui.command_panel, textvariable=ui.command_status, font=font(18, "bold"),
                                    text_color=t["ink"], anchor="w", justify="left")
    ui.command_label.grid(row=1, column=0, sticky="ew", padx=18)
    ui.partial_label = ctk.CTkLabel(ui.command_panel, textvariable=ui.partial, font=font(13, slant="italic"),
                                    text_color=t["muted"], anchor="w", justify="left")
    ui.partial_label.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 10))
    _wrap_on_resize(ui.command_panel, [ui.command_label, ui.partial_label], 40)

    # Transcript of both decoders.
    ui.pretrained_panel = _card(right)
    ui.pretrained_panel.grid(row=0, column=0, sticky="nsew")
    ui.pretrained_panel.grid_columnconfigure(0, weight=1)
    ui.pretrained_panel.grid_rowconfigure(1, weight=1)
    head = ctk.CTkFrame(ui.pretrained_panel, fg_color="transparent")
    head.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 0))
    head.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(head, text="01  Transkrip pretrained", font=font(15, "bold"),
                 text_color=t["ink"], anchor="w").grid(row=0, column=0, sticky="w")
    ctk.CTkLabel(head, textvariable=ui.model_profile, font=font(11), text_color=t["muted"],
                 fg_color=t["neutral"], corner_radius=8, height=22).grid(row=0, column=1, sticky="e")
    ui.transcript = ctk.CTkTextbox(ui.pretrained_panel, wrap="word", height=60, corner_radius=10,
                                   fg_color=t["field"], text_color=t["ink"], font=font(13),
                                   border_width=0, activate_scrollbars=True)
    ui.transcript.grid(row=1, column=0, sticky="nsew", padx=14, pady=(8, 4))
    ui.transcript.tag_config("mic", foreground=t["idle"])
    ui.transcript.tag_config("cmd", foreground=t["accent"])
    ui.transcript.tag_config("test", foreground=t["warn"])
    ui.transcript.configure(state="disabled")
    ui.transcript.bind("<Configure>", lambda event: ui.transcript.see("end-2c"))
    legend = ui.legend_label = ctk.CTkLabel(
        ui.pretrained_panel, font=font(11), text_color=t["muted"], anchor="w", justify="left",
        text="UCAPAN = semua yang didengar (MIC)  ·  PERINTAH = hasil decoder perintah (COMMAND ASR)")
    legend.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 10))
    _wrap_on_resize(ui.pretrained_panel, [legend], 32)

    history = _card(right)
    history.grid(row=1, column=0, sticky="ew", pady=(12, 0))
    ctk.CTkLabel(history, text="Riwayat aksi", font=font(15, "bold"), text_color=t["ink"],
                 anchor="w").pack(fill="x", padx=16, pady=(10, 0))
    ui.actions = ActionLog(history)
    ui.actions.pack(fill="both", expand=True, padx=10, pady=(0, 8))

    # ---- MFCC strip -----------------------------------------------------------
    ui.mfcc_panel = _card(outer)
    ui.mfcc_panel.grid(row=4, column=0, sticky="ew", padx=pad, pady=(12, 14))
    ui.mfcc_panel.grid_columnconfigure(1, weight=1)
    info = ctk.CTkFrame(ui.mfcc_panel, fg_color="transparent", width=340)
    info.grid(row=0, column=0, sticky="nsw", padx=(16, 12), pady=10)
    title_row = ctk.CTkFrame(info, fg_color="transparent")
    title_row.pack(anchor="w")
    ctk.CTkLabel(title_row, text="02  MFCC manual", font=font(15, "bold"),
                 text_color=t["ink"]).pack(side="left")
    ctk.CTkLabel(title_row, text="  NUMPY · TERPISAH DARI INPUT VOSK", font=font(11, "bold"),
                 text_color=t["accent"]).pack(side="left")
    ui.mfcc_explanation = ctk.CTkLabel(info, text="Belum ada model pengenal. Tidak menghasilkan teks atau aksi.",
                                       font=font(12), text_color=t["muted"], anchor="w", justify="left",
                                       wraplength=330)
    ui.mfcc_explanation.pack(anchor="w", fill="x")
    ui.feature_status_label = ctk.CTkLabel(info, textvariable=ui.feature_status, font=font(12),
                                           text_color=t["ink"], anchor="w", justify="left", wraplength=330)
    ui.feature_status_label.pack(anchor="w", fill="x")
    ui.feature_values_label = ctk.CTkLabel(info, textvariable=ui.feature_values, font=font(12, family="Consolas"),
                                           text_color=t["muted"], anchor="w", justify="left", wraplength=330)
    ui.feature_values_label.pack(anchor="w", fill="x")
    ui.heatmap = tk.Canvas(ui.mfcc_panel, height=72, bg=t["slide"], highlightthickness=0)
    ui.heatmap.grid(row=0, column=1, sticky="nsew", padx=(0, 16), pady=12)
    ui.heatmap.bind("<Configure>", lambda event: ui.redraw_heatmap())

    build_settings(ui)


def build_settings(ui):
    t = THEME
    dialog = ctk.CTkToplevel(ui.root, fg_color=t["bg"])
    dialog.withdraw()
    dialog.title("Pengaturan dan diagnostik")
    dialog.geometry("580x620")
    dialog.minsize(540, 580)
    dialog.transient(ui.root)
    dialog.protocol("WM_DELETE_WINDOW", ui.hide_settings)
    dialog.bind("<Escape>", lambda event: ui.hide_settings())
    ui.settings_dialog = dialog
    tabs = ctk.CTkTabview(dialog, fg_color=t["card"], corner_radius=14,
                          segmented_button_fg_color=t["line"], segmented_button_selected_color="#b6e2dc",
                          segmented_button_selected_hover_color="#a3d9d1",
                          segmented_button_unselected_color=t["card"],
                          segmented_button_unselected_hover_color=t["soft"], text_color=t["ink"])
    tabs.pack(fill="both", expand=True, padx=14, pady=(8, 8))
    ui.settings_tabs = tabs
    setup = tabs.add("Pengaturan")
    diagnostics = tabs.add("Diagnostik / tes teks")

    def caption(parent, text):
        ctk.CTkLabel(parent, text=text, font=font(13, "bold"), text_color=t["ink"],
                     anchor="w").pack(fill="x", padx=8, pady=(12, 4))

    def note(parent, text=None, textvariable=None, pady=(4, 0)):
        label = ctk.CTkLabel(parent, text=text or "", textvariable=textvariable, font=font(12),
                             text_color=t["muted"], anchor="w", justify="left", wraplength=480)
        label.pack(fill="x", padx=8, pady=pady)
        return label

    caption(setup, "Mikrofon")
    inputs = ctk.CTkFrame(setup, fg_color="transparent")
    inputs.pack(fill="x", padx=8)
    ui.device_box = _option_menu(inputs, ui.device, list(ui.devices), width=380)
    ui.device_box.pack(side="left", fill="x", expand=True)
    ui.refresh_button = _neutral_button(inputs, text="Refresh", command=ui.refresh_devices, width=90, height=34)
    ui.refresh_button.pack(side="right", padx=(8, 0))
    caption(setup, "Model pretrained")
    ui.model_box = _option_menu(setup, ui.model_profile,
                                [item["label"] for item in config.MODEL_PROFILES.values()])
    ui.model_box.pack(fill="x", padx=8)
    caption(setup, "Mode perintah")
    ui.mode_box = _option_menu(setup, ui.command_mode, list(config.COMMAND_MODES.values()),
                               command=lambda value: ui.change_command_mode())
    ui.mode_box.pack(fill="x", padx=8)
    caption(setup, "Jeda akhir perintah")
    ui.endpoint_box = _option_menu(setup, ui.endpoint_choice, list(config.ENDPOINT_SILENCE_OPTIONS.values()))
    ui.endpoint_box.pack(fill="x", padx=8)
    note(setup, "Lama hening sebelum perintah dijalankan. Lebih pendek = lebih cepat, tetapi"
                " perintah panjang bisa terpotong.", pady=(2, 0))
    check_style = dict(font=font(13), text_color=t["ink"], fg_color=t["accent"], hover_color=t["accent_hover"],
                       border_color=t["idle"], checkbox_width=20, checkbox_height=20, corner_radius=5)
    ui.assist_check = ctk.CTkCheckBox(setup, text="Command assist (disarankan untuk demo)",
                                      variable=ui.command_assist, **check_style)
    ui.assist_check.pack(anchor="w", padx=8, pady=(16, 8))
    ui.record_check = ctk.CTkCheckBox(setup, text="Rekam input untuk evaluasi (WAV lokal)",
                                      variable=ui.record_audio, **check_style)
    ui.record_check.pack(anchor="w", padx=8)
    ui.play_button = _neutral_button(setup, text="Putar rekaman terakhir", command=ui.play_recording,
                                     state="disabled", width=190, height=34)
    ui.play_button.pack(anchor="w", padx=8, pady=(14, 6))
    note(setup, "Default demo: Light English + Direct commands + Command assist.\n"
                "Pengaturan audio dikunci selama sesi. Rekaman mati secara default.", pady=(8, 0))

    caption(diagnostics, "Latensi suara")
    ctk.CTkLabel(diagnostics, textvariable=ui.latency, font=font(13, "bold"), text_color=t["ink"],
                 anchor="w", justify="left", wraplength=480).pack(fill="x", padx=8)
    note(diagnostics, "Diukur dari akhir kata terakhir (timestamp Vosk). L1 = teks tampil, L2 = slide"
                      " berpindah. Semua sampel tersimpan di logs\\session-*.jsonl; ringkas dengan"
                      " python -m scripts.latency_report.", pady=(4, 6))
    note(diagnostics, textvariable=ui.timing, pady=(0, 10))
    caption(diagnostics, "Tes parser tanpa pengenalan suara")
    note(diagnostics, "Tes ini melewati ASR dan dapat menggerakkan target slide.\n"
                      "Hasilnya bukan bukti keberhasilan pengenalan suara.", pady=(0, 8))
    ui.test_input = ctk.CTkEntry(diagnostics, font=font(13), height=34, corner_radius=8,
                                 fg_color=t["field"], border_color=t["line"], text_color=t["ink"])
    ui.test_input.insert(0, "Next slide" if config.DEFAULT_COMMAND_MODE == "direct" else "Hey Slides, next slide")
    ui.test_input.pack(fill="x", padx=8)
    ui.test_input.bind("<Return>", lambda event: ui.test_phrase())
    ctk.CTkButton(diagnostics, text="Jalankan tes teks", command=ui.test_phrase, height=34, corner_radius=10,
                  font=font(13), fg_color=t["accent"], hover_color=t["accent_hover"]).pack(anchor="w", padx=8,
                                                                                          pady=8)
    note(diagnostics, "MFCC manual menghasilkan 156 nilai fitur. Belum ada classifier yang"
                      " menggunakan fitur tersebut untuk menghasilkan kata atau aksi.", pady=(10, 0))
    ui.save_features_button = _neutral_button(diagnostics, text="Simpan fitur terakhir (JSON)",
                                              command=ui.save_features, state="disabled", width=220, height=34)
    ui.save_features_button.pack(anchor="w", padx=8, pady=(8, 0))
    _neutral_button(dialog, text="Tutup pengaturan", command=ui.hide_settings, width=160).pack(pady=(0, 12))

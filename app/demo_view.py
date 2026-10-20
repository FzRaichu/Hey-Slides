"""Presentation-friendly Tk layout; recognition and navigation stay in main/session."""

import tkinter as tk
from tkinter import ttk

from app import config


def build_demo_view(ui, palette):
    bg, card, ink, muted, accent = palette
    root = ui.root
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TButton", font=("Segoe UI", 10), padding=(12, 7))
    style.configure("Accent.TButton", background=accent, foreground="white")
    style.configure("TCombobox", padding=5)

    outer = tk.Frame(root, bg=bg, padx=22, pady=16)
    outer.pack(fill="both", expand=True)
    outer.columnconfigure(0, weight=1)
    outer.rowconfigure(4, weight=1)
    header = tk.Frame(outer, bg=bg)
    header.grid(row=0, column=0, sticky="ew")
    tk.Label(header, text="Voice Slide Control", bg=bg, fg=ink,
             font=("Segoe UI", 23, "bold")).pack(side="left")
    tk.Label(header, text="PROTOTIPE LOKAL", bg=bg, fg=muted,
             font=("Segoe UI", 9, "bold")).pack(side="right")
    tk.Label(outer, text="Satu mikrofon, dua jalur. Kendali slide menggunakan pretrained.",
             bg=bg, fg=muted, font=("Segoe UI", 10), anchor="w").grid(row=1, column=0, sticky="ew", pady=(2, 10))

    toolbar = tk.Frame(outer, bg=bg)
    toolbar.grid(row=2, column=0, sticky="ew")
    ui.start_button = ttk.Button(toolbar, text="Mulai mendengarkan", command=ui.start, style="Accent.TButton")
    ui.start_button.pack(side="left")
    ui.stop_button = ttk.Button(toolbar, text="Stop", command=ui.stop, state="disabled")
    ui.stop_button.pack(side="left", padx=(7, 18))
    tk.Label(toolbar, text="Target", bg=bg, fg=muted, font=("Segoe UI", 10)).pack(side="left", padx=(0, 7))
    ui.target_box = ttk.Combobox(toolbar, textvariable=ui.target, state="readonly",
                                values=("Demo slides", "PowerPoint"), width=14)
    ui.target_box.pack(side="left")
    ui.target_box.bind("<<ComboboxSelected>>", lambda event: ui.change_target())
    ui.connect_button = ttk.Button(toolbar, text="Hubungkan PowerPoint", command=ui.connect_powerpoint)
    # Only shown for the PowerPoint target by show_slide().
    ui.settings_button = ttk.Button(toolbar, text="Pengaturan", command=ui.show_settings)
    ui.settings_button.pack(side="right")

    status_row = tk.Frame(outer, bg=bg)
    status_row.grid(row=3, column=0, sticky="ew", pady=(8, 8))
    tk.Label(status_row, textvariable=ui.status, anchor="w", bg=bg, fg=accent,
             font=("Segoe UI", 10), wraplength=650, justify="left").pack(side="left", fill="x", expand=True)
    tk.Label(status_row, textvariable=ui.audio_quality, bg=bg, fg=muted,
             font=("Segoe UI", 9)).pack(side="right")

    body = tk.Frame(outer, bg=bg)
    body.grid(row=4, column=0, sticky="nsew")
    body.columnconfigure(0, weight=1, uniform="outputs")
    body.columnconfigure(1, weight=1, uniform="outputs")
    body.rowconfigure(0, weight=1)
    ui.pretrained_panel = tk.Frame(body, bg=card, padx=18, pady=14)
    ui.pretrained_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
    ui.mfcc_panel = tk.Frame(body, bg=card, padx=18, pady=14)
    ui.mfcc_panel.grid(row=0, column=1, sticky="nsew", padx=(7, 0))

    left, right = ui.pretrained_panel, ui.mfcc_panel
    left.columnconfigure(0, weight=1)
    left.rowconfigure(3, weight=1, minsize=50)
    tk.Label(left, text="01  Pengenalan pretrained", bg=card, fg=ink,
             font=("Segoe UI", 15, "bold")).grid(row=0, column=0, sticky="w")
    tk.Label(left, textvariable=ui.model_profile, bg=card, fg=muted,
             font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=(2, 4))
    ui.partial_label = tk.Label(left, textvariable=ui.partial, bg=card, fg=accent,
                               font=("Segoe UI", 10, "italic"), height=1, anchor="w", justify="left", wraplength=440)
    ui.partial_label.grid(row=2, column=0, sticky="ew", pady=(8, 6))
    transcript_frame = tk.Frame(left, bg=card)
    transcript_frame.grid(row=3, column=0, sticky="nsew")
    ui.transcript = tk.Text(transcript_frame, height=4, width=30, wrap="word", state="disabled",
                            bg="#f4f7f8", fg=ink, relief="flat", font=("Segoe UI", 11), padx=10, pady=8)
    scroll = ttk.Scrollbar(transcript_frame, command=ui.transcript.yview)
    ui.transcript.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")
    ui.transcript.pack(side="left", fill="both", expand=True)
    ui.transcript.bind("<Configure>", lambda event: ui.transcript.see("end-2c"))
    tk.Label(left, text="MIC = ucapan umum  |  COMMAND ASR = kandidat perintah", bg=card,
             fg=muted, font=("Segoe UI", 8), anchor="w").grid(row=4, column=0, sticky="ew", pady=(5, 4))
    ui.command_label = tk.Label(left, textvariable=ui.command_status, bg=card, fg=accent,
                                font=("Segoe UI", 10), height=2, anchor="w", justify="left", wraplength=440)
    ui.command_label.grid(row=5, column=0, sticky="ew")
    left.bind("<Configure>", lambda event: [label.configure(wraplength=max(260, event.width - 36))
                                           for label in (ui.partial_label, ui.command_label)])

    right.columnconfigure(0, weight=1)
    right.rowconfigure(3, weight=1, minsize=36)
    tk.Label(right, text="02  MFCC manual", bg=card, fg=ink,
             font=("Segoe UI", 15, "bold")).grid(row=0, column=0, sticky="w")
    tk.Label(right, text="FITUR NUMPY / TERPISAH DARI INPUT VOSK", bg=card, fg=accent,
             font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=(2, 4))
    ui.mfcc_explanation = tk.Label(right,
        text="Belum ada model pengenal. Tidak menghasilkan teks atau aksi.",
        bg=card, fg=muted, font=("Segoe UI", 9), anchor="w", justify="left", wraplength=440)
    ui.mfcc_explanation.grid(row=2, column=0, sticky="ew", pady=(4, 6))
    ui.heatmap = tk.Canvas(right, height=64, bg=ink, highlightthickness=0)
    ui.heatmap.grid(row=3, column=0, sticky="nsew")
    ui.heatmap.bind("<Configure>", lambda event: ui.draw_features(ui.last_mfcc) if ui.last_mfcc is not None else None)
    ui.feature_status_label = tk.Label(right, textvariable=ui.feature_status, bg=card, fg=ink, font=("Segoe UI", 9),
                                       anchor="w", justify="left", wraplength=440)
    ui.feature_status_label.grid(row=4, column=0, sticky="ew", pady=(7, 4))
    ui.feature_values_label = tk.Label(right, textvariable=ui.feature_values, bg=card, fg=muted,
                                       font=("Consolas", 10), anchor="nw", justify="left", wraplength=440)
    ui.feature_values_label.grid(row=5, column=0, sticky="ew")
    right.bind("<Configure>", lambda event: [label.configure(wraplength=max(260, event.width - 36))
                                            for label in (ui.mfcc_explanation, ui.feature_status_label, ui.feature_values_label)])

    bottom = tk.Frame(outer, bg=bg)
    bottom.grid(row=5, column=0, sticky="ew", pady=(12, 0))
    bottom.columnconfigure(0, weight=3)
    bottom.columnconfigure(1, weight=2)
    preview = tk.Frame(bottom, bg=ink, padx=16, pady=10, height=180)
    preview.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
    preview.grid_propagate(False)
    preview.columnconfigure(0, weight=1)
    preview.rowconfigure(2, weight=1)
    ui.preview_caption = tk.Label(preview, bg=ink, fg="#6dd8ca", font=("Segoe UI", 8, "bold"), anchor="w")
    ui.preview_caption.grid(row=0, column=0, sticky="ew")
    ui.slide_kicker = tk.Label(preview, bg=ink, fg="#a7bbcf", font=("Segoe UI", 8), width=24, anchor="e")
    ui.slide_kicker.grid(row=0, column=1, sticky="e")
    ui.slide_title = tk.Label(preview, bg=ink, fg="white", font=("Segoe UI", 15, "bold"), anchor="w")
    ui.slide_title.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 2))
    ui.slide_body = tk.Label(preview, bg=ink, fg="#d4e1ec", font=("Segoe UI", 9), anchor="nw", justify="left")
    ui.slide_body.grid(row=2, column=0, columnspan=2, sticky="nsew")
    nav = tk.Frame(preview, bg=ink)
    nav.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))
    ui.previous_button = ttk.Button(nav, text="Previous", command=lambda: ui.manual_action("previous"))
    ui.previous_button.pack(side="left")
    tk.Label(nav, textvariable=ui.slide_number, bg=ink, fg="white", font=("Segoe UI", 11, "bold")).pack(side="left", expand=True)
    ui.next_button = ttk.Button(nav, text="Next", command=lambda: ui.manual_action("next"))
    ui.next_button.pack(side="right")
    preview.bind("<Configure>", lambda event: [label.configure(wraplength=max(260, event.width - 32))
                                              for label in (ui.slide_title, ui.slide_body)])

    history = tk.Frame(bottom, bg=card, padx=14, pady=12)
    history.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
    tk.Label(history, text="Riwayat aksi", bg=card, fg=ink, font=("Segoe UI", 11, "bold")).pack(anchor="w")
    ui.actions = tk.Listbox(history, height=4, width=25, bg=card, fg=ink, relief="flat",
                            font=("Segoe UI", 10), selectborderwidth=0)
    ui.actions.pack(fill="both", expand=True, pady=(6, 0))
    tk.Label(outer, textvariable=ui.demo_hint, bg=bg,
             fg=muted, font=("Segoe UI", 9), anchor="w").grid(row=6, column=0, sticky="ew", pady=(8, 0))
    build_settings(ui, palette)


def build_settings(ui, palette):
    bg, card, ink, muted, accent = palette
    dialog = tk.Toplevel(ui.root)
    dialog.withdraw()
    dialog.title("Pengaturan dan diagnostik")
    dialog.geometry("570x580")
    dialog.minsize(530, 540)
    dialog.transient(ui.root)
    dialog.protocol("WM_DELETE_WINDOW", ui.hide_settings)
    dialog.bind("<Escape>", lambda event: ui.hide_settings())
    ui.settings_dialog = dialog
    tabs = ttk.Notebook(dialog)
    tabs.pack(fill="both", expand=True, padx=14, pady=14)
    ui.settings_tabs = tabs
    setup, diagnostics = ttk.Frame(tabs, padding=16), ttk.Frame(tabs, padding=16)
    tabs.add(setup, text="Pengaturan")
    tabs.add(diagnostics, text="Diagnostik / tes teks")

    def caption(parent, text):
        ttk.Label(parent, text=text, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 4))

    caption(setup, "Mikrofon")
    inputs = ttk.Frame(setup)
    inputs.pack(fill="x")
    ui.device_box = ttk.Combobox(inputs, textvariable=ui.device, state="readonly", width=34)
    ui.device_box.pack(side="left", fill="x", expand=True)
    ui.refresh_button = ttk.Button(inputs, text="Refresh", command=ui.refresh_devices)
    ui.refresh_button.pack(side="right", padx=(5, 0))
    caption(setup, "Model pretrained")
    ui.model_box = ttk.Combobox(setup, textvariable=ui.model_profile, state="readonly", width=40,
                               values=[item["label"] for item in config.MODEL_PROFILES.values()])
    ui.model_box.pack(fill="x")
    caption(setup, "Mode perintah")
    ui.mode_box = ttk.Combobox(setup, textvariable=ui.command_mode, state="readonly", width=40,
                              values=list(config.COMMAND_MODES.values()))
    ui.mode_box.pack(fill="x")
    ui.mode_box.bind("<<ComboboxSelected>>", lambda event: ui.change_command_mode())
    ui.assist_check = ttk.Checkbutton(setup, text="Command assist (disarankan untuk demo)", variable=ui.command_assist)
    ui.assist_check.pack(anchor="w", pady=(12, 6))
    ui.record_check = ttk.Checkbutton(setup, text="Rekam input untuk evaluasi (WAV lokal)", variable=ui.record_audio)
    ui.record_check.pack(anchor="w")
    ui.play_button = ttk.Button(setup, text="Putar rekaman terakhir", command=ui.play_recording, state="disabled")
    ui.play_button.pack(anchor="w", pady=(10, 6))
    ttk.Label(setup, text="Default demo: Light English + Direct commands + Command assist.\n"
              "Pengaturan audio dikunci selama sesi. Rekaman mati secara default.",
              wraplength=480, justify="left").pack(fill="x", pady=(8, 0))

    caption(diagnostics, "Pengukuran pemrosesan")
    ttk.Label(diagnostics, textvariable=ui.timing, wraplength=470, justify="left").pack(fill="x")
    ttk.Label(diagnostics, text="Angka ini bukan latensi suara-ke-slide. Target 200 ms belum tervalidasi.",
              wraplength=470, justify="left").pack(fill="x", pady=(8, 18))
    caption(diagnostics, "Tes parser tanpa pengenalan suara")
    ttk.Label(diagnostics, text="Tes ini melewati ASR dan dapat menggerakkan target slide.\n"
              "Hasilnya bukan bukti keberhasilan pengenalan suara.", wraplength=470, justify="left").pack(fill="x", pady=(0, 8))
    ui.test_input = ttk.Entry(diagnostics, font=("Segoe UI", 11))
    ui.test_input.insert(0, "Next slide" if config.DEFAULT_COMMAND_MODE == "direct" else "Hey Slides, next slide")
    ui.test_input.pack(fill="x")
    ui.test_input.bind("<Return>", lambda event: ui.test_phrase())
    ttk.Button(diagnostics, text="Jalankan tes teks", command=ui.test_phrase).pack(anchor="w", pady=8)
    ttk.Label(diagnostics, text="MFCC manual menghasilkan 156 nilai fitur. Belum ada classifier yang"
              " menggunakan fitur tersebut untuk menghasilkan kata atau aksi.",
              wraplength=470, justify="left").pack(fill="x", pady=(14, 0))
    ui.save_features_button = ttk.Button(diagnostics, text="Simpan fitur terakhir (JSON)",
                                          command=ui.save_features, state="disabled")
    ui.save_features_button.pack(anchor="w", pady=(8, 0))
    ttk.Button(dialog, text="Tutup pengaturan", command=ui.hide_settings).pack(pady=(0, 12))

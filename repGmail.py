import os
import sys
import json
import time
import threading
import textwrap
import random
import smtplib
import re
import shutil
from email.mime.text import MIMEText
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
# KONFIGURASI AWAL
# ═══════════════════════════════════════════════════════════════
CONFIG_DIR = os.path.expanduser("~/.gmail_reporter")
CONFIG_FILE = os.path.join(CONFIG_DIR, "senders.json")
LOG_FILE = os.path.join(CONFIG_DIR, "report.log")

# Template persistent storage — dual location
TEMPLATE_FILE_INTERNAL = os.path.join(CONFIG_DIR, "templates.json")
# External storage: try Termux shared first, then sdcard fallback
_TEMPLATE_EXTERNAL_CANDIDATES = [
    os.path.expanduser("~/storage/shared/DLSpotify/templates.json"),
    "/sdcard/DLSpotify/templates.json",
    os.path.expanduser("~/storage/downloads/DLSpotify/templates.json"),
]

# Find first writable external path
TEMPLATE_FILE_EXTERNAL = None
for cand in _TEMPLATE_EXTERNAL_CANDIDATES:
    try:
        os.makedirs(os.path.dirname(cand), exist_ok=True)
        # Test write
        with open(cand, 'a') as f:
            pass
        TEMPLATE_FILE_EXTERNAL = cand
        break
    except:
        continue

# Fallback: if none writable, use home dir
if TEMPLATE_FILE_EXTERNAL is None:
    TEMPLATE_FILE_EXTERNAL = os.path.expanduser("~/DLSpotify_templates_backup.json")
    os.makedirs(os.path.dirname(TEMPLATE_FILE_EXTERNAL) if os.path.dirname(TEMPLATE_FILE_EXTERNAL) else ".", exist_ok=True)

os.makedirs(CONFIG_DIR, exist_ok=True)

MAX_TEMPLATES = 25

# ═══════════════════════════════════════════════════════════════
# WARNA ANSI — MINIMALIST DARK
# ═══════════════════════════════════════════════════════════════
C = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "white": "\033[97m",
    "gray": "\033[90m",
    "darkgray": "\033[38;5;240m",
    "orange": "\033[38;5;208m",
    "link": "\033[38;5;75m",
}

# ═══════════════════════════════════════════════════════════════
# UTILITAS UI
# ═══════════════════════════════════════════════════════════════

def clear():
    os.system('clear')

def line(char="─", width=60):
    return char * width

def header(text, width=60):
    pad = (width - len(text) - 4) // 2
    return "│" + " " * pad + C["bold"] + text + C["reset"] + " " * (width - len(text) - 4 - pad) + "│"

def box_top(width=60):
    return "╭" + line("─", width - 2) + "╮"

def box_bottom(width=60):
    return "╰" + line("─", width - 2) + "╯"

def box_row(text, width=60, align="left"):
    if align == "center":
        pad = (width - 4 - len(text)) // 2
        return "│ " + " " * pad + text + " " * (width - 4 - pad - len(text)) + " │"
    return "│ " + text.ljust(width - 4) + " │"

def print_box(lines, width=60):
    print(box_top(width))
    for ln in lines:
        if isinstance(ln, tuple):
            text, align = ln
            print(box_row(text, width, align))
        else:
            print(box_row(ln, width))
    print(box_bottom(width))

# ═══════════════════════════════════════════════════════════════
# BANNER — ASCII PERTAHANKAN
# ═══════════════════════════════════════════════════════════════


def print_banner():
    clear()
    print(f"{C['gray']}{C['bold']}")
    print(f"""
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠖⠃⠀⠀⠀⡁⠀⠀⠀⠀⠀⠐⠆⠀⠀⠀⠀⠀⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡠⢔⡤⠊⠁⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠀⠀⠀⠁⠀⠀⠘⠁⢀⠀⠀⠀⠀⢈⠓⠂⠠⡄⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣶⠿⠞⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠒⠁⠀⠠⡚⠁⢀⣙⣀⣈⡩⠬⢁⠀⢑⠶⠤⡆⠤⡀⠀⠀⠀⠀⠀⠀⢀⠴⢲⣋⣽⣷⠟⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠀⢠⠀⠀⣶⠃⠗⣡⣶⣮⣿⡿⠿⠿⢿⣿⣷⣶⣤⣤⠤⠴⠦⠬⣤⣤⠄⣉⠉⠝⢲⣿⡷⠻⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠁⡀⡸⠁⣰⣿⡿⠛⠋⣁⡀⠤⠤⢄⡀⠈⠛⢯⣿⣟⣾⣶⣶⣮⣭⣵⣾⣿⣟⠿⠉⢨⠖⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⠀⢠⠳⡧⣻⡿⠋⢀⠒⠉⠀⠀⠀⠀⠀⠀⠉⠢⠀⠀⠙⠛⣻⣿⣿⣿⢿⣿⣿⠟⡱⠖⠊⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⢠⣧⠓⣾⣿⠁⠀⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⢦⣠⣾⣿⠿⣿⣿⣿⡿⣫⠏⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⠀⠂⢃⣸⣿⠇⢠⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣴⣿⠟⢿⠁⠸⡿⣿⣯⡶⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⢘⡄⠘⣿⣿⠀⠸⡀⠀⠀⠀⠀⠀⢀⣀⣴⣾⣿⡿⡟⡋⠐⡇⠀⢸⣿⣿⠃⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢡⠘⢰⣿⡿⡆⠀⣇⠀⣀⣠⣤⣶⣿⢷⢟⠻⠀⠈⠀⠀⠀⡇⠀⣼⣿⣿⠂⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠔⢀⡴⢯⣾⠟⡏⢀⣠⣿⣿⣿⣟⢟⡋⠅⠘⠉⠀⠀⠀⠀⢀⠀⠁⢠⣿⣟⠃⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⠞⣻⣷⡿⢙⣩⣶⡿⠿⠛⠉⠑⢡⡁⠀⠀⠀⠀⠀⠀⢀⠔⠁⠀⣰⣿⣿⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣡⣾⣥⣾⢫⡦⠾⠛⠙⠉⠀⠀⢀⣀⠀⠈⠙⠓⠦⠤⠤⠀⠘⠁⢀⡤⣾⡿⠏⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠔⣴⣾⣿⣿⢟⢝⠢⠃⢀⣤⢴⣾⣮⣷⣶⢿⣶⡤⣐⡀⠀⣠⣤⢶⣪⣿⣿⡿⠟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⡀⣦⣾⡿⡛⠵⠺⢈⡠⠶⠿⠥⠥⡭⠉⠉⢱⡛⠻⠿⣿⣿⣿⣿⣿⠿⠿⠿⠟⠭⠛⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⢀⢴⠕⣋⠝⠕⠐⠀⠔⠉⠀⠀⠀⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠁⠉⠁⠁⠁⠁⠈⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⢀⣠⠁⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    """)
    print(f"{C['reset']}")
    print(f"{C['bold']}{C['white']}{' ' * 9}༗ Owners @rizkitahalu |{C['reset']} {C['link']}rizkitahalu.t.me{C['reset']}")
    print(f"{C['darkgray']}{' ' * 8}{line('─', 43)}{C['reset']}")
    print(f"{C['bold']}{C['white']}{' ' * 23}ᯤ Version  2.9{C['reset']}")
    print(f"{C['darkgray']}{' ' * 22}{line('─', 16)}{C['reset']}\n")

    disclaimer = (
        "Script ini dibuat untuk tujuan edukasi dan otomatisasi pelaporan yang sah. "
        "Pengguna bertanggung jawab atas setiap penggunaan script dan wajib mematuhi "
        "hukum serta ketentuan layanan yang berlaku. Dilarang menggunakan script untuk "
        "spam, konten ilegal, penipuan, atau aktivitas yang merugikan pihak lain. "
        "Gunakan teknologi secara bijak dan bertanggung jawab."
    )
    print(f"{C['gray']}[{C['bold']}i{C['reset']}{C['gray']}] {C['bold']}PERINGATAN PENGGUNAAN & TANGGUNG JAWAB{C['reset']}")
    print(f"{C['darkgray']}" + textwrap.fill(disclaimer.strip(), width=70) + f"{C['reset']}")
    print()

# ═══════════════════════════════════════════════════════════════
# VALIDASI INPUT
# ═══════════════════════════════════════════════════════════════

def validate_yes_no(prompt):
    """Validasi input Y/N, tolak selain Y/N"""
    while True:
        val = input(f"{prompt} ").strip().upper()
        if val in ("Y", "N"):
            return val
        print(f"{C['red']}  ✗ Input tidak valid. Masukkan Y atau N.{C['reset']}")

def validate_menu_choice(prompt, valid_choices):
    """Validasi pilihan menu"""
    while True:
        val = input(f"{prompt} ").strip().upper()

        if val == "X":
            return "X"

        if val in valid_choices:
            return val

        print(f"{C['red']}  ✗ Pilihan tidak valid. Coba lagi.{C['reset']}")

def validate_email(email, require_gmail=False):
    """Validasi format email"""
    pattern = r"^[a-zA-Z0-9._%+-]+@gmail\.com$" if require_gmail else r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None

def parse_multi_email(text):
    """
    Parse input berisi satu atau banyak email, dipisah koma atau '|'.
    Return (True, [list_email]) kalau semua valid.
    Return (False, email_yang_salah) kalau ada satu yang formatnya invalid.
    """
    raw = re.split(r"[,|]", text)
    targets = [e.strip() for e in raw if e.strip()]
    if not targets:
        return False, "(kosong)"
    for e in targets:
        if not validate_email(e):
            return False, e
    return True, targets

def validate_positive_int(val, max_val=None):
    """Validasi bilangan bulat positif"""
    try:
        n = int(val)
        if n <= 0:
            return False, None
        if max_val is not None and n > max_val:
            return False, None
        return True, n
    except:
        return False, None

def validate_non_empty(text, max_len=500):
    """Validasi teks tidak kosong dan tidak melebihi batas"""
    if not text or not text.strip():
        return False
    if len(text) > max_len:
        return False
    # Security: block suspicious patterns
    suspicious = re.compile(r"[<>'\"\\{}\[\]|^`]|javascript:|data:|vbscript:|on\w+\s*=")
    if suspicious.search(text):
        return False
    return True

def read_multiline_text():
    """
    Baca teks multi-baris tanpa batasan konten apa pun.

    Diakhiri dengan EOF (Ctrl+D di Linux/Termux/Mac, Ctrl+Z lalu Enter
    di Windows) — BUKAN kata kunci di dalam teks. Karena terminatornya
    sinyal stream, bukan teks, maka baris kosong, kata "selesai", huruf
    "x" sendirian, atau kombinasi apa pun di TENGAH teks tetap tersimpan
    apa adanya. Tidak ada kata yang "dicadangkan" dan bisa memutus teks
    secara tidak sengaja.

    "X" hanya dianggap perintah batal kalau itu baris PERTAMA yang
    diketik (belum ada konten lain). Setelah user mulai mengetik isi,
    "X" jadi bagian teks biasa seperti karakter lain.

    Return (True, teks) kalau selesai normal (teks bisa None jika kosong).
    Return (False, None) kalau user membatalkan di baris pertama.
    """
    text_lines = []
    while True:
        try:
            line = input("  > ")
        except EOFError:
            print()
            break
        if not text_lines and line.strip().upper() == "X":
            return False, None
        text_lines.append(line)
    result = "\n".join(text_lines).strip()
    return True, (result if result else None)

def sanitize_path(name):
    """Sanitasi nama file/path"""
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', name).strip()

# ═══════════════════════════════════════════════════════════════
# MANAJEMEN SENDER
# ═══════════════════════════════════════════════════════════════

def load_senders():
    if not os.path.exists(CONFIG_FILE):
        return []
    try:
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)
            return data.get('senders', [])
    except:
        return []

def save_senders(senders):
    with open(CONFIG_FILE, 'w') as f:
        json.dump({'senders': senders}, f, indent=2)

def add_sender():
    print_banner()
    print(f"{C['cyan']}  [2] Tambah Sender Baru{C['reset']}\n")
    email = input("  Email Sender (Gmail) : ").strip()
    if email.upper() == "X":
        return
    if not validate_email(email, require_gmail=True):
        print(f"{C['red']}  ✗ Format email tidak valid! Harus @gmail.com{C['reset']}")
        time.sleep(1.5)
        return
    password = input("  App Password (16 karakter) : ").strip().replace(" ", "")
    if password.upper() == "X":
        return
    if len(password) != 16:
        print(f"{C['red']}  ✗ App Password harus 16 karakter!{C['reset']}")
        time.sleep(1.5)
        return
    senders = load_senders()
    for s in senders:
        if s['email'] == email:
            print(f"{C['red']}  ✗ Email sudah terdaftar!{C['reset']}")
            time.sleep(1.5)
            return
    senders.append({'email': email, 'password': password})
    save_senders(senders)
    print(f"{C['green']}  ✓ Sender berhasil ditambahkan.{C['reset']}")
    time.sleep(1.5)

def delete_sender():
    senders = load_senders()
    if not senders:
        print(f"{C['red']}  ✗ Belum ada sender terdaftar.{C['reset']}")
        time.sleep(1.5)
        return
    print_banner()
    print(f"{C['cyan']}  [3] Hapus Sender{C['reset']}\n")
    for i, s in enumerate(senders, 1):
        print(f"  [{i}] {s['email']}")
    print()
    choice = validate_menu_choice("  Pilih nomor :", [str(i) for i in range(1, len(senders)+1)])
    if choice == "X":
        return
    idx = int(choice) - 1
    deleted = senders.pop(idx)
    save_senders(senders)
    print(f"{C['green']}  ✓ Sender {deleted['email']} dihapus.{C['reset']}")
    time.sleep(1.5)

def list_senders():
    senders = load_senders()
    print_banner()
    if not senders:
        print(f"{C['red']}  ✗ Belum ada sender terdaftar.{C['reset']}")
    else:
        print(f"{C['green']}  ◈ Daftar Sender{C['reset']}\n")
        for i, s in enumerate(senders, 1):
            print(f"  [{i}] {s['email']}")
    input(f"\n  {C['darkgray']}[Tekan Enter untuk kembali]{C['reset']}")

# ═══════════════════════════════════════════════════════════════
# CEK LIMIT EMAIL
# ═══════════════════════════════════════════════════════════════

def check_limit(email, password, test_target="test@example.com"):
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(email, password)
        msg = MIMEText("Test email untuk cek limit.")
        msg['Subject'] = "Test Limit"
        msg['From'] = email
        msg['To'] = test_target
        server.sendmail(email, [test_target], msg.as_string())
        server.quit()
        return True, "READY"
    except smtplib.SMTPAuthenticationError:
        return False, "AUTH ERROR"
    except smtplib.SMTPSenderRefused:
        return False, "LIMIT / BLOCKED"
    except Exception as e:
        return False, f"ERROR: {str(e)[:50]}"

def check_limits():
    senders = load_senders()
    if not senders:
        print(f"{C['red']}  ✗ Belum ada sender.{C['reset']}")
        time.sleep(1.5)
        return
    print_banner()
    print(f"{C['cyan']}  [5] Cek Limit Email{C['reset']}\n")
    target = input("  Email tujuan tes : ").strip()
    if target.upper() == "X":
        return
    if not target:
        target = "test@example.com"
        print(f"  {C['yellow']}◈ Menggunakan default test@example.com{C['reset']}")
    for s in senders:
        status, msg = check_limit(s['email'], s['password'], target)
        color = C['green'] if status else C['red']
        print(f"  {color}◈ {s['email']} → {msg}{C['reset']}")
        time.sleep(0.5)
    input(f"\n  {C['darkgray']}[Tekan Enter untuk kembali]{C['reset']}")

# ═══════════════════════════════════════════════════════════════
# REFRESH SCRIPT
# ═══════════════════════════════════════════════════════════════

def refresh_script():#
    os.execv(sys.executable, [sys.executable] + sys.argv)

def auto_refresh():
    file = os.path.abspath(__file__)
    last_modified = os.path.getmtime(file)
    while True:
        time.sleep(1)
        current_modified = os.path.getmtime(file)
        if current_modified != last_modified:
            os.execv(sys.executable, [sys.executable] + sys.argv)

# ═══════════════════════════════════════════════════════════════
# PERSISTENT TEMPLATE STORAGE — DUAL FILE SYSTEM
# ═══════════════════════════════════════════════════════════════

def _ensure_template_dirs():
    """Pastikan direktori template tersedia"""
    os.makedirs(os.path.dirname(TEMPLATE_FILE_INTERNAL), exist_ok=True)
    ext_dir = os.path.dirname(TEMPLATE_FILE_EXTERNAL)
    if ext_dir:
        os.makedirs(ext_dir, exist_ok=True)

def _read_template_file(path):
    """Baca file template, return list atau None jika gagal"""
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and 'templates' in data:
                return data['templates']
            return None
    except:
        return None

def _write_template_file(path, templates):
    """Tulis file template"""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(templates, f, indent=2, ensure_ascii=False)
        return True
    except:
        return False

def _count_valid_templates(templates):
    """Hitung template yang valid"""
    if not isinstance(templates, list):
        return 0
    return sum(1 for t in templates if isinstance(t, dict) and t.get('id') is not None)

def load_templates():
    """
    Load template dari dual storage dengan auto-recovery.
    Kedua file harus 100% identik setelah operasi.
    """
    _ensure_template_dirs()
    internal = _read_template_file(TEMPLATE_FILE_INTERNAL)
    external = _read_template_file(TEMPLATE_FILE_EXTERNAL)

    # Case 1: Kedua file tidak ada → buat baru
    if internal is None and external is None:
        empty = []
        _write_template_file(TEMPLATE_FILE_INTERNAL, empty)
        _write_template_file(TEMPLATE_FILE_EXTERNAL, empty)
        return empty

    # Case 2: Hanya internal tersedia → recovery ke external
    if internal is not None and external is None:
        _write_template_file(TEMPLATE_FILE_EXTERNAL, internal)
        return internal

    # Case 3: Hanya external tersedia → recovery ke internal
    if internal is None and external is not None:
        _write_template_file(TEMPLATE_FILE_INTERNAL, external)
        return external

    # Case 4: Kedua tersedia → validasi & sync
    int_count = _count_valid_templates(internal)
    ext_count = _count_valid_templates(external)

    # Jika identik, return
    if int_count == ext_count and int_count > 0:
        # Cross-check isi
        try:
            if json.dumps(internal, sort_keys=True) == json.dumps(external, sort_keys=True):
                return internal
        except:
            pass

    # Jika berbeda, pilih yang lebih lengkap (lebih banyak template valid)
    if int_count >= ext_count:
        source = internal
    else:
        source = external

    # Sync kedua file agar 100% identik
    _write_template_file(TEMPLATE_FILE_INTERNAL, source)
    _write_template_file(TEMPLATE_FILE_EXTERNAL, source)
    return source

def save_templates(templates):
    """Simpan template ke kedua lokasi, selalu identik"""
    _ensure_template_dirs()
    _write_template_file(TEMPLATE_FILE_INTERNAL, templates)
    _write_template_file(TEMPLATE_FILE_EXTERNAL, templates)

def get_next_template_id(templates):
    """Dapatkan ID berikutnya, auto-increment, tidak reuse ID yang dihapus"""
    if not templates:
        return 1
    max_id = 0
    for t in templates:
        if isinstance(t, dict) and 'id' in t:
            try:
                tid = int(t['id'])
                if tid > max_id:
                    max_id = tid
            except:
                pass
    return max_id + 1

def find_template_by_id(templates, tid):
    """Cari template berdasarkan ID, return (index, template) atau (None, None)"""
    for i, t in enumerate(templates):
        if isinstance(t, dict) and str(t.get('id')) == str(tid):
            return i, t
    return None, None

# ═══════════════════════════════════════════════════════════════
# TEMPLATE MANAGEMENT
# ═══════════════════════════════════════════════════════════════

def print_template_preview(t, title="Preview Template"):
    """Tampilkan preview template dalam box"""
    lines = [
        (title, "center"),
        "",
        f"Nama Template  : {t.get('name', '—')}",
        f"Looping        : {t.get('looping', '—')}",
        f"Email Tujuan   : {t.get('target', '—')}",
        f"Subject        : {t.get('subject', '—')}",
        "",
        "Teks Laporan :",
    ]
    # Split text into lines untuk box
    text = t.get('text', '')
    if text:
        for txt_line in text.split('\n')[:20]:  # max 20 lines in preview
            lines.append(txt_line[:56])
    else:
        lines.append("(kosong)")
    print_box(lines, width=60)

def template_menu():
    """Menu utama Template"""
    while True:
        clear()
        templates = load_templates()
        count = len(templates)

        lines = [
            ("◈ MENU TEMPLATE", "center"),
            "",
            f"Jumlah Template : {count} / {MAX_TEMPLATES}",
            "",
            "[1] Tambah Template",
            "[2] Hapus Template",
            "[3] Edit Template",
            "[4] Daftar Template",
            "",
            "[0] Kembali",
        ]
        print_box(lines, width=60)

        choice = validate_menu_choice("  Pilih :", ["0", "1", "2", "3", "4"])
        if choice == "1":
            add_template()
        elif choice == "2":
            delete_template()
        elif choice == "3":
            edit_template()
        elif choice == "4":
            list_templates()
        elif choice == "0":
            break
        elif choice == "X":
            return

def add_template():
    """Tambah template baru"""
    templates = load_templates()
    if len(templates) >= MAX_TEMPLATES:
        clear()
        print(f"{C['red']}  ✗ Batas maksimum {MAX_TEMPLATES} template telah tercapai.{C['reset']}")
        print(f"  {C['darkgray']}Hapus template lama untuk menambahkan yang baru.{C['reset']}")
        time.sleep(2.5)
        return

    clear()
    lines = [("◈ TAMBAH TEMPLATE", "center"), ""]
    print_box(lines, width=60)

    # Nama Template
    while True:
        name = input("  Nama Template : ").strip()
        if name.upper() == "X":
            return
        if validate_non_empty(name, max_len=100):
            # Cek duplikat nama
            dup = any(t.get('name', '').lower() == name.lower() for t in templates)
            if dup:
                print(f"{C['red']}  ✗ Nama template sudah digunakan.{C['reset']}")
                continue
            break
        print(f"{C['red']}  ✗ Nama tidak valid. Masukkan nama yang benar.{C['reset']}")

    # Looping
    while True:
        looping_raw = input("  Looping (jumlah report) : ").strip()
        if looping_raw.upper() == "X":
            return
        ok, looping = validate_positive_int(looping_raw, max_val=9999)
        if ok:
            break
        print(f"{C['red']}  ✗ Masukkan angka positif (1-9999).{C['reset']}")

    # Email Tujuan
    while True:
        target_raw = input("  Email Tujuan (pisahkan dengan koma untuk multi-target) : ").strip()
        if target_raw.upper() == "X":
            return
        ok, hasil = parse_multi_email(target_raw)
        if ok:
            target = ', '.join(hasil)
            break
        print(f"{C['red']}  ✗ Format email tidak valid: {hasil}{C['reset']}")

    # Subject
    while True:
        subject = input("  Subject : ").strip()
        if subject.upper() == "X":
            return
        if validate_non_empty(subject, max_len=200):
            break
        print(f"{C['red']}  ✗ Subject tidak valid.{C['reset']}")

    # Teks Laporan
    print(f"\n  {C['cyan']}◈ Teks/Pesan Laporan{C['reset']}")
    print(f"  {C['darkgray']}(Tekan Ctrl+D pada baris baru untuk mengakhiri){C['reset']}")
    print(f"  {C['darkgray']}(Isi apa pun tersimpan apa adanya — baris kosong, dsb){C['reset']}\n")
    ok, hasil = read_multiline_text()
    if not ok:
        return
    text = hasil if hasil else "Laporan otomatis."

    # Preview
    clear()
    new_template = {
        "id": get_next_template_id(templates),
        "name": name,
        "looping": looping,
        "target": target,
        "subject": subject,
        "text": text
    }
    print_template_preview(new_template, "◈ PREVIEW TEMPLATE BARU")

    if validate_yes_no("  Simpan Template? [Y/N] :") == "Y":
        templates.append(new_template)
        save_templates(templates)
        print(f"\n  {C['green']}✓ Template '{name}' berhasil disimpan.{C['reset']}")
    else:
        print(f"\n  {C['yellow']}◈ Template dibatalkan.{C['reset']}")
    time.sleep(1.5)

def list_templates():
    """Daftar template"""
    templates = load_templates()
    clear()
    if not templates:
        print(f"{C['red']}  ✗ Belum ada template tersimpan.{C['reset']}")
        time.sleep(1.5)
        return

    lines = [("◈ DAFTAR TEMPLATE", "center"), ""]
    for t in templates:
        lines.append(f"[{t['id']}] {t['name']}")
    lines.extend(["", "[0] Kembali", "", f"{C['darkgray']}Pilih nomor untuk melihat detail{C['reset']}"])
    print_box(lines, width=60)

    valid_ids = [str(t['id']) for t in templates] + ["0"]
    choice = validate_menu_choice("  Pilih :", valid_ids)
    if choice == "X":
        return
    if choice == "0":
        return

    _, selected = find_template_by_id(templates, choice)
    if selected:
        clear()
        print_template_preview(selected, f"◈ DETAIL TEMPLATE [{selected['id']}]")
        input(f"\n  {C['darkgray']}[Tekan Enter untuk kembali]{C['reset']}")

def delete_template():
    """Hapus template"""
    templates = load_templates()
    if not templates:
        clear()
        print(f"{C['red']}  ✗ Belum ada template tersimpan.{C['reset']}")
        time.sleep(1.5)
        return

    clear()
    lines = [("◈ HAPUS TEMPLATE", "center"), ""]
    for t in templates:
        lines.append(f"[{t['id']}] {t['name']}")
    lines.append("")
    print_box(lines, width=60)

    valid_ids = [str(t['id']) for t in templates]
    choice = validate_menu_choice("  Pilih Template :", valid_ids)
    if choice == "X":
        return
    idx, selected = find_template_by_id(templates, choice)

    if selected is None:
        print(f"{C['red']}  ✗ Template tidak ditemukan.{C['reset']}")
        time.sleep(1.5)
        return

    if validate_yes_no(f"  Hapus Template \"{selected['name']}\"? [Y/N] :") == "Y":
        templates.pop(idx)
        save_templates(templates)
        print(f"\n  {C['green']}✓ Template '{selected['name']}' dihapus.{C['reset']}")
    else:
        print(f"\n  {C['yellow']}◈ Penghapusan dibatalkan.{C['reset']}")
    time.sleep(1.5)

def edit_template():
    """Edit template"""
    templates = load_templates()
    if not templates:
        clear()
        print(f"{C['red']}  ✗ Belum ada template tersimpan.{C['reset']}")
        time.sleep(1.5)
        return

    clear()
    lines = [("◈ EDIT TEMPLATE", "center"), ""]
    for t in templates:
        lines.append(f"[{t['id']}] {t['name']}")
    lines.append("")
    print_box(lines, width=60)

    valid_ids = [str(t['id']) for t in templates]
    choice = validate_menu_choice("  Pilih Template :", valid_ids)
    if choice == "X":
        return
    idx, selected = find_template_by_id(templates, choice)

    if selected is None:
        print(f"{C['red']}  ✗ Template tidak ditemukan.{C['reset']}")
        time.sleep(1.5)
        return

    # Edit loop
    edited = dict(selected)  # shallow copy
    while True:
        clear()
        print_template_preview(edited, "◈ EDIT TEMPLATE")
        print()
        edit_lines = [
            "[1] Edit Nama Template",
            "[2] Edit Looping",
            "[3] Edit Email Tujuan",
            "[4] Edit Subject",
            "[5] Edit Teks/Pesan Laporan",
            "",
            "[S] Simpan Perubahan",
            "[B] Batal",
        ]
        print_box(edit_lines, width=60)

        edit_choice = validate_menu_choice("  Pilih :", ["1", "2", "3", "4", "5", "S", "B"])

        if edit_choice == "X":
            print(f"\n  {C['yellow']}◈ Edit dibatalkan.{C['reset']}")
            time.sleep(1.5)
            break

        if edit_choice == "1":
            while True:
                new_name = input("  Nama Template baru : ").strip()
                if new_name.upper() == "X":
                    break
                if validate_non_empty(new_name, max_len=100):
                    dup = any(t.get('name', '').lower() == new_name.lower() and t.get('id') != edited['id'] for t in templates)
                    if dup:
                        print(f"{C['red']}  ✗ Nama sudah digunakan oleh template lain.{C['reset']}")
                        continue
                    edited['name'] = new_name
                    break
                print(f"{C['red']}  ✗ Nama tidak valid.{C['reset']}")

        elif edit_choice == "2":
            while True:
                val = input("  Looping baru : ").strip()
                if val.upper() == "X":
                    break
                ok, n = validate_positive_int(val, max_val=9999)
                if ok:
                    edited['looping'] = n
                    break
                print(f"{C['red']}  ✗ Masukkan angka positif (1-9999).{C['reset']}")

        elif edit_choice == "3":
            while True:
                val = input("  Email Tujuan baru (pisahkan dengan koma untuk multi-target) : ").strip()
                if val.upper() == "X":
                    break
                ok, hasil = parse_multi_email(val)
                if ok:
                    edited['target'] = ', '.join(hasil)
                    break
                print(f"{C['red']}  ✗ Format email tidak valid: {hasil}{C['reset']}")

        elif edit_choice == "4":
            while True:
                val = input("  Subject baru : ").strip()
                if val.upper() == "X":
                    break
                if validate_non_empty(val, max_len=200):
                    edited['subject'] = val
                    break
                print(f"{C['red']}  ✗ Subject tidak valid.{C['reset']}")

        elif edit_choice == "5":
            print(f"\n  {C['cyan']}◈ Teks/Pesan Laporan Baru{C['reset']}")
            print(f"  {C['darkgray']}(Tekan Ctrl+D pada baris baru untuk mengakhiri){C['reset']}")
            print(f"  {C['darkgray']}(Isi apa pun tersimpan apa adanya — baris kosong, dsb){C['reset']}\n")
            ok, hasil = read_multiline_text()
            if ok and hasil:
                edited['text'] = hasil

        elif edit_choice == "S":
            clear()
            print_template_preview(edited, "◈ PREVIEW PERUBAHAN")
            if validate_yes_no("  Simpan perubahan? [Y/N] :") == "Y":
                templates[idx] = edited
                save_templates(templates)
                print(f"\n  {C['green']}✓ Perubahan disimpan.{C['reset']}")
            else:
                print(f"\n  {C['yellow']}◈ Perubahan dibatalkan.{C['reset']}")
            time.sleep(1.5)
            break

        elif edit_choice == "B":
            print(f"\n  {C['yellow']}◈ Edit dibatalkan.{C['reset']}")
            time.sleep(1.5)
            break
            

# ═══════════════════════════════════════════════════════════════
# PROSES REPORT
# ═══════════════════════════════════════════════════════════════

def animasi_loading(detik):
    chars = ['│', '╱', '─', '╲']
    start = time.time()
    while time.time() - start < detik:
        for ch in chars:
            sys.stdout.write(f'\r  {C['darkgray']}⏳ Mengirim laporan {ch}{C['reset']}')
            sys.stdout.flush()
            time.sleep(0.1)
    sys.stdout.write('\r  ' + ' ' * 30 + '\r')
    sys.stdout.flush()

def kirim_email(sender, password, tujuan, subjek, teks):
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        msg = MIMEText(teks)
        msg['Subject'] = subjek
        msg['From'] = sender
        msg['To'] = tujuan
        server.sendmail(sender, [tujuan], msg.as_string())
        server.quit()
        return True
    except:
        return False

def log_result(entry):
    with open(LOG_FILE, 'a') as f:
        f.write(f"{datetime.now().isoformat()} | {entry}\n")

def start_report():
    senders = load_senders()
    if not senders:
        print(f"{C['red']}  ✗ Tidak ada sender terdaftar. Tambahkan dulu.{C['reset']}")
        time.sleep(1.5)
        return

    print_banner()
    print(f"{C['cyan']}  [1] Mulai Report{C['reset']}\n")

    # ── PILIH MODE: Manual atau Template ──
    templates = load_templates()
    use_template = False
    selected_template = None

    if templates:
        print(f"  {C['white']}◈ Template tersedia: {len(templates)}{C['reset']}")
        if validate_yes_no("  Gunakan Template? [Y/N] :") == "Y":
            clear()
            lines = [("◈ PILIH TEMPLATE", "center"), ""]
            for t in templates:
                lines.append(f"[{t['id']}] {t['name']} (×{t['looping']})")
            lines.extend(["", "[0] Batal"])
            print_box(lines, width=60)

            valid_ids = [str(t['id']) for t in templates] + ["0"]
            tchoice = validate_menu_choice("  Pilih Template :", valid_ids)
            if tchoice == "X":
                return
            if tchoice != "0":
                _, selected_template = find_template_by_id(templates, tchoice)
                if selected_template:
                    clear()
                    print_template_preview(selected_template, "◈ PREVIEW TEMPLATE")
                    if validate_yes_no("  Lanjutkan menggunakan Template ini? [Y/N] :") == "Y":
                        use_template = True
                    else:
                        print(f"\n  {C['yellow']}◈ Penggunaan Template dibatalkan.{C['reset']}")
                        time.sleep(1.5)
                        return

    # ── KONFIGURASI REPORT ──
    if use_template and selected_template:
        jumlah = selected_template['looping']
        ok, tujuan_list = parse_multi_email(selected_template['target'])
        if not ok:
            print(f"{C['red']}  ✗ Target di template tidak valid: {tujuan_list}{C['reset']}")
            time.sleep(1.5)
            return
        subjek = selected_template['subject']
        teks = selected_template['text']
        print(f"\n  {C['green']}◈ Menggunakan Template: {selected_template['name']}{C['reset']}")
        print(f"  {C['darkgray']}  Looping: {jumlah} | Target: {', '.join(tujuan_list)}{C['reset']}\n")
    else:
        # Manual input
        while True:
            jumlah_raw = input("  Jumlah report (10, 25, 50, 100, 200) : ").strip()
            if jumlah_raw.upper() == "X":
                return
            ok, jumlah = validate_positive_int(jumlah_raw)
            if ok:
                break
            print(f"{C['red']}  ✗ Masukkan angka positif.{C['reset']}")

        while True:
            tujuan_raw = input("  Email tujuan (pisahkan dengan koma untuk multi-target) : ").strip()
            if tujuan_raw.upper() == "X":
                return
            ok, hasil = parse_multi_email(tujuan_raw)
            if ok:
                tujuan_list = hasil
                break
            print(f"{C['red']}  ✗ Format email tidak valid: {hasil}{C['reset']}")

        subjek = input("  Subject : ").strip()
        if subjek.upper() == "X":
            return
        if not subjek:
            subjek = "Laporan"
            print(f"  {C['yellow']}◈ Subject kosong, menggunakan default 'Laporan'{C['reset']}")

        print(f"\n  {C['cyan']}◈ Teks Laporan{C['reset']}")
        print(f"  {C['darkgray']}(Tekan Ctrl+D pada baris baru untuk mengakhiri){C['reset']}")
        print(f"  {C['darkgray']}(Isi apa pun tersimpan apa adanya — baris kosong, dsb){C['reset']}\n")
        ok, hasil = read_multiline_text()
        if not ok:
            return
        teks = hasil if hasil else "Laporan otomatis."

    # ── PILIH SENDER ──
    print(f"\n  {C['cyan']}◈ Pilih Sender{C['reset']}")
    for i, s in enumerate(senders, 1):
        print(f"  [{i}] {s['email']}")
    print(f"  [{len(senders)+1}] Semua sender")
    valid_senders = [str(i) for i in range(1, len(senders)+2)]
    schoice = validate_menu_choice("  Pilih :", valid_senders)
    if schoice == "X":
        return
    if int(schoice) == len(senders) + 1:
        selected_senders = senders
    else:
        selected_senders = [senders[int(schoice) - 1]]

    # ── PREVIEW ──
    while True:
        print_banner()
        print(f"{C['bold']}  ◈ PREVIEW LAPORAN{C['reset']}\n")
        print(f"  Jumlah Report  : {jumlah}")
        print(f"  Email Tujuan   : {', '.join(tujuan_list)}")
        print(f"  Subject        : {subjek}")
        print(f"  Jumlah Sender  : {len(selected_senders)}")
        print(f"  Jumlah Target  : {len(tujuan_list)}")
        print()
        show = validate_yes_no("  Tampilkan teks laporan? [Y/N] :")
        if show == "Y":
            clear()
            print(f"{C['cyan']}  ── TEKS LAPORAN ──{C['reset']}")
            print(teks)
            print(f"{C['cyan']}  ──────────────────{C['reset']}")
            input(f"\n  {C['darkgray']}[Tekan Enter untuk kembali]{C['reset']}")
            continue
        break

    # ── KONFIRMASI FINAL ──
    if validate_yes_no("  Mulai report? [Y/N] :") != "Y":
        print(f"\n  {C['yellow']}◈ Dibatalkan oleh pengguna.{C['reset']}")
        time.sleep(1.5)
        return

    # ── EKSEKUSI ──
    print(f"\n  {C['green']}◈ Memulai report...{C['reset']}\n")
    total_sukses = 0
    total_gagal = 0
    total_percobaan = jumlah * len(tujuan_list)
    percobaan_ke = 0
    try:
        for i in range(1, jumlah + 1):
            sender = selected_senders[(i - 1) % len(selected_senders)]
            for tujuan in tujuan_list:
                percobaan_ke += 1
                status = kirim_email(sender['email'], sender['password'], tujuan, subjek, teks)
                if status:
                    total_sukses += 1
                    log_result(f"SUCCESS | #{i} | {sender['email']} → {tujuan}")
                    sys.stdout.write(f"\r  {C['green']}✓ [{percobaan_ke}/{total_percobaan}] Berhasil → {tujuan}{C['reset']}  ")
                else:
                    total_gagal += 1
                    log_result(f"FAILED  | #{i} | {sender['email']} → {tujuan}")
                    sys.stdout.write(f"\r  {C['red']}✗ [{percobaan_ke}/{total_percobaan}] Gagal → {tujuan}{C['reset']}  ")
                sys.stdout.flush()
            if i < jumlah:
                delay = random.uniform(5, 7)
                animasi_loading(delay)
        print()
    except KeyboardInterrupt:
        print(f"\n\n  {C['yellow']}◈ Proses dihentikan oleh pengguna.{C['reset']}")
        log_result(f"INTERRUPTED after {total_sukses+total_gagal} emails")
        time.sleep(1.5)
        return

    # ── HASIL ──
    print_banner()
    print(f"{C['bold']}  ◈ HASIL REPORT{C['reset']}\n")
    print(f"  Target         : {', '.join(tujuan_list)}")
    print(f"  Berhasil       : {total_sukses}")
    print(f"  Gagal          : {total_gagal}")
    print(f"  Total          : {total_sukses + total_gagal}")
    print(f"  Log            : {LOG_FILE}")
    input(f"\n  {C['darkgray']}[Tekan Enter untuk kembali]{C['reset']}")
        
     
def note():
    while True:
        clear()
        print("""
  [i]  Note

Tool ini dibuat dengan waktu dan usaha oleh pembuat aslinya.
Jika kamu menggunakan, memodifikasi, atau menyebarkan tool ini,
mohon:

1. Sertakan kredit ke pembuat asli
2. Jangan mengklaim ini sebagai karya sendiri
3. Jangan menjual atau memperjualbelikan tanpa izin

Menghargai kerja pembuat adalah bentuk etika dasar dalam
berbagi karya open source.

    Ketik 'x' untuk kembali ke menu.
        """)
        pilihan = input(">> ").strip().lower()
        if pilihan == "x":
            break

# ═══════════════════════════════════════════════════════════════
# MENU UTAMA
# ═══════════════════════════════════════════════════════════════

def main_menu():
    threading.Thread(target=auto_refresh, daemon=True).start()

    while True:
        print_banner()
        lines = [
            ("⌯ MAIN MENU", "center"),
            "",
            "[1] Mulai Report ⊸",
            "[2] Tambah Sender ⊸",
            "[3] Hapus Sender ⊸",
            "[4] Daftar Sender ⊸",
            "[5] Cek Limit Email ⊸",
            "[6] Template ⊸",
            "[7] Note ⊸",
            "",
            "[0] Keluar"
        ]
        print_box(lines, width=60)
        print()
        print(f"{C['darkgray']}  {line('─', 47)}{C['reset']}")
        print(f"  {C['bold']}֍ Development Assistant{C['reset']}\n")
        print(f"  {C['darkgray']}  OpenAI · ChatGPT{C['reset']}")
        print(f"  {C['darkgray']}  Moonshot · Kimi{C['reset']}")
        print(f"  {C['darkgray']}  DeepSeek · DeepSeek{C['reset']}")
        print(f"{C['darkgray']}  {line('─', 47)}{C['reset']}")
        print(f"{C['darkgray']}  {line('─', 47)}{C['reset']}")
        print(f"  {C['bold']}⊶ Help?{C['reset']}\n")
        print(f"  {C['darkgray']}  Tekan (X) untuk membatalkan dan kembali.{C['reset']}")
        print(f"{C['darkgray']}  {line('─', 47)}{C['reset']}")
        print(f"  {C['bold']}⍟ Laporkan Bug : {C['reset']} {C['link']}IntDy5.t.me{C['reset']}")
        print()

        choice = validate_menu_choice(f"  {C['bold']}{C['green']}Select » {C['reset']}", ["0", "1", "2", "3", "4", "5", "6", "7"])

        if choice == '1':
            start_report()
        elif choice == '2':
            add_sender()
        elif choice == '3':
            delete_sender()
        elif choice == '4':
            list_senders()
        elif choice == '5':
            check_limits()
        elif choice == '6':
            template_menu()
        elif choice == '7':
            note()
        elif choice == '0':
            clear()
            print(f"{C['green']}  ✦ Terima kasih telah menggunakan script ini.{C['reset']}")
            sys.exit(0)


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print(f"\n\n  {C['yellow']}⛌ Program dihentikan.{C['reset']}")
        sys.exit(0)

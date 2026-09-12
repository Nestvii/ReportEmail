#!/data/data/com.termux/files/usr/bin/bash
set -e

ENTRY_FILE="repGmail.py"

git reset --hard --quiet 2>/dev/null || true

echo "◈ Sedang memeriksa pembaruan dari GitHub."
if git pull --quiet 2>/tmp/gr_fetch_err.log; then
    echo "✓ Sinkronisasi dengan GitHub berhasil."
else
    echo "⚠ Tidak dapat terhubung ke GitHub. Proses dilanjutkan menggunakan versi lokal terakhir."
    cat /tmp/gr_fetch_err.log 2>/dev/null
fi

echo ""
python3 "$ENTRY_FILE"
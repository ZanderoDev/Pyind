"""
keywords.py — Leksikon Bahasa Indonesia untuk Pyind.
Bagian dari proyek Pyind (Python Indonesia).

Modul ini memuat tiga kelompok leksikon yang sengaja dipisah:

1. :data:`KATA_KUNCI_KHUSUS` — *reserved words*. Nama-nama ini tidak boleh
   dipakai sebagai identifier, persis seperti ``def``/``if``/``class`` di
   Python. Contoh: ``fungsi``, ``jika``, ``kelas``.
2. :data:`KATA_KUNCI_KONTEKSTUAL` — *soft keywords*. Hanya makna khusus di
   konteks tertentu; di luar itu tetap boleh menjadi identifier. Contoh:
   ``cetak``, ``panjang``, ``dalam``.
3. :data:`FUNGSI_BAWAAN` — nama fungsi/kelas bawaan Python yang punya
   padanan Bahasa Indonesia.

Mengapa pemisahan ini penting? Karena Python sendiri membedakan *reserved*
vs *soft keyword* pada tingkat parser, bukan lexer
(lihat https://docs.python.org/3/reference/lexical_analysis.html#soft-keywords).
Pyind meniru perilaku tersebut: lexer hanya menandai *reserved word*,
selain soft keyword sisanya tetap keluar sebagai token ``NAMA`` dan
diperlakukan sebagai nama biasa.

Kata kunci Python yang belum diterjemahkan (``True``, ``not``, ``in``,
``is``, ``async``, ``await``, ``yield``, ``match`` …) tetap bisa ditulis
apa adanya supaya kode lama tidak rusak.
"""

from __future__ import annotations

# ── 1. Kata kunci khusus (reserved) ──────────────────────────────────────────
# Peta: Bahasa Indonesia -> Python.
KATA_KUNCI_KHUSUS: dict[str, str] = {
    # Definisi & struktur
    "fungsi":       "def",
    "kelas":        "class",
    "impor":        "import",
    "dari":         "from",
    "sebagai":       "as",
    "kembalikan":   "return",
    "kembali":      "return",      # alias yang lebih ringkas

    # Kontrol alur
    "benar":        "True",
    "salah":        "False",
    "kosong":       "None",

    "jika":         "if",
    "lainnya":      "else",
    "jika_tidak":   "elif",
    "untuk":        "for",
    "selama":       "while",
    "hentikan":     "break",
    "lanjut":       "continue",
    "lewati":       "pass",
    "coba":         "try",
    "kecuali":     "except",
    "akhirnya":     "finally",
    "naikkan":      "raise",
    "pernyataan":   "assert",

    # Operator logika (kata kunci di Python, bukan simbol)
    "dan":          "and",
    "atau":         "or",
    "bukan":        "not",
    "tidak":        "not",         # alias

    # Pernyataan sederhana
    "hapus":        "del",
    "bersama":      "with",
    "global":       "global",
    "nonlokal":     "nonlocal",
    "lambda":       "lambda",
    "hasilkan":     "yield",       # konten: 'hasilkan x'
    "hasilkan_dari": "yield_dari", # konten: 'hasilkan_dari x' -> yield from

    # Alias lain yang dipertahankan untuk kompatibilitas
    "jika_hanya":   "if",          # tidak standar; dipakai sebagai penanda
}

# Alias lain: 'menjadi' (as) dan 'lewat' (pass) sengaja TIDAK ada di sini
# supaya keduanya tetap sah sebagai nama variabel/identifier.
#
# 'menjadi'   -> penulisan `impor os menjadi o` ditangani parser
#                sebagai alias dari 'sebagai' (lihat parser.Parser._adalah_alias)
# 'lewat'     -> tidak dipetakan; pakai 'lewati' untuk `pass`.

KATA_KUNCI_KHUSUS_SET: frozenset[str] = frozenset(KATA_KUNCI_KHUSUS)

# ── 2. Kata kunci kontekstual (soft keyword) ─────────────────────────────────
# Nama ini boleh identifier; resolver simbol di transpiler memakai peta ini
# untuk mengganti ke padanan Python HANYA jika nama tersebut tetap bebas
# (tidak pernah di-bind ke nilai lain di scope tersebut).
KATA_KUNCI_KONTEKSTUAL: dict[str, str] = {
    # Fungsi bawaan yang paling sering dipakai
    "cetak":     "print",
    "masukkan":  "input",
    "panjang":   "len",
    "tipe":      "type",
    "bilangan":  "int",
    "desimal":   "float",
    "teks":      "str",
    "daftar":    "list",
    "kamus":     "dict",
    "himpunan":  "set",
    "rentang":   "range",

    # Pelengkap yang sering dipakai
    "sebut":     "str",      # alias 'teks'
    "urut":      "sorted",
    "jumlah":    "sum",
    "muter":     "iter",
    "nilai_abs": "abs",
    "bulat":     "round",
}

KATA_KUNCI_KONTEKSTUAL_SET: frozenset[str] = frozenset(KATA_KUNCI_KONTEKSTUAL)

# ── 3. Fungsi bawaan Python dengan padanan Indonesia ───────────────────────
# Nama yang TIDAK boleh identifier bebas (dipakai sebagai penanda sintaks):
# 'hapus' (del), 'bersama' (with), 'global', 'nonlokal', 'lewat' (pass),
# 'pernyataan' (assert), 'lambda', 'hasilkan' (yield), 'hasilkan_dari'.
# Semua sudah masuk KATA_KUNCI_KHUSUS.

# Kata kunci Python yang boleh dipakai langsung apa adanya (tanpa terjemahan).
KATA_KUNCI_PYTHON: frozenset[str] = frozenset({
    "False", "None", "True",
    "and", "as", "assert", "async", "await", "break", "class", "continue",
    "def", "del", "elif", "else", "except", "finally", "for", "from",
    "global", "if", "import", "in", "is", "lambda", "nonlocal", "not", "or",
    "pass", "raise", "return", "try", "while", "with", "yield",
    "match", "case",  # soft keyword Python 3.10+
})

# Kata kunci Python yang dipetakan ke literal.
KATA_KUNCI_LITERAL: dict[str, str] = {"True": "True", "False": "False", "None": "None"}

# ── Peta gabungan untuk kompatibilitas ke belakang ────────────────────────────
#: Versi lama modul ini mengekspor KEYWORDS; pertahankan agar kode lama tidak
#: rusak. Sekarang isinya adalah gabungan reserved + kontekstual + builtin.
KEYWORDS: dict[str, str] = {**KATA_KUNCI_KHUSUS, **KATA_KUNCI_KONTEKSTUAL}
KEYWORD_SET: frozenset[str] = frozenset(KEYWORDS)

# ── Token operator & delimiter ───────────────────────────────────────────────
#: Operator 3 karakter — dicek paling dulu (longest-match-first).
THREE_CHAR_OPS: frozenset[str] = frozenset({"**=", "//=", ">>=", "<<=", "..."})

#: Operator 2 karakter — dicek setelah 3 karakter.
TWO_CHAR_OPS: frozenset[str] = frozenset({
    "==", "!=", "<=", ">=", "+=", "-=", "*=", "/=",
    "//", "**", "->", "<<", ">>", "%=", "&=", "|=", "^=", "@=", ":=",
})

#: Operator 1 karakter.
ONE_CHAR_OPS: frozenset[str] = frozenset({
    "+", "-", "*", "/", "%", "=", "<", ">", "!",
    "&", "|", "^", "~", "@",
})

#: Delimiter (tanda baca). Python mengelompokkan sebagian di sini sebagai OP.
DELIMITERS: frozenset[str] = frozenset({
    "(", ")", "[", "]", "{", "}",
    ",", ":", ".", ";",
})

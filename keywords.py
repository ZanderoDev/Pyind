"""
keywords.py — Peta kata kunci Bahasa Indonesia ke Python.
Bagian dari proyek Pyind (Python Indonesia).

Modul ini berisi semua kata kunci yang dikenali transpiler,
termasuk kata kunci kontrol alur, tipe data, dan operator logika.
"""

# Peta kata kunci: Bahasa Indonesia -> Python
KEYWORDS: dict[str, str] = {
    # Definisi & struktur
    "fungsi":     "def",
    "kelas":      "class",
    "impor":      "import",
    "dari":       "from",
    "sebagai":    "as",
    "kembalikan": "return",
    "kembali":    "return",   # alias

    # Kontrol alur
    "jika":       "if",
    "lainnya":    "else",
    "jika_tidak": "elif",
    "untuk":      "for",
    "selama":     "while",
    "hentikan":   "break",
    "lanjut":     "continue",
    "lewati":     "pass",

    # Iterasi
    "dalam":      "in",
    "rentang":    "range",

    # Penanganan error
    "coba":       "try",
    "kecuali":    "except",
    "akhirnya":   "finally",
    "naikkan":    "raise",

    # Nilai literal
    "benar":      "True",
    "salah":      "False",
    "kosong":     "None",

    # Operator logika
    "dan":        "and",
    "atau":       "or",
    "bukan":      "not",
    "tidak":      "not",   # alias

    # Fungsi bawaan umum
    "cetak":      "print",
    "masukkan":   "input",
    "panjang":    "len",
    "tipe":       "type",
    "bilangan":   "int",
    "desimal":    "float",
    "teks":       "str",
    "daftar":     "list",
    "kamus":      "dict",
    "himpunan":   "set",
    "hapus":      "del",
    "bersama":    "with",
    "menjadi":    "as",
    "global":     "global",
    "nonlokal":   "nonlocal",
    "lewat":      "pass",
    "pernyataan": "assert",
    # yield tidak dipetakan — terlalu ambigu sebagai nama variabel/metode.
    # Gunakan 'yield' Python langsung jika diperlukan.
    "lambda":     "lambda",
}

# Sekumpulan kata kunci (untuk pengecekan cepat O(1))
KEYWORD_SET: set[str] = set(KEYWORDS.keys())

# Operator TIGA karakter — harus dicek lebih dulu di lexer (longest-match-first)
THREE_CHAR_OPS: set[str] = {"**=", "//="}

# Operator DUA karakter — dicek setelah THREE_CHAR_OPS
TWO_CHAR_OPS: set[str] = {
    "==", "!=", "<=", ">=", "+=", "-=", "*=", "/=",
    "//", "**", "->", "<<", ">>", "%=",
}

# Operator satu karakter
ONE_CHAR_OPS: set[str] = {
    "+", "-", "*", "/", "%", "=", "<", ">", "!",
    "&", "|", "^", "~", "@",
}

# Delimiter (tidak termasuk dalam operator)
DELIMITERS: set[str] = {
    "(", ")", "[", "]", "{", "}",
    ",", ":", ".", ";",
}

"""
sinkronkan_leksikon.py — Bangun ulang grammar highlight dari keywords.py.
Bagian dari proyek Pyind (Python Indonesia).

Fungsi:
  Regenerate `extensi/vscode/syntaxes/pyind.tmLanguage.json` dan daftar
  kata kunci di `extensi/acode/main.js` sehingga keduanya selalu mengikuti
  `keywords.py` — sumber kebenaran tunggal.

Pakai ulang setelah mengubah leksikon:

    python extensi/alat/sinkronkan_leksikon.py

Hanya pustaka standar.
"""

from __future__ import annotations

import json
import os
import re
import sys

AKAR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, AKAR)

from keywords import KATA_KUNCI_KHUSUS, KATA_KUNCI_KONTEKSTUAL  # noqa: E402

#: Kata kunci Python yang boleh ditulis apa adanya di berkas .pyind.
KATA_KUNCI_PYTHON: frozenset[str] = frozenset({
    "async", "await", "break", "class", "continue", "def", "del", "elif",
    "else", "except", "finally", "for", "from", "global", "if", "import",
    "in", "is", "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
    "try", "while", "with", "yield", "and", "as", "assert", "match", "case",
})

KELOMPOK: dict[str, set[str]] = {
    "kontrol": set(KATA_KUNCI_KHUSUS) | set(KATA_KUNCI_PYTHON),
    "exception": {"coba", "kecuali", "akhirnya", "naikkan", "pernyataan"},
    "literal": {"benar", "salah", "kosong", "True", "False", "None"},
    "logika": {"dan", "atau", "bukan", "tidak"},
    "penghasil": {"hasilkan", "hasilkan_dari", "yield"},
    "hapus": {"hapus", "del"},
    "bawaan": set(KATA_KUNCI_KONTEKSTUAL),
}

#: Nama yang sah sebagai identifier sehingga tidak boleh jadi keyword.
JANGAN_KEYWORD: frozenset[str] = frozenset({
    "dalam", "rentang", "lewat", "menjadi",
})

#: Regex pembuka string triple-quote dengan prefiks opsional.
#: Ditulis lewat chr() supaya file ini tidak memuat triple-quote.
POLA_TIGA_KUTIP = (
    r"[bBfFrRtTuU]{0,2}(" + chr(34) * 3 + "|" + chr(39) * 3 + ")"
)


def pola(kata) -> str:
    """Susun alternasi regex, yang panjang lebih dulu agar tidak tertelan."""
    return "|".join(sorted(set(kata), key=lambda x: (-len(x), x)))


def pola_kontrol() -> str:
    """Pola keyword kontrol: buang nama yang sah sebagai identifier."""
    return pola(k for k in KELOMPOK["kontrol"] if k not in JANGAN_KEYWORD)


def bangun_tmlanguage() -> dict:
    """Bangun objek grammar TextMate."""
    return {
        "$schema": "https://raw.githubusercontent.com/martinring/tmlanguage/master/tmlanguage.json",
        "name": "Pyind",
        "scopeName": "source.pyind",
        "version": "1.1.0",
        "comment": "Dihasilkan oleh extensi/alat/sinkronkan_leksikon.py — jangan diubah manual.",
        "patterns": [
            {"include": "#comments"},
            {"include": "#strings"},
            {"include": "#numbers"},
            {"include": "#decorator"},
            {"include": "#function-definition"},
            {"include": "#class-definition"},
            {"include": "#keywords-exception"},
            {"include": "#constants"},
            {"include": "#keywords-yield"},
            {"include": "#keywords-del"},
            {"include": "#keywords-logical"},
            {"include": "#keywords-control"},
            {"include": "#builtins"},
            {"include": "#operators"},
        ],
        "repository": {
            "comments": {
                "name": "comment.line.number-sign.pyind",
                "begin": "#", "end": "$",
                "beginCaptures": {"0": {"name": "punctuation.definition.comment.pyind"}},
            },
            "strings": {"patterns": [
                {
                    "comment": "Triple-quote dengan prefiks rb/br/fr/rf/tr/u",
                    "name": "string.quoted.triple.pyind",
                    "begin": POLA_TIGA_KUTIP,
                    "end": r"(\1)",
                },
                {
                    "name": "string.quoted.double.pyind",
                    "begin": r"[bBfFrRtTuU]{0,2}\"", "end": "\"",
                    "patterns": [{"name": "constant.character.escape.pyind", "match": r"\\."}],
                },
                {
                    "name": "string.quoted.single.pyind",
                    "begin": r"[bBfFrRtTuU]{0,2}'", "end": "'",
                    "patterns": [{"name": "constant.character.escape.pyind", "match": r"\\."}],
                },
            ]},
            "numbers": {
                "comment": "Biner/oktal/heksa, desimal, eksponen, kompleks",
                "name": "constant.numeric.pyind",
                "match": r"\b(?:0[xX][0-9a-fA-F_]+|0[oO][0-7_]+|0[bB][01_]+"
                        r"|\d[\d_]*\.?[\d_]*(?:[eE][+-]?\d+)?)[jJ]?\b",
            },
            "decorator": {
                "match": r"(@)\s*([_\p{L}][_\p{L}\p{N}]*)",
                "captures": {
                    "1": {"name": "punctuation.definition.decorator.pyind"},
                    "2": {"name": "entity.name.function.pyind"},
                },
            },
            "function-definition": {
                "match": r"\b(fungsi)\s+([_\p{L}][_\p{L}\p{N}]*)",
                "captures": {
                    "1": {"name": "keyword.control.pyind"},
                    "2": {"name": "entity.name.function.pyind"},
                },
            },
            "class-definition": {
                "match": r"\b(kelas)\s+([_\p{L}][_\p{L}\p{N}]*)",
                "captures": {
                    "1": {"name": "keyword.control.pyind"},
                    "2": {"name": "entity.name.class.pyind"},
                },
            },
            "keywords-control": {
                "name": "keyword.control.pyind",
                "match": r"\b(?:%s)\b" % pola_kontrol(),
            },
            "keywords-exception": {
                "name": "keyword.control.exception.pyind",
                "match": r"\b(?:%s)\b" % pola(KELOMPOK["exception"]),
            },
            "keywords-yield": {
                "name": "keyword.control.pyind",
                "match": r"\b(?:%s)\b" % pola(KELOMPOK["penghasil"]),
            },
            "keywords-del": {
                "name": "keyword.control.pyind",
                "match": r"\b(?:%s)\b" % pola(KELOMPOK["hapus"]),
            },
            "keywords-logical": {
                "name": "keyword.operator.logical.pyind",
                "match": r"\b(?:%s)\b" % pola(KELOMPOK["logika"]),
            },
            "constants": {
                "name": "constant.language.pyind",
                "match": r"\b(?:%s)\b" % pola(KELOMPOK["literal"]),
            },
            "builtins": {
                "comment": "Boleh juga identifier — warna hanya petunjuk",
                "name": "support.function.builtin.pyind",
                "match": r"\b(?:%s)\b" % pola(KELOMPOK["bawaan"]),
            },
            "operators": {
                "name": "keyword.operator.pyind",
                "match": r"\*\*=|//=|>>=|<<=|:=|\.\.\.|"
                        r"[+\-*/%@&|^]=|==|!=|<=|>=|->|//|\*\*|<<|>>|"
                        r"\+=|-=|\*=|/=|%=",
            },
        },
    }


def tulis_tmlanguage() -> str:
    """Tulis grammar TextMate dan kembalikan jalurnya."""
    jalur = os.path.join(AKAR, "extensi", "vscode", "syntaxes", "pyind.tmLanguage.json")
    os.makedirs(os.path.dirname(jalur), exist_ok=True)
    with open(jalur, "w", encoding="utf-8") as f:
        json.dump(bangun_tmlanguage(), f, ensure_ascii=False, indent=2)
        f.write("\n")
    return jalur


def perbarui_acode() -> str:
    """
    Perbarui hanya blok leksikon di main.js Acode.

    main.js ditulis tangan (bukan template) supaya indentasi dan regex
    tetap mudah dibaca; hanya tujuh baris ``new Set([...])`` yang
    disinkronkan.
    """
    jalur = os.path.join(AKAR, "extensi", "acode", "main.js")
    with open(jalur, encoding="utf-8") as f:
        teks = f.read()

    kontrol = (set(KATA_KUNCI_KHUSUS) | set(KATA_KUNCI_PYTHON)) - set(JANGAN_KEYWORD)
    pasang = {
        "KONTROL": sorted(kontrol),
        "EXCEPTION": sorted(KELOMPOK["exception"]),
        "LITERAL": sorted(KELOMPOK["literal"]),
        "LOGIKA": sorted(KELOMPOK["logika"]),
        "PENGHASIL": sorted(KELOMPOK["penghasil"]),
        "HAPUS": sorted(KELOMPOK["hapus"]),
        "BAWAAN": sorted(KATA_KUNCI_KONTEKSTUAL),
    }

    for nama, daftar in pasang.items():
        pola_teks = json.dumps(daftar, ensure_ascii=False)
        spasi = " " * max(1, 12 - len(nama))
        baru = f"const {nama}{spasi}= new Set({pola_teks});"
        teks, n = re.subn(rf"const {nama}\s*= new Set\(\[.*?\]\);", baru, teks, count=1)
        if n != 1:
            raise RuntimeError(f"Tidak menemukan blok const {nama} di main.js")

    with open(jalur, "w", encoding="utf-8") as f:
        f.write(teks)
    return jalur


def utama() -> None:
    """Regenerate seluruh berkas highlight."""
    a = tulis_tmlanguage()
    b = perbarui_acode()
    print(f"[Pyind] Ditulis: {os.path.relpath(a, AKAR)}")
    print(f"[Pyind] Ditulis: {os.path.relpath(b, AKAR)}")
    print(f"[Pyind] reserved={len(KATA_KUNCI_KHUSUS)} "
          f"kontekstual={len(KATA_KUNCI_KONTEKSTUAL)}")


if __name__ == "__main__":
    utama()

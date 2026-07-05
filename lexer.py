"""
lexer.py — Tokenizer (Lexer) untuk Pyind.
Bagian dari proyek Pyind (Python Indonesia).

Mengubah source code teks menjadi aliran token yang terstruktur.
Tahap ini menangani: keyword, identifier, number, string, operator,
delimiter, komentar, NEWLINE, INDENT, dan DEDENT.

String literal AMAN: teks di dalam tanda kutip tidak akan diterjemahkan.
"""

from __future__ import annotations
from enum import Enum, auto
from typing import Iterator

from keywords import (
    KEYWORDS, KEYWORD_SET, ONE_CHAR_OPS, TWO_CHAR_OPS, THREE_CHAR_OPS, DELIMITERS
)
from errors import (
    err_karakter_tak_dikenal,
    err_string_tidak_ditutup,
    err_dedent_tak_cocok,
)


# ── Jenis-jenis Token ────────────────────────────────────────────────────────

class TipeToken(Enum):
    # Literal nilai
    ANGKA      = auto()   # integer atau float: 42, 3.14
    TEKS       = auto()   # string literal: "halo", 'dunia'
    BENAR      = auto()   # True / benar
    SALAH      = auto()   # False / salah
    KOSONG     = auto()   # None / kosong

    # Nama & kata kunci
    NAMA       = auto()   # identifier / nama variabel
    KATA_KUNCI = auto()   # kata kunci (sudah dipetakan ke padanan Python)

    # Operator & tanda baca
    OP         = auto()   # operator (+, -, ==, <=, dst.)
    DELIMITER  = auto()   # tanda baca (, : ( ) [ ] { })

    # Kontrol struktur
    BARIS_BARU = auto()   # \n (akhir pernyataan)
    INDENT     = auto()   # tambah level indentasi
    DEDENT     = auto()   # kurang level indentasi

    # Spesial
    EOF        = auto()   # akhir file


class Token:
    """Satu unit leksikal dari source code."""

    __slots__ = ("tipe", "nilai", "baris", "kolom")

    def __init__(self, tipe: TipeToken, nilai: str | int | float,
                 baris: int = 0, kolom: int = 0):
        self.tipe = tipe
        self.nilai = nilai
        self.baris = baris
        self.kolom = kolom

    def __repr__(self) -> str:
        return (
            f"Token({self.tipe.name}, {self.nilai!r}, "
            f"b{self.baris}:k{self.kolom})"
        )


# ── Kelas Lexer ──────────────────────────────────────────────────────────────

class Lexer:
    """
    Memproses source code karakter per karakter dan menghasilkan
    daftar token. Mendukung INDENT/DEDENT berbasis spasi.
    """

    def __init__(self, source: str):
        self.source = source
        self.pos = 0           # posisi karakter saat ini
        self.baris = 1
        self.kolom = 1
        self._indent_stack: list[int] = [0]   # tumpukan level indentasi

    # ── API publik ────────────────────────────────────────────────────────────

    def tokenisasi(self) -> list[Token]:
        """
        Jalankan seluruh proses tokenisasi dan kembalikan daftar token.
        Menambahkan token EOF di akhir.
        """
        return list(self._iterasi_token())

    # ── Generator utama ───────────────────────────────────────────────────────

    def _iterasi_token(self) -> Iterator[Token]:
        """Hasilkan token satu per satu dari source code."""
        awal_baris = True   # apakah kita di awal baris baru?

        while self.pos < len(self.source):
            c = self._karakter()

            # ── Awal baris: hitung indentasi ──────────────────────────────
            if awal_baris:
                awal_baris = False
                for tok in self._proses_indentasi():
                    yield tok
                continue

            # ── Lewati spasi (bukan awal baris) ──────────────────────────
            if c in (' ', '\t'):
                self._maju()
                continue

            # ── Komentar (#) ──────────────────────────────────────────────
            if c == '#':
                self._lewati_komentar()
                continue

            # ── Baris baru ────────────────────────────────────────────────
            if c == '\n':
                b = self.baris
                self._maju()
                self.baris += 1
                self.kolom = 1
                awal_baris = True
                yield Token(TipeToken.BARIS_BARU, "\n", b, self.kolom)
                continue

            # ── Karakter \ sebagai line continuation ──────────────────────
            if c == '\\' and self._intip(1) == '\n':
                self._maju()
                self._maju()
                self.baris += 1
                self.kolom = 1
                continue

            # ── String literal (isi string TIDAK diterjemahkan) ───────────
            if c in ('"', "'"):
                yield self._baca_string()
                continue

            # ── f-string ──────────────────────────────────────────────────
            if c in ('f', 'F', 'r', 'R', 'b', 'B') and self._intip(1) in ('"', "'"):
                yield self._baca_string_prefix()
                continue

            # ── Angka ─────────────────────────────────────────────────────
            if c.isdigit() or (c == '.' and self._intip(1).isdigit()):
                yield self._baca_angka()
                continue

            # ── Identifier / kata kunci ───────────────────────────────────
            if c.isalpha() or c == '_':
                yield self._baca_nama()
                continue

            # ── Operator tiga karakter (longest-match-first) ──────────────
            tiga = self.source[self.pos: self.pos + 3]
            if tiga in THREE_CHAR_OPS:
                tok = Token(TipeToken.OP, tiga, self.baris, self.kolom)
                self._maju(); self._maju(); self._maju()
                yield tok
                continue

            # ── Operator dua karakter ─────────────────────────────────────
            dua = self.source[self.pos: self.pos + 2]
            if dua in TWO_CHAR_OPS:
                tok = Token(TipeToken.OP, dua, self.baris, self.kolom)
                self._maju()
                self._maju()
                yield tok
                continue

            # ── Operator satu karakter ────────────────────────────────────
            if c in ONE_CHAR_OPS:
                tok = Token(TipeToken.OP, c, self.baris, self.kolom)
                self._maju()
                yield tok
                continue

            # ── Delimiter ─────────────────────────────────────────────────
            if c in DELIMITERS:
                tok = Token(TipeToken.DELIMITER, c, self.baris, self.kolom)
                self._maju()
                yield tok
                continue

            # ── Karakter tidak dikenal ────────────────────────────────────
            raise err_karakter_tak_dikenal(c, self.baris, self.kolom)

        # ── Akhir file: tutup semua INDENT yang masih terbuka ─────────────
        while len(self._indent_stack) > 1:
            self._indent_stack.pop()
            yield Token(TipeToken.DEDENT, "DEDENT", self.baris, self.kolom)

        yield Token(TipeToken.EOF, "EOF", self.baris, self.kolom)

    # ── Pemrosesan indentasi ──────────────────────────────────────────────────

    def _proses_indentasi(self) -> Iterator[Token]:
        """
        Hitung spasi di awal baris. Hasilkan INDENT atau DEDENT
        sesuai perubahan level. Baris kosong dan baris komentar dilewati.
        """
        spasi = 0

        while self.pos < len(self.source):
            c = self.source[self.pos]
            if c == ' ':
                spasi += 1
                self._maju()
            elif c == '\t':
                spasi = (spasi // 4 + 1) * 4   # konversi tab ke 4 spasi
                self._maju()
            elif c == '\n':
                # Baris kosong — reset dan mulai ulang
                self._maju()
                self.baris += 1
                self.kolom = 1
                spasi = 0
            elif c == '#':
                # Baris komentar — lewati, lalu mulai ulang
                self._lewati_komentar()
                spasi = 0
            else:
                break

        prev = self._indent_stack[-1]

        if spasi > prev:
            self._indent_stack.append(spasi)
            yield Token(TipeToken.INDENT, "INDENT", self.baris, self.kolom)
        elif spasi < prev:
            while self._indent_stack[-1] > spasi:
                self._indent_stack.pop()
                yield Token(TipeToken.DEDENT, "DEDENT", self.baris, self.kolom)
            if self._indent_stack[-1] != spasi:
                raise err_dedent_tak_cocok(self.baris)

    # ── Pembacaan token individual ────────────────────────────────────────────

    def _baca_string(self) -> Token:
        """
        Membaca string literal (tunggal, ganda, atau triple-quote).
        Isi string TIDAK diproses untuk penerjemahan kata kunci —
        ini menjamin keamanan: cetak("jika hujan") tetap utuh.
        """
        b, k = self.baris, self.kolom
        pembuka = self._karakter()
        self._maju()

        # Deteksi triple-quote
        if self.source[self.pos: self.pos + 2] == pembuka * 2:
            self._maju()
            self._maju()
            return self._baca_string_triple(pembuka, b, k)

        # String biasa (satu baris)
        hasil = pembuka
        while self.pos < len(self.source):
            c = self._karakter()
            if c == '\n':
                raise err_string_tidak_ditutup(b, k)
            if c == '\\':
                hasil += c
                self._maju()
                if self.pos < len(self.source):
                    hasil += self._karakter()
                    self._maju()
                continue
            hasil += c
            self._maju()
            if c == pembuka:
                break
        else:
            raise err_string_tidak_ditutup(b, k)

        return Token(TipeToken.TEKS, hasil, b, k)

    def _baca_string_triple(self, pembuka: str, b: int, k: int) -> Token:
        """Membaca string triple-quote (bisa multi-baris)."""
        penutup = pembuka * 3
        hasil = penutup

        while self.pos < len(self.source):
            if self.source[self.pos: self.pos + 3] == penutup:
                hasil += penutup
                self._maju()
                self._maju()
                self._maju()
                return Token(TipeToken.TEKS, hasil, b, k)
            c = self._karakter()
            if c == '\n':
                self.baris += 1
                self.kolom = 1
            hasil += c
            self._maju()

        raise err_string_tidak_ditutup(b, k)

    def _baca_string_prefix(self) -> Token:
        """Membaca f-string, r-string, atau b-string dengan prefix."""
        b, k = self.baris, self.kolom
        prefix = self._karakter()
        self._maju()
        # Ambil string berikutnya lalu sisipkan prefix
        tok = self._baca_string()
        return Token(TipeToken.TEKS, prefix + str(tok.nilai), b, k)

    def _baca_angka(self) -> Token:
        """Membaca integer atau float (termasuk format 1_000_000)."""
        b, k = self.baris, self.kolom
        awal = self.pos
        ada_titik = False

        while self.pos < len(self.source):
            c = self._karakter()
            if c.isdigit() or c == '_':
                self._maju()
            elif c == '.' and not ada_titik and self._intip(1).isdigit():
                ada_titik = True
                self._maju()
            else:
                break

        teks = self.source[awal: self.pos].replace("_", "")
        nilai: int | float = float(teks) if ada_titik else int(teks)
        return Token(TipeToken.ANGKA, nilai, b, k)

    def _baca_nama(self) -> Token:
        """
        Membaca identifier. Jika cocok dengan kata kunci Bahasa Indonesia,
        tipe token disesuaikan dan nilai dipetakan ke padanan Python.
        """
        b, k = self.baris, self.kolom
        awal = self.pos

        while self.pos < len(self.source):
            c = self._karakter()
            if c.isalnum() or c == '_':
                self._maju()
            else:
                break

        teks = self.source[awal: self.pos]

        # Kata kunci Bahasa Indonesia → Python
        if teks in KEYWORD_SET:
            padanan = KEYWORDS[teks]
            if padanan == "True":
                return Token(TipeToken.BENAR, teks, b, k)
            if padanan == "False":
                return Token(TipeToken.SALAH, teks, b, k)
            if padanan == "None":
                return Token(TipeToken.KOSONG, teks, b, k)
            return Token(TipeToken.KATA_KUNCI, padanan, b, k)

        # Kata kunci Python bawaan yang boleh dipakai langsung
        PYTHON_KW = {
            "True", "False", "None", "and", "or", "not",
            "in", "is", "lambda", "yield", "global", "nonlocal",
            "del", "pass", "assert", "raise", "with", "as",
            "import", "from", "def", "class", "return",
            "if", "elif", "else", "while", "for", "break",
            "continue", "try", "except", "finally",
        }
        if teks in PYTHON_KW:
            if teks == "True":
                return Token(TipeToken.BENAR, teks, b, k)
            if teks == "False":
                return Token(TipeToken.SALAH, teks, b, k)
            if teks == "None":
                return Token(TipeToken.KOSONG, teks, b, k)
            return Token(TipeToken.KATA_KUNCI, teks, b, k)

        return Token(TipeToken.NAMA, teks, b, k)

    # ── Utilitas ──────────────────────────────────────────────────────────────

    def _karakter(self) -> str:
        """Karakter pada posisi saat ini (tanpa maju)."""
        return self.source[self.pos] if self.pos < len(self.source) else '\x00'

    def _intip(self, offset: int = 1) -> str:
        """Intip karakter ke depan tanpa menggerakkan posisi."""
        p = self.pos + offset
        return self.source[p] if p < len(self.source) else '\x00'

    def _maju(self) -> None:
        """Gerakkan posisi satu karakter ke depan."""
        self.pos += 1
        self.kolom += 1

    def _lewati_komentar(self) -> None:
        """Lewati semua karakter sampai akhir baris."""
        while self.pos < len(self.source) and self.source[self.pos] != '\n':
            self._maju()

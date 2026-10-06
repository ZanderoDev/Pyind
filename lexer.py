"""
lexer.py — Tokenizer (analisis leksikal) untuk Pyind.
Bagian dari proyek Pyind (Python Indonesia).

Mengubah teks ``.pyind`` menjadi aliran token. Tahapan ini hanya
membaca karakter; tidak ada struktur sintaks yang dipahami di sini.

Sifat penting:

* **Iteratif.** Token dihasilkan oleh :meth:`Lexer.tokenisasi` yang
  memakai loop dan generator — tanpa rekursi. Program arbitrarily
  panjang tidak akan menyebabkan ``RecursionError``.
* **Aman terhadap string & komentar.** Isi string dan komentar tidak
  pernah dipetakan ke kata kunci, jadi ``cetak("jika hujan")`` tetap
  utuh.
* **Bentuk sumber angka & string dipertahankan.** Token menyimpan
  ``teks_asli`` sehingga transpiler bisa menulis ulang literal apa
  adanya (``0x_1f``, ``1_000``, ``rb"ab"``).

Rujukan: https://docs.python.org/3/reference/lexical_analysis.html
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Iterator

from keywords import (
    KATA_KUNCI_KHUSUS,
    KATA_KUNCI_KHUSUS_SET,
    KATA_KUNCI_KONTEKSTUAL,
    KATA_KUNCI_PYTHON,
    ONE_CHAR_OPS,
    THREE_CHAR_OPS,
    TWO_CHAR_OPS,
)
from errors import (
    err_angka_tidak_valid,
    err_dedent_tak_cocok,
    err_indent_tak_terduga,
    err_karakter_tak_dikenal,
    err_string_tidak_ditutup,
)

#: Lebar kolom untuk satu tab, mengikuti aturan Python.
LEBAR_TAB = 8

#: Sufiks penanda bilangan imajiner (kompleks).
SUFIKS_KOMPLEKS = "jJ"

#: Huruf yang boleh menjadi bagian prefiks string.
HURUF_PREFIX = "bBfFrRtTuU"


class TipeToken(Enum):
    """Jenis setiap token hasil analisis leksikal."""

    # Literal nilai
    ANGKA      = auto()   # 42, 3.14, 1_000, 0x1f, 2j
    TEKS       = auto()   # "halo", 'dunia', rb"ab", """ blok """
    BENAR      = auto()   # True / benar
    SALAH      = auto()   # False / salah
    KOSONG     = auto()   # None / kosong

    # Nama & kata kunci
    NAMA       = auto()   # identifier
    KATA_KUNCI = auto()   # kata kunci (nilai = padanan Python)

    # Operator & tanda baca
    OP         = auto()   # operator dan delimiter simbolik
    DELIMITER  = auto()   # tanda baca (, : [ ] { })

    # Struktur baris
    BARIS_BARU = auto()   # akhir pernyataan logis
    INDENT     = auto()   # naik level indentasi
    DEDENT     = auto()   # turun level indentasi

    # Akhir
    EOF        = auto()   # akhir berkas


class Token:
    """
    Satu unit leksikal.

    Atribut:

    ``tipe``
        :class:`TipeToken` dari token ini.
    ``nilai``
        Untuk kata kunci: padanan Python (``"cetak"`` → ``"print"``).
        Untuk angka: nilai Python-nya (``int``/``float``/``complex``).
        Untuk token lain: teks mentahnya.
    ``teks_asli``
        Teks persis seperti ditulis di sumber. Untuk kata kunci ini
        invaluable: ``cetak`` tetap ``cetak``, bukan ``print``.
    ``baris``/``kolom``
        Posisi awal (1-based).
    ``baris_akhir``/``kolom_akhir``
        Posisi akhir (1-based, inklusif) untuk diagnostik.
    """

    __slots__ = ("tipe", "nilai", "baris", "kolom", "baris_akhir", "kolom_akhir", "teks_asli")

    def __init__(
        self,
        tipe: TipeToken,
        nilai: str | int | float | complex,
        baris: int = 0,
        kolom: int = 0,
        teks_asli: str | None = None,
        baris_akhir: int | None = None,
        kolom_akhir: int | None = None,
    ) -> None:
        self.tipe = tipe
        self.nilai = nilai
        self.baris = baris
        self.kolom = kolom
        self.baris_akhir = baris if baris_akhir is None else baris_akhir
        self.kolom_akhir = kolom if kolom_akhir is None else kolom_akhir
        self.teks_asli = nilai if teks_asli is None else teks_asli

    def __repr__(self) -> str:
        return (
            f"Token({self.tipe.name}, {self.nilai!r}, "
            f"b{self.baris}:k{self.kolom})"
        )


# ── Bantuan karakter ────────────────────────────────────────────────────────

def _mulai_valid(karakter: str) -> bool:
    """True bila karakter boleh memulai identifier (XID_Start atau '_')."""
    return ("_" + karakter).isidentifier()


def _lanjut_valid(karakter: str) -> bool:
    """True bila karakter boleh melanjutkan identifier (XID_Continue)."""
    return ("a" + karakter).isidentifier()


class Lexer:
    """
    Mengubah teks sumber menjadi daftar :class:`Token`.

    Contoh::

        tokens = Lexer('cetak("halo")').tokenisasi()
    """

    def __init__(self, source: str, nama_berkas: str | None = None) -> None:
        self.source = source
        self.nama_berkas = nama_berkas
        self.pos = 0
        self.baris = 1
        self.kolom = 1
        # Tumpukan indentasi kolom absolut; element pertama selalu 0.
        self._tumpukan_indent: list[int] = [0]
        # Kedalaman tanda kurung/siku/kurawal: menahan NEWLINE di dalamnya.
        self._kedalaman_tanda: list[str] = []
        # Benar setelah baris berkonten pertama ditemukan.
        self._sudah_baris_pertama = False
        # -*- uzup nama berkas ke pesan error.
        self._kw_error: dict[str, object] = {"berkas": nama_berkas, "sumber": source} if nama_berkas else {}

    # ── API publik ────────────────────────────────────────────────────────────

    def tokenisasi(self) -> list[Token]:
        """Jalankan analisis leksikal penuh dan kembalikan daftar token."""
        return list(self._alir_token())

    #: Alias kompatibilitas ke API Inggris.
    tokenize = tokenisasi

    def __iter__(self) -> Iterator[Token]:
        """Lexer dapat diiterasi langsung, sama dengan hasil tokenisasi()."""
        return self._alir_token()

    # ── Generator utama (iteratif) ────────────────────────────────────────────

    def _alir_token(self) -> Iterator[Token]:
        """
        Hasilkan token satu per satu (iteratif, tanpa rekursi).

        Alur per iterasi: ukur indentasi bila di awal baris → baca satu token
        → majukan kursor.
        """
        awal_baris = True
        panjang = len(self.source)

        while self.pos < panjang:
            if awal_baris:
                awal_baris = False
                for tok in self._proses_indentasi():
                    yield tok
                continue

            karakter = self._karakter()

            # Spasi di tengah baris
            if karakter in (" ", "\t", "\f"):
                self._maju()
                continue

            # Baris baru logis (di luar kurung)
            if karakter in ("\r", "\n"):
                baris_awal, kolom_awal = self.baris, self.kolom
                self._maju_baris_baru()
                if not self._kedalaman_tanda:
                    yield Token(
                        TipeToken.BARIS_BARU, "\n", baris_awal, kolom_awal,
                        baris_akhir=baris_awal, kolom_akhir=kolom_awal,
                    )
                    awal_baris = True
                continue

            # Lanjutan baris eksplisit (backslash di akhir baris)
            if karakter == "\\" and self._intip(1) == "\n":
                self._maju()
                self._maju_baris_baru()
                continue

            # Komentar
            if karakter == "#":
                self._lewati_komentar()
                continue

            # String: dengan atau tanpa prefiks gabungan
            if karakter in ('"', "'"):
                yield self._baca_string("")
                continue
            prefiks = self._coba_prefiks_string()
            if prefiks is not None:
                yield self._baca_string(prefiks)
                continue

            # Angka
            if karakter.isascii() and karakter.isdigit():
                yield self._baca_angka()
                continue
            if karakter == "." and self._intip(1).isascii() and self._intip(1).isdigit():
                yield self._baca_angka()
                continue

            # Identifier / kata kunci
            if _mulai_valid(karakter):
                yield self._baca_nama()
                continue

            # Operator & delimiter: longest-match-first
            tiga = self._potongan(3)
            if tiga in THREE_CHAR_OPS:
                yield self._buat_op(tiga, 3)
                continue
            dua = self._potongan(2)
            if dua in TWO_CHAR_OPS:
                yield self._buat_op(dua, 2)
                continue
            if karakter in ONE_CHAR_OPS:
                yield self._buat_op(karakter, 1)
                continue
            if karakter in ("(", ")", "[", "]", "{", "}"):
                yield self._baca_tanda(karakter)
                continue
            if karakter in (",", ":", ".", ";"):
                yield Token(
                    TipeToken.DELIMITER, karakter, self.baris, self.kolom,
                    baris_akhir=self.baris, kolom_akhir=self.kolom,
                )
                self._maju()
                continue

            raise err_karakter_tak_dikenal(karakter, self.baris, self.kolom, **self._kw_error)

        # Tutup indentasi yang masih terbuka
        while len(self._tumpukan_indent) > 1:
            self._tumpukan_indent.pop()
            yield self._token_struktur(TipeToken.DEDENT, "DEDENT")

        # Baris baru virtual bila berkas tidak diakhiri newline
        if self._baris_terakhir_ada_isi():
            yield Token(
                TipeToken.BARIS_BARU, "\n", self.baris, max(1, self.kolom),
                baris_akhir=self.baris, kolom_akhir=max(1, self.kolom),
            )

        yield self._token_struktur(TipeToken.EOF, "EOF")

    # ── Indentasi ─────────────────────────────────────────────────────────────

    def _proses_indentasi(self) -> Iterator[Token]:
        """
        Lewati spasi/komentar/baris kosong di awal baris, lalu hasilkan
        INDENT/DEDENT bila level indentasi berubah.

        Baris kosong dan baris komentar tidak menghasilkan token dan tidak
        mengubah level indentasi.
        """
        while self.pos < len(self.source):
            karakter = self._karakter()

            if karakter in (" ", "\t", "\f"):
                lebar = self._lewati_spasi_indentasi()
                # Baris kosong: abaikan tanpa mengubah level
                if self._karakter() in ("\r", "\n"):
                    self._maju_baris_baru()
                    continue
                if self._karakter() == "#":
                    self._lewati_komentar()
                    continue
                if self.pos >= len(self.source):
                    return
                for tok in self._cocok_indent(lebar):
                    yield tok
                return

            if karakter == "#":
                self._lewati_komentar()
                continue

            if karakter in ("\r", "\n"):
                self._maju_baris_baru()
                continue

            # Baris tanpa spasi di depan
            for tok in self._cocok_indent(0):
                yield tok
            return

    def _lewati_spasi_indentasi(self) -> int:
        """
        Lewati seluruh spasi/tab/formfeed di awal baris; kembalikan lebarnya.

        Tab dihitung kelipatan :data:`LEBAR_TAB`, persis aturan Python, sehingga
        ``\t`` dan ``        `` (8 spasi) dianggap level indentasi yang sama.
        """
        lebar = 0
        while self.pos < len(self.source):
            karakter = self._karakter()
            if karakter == " ":
                lebar += 1
            elif karakter == "\t":
                lebar = (lebar // LEBAR_TAB + 1) * LEBAR_TAB
            elif karakter == "\f":
                lebar = 0
            else:
                break
            self._maju()
        return lebar

    def _cocok_indent(self, lebar: int) -> Iterator[Token]:
        """Bandingkan lebar indentasi dengan tumpukan; hasilkan INDENT/DEDENT."""
        # Indentasi pada baris pertama tidak punya blok induk
        if not self._sudah_baris_pertama and lebar > 0:
            raise err_indent_tak_terduga(self.baris, self.kolom, **self._kw_error)
        self._sudah_baris_pertama = True

        sebelumnya = self._tumpukan_indent[-1]

        if lebar > sebelumnya:
            self._tumpukan_indent.append(lebar)
            yield self._token_struktur(TipeToken.INDENT, "INDENT")
            return

        while self._tumpukan_indent and self._tumpukan_indent[-1] > lebar:
            self._tumpukan_indent.pop()
            yield self._token_struktur(TipeToken.DEDENT, "DEDENT")

        if self._tumpukan_indent[-1] != lebar:
            raise err_dedent_tak_cocok(self.baris, self.kolom, **self._kw_error)

    # ── Pembacaan token ───────────────────────────────────────────────────────

    def _baca_tanda(self, karakter: str) -> Token:
        """Baca tanda kurung/siku/kurawal dan lacak kedalaman nesting."""
        b, k = self.baris, self.kolom
        if karakter in "([{":
            self._kedalaman_tanda.append(karakter)
        else:
            if self._kedalaman_tanda:
                pasangan = {"(": ")", "[": "]", "{": "}"}[self._kedalaman_tanda[-1]]
                if karakter == pasangan:
                    self._kedalaman_tanda.pop()
        self._maju()
        return Token(
            TipeToken.DELIMITER, karakter, b, k,
            baris_akhir=b, kolom_akhir=k,
        )

    def _buat_op(self, teks: str, panjang: int) -> Token:
        """Buat token operator sepanjang ``panjang`` karakter."""
        b, k = self.baris, self.kolom
        for _ in range(panjang):
            self._maju()
        return Token(
            TipeToken.OP, teks, b, k,
            baris_akhir=b, kolom_akhir=k - 1 if panjang == 1 else k + panjang - 2,
        )

    def _coba_prefiks_string(self) -> str | None:
        """
        Deteksi prefiks string gabungan lalu gerakinya.

        Mengembalikan teks prefiks (``""`` jika tanpa prefiks) atau ``None``
        bila posisi ini bukan awal literal string. Satu prefiks，最多 dua huruf
        (``rb``/``br``/``fr``/``rf``) — lihat
        https://docs.python.org/3/reference/lexical_analysis.html#string-prefixes
        """
        if self._karakter() not in HURUF_PREFIX:
            return None

        awal = self.pos
        # Coba dua huruf lebih dulu agar 'rb' tidak salah baca sebagai nama.
        if self._intip(1) in HURUF_PREFIX and self._intip(2) in ('"', "'"):
            self._maju()
            self._maju()
            return self.source[awal:self.pos]
        if self._intip(1) in ('"', "'"):
            self._maju()
            return self.source[awal:self.pos]
        return None

    def _baca_string(self, prefiks: str) -> Token:
        """
        Baca satu literal string lengkap (dengan prefiks bila ada).

        Teks sumber disimpan apa adanya di ``Token.teks_asli`` — tidak ada
        terjemahan di dalamnya. Validasi prefiks ``rb/br/fr/rf`` memakai
        https://docs.python.org/3/reference/lexical_analysis.html#string-prefixes
        """
        b_awal, k_awal = self.baris, self.kolom
        prefiks_cek = prefiks.lower()

        if prefiks_cek:
            if len(prefiks_cek) > 2:
                raise err_karakter_tak_dikenal(prefiks[2], b_awal, k_awal + 2, **self._kw_error)
            huruf = set(prefiks_cek)
            if huruf - set("brftu"):
                raise err_karakter_tak_dikenal(prefiks, b_awal, k_awal, **self._kw_error)
            if "u" in huruf and len(huruf) > 1:
                raise err_karakter_tak_dikenal(prefiks, b_awal, k_awal, **self._kw_error)
            if huruf == {"b", "f"} or huruf == {"b", "t"} or huruf == {"f", "t"}:
                raise err_karakter_tak_dikenal(prefiks, b_awal, k_awal, **self._kw_error)

        mentah = "r" in prefiks_cek
        pembuka = self._karakter()
        self._maju()

        # Triple-quote?
        if self._potongan(2) == pembuka * 2:
            self._maju()
            self._maju()
            return self._baca_isi_string(prefiks, pembuka, 3, mentah, b_awal, k_awal)

        return self._baca_isi_string(prefiks, pembuka, 1, mentah, b_awal, k_awal)

    def _baca_isi_string(
        self,
        prefiks: str,
        pembuka: str,
        panjang_pembuka: int,
        mentah: bool,
        b_awal: int,
        k_awal: int,
    ) -> Token:
        """Telusuri isi string sampai penutup; kumpulkan teks sumber utuh."""
        penutup = pembuka * panjang_pembuka
        sumber = self.source
        panjang = len(sumber)
        awal_isi = self.pos
        setelah_isi = None
        b_akhir, k_akhir = b_awal, k_awal + len(prefiks) + panjang_pembuka

        while self.pos < panjang:
            karakter = sumber[self.pos]
            if karakter == "\n":
                if panjang_pembuka == 1:
                    # String satu baris tidak boleh memuat baris baru
                    raise err_string_tidak_ditutup(b_awal, k_awal, **self._kw_error)
                self._maju_baris_baru()
                k_akhir = self.kolom - 1
                continue
            if panjang_pembuka == 1 and karakter == "\\":
                # Escape: karakter berikutnyataken apa adanya
                self._maju()
                if self.pos >= panjang:
                    raise err_string_tidak_ditutup(b_awal, k_awal, **self._kw_error)
                if sumber[self.pos] == "\n":
                    self._maju_baris_baru()
                    k_akhir = self.kolom - 1
                    continue
                self._maju()
                k_akhir = self.kolom
                continue
            if sumber.startswith(penutup, self.pos):
                setelah_isi = self.pos
                for _ in range(panjang_pembuka):
                    self._maju()
                b_akhir = self.baris
                k_akhir = self.kolom - 1
                break
            self._maju()
            k_akhir = self.kolom

        if setelah_isi is None:
            raise err_string_tidak_ditutup(b_awal, k_awal, **self._kw_error)

        isi = sumber[awal_isi:setelah_isi]
        teks = prefiks + sumber[awal_isi - panjang_pembuka: self.pos]
        return Token(
            TipeToken.TEKS, teks, b_awal, k_awal,
            teks_asli=teks, baris_akhir=b_akhir, kolom_akhir=k_akhir,
        )

    def _baca_angka(self) -> Token:
        """
        Baca literal angka: desimal, biner, oktal, heksa, float, imajiner.

        Mengikuti grammar resmi Python: underscore hanya boleh di antara
        digit, `0` di depan angka desimal non-nol ditolak, dan tanda `-`
        bukan bagian literal (itu unary operator).
        """
        b, k = self.baris, self.kolom
        awal = self.pos
        sumber = self.source
        panjang = len(sumber)
        imajiner = False

        karakter = self._karakter()
        basis = 0

        # Basis khusus: 0b / 0o / 0x
        if karakter == "0" and self._intip(1) in "bBoOxX":
            basis_char = self._intip(1).lower()
            basis = {"b": 2, "o": 8, "x": 16}[basis_char]
            self._maju()
            self._maju()
            self._maju_underscore_awal()
            digit_awal = self.pos
            self._maju_digit_basis(basis)
            if self.pos == digit_awal:
                raise err_angka_tidak_valid(
                    sumber[awal:self.pos], b, k,
                    f'tidak ada digit {basis_char} setelah prefiks', **self._kw_error,
                )
        else:
            # Desimal / float
            self._maju_digit_desimal()
            if self._karakter() == ".":
                self._maju()
                self._maju_digit_desimal()
            huruf = self._karakter()
            if huruf in "eE":
                self._maju()
                if self._karakter() in "+-":
                    self._maju()
                awal_eksponen = self.pos
                self._maju_digit_desimal()
                if self.pos == awal_eksponen:
                    raise err_angka_tidak_valid(
                        sumber[awal:self.pos], b, k,
                        "eksponen tidak punya digit", **self._kw_error,
                    )

        # Suffix imajiner
        if self._karakter() in SUFIKS_KOMPLEKS:
            imajiner = True
            self._maju()

        teks = sumber[awal:self.pos]

        # Nol di depan tidak valid: 0123, 00 -> error
        if basis == 0 and not imajiner and teks[0] == "0" and len(teks) > 1:
            if teks.isdigit() or (teks[0] == "0" and teks[1].isdigit()):
                raise err_angka_tidak_valid(
                    teks, b, k,
                    "nol di depan tidak diperbolehkan (gunakan 0o untuk oktal)",
                    **self._kw_error,
                )

        # Batas token: huruf/underscore langsung setelah angka = salah
        if self._karakter() not in ("", "\x00", " ", "\t", "\n", "\r", "\f", ")", "]", "}", ",", ";", ":"):
            if self.pos < panjang and (_lanjut_valid(self._karakter()) or self._karakter().isascii() and self._karakter().isalnum()):
                raise err_angka_tidak_valid(
                    teks, b, k,
                    f"karakter {self._karakter()!r} langsung setelah angka",
                    **self._kw_error,
                )

        nilai = self._nilai_angka(teks, imajiner, b, k)
        return Token(
            TipeToken.ANGKA, nilai, b, k,
            teks_asli=teks, baris_akhir=b, kolom_akhir=k + len(teks) - 1,
        )

    def _maju_digit_desimal(self) -> None:
        """Maju sambil menerima digit desimal dengan underscore di antaranya."""
        self._maju_underscore_awal()
        while self.pos < len(self.source):
            karakter = self._karakter()
            if karakter.isascii() and karakter.isdigit():
                self._maju()
                self._maju_underscore_akhir()
            else:
                break

    def _maju_digit_basis(self, basis: int) -> None:
        """Maju sambil menerima digit sesuai ``basis`` (2, 8, atau 16)."""
        while self.pos < len(self.source):
            karakter = self._karakter().lower()
            if karakter == "_":
                self._maju()
                continue
            nilai_digit = self._nilai_digit(karakter, basis)
            if nilai_digit is None:
                break
            self._maju()

    def _maju_underscore_awal(self) -> None:
        """Lewati satu underscore tepat setelah prefiks basis (``0x_1f``)."""
        if self._karakter() == "_":
            self._maju()

    def _maju_underscore_akhir(self) -> None:
        """Konsumsi underscore bila diikuti digit (batas token angka)."""
        if self._karakter() == "_":
            intip = self._intip(1)
            if intip.isascii() and intip.isdigit():
                self._maju()
                if self._karakter() == "_":
                    raise err_angka_tidak_valid(
                        self.source[:self.pos + 1], self.baris, self.kolom,
                        "underscore ganda tidak diperbolehkan", **self._kw_error,
                    )

    @staticmethod
    def _nilai_digit(karakter: str, basis: int) -> int | None:
        """Nilai digit dalam basis tertentu, atau None bila bukan digit."""
        if "0" <= karakter <= "9":
            return ord(karakter) - 48
        if "a" <= karakter <= "f":
            return ord(karakter) - 87
        return None

    def _nilai_angka(self, teks: str, imajiner: bool, b: int, k: int) -> int | float | complex:
        """Ubah teks sumber literal menjadi nilai Python."""
        bersih = teks.replace("_", "")
        try:
            if imajiner:
                return complex(bersih)
            huruf = bersih[:2].lower()
            if huruf in ("0b", "0o", "0x"):
                return int(bersih, {"0b": 2, "0o": 8, "0x": 16}[huruf])
            if "." in bersih or "e" in bersih.lower():
                return float(bersih)
            return int(bersih)
        except ValueError:
            raise err_angka_tidak_valid(teks, b, k, "tidak dapat dibaca sebagai angka", **self._kw_error) from None

    def _baca_nama(self) -> Token:
        """
        Baca identifier lalu tandai sebagai kata kunci bila perlu.

        Kata kunci Indonesia menghasilkan :attr:`TipeToken.KATA_KUNCI` dengan
        ``nilai`` = padanan Python dan ``teks_asli`` = ejaan Indonesia.
        Soft keyword (``cetak``, ``panjang``, …) juga ditandai KATA_KUNCI;
        parser yang memutuskan apakah itu nama atau pemanggilan builtin.
        """
        b, k = self.baris, self.kolom
        awal = self.pos
        self._maju()
        while self.pos < len(self.source):
            karakter = self._karakter()
            if karakter == "_" or karakter.isascii() and karakter.isdigit() or _lanjut_valid(karakter):
                self._maju()
            else:
                break
        teks = self.source[awal:self.pos]

        if teks in KATA_KUNCI_KHUSUS_SET:
            padanan = KATA_KUNCI_KHUSUS[teks]
            if padanan == "True":
                tipe = TipeToken.BENAR
            elif padanan == "False":
                tipe = TipeToken.SALAH
            elif padanan == "None":
                tipe = TipeToken.KOSONG
            else:
                tipe = TipeToken.KATA_KUNCI
            return Token(tipe, padanan, b, k, teks_asli=teks, baris_akhir=b, kolom_akhir=k + len(teks) - 1)

        if teks in KATA_KUNCI_KONTEKSTUAL:
            return Token(
                TipeToken.KATA_KUNCI, KATA_KUNCI_KONTEKSTUAL[teks], b, k,
                teks_asli=teks, baris_akhir=b, kolom_akhir=k + len(teks) - 1,
            )

        if teks in ("True", "False", "None"):
            tipe = {"True": TipeToken.BENAR, "False": TipeToken.SALAH, "None": TipeToken.KOSONG}[teks]
            return Token(tipe, teks, b, k, teks_asli=teks, baris_akhir=b, kolom_akhir=k + len(teks) - 1)

        if teks in KATA_KUNCI_PYTHON:
            return Token(
                TipeToken.KATA_KUNCI, teks, b, k,
                teks_asli=teks, baris_akhir=b, kolom_akhir=k + len(teks) - 1,
            )

        return Token(
            TipeToken.NAMA, teks, b, k,
            teks_asli=teks, baris_akhir=b, kolom_akhir=k + len(teks) - 1,
        )

    # ── Utilitas ──────────────────────────────────────────────────────────────

    def _karakter(self) -> str:
        """Karakter pada posisi sekarang, atau NUL bila di akhir."""
        return self.source[self.pos] if self.pos < len(self.source) else "\x00"

    def _intip(self, jarak: int = 1) -> str:
        """Karakter ``jarak`` posisi ke depan tanpa bergerak."""
        posisi = self.pos + jarak
        return self.source[posisi] if posisi < len(self.source) else "\x00"

    def _potongan(self, panjang: int) -> str:
        """Potongan sumber sepanjang ``panjang`` karakter."""
        return self.source[self.pos:self.pos + panjang]

    def _maju(self) -> None:
        """Geser satu karakter ke depan (memperbarui kolom)."""
        if self.pos < len(self.source):
            karakter = self.source[self.pos]
            self.pos += 1
            if karakter == "\t":
                self.kolom += LEBAR_TAB - ((self.kolom - 1) % LEBAR_TAB)
            elif karakter == "\n" or karakter == "\r":
                pass
            else:
                self.kolom += 1

    def _maju_baris_baru(self) -> None:
        """Lewati satu baris baru (LF atau CRLF) dan reset kolom ke 1."""
        if self.pos < len(self.source):
            karakter = self.source[self.pos]
            if karakter == "\r" and self._intip(1) == "\n":
                self.pos += 2
            elif karakter in "\r\n":
                self.pos += 1
            self.baris += 1
        self.kolom = 1

    def _lewati_komentar(self) -> None:
        """Lewati karakter hingga baris baru berikutnya (tanpa memakainya)."""
        while self.pos < len(self.source) and self.source[self.pos] not in "\r\n":
            self._maju()

    def _token_struktur(self, tipe: TipeToken, nilai: str) -> Token:
        """Buat token struktural (INDENT/DEDENT/EOF) pada posisi sekarang."""
        return Token(
            tipe, nilai, self.baris, max(1, self.kolom),
            baris_akhir=self.baris, kolom_akhir=max(1, self.kolom),
        )

    def _baris_terakhir_ada_isi(self) -> bool:
        """True bila sumber berakhir pada karakter non-spasi."""
        if not self.source:
            return False
        return self.source[-1] not in ("\n", "\r", "\f", " ", "\t")


# ── Pintasan tingkat modul ──────────────────────────────────────────────────

def tokenisasi(source: str, nama_berkas: str | None = None) -> list[Token]:
    """Shortcut modul: tokenisasi ``source`` menjadi daftar token."""
    return Lexer(source, nama_berkas).tokenisasi()


#: Alias kompatibilitas ke API Inggris.
tokenize = tokenisasi

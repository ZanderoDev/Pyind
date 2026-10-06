"""
parser.py — Parser Pyind: token menjadi AST.
Bagian dari proyek Pyind (Python Indonesia).

Menggunakan *recursive descent* (descend rekursif): setiap level operator
punya metode sendiri sehingga urutan presedensi jelas terbaca di kode.
Hasilnya pohon AST berupa ``dict`` sederhana dengan kunci ``"jenis"``.

Konvensi penting
----------------

* Nama identifier diambil dari ``Token.teks_asli``, bukan ``Token.nilai``.
  Jadi penulisan ``fungsi cetak():`` menghasilkan fungsi bernama ``cetak``,
  bukan ``print`` —_resolution_ alias builtin diserahkan ke transpiler.
* Kata kunci kontekstual (``cetak``, ``dalam``, ``panjang``, …) boleh
  identifier; pemakainya sebagai builtin diputuskan parser/transpiler.
* Semuasimpul menyimpan ``baris`` untuk diagnostik yang lebih baik.
"""

from __future__ import annotations

from typing import Any

from lexer import Lexer, Token, TipeToken
from errors import (
    err_ekspresi_diharapkan,
    err_kata_kunci_sebagai_nama,
    err_token_diharapkan,
)
from keywords import KATA_KUNCI_KHUSUS, KATA_KUNCI_KONTEKSTUAL

#: Alias tipe untuk simpul AST.
Simpul = dict[str, Any]

#: Operator perbandingan (termasuk uji keanggotaan & identitas).
OPERATOR_PERBANDINGAN: frozenset[str] = frozenset(
    {"==", "!=", "<", ">", "<=", ">=", "in", "not in", "is", "is not"}
)

#: Operator penugasan gabungan.
OPERATOR_GABUNGAN: frozenset[str] = frozenset(
    {"+=", "-=", "*=", "/=", "%=", "**=", "//=", "&=", "|=", "^=", "<<=", ">>=", "@="}
)


class Parser:
    """
    Mengubah daftar :class:`~lexer.Token` menjadi AST.

    Contoh::

        tokens = Lexer(source).tokenisasi()
        ast = Parser(tokens).urai()
    """

    def __init__(self, tokens: list[Token], nama_berkas: str | None = None) -> None:
        self.tokens = tokens
        self.pos = 0
        self.nama_berkas = nama_berkas
        self._sumber_kw: dict[str, object] = {"berkas": nama_berkas} if nama_berkas else {}

    # ── API publik ────────────────────────────────────────────────────────────

    def urai(self) -> Simpul:
        """Urai seluruh program; kembalikan simpul ``Modul``."""
        tubuh = self._urai_blok_modul()
        return {"jenis": "Modul", "tubuh": tubuh}

    #: Alias kompatibilitas ke API Inggris.
    parse = urai

    # ── Navigasi token ────────────────────────────────────────────────────────

    def _saat_ini(self) -> Token:
        return self.tokens[self.pos]

    def _intip(self, jarak: int = 1) -> Token:
        indeks = self.pos + jarak
        return self.tokens[indeks] if indeks < len(self.tokens) else self.tokens[-1]

    def _maju(self) -> Token:
        """Kembalikan token saat ini lalu geser kursor satu langkah."""
        token = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return token

    def _cocok(self, *nilai_atau_tipe: str) -> Token:
        """
        Pastikan token saat ini cocok dengan salah satu kriteria, lalu maju.

        Kriteria dicocokkan terhadap *nilai* token (``")"``, ``"if"`` …) atau
        *nama tipenya* (``"INDENT"``, ``"DEDENT"``, ``"EOF"``).
        """
        token = self._saat_ini()
        for kriteria in nilai_atau_tipe:
            if self._token_cocok(token, kriteria):
                return self._maju()
        raise err_token_diharapkan(
            " atau ".join(f"{c!r}" for c in nilai_atau_tipe),
            self._label(token),
            token.baris,
            token.kolom,
            **self._sumber_kw,
        )

    def _cocok_maka(self, *nilai_atau_tipe: str) -> bool:
        """Coba cocokkan; kembalikan True dan maju bila berhasil."""
        if self._cocok_saja(*nilai_atau_tipe):
            self._maju()
            return True
        return False

    def _cocok_saja(self, *nilai_atau_tipe: str) -> bool:
        """Periksa kecocokan tanpa bergerak."""
        token = self._saat_ini()
        return any(self._token_cocok(token, kriteria) for kriteria in nilai_atau_tipe)

    @staticmethod
    def _token_cocok(token: Token, kriteria: str) -> bool:
        """
        True bila ``token`` cocok dengan ``kriteria``.

        Token struktural (INDENT/DEDENT/EOF) dicocokkan lewat nama tipe;
        token lainnya lewat nilai (``")"``, ``"if"``, …). Pencocokan lewat
        nilai murni sudah cukup karena nilai token struktural tidak pernah
        bentrok dengan tanda baca.
        """
        if token.tipe in (TipeToken.INDENT, TipeToken.DEDENT, TipeToken.EOF):
            return token.tipe.name == kriteria
        return str(token.nilai) == kriteria

    @staticmethod
    def _label(token: Token) -> str:
        """Nama ramah untuk pesan error: pakai teks asli bila ada."""
        return str(token.teks_asli if token.teks_asli else token.nilai)

    def _cocok_teks(self, teks: str) -> bool:
        """Cocokkan berdasarkan *teks sumber* (mis. ``dalam`` untuk ``in``)."""
        return str(self._saat_ini().teks_asli) == teks

    def _cocok_teks_maka(self, teks: str) -> bool:
        """Cocokkan berdasarkan teks sumber lalu maju bila cocok."""
        if self._cocok_teks(teks):
            self._maju()
            return True
        return False

    def _di_akhir_baris(self) -> bool:
        """True bila pernyataan selesai (baris baru, DEDENT, atau EOF)."""
        return self._saat_ini().tipe in (
            TipeToken.BARIS_BARU,
            TipeToken.INDENT,
            TipeToken.DEDENT,
            TipeToken.EOF,
        )

    # ── Pengambilan nama ──────────────────────────────────────────────────────

    def _bisa_jadi_nama(self, token: Token | None = None, *, teks: bool = False) -> bool:
        """
        True bila token boleh dipakai sebagai identifier.

        Token :attr:`~lexer.TipeToken.NAMA` dan *soft keyword* boleh. Kata
        kunci khusus (``fungsi``, ``jika``, …) tidak — memakai ``fungsi`` sebagai
        nama variabel adalah kesalahan sintaks yang perlu dilaporkan.

        Parameter ``teks`` melonggarkan aturan untuk nama setelah titik
        (``diri.kosong()``). Python sendiri mengizinkan ``None``/``True``
        sebagai nama atribut, jadi literal ``benar``/``salah``/``kosong``
        juga harus sah di posisi itu.
        """
        token = token if token is not None else self._saat_ini()
        if token.tipe is TipeToken.NAMA:
            return True
        if token.tipe is TipeToken.KATA_KUNCI:
            return token.teks_asli in KATA_KUNCI_KONTEKSTUAL
        if teks and token.tipe in (TipeToken.BENAR, TipeToken.SALAH, TipeToken.KOSONG):
            return True
        return False

    def _ambil_nama(self, *, teks: bool = False) -> str:
        """
        Ambil nama identifier dari token saat ini.

        Mengembalikan ``Token.teks_asli`` supaya ejaan Bahasa Indonesia
        tidak berubah jadi padanan Python. Soft keyword yang dipakai sebagai
        nama (``cetak = 1``) diperbolehkan; pemakainya sebagai builtin
        (@:mod:`transpiler`) ditentukan terpisah.
        """
        token = self._saat_ini()
        if not self._bisa_jadi_nama(token, teks=teks):
            if token.tipe is TipeToken.KATA_KUNCI:
                raise err_kata_kunci_sebagai_nama(
                    self._label(token), token.baris, token.kolom, **self._sumber_kw
                )
            raise err_token_diharapkan(
                "nama", self._label(token), token.baris, token.kolom, **self._sumber_kw
            )
        self._maju()
        return str(token.teks_asli if token.teks_asli else token.nilai)

    # ── Blok ──────────────────────────────────────────────────────────────────

    def _lewati_baris_baru(self) -> None:
        while self._saat_ini().tipe is TipeToken.BARIS_BARU:
            self._maju()

    def _urai_blok_modul(self) -> list[Simpul]:
        """Urai daftar pernyataan tingkat modul."""
        pernyataan: list[Simpul] = []
        self._lewati_baris_baru()
        while self._saat_ini().tipe is not TipeToken.EOF:
            pernyataan.extend(self._urai_pernyataan_blok())
            self._lewati_baris_baru()
        return pernyataan

    def _urai_pernyataan_blok(self) -> list[Simpul]:
        """Urai satu atau beberapa pernyataan pada level indentasi ini."""
        hasil: list[Simpul] = []
        while self._saat_ini().tipe not in (TipeToken.DEDENT, TipeToken.EOF):
            sebelum = self.pos
            simpul = self._urai_pernyataan()
            if simpul is not None:
                hasil.append(simpul)
            self._lewati_baris_baru()
            if self.pos == sebelum:
                # Tidak ada kemajuan: cegah putaran tak berakhir.
                token = self._saat_ini()
                if token.tipe in (TipeToken.DEDENT, TipeToken.EOF):
                    break
                raise err_token_diharapkan(
                    "pernyataan", self._label(token),
                    token.baris, token.kolom, **self._sumber_kw,
                )
        return hasil

    def _urai_blok_indent(self) -> list[Simpul]:
        """Urai blok terindentasi setelah tanda ``:``."""
        self._lewati_baris_baru()
        if self._saat_ini().tipe is not TipeToken.INDENT:
            token = self._saat_ini()
            raise err_token_diharapkan(
                "blok terindentasi setelah ':'", self._label(token),
                token.baris, token.kolom, **self._sumber_kw,
            )
        self._maju()
        hasil = self._urai_pernyataan_blok()
        if self._saat_ini().tipe is TipeToken.DEDENT:
            self._maju()
        return hasil

    # ── Pernyataan ────────────────────────────────────────────────────────────

    def _urai_pernyataan(self) -> Simpul | None:
        """Pilih handler pernyataan berdasarkan token saat ini."""
        self._lewati_baris_baru()
        token = self._saat_ini()
        if token.tipe in (TipeToken.EOF, TipeToken.DEDENT, TipeToken.INDENT):
            return None

        # Dekorator: '@nama' di awal baris
        if token.tipe is TipeToken.OP and token.nilai == "@":
            return self._urai_dekorator()

        nilai = str(token.nilai)

        # Kata kunci async/await
        if nilai == "async" and self._intip(1).nilai in ("def", "for", "with"):
            return self._urai_asinkron()
        if nilai == "async":
            return self._urai_pernyataan_ekspresi()

        tabela: dict[str, Any] = {
            "def": self._urai_fungsi,
            "class": self._urai_kelas,
            "if": self._urai_jika,
            "while": self._urai_selama,
            "for": self._urai_untuk,
            "return": self._urai_kembali,
            "import": self._urai_impor,
            "from": self._urai_dari,
            "try": self._urai_coba,
            "del": self._urai_hapus,
            "global": self._urai_global,
            "nonlocal": self._urai_nonlokal,
            "assert": self._urai_pernyataan_kondisi,
            "raise": self._urai_naikkan,
            "with": self._urai_bersama,
            "match": self._urai_cocok_pola,
        }
        if nilai in tabela:
            return tabela[nilai]()

        # Pernyataan sederhana tanpa nilai
        for kata, jenis in (("break", "Hentikan"), ("continue", "Lanjut"), ("pass", "Lewati")):
            if nilai == kata:
                self._maju()
                return {"jenis": jenis, "baris": token.baris}

        return self._urai_ekspresi_atau_penugasan()

    def _urai_dekorator(self) -> list[Simpul]:
        """Urai satu atau lebih dekorator menjadi daftar simpul."""
        dekorator: list[Simpul] = []
        while self._cocok_saja("@"):
            token = self._saat_ini()
            self._maju()
            ekspresi = self._urai_ekspresi()
            dekorator.append({"ekspresi": ekspresi, "baris": token.baris})
            self._lewati_baris_baru()
        # Setelah dekorator wajib pernyataan yang bisa diberi dekorator
        self._lewati_baris_baru()
        token = self._saat_ini()
        target = self._urai_pernyataan()
        if target is None:
            raise err_token_diharapkan(
                "fungsi atau kelas setelah dekorator", self._label(token),
                token.baris, token.kolom, **self._sumber_kw,
            )
        target = dict(target)
        target["dekorator"] = dekorator
        return target

    def _urai_asinkron(self) -> Simpul:
        """Urai ``async fungsi``, ``async untuk``, atau ``async bersama``."""
        async_token = self._cocok("async")
        berikut = self._saat_ini()
        if berikut.nilai == "def":
            simpul = self._urai_fungsi()
            simpul["asinkron"] = True
            simpul["baris"] = async_token.baris
            return simpul
        if berikut.nilai == "for":
            simpul = self._urai_untuk()
            simpul["asinkron"] = True
            simpul["baris"] = async_token.baris
            return simpul
        if berikut.nilai == "with":
            simpul = self._urai_bersama()
            simpul["asinkron"] = True
            simpul["baris"] = async_token.baris
            return simpul
        raise err_token_diharapkan(
            "'fungsi', 'untuk', atau 'bersama' setelah 'async'",
            self._label(berikut), berikut.baris, berikut.kolom, **self._sumber_kw,
        )

    def _urai_ekspresi_atau_penugasan(self) -> Simpul:
        """
        Urai ekspresi solitary atau penugasan.

        Menangani:
        * ``x = nilai`` dan tuple unpacking ``a, b = …``
        * penugasan gabungan ``x += 1``
        * penugasan bertanda ``x: int = 5``
        * penugasan berbintang ``*x, y = data``
        """
        # Penugasan bertanda: nama : anotasi [= nilai]
        if self._bisa_jadi_nama() and self._intip(1).tipe is TipeToken.DELIMITER \
                and self._intip(1).nilai == ":" and not self._di_akhir_baris_setelah(2):
            return self._urai_penugasan_bertanda()

        # Sisi kiri bisa berupa tuple: a, b = ...
        target = self._urai_target_penugasan()

        token = self._saat_ini()

        if token.tipe is TipeToken.OP and token.nilai == "=":
            self._maju()
            nilai = self._urai_ekspresi_dengan_koma()
            return {"jenis": "Penugasan", "target": target, "nilai": nilai, "baris": token.baris}

        if token.tipe is TipeToken.OP and token.nilai in OPERATOR_GABUNGAN:
            self._maju()
            nilai = self._urai_ekspresi_dengan_koma()
            return {
                "jenis": "PenugasanGabungan",
                "op": str(token.nilai),
                "target": target,
                "nilai": nilai,
                "baris": token.baris,
            }

        if token.tipe is TipeToken.OP and token.nilai == ":=":
            self._maju()
            nilai = self._urai_ekspresi()
            return {"jenis": "PenugasanEkspresi", "target": target, "nilai": nilai, "baris": token.baris}

        return {"jenis": "EkspresiPernyataan", "ekspresi": target, "baris": token.baris}

    def _di_akhir_baris_setelah(self, jarak: int) -> bool:
        """True bila token pada jarak tertentu menutup baris."""
        return self._intip(jarak).tipe in (
            TipeToken.BARIS_BARU, TipeToken.DEDENT, TipeToken.EOF
        )

    def _urai_penugasan_bertanda(self) -> Simpul:
        """Urai ``nama: anotasi = nilai``."""
        token = self._saat_ini()
        nama = self._ambil_nama()
        self._cocok(":")
        anotasi = self._urai_ekspresi()
        nilai = None
        if self._cocok_maka("="):
            nilai = self._urai_ekspresi_dengan_koma()
        return {
            "jenis": "PenugasanBertanda",
            "nama": nama,
            "anotasi": anotasi,
            "nilai": nilai,
            "baris": token.baris,
        }

    def _urai_target_penugasan(self) -> Simpul:
        """
        Urai sisi kiri penugasan: nama, atribut, subskrip, atau tuple.

        Berbeda dari ekspresi biasa, target boleh berupa ``*nama`` (unpacking).
        """
        elemen: list[Simpul] = []

        while True:
            if self._cocok_saja("*"):
                self._maju()
                nama = self._ambil_nama()
                elemen.append({"jenis": "Bintang", "nilai": {"jenis": "Nama", "nama": nama}})
            else:
                elemen.append(self._urai_ekspresi())

            if self._cocok_saja(","):
                self._maju()
                # Kurung tutup / baris baru menghentikan tuple
                if self._di_akhir_baris() or self._cocok_saja("="):
                    break
                continue
            break

        if len(elemen) == 1 and elemen[0].get("jenis") != "Bintang":
            return elemen[0]
        return {"jenis": "Tuple", "elemen": elemen}

    def _urai_ekspresi_dengan_koma(self) -> Simpul:
        """Urai ekspresi yang boleh berupa tuple (sisi kanan penugasan)."""
        pertama = self._urai_ekspresi()
        if not self._cocok_saja(","):
            return pertama
        elemen = [pertama]
        while self._cocok_maka(","):
            if self._di_akhir_baris() or self._cocok_saja("=", ")", "]", "}"):
                break
            elemen.append(self._urai_ekspresi())
        return {"jenis": "Tuple", "elemen": elemen}

    # ── Pernyataan terstruktur ────────────────────────────────────────────────

    def _urai_fungsi(self) -> Simpul:
        """Urai definisi fungsi: ``fungsi nama(params) -> anotasi:``."""
        token = self._cocok("def")
        nama = self._ambil_nama(teks=True)
        self._cocok("(")
        parameter = self._urai_daftar_parameter()
        self._cocok(")")

        anotasi_kembali = None
        if self._cocok_saja("->"):
            self._maju()
            anotasi_kembali = self._urai_ekspresi()

        self._cocok(":")
        tubuh = self._urai_blok_indent()
        return {
            "jenis": "DefinisiFungsi",
            "nama": nama,
            "parameter": parameter,
            "kembali_anotasi": anotasi_kembali,
            "tubuh": tubuh,
            "baris": token.baris,
        }

    def _urai_daftar_parameter(self) -> list[Simpul]:
        """
        Urai daftar parameter fungsi.

        Didukung: anotasi, nilai bawaan, ``*args``, ``**kwargs``,
        parameter posisional-only ``/``, dan keyword-only ``*``.

        Pemisah ``/`` dan ``*`` disimpan sebagai entri :data:`PEMISAH` agar
        urutan aslinya terjaga; transpiler hanya perlu merakit ulang sesuai
        urutan kemunculannya.
        """
        parameter: list[Simpul] = []

        while not self._cocok_saja(")") and self._saat_ini().tipe is not TipeToken.EOF:
            token = self._saat_ini()

            # Pemisah posisional-only: '/'
            if token.tipe is TipeToken.OP and token.nilai == "/":
                self._maju()
                parameter.append({"jenis": "PEMISAH", "tanda": "/", "posisi": "posonly"})
                if self._cocok_maka(","):
                    continue
                break

            # '*' pemisah keyword-only, atau '*args'
            if token.tipe is TipeToken.OP and token.nilai == "*":
                self._maju()
                if self._bisa_jadi_nama():
                    parameter.append(self._urai_parameter("positional", "*"))
                else:
                    parameter.append({"jenis": "PEMISAH", "tanda": "*", "posisi": "kwonly"})
                if self._cocok_maka(","):
                    continue
                break

            # '**kwargs'
            if token.tipe is TipeToken.OP and token.nilai == "**":
                self._maju()
                parameter.append(self._urai_parameter("positional", "**"))
                if self._cocok_maka(","):
                    continue
                break

            parameter.append(self._urai_parameter("positional", None))

            if self._cocok_maka(","):
                continue
            break

        # Tandai parameter yang sesudah '/' sebagai posisional biasa
        ada_pemisah_posonly = any(
            p.get("jenis") == "PEMISAH" and p.get("tanda") == "/" for p in parameter
        )
        if ada_pemisah_posonly:
            lewat = False
            for p in parameter:
                if p.get("jenis") == "PEMISAH" and p.get("tanda") == "/":
                    lewat = True
                    continue
                if lewat and p.get("posisi") == "positional" and not p.get("bintang"):
                    p["posisi"] = "setelah_pemisah"

        return parameter

    def _urai_parameter(self, posisi: str, bintang: str | None) -> Simpul:
        """Urai satu parameter beserta anotasi dan nilai bawaannya."""
        nama = self._ambil_nama(teks=True)
        anotasi = None
        nilai = None
        if self._cocok_saja(":"):
            self._maju()
            anotasi = self._urai_ekspresi()
        if self._cocok_saja("="):
            self._maju()
            nilai = self._urai_ekspresi()
        simpul: Simpul = {"nama": nama, "posisi": posisi}
        if bintang:
            simpul["bintang"] = bintang
        if anotasi is not None:
            simpul["anotasi"] = anotasi
        if nilai is not None:
            simpul["nilai_bawaan"] = nilai
        return simpul

    def _urai_kelas(self) -> Simpul:
        """Urai definisi kelas: ``kelas Nama(Induk, ...):``."""
        token = self._cocok("class")
        nama = self._ambil_nama(teks=True)
        induk: list[Simpul] = []
        if self._cocok_maka("("):
            while not self._cocok_saja(")") and self._saat_ini().tipe is not TipeToken.EOF:
                induk.append(self._urai_ekspresi())
                if not self._cocok_maka(","):
                    break
            self._cocok(")")

        self._cocok(":")
        tubuh = self._urai_blok_indent()
        return {
            "jenis": "DefinisiKelas",
            "nama": nama,
            "induk": induk,
            "tubuh": tubuh,
            "baris": token.baris,
        }

    def _urai_jika(self) -> Simpul:
        """Urai ``jika / jika_tidak / lainnya``."""
        token = self._cocok("if")
        kondisi = self._urai_ekspresi_dengan_koma()
        self._cocok(":")
        cabang_then = self._urai_blok_indent()

        elif_cabang: list[Simpul] = []
        self._lewati_baris_baru()
        while self._cocok_saja("elif"):
            self._maju()
            elif_kondisi = self._urai_ekspresi_dengan_koma()
            self._cocok(":")
            elif_cabang.append({"kondisi": elif_kondisi, "tubuh": self._urai_blok_indent()})
            self._lewati_baris_baru()

        else_blok: list[Simpul] = []
        if self._cocok_saja("else"):
            self._maju()
            self._cocok(":")
            else_blok = self._urai_blok_indent()

        return {
            "jenis": "Jika",
            "kondisi": kondisi,
            "then": cabang_then,
            "elif": elif_cabang,
            "else": else_blok,
            "baris": token.baris,
        }

    def _urai_selama(self) -> Simpul:
        """Urai loop ``selama``."""
        token = self._cocok("while")
        kondisi = self._urai_ekspresi_dengan_koma()
        self._cocok(":")
        return {
            "jenis": "Selama",
            "kondisi": kondisi,
            "tubuh": self._urai_blok_indent(),
            "baris": token.baris,
        }

    def _urai_untuk(self) -> Simpul:
        """Urai loop ``untuk … dalam …``."""
        token = self._cocok("for")
        target = self._urai_target_penugasan()
        # 'dalam'/'in' bisa ditulis sebagai soft keyword atau kata kunci Python
        if not (self._cocok_teks_maka("dalam") or self._cocok_maka("in")):
            token_kini = self._saat_ini()
            raise err_token_diharapkan(
                "'dalam' atau 'in'", self._label(token_kini),
                token_kini.baris, token_kini.kolom, **self._sumber_kw,
            )
        iterable = self._urai_ekspresi_dengan_koma()
        self._cocok(":")
        return {
            "jenis": "Untuk",
            "target": target,
            "iterable": iterable,
            "tubuh": self._urai_blok_indent(),
            "baris": token.baris,
        }

    def _urai_kembali(self) -> Simpul:
        """Urai ``kembalikan [nilai]``."""
        token = self._cocok("return")
        nilai = None
        if not self._di_akhir_baris():
            nilai = self._urai_ekspresi_dengan_koma()
        return {"jenis": "Kembali", "nilai": nilai, "baris": token.baris}

    def _urai_impor(self) -> Simpul:
        """Urai ``impor modul [sebagai alias]``."""
        token = self._cocok("import")
        nama = self._urai_nama_titik()
        alias = None
        if self._adalah_alias():
            self._maju()
            alias = self._ambil_nama()
        return {"jenis": "Impor", "nama": nama, "alias": alias, "baris": token.baris}

    def _adalah_alias(self) -> bool:
        """True bila token adalah penanda alias (``sebagai``/``menjadi``/``as``)."""
        return self._cocok_saja("as") or self._cocok_teks("menjadi")

    def _urai_dari(self) -> Simpul:
        """Urai ``dari modul impor a, b [sebagai c]``."""
        token = self._cocok("from")
        modul = self._urai_nama_titik()
        self._cocok("import")

        # Tanda bintang: 'dari modul impor *'
        if self._cocok_saja("*"):
            return {
                "jenis": "DariImpor",
                "modul": modul,
                "nama": [{"nama": "*", "alias": None}],
                "baris": token.baris,
            }

        berkurung = self._cocok_saja("(")
        daftar: list[dict] = []
        while True:
            nama = self._ambil_nama()
            alias = None
            if self._adalah_alias():
                self._maju()
                alias = self._ambil_nama()
            daftar.append({"nama": nama, "alias": alias})
            if self._cocok_saja(","):
                self._maju()
                self._lewati_baris_baru()
                if berkurung and self._cocok_saja(")"):
                    break
                continue
            break
        if berkurung:
            self._cocok(")")
        return {"jenis": "DariImpor", "modul": modul, "nama": daftar, "baris": token.baris}

    def _urai_coba(self) -> Simpul:
        """Urai ``coba / kecuali / lainnya / akhirnya``."""
        token = self._cocok("try")
        self._cocok(":")
        tubuh = self._urai_blok_indent()

        handler: list[Simpul] = []
        self._lewati_baris_baru()
        while self._cocok_saja("except"):
            self._maju()
            tipe_exc = None
            nama_exc = None
            if not self._cocok_saja(":"):
                tipe_exc = self._urai_ekspresi()
                if self._adalah_alias():
                    self._maju()
                    nama_exc = self._ambil_nama()
            self._cocok(":")
            handler.append({"tipe": tipe_exc, "nama": nama_exc, "tubuh": self._urai_blok_indent()})
            self._lewati_baris_baru()

        else_blok: list[Simpul] = []
        if self._cocok_saja("else"):
            self._maju()
            self._cocok(":")
            else_blok = self._urai_blok_indent()
            self._lewati_baris_baru()

        finally_blok: list[Simpul] = []
        if self._cocok_saja("finally"):
            self._maju()
            self._cocok(":")
            finally_blok = self._urai_blok_indent()

        return {
            "jenis": "CobaDanKecuali",
            "tubuh": tubuh,
            "handler": handler,
            "else": else_blok,
            "finally": finally_blok,
            "baris": token.baris,
        }

    def _urai_hapus(self) -> Simpul:
        """Urai ``hapus target``."""
        token = self._cocok("del")
        target = self._urai_ekspresi_dengan_koma()
        return {"jenis": "Hapus", "target": target, "baris": token.baris}

    def _urai_global(self) -> Simpul:
        """Urai ``global a, b``."""
        token = self._cocok("global")
        nama = [self._ambil_nama()]
        while self._cocok_maka(","):
            nama.append(self._ambil_nama())
        return {"jenis": "Global", "nama": nama, "baris": token.baris}

    def _urai_nonlokal(self) -> Simpul:
        """Urai ``nonlokal a, b``."""
        token = self._cocok("nonlocal")
        nama = [self._ambil_nama()]
        while self._cocok_maka(","):
            nama.append(self._ambil_nama())
        return {"jenis": "Nonlokal", "nama": nama, "baris": token.baris}

    def _urai_pernyataan_kondisi(self) -> Simpul:
        """Urai ``pernyataan kondisi [pesan]`` (padanan ``assert``)."""
        token = self._cocok("assert")
        kondisi = self._urai_ekspresi()
        pesan = None
        if self._cocok_saja(","):
            self._maju()
            pesan = self._urai_ekspresi()
        return {"jenis": "Assert", "kondisi": kondisi, "pesan": pesan, "baris": token.baris}

    def _urai_naikkan(self) -> Simpul:
        """Urai ``naikkan [ekspresi]`` atau ``naikkan … dari …``."""
        token = self._cocok("raise")
        ekspresi = None
        penyebab = None
        if not self._di_akhir_baris():
            ekspresi = self._urai_ekspresi()
            if self._cocok_saja("from"):
                self._maju()
                penyebab = self._urai_ekspresi()
        return {"jenis": "Naikkan", "ekspresi": ekspresi, "dari": penyebab, "baris": token.baris}

    def _urai_bersama(self) -> Simpul:
        """Urai ``bersama konteks [sebagai nama]`` (dapat berkoma)."""
        token = self._cocok("with")
        item: list[Simpul] = []

        while True:
            konteks = self._urai_ekspresi()
            nama = None
            if self._adalah_alias():
                self._maju()
                nama = self._ambil_nama()
            item.append({"konteks": konteks, "nama": nama})
            if self._cocok_saja(","):
                self._maju()
                continue
            break

        self._cocok(":")
        return {
            "jenis": "Bersama",
            "item": item,
            "tubuh": self._urai_blok_indent(),
            "baris": token.baris,
        }

    def _urai_cocok_pola(self) -> Simpul:
        """Urai pernyataan ``match`` — memakai padanan Python apa adanya."""
        # Guest: 'match' tetap dieksekusi Python, jadi cukup teruskan.
        token = self._cocok("match")
        subjek = self._urai_ekspresi()
        self._cocok(":")
        return {"jenis": "CocokPola", "subjek": subjek, "tubuh": [], "baris": token.baris}

    # ── Ekspresi (descend rekursif mengikuti presedensi Python) ────────────────

    def _urai_ekspresi(self) -> Simpul:
        """Ekspresi paling atas: lambda, penghasil, atau ekspresi kondisi."""
        if self._cocok_saja("lambda"):
            return self._urai_lambda()
        if self._cocok_saja("yield", "yield_dari"):
            return self._urai_hasil()
        return self._urai_kondisional()

    def _urai_hasil(self) -> Simpul:
        """
        Urai ``hasilkan nilai`` dan ``hasilkan_dari iterable``.

        Padanan Python-nya ``yield`` / ``yield from``.
        """
        token = self._saat_ini()
        dari = str(token.teks_asli) == "hasilkan_dari" or bool(self._cocok_saja("from"))
        self._maju()
        nilai = None
        if not self._di_akhir_baris() and not self._cocok_saja(")"):
            nilai = self._urai_ekspresi_dengan_koma()
        return {
            "jenis": "Hasil",
            "nilai": nilai,
            "dari": dari,
            "baris": token.baris,
        }

    def _urai_lambda(self) -> Simpul:
        """Urai ``lambda params: ekspresi``."""
        token = self._cocok("lambda")
        parameter: list[Simpul] = []
        while not self._cocok_saja(":") and self._saat_ini().tipe is not TipeToken.EOF:
            if self._bisa_jadi_nama():
                parameter.append({"nama": self._ambil_nama(), "posisi": "positional"})
            elif self._cocok_saja("*"):
                self._maju()
                parameter.append({"nama": self._ambil_nama(), "posisi": "kwonly", "bintang": "*"})
            elif self._cocok_saja("**"):
                self._maju()
                parameter.append({"nama": self._ambil_nama(), "posisi": "positional", "bintang": "**"})
            if self._cocok_maka(","):
                continue
            break
        self._cocok(":")
        return {"jenis": "Lambda", "parameter": parameter, "tubuh": self._urai_ekspresi(), "baris": token.baris}

    def _urai_kondisional(self) -> Simpul:
        """Urai ``nilai jika kondisi lainnya alternatif``."""
        nilai = self._urai_atau()
        if self._cocok_saja("if"):
            self._maju()
            kondisi = self._urai_atau()
            if self._cocok_saja("else"):
                self._maju()
                alternatif = self._urai_kondisional()
            else:
                raise err_kata_kunci_sebagai_nama("else", self._saat_ini().baris, self._saat_ini().kolom, **self._sumber_kw)
            return {
                "jenis": "EkspresiKondisi",
                "nilai": nilai,
                "kondisi": kondisi,
                "alternatif": alternatif,
            }
        return nilai

    def _urai_atau(self) -> Simpul:
        kiri = self._urai_dan()
        while self._cocok_saja("or"):
            operator = str(self._maju().nilai)
            kanan = self._urai_dan()
            kiri = {"jenis": "BinOp", "op": operator, "kiri": kiri, "kanan": kanan}
        return kiri

    def _urai_dan(self) -> Simpul:
        kiri = self._urai_bukan()
        while self._cocok_saja("and"):
            operator = str(self._maju().nilai)
            kanan = self._urai_bukan()
            kiri = {"jenis": "BinOp", "op": operator, "kiri": kiri, "kanan": kanan}
        return kiri

    def _urai_bukan(self) -> Simpul:
        """Urai operator logika unary ``bukan``/``not``."""
        if self._cocok_saja("not"):
            operator = str(self._maju().nilai)
            return {"jenis": "UnOp", "op": operator, "operand": self._urai_bukan()}
        return self._urai_perbandingan()

    def _urai_perbandingan(self) -> Simpul:
        """
        Urai perbandingan, termasuk *chaining* ``a < b <= c``.

        Rantai disimpan sebagai :data:`PerbandinganRantai` berisi operand
        pertama lalu tiap pasangan ``(op, operand)``. Transpiler akan
        membangkitkan ulang bentuk ``a < b <= c`` yang ekuivalen secara
        semantik dengan Python (operand tengah dievaluasi satu kali).
        """
        operand_pertama = self._urai_bitor()
        segmen: list[Simpul] = []

        while True:
            token = self._saat_ini()
            operator = self._baca_operator_perbandingan()
            if operator is None:
                break
            segmen.append({
                "op": operator,
                "kanan": self._urai_bitor(),
                "baris": token.baris,
            })

        if not segmen:
            return operand_pertama

        return {
            "jenis": "PerbandinganRantai",
            "awal": operand_pertama,
            "segmen": segmen,
            "baris": segmen[0]["baris"],
        }

    def _baca_operator_perbandingan(self) -> str | None:
        """Baca satu operator perbandingan (termasuk ``not in``/``is not``)."""
        token = self._saat_ini()
        if token.tipe is TipeToken.OP and token.nilai in ("==", "!=", "<", ">", "<=", ">="):
            self._maju()
            return str(token.nilai)
        if token.nilai == "not" and self._intip(1).nilai == "in":
            self._maju()
            self._maju()
            return "not in"
        if token.nilai == "is" and self._intip(1).nilai == "not":
            self._maju()
            self._maju()
            return "is not"
        if token.nilai in ("in", "is"):
            self._maju()
            return str(token.nilai)
        if token.tipe is TipeToken.OP and token.nilai == ":":
            return None
        return None

    def _urai_bitor(self) -> Simpul:
        kiri = self._urai_bitxor()
        while self._cocok_op("|"):
            operator = str(self._maju().nilai)
            kanan = self._urai_bitxor()
            kiri = {"jenis": "BinOp", "op": operator, "kiri": kiri, "kanan": kanan}
        return kiri

    def _urai_bitxor(self) -> Simpul:
        kiri = self._urai_bitand()
        while self._cocok_op("^"):
            operator = str(self._maju().nilai)
            kanan = self._urai_bitand()
            kiri = {"jenis": "BinOp", "op": operator, "kiri": kiri, "kanan": kanan}
        return kiri

    def _urai_bitand(self) -> Simpul:
        kiri = self._urai_geseran()
        while self._cocok_op("&"):
            operator = str(self._maju().nilai)
            kanan = self._urai_geseran()
            kiri = {"jenis": "BinOp", "op": operator, "kiri": kiri, "kanan": kanan}
        return kiri

    def _urai_geseran(self) -> Simpul:
        kiri = self._urai_penjumlahan()
        while self._cocok_op("<<", ">>"):
            operator = str(self._maju().nilai)
            kanan = self._urai_penjumlahan()
            kiri = {"jenis": "BinOp", "op": operator, "kiri": kiri, "kanan": kanan}
        return kiri

    def _urai_penjumlahan(self) -> Simpul:
        kiri = self._urai_perkalian()
        while self._cocok_op("+", "-"):
            operator = str(self._maju().nilai)
            kanan = self._urai_perkalian()
            kiri = {"jenis": "BinOp", "op": operator, "kiri": kiri, "kanan": kanan}
        return kiri

    def _urai_perkalian(self) -> Simpul:
        kiri = self._urai_eksponen()
        while self._cocok_op("*", "/", "//", "%", "@"):
            operator = str(self._maju().nilai)
            kanan = self._urai_eksponen()
            kiri = {"jenis": "BinOp", "op": operator, "kiri": kiri, "kanan": kanan}
        return kiri

    def _cocok_op(self, *nilai: str) -> bool:
        """True bila token saat ini adalah OP dengan salah satu nilai."""
        token = self._saat_ini()
        return token.tipe is TipeToken.OP and str(token.nilai) in nilai

    def _urai_eksponen(self) -> Simpul:
        """
        Pangkat: right-associative (``2**3**2`` = ``2**(3**2)``).

        Sisi kanan diparsing rekursif dengan :meth:`_urai_eksponen`.
        """
        kiri = self._urai_unary()
        if self._cocok_op("**"):
            operator = str(self._maju().nilai)
            kanan = self._urai_eksponen()
            return {"jenis": "BinOp", "op": operator, "kiri": kiri, "kanan": kanan}
        return kiri

    def _urai_unary(self) -> Simpul:
        """Urai operator unary ``-``, ``+``, ``~``, ``bukan``, ``tunggu``."""
        token = self._saat_ini()
        if self._cocok_op("-", "+", "~"):
            operator = str(self._maju().nilai)
            return {"jenis": "UnOp", "op": operator, "operand": self._urai_unary()}
        if self._cocok_saja("await"):
            self._maju()
            return {"jenis": "Tunggu", "operand": self._urai_unary()}
        return self._urai_postfix()

    def _urai_postfix(self) -> Simpul:
        """Urai subscript, slicing, pemanggilan, dan akses atribut."""
        simpul = self._urai_atom()
        while True:
            token = self._saat_ini()

            if token.tipe is TipeToken.DELIMITER and token.nilai == ".":
                self._maju()
                atribut = self._ambil_nama(teks=True)
                simpul = {"jenis": "Atribut", "objek": simpul, "atribut": atribut}
                continue

            if token.tipe is TipeToken.DELIMITER and token.nilai == "[":
                self._maju()
                simpul = self._urai_indeks(simpul)
                continue

            if token.tipe is TipeToken.DELIMITER and token.nilai == "(":
                argumen = self._urai_argumen()
                simpul = {"jenis": "Panggilan", "fungsi": simpul, "argumen": argumen}
                continue

            break
        return simpul

    def _urai_indeks(self, objek: Simpul) -> Simpul:
        """Urai ``[indeks]`` atau ``[awal:akhir:langkah]`` (boleh kosong)."""
        awal = self._urai_slice_awal()
        if not self._cocok_saja(":"):
            self._cocok("]")
            return {"jenis": "Subskrip", "objek": objek, "indeks": awal}

        self._maju()
        akhir = None
        if not self._cocok_saja(":") and not self._cocok_saja("]"):
            akhir = self._urai_ekspresi()
        langkah = None
        if self._cocok_maka(":"):
            if not self._cocok_saja("]"):
                langkah = self._urai_ekspresi()
        self._cocok("]")
        return {
            "jenis": "Slice",
            "objek": objek,
            "awal": awal,
            "akhir": akhir,
            "langkah": langkah,
        }

    def _urai_slice_awal(self) -> Simpul:
        """Urai bagian sebelum tanda ``:`` pada indeks/slice."""
        if self._cocok_saja("]") or self._cocok_saja(":"):
            return {"jenis": "Kosong"}
        return self._urai_ekspresi()

    def _urai_argumen(self) -> list[Simpul]:
        """Urai daftar argumen: posisional, kunci, ``*args``, ``**kwargs``."""
        self._cocok("(")
        argumen: list[Simpul] = []
        while not self._cocok_saja(")") and self._saat_ini().tipe is not TipeToken.EOF:
            if self._cocok_saja("**"):
                self._maju()
                argumen.append({"jenis": "KwargsUnpack", "nilai": self._urai_ekspresi()})
            elif self._cocok_saja("*"):
                self._maju()
                argumen.append({"jenis": "ArgsUnpack", "nilai": self._urai_ekspresi()})
            elif self._cocok_saja(":="):
                self._maju()
                target = self._uri_nama_target()
                argumen.append({"jenis": "PenugasanEkspresi", "target": target, "nilai": self._urai_ekspresi()})
            elif self._bisa_jadi_nama() and self._intip(1).tipe is TipeToken.OP \
                    and self._intip(1).nilai == "=":
                nama = self._ambil_nama()
                self._cocok("=")
                argumen.append({"jenis": "ArgKunci", "nama": nama, "nilai": self._urai_ekspresi()})
            else:
                argumen.append(self._urai_ekspresi())
            if self._cocok_maka(","):
                continue
            break
        self._cocok(")")
        return argumen

    def _uri_nama_target(self) -> Simpul:
        """Ambil satu nama untuk target ``:=``."""
        nama = self._ambil_nama()
        return {"jenis": "Nama", "nama": nama}

    def _urai_atom(self) -> Simpul:
        """Urai nilai atom: literal, nama, list, dict, set, tuple."""
        token = self._saat_ini()
        tipe = token.tipe

        if tipe is TipeToken.ANGKA:
            self._maju()
            return {
                "jenis": "Angka",
                "nilai": token.nilai,
                "source": str(token.teks_asli),
            }

        if tipe is TipeToken.TEKS:
            self._maju()
            return {"jenis": "Teks", "nilai": str(token.teks_asli)}

        if tipe is TipeToken.BENAR:
            self._maju()
            return {"jenis": "Boolean", "nilai": True}

        if tipe is TipeToken.SALAH:
            self._maju()
            return {"jenis": "Boolean", "nilai": False}

        if tipe is TipeToken.KOSONG:
            self._maju()
            return {"jenis": "Kosong"}

        if self._bisa_jadi_nama(token):
            self._maju()
            return {"jenis": "Nama", "nama": str(token.teks_asli if token.teks_asli else token.nilai)}

        if tipe is TipeToken.DELIMITER and token.nilai == "(":
            return self._urai_kurung()
        if tipe is TipeToken.DELIMITER and token.nilai == "[":
            return self._urai_daftar()
        if tipe is TipeToken.DELIMITER and token.nilai == "{":
            return self._urai_kamus_himpunan()
        if tipe is TipeToken.OP and token.nilai == "*":
            self._maju()
            return {"jenis": "ArgsUnpack", "nilai": self._urai_ekspresi()}

        if tipe is TipeToken.OP and token.nilai == "...":
            self._maju()
            return {"jenis": "Elipsis"}

        raise err_ekspresi_diharapkan(
            self._label(token), token.baris, token.kolom, **self._sumber_kw
        )

    def _urai_kurung(self) -> Simpul:
        """Urai kurung: grup, tuple, atau generator ekspresi."""
        self._cocok("(")
        if self._cocok_maka(")"):
            return {"jenis": "Tuple", "elemen": []}
        # Bentuk walrus: (nama := nilai)
        if self._bisa_jadi_nama() and self._intip(1).tipe is TipeToken.OP \
                and self._intip(1).nilai == ":=":
            nama = self._ambil_nama()
            self._cocok(":=")
            nilai = self._urai_ekspresi()
            self._cocok(")")
            return {
                "jenis": "PenugasanEkspresi",
                "target": {"jenis": "Nama", "nama": nama},
                "nilai": nilai,
            }
        pertama = self._urai_ekspresi()
        if self._cocok_saja("for"):
            komp = self._urai_comprehension()
            self._cocok(")")
            return {"jenis": "GeneratorEkspresi", "ekspresi": pertama, "comprehension": komp}
        if self._cocok_maka(","):
            elemen = [pertama]
            while True:
                if self._cocok_saja(")"):
                    break
                elemen.append(self._urai_ekspresi())
                if not self._cocok_maka(","):
                    break
            self._cocok(")")
            return {"jenis": "Tuple", "elemen": elemen}
        self._cocok(")")
        # Tandai kurung eksplisit: affects exponent sign, slices, etc.
        if pertama.get("jenis") in ("UnOp", "BinOp", "Tunggu", "PerbandinganRantai"):
            pertama = dict(pertama)
            pertama["dalam_kurung"] = True
        return pertama

    def _urai_daftar(self) -> Simpul:
        """Urai list literal atau list comprehension."""
        self._cocok("[")
        if self._cocok_maka("]"):
            return {"jenis": "Daftar", "elemen": []}
        pertama = self._urai_ekspresi()
        if self._cocok_saja("for"):
            komp = self._urai_comprehension()
            self._cocok("]")
            return {"jenis": "ListComprehension", "ekspresi": pertama, "comprehension": komp}
        elemen = [pertama]
        while self._cocok_maka(","):
            if self._cocok_saja("]"):
                break
            elemen.append(self._urai_ekspresi())
        self._cocok("]")
        return {"jenis": "Daftar", "elemen": elemen}

    def _urai_kamus_himpunan(self) -> Simpul:
        """Urai dict/set literal atau comprehension-nya."""
        self._cocok("{")
        if self._cocok_maka("}"):
            return {"jenis": "Kamus", "pasang": []}
        pertama = self._urai_ekspresi()
        if self._cocok_saja(":"):
            self._maju()
            nilai = self._urai_ekspresi()
            if self._cocok_saja("for"):
                komp = self._urai_comprehension()
                self._cocok("}")
                return {
                    "jenis": "DictComprehension",
                    "kunci": pertama,
                    "nilai": nilai,
                    "comprehension": komp,
                }
            pasang = [(pertama, nilai)]
            while self._cocok_maka(","):
                if self._cocok_saja("}"):
                    break
                k = self._urai_ekspresi()
                self._cocok(":")
                v = self._urai_ekspresi()
                pasang.append((k, v))
            self._cocok("}")
            return {"jenis": "Kamus", "pasang": pasang}
        # Set
        elemen = [pertama]
        while self._cocok_maka(","):
            if self._cocok_saja("}"):
                break
            elemen.append(self._urai_ekspresi())
        self._cocok("}")
        return {"jenis": "Himpunan", "elemen": elemen}

    def _urai_comprehension(self) -> list[Simpul]:
        """Urai ekor comprehension: ``untuk x dalam xs [jika kondisi]``."""
        komp: list[Simpul] = []
        while self._cocok_saja("for"):
            self._maju()
            target = self._urai_target_penugasan()
            if not (self._cocok_teks_maka("dalam") or self._cocok_maka("in")):
                token = self._saat_ini()
                raise err_token_diharapkan(
                    "'dalam' atau 'in'", self._label(token),
                    token.baris, token.kolom, **self._sumber_kw,
                )
            iterable = self._urai_atau()
            kondisi = None
            if self._cocok_maka("if"):
                kondisi = self._urai_atau()
            komp.append({"target": target, "iterable": iterable, "kondisi": kondisi})
        return komp

    def _urai_nama_titik(self) -> str:
        """Urai nama modul bertitik: ``a.b.c``."""
        bagian = [self._ambil_nama()]
        while self._cocok_saja("."):
            self._maju()
            bagian.append(self._ambil_nama())
        return ".".join(bagian)


# ── Pintasan tingkat modul ──────────────────────────────────────────────────

def urai(source: str, nama_berkas: str | None = None) -> Simpul:
    """Pintasan: tokenisasi + urai, kembalikan AST modul."""
    tokens = Lexer(source, nama_berkas).tokenisasi()
    return Parser(tokens, nama_berkas).urai()


#: Alias kompatibilitas ke API Inggris.
parse = urai

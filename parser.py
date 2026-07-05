"""
parser.py — Parser Pyind: token → AST.
Bagian dari proyek Pyind (Python Indonesia).

Parser ini menggunakan metode Recursive Descent Parsing.
Setiap konstruk bahasa (if, while, for, fungsi, dsb.) memiliki
metode parse tersendiri. Hasilnya adalah pohon AST berupa dict
Python sederhana dengan kunci 'jenis'.
"""

from __future__ import annotations
from typing import Any

from lexer import Token, TipeToken, Lexer
from errors import (
    err_token_diharapkan,
    err_ekspresi_diharapkan,
)

# Tipe alias untuk simpul AST
Simpul = dict[str, Any]


class Parser:
    """
    Menerima daftar token dari Lexer dan menghasilkan AST.

    Contoh penggunaan:
        tokens = Lexer(source).tokenisasi()
        ast = Parser(tokens).parse()
    """

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    # ── API publik ────────────────────────────────────────────────────────────

    def parse(self) -> Simpul:
        """Parse seluruh program dan kembalikan simpul Modul."""
        tubuh = self._parse_blok_modul()
        return {"jenis": "Modul", "tubuh": tubuh}

    # ── Navigasi token ────────────────────────────────────────────────────────

    def _saat_ini(self) -> Token:
        return self.tokens[self.pos]

    def _intip(self, offset: int = 1) -> Token:
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else self.tokens[-1]

    def _maju(self) -> Token:
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def _cocokkan(self, *tipe_atau_nilai: str) -> Token:
        """Pastikan token saat ini cocok lalu maju; lempar error jika tidak."""
        tok = self._saat_ini()
        for tv in tipe_atau_nilai:
            if tok.nilai == tv or tok.tipe.name == tv:
                return self._maju()
        diharapkan = " atau ".join(f"'{x}'" for x in tipe_atau_nilai)
        raise err_token_diharapkan(diharapkan, str(tok.nilai), tok.baris, tok.kolom)

    def _ambil_ident(self) -> str:
        """
        Ambil token berikutnya sebagai identifier (nama).
        Menerima NAMA, KATA_KUNCI, BENAR, SALAH, KOSONG agar kata kunci
        Bahasa Indonesia bisa dipakai sebagai nama fungsi/metode/parameter.

        Untuk BENAR/SALAH/KOSONG, nilai-nya adalah teks Indonesia asli
        ("benar", "salah", "kosong") yang tetap valid sebagai nama Python.
        Untuk KATA_KUNCI, nilai-nya adalah padanan Python ("print", dst.).
        """
        tok = self._saat_ini()
        TIPE_IDENT = {
            TipeToken.NAMA, TipeToken.KATA_KUNCI,
            TipeToken.BENAR, TipeToken.SALAH, TipeToken.KOSONG,
        }
        if tok.tipe not in TIPE_IDENT:
            raise err_token_diharapkan("NAMA", str(tok.nilai), tok.baris, tok.kolom)
        self._maju()
        return str(tok.nilai)

    def _lewati_baris_baru(self) -> None:
        while self._saat_ini().tipe == TipeToken.BARIS_BARU:
            self._maju()

    def _adalah(self, *nilai_atau_tipe: str) -> bool:
        tok = self._saat_ini()
        return tok.nilai in nilai_atau_tipe or tok.tipe.name in nilai_atau_tipe

    def _adalah_eof(self) -> bool:
        return self._saat_ini().tipe == TipeToken.EOF

    # ── Parsing blok ─────────────────────────────────────────────────────────

    def _parse_blok_modul(self) -> list[Simpul]:
        pernyataan: list[Simpul] = []
        self._lewati_baris_baru()
        while not self._adalah_eof():
            stmt = self._parse_pernyataan()
            if stmt is not None:
                pernyataan.append(stmt)
            self._lewati_baris_baru()
        return pernyataan

    def _parse_blok_indented(self) -> list[Simpul]:
        """Parse blok yang diindentasi (tubuh if, while, for, fungsi, dsb.)."""
        self._lewati_baris_baru()
        self._cocokkan("INDENT")
        self._lewati_baris_baru()

        pernyataan: list[Simpul] = []
        while not self._adalah("DEDENT") and not self._adalah_eof():
            stmt = self._parse_pernyataan()
            if stmt is not None:
                pernyataan.append(stmt)
            self._lewati_baris_baru()

        if self._adalah("DEDENT"):
            self._maju()
        return pernyataan

    # ── Parsing pernyataan ────────────────────────────────────────────────────

    def _parse_pernyataan(self) -> Simpul | None:
        """Arahkan ke parser pernyataan yang tepat berdasarkan token saat ini."""
        self._lewati_baris_baru()
        tok = self._saat_ini()

        if tok.tipe in (TipeToken.EOF, TipeToken.DEDENT):
            return None

        nilai = tok.nilai

        if nilai == "def":       return self._parse_fungsi()
        if nilai == "class":     return self._parse_kelas()
        if nilai == "if":        return self._parse_jika()
        if nilai == "while":     return self._parse_selama()
        if nilai == "for":       return self._parse_untuk()
        if nilai == "return":    return self._parse_kembali()
        if nilai == "import":    return self._parse_impor()
        if nilai == "from":      return self._parse_dari()
        if nilai == "try":       return self._parse_coba()
        if nilai == "del":       return self._parse_hapus()
        if nilai == "global":    return self._parse_global()
        if nilai == "nonlocal":  return self._parse_nonlokal()
        if nilai == "assert":    return self._parse_assert()
        if nilai == "raise":     return self._parse_naikkan()
        if nilai == "with":      return self._parse_bersama()

        if nilai == "break":
            self._maju(); self._lewati_baris_baru()
            return {"jenis": "Hentikan"}
        if nilai == "continue":
            self._maju(); self._lewati_baris_baru()
            return {"jenis": "Lanjut"}
        if nilai == "pass":
            self._maju(); self._lewati_baris_baru()
            return {"jenis": "Lewati"}

        return self._parse_ekspresi_atau_penugasan()

    def _parse_ekspresi_atau_penugasan(self) -> Simpul:
        """
        Parse ekspresi atau pernyataan penugasan.
        Mendukung tuple unpacking: a, b = 0, 1
        """
        ekspresi = self._parse_ekspresi()

        # ── Tangani tuple di sisi kiri: a, b = ... ────────────────────────
        if self._adalah(","):
            elemen = [ekspresi]
            while self._adalah(","):
                self._maju()
                tok_dep = self._saat_ini()
                # Berhenti jika token berikutnya bukan bagian dari ekspresi
                if tok_dep.tipe in (TipeToken.BARIS_BARU, TipeToken.EOF, TipeToken.DEDENT):
                    break
                if tok_dep.tipe == TipeToken.OP and tok_dep.nilai == "=":
                    break
                elemen.append(self._parse_ekspresi())
            ekspresi = {"jenis": "Tuple", "elemen": elemen}

        tok = self._saat_ini()

        # ── Penugasan biasa: target = nilai ───────────────────────────────
        if tok.nilai == "=" and tok.tipe == TipeToken.OP:
            self._maju()
            nilai = self._parse_ekspresi()
            # Tangani tuple di sisi kanan: = a, b
            if self._adalah(","):
                elemen_kanan = [nilai]
                while self._adalah(","):
                    self._maju()
                    tok_dep = self._saat_ini()
                    if tok_dep.tipe in (TipeToken.BARIS_BARU, TipeToken.EOF, TipeToken.DEDENT):
                        break
                    elemen_kanan.append(self._parse_ekspresi())
                nilai = {"jenis": "Tuple", "elemen": elemen_kanan}
            self._lewati_baris_baru()
            return {"jenis": "Penugasan", "target": ekspresi, "nilai": nilai}

        # ── Penugasan gabungan: +=, -=, *=, /=, dsb. ─────────────────────
        op_gabung = {"+=", "-=", "*=", "/=", "%=", "**=", "//="}
        if tok.tipe == TipeToken.OP and tok.nilai in op_gabung:
            op = self._maju().nilai
            nilai = self._parse_ekspresi()
            self._lewati_baris_baru()
            return {"jenis": "PenugasanGabungan", "op": op, "target": ekspresi, "nilai": nilai}

        self._lewati_baris_baru()
        return {"jenis": "EkspresiPernyataan", "ekspresi": ekspresi}

    # ── Pernyataan terstruktur ────────────────────────────────────────────────

    def _parse_fungsi(self) -> Simpul:
        """Parse: def nama(param...): blok"""
        self._cocokkan("def")
        nama = self._ambil_ident()   # terima keyword sebagai nama fungsi/metode
        self._cocokkan("(")
        params = self._parse_daftar_parameter()
        self._cocokkan(")")
        kembali_anotasi = None
        if self._adalah("->"):
            self._maju()
            kembali_anotasi = self._parse_ekspresi()
        self._cocokkan(":")
        self._lewati_baris_baru()
        tubuh = self._parse_blok_indented()
        return {
            "jenis": "DefinisiFungsi",
            "nama": nama,
            "parameter": params,
            "kembali_anotasi": kembali_anotasi,
            "tubuh": tubuh,
        }

    def _parse_daftar_parameter(self) -> list[Simpul]:
        """Parse daftar parameter fungsi termasuk default dan *args/**kwargs."""
        params: list[Simpul] = []
        while not self._adalah(")") and not self._adalah_eof():
            param: Simpul = {}
            if self._adalah("**"):
                self._maju()
                param["bintang"] = "**"
            elif self._adalah("*"):
                self._maju()
                param["bintang"] = "*"

            # Terima keyword sebagai nama parameter (misal: fungsi f(kosong=None))
            TIPE_IDENT = {TipeToken.NAMA, TipeToken.KATA_KUNCI,
                          TipeToken.BENAR, TipeToken.SALAH, TipeToken.KOSONG}
            if self._saat_ini().tipe in TIPE_IDENT:
                param["nama"] = self._ambil_ident()
            else:
                break

            if self._adalah(":"):
                self._maju()
                param["anotasi"] = self._parse_ekspresi()
            if self._adalah("="):
                self._maju()
                param["default"] = self._parse_ekspresi()

            params.append(param)
            if self._adalah(","):
                self._maju()
            else:
                break
        return params

    def _parse_kelas(self) -> Simpul:
        """Parse: class Nama(Base...): blok"""
        self._cocokkan("class")
        nama = self._ambil_ident()   # terima keyword sebagai nama kelas
        induk: list[Simpul] = []
        if self._adalah("("):
            self._maju()
            while not self._adalah(")") and not self._adalah_eof():
                induk.append(self._parse_ekspresi())
                if self._adalah(","):
                    self._maju()
            self._cocokkan(")")
        self._cocokkan(":")
        self._lewati_baris_baru()
        tubuh = self._parse_blok_indented()
        return {"jenis": "DefinisiKelas", "nama": nama, "induk": induk, "tubuh": tubuh}

    def _parse_jika(self) -> Simpul:
        """Parse: if kondisi: blok [elif: blok]* [else: blok]"""
        self._cocokkan("if")
        kondisi = self._parse_ekspresi()
        self._cocokkan(":")
        self._lewati_baris_baru()
        then_blok = self._parse_blok_indented()

        elif_cabang: list[Simpul] = []
        else_blok: list[Simpul] = []

        self._lewati_baris_baru()
        while self._adalah("elif"):
            self._maju()
            k = self._parse_ekspresi()
            self._cocokkan(":")
            self._lewati_baris_baru()
            b = self._parse_blok_indented()
            elif_cabang.append({"kondisi": k, "tubuh": b})
            self._lewati_baris_baru()

        if self._adalah("else"):
            self._maju()
            self._cocokkan(":")
            self._lewati_baris_baru()
            else_blok = self._parse_blok_indented()

        return {
            "jenis": "Jika",
            "kondisi": kondisi,
            "then": then_blok,
            "elif": elif_cabang,
            "else": else_blok,
        }

    def _parse_selama(self) -> Simpul:
        """Parse: while kondisi: blok"""
        self._cocokkan("while")
        kondisi = self._parse_ekspresi()
        self._cocokkan(":")
        self._lewati_baris_baru()
        tubuh = self._parse_blok_indented()
        return {"jenis": "Selama", "kondisi": kondisi, "tubuh": tubuh}

    def _parse_untuk(self) -> Simpul:
        """Parse: for var in iterable: blok"""
        self._cocokkan("for")
        target = self._parse_target_for()
        self._cocokkan("in")
        iterable = self._parse_ekspresi()
        self._cocokkan(":")
        self._lewati_baris_baru()
        tubuh = self._parse_blok_indented()
        return {"jenis": "Untuk", "target": target, "iterable": iterable, "tubuh": tubuh}

    def _parse_target_for(self) -> Simpul:
        """Parse target loop for — bisa nama tunggal atau tuple: a, b"""
        if self._saat_ini().tipe == TipeToken.NAMA:
            nama = self._maju().nilai
            if self._adalah(","):
                elemen = [{"jenis": "Nama", "nama": nama}]
                while self._adalah(","):
                    self._maju()
                    if self._saat_ini().tipe == TipeToken.NAMA:
                        elemen.append({"jenis": "Nama", "nama": self._maju().nilai})
                return {"jenis": "Tuple", "elemen": elemen}
            return {"jenis": "Nama", "nama": nama}
        return self._parse_ekspresi()

    def _parse_kembali(self) -> Simpul:
        self._cocokkan("return")
        if self._adalah("BARIS_BARU") or self._adalah_eof():
            return {"jenis": "Kembali", "nilai": None}
        nilai = self._parse_ekspresi()
        self._lewati_baris_baru()
        return {"jenis": "Kembali", "nilai": nilai}

    def _parse_impor(self) -> Simpul:
        """Parse: import modul [as alias]"""
        self._cocokkan("import")
        nama = self._parse_nama_titik()
        alias = None
        if self._adalah("as"):
            self._maju()
            alias = self._cocokkan("NAMA").nilai
        self._lewati_baris_baru()
        return {"jenis": "Impor", "nama": nama, "alias": alias}

    def _parse_dari(self) -> Simpul:
        """Parse: from modul import nama [as alias], ..."""
        self._cocokkan("from")
        modul = self._parse_nama_titik()
        self._cocokkan("import")
        if self._adalah("*"):
            self._maju()
            self._lewati_baris_baru()
            return {"jenis": "DariImpor", "modul": modul, "nama": [{"nama": "*", "alias": None}]}
        dengan_kurung = self._adalah("(")
        if dengan_kurung:
            self._maju()
        nama_list: list[dict] = []
        while True:
            n = self._cocokkan("NAMA").nilai
            a = None
            if self._adalah("as"):
                self._maju()
                a = self._cocokkan("NAMA").nilai
            nama_list.append({"nama": n, "alias": a})
            if self._adalah(","):
                self._maju()
                self._lewati_baris_baru()
                if self._adalah(")"):
                    break
            else:
                break
        if dengan_kurung:
            self._cocokkan(")")
        self._lewati_baris_baru()
        return {"jenis": "DariImpor", "modul": modul, "nama": nama_list}

    def _parse_coba(self) -> Simpul:
        """Parse: try: blok except Tipe [as nama]: blok [finally: blok]"""
        self._cocokkan("try")
        self._cocokkan(":")
        self._lewati_baris_baru()
        tubuh = self._parse_blok_indented()

        handler: list[Simpul] = []
        self._lewati_baris_baru()
        while self._adalah("except"):
            self._maju()
            tipe_exc = None
            nama_exc = None
            if not self._adalah(":"):
                tipe_exc = self._parse_ekspresi()
                if self._adalah("as"):
                    self._maju()
                    nama_exc = self._cocokkan("NAMA").nilai
            self._cocokkan(":")
            self._lewati_baris_baru()
            b = self._parse_blok_indented()
            handler.append({"tipe": tipe_exc, "nama": nama_exc, "tubuh": b})
            self._lewati_baris_baru()

        else_blok: list[Simpul] = []
        if self._adalah("else"):
            self._maju(); self._cocokkan(":")
            self._lewati_baris_baru()
            else_blok = self._parse_blok_indented()
            self._lewati_baris_baru()

        finally_blok: list[Simpul] = []
        if self._adalah("finally"):
            self._maju(); self._cocokkan(":")
            self._lewati_baris_baru()
            finally_blok = self._parse_blok_indented()

        return {
            "jenis": "CobaDanKecuali",
            "tubuh": tubuh,
            "handler": handler,
            "else": else_blok,
            "finally": finally_blok,
        }

    def _parse_hapus(self) -> Simpul:
        self._cocokkan("del")
        target = self._parse_ekspresi()
        self._lewati_baris_baru()
        return {"jenis": "Hapus", "target": target}

    def _parse_global(self) -> Simpul:
        self._cocokkan("global")
        nama = [self._cocokkan("NAMA").nilai]
        while self._adalah(","):
            self._maju()
            nama.append(self._cocokkan("NAMA").nilai)
        self._lewati_baris_baru()
        return {"jenis": "Global", "nama": nama}

    def _parse_nonlokal(self) -> Simpul:
        self._cocokkan("nonlocal")
        nama = [self._cocokkan("NAMA").nilai]
        while self._adalah(","):
            self._maju()
            nama.append(self._cocokkan("NAMA").nilai)
        self._lewati_baris_baru()
        return {"jenis": "Nonlokal", "nama": nama}

    def _parse_assert(self) -> Simpul:
        self._cocokkan("assert")
        kondisi = self._parse_ekspresi()
        pesan = None
        if self._adalah(","):
            self._maju()
            pesan = self._parse_ekspresi()
        self._lewati_baris_baru()
        return {"jenis": "Assert", "kondisi": kondisi, "pesan": pesan}

    def _parse_naikkan(self) -> Simpul:
        self._cocokkan("raise")
        if self._adalah("BARIS_BARU") or self._adalah_eof():
            return {"jenis": "Naikkan", "ekspresi": None}
        ekspresi = self._parse_ekspresi()
        self._lewati_baris_baru()
        return {"jenis": "Naikkan", "ekspresi": ekspresi}

    def _parse_bersama(self) -> Simpul:
        self._cocokkan("with")
        konteks = self._parse_ekspresi()
        nama = None
        if self._adalah("as"):
            self._maju()
            nama = self._cocokkan("NAMA").nilai
        self._cocokkan(":")
        self._lewati_baris_baru()
        tubuh = self._parse_blok_indented()
        return {"jenis": "Bersama", "konteks": konteks, "nama": nama, "tubuh": tubuh}

    # ── Parsing ekspresi (precedence climbing) ────────────────────────────────

    def _parse_ekspresi(self) -> Simpul:
        if self._adalah("lambda"):
            return self._parse_lambda()
        return self._parse_ekspresi_kondisional()

    def _parse_lambda(self) -> Simpul:
        self._cocokkan("lambda")
        params: list[str] = []
        while not self._adalah(":") and not self._adalah_eof():
            if self._saat_ini().tipe == TipeToken.NAMA:
                params.append(self._maju().nilai)
            if self._adalah(","):
                self._maju()
        self._cocokkan(":")
        tubuh = self._parse_ekspresi()
        return {"jenis": "Lambda", "parameter": params, "tubuh": tubuh}

    def _parse_ekspresi_kondisional(self) -> Simpul:
        """ekspresi [if kondisi else alternatif]"""
        kiri = self._parse_or()
        if self._adalah("if"):
            self._maju()
            kondisi = self._parse_or()
            self._cocokkan("else")
            kanan = self._parse_ekspresi_kondisional()
            return {"jenis": "EkspresiKondisi", "nilai": kiri, "kondisi": kondisi, "alternatif": kanan}
        return kiri

    def _parse_or(self) -> Simpul:
        kiri = self._parse_and()
        while self._adalah("or"):
            op = self._maju().nilai
            kanan = self._parse_and()
            kiri = {"jenis": "BinOp", "op": op, "kiri": kiri, "kanan": kanan}
        return kiri

    def _parse_and(self) -> Simpul:
        kiri = self._parse_not()
        while self._adalah("and"):
            op = self._maju().nilai
            kanan = self._parse_not()
            kiri = {"jenis": "BinOp", "op": op, "kiri": kiri, "kanan": kanan}
        return kiri

    def _parse_not(self) -> Simpul:
        if self._adalah("not"):
            op = self._maju().nilai
            return {"jenis": "UnOp", "op": op, "operand": self._parse_not()}
        return self._parse_perbandingan()

    def _parse_perbandingan(self) -> Simpul:
        kiri = self._parse_bitor()
        OP_PERB = {"==", "!=", "<", ">", "<=", ">="}
        while True:
            tok = self._saat_ini()
            if tok.nilai in OP_PERB:
                op = self._maju().nilai
            elif tok.nilai == "not" and self._intip(1).nilai == "in":
                self._maju(); self._maju(); op = "not in"
            elif tok.nilai == "is" and self._intip(1).nilai == "not":
                self._maju(); self._maju(); op = "is not"
            elif tok.nilai in ("in", "is"):
                op = self._maju().nilai
            else:
                break
            kanan = self._parse_bitor()
            kiri = {"jenis": "BinOp", "op": op, "kiri": kiri, "kanan": kanan}
        return kiri

    def _parse_bitor(self) -> Simpul:
        kiri = self._parse_bitxor()
        while self._saat_ini().tipe == TipeToken.OP and self._saat_ini().nilai == "|":
            op = self._maju().nilai
            kanan = self._parse_bitxor()
            kiri = {"jenis": "BinOp", "op": op, "kiri": kiri, "kanan": kanan}
        return kiri

    def _parse_bitxor(self) -> Simpul:
        kiri = self._parse_bitand()
        while self._saat_ini().tipe == TipeToken.OP and self._saat_ini().nilai == "^":
            op = self._maju().nilai
            kanan = self._parse_bitand()
            kiri = {"jenis": "BinOp", "op": op, "kiri": kiri, "kanan": kanan}
        return kiri

    def _parse_bitand(self) -> Simpul:
        kiri = self._parse_shift()
        while self._saat_ini().tipe == TipeToken.OP and self._saat_ini().nilai == "&":
            op = self._maju().nilai
            kanan = self._parse_shift()
            kiri = {"jenis": "BinOp", "op": op, "kiri": kiri, "kanan": kanan}
        return kiri

    def _parse_shift(self) -> Simpul:
        kiri = self._parse_penjumlahan()
        while self._saat_ini().tipe == TipeToken.OP and self._saat_ini().nilai in ("<<", ">>"):
            op = self._maju().nilai
            kanan = self._parse_penjumlahan()
            kiri = {"jenis": "BinOp", "op": op, "kiri": kiri, "kanan": kanan}
        return kiri

    def _parse_penjumlahan(self) -> Simpul:
        kiri = self._parse_perkalian()
        while self._saat_ini().tipe == TipeToken.OP and self._saat_ini().nilai in ("+", "-"):
            op = self._maju().nilai
            kanan = self._parse_perkalian()
            kiri = {"jenis": "BinOp", "op": op, "kiri": kiri, "kanan": kanan}
        return kiri

    def _parse_perkalian(self) -> Simpul:
        kiri = self._parse_eksponen()
        while self._saat_ini().tipe == TipeToken.OP and self._saat_ini().nilai in ("*", "/", "//", "%", "@"):
            op = self._maju().nilai
            kanan = self._parse_eksponen()
            kiri = {"jenis": "BinOp", "op": op, "kiri": kiri, "kanan": kanan}
        return kiri

    def _parse_eksponen(self) -> Simpul:
        """
        Pangkat bersifat right-associative: 2**3**2 == 2**(3**2) == 512.
        Karena itu sisi kanan diparsing secara rekursif dengan _parse_eksponen(),
        bukan _parse_unary() — perbedaan ini krusial untuk chaining yang benar.
        """
        kiri = self._parse_unary()
        if self._saat_ini().tipe == TipeToken.OP and self._saat_ini().nilai == "**":
            op = self._maju().nilai
            kanan = self._parse_eksponen()   # rekursif agar right-associative
            return {"jenis": "BinOp", "op": op, "kiri": kiri, "kanan": kanan}
        return kiri

    def _parse_unary(self) -> Simpul:
        if self._saat_ini().tipe == TipeToken.OP and self._saat_ini().nilai in ("-", "+", "~"):
            op = self._maju().nilai
            return {"jenis": "UnOp", "op": op, "operand": self._parse_unary()}
        return self._parse_postfix()

    def _parse_postfix(self) -> Simpul:
        """Akses atribut, subskrip, dan pemanggilan fungsi."""
        simpul = self._parse_atom()
        while True:
            tok = self._saat_ini()
            if tok.nilai == ".":
                self._maju()
                attr = self._ambil_ident()   # metode/atribut bisa bernama keyword
                simpul = {"jenis": "Atribut", "objek": simpul, "atribut": attr}
            elif tok.nilai == "[":
                self._maju()
                indeks = self._parse_ekspresi()
                if self._adalah(":"):
                    self._maju()
                    akhir = None if self._adalah("]") else self._parse_ekspresi()
                    langkah = None
                    if self._adalah(":"):
                        self._maju()
                        langkah = None if self._adalah("]") else self._parse_ekspresi()
                    self._cocokkan("]")
                    simpul = {"jenis": "Slice", "objek": simpul, "awal": indeks, "akhir": akhir, "langkah": langkah}
                else:
                    self._cocokkan("]")
                    simpul = {"jenis": "Subskrip", "objek": simpul, "indeks": indeks}
            elif tok.nilai == "(":
                argumen = self._parse_argumen()
                simpul = {"jenis": "Panggilan", "fungsi": simpul, "argumen": argumen}
            else:
                break
        return simpul

    def _parse_argumen(self) -> list[Simpul]:
        """Parse daftar argumen: positional, keyword, *args, **kwargs."""
        self._cocokkan("(")
        args: list[Simpul] = []
        while not self._adalah(")") and not self._adalah_eof():
            if self._adalah("**"):
                self._maju()
                args.append({"jenis": "KwargsUnpack", "nilai": self._parse_ekspresi()})
            elif self._adalah("*"):
                self._maju()
                args.append({"jenis": "ArgsUnpack", "nilai": self._parse_ekspresi()})
            elif (self._saat_ini().tipe == TipeToken.NAMA
                  and self._intip(1).nilai == "="
                  and self._intip(1).tipe == TipeToken.OP):
                nama = self._maju().nilai
                self._cocokkan("=")
                nilai = self._parse_ekspresi()
                args.append({"jenis": "ArgKunci", "nama": nama, "nilai": nilai})
            else:
                args.append(self._parse_ekspresi())
            if self._adalah(","):
                self._maju()
            else:
                break
        self._cocokkan(")")
        return args

    def _parse_atom(self) -> Simpul:
        """Nilai atom: literal, nama, list, dict, tuple, set."""
        tok = self._saat_ini()

        if tok.tipe == TipeToken.ANGKA:
            self._maju()
            return {"jenis": "Angka", "nilai": tok.nilai}

        if tok.tipe == TipeToken.TEKS:
            self._maju()
            return {"jenis": "Teks", "nilai": tok.nilai}

        if tok.tipe == TipeToken.BENAR:
            self._maju(); return {"jenis": "Boolean", "nilai": True}

        if tok.tipe == TipeToken.SALAH:
            self._maju(); return {"jenis": "Boolean", "nilai": False}

        if tok.tipe == TipeToken.KOSONG:
            self._maju(); return {"jenis": "Kosong"}

        if tok.tipe in (TipeToken.NAMA, TipeToken.KATA_KUNCI):
            self._maju()
            return {"jenis": "Nama", "nama": tok.nilai}

        # Ekspresi dalam kurung atau tuple
        if tok.nilai == "(":
            self._maju()
            if self._adalah(")"):
                self._maju()
                return {"jenis": "Tuple", "elemen": []}
            ekspresi = self._parse_ekspresi()
            if self._adalah("for"):
                komp = self._parse_comprehension_tail()
                self._cocokkan(")")
                return {"jenis": "GeneratorEkspresi", "ekspresi": ekspresi, "comprehension": komp}
            if self._adalah(","):
                elemen = [ekspresi]
                while self._adalah(","):
                    self._maju()
                    if self._adalah(")"):
                        break
                    elemen.append(self._parse_ekspresi())
                self._cocokkan(")")
                return {"jenis": "Tuple", "elemen": elemen}
            self._cocokkan(")")
            return ekspresi

        # List atau list comprehension
        if tok.nilai == "[":
            self._maju()
            if self._adalah("]"):
                self._maju()
                return {"jenis": "Daftar", "elemen": []}
            pertama = self._parse_ekspresi()
            if self._adalah("for"):
                komp = self._parse_comprehension_tail()
                self._cocokkan("]")
                return {"jenis": "ListComprehension", "ekspresi": pertama, "comprehension": komp}
            elemen = [pertama]
            while self._adalah(","):
                self._maju()
                if self._adalah("]"):
                    break
                elemen.append(self._parse_ekspresi())
            self._cocokkan("]")
            return {"jenis": "Daftar", "elemen": elemen}

        # Dict atau set literal
        if tok.nilai == "{":
            self._maju()
            if self._adalah("}"):
                self._maju()
                return {"jenis": "Kamus", "pasang": []}
            pertama = self._parse_ekspresi()
            if self._adalah(":"):
                # Dict
                self._maju()
                nilai_pertama = self._parse_ekspresi()
                if self._adalah("for"):
                    komp = self._parse_comprehension_tail()
                    self._cocokkan("}")
                    return {"jenis": "DictComprehension", "kunci": pertama, "nilai": nilai_pertama, "comprehension": komp}
                pasang = [(pertama, nilai_pertama)]
                while self._adalah(","):
                    self._maju()
                    if self._adalah("}"):
                        break
                    k = self._parse_ekspresi()
                    self._cocokkan(":")
                    v = self._parse_ekspresi()
                    pasang.append((k, v))
                self._cocokkan("}")
                return {"jenis": "Kamus", "pasang": pasang}
            else:
                # Set
                elemen = [pertama]
                while self._adalah(","):
                    self._maju()
                    if self._adalah("}"):
                        break
                    elemen.append(self._parse_ekspresi())
                self._cocokkan("}")
                return {"jenis": "Himpunan", "elemen": elemen}

        raise err_ekspresi_diharapkan(str(tok.nilai), tok.baris, tok.kolom)

    def _parse_comprehension_tail(self) -> list[Simpul]:
        """Parse ekor comprehension: for x in xs [if kondisi]"""
        komp: list[Simpul] = []
        while self._adalah("for"):
            self._maju()
            target = self._parse_target_for()
            self._cocokkan("in")
            iterable = self._parse_or()
            kondisi = None
            if self._adalah("if"):
                self._maju()
                kondisi = self._parse_or()
            komp.append({"target": target, "iterable": iterable, "kondisi": kondisi})
        return komp

    def _parse_nama_titik(self) -> str:
        """Parse nama modul dengan titik: a.b.c"""
        bagian = [self._cocokkan("NAMA").nilai]
        while self._adalah("."):
            self._maju()
            bagian.append(self._cocokkan("NAMA").nilai)
        return ".".join(bagian)


# ── Fungsi utilitas ───────────────────────────────────────────────────────────

def parse(source: str) -> Simpul:
    """Shortcut: tokenisasi + parse dan kembalikan AST."""
    tokens = Lexer(source).tokenisasi()
    return Parser(tokens).parse()

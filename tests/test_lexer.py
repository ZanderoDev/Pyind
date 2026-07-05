"""
test_lexer.py — Unit test untuk lexer Pyind.
Jalankan dengan: pytest tests/test_lexer.py -v
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from lexer import Lexer, TipeToken, Token


# ── Helpers ───────────────────────────────────────────────────────────────────

def tokenisasi(source: str) -> list[Token]:
    """Shortcut tokenisasi — filter EOF untuk kemudahan."""
    return Lexer(source).tokenisasi()


def tipe_saja(tokens: list[Token]) -> list[str]:
    return [t.tipe.name for t in tokens]


def nilai_saja(tokens: list[Token]) -> list:
    return [t.nilai for t in tokens]


# ── Test keyword ──────────────────────────────────────────────────────────────

class TestKeyword:
    def test_cetak_dipetakan_ke_print(self):
        tokens = tokenisasi("cetak")
        assert tokens[0].tipe == TipeToken.KATA_KUNCI
        assert tokens[0].nilai == "print"

    def test_jika_dipetakan_ke_if(self):
        tokens = tokenisasi("jika")
        assert tokens[0].nilai == "if"

    def test_fungsi_dipetakan_ke_def(self):
        tokens = tokenisasi("fungsi")
        assert tokens[0].nilai == "def"

    def test_untuk_dipetakan_ke_for(self):
        tokens = tokenisasi("untuk")
        assert tokens[0].nilai == "for"

    def test_selama_dipetakan_ke_while(self):
        tokens = tokenisasi("selama")
        assert tokens[0].nilai == "while"

    def test_kembali_dipetakan_ke_return(self):
        tokens = tokenisasi("kembali")
        assert tokens[0].nilai == "return"

    def test_benar_adalah_tipe_BENAR(self):
        tokens = tokenisasi("benar")
        assert tokens[0].tipe == TipeToken.BENAR

    def test_salah_adalah_tipe_SALAH(self):
        tokens = tokenisasi("salah")
        assert tokens[0].tipe == TipeToken.SALAH

    def test_kosong_adalah_tipe_KOSONG(self):
        tokens = tokenisasi("kosong")
        assert tokens[0].tipe == TipeToken.KOSONG

    def test_jika_tidak_dipetakan_ke_elif(self):
        tokens = tokenisasi("jika_tidak")
        assert tokens[0].nilai == "elif"

    def test_lainnya_dipetakan_ke_else(self):
        tokens = tokenisasi("lainnya")
        assert tokens[0].nilai == "else"


# ── Test identifier ───────────────────────────────────────────────────────────

class TestIdentifier:
    def test_nama_biasa(self):
        tokens = tokenisasi("nama_variabel")
        assert tokens[0].tipe == TipeToken.NAMA
        assert tokens[0].nilai == "nama_variabel"

    def test_nama_dengan_angka(self):
        tokens = tokenisasi("var1")
        assert tokens[0].tipe == TipeToken.NAMA

    def test_nama_dengan_underscore_depan(self):
        tokens = tokenisasi("_privat")
        assert tokens[0].tipe == TipeToken.NAMA
        assert tokens[0].nilai == "_privat"


# ── Test angka ────────────────────────────────────────────────────────────────

class TestAngka:
    def test_integer(self):
        tokens = tokenisasi("42")
        assert tokens[0].tipe == TipeToken.ANGKA
        assert tokens[0].nilai == 42

    def test_float(self):
        tokens = tokenisasi("3.14")
        assert tokens[0].tipe == TipeToken.ANGKA
        assert abs(tokens[0].nilai - 3.14) < 1e-9

    def test_nol(self):
        tokens = tokenisasi("0")
        assert tokens[0].nilai == 0

    def test_angka_besar(self):
        tokens = tokenisasi("1000000")
        assert tokens[0].nilai == 1_000_000


# ── Test string ───────────────────────────────────────────────────────────────

class TestString:
    def test_string_kutip_ganda(self):
        tokens = tokenisasi('"halo dunia"')
        assert tokens[0].tipe == TipeToken.TEKS
        assert tokens[0].nilai == '"halo dunia"'

    def test_string_kutip_tunggal(self):
        tokens = tokenisasi("'halo'")
        assert tokens[0].tipe == TipeToken.TEKS
        assert tokens[0].nilai == "'halo'"

    def test_keyword_dalam_string_tidak_diterjemahkan(self):
        """KRITIS: kata kunci di dalam string harus tetap utuh."""
        tokens = tokenisasi('"jika hujan"')
        assert tokens[0].tipe == TipeToken.TEKS
        # Nilai string harus mengandung 'jika' bukan 'if'
        assert "jika" in tokens[0].nilai
        assert "if" not in tokens[0].nilai.replace('"', "")

    def test_string_dengan_spasi(self):
        tokens = tokenisasi('"satu dua tiga"')
        assert tokens[0].tipe == TipeToken.TEKS

    def test_string_kosong(self):
        tokens = tokenisasi('""')
        assert tokens[0].tipe == TipeToken.TEKS
        assert tokens[0].nilai == '""'


# ── Test operator ─────────────────────────────────────────────────────────────

class TestOperator:
    def test_op_tambah(self):
        tokens = tokenisasi("a + b")
        assert any(t.nilai == "+" for t in tokens)

    def test_op_sama_dengan(self):
        tokens = tokenisasi("a == b")
        assert any(t.nilai == "==" for t in tokens)

    def test_op_tidak_sama(self):
        tokens = tokenisasi("a != b")
        assert any(t.nilai == "!=" for t in tokens)

    def test_op_gabung(self):
        tokens = tokenisasi("x += 1")
        assert any(t.nilai == "+=" for t in tokens)

    def test_penugasan(self):
        tokens = tokenisasi("x = 5")
        # Harus ada OP '='
        assert any(t.tipe == TipeToken.OP and t.nilai == "=" for t in tokens)


# ── Test delimiter ────────────────────────────────────────────────────────────

class TestDelimiter:
    def test_kurung_buka_tutup(self):
        tokens = tokenisasi("()")
        nilai = nilai_saja(tokens)
        assert "(" in nilai
        assert ")" in nilai

    def test_titik_dua(self):
        tokens = tokenisasi("jika benar:")
        assert any(t.nilai == ":" for t in tokens)

    def test_koma(self):
        tokens = tokenisasi("a, b, c")
        koma = [t for t in tokens if t.nilai == ","]
        assert len(koma) == 2


# ── Test INDENT/DEDENT ────────────────────────────────────────────────────────

class TestIndentDedent:
    def test_blok_sederhana(self):
        source = "jika benar:\n    cetak(1)\n"
        tokens = tokenisasi(source)
        tipe = tipe_saja(tokens)
        assert "INDENT" in tipe
        assert "DEDENT" in tipe

    def test_tanpa_blok_tidak_ada_indent(self):
        source = "x = 1\n"
        tokens = tokenisasi(source)
        tipe = tipe_saja(tokens)
        assert "INDENT" not in tipe
        assert "DEDENT" not in tipe

    def test_baris_baru_dihasilkan(self):
        source = "x = 1\ny = 2\n"
        tokens = tokenisasi(source)
        tipe = tipe_saja(tokens)
        assert "BARIS_BARU" in tipe


# ── Test komentar ─────────────────────────────────────────────────────────────

class TestKomentar:
    def test_komentar_dilewati(self):
        source = "# ini komentar\nx = 1\n"
        tokens = tokenisasi(source)
        # Tidak boleh ada token dengan nilai yang mengandung '#'
        for t in tokens:
            assert "#" not in str(t.nilai)

    def test_komentar_inline(self):
        source = "x = 1  # variabel x\n"
        tokens = tokenisasi(source)
        nilai = nilai_saja(tokens)
        assert "x" in nilai
        assert 1 in nilai
        assert "# variabel x" not in nilai


# ── Test error ────────────────────────────────────────────────────────────────

class TestError:
    def test_karakter_tak_dikenal(self):
        from errors import KesalahanLeksikal
        with pytest.raises(KesalahanLeksikal):
            tokenisasi("x = $5")

    def test_string_tidak_ditutup(self):
        from errors import KesalahanLeksikal
        with pytest.raises(KesalahanLeksikal):
            tokenisasi('"tidak ditutup')

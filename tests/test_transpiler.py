"""
test_transpiler.py — Unit test untuk transpiler Pyind.
Menguji bahwa kode Bahasa Indonesia menghasilkan Python yang benar.
Jalankan dengan: pytest tests/test_transpiler.py -v
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from lexer import Lexer
from parser import Parser
from transpiler import Transpiler


# ── Helper ────────────────────────────────────────────────────────────────────

def tr(source: str) -> str:
    """Transpilasi source code Pyind dan kembalikan kode Python (strip)."""
    tokens = Lexer(source).tokenisasi()
    ast    = Parser(tokens).parse()
    kode   = Transpiler().transpile(ast)
    return kode.strip()


def jalankan(source: str) -> dict:
    """Transpilasi dan exec, kembalikan namespace hasil eksekusi."""
    kode = tr(source)
    ns: dict = {}
    exec(compile(kode, "<test>", "exec"), ns)
    return ns


# ── Test penugasan ────────────────────────────────────────────────────────────

class TestPenugasan:
    def test_penugasan_integer(self):
        ns = jalankan("x = 42\n")
        assert ns["x"] == 42

    def test_penugasan_string(self):
        ns = jalankan('nama = "Pyind"\n')
        assert ns["nama"] == "Pyind"

    def test_penugasan_boolean_benar(self):
        ns = jalankan("aktif = benar\n")
        assert ns["aktif"] is True

    def test_penugasan_boolean_salah(self):
        ns = jalankan("aktif = salah\n")
        assert ns["aktif"] is False

    def test_penugasan_kosong(self):
        ns = jalankan("nilai = kosong\n")
        assert ns["nilai"] is None

    def test_penugasan_gabungan(self):
        ns = jalankan("x = 10\nx += 5\n")
        assert ns["x"] == 15

    def test_penugasan_ekspresi(self):
        ns = jalankan("hasil = 3 * 4 + 2\n")
        assert ns["hasil"] == 14


# ── Test operasi ──────────────────────────────────────────────────────────────

class TestOperasi:
    def test_penjumlahan(self):
        ns = jalankan("h = 1 + 2\n")
        assert ns["h"] == 3

    def test_pengurangan(self):
        ns = jalankan("h = 10 - 3\n")
        assert ns["h"] == 7

    def test_perkalian(self):
        ns = jalankan("h = 4 * 5\n")
        assert ns["h"] == 20

    def test_pembagian(self):
        ns = jalankan("h = 10 / 4\n")
        assert abs(ns["h"] - 2.5) < 1e-9

    def test_pembagian_bulat(self):
        ns = jalankan("h = 10 // 3\n")
        assert ns["h"] == 3

    def test_modulo(self):
        ns = jalankan("h = 10 % 3\n")
        assert ns["h"] == 1

    def test_eksponen(self):
        ns = jalankan("h = 2 ** 8\n")
        assert ns["h"] == 256

    def test_eksponen_chaining_right_associative(self):
        """2 ** 3 ** 2 harus 2**(3**2) = 512, bukan (2**3)**2 = 64."""
        ns = jalankan("h = 2 ** 3 ** 2\n")
        assert ns["h"] == 512

    def test_eksponen_dengan_kurung_kiri(self):
        """Kurung eksplisit mengubah asosiativitas: (2**3)**2 = 64."""
        ns = jalankan("h = (2 ** 3) ** 2\n")
        assert ns["h"] == 64

    def test_eksponen_unary_minus(self):
        """-2**2 harus -(2**2) = -4, bukan (-2)**2 = 4."""
        ns = jalankan("h = -2 ** 2\n")
        assert ns["h"] == -4

    def test_operator_dan(self):
        ns = jalankan("h = benar dan salah\n")
        assert ns["h"] is False

    def test_operator_atau(self):
        ns = jalankan("h = benar atau salah\n")
        assert ns["h"] is True

    def test_operator_bukan(self):
        ns = jalankan("h = bukan benar\n")
        assert ns["h"] is False


# ── Test if/elif/else ─────────────────────────────────────────────────────────

class TestJika:
    def test_jika_benar(self):
        ns = jalankan("x = 0\njika benar:\n    x = 1\n")
        assert ns["x"] == 1

    def test_jika_salah_tidak_dieksekusi(self):
        ns = jalankan("x = 0\njika salah:\n    x = 1\n")
        assert ns["x"] == 0

    def test_jika_lainnya(self):
        ns = jalankan("x = 0\njika salah:\n    x = 1\nlainnya:\n    x = 2\n")
        assert ns["x"] == 2

    def test_jika_tidak(self):
        source = "n = 5\njika n > 10:\n    hasil = 'besar'\njika_tidak n > 0:\n    hasil = 'positif'\nlainnya:\n    hasil = 'negatif'\n"
        ns = jalankan(source)
        assert ns["hasil"] == "positif"

    def test_perbandingan_sama(self):
        ns = jalankan("x = 5\njika x == 5:\n    ok = benar\n")
        assert ns["ok"] is True


# ── Test while ────────────────────────────────────────────────────────────────

class TestSelama:
    def test_hitung_mundur(self):
        source = "i = 0\nselama i < 5:\n    i += 1\n"
        ns = jalankan(source)
        assert ns["i"] == 5

    def test_akumulasi(self):
        source = "total = 0\ni = 1\nselama i <= 10:\n    total += i\n    i += 1\n"
        ns = jalankan(source)
        assert ns["total"] == 55

    def test_break(self):
        source = "i = 0\nselama benar:\n    i += 1\n    jika i == 5:\n        hentikan\n"
        ns = jalankan(source)
        assert ns["i"] == 5


# ── Test for ──────────────────────────────────────────────────────────────────

class TestUntuk:
    def test_for_range(self):
        source = "total = 0\nuntuk i dalam rentang(5):\n    total += i\n"
        ns = jalankan(source)
        assert ns["total"] == 10   # 0+1+2+3+4

    def test_for_list(self):
        source = "hasil = []\nuntuk x dalam [1, 2, 3]:\n    hasil.append(x * 2)\n"
        ns = jalankan(source)
        assert ns["hasil"] == [2, 4, 6]

    def test_continue(self):
        source = "hasil = []\nuntuk i dalam rentang(6):\n    jika i % 2 == 0:\n        lanjut\n    hasil.append(i)\n"
        ns = jalankan(source)
        assert ns["hasil"] == [1, 3, 5]


# ── Test fungsi ───────────────────────────────────────────────────────────────

class TestFungsi:
    def test_fungsi_tanpa_parameter(self):
        source = "fungsi halo():\n    kembali 42\nhasil = halo()\n"
        ns = jalankan(source)
        assert ns["hasil"] == 42

    def test_fungsi_dengan_parameter(self):
        source = "fungsi tambah(a, b):\n    kembali a + b\nhasil = tambah(3, 4)\n"
        ns = jalankan(source)
        assert ns["hasil"] == 7

    def test_fungsi_rekursif(self):
        source = "fungsi faktorial(n):\n    jika n <= 1:\n        kembali 1\n    kembali n * faktorial(n - 1)\nhasil = faktorial(5)\n"
        ns = jalankan(source)
        assert ns["hasil"] == 120

    def test_fungsi_dengan_default(self):
        source = "fungsi sapa(nama, salam='Halo'):\n    kembali salam + ' ' + nama\nhasil = sapa('Budi')\n"
        ns = jalankan(source)
        assert ns["hasil"] == "Halo Budi"


# ── Test string safety ────────────────────────────────────────────────────────

class TestStringSafety:
    def test_keyword_dalam_string_aman(self):
        """Kata kunci di dalam string harus TIDAK ikut diterjemahkan."""
        source = 'pesan = "jika hujan lebat"\n'
        ns = jalankan(source)
        # String harus tetap mengandung 'jika', bukan 'if'
        assert "jika" in ns["pesan"]
        assert ns["pesan"] == "jika hujan lebat"

    def test_string_dengan_banyak_keyword(self):
        source = 'kalimat = "untuk selama jika lainnya"\n'
        ns = jalankan(source)
        assert ns["kalimat"] == "untuk selama jika lainnya"

    def test_cetak_string_dengan_keyword(self):
        """Fungsi cetak dengan argumen string yang mengandung keyword."""
        kode = tr('cetak("jika hujan")\n')
        assert 'print("jika hujan")' in kode
        # 'jika' di luar tanda kutip tidak ada (sudah diganti 'if')
        # 'jika' di dalam tanda kutip tetap ada
        assert '"jika hujan"' in kode


# ── Test impor ────────────────────────────────────────────────────────────────

class TestImpor:
    def test_impor_math(self):
        kode = tr("impor math\n")
        assert kode.strip() == "import math"

    def test_impor_dengan_alias(self):
        kode = tr("impor numpy sebagai np\n")
        assert "import numpy as np" in kode

    def test_dari_impor(self):
        kode = tr("dari math impor sqrt\n")
        assert "from math import sqrt" in kode


# ── Test try/except ───────────────────────────────────────────────────────────

class TestCoba:
    def test_coba_tanpa_error(self):
        source = "hasil = 0\ncoba:\n    hasil = 1\nkecuali:\n    hasil = -1\n"
        ns = jalankan(source)
        assert ns["hasil"] == 1

    def test_kecuali_menangkap_error(self):
        source = "tangkap = salah\ncoba:\n    x = 1 / 0\nkecuali ZeroDivisionError:\n    tangkap = benar\n"
        ns = jalankan(source)
        assert ns["tangkap"] is True


# ── Test kelas ────────────────────────────────────────────────────────────────

class TestKelas:
    def test_kelas_sederhana(self):
        source = (
            "kelas Titik:\n"
            "    fungsi __init__(diri, x, y):\n"
            "        diri.x = x\n"
            "        diri.y = y\n"
            "p = Titik(3, 4)\n"
            "hasil_x = p.x\n"
        )
        ns = jalankan(source)
        assert ns["hasil_x"] == 3

    def test_kelas_dengan_metode(self):
        source = (
            "kelas Persegi:\n"
            "    fungsi __init__(diri, sisi):\n"
            "        diri.sisi = sisi\n"
            "    fungsi luas(diri):\n"
            "        kembali diri.sisi * diri.sisi\n"
            "p = Persegi(5)\n"
            "hasil = p.luas()\n"
        )
        ns = jalankan(source)
        assert ns["hasil"] == 25


# ── Test pembangkitan kode ────────────────────────────────────────────────────

class TestPembangkitanKode:
    """Verifikasi string Python yang dihasilkan secara langsung."""

    def test_keyword_bahasa_indonesia_diganti(self):
        kode = tr("cetak('halo')\n")
        assert "print" in kode
        assert "cetak" not in kode

    def test_jika_menjadi_if(self):
        kode = tr("jika x:\n    lewati\n")
        assert "if x:" in kode
        assert "jika" not in kode

    def test_selama_menjadi_while(self):
        kode = tr("selama benar:\n    lewati\n")
        assert "while True:" in kode

    def test_untuk_menjadi_for(self):
        kode = tr("untuk i dalam rentang(3):\n    lewati\n")
        assert "for i in range(3):" in kode

    def test_fungsi_menjadi_def(self):
        kode = tr("fungsi f():\n    lewati\n")
        assert "def f():" in kode

    def test_kelas_menjadi_class(self):
        kode = tr("kelas A:\n    lewati\n")
        assert "class A:" in kode

    def test_indentasi_benar(self):
        source = "jika benar:\n    x = 1\n"
        kode = tr(source)
        baris = kode.split("\n")
        assert baris[0] == "if True:"
        assert baris[1] == "    x = 1"

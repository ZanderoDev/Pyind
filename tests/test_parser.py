"""
test_parser.py — Unit test untuk parser Pyind.
Jalankan dengan: pytest tests/test_parser.py -v
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from parser import parse


# ── Helpers ───────────────────────────────────────────────────────────────────

def pertama(source: str) -> dict:
    """Parse dan ambil pernyataan pertama dari modul."""
    ast = parse(source)
    assert ast["jenis"] == "Modul"
    assert len(ast["tubuh"]) > 0, "Tidak ada pernyataan yang diparsing"
    return ast["tubuh"][0]


# ── Test penugasan ────────────────────────────────────────────────────────────

class TestPenugasan:
    def test_penugasan_sederhana(self):
        stmt = pertama("x = 5\n")
        assert stmt["jenis"] == "Penugasan"
        assert stmt["target"]["nama"] == "x"
        assert stmt["nilai"]["nilai"] == 5

    def test_penugasan_string(self):
        stmt = pertama('nama = "Ali"\n')
        assert stmt["jenis"] == "Penugasan"
        assert stmt["nilai"]["jenis"] == "Teks"

    def test_penugasan_gabungan_tambah(self):
        stmt = pertama("x += 1\n")
        assert stmt["jenis"] == "PenugasanGabungan"
        assert stmt["op"] == "+="

    def test_penugasan_gabungan_kali(self):
        stmt = pertama("x *= 2\n")
        assert stmt["jenis"] == "PenugasanGabungan"
        assert stmt["op"] == "*="


# ── Test ekspresi ─────────────────────────────────────────────────────────────

class TestEkspresi:
    def test_literal_angka(self):
        stmt = pertama("42\n")
        assert stmt["ekspresi"]["nilai"] == 42

    def test_literal_boolean_benar(self):
        stmt = pertama("benar\n")
        assert stmt["ekspresi"]["jenis"] == "Boolean"
        assert stmt["ekspresi"]["nilai"] is True

    def test_literal_boolean_salah(self):
        stmt = pertama("salah\n")
        assert stmt["ekspresi"]["nilai"] is False

    def test_literal_kosong(self):
        stmt = pertama("kosong\n")
        assert stmt["ekspresi"]["jenis"] == "Kosong"

    def test_operasi_aritmetika(self):
        stmt = pertama("1 + 2\n")
        eksp = stmt["ekspresi"]
        assert eksp["jenis"] == "BinOp"
        assert eksp["op"] == "+"

    def test_operasi_perbandingan(self):
        stmt = pertama("a == b\n")
        eksp = stmt["ekspresi"]
        assert eksp["jenis"] == "BinOp"
        assert eksp["op"] == "=="

    def test_list_kosong(self):
        stmt = pertama("[]\n")
        assert stmt["ekspresi"]["jenis"] == "Daftar"
        assert stmt["ekspresi"]["elemen"] == []

    def test_list_dengan_elemen(self):
        stmt = pertama("[1, 2, 3]\n")
        eksp = stmt["ekspresi"]
        assert eksp["jenis"] == "Daftar"
        assert len(eksp["elemen"]) == 3

    def test_dict_kosong(self):
        stmt = pertama("{}\n")
        assert stmt["ekspresi"]["jenis"] == "Kamus"

    def test_tuple(self):
        stmt = pertama("(1, 2)\n")
        assert stmt["ekspresi"]["jenis"] == "Tuple"
        assert len(stmt["ekspresi"]["elemen"]) == 2


# ── Test pemanggilan fungsi ───────────────────────────────────────────────────

class TestPanggilan:
    def test_panggilan_tanpa_argumen(self):
        stmt = pertama("cetak()\n")
        eksp = stmt["ekspresi"]
        assert eksp["jenis"] == "Panggilan"
        assert eksp["fungsi"]["nama"] == "print"
        assert eksp["argumen"] == []

    def test_panggilan_dengan_argumen(self):
        stmt = pertama('cetak("halo")\n')
        eksp = stmt["ekspresi"]
        assert eksp["jenis"] == "Panggilan"
        assert len(eksp["argumen"]) == 1

    def test_panggilan_dengan_keyword_arg(self):
        stmt = pertama("cetak(end='')\n")
        eksp = stmt["ekspresi"]
        assert eksp["argumen"][0]["jenis"] == "ArgKunci"
        assert eksp["argumen"][0]["nama"] == "end"

    def test_akses_atribut(self):
        stmt = pertama("obj.metode()\n")
        eksp = stmt["ekspresi"]
        assert eksp["jenis"] == "Panggilan"
        assert eksp["fungsi"]["jenis"] == "Atribut"
        assert eksp["fungsi"]["atribut"] == "metode"


# ── Test if/elif/else ─────────────────────────────────────────────────────────

class TestJika:
    def test_jika_sederhana(self):
        source = "jika x > 0:\n    cetak(x)\n"
        stmt = pertama(source)
        assert stmt["jenis"] == "Jika"
        assert stmt["kondisi"]["jenis"] == "BinOp"
        assert len(stmt["then"]) == 1

    def test_jika_lainnya(self):
        source = "jika x > 0:\n    cetak(1)\nlainnya:\n    cetak(0)\n"
        stmt = pertama(source)
        assert stmt["jenis"] == "Jika"
        assert len(stmt["else"]) == 1

    def test_jika_jika_tidak(self):
        source = "jika x > 0:\n    cetak(1)\njika_tidak x == 0:\n    cetak(0)\nlainnya:\n    cetak(-1)\n"
        stmt = pertama(source)
        assert len(stmt["elif"]) == 1
        assert stmt["elif"][0]["kondisi"]["op"] == "=="


# ── Test while ────────────────────────────────────────────────────────────────

class TestSelama:
    def test_selama_sederhana(self):
        source = "selama i < 10:\n    i += 1\n"
        stmt = pertama(source)
        assert stmt["jenis"] == "Selama"
        assert stmt["kondisi"]["op"] == "<"
        assert len(stmt["tubuh"]) == 1


# ── Test for ──────────────────────────────────────────────────────────────────

class TestUntuk:
    def test_untuk_range(self):
        source = "untuk i dalam rentang(10):\n    cetak(i)\n"
        stmt = pertama(source)
        assert stmt["jenis"] == "Untuk"
        assert stmt["target"]["nama"] == "i"
        assert stmt["iterable"]["jenis"] == "Panggilan"

    def test_untuk_list(self):
        source = "untuk item dalam daftar_belanja:\n    cetak(item)\n"
        stmt = pertama(source)
        assert stmt["jenis"] == "Untuk"
        assert stmt["target"]["nama"] == "item"


# ── Test fungsi ───────────────────────────────────────────────────────────────

class TestFungsi:
    def test_definisi_fungsi_kosong(self):
        source = "fungsi halo():\n    lewati\n"
        stmt = pertama(source)
        assert stmt["jenis"] == "DefinisiFungsi"
        assert stmt["nama"] == "halo"
        assert stmt["parameter"] == []

    def test_definisi_fungsi_dengan_parameter(self):
        source = "fungsi tambah(a, b):\n    kembali a + b\n"
        stmt = pertama(source)
        assert stmt["jenis"] == "DefinisiFungsi"
        assert len(stmt["parameter"]) == 2
        assert stmt["parameter"][0]["nama"] == "a"

    def test_return_nilai(self):
        source = "fungsi satu():\n    kembali 1\n"
        stmt = pertama(source)
        tubuh_0 = stmt["tubuh"][0]
        assert tubuh_0["jenis"] == "Kembali"
        assert tubuh_0["nilai"]["nilai"] == 1

    def test_return_tanpa_nilai(self):
        source = "fungsi kosong_return():\n    kembali\n"
        stmt = pertama(source)
        assert stmt["tubuh"][0]["nilai"] is None


# ── Test impor ────────────────────────────────────────────────────────────────

class TestImpor:
    def test_impor_sederhana(self):
        stmt = pertama("impor math\n")
        assert stmt["jenis"] == "Impor"
        assert stmt["nama"] == "math"
        assert stmt["alias"] is None

    def test_impor_dengan_alias(self):
        stmt = pertama("impor numpy sebagai np\n")
        assert stmt["alias"] == "np"

    def test_dari_impor(self):
        stmt = pertama("dari math impor sqrt\n")
        assert stmt["jenis"] == "DariImpor"
        assert stmt["modul"] == "math"
        assert stmt["nama"][0]["nama"] == "sqrt"


# ── Test try/except ───────────────────────────────────────────────────────────

class TestCoba:
    def test_coba_kecuali(self):
        source = "coba:\n    x = 1\nkecuali:\n    lewati\n"
        stmt = pertama(source)
        assert stmt["jenis"] == "CobaDanKecuali"
        assert len(stmt["handler"]) == 1

    def test_coba_kecuali_dengan_tipe(self):
        source = "coba:\n    x = 1\nkecuali ValueError:\n    lewati\n"
        stmt = pertama(source)
        assert stmt["handler"][0]["tipe"] is not None


# ── Test kelas ────────────────────────────────────────────────────────────────

class TestKelas:
    def test_definisi_kelas_kosong(self):
        source = "kelas Hewan:\n    lewati\n"
        stmt = pertama(source)
        assert stmt["jenis"] == "DefinisiKelas"
        assert stmt["nama"] == "Hewan"
        assert stmt["induk"] == []

    def test_definisi_kelas_dengan_induk(self):
        source = "kelas Anjing(Hewan):\n    lewati\n"
        stmt = pertama(source)
        assert len(stmt["induk"]) == 1

"""
test_regresi.py — Uji regresi Pyind.
Jalankan dengan: pytest tests/test_regresi.py -v

Berkas ini mengunci perilaku yang mudah rusak: nama kontekstual sebagai
identifier, slice kosong, perbandingan berantai, literal angka/string yang
harus ditulis apa adanya, async/await/yield/walrus, dekorator, dan
parameter modern.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from lexer import Lexer, TipeToken
from parser import Parser
from parser import urai as urai_modul
from transpiler import Transpiler
from transpiler import terjemahkan as terjemahkan_modul
from errors import PyindError, KesalahanLeksikal, KesalahanSintaks


# ── Helpers ──────────────────────────────────────────────────────────────────

def tr(source: str) -> str:
    """Transpilasi penuh; kembalikan kode Python tanpa spasi tepi."""
    tokens = Lexer(source).tokenisasi()
    ast = Parser(tokens).urai()
    return Transpiler().terjemahkan(ast).strip()


def jalankan(source: str) -> dict:
    """Transpilasi lalu eksekusi; kembalikan namespace hasil."""
    kode = tr(source)
    ns: dict = {}
    exec(compile(kode, "<regresi>", "exec"), ns)
    return ns


def hasil(source: str):
    """Jalankan satu ekspresi Pyind dan kembalikan nilainya."""
    ns: dict = {}
    kode = tr(source)
    exec(compile(kode, "<regresi>", "exec"), ns)
    return ns.get("hasil")


# ── Alias API Indonesia ─────────────────────────────────────────────────────

class TestApiIndonesia:
    def test_lexer_tokenisasi(self):
        assert Lexer("x = 1\n").tokenisasi()[0].tipe is TipeToken.NAMA

    def test_parser_urai(self):
        ast = Parser(Lexer("x = 1\n").tokenisasi()).urai()
        assert ast["jenis"] == "Modul"

    def test_transpiler_terjemahkan(self):
        assert Transpiler().terjemahkan(urai_modul("x = 1\n")) == "x = 1\n"

    def test_alias_inggris_masih_ada(self):
        assert Lexer.tokenize is Lexer.tokenisasi
        assert Parser.parse is Parser.urai
        assert Transpiler.transpile is Transpiler.terjemahkan
        assert urai_modul is Parser.urai or callable(urai_modul)
        assert callable(terjemahkan_modul)

    def test_knowledge_pada_kata_kunci(self):
        token = Lexer("cetak").tokenisasi()[0]
        assert token.tipe is TipeToken.KATA_KUNCI
        assert token.nilai == "print"
        assert token.teks_asli == "cetak"


# ── Nama kontekstual sebagai identifier ────────────────────────────────────

class TestNamaSebagaiIdentifier:
    @pytest.mark.parametrize("nama", ["cetak", "panjang", "dalam", "daftar", "teks"])
    def test_nama_bebas_boleh_dipakai(self, nama):
        kode = tr(f"{nama} = 1\n")
        assert kode == f"{nama} = 1"

    def test_metode_bernama_kosong(self):
        kode = tr("diri.kosong()\n")
        assert "diri.kosong()" in kode
        assert "None()" not in kode

    def test_metode_bernama_cetak(self):
        kode = tr("diri.cetak()\n")
        assert "diri.cetak()" in kode

    def test_alias_mati_setelah_di_bind(self):
        kode = tr("cetak = fungsi_lain\ncetak('halo')\n")
        assert "cetak('halo')" in kode
        assert "print" not in kode

    def test_tetap_alias_bila_tidak_di_bind(self):
        assert "print('halo')" in tr("cetak('halo')\n")

    def test_binding_di_fungsi_tidak_mematikan_alias_global(self):
        kode = tr("fungsi f():\n    cetak = 1\ncetak('halo')\n")
        assert "cetak = 1" in kode
        assert "print('halo')" in kode

    def test_dalam_bisa_dipakai(self):
        ns = jalankan("dalam = 5\nhasil = dalam + 1\n")
        assert ns["hasil"] == 6


# ── Slice ───────────────────────────────────────────────────────────────────

class TestSlice:
    def test_slice_kosong(self):
        assert tr("a[:]\n") == "a[:]"

    def test_slice_awal_kosong(self):
        assert tr("a[:2]\n") == "a[:2]"

    def test_slice_akhir_kosong(self):
        assert tr("a[1:]\n") == "a[1:]"

    def test_slice_langkah_kosong(self):
        assert tr("a[::2]\n") == "a[::2]"

    def test_slice_nol_ditulis_penuh(self):
        """Ekspresi bernilai 0 bukan berarti kosong."""
        kode = tr("a[0:0]\n")
        assert kode == "a[0:0]"

    def test_slice_langkah_nol_ditulis_penuh(self):
        assert tr("a[::0]\n") == "a[::0]"

    def test_slice_negatif(self):
        assert tr("a[-1:-2]\n") == "a[-1:-2]"

    def test_subskrip_nilai_nol(self):
        assert tr("a[0]\n") == "a[0]"


# ── Perbandingan berantai ───────────────────────────────────────────────────

class TestPerbandinganRantai:
    def test_rantai_tiga_ruas(self):
        kode = tr("a < b < c\n")
        assert kode == "a < b and b < c"

    def test_rantai_campuran(self):
        kode = tr("1 < x <= 10\n")
        assert "and" in kode

    def test_rantai_nilai_benar(self):
        assert hasil("x = 5\nhasil = 1 < x < 10\n") is True

    def test_rantai_nilai_salah(self):
        assert hasil("x = 50\nhasil = 1 < x < 10\n") is False

    def test_perbandingan_tunggal_tetap_berfungsi(self):
        assert hasil("hasil = 1 < 2\n") is True

    def test_rantai_dalam_kondisi(self):
        assert hasil("x = 5\nhasil = 1 < x < 10 dan x != 7\n") is True


# ── Literal angka & string ──────────────────────────────────────────────────

class TestLiteral:
    @pytest.mark.parametrize("sumber,nilai", [
        ("42", 42),
        ("3.14", 3.14),
        ("1_000_000", 1000000),
        ("0b1010", 10),
        ("0o17", 15),
        ("0x1f", 31),
        ("0x_1f", 31),
        ("0xDEAD_BEEF", 3735928559),
        ("1_0.0_1", 10.01),
        ("1.5e3", 1500.0),
        ("10.", 10.0),
        (".5", 0.5),
    ])
    def test_bentuk_sumber_terjaga(self, sumber, nilai):
        kode = tr(f"x = {sumber}\n")
        assert kode == f"x = {sumber}"
        ns = jalankan(f"x = {sumber}\n")
        assert ns["x"] == pytest.approx(nilai)

    def test_literal_kompleks(self):
        ns = jalankan("z = 2j\n")
        assert ns["z"] == 2j
        assert isinstance(ns["z"], complex)

    def test_literal_kompleks_real(self):
        ns = jalankan("z = 1.5j\n")
        assert ns["z"] == 1.5j

    def test_kompleks_dalam_aritmetika(self):
        ns = jalankan("hasil = 2j * 3\n")
        assert ns["hasil"] == 6j

    @pytest.mark.parametrize("sumber", ['rb"ab"', "br'x'", 'fr"a{}"', 'rf"a"', 'u"abc"', 'b"data"'])
    def test_prefiks_string(self, sumber):
        assert tr(f"x = {sumber}\n") == f"x = {sumber}"

    def test_raw_bytes_terpakai_benar(self):
        ns = jalankan("x = rb'\\x41'\n")
        assert ns["x"] == b"\\x41"

    def test_string_besar_utuh(self):
        kode = tr('x = """halo\ndunia"""\n')
        assert '"""halo' in kode


# ── Angka salah ─────────────────────────────────────────────────────────────

class TestAngkaTidakValid:
    @pytest.mark.parametrize("sumber", ["0123", "0x", "1.2e", "1__2", "123abc", "0b2"])
    def test_ditolak(self, sumber):
        with pytest.raises(KesalahanLeksikal):
            Lexer(sumber).tokenisasi()


# ── async / await / yield / walrus ──────────────────────────────────────────

class TestAsyncAwaitYieldWalrus:
    def test_async_fungsi(self):
        assert tr("async fungsi f():\n    kembali 1\n").startswith("async def f():")

    def test_await(self):
        kode = tr("async fungsi f():\n    x = await ambil()\n    kembali x\n")
        assert "await ambil()" in kode

    def test_async_for(self):
        kode = tr("async fungsi f():\n    async untuk i dalam data:\n        lewati\n")
        assert "async for i in data:" in kode

    def test_async_with(self):
        kode = tr("async fungsi f():\n    async bersama f() sebagai g:\n        lewati\n")
        assert "async with f() as g:" in kode

    def test_yield(self):
        kode = tr("fungsi g():\n    hasilkan 1\n")
        assert "yield 1" in kode

    def test_yield_dari(self):
        kode = tr("fungsi g():\n    hasilkan_dari [1, 2]\n")
        assert "yield from [1, 2]" in kode

    def test_yield_tanpa_nilai(self):
        assert "yield" in tr("fungsi g():\n    hasilkan\n")

    def test_walrus_dalam_kondisi(self):
        kode = tr("jika (n := panjang(a)) > 2:\n    cetak(n)\n")
        assert "(n := len(a))" in kode

    def test_walrus_langsung(self):
        ns = jalankan("hasil = (n := 5)\n")
        assert ns["hasil"] == 5

    def test_walrus_menbriefkan(self):
        assert hasil("data = [1, 2, 3]\nhasil = (n := panjang(data)) > 2\n") is True


# ── Dekorator ───────────────────────────────────────────────────────────────

class TestDekorator:
    def test_dekorator_fungsi(self):
        kode = tr("@deco\nfungsi f():\n    lewati\n")
        assert kode.split("\n")[0] == "@deco"
        assert "def f():" in kode

    def test_dekorator_kelas(self):
        kode = tr("@deco\nkelas A:\n    lewati\n")
        assert kode.split("\n")[0] == "@deco"
        assert "class A:" in kode

    def test_dekorator_beberapa(self):
        kode = tr("@a\n@b\nfungsi f():\n    lewati\n")
        assert kode.split("\n")[0] == "@a"
        assert kode.split("\n")[1] == "@b"

    def test_dekorator_dengan_argumen(self):
        kode = tr("@deko(1)\nfungsi f():\n    lewati\n")
        assert "@deko(1)" in kode


# ── Parameter modern ────────────────────────────────────────────────────────

class TestParameterModern:
    def test_positional_only(self):
        assert tr("fungsi f(a, /):\n    lewati\n") == "def f(a, /):\n    pass"

    def test_positional_only_campuran(self):
        kode = tr("fungsi f(a, b, /, c):\n    lewati\n").split("\n")[0]
        assert kode == "def f(a, b, /, c):"

    def test_keyword_only(self):
        assert tr("fungsi f(a, *, b):\n    lewati\n").split("\n")[0] == "def f(a, *, b):"

    def test_keyword_only_default(self):
        kode = tr("fungsi f(a, *, b=1):\n    lewati\n").split("\n")[0]
        assert kode == "def f(a, *, b = 1):"

    def test_args_kwargs(self):
        kode = tr("fungsi f(*a, **k):\n    lewati\n").split("\n")[0]
        assert kode == "def f(*a, **k):"

    def test_anotasi_sederhana(self):
        kode = tr("fungsi f(a: int) -> str:\n    kembali 'x'\n").split("\n")[0]
        assert kode == "def f(a: int) -> str:"

    def test_anotasi_union(self):
        kode = tr("fungsi f(a: int | str):\n    lewati\n").split("\n")[0]
        assert kode == "def f(a: int | str):"

    def test_anotasi_generik(self):
        kode = tr("fungsi f(a: daftar[int]):\n    lewati\n").split("\n")[0]
        assert kode == "def f(a: list[int]):"

    def test_anotasi_union_dengan_nilai_bawaan(self):
        kode = tr("fungsi f(a: daftar[int] | kosong = kosong):\n    lewati\n").split("\n")[0]
        assert kode == "def f(a: list[int] | None = None):"


# ── Determinisme & kompilasi ────────────────────────────────────────────────

class TestDeterminismeDanKompilasi:
    KASUS = [
        'cetak("halo")\n',
        "x = 1\ny = x + 2\n",
        "fungsi f(a, b):\n    kembali a * b\nhasil = f(2, 3)\n",
        "kelas A:\n    fungsi __init__(diri):\n        diri.x = 1\n",
        "untuk i dalam rentang(3):\n    cetak(i)\n",
        "coba:\n    x = 1\nkecuali ValueError:\n    x = 2\n",
        "d = {'a': 1}\n",
        "s = {1, 2}\n",
        "hasil = [x * 2 untuk x dalam rentang(3)]\n",
        "hasil = {x: x * 2 untuk x dalam rentang(3)}\n",
        "hasil = (x untuk x dalam rentang(3))\n",
        "fungsi f(a=1, *args, **kwargs):\n    lewati\n",
        "async fungsi f():\n    await g()\n",
        "@deco\nfungsi f():\n    lewati\n",
        "hasil = a if benar else salah\n",
        "hasil = lambda x: x + 1\n",
        "x = 2 ** 3 ** 2\n",
        "hasil = -2 ** 2\n",
        "cetak(f\"nilai: {x}\")\n",
    ]

    @pytest.mark.parametrize("source", KASUS)
    def test_keluaran_deterministik(self, source):
        assert tr(source) == tr(source)

    @pytest.mark.parametrize("source", KASUS)
    def test_keluaran_bisa_dikompilasi(self, source):
        kode = tr(source)
        compile(kode, "<regresi>", "exec")


# ── Indentasi ───────────────────────────────────────────────────────────────

class TestIndentasi:
    def test_indentasi_awal_ditolak(self):
        with pytest.raises(KesalahanLeksikal):
            Lexer("    x = 1\n").tokenisasi()

    def test_tab_dan_spasi_setara(self):
        """Tab = 8 kolom, sama seperti Python."""
        kode_tab = tr("jika benar:\n\tcetak(1)\n")
        kode_spasi = tr("jika benar:\n        cetak(1)\n")
        assert kode_tab == kode_spasi

    def test_blok_nested(self):
        kode = tr("jika a:\n    jika b:\n        lewati\ncetak(1)\n")
        assert kode.split("\n")[2] == "        pass"
        assert kode.split("\n")[3] == "print(1)"

    def test_baris_kosong_diabaikan(self):
        kode = tr("x = 1\n\n\n\ny = 2\n")
        assert kode == "x = 1\ny = 2"

    def test_komentar_diabaikan(self):
        kode = tr("# catatan\nx = 1\n# lagi\n")
        assert kode == "x = 1"

    def test_pernyataan_setelah_return(self):
        kode = tr("fungsi f():\n    kembali 1\n    cetak('tidak')\n")
        assert "return 1" in kode
        assert "print('tidak')" in kode


# ── String & komentar aman ──────────────────────────────────────────────────

class TestKesamananString:
    def test_kata_kunci_dalam_string_utuh(self):
        assert hasil('x = "jika hujan"\nhasil = x\n') == "jika hujan"

    def test_komentar_utuh(self):
        kode = tr("x = 1  # jika dan untuk\n")
        assert kode == "x = 1"

    def test_escaped_quote(self):
        ns = jalankan("x = \"a\\\"b\"\n")
        assert ns["x"] == 'a"b'

    def test_backslash_lanjutan_baris(self):
        kode = tr("x = 1 + \\\n    2\n")
        assert "2" in kode


# ── Galat sintaks ───────────────────────────────────────────────────────────

class TestGalatSintaks:
    @pytest.mark.parametrize("source", [
        "jika benar\n    x = 1\n",
        "fungsi f(:\n    lewati\n",
        "fungsi ():\n    lewati\n",
        "x = = 1\n",
        "kelas :\n    lewati\n",
        "untuk i rentang(3):\n    lewati\n",
        "jika benar:\nlewati\n",
    ])
    def test_galat_adalah_pyind_error(self, source):
        with pytest.raises(PyindError):
            urai_modul(source)

    def test_kata_kunci_umum_tidak_bisa_jadi_nama(self):
        with pytest.raises(KesalahanSintaks):
            urai_modul("fungsi = 1\n")

    def test_pesan_error_memuat_lokasi(self):
        with pytest.raises(KesalahanSintaks) as info:
            urai_modul("jika benar\n")
        assert "baris 1" in str(info.value)

    def test_string_tidak_ditutup(self):
        with pytest.raises(KesalahanLeksikal):
            Lexer('x = "abc\n').tokenisasi()


# ── Eksponen & presedensi ───────────────────────────────────────────────────

class TestPresedensi:
    def test_eksponen_kanan(self):
        assert hasil("hasil = 2 ** 3 ** 2\n") == 512

    def test_eksponen_kurung_kiri(self):
        assert hasil("hasil = (2 ** 3) ** 2\n") == 64

    def test_unary_minus_eksponen(self):
        assert hasil("hasil = -2 ** 2\n") == -4

    def test_kurung_kiri_eksponen(self):
        assert hasil("hasil = (-2) ** 2\n") == 4

    def test_perkalian_lebih_tinggi_penjumlahan(self):
        assert hasil("hasil = 2 + 3 * 4\n") == 14

    def test_dan_lebih_tinggi_atau(self):
        assert hasil("hasil = benar atau salah dan salah\n") is True

    def test_bukan_lebih_tinggi_dan(self):
        assert hasil("hasil = bukan salah dan benar\n") is True


# ── Regresi: nama fungsi buatan pengguna tidak tertimpa alias ───────────────

class TestNamaBuatanTidakTertimpa:
    def test_fungsi_bernama_alias_builtin(self):
        """'fungsi jumlahkan(...)' tidak boleh jadi 'def sum(...)'."""
        kode = tr("fungsi jumlahkan(a):\n    kembali a\nhasil = jumlahkan(1)\n")
        assert "def jumlahkan(a):" in kode
        assert "def sum(" not in kode
        assert kode.endswith("hasil = jumlahkan(1)")

    def test_fungsi_bernama_cetak_tetap_cetak(self):
        kode = tr("fungsi cetak(x):\n    kembali x\nhasil = cetak(1)\n")
        assert "def cetak(x):" in kode
        assert "print(1)" not in kode

    def test_fungsi_bernama_panjang_tetap_panjang(self):
        kode = tr("fungsi panjang(x):\n    kembali x\nhasil = panjang(1)\n")
        assert "def panjang(x):" in kode
        assert "len(1)" not in kode

    def test_parameter_bernama_alias(self):
        kode = tr("fungsi f(cetak):\n    kembali cetak\n")
        assert "def f(cetak):" in kode
        assert "def f(print):" not in kode

    def test_metode_bernama_alias(self):
        kode = tr("diri.cetak(x)\n")
        assert "diri.cetak(x)" in kode

    def test_kelas_bernama_alias(self):
        kode = tr("kelas cetak:\n    lewati\n")
        assert "class cetak:" in kode
        assert "class print:" not in kode

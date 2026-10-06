"""
transpiler.py — AST menjadi kode Python valid.
Bagian dari proyek Pyind (Python Indonesia).

Menelusuri pohon AST dari :mod:`parser` lalu menulis kode Python sebagai
teks. Modul ini murni pembangkitan teks: tidak ada ``eval()``, ``exec()``,
maupun ``compile()`` di sini.

Dua hal yang membuatnya lebih dari sekadar "pengganti kata kunci":

:data:`Resolver`
    Menentukan apakah sebuah nama bebas masih berarti *builtin* padanannya.
    ``cetak("halo")`` menjadi ``print("halo")``, tetapi begitu ``cetak``
    di-bind ke nilai lain, seluruh pemakaiannya menjadi ``cetak`` apa adanya.

Literal apa adanya
    Angka dan string ditulis ulang memakai bentuk sumber aslinya
    (``0x1f``, ``1_000``, ``rb"ab"``), bukan hasil ``repr()``.

Rujukan presedensi: https://docs.python.org/3/reference/expressions.html
"""

from __future__ import annotations

from typing import Any

from errors import err_simpul_tak_dikenal
from keywords import KATA_KUNCI_KONTEKSTUAL

#: Alias tipe untuk simpul AST.
Simpul = dict[str, Any]

#: Satu level indentasi (PEP 8).
INDENT = "    "

#: Presedensi operator; makin besar makin mengikat.
#: Sesuai tabel resmi Python.
PRESEDENSI: dict[str, int] = {
    "lambda": 1,
    "if-else": 2,
    "or": 3,
    "and": 4,
    "not": 5,
    "==": 6, "!=": 6, "<": 6, ">": 6, "<=": 6, ">=": 6,
    "in": 6, "not in": 6, "is": 6, "is not": 6,
    "|": 7,
    "^": 8,
    "&": 9,
    "<<": 10, ">>": 10,
    "+": 11, "-": 11,
    "*": 12, "/": 12, "//": 12, "%": 12, "@": 12,
    "await": 13,
    "**": 14,
    "unary": 15,   # +x, -x, ~x
    "atom": 16,    # x[i], x(...), x.a
}

#: Operator yang mengikat ke kanan.
ASOSIASI_KANAN: frozenset[str] = frozenset({"**"})

#: Nama builtin yang boleh ditulis apa adanya di Python.
NAMA_BAWAAN_PYTHON: frozenset[str] = frozenset({
    "print", "input", "len", "type", "int", "float", "str",
    "list", "dict", "set", "range", "sum", "sorted", "iter",
    "abs", "bool", "bytes", "complex", "frozenset", "hash",
    "id", "max", "min", "next", "object", "oct", "ord", "pow",
    "repr", "reversed", "round", "setattr", "slice", "sorted",
    "staticmethod", "classmethod", "property", "super",
    "enumerate", "filter", "map", "zip", "callable", "chr",
    "divmod", "getattr", "hasattr", "hex", "isinstance", "issubclass",
    "bin", "all", "any", "ascii", "format", "vars", "dir",
})

#: Nama yang tidak boleh ditulis apa adanya karena kata kunci Python.
TERLARANG: frozenset[str] = frozenset({
    "False", "None", "True", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else", "except",
    "finally", "for", "from", "global", "if", "import", "in", "is", "lambda",
    "nonlocal", "not", "or", "pass", "raise", "return", "try", "while",
    "with", "yield",
})


class Resolver:
    """
    Melacak nama yang sudah di-*bind* pada setiap scope.

    Resolver hanya perlu satu informasi: apakah sebuah nama bebas di scope ini
    sudah dipakai untuk nilai milik program sendiri. Kalau belum, nama seperti
    ``cetak`` masih boleh ditulis sebagai ``print``; kalau sudah, alias
    tersebut harus dimatikan.

    Sifat penting: shadowing bersifat *per-scope*. ``cetak`` yang di-bind di
    level modul tidak mematikan alias ``print`` di dalam fungsi, dan
    sebaliknya — persis seperti Python yang memakai namespace per frame.
    """

    def __init__(self) -> None:
        self._tumpukan: list[set[str]] = [set()]

    # ── Scope ────────────────────────────────────────────────────────────────

    def masuk(self) -> None:
        """Masuk scope baru (fungsi, kelas, lambda, comprehension)."""
        self._tumpukan.append(set())

    def keluar(self) -> None:
        """Keluar scope saat ini; kembali ke scope induk."""
        if len(self._tumpukan) > 1:
            self._tumpukan.pop()

    def _lingkup(self) -> set[str]:
        return self._tumpukan[-1]

    def ikat(self, nama: str) -> None:
        """Tandai ``nama`` sebagai milik program pada scope saat ini."""
        if nama:
            self._lingkup().add(nama)

    def terikat(self, nama: str) -> bool:
        """
        True bila ``nama`` sudah terikat di scope ini ATAU scope induk.

        Rantai scope diperiksa dari yang paling dalam ke luar, sehingga
        ``cetak`` yang di-bind di luar modul tetap membatalkan alias
        ``print`` di seluruh scope di bawahnya.
        """
        return any(nama in lingkup for lingkup in self._tumpukan)



class Transpiler:
    """
    Mengubah AST Pyind menjadi source Python.

    Contoh::

        ast = Parser(tokens).urai()
        kode = Transpiler().terjemahkan(ast)
    """

    def __init__(self) -> None:
        self.resolver = Resolver()

    # ── API publik ────────────────────────────────────────────────────────────

    def terjemahkan(self, ast: Simpul) -> str:
        """Terjemahkan simpul ``Modul`` menjadi kode Python."""
        baris = self._pernyataan_daftar(ast.get("tubuh", []), 0)
        kode = "\n".join(baris)
        return kode.rstrip("\n") + "\n" if kode.strip() else "\n"

    #: Alias kompatibilitas ke API Inggris.
    transpile = terjemahkan

    @staticmethod
    def _ind(level: int) -> str:
        """Indentasi untuk ``level`` tertentu."""
        return INDENT * level

    # ── Dispatcher ────────────────────────────────────────────────────────────

    def _pernyataan(self, simpul: Simpul, level: int) -> list[str]:
        """Teruskan ke handler ``_s_<jenis>``."""
        jenis = simpul.get("jenis", "")
        handler = getattr(self, f"_s_{jenis}", None)
        if handler is None:
            raise err_simpul_tak_dikenal(jenis)
        return handler(simpul, level)

    def _pernyataan_daftar(self, daftar: list[Simpul], level: int) -> list[str]:
        """Terjemahkan daftar pernyataan pada level indentasi tertentu."""
        hasil: list[str] = []
        for simpul in daftar:
            hasil.extend(self._pernyataan(simpul, level))
        return hasil

    def _blok(self, isi: list[Simpul], level: int) -> list[str]:
        """Terjemahkan isi blok; memakai ``pass`` bila kosong."""
        baris = self._pernyataan_daftar(isi, level + 1)
        return baris or [f"{self._ind(level + 1)}pass"]

    def _ekspresi(self, simpul: Simpul) -> str:
        """Terjemahkan satu ekspresi menjadi teks Python."""
        jenis = simpul.get("jenis", "")
        handler = getattr(self, f"_e_{jenis}", None)
        if handler is None:
            raise err_simpul_tak_dikenal(jenis)
        return handler(simpul)

    # ── PENGGANTI NAMA ────────────────────────────────────────────────────────

    def _nama(self, nama: str) -> str:
        """
        Terjemahkan nama bebas menjadi nama Python yang sah.

        Aturan:

        1. Kalau nama sudah terikat di scope ini/induk → pakai apa adanya.
        2. Kalau nama ada di leksikon kontekstual dan belum terikat →
           pakai padanan Python-nya (``cetak`` → ``print``).
        3. Kalau nama bentrok dengan kata kunci Python yang tak punya padanan
           (``async``, ``await``, ``match`` …) → beri akhiran ``_`` agar
           kode tetap valid.
        """
        if self.resolver.terikat(nama):
            return nama
        padanan = KATA_KUNCI_KONTEKSTUAL.get(nama)
        if padanan is not None:
            return padanan
        if nama in TERLARANG:
            return f"{nama}_"
        return nama

    def _daftar_nama(self, nama: list[str]) -> str:
        """Terjemahkan daftar nama (untuk ``global``/``nonlokal``)."""
        return ", ".join(self._nama(n) for n in nama)

    # ── Pernyataan ────────────────────────────────────────────────────────────

    def _s_Penugasan(self, s: Simpul, level: int) -> list[str]:
        """``target = nilai``"""
        self._ikat_target(s["target"])
        return [f"{self._ind(level)}{self._ekspresi(s['target'])} = {self._ekspresi(s['nilai'])}"]

    def _s_PenugasanGabungan(self, s: Simpul, level: int) -> list[str]:
        """``target += nilai``"""
        self._ikat_target(s["target"])
        return [
            f"{self._ind(level)}{self._ekspresi(s['target'])} "
            f"{s['op']} {self._ekspresi(s['nilai'])}"
        ]

    def _s_PenugasanBertanda(self, s: Simpul, level: int) -> list[str]:
        """``nama: anotasi = nilai``"""
        nama = self._nama(s["nama"])
        self.resolver.ikat(s["nama"])
        teks = f"{self._ind(level)}{nama}: {self._ekspresi(s['anotasi'])}"
        if s.get("nilai") is not None:
            teks += f" = {self._ekspresi(s['nilai'])}"
        return [teks]

    def _s_PenugasanEkspresi(self, s: Simpul, level: int) -> list[str]:
        """``nama := nilai`` sebagai pernyataan."""
        self._ikat_target(s["target"])
        return [f"{self._ind(level)}{self._ekspresi(s['target'])} := {self._ekspresi(s['nilai'])}"]

    def _e_PenugasanEkspresi(self, s: Simpul) -> str:
        """``(nama := nilai)`` sebagai ekspresi — harus dikurung."""
        self._ikat_target(s["target"])
        return f"({self._ekspresi(s['target'])} := {self._ekspresi(s['nilai'])})"

    def _s_EkspresiPernyataan(self, s: Simpul, level: int) -> list[str]:
        """Ekspresi berdiri sendiri, misal ``cetak(x)``."""
        return [f"{self._ind(level)}{self._ekspresi(s['ekspresi'])}"]

    def _s_Hentikan(self, _s: Simpul, level: int) -> list[str]:
        return [f"{self._ind(level)}break"]

    def _s_Lanjut(self, _s: Simpul, level: int) -> list[str]:
        return [f"{self._ind(level)}continue"]

    def _s_Lewati(self, _s: Simpul, level: int) -> list[str]:
        return [f"{self._ind(level)}pass"]

    def _s_Kembali(self, s: Simpul, level: int) -> list[str]:
        """``return [nilai]``"""
        if s.get("nilai") is None:
            return [f"{self._ind(level)}return"]
        return [f"{self._ind(level)}return {self._ekspresi(s['nilai'])}"]

    def _s_Hapus(self, s: Simpul, level: int) -> list[str]:
        return [f"{self._ind(level)}del {self._ekspresi(s['target'])}"]

    def _s_Global(self, s: Simpul, level: int) -> list[str]:
        return [f"{self._ind(level)}global {self._daftar_nama(s['nama'])}"]

    def _s_Nonlokal(self, s: Simpul, level: int) -> list[str]:
        return [f"{self._ind(level)}nonlocal {self._daftar_nama(s['nama'])}"]

    def _s_Assert(self, s: Simpul, level: int) -> list[str]:
        """``assert kondisi [pesan]``"""
        teks = f"{self._ind(level)}assert {self._ekspresi(s['kondisi'])}"
        if s.get("pesan") is not None:
            teks += f", {self._ekspresi(s['pesan'])}"
        return [teks]

    def _s_Naikkan(self, s: Simpul, level: int) -> list[str]:
        """``raise [ekspresi] [from penyebab]``"""
        if s.get("ekspresi") is None:
            return [f"{self._ind(level)}raise"]
        teks = f"{self._ind(level)}raise {self._ekspresi(s['ekspresi'])}"
        if s.get("dari") is not None:
            teks += f" from {self._ekspresi(s['dari'])}"
        return [teks]

    def _s_Impor(self, s: Simpul, level: int) -> list[str]:
        """``import modul [as alias]``"""
        nama = self._nama_titik(s["nama"])
        if s.get("alias"):
            alias = self._nama(s["alias"])
            self.resolver.ikat(s["alias"])
            return [f"{self._ind(level)}import {nama} as {alias}"]
        # import a.b mengikat 'a'
        akar = nama.split(".")[0]
        self.resolver.ikat(akar)
        return [f"{self._ind(level)}import {nama}"]

    def _s_DariImpor(self, s: Simpul, level: int) -> list[str]:
        """``from modul import a [as x], ...``"""
        modul = self._nama_titik(s["modul"])
        bagian: list[str] = []
        for item in s["nama"]:
            if item["nama"] == "*":
                bagian.append("*")
                continue
            nama = self._nama_titik(item["nama"])
            if item.get("alias"):
                alias = self._nama(item["alias"])
                self.resolver.ikat(item["alias"])
                bagian.append(f"{nama} as {alias}")
            else:
                self.resolver.ikat(item["nama"].split(".")[0])
                bagian.append(nama)
        return [f"{self._ind(level)}from {modul} import {', '.join(bagian)}"]

    # ── Definisi ─────────────────────────────────────────────────────────────

    def _s_DefinisiFungsi(self, s: Simpul, level: int) -> list[str]:
        """``def nama(params) -> anotasi:`` (dengan dekorator bila ada)."""
        # Nama fungsi diikat di scope LUAR (fungsi yang di-bind, bukan isinya)
        self.resolver.ikat(s["nama"])
        nama_luar = self._nama(s["nama"])

        # Parameter terikat di scope DALAM fungsi
        self.resolver.masuk()
        for p in s["parameter"]:
            if p.get("nama"):
                self.resolver.ikat(p["nama"])

        parameter = self._format_parameter(s["parameter"])
        awalan = "async " if s.get("asinkron") else ""
        kepala = f"{self._ind(level)}{awalan}def {nama_luar}({parameter})"
        if s.get("kembali_anotasi") is not None:
            kepala += f" -> {self._ekspresi(s['kembali_anotasi'])}"
        kepala += ":"

        tubuh = self._pernyataan_daftar(s["tubuh"], level + 1)
        self.resolver.keluar()

        baris = list(tubuh) or [f"{self._ind(level + 1)}pass"]
        return self._dengan_dekorator(s, kepala, baris, level)

    def _s_DefinisiKelas(self, s: Simpul, level: int) -> list[str]:
        """``class Nama(Induk, ...):``"""
        self.resolver.ikat(s["nama"])
        nama_luar = self._nama(s["nama"])

        induk = ""
        if s.get("induk"):
            induk = f"({', '.join(self._ekspresi(b) for b in s['induk'])})"
        kepala = f"{self._ind(level)}class {nama_luar}{induk}:"

        # Isi kelas punya scope sendiri di Python
        self.resolver.masuk()
        isi = self._pernyataan_daftar(s["tubuh"], level + 1)
        self.resolver.keluar()

        baris = list(isi) or [f"{self._ind(level + 1)}pass"]
        return self._dengan_dekorator(s, kepala, baris, level)

    def _dengan_dekorator(self, s: Simpul, kepala: str, baris: list[str], level: int) -> list[str]:
        """Tempatkan baris dekorator tepat di atas kepala definisi."""
        dekorator = s.get("dekorator") or []
        if not dekorator:
            return [kepala] + baris
        atas = [f"{self._ind(level)}@{self._ekspresi(d['ekspresi'])}" for d in dekorator]
        return atas + [kepala] + baris

    def _format_parameter(self, parameter: list[Simpul]) -> str:
        """
        Format daftar parameter fungsi sesuai urutan aslinya.

        Pemisah ``/`` dan ``*`` sudah disimpan parser sebagai entri
        :data:`PEMISAH`, jadi perakitan di sini cukup mengikuti urutan
        kemunculannya:

        * ``def f(a, /, b)`` → ``a`` posisional-only, ``b`` posisional biasa
        * ``def f(a, *, b)`` → ``a`` positional, ``b`` keyword-only
        * ``def f(a, *, b=1)`` → ``*`` tunggal sebelum ``b``
        """
        bagian: list[str] = []
        bintang_kwonly_tercetak = False

        for p in parameter:
            if p.get("jenis") == "PEMISAH":
                tanda = p.get("tanda")
                if tanda == "/":
                    bagian.append("/")
                elif tanda == "*" and not bintang_kwonly_tercetak:
                    bagian.append("*")
                    bintang_kwonly_tercetak = True
                continue

            if p.get("posisi") == "kwonly" and not bintang_kwonly_tercetak:
                bagian.append("*")
                bintang_kwonly_tercetak = True

            teks = p.get("bintang", "") or ""
            self.resolver.ikat(p["nama"])
            teks += self._nama(p["nama"])
            if p.get("anotasi") is not None:
                teks += f": {self._ekspresi(p['anotasi'])}"
            if p.get("nilai_bawaan") is not None:
                teks += f" = {self._ekspresi(p['nilai_bawaan'])}"
            bagian.append(teks)

        return ", ".join(bagian)

    # ── Kontrol alur ─────────────────────────────────────────────────────────

    def _s_Jika(self, s: Simpul, level: int) -> list[str]:
        """``if / elif / else``"""
        baris = [f"{self._ind(level)}if {self._ekspresi(s['kondisi'])}:"]
        baris += self._blok(s["then"], level)

        for cabang in s.get("elif", []):
            baris.append(f"{self._ind(level)}elif {self._ekspresi(cabang['kondisi'])}:")
            isi = self._pernyataan_daftar(cabang["tubuh"], level + 1)
            baris += isi or [f"{self._ind(level + 1)}pass"]

        if s.get("else"):
            baris.append(f"{self._ind(level)}else:")
            baris += self._blok(s["else"], level)
        return baris

    def _s_Selama(self, s: Simpul, level: int) -> list[str]:
        """``while``"""
        awalan = "async " if s.get("asinkron") else ""
        return [f"{self._ind(level)}{awalan}while {self._ekspresi(s['kondisi'])}:"] + \
            self._blok(s["tubuh"], level)

    def _s_Untuk(self, s: Simpul, level: int) -> list[str]:
        """``for`` (+ ``else`` bila ada)"""
        self._ikat_target(s["target"])
        awalan = "async " if s.get("asinkron") else ""
        kepala = (f"{self._ind(level)}{awalan}for "
                  f"{self._ekspresi(s['target'])} in {self._ekspresi(s['iterable'])}:")
        baris = [kepala] + self._blok(s["tubuh"], level)
        if s.get("else"):
            baris.append(f"{self._ind(level)}else:")
            baris += self._pernyataan_daftar(s["else"], level + 1)
        return baris

    def _s_CobaDanKecuali(self, s: Simpul, level: int) -> list[str]:
        """``try / except / else / finally``"""
        baris = [f"{self._ind(level)}try:"] + self._blok(s["tubuh"], level)

        for h in s.get("handler", []):
            klausa = "except"
            if h.get("tipe") is not None:
                klausa += f" {self._ekspresi(h['tipe'])}"
                if h.get("nama"):
                    klausa += f" as {self._nama(h['nama'])}"
                    self.resolver.ikat(h["nama"])
            baris.append(f"{self._ind(level)}{klausa}:")
            isi = self._pernyataan_daftar(h["tubuh"], level + 1)
            baris += isi or [f"{self._ind(level + 1)}pass"]

        if s.get("else"):
            baris.append(f"{self._ind(level)}else:")
            baris += self._pernyataan_daftar(s["else"], level + 1)

        if s.get("finally"):
            baris.append(f"{self._ind(level)}finally:")
            isi = self._pernyataan_daftar(s["finally"], level + 1)
            baris += isi or [f"{self._ind(level + 1)}pass"]

        return baris

    def _s_Bersama(self, s: Simpul, level: int) -> list[str]:
        """``with`` — mendukung beberapa item dipisah koma."""
        bagian: list[str] = []
        for item in s.get("item", []):
            teks = self._ekspresi(item["konteks"])
            if item.get("nama"):
                teks += f" as {self._nama(item['nama'])}"
                self.resolver.ikat(item["nama"])
            bagian.append(teks)

        awalan = "async " if s.get("asinkron") else ""
        kepala = f"{self._ind(level)}{awalan}with {', '.join(bagian)}:"
        return [kepala] + self._blok(s["tubuh"], level)

    def _s_CocokPola(self, s: Simpul, level: int) -> list[str]:
        """``match`` — diteruskan apa adanya ke Python."""
        return [f"{self._ind(level)}match {self._ekspresi(s['subjek'])}:"] + \
            self._blok(s["tubuh"], level)

    # ── Ekspresi: literal ────────────────────────────────────────────────────

    def _e_Nama(self, s: Simpul) -> str:
        """Nama bebas, dengan resolusi alias builtin."""
        return self._nama(s["nama"])

    def _e_Angka(self, s: Simpul) -> str:
        """
        Tulis ulang angka memakai bentuk sumber aslinya.

        Sumber dipertahankan agar ``0x_1f``, ``1_000``, ``1_0.5e-3``, dan
        ``3j`` tetap sama persis bentuknya di kode hasil.
        """
        sumber = s.get("source")
        if sumber:
            return str(sumber)
        nilai = s["nilai"]
        if isinstance(nilai, complex):
            return repr(nilai)
        if isinstance(nilai, float) and nilai.is_integer() and "." not in str(s.get("source", "")):
            return str(int(nilai))
        return repr(nilai)

    def _e_Teks(self, s: Simpul) -> str:
        """String literal — isi dan prefiks dipertahankan apa adanya."""
        return str(s["nilai"])

    def _e_Boolean(self, s: Simpul) -> str:
        return "True" if s["nilai"] else "False"

    def _e_Kosong(self, _s: Simpul) -> str:
        return "None"

    def _e_Elipsis(self, _s: Simpul) -> str:
        return "..."

    # ── Ekspresi: operator ───────────────────────────────────────────────────

    def _e_BinOp(self, s: Simpul) -> str:
        """Operasi biner, dengan kurung sesuai presedensi."""
        op = s["op"]
        kiri = self._ekspresi_anak(s["kiri"], op, sisi_kanan=False)
        kanan = self._ekspresi_anak(s["kanan"], op, sisi_kanan=True)
        return f"{kiri} {op} {kanan}"

    def _e_PerbandinganRantai(self, s: Simpul) -> str:
        """
        Perbandingan berantai: ``a < b <= c``.

        Ditulis ulang sebagai ``a < b and b <= c``. Bentuk ini menjaga
        semantik短路 milik Python tanpa perlu menyalin operand tengah
        ke variabel sementara.
        """
        awal = self._ekspresi(s["awal"])
        ruas: list[str] = []
        operand_sebelumnya = awal
        for seg in s["segmen"]:
            kanan = self._ekspresi(seg["kanan"])
            ruas.append(f"{operand_sebelumnya} {seg['op']} {kanan}")
            operand_sebelumnya = kanan
        return " and ".join(ruas)

    def _ekspresi_anak(self, simpul: Simpul, op_induk: str, sisi_kanan: bool) -> str:
        """Terjemahkan ekspresi anak, tambahkan kurung bila perlu."""
        teks = self._ekspresi(simpul)
        if simpul.get("dalam_kurung"):
            # Kurung ditulis eksplisit di sumber — pertahankan agar makna
            # tanda, urutan evaluasi, dan operator tetap sama.
            return f"({teks})"
        if not self._perlu_kurung(simpul, op_induk, sisi_kanan):
            return teks
        return f"({teks})"

    def _perlu_kurung(self, simpul: Simpul, op_induk: str, sisi_kanan: bool) -> bool:
        """
        Tentukan apakah ekspresi anak perlu dikurung.

        Perbandingan memakai tabel presedensi resmi Python. Dua kasus khusus:

        * ``**`` mengikat ke kanan → sisi kiri berpresedensi sama perlu kurung.
        * Rantai perbandingan di bawah ``and``/``or`` selalu perlu kurung.
        """
        jenis = simpul.get("jenis")

        if jenis == "BinOp":
            p_anak = PRESEDENSI.get(simpul["op"], PRESEDENSI["atom"])
        elif jenis in ("UnOp", "Tunggu"):
            p_anak = PRESEDENSI["unary"]
        elif jenis == "PerbandinganRantai":
            p_anak = PRESEDENSI["=="]
        elif jenis in ("EkspresiKondisi",):
            p_anak = PRESEDENSI["if-else"]
        else:
            p_anak = PRESEDENSI["atom"]

        p_induk = PRESEDENSI.get(op_induk, PRESEDENSI["atom"])

        if p_anak < p_induk:
            return True
        if p_anak > p_induk:
            return False

        # Presedensi sama: putuskan lewat asosiasiativity
        if op_induk in ASOSIASI_KANAN:
            return not sisi_kanan
        return sisi_kanan

    def _e_UnOp(self, s: Simpul) -> str:
        """``-x``, ``+x``, ``~x``, ``not x``"""
        op = s["op"]
        operand = self._ekspresi(s["operand"])
        if op == "not":
            return f"not {operand}"
        return f"{op}{operand}"

    def _e_Tunggu(self, s: Simpul) -> str:
        """``await x``"""
        return f"await {self._ekspresi(s['operand'])}"

    def _e_Hasil(self, s: Simpul) -> str:
        """``yield nilai`` / ``yield from iterable``"""
        kata = "yield from" if s.get("dari") else "yield"
        if s.get("nilai") is None:
            return kata
        return f"{kata} {self._ekspresi(s['nilai'])}"

    def _e_EkspresiKondisi(self, s: Simpul) -> str:
        """``nilai if kondisi else alternatif``"""
        nilai = self._ekspresi_kondisi_nilai(s["nilai"])
        kondisi = self._ekspresi(s["kondisi"])
        alternatif = self._ekspresi(s["alternatif"])
        return f"{nilai} if {kondisi} else {alternatif}"

    def _ekspresi_kondisi_nilai(self, s: Simpul) -> str:
        """Terjemahkan nilai pada ekspresi kondisi (perlu kurung bila BinOp)."""
        if s.get("jenis") == "BinOp":
            return f"({self._ekspresi(s)})"
        return self._ekspresi(s)

    # ── Ekspresi: akses & pemanggilan ─────────────────────────────────────────

    def _e_Panggilan(self, s: Simpul) -> str:
        """``fungsi(argumen, ...)``"""
        fungsi = self._ekspresi(s["fungsi"])
        argumen = ", ".join(self._format_argumen(a) for a in s["argumen"])
        return f"{fungsi}({argumen})"

    def _e_Atribut(self, s: Simpul) -> str:
        """``objek.atribut`` — nama atribut tidak pernah dipetakan."""
        return f"{self._ekspresi(s['objek'])}.{s['atribut']}"

    def _e_Subskrip(self, s: Simpul) -> str:
        """``objek[indeks]``"""
        return f"{self._ekspresi(s['objek'])}[{self._ekspresi(s['indeks'])}]"

    def _e_Slice(self, s: Simpul) -> str:
        """
        ``objek[awal:akhir:langkah]`` — semua bagian boleh kosong.

        Keberadaan bagian ditentukan dari ``None``, bukan nilai kebenaran, agar
        ``a[0:0]`` tetap menghasilkan ``0:0`` dan bukan ``:``.
        """
        awal = self._bagian_slice(s.get("awal"))
        akhir = self._bagian_slice(s.get("akhir"))
        teks = f"{awal}:{akhir}"
        if s.get("langkah") is not None:
            teks += f":{self._bagian_slice(s['langkah'])}"
        return f"{self._ekspresi(s['objek'])}[{teks}]"

    def _bagian_slice(self, simpul: Simpul | None) -> str:
        """
        Terjemahkan satu bagian slice.

        ``None`` berarti bagian tidak ada; simpul ``Kosong`` yang dihasilkan dari
        ``a[:]`` juga berarti tidak ada — bukan literal ``None``.
        """
        if simpul is None:
            return ""
        if simpul.get("jenis") == "Kosong" and "nilai" not in simpul:
            return ""
        return self._ekspresi(simpul)

    def _e_Tuple(self, s: Simpul) -> str:
        """Tuple; satu elemen tetap diberi koma agar tetap tuple."""
        elemen = s["elemen"]
        if not elemen:
            return "()"
        isi = ", ".join(self._ekspresi(e) for e in elemen)
        if len(elemen) == 1:
            return f"({isi},)"
        return f"({isi})"

    def _e_Daftar(self, s: Simpul) -> str:
        return "[" + ", ".join(self._ekspresi(e) for e in s["elemen"]) + "]"

    def _e_Kamus(self, s: Simpul) -> str:
        isi = ", ".join(f"{self._ekspresi(k)}: {self._ekspresi(v)}" for k, v in s["pasang"])
        return "{" + isi + "}"

    def _e_Himpunan(self, s: Simpul) -> str:
        return "{" + ", ".join(self._ekspresi(e) for e in s["elemen"]) + "}"

    def _e_ArgKunci(self, s: Simpul) -> str:
        """``nama=nilai`` pada pemanggilan fungsi."""
        return f"{s['nama']}={self._ekspresi(s['nilai'])}"

    def _e_ArgsUnpack(self, s: Simpul) -> str:
        return f"*{self._ekspresi(s['nilai'])}"

    def _e_KwargsUnpack(self, s: Simpul) -> str:
        return f"**{self._ekspresi(s['nilai'])}"

    def _e_Bintang(self, s: Simpul) -> str:
        """``*nama`` pada target unpacking."""
        return f"*{self._ekspresi(s['nilai'])}"

    def _e_Lambda(self, s: Simpul) -> str:
        """``lambda params: ekspresi``"""
        self.resolver.masuk()
        for p in s.get("parameter", []):
            self.resolver.ikat(p["nama"])
        teks = "lambda " + self._format_parameter_lambda(s.get("parameter", [])) + ": " \
            + self._ekspresi(s["tubuh"])
        self.resolver.keluar()
        return teks

    def _format_parameter_lambda(self, parameter: list[Simpul]) -> str:
        """Format parameter lambda (hanya nama, ``*``, ``**``, dan anotasi)."""
        bagian: list[str] = []
        for p in parameter:
            if p.get("jenis") == "PEMISAH":
                continue
            teks = p.get("bintang", "") or ""
            self.resolver.ikat(p["nama"])
            teks += self._nama(p["nama"])
            if p.get("anotasi") is not None:
                teks += f": {self._ekspresi(p['anotasi'])}"
            bagian.append(teks)
        return ", ".join(bagian)

    # ── Comprehension ─────────────────────────────────────────────────────────

    def _e_ListComprehension(self, s: Simpul) -> str:
        return f"[{self._format_comprehension(s['ekspresi'], s['comprehension'])}]"

    def _e_GeneratorEkspresi(self, s: Simpul) -> str:
        return f"({self._format_comprehension(s['ekspresi'], s['comprehension'])})"

    def _e_DictComprehension(self, s: Simpul) -> str:
        kunci = self._ekspresi(s["kunci"])
        nilai = self._ekspresi(s["nilai"])
        ekor = self._format_comprehension_tail(s["comprehension"])
        return "{" + f"{kunci}: {nilai} {ekor}" + "}"

    def _format_comprehension(self, ekspresi: Simpul, komprehension: list[Simpul]) -> str:
        """Format comprehension; loop var terikat di scope baru."""
        self.resolver.masuk()
        try:
            return self._ekspresi(ekspresi) + " " + self._format_comprehension_tail(komprehension)
        finally:
            self.resolver.keluar()

    def _format_comprehension_tail(self, komprehension: list[Simpul]) -> str:
        """Format ekor comprehension saja."""
        bagian: list[str] = []
        for k in komprehension:
            self._ikat_target(k["target"])
            teks = f"for {self._ekspresi(k['target'])} in {self._ekspresi(k['iterable'])}"
            if k.get("kondisi") is not None:
                teks += f" if {self._ekspresi(k['kondisi'])}"
            bagian.append(teks)
        return " ".join(bagian)

    # ── Pengikatan nama ──────────────────────────────────────────────────────

    def _ikat_target(self, simpul: Simpul) -> None:
        """
        Catat semua nama yang di-*bind* oleh sebuah target penugasan.

        Menangani nama, tuple, dan bentuk berbintang ``*nama``.
        """
        jenis = simpul.get("jenis")
        if jenis == "Nama":
            self.resolver.ikat(simpul["nama"])
        elif jenis == "Tuple":
            for e in simpul["elemen"]:
                self._ikat_target(e)
        elif jenis == "Bintang":
            self._ikat_target(simpul["nilai"])
        elif jenis == "Atribut":
            # t.x = ... tidak mengikat nama baru
            return
        elif jenis == "Subskrip":
            # a[i] = ... tidak mengikat nama baru
            return

    def _nama_titik(self, nama: str) -> str:
        """Terjemahkan nama bertitik; hanya bagian terakhir yang boleh alias."""
        bagian = nama.split(".")
        return ".".join(self._nama(b) if i == 0 else b for i, b in enumerate(bagian))

    def _format_argumen(self, arg: Simpul) -> str:
        """Format satu argumen pemanggilan."""
        jenis = arg.get("jenis")
        if jenis == "ArgKunci":
            return self._e_ArgKunci(arg)
        if jenis in ("ArgsUnpack", "KwargsUnpack"):
            return self._ekspresi(arg)
        if jenis == "PenugasanEkspresi":
            self._ikat_target(arg["target"])
            return f"({self._ekspresi(arg['target'])} := {self._ekspresi(arg['nilai'])})"
        return self._ekspresi(arg)


# ── Pintasan tingkat modul ──────────────────────────────────────────────────

def terjemahkan(ast: Simpul) -> str:
    """Pintasan: terima AST, kembalikan kode Python."""
    return Transpiler().terjemahkan(ast)


#: Alias kompatibilitas ke API Inggris.
transpile = terjemahkan

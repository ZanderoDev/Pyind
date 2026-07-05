"""
transpiler.py — AST → Kode Python valid.
Bagian dari proyek Pyind (Python Indonesia).

Modul ini berjalan setelah parser.py menghasilkan AST.
Ia menelusuri pohon simpul secara rekursif dan menghasilkan
kode Python yang valid dengan indentasi yang benar.

Tidak ada exec() atau eval() di sini — ini murni pembangkitan teks.
"""

from __future__ import annotations
from typing import Any

from errors import err_simpul_tak_dikenal

# Tipe alias
Simpul = dict[str, Any]

INDENT = "    "   # 4 spasi per level, sesuai konvensi Python (PEP 8)


class Transpiler:
    """
    Menelusuri AST dari Parser dan menghasilkan string kode Python.

    Penggunaan:
        ast  = Parser(tokens).parse()
        kode = Transpiler().transpile(ast)
    """

    # ── API publik ────────────────────────────────────────────────────────────

    def transpile(self, ast: Simpul) -> str:
        """
        Titik masuk utama. Terima simpul Modul dan hasilkan
        seluruh kode Python sebagai satu string.
        """
        baris = self._stmt_list(ast["tubuh"], level=0)
        kode = "\n".join(baris)
        # Pastikan file diakhiri baris baru tunggal
        return kode.rstrip("\n") + "\n"

    # ── Helpers indentasi ─────────────────────────────────────────────────────

    @staticmethod
    def _ind(level: int) -> str:
        """Kembalikan string indentasi untuk level tertentu."""
        return INDENT * level

    # ── Dispatcher pernyataan ─────────────────────────────────────────────────

    def _stmt_list(self, stmts: list[Simpul], level: int) -> list[str]:
        """Proses daftar pernyataan dan kembalikan daftar baris teks."""
        baris: list[str] = []
        for stmt in stmts:
            baris.extend(self._stmt(stmt, level))
        return baris

    def _stmt(self, simpul: Simpul, level: int) -> list[str]:
        """
        Dispatch ke handler pernyataan berdasarkan jenis simpul.
        Kembalikan daftar baris (sudah terindentasi).
        """
        jenis = simpul.get("jenis", "")
        handler = getattr(self, f"_s_{jenis}", None)
        if handler is None:
            raise err_simpul_tak_dikenal(jenis)
        return handler(simpul, level)

    # ── Handler pernyataan ────────────────────────────────────────────────────

    def _s_Penugasan(self, s: Simpul, lv: int) -> list[str]:
        """target = nilai"""
        target = self._ekspresi(s["target"])
        nilai  = self._ekspresi(s["nilai"])
        return [f"{self._ind(lv)}{target} = {nilai}"]

    def _s_PenugasanGabungan(self, s: Simpul, lv: int) -> list[str]:
        """target += nilai  (dan variannya)"""
        target = self._ekspresi(s["target"])
        nilai  = self._ekspresi(s["nilai"])
        return [f"{self._ind(lv)}{target} {s['op']} {nilai}"]

    def _s_EkspresiPernyataan(self, s: Simpul, lv: int) -> list[str]:
        """Ekspresi yang berdiri sendiri, misal: cetak(...)"""
        return [f"{self._ind(lv)}{self._ekspresi(s['ekspresi'])}"]

    def _s_Hentikan(self, _s: Simpul, lv: int) -> list[str]:
        return [f"{self._ind(lv)}break"]

    def _s_Lanjut(self, _s: Simpul, lv: int) -> list[str]:
        return [f"{self._ind(lv)}continue"]

    def _s_Lewati(self, _s: Simpul, lv: int) -> list[str]:
        return [f"{self._ind(lv)}pass"]

    def _s_Kembali(self, s: Simpul, lv: int) -> list[str]:
        """return [nilai]"""
        if s["nilai"] is None:
            return [f"{self._ind(lv)}return"]
        return [f"{self._ind(lv)}return {self._ekspresi(s['nilai'])}"]

    def _s_Hapus(self, s: Simpul, lv: int) -> list[str]:
        return [f"{self._ind(lv)}del {self._ekspresi(s['target'])}"]

    def _s_Global(self, s: Simpul, lv: int) -> list[str]:
        return [f"{self._ind(lv)}global {', '.join(s['nama'])}"]

    def _s_Nonlokal(self, s: Simpul, lv: int) -> list[str]:
        return [f"{self._ind(lv)}nonlocal {', '.join(s['nama'])}"]

    def _s_Assert(self, s: Simpul, lv: int) -> list[str]:
        cond = self._ekspresi(s["kondisi"])
        if s["pesan"]:
            return [f"{self._ind(lv)}assert {cond}, {self._ekspresi(s['pesan'])}"]
        return [f"{self._ind(lv)}assert {cond}"]

    def _s_Naikkan(self, s: Simpul, lv: int) -> list[str]:
        if s["ekspresi"] is None:
            return [f"{self._ind(lv)}raise"]
        return [f"{self._ind(lv)}raise {self._ekspresi(s['ekspresi'])}"]

    def _s_Impor(self, s: Simpul, lv: int) -> list[str]:
        """import modul [as alias]"""
        baris = f"{self._ind(lv)}import {s['nama']}"
        if s["alias"]:
            baris += f" as {s['alias']}"
        return [baris]

    def _s_DariImpor(self, s: Simpul, lv: int) -> list[str]:
        """from modul import nama [as alias], ..."""
        bagian = []
        for item in s["nama"]:
            if item["alias"]:
                bagian.append(f"{item['nama']} as {item['alias']}")
            else:
                bagian.append(item["nama"])
        return [f"{self._ind(lv)}from {s['modul']} import {', '.join(bagian)}"]

    def _s_DefinisiFungsi(self, s: Simpul, lv: int) -> list[str]:
        """def nama(params) -> anotasi: tubuh"""
        params = self._format_params(s["parameter"])
        sig = f"{self._ind(lv)}def {s['nama']}({params})"
        if s.get("kembali_anotasi"):
            sig += f" -> {self._ekspresi(s['kembali_anotasi'])}"
        sig += ":"
        tubuh = self._stmt_list(s["tubuh"], lv + 1)
        if not tubuh:
            tubuh = [f"{self._ind(lv + 1)}pass"]
        return [sig] + tubuh

    def _s_DefinisiKelas(self, s: Simpul, lv: int) -> list[str]:
        """class Nama(Base, ...): tubuh"""
        induk = ""
        if s["induk"]:
            induk = f"({', '.join(self._ekspresi(b) for b in s['induk'])})"
        header = f"{self._ind(lv)}class {s['nama']}{induk}:"
        tubuh = self._stmt_list(s["tubuh"], lv + 1)
        if not tubuh:
            tubuh = [f"{self._ind(lv + 1)}pass"]
        return [header] + tubuh

    def _s_Jika(self, s: Simpul, lv: int) -> list[str]:
        """if kondisi: ... elif ...: ... else: ..."""
        baris = [f"{self._ind(lv)}if {self._ekspresi(s['kondisi'])}:"]
        baris += self._stmt_list(s["then"], lv + 1) or [f"{self._ind(lv+1)}pass"]

        for cab in s.get("elif", []):
            baris.append(f"{self._ind(lv)}elif {self._ekspresi(cab['kondisi'])}:")
            baris += self._stmt_list(cab["tubuh"], lv + 1) or [f"{self._ind(lv+1)}pass"]

        if s.get("else"):
            baris.append(f"{self._ind(lv)}else:")
            baris += self._stmt_list(s["else"], lv + 1) or [f"{self._ind(lv+1)}pass"]

        return baris

    def _s_Selama(self, s: Simpul, lv: int) -> list[str]:
        """while kondisi: tubuh"""
        baris = [f"{self._ind(lv)}while {self._ekspresi(s['kondisi'])}:"]
        baris += self._stmt_list(s["tubuh"], lv + 1) or [f"{self._ind(lv+1)}pass"]
        return baris

    def _s_Untuk(self, s: Simpul, lv: int) -> list[str]:
        """for target in iterable: tubuh"""
        target   = self._ekspresi(s["target"])
        iterable = self._ekspresi(s["iterable"])
        baris = [f"{self._ind(lv)}for {target} in {iterable}:"]
        baris += self._stmt_list(s["tubuh"], lv + 1) or [f"{self._ind(lv+1)}pass"]
        return baris

    def _s_CobaDanKecuali(self, s: Simpul, lv: int) -> list[str]:
        """try: ... except Tipe as nama: ... finally: ..."""
        baris = [f"{self._ind(lv)}try:"]
        baris += self._stmt_list(s["tubuh"], lv + 1) or [f"{self._ind(lv+1)}pass"]

        for h in s.get("handler", []):
            if h["tipe"]:
                klausa = f"except {self._ekspresi(h['tipe'])}"
                if h["nama"]:
                    klausa += f" as {h['nama']}"
            else:
                klausa = "except"
            baris.append(f"{self._ind(lv)}{klausa}:")
            baris += self._stmt_list(h["tubuh"], lv + 1) or [f"{self._ind(lv+1)}pass"]

        if s.get("else"):
            baris.append(f"{self._ind(lv)}else:")
            baris += self._stmt_list(s["else"], lv + 1)

        if s.get("finally"):
            baris.append(f"{self._ind(lv)}finally:")
            baris += self._stmt_list(s["finally"], lv + 1) or [f"{self._ind(lv+1)}pass"]

        return baris

    def _s_Bersama(self, s: Simpul, lv: int) -> list[str]:
        """with konteks [as nama]: tubuh"""
        baris_with = f"{self._ind(lv)}with {self._ekspresi(s['konteks'])}"
        if s.get("nama"):
            baris_with += f" as {s['nama']}"
        baris_with += ":"
        tubuh = self._stmt_list(s["tubuh"], lv + 1) or [f"{self._ind(lv+1)}pass"]
        return [baris_with] + tubuh

    # ── Dispatcher ekspresi ───────────────────────────────────────────────────

    def _ekspresi(self, simpul: Simpul) -> str:
        """
        Dispatch ke handler ekspresi berdasarkan jenis simpul.
        Kembalikan representasi string ekspresi tersebut.
        """
        jenis = simpul.get("jenis", "")
        handler = getattr(self, f"_e_{jenis}", None)
        if handler is None:
            raise err_simpul_tak_dikenal(jenis)
        return handler(simpul)

    # ── Handler ekspresi ──────────────────────────────────────────────────────

    def _e_Nama(self, s: Simpul) -> str:
        return s["nama"]

    def _e_Angka(self, s: Simpul) -> str:
        nilai = s["nilai"]
        # Hapus .0 yang tidak perlu hanya bila nilai adalah integer murni
        if isinstance(nilai, float) and nilai.is_integer() and "." not in str(nilai):
            return str(int(nilai))
        return repr(nilai)

    def _e_Teks(self, s: Simpul) -> str:
        # Nilai sudah mengandung tanda kutip dari lexer
        return str(s["nilai"])

    def _e_Boolean(self, s: Simpul) -> str:
        return "True" if s["nilai"] else "False"

    def _e_Kosong(self, _s: Simpul) -> str:
        return "None"

    def _e_BinOp(self, s: Simpul) -> str:
        """Operasi biner: kiri op kanan — beri kurung bila perlu."""
        kiri  = self._ekspresi_dengan_kurung(s["kiri"],  s["op"])
        kanan = self._ekspresi_dengan_kurung(s["kanan"], s["op"], sisi_kanan=True)
        return f"{kiri} {s['op']} {kanan}"

    def _ekspresi_dengan_kurung(self, simpul: Simpul, op_induk: str,
                                 sisi_kanan: bool = False) -> str:
        """Tambah kurung pada ekspresi anak bila precedence-nya lebih rendah."""
        jenis = simpul.get("jenis")
        if jenis == "BinOp":
            if self._perlu_kurung(simpul["op"], op_induk, sisi_kanan):
                return f"({self._ekspresi(simpul)})"
        return self._ekspresi(simpul)

    @staticmethod
    def _perlu_kurung(op_anak: str, op_induk: str, sisi_kanan: bool) -> bool:
        """
        Tentukan apakah ekspresi anak perlu dikurung berdasarkan precedence.
        Tabel precedence (makin tinggi angka, makin tinggi prioritas).

        Aturan asosiativitas:
        - Operator left-associative (semua kecuali **):
            Sisi kanan perlu kurung jika preseden sama (a-(b-c) ≠ a-b-c).
        - Operator right-associative (**):
            Sisi KIRI perlu kurung jika preseden sama,
            karena 2**3**2 == 2**(3**2) secara alami — kurung kiri
            hanya diperlukan untuk (2**3)**2 agar tidak salah arti.
        """
        PREC: dict[str, int] = {
            "or": 1, "and": 2, "not": 3,
            "==": 4, "!=": 4, "<": 4, ">": 4, "<=": 4, ">=": 4,
            "in": 4, "not in": 4, "is": 4, "is not": 4,
            "|": 5, "^": 6, "&": 7, "<<": 8, ">>": 8,
            "+": 9, "-": 9,
            "*": 10, "/": 10, "//": 10, "%": 10, "@": 10,
            "**": 11,
        }
        p_induk = PREC.get(op_induk, 0)
        p_anak  = PREC.get(op_anak, 0)

        if p_anak < p_induk:
            return True   # preseden lebih rendah → selalu perlu kurung

        if p_anak == p_induk:
            if op_induk == "**":
                # ** adalah right-associative:
                # sisi kanan tidak perlu kurung (sudah alami),
                # sisi KIRI perlu kurung agar (a**b)**c tidak dibaca a**(b**c).
                return not sisi_kanan
            else:
                # Operator left-associative: sisi kanan perlu kurung.
                return sisi_kanan

        return False

    def _e_UnOp(self, s: Simpul) -> str:
        """Operasi unary: -x, not x, ~x"""
        op      = s["op"]
        operand = self._ekspresi(s["operand"])
        # Tambah spasi untuk operator kata (not)
        if op == "not":
            return f"not {operand}"
        # Kurung jika operand adalah BinOp agar ambigu tidak terjadi
        if s["operand"].get("jenis") == "BinOp":
            return f"{op}({operand})"
        return f"{op}{operand}"

    def _e_Panggilan(self, s: Simpul) -> str:
        """Pemanggilan fungsi: fungsi(argumen, ...)"""
        fungsi = self._ekspresi(s["fungsi"])
        argumen = ", ".join(self._format_argumen(a) for a in s["argumen"])
        return f"{fungsi}({argumen})"

    def _e_Atribut(self, s: Simpul) -> str:
        """Akses atribut: objek.atribut"""
        return f"{self._ekspresi(s['objek'])}.{s['atribut']}"

    def _e_Subskrip(self, s: Simpul) -> str:
        """Akses indeks: objek[indeks]"""
        return f"{self._ekspresi(s['objek'])}[{self._ekspresi(s['indeks'])}]"

    def _e_Slice(self, s: Simpul) -> str:
        """Slice: objek[awal:akhir:langkah]"""
        awal   = self._ekspresi(s["awal"])   if s.get("awal")   else ""
        akhir  = self._ekspresi(s["akhir"])  if s.get("akhir")  else ""
        langkah = self._ekspresi(s["langkah"]) if s.get("langkah") else ""
        slice_str = f"{awal}:{akhir}"
        if langkah:
            slice_str += f":{langkah}"
        return f"{self._ekspresi(s['objek'])}[{slice_str}]"

    def _e_Tuple(self, s: Simpul) -> str:
        elemen = s["elemen"]
        if not elemen:
            return "()"
        isi = ", ".join(self._ekspresi(e) for e in elemen)
        if len(elemen) == 1:
            return f"({isi},)"
        return f"({isi})"

    def _e_Daftar(self, s: Simpul) -> str:
        isi = ", ".join(self._ekspresi(e) for e in s["elemen"])
        return f"[{isi}]"

    def _e_Kamus(self, s: Simpul) -> str:
        pasang = ", ".join(
            f"{self._ekspresi(k)}: {self._ekspresi(v)}"
            for k, v in s["pasang"]
        )
        return "{" + pasang + "}"

    def _e_Himpunan(self, s: Simpul) -> str:
        isi = ", ".join(self._ekspresi(e) for e in s["elemen"])
        return "{" + isi + "}"

    def _e_ArgKunci(self, s: Simpul) -> str:
        return f"{s['nama']}={self._ekspresi(s['nilai'])}"

    def _e_ArgsUnpack(self, s: Simpul) -> str:
        return f"*{self._ekspresi(s['nilai'])}"

    def _e_KwargsUnpack(self, s: Simpul) -> str:
        return f"**{self._ekspresi(s['nilai'])}"

    def _e_Lambda(self, s: Simpul) -> str:
        params = ", ".join(s["parameter"])
        return f"lambda {params}: {self._ekspresi(s['tubuh'])}"

    def _e_EkspresiKondisi(self, s: Simpul) -> str:
        """nilai if kondisi else alternatif"""
        nilai     = self._ekspresi(s["nilai"])
        kondisi   = self._ekspresi(s["kondisi"])
        alternatif = self._ekspresi(s["alternatif"])
        return f"{nilai} if {kondisi} else {alternatif}"

    def _e_ListComprehension(self, s: Simpul) -> str:
        return f"[{self._format_comprehension(s['ekspresi'], s['comprehension'])}]"

    def _e_GeneratorEkspresi(self, s: Simpul) -> str:
        return f"({self._format_comprehension(s['ekspresi'], s['comprehension'])})"

    def _e_DictComprehension(self, s: Simpul) -> str:
        kunci = self._ekspresi(s["kunci"])
        nilai = self._ekspresi(s["nilai"])
        komp  = self._format_comprehension_tail(s["comprehension"])
        return "{" + f"{kunci}: {nilai} {komp}" + "}"

    # ── Utilitas format ───────────────────────────────────────────────────────

    def _format_argumen(self, arg: Simpul) -> str:
        """Format satu argumen (bisa keyword, *args, **kwargs, atau biasa)."""
        jenis = arg.get("jenis")
        if jenis == "ArgKunci":
            return self._e_ArgKunci(arg)
        if jenis == "ArgsUnpack":
            return self._e_ArgsUnpack(arg)
        if jenis == "KwargsUnpack":
            return self._e_KwargsUnpack(arg)
        return self._ekspresi(arg)

    def _format_params(self, params: list[Simpul]) -> str:
        """Format daftar parameter definisi fungsi."""
        bagian = []
        for p in params:
            s = ""
            bintang = p.get("bintang", "")
            s += bintang + p.get("nama", "")
            if p.get("anotasi"):
                s += f": {self._ekspresi(p['anotasi'])}"
            if p.get("default"):
                s += f" = {self._ekspresi(p['default'])}"
            bagian.append(s)
        return ", ".join(bagian)

    def _format_comprehension(self, ekspresi: Simpul, comprehension: list[Simpul]) -> str:
        """Format ekspresi comprehension: expr for x in xs [if cond]"""
        hasil = self._ekspresi(ekspresi)
        hasil += " " + self._format_comprehension_tail(comprehension)
        return hasil

    def _format_comprehension_tail(self, comprehension: list[Simpul]) -> str:
        """Format ekor comprehension saja."""
        bagian = []
        for komp in comprehension:
            target   = self._ekspresi(komp["target"])
            iterable = self._ekspresi(komp["iterable"])
            bagian_str = f"for {target} in {iterable}"
            if komp.get("kondisi"):
                bagian_str += f" if {self._ekspresi(komp['kondisi'])}"
            bagian.append(bagian_str)
        return " ".join(bagian)


# ── Fungsi utilitas tingkat modul ─────────────────────────────────────────────

def transpile(ast: dict) -> str:
    """Shortcut: terima AST dan kembalikan kode Python."""
    return Transpiler().transpile(ast)

"""
errors.py — Kelas error & diagnostik Pyind.
Bagian dari proyek Pyind (Python Indonesia).

Seluruh kegagalan di dalam pipeline Pyind (tokenisasi, parsing,
transpilasi) dilaporkan memakai kelas turunan :class:`PyindError` supaya
pesan kesalahan selalu berbahasa Indonesia dan disertai informasi lokasi
(baris/kolom) beserta cuplikan kode sumber bila tersedia.

Hierarki::

    PyindError
    ├── KesalahanLeksikal     tokenisasi gagal
    ├── KesalahanSintaks      sintaks tidak valid
    ├── KesalahanTranspilasi  simpul AST tidak bisa dibangkitkan
    └── KesalahanNama         nama belum didefinisikan
"""

from __future__ import annotations

TAB_CUPLIKAN = "  | "
LEBAR_GOAH = 70


class PyindError(Exception):
    """
    Kelas dasar semua error Pyind.

    Parameter_position ``pesan``/``baris``/``kolom`` sengaja dipertahankan
    agar konstruktor lama tetap kompatibel. Parameter tambahan bersifat
    opsional dan hanya dipakai untuk diagnostik yang lebih kaya.
    """

    # Nama singkat untuk dokumentasi / kode mesin (mis. "E1001").
    kode: str | None = None
    # Label Barney yang tampil di depan pesan.
    jenjang: str = "galat"

    def __init__(
        self,
        pesan: str,
        baris: int = 0,
        kolom: int = 0,
        berkas: str | None = None,
        *,
        kode: str | None = None,
        baris_akhir: int | None = None,
        kolom_akhir: int | None = None,
        sumber: str | None = None,
        catatan: str | None = None,
    ) -> None:
        self.pesan = pesan
        self.baris = baris
        self.kolom = kolom
        self.berkas = berkas
        self.baris_akhir = baris if baris_akhir is None else baris_akhir
        self.kolom_akhir = kolom if kolom_akhir is None else kolom_akhir
        self.sumber = sumber
        self.catatan = catatan
        if kode is not None:
            self.kode = kode
        super().__init__(self._susun_teks())

    # ── Penyusunan pesan ──────────────────────────────────────────────────────

    def _lokasi_teks(self) -> str:
        """Ruas lokasi seperti ``contoh.pyind:3:7`` atau ``baris 3, kolom 7``."""
        bagian: list[str] = []
        if self.berkas:
            bagian.append(str(self.berkas))
        if self.baris:
            bagian.append(f"baris {self.baris}")
            if self.kolom:
                bagian.append(f"kolom {self.kolom}")
        if not bagian:
            return ""
        return ":".join(bagian) if self.berkas else f"({', '.join(bagian)})"

    def _susun_teks(self) -> str:
        kepala = "[Pyind]"
        if self.kode:
            kepala += f" {self.kode}"
        lokasi = self._lokasi_teks()
        if lokasi:
            kepala += f" {lokasi}"
        baris = [f"{kepala}: {self.pesan}"]
        if self.catatan:
            baris.append(f"    catatan: {self.catatan}")
        potret = self._potret_sumber()
        if potret:
            baris.append(potret)
        return "\n".join(baris)

    def _potret_sumber(self) -> str:
        """Bangun cuplikan sumber dengan penunjuk caret di bawah kolom error."""
        if self.sumber is None or not self.baris:
            return ""
        baris_sumber = self.sumber.splitlines()
        if not baris_sumber:
            return ""
        nomor_awal = max(1, self.baris)
        if nomor_awal > len(baris_sumber):
            return ""
        lebar_no = len(str(nomor_awal + 1))
        hasil: list[str] = []
        for nomor in (nomor_awal, nomor_awal + 1):
            if nomor > len(baris_sumber):
                break
            teks_baris = baris_sumber[nomor - 1].replace("\t", " ").rstrip()
            if len(teks_baris) > LEBAR_GOAH:
                geser = max(0, self.kolom - 1 - LEBAR_GOAH // 2)
                teks_baris = "…" + teks_baris[geser: geser + LEBAR_GOAH] + "…"
                kolom_tunjuk = self.kolom - geser
            else:
                kolom_tunjuk = self.kolom
            hasil.append(f"{nomor:>{lebar_no}} | {teks_baris}")
            if nomor == nomor_awal:
                panjang = max(1, (self.kolom_akhir or self.kolom) - (self.kolom - 1))
                panjang = max(1, min(panjang, max(1, kolom_tunjuk)))
                hasil.append(
                    f"{'' :>{lebar_no}} | {' ' * max(0, kolom_tunjuk - 1)}{'^' * panjang}"
                )
        return "\n".join(hasil)

    def __str__(self) -> str:
        return self._susun_teks()

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.pesan!r}, baris={self.baris}, kolom={self.kolom})"


class KesalahanLeksikal(PyindError):
    """Tokenisasi gagal: karakter, literal angka, atau string tidak valid."""

    kode = "E1001"


class KesalahanSintaks(PyindError):
    """Parsing gagal: susunan token tidak membentuk kalimat valid."""

    kode = "E2001"


class KesalahanTranspilasi(PyindError):
    """Gagal membangkitkan kode Python dari sebuah simpul AST."""

    kode = "E3001"


class KesalahanNama(PyindError):
    """Nama yang dipakai tidak ditemukan atau tidak boleh dipakai di sini."""

    kode = "E4001"


# ── Pabrik pesan siap pakai ───────────────────────────────────────────────────

def err_karakter_tak_dikenal(karakter: str, baris: int, kolom: int, **kw) -> KesalahanLeksikal:
    return KesalahanLeksikal(f"Karakter tidak dikenal: {karakter!r}", baris, kolom, **kw)


def err_string_tidak_ditutup(baris: int, kolom: int, **kw) -> KesalahanLeksikal:
    return KesalahanLeksikal("String tidak ditutup dengan benar.", baris, kolom, **kw)


def err_angka_tidak_valid(teks: str, baris: int, kolom: int, alasan: str, **kw) -> KesalahanLeksikal:
    return KesalahanLeksikal(
        f"Literal angka tidak valid: {teks!r} — {alasan}.", baris, kolom, **kw
    )


def err_nama_tidak_valid(teks: str, baris: int, kolom: int, alasan: str, **kw) -> KesalahanLeksikal:
    return KesalahanLeksikal(
        f"Nama tidak valid: {teks!r} — {alasan}.", baris, kolom, **kw
    )


def err_indent_tak_terduga(baris: int, kolom: int, **kw) -> KesalahanLeksikal:
    return KesalahanLeksikal(
        "Indentasi muncul sebelum ada pernyataan — baris ini tidak punya induk blok.",
        baris,
        kolom,
        **kw,
    )


def err_token_diharapkan(diharapkan: str, didapat: str, baris: int, kolom: int, **kw) -> KesalahanSintaks:
    return KesalahanSintaks(
        f"Diharapkan {diharapkan}, tetapi mendapat {didapat!r}.", baris, kolom, **kw
    )


def err_ekspresi_diharapkan(didapat: str, baris: int, kolom: int, **kw) -> KesalahanSintaks:
    return KesalahanSintaks(
        f"Diharapkan ekspresi, tetapi mendapat {didapat!r}.", baris, kolom, **kw
    )


def err_indentasi_tak_konsisten(baris: int, **kw) -> KesalahanSintaks:
    return KesalahanSintaks(
        "Indentasi tidak konsisten — periksa spasi atau tab pada blok kode.", baris, **kw
    )


def err_dedent_tak_cocok(baris: int, kolom: int = 0, **kw) -> KesalahanSintaks:
    return KesalahanSintaks(
        "Dedentasi tidak cocok dengan level indentasi sebelumnya.",
        baris,
        kolom,
        **kw,
    )


def err_blok_kosong(baris: int, kolom: int, **kw) -> KesalahanSintaks:
    return KesalahanSintaks(
        "Blok pernyataan kosong — isi blok dengan minimal satu baris.", baris, kolom, **kw
    )


def err_kata_kunci_sebagai_nama(nama: str, baris: int, kolom: int, **kw) -> KesalahanSintaks:
    return KesalahanSintaks(
        f"{nama!r} adalah kata kunci khusus dan tidak boleh dipakai sebagai nama.",
        baris,
        kolom,
        **kw,
    )


def err_variabel_belum_ada(nama: str, baris: int, **kw) -> KesalahanNama:
    return KesalahanNama(f"Nama {nama!r} belum didefinisikan atau tidak ditemukan.", baris, **kw)


def err_simpul_tak_dikenal(jenis: str, **kw) -> KesalahanTranspilasi:
    return KesalahanTranspilasi(
        f"Jenis simpul AST tidak dikenal: {jenis!r} — fitur ini mungkin belum didukung.",
        **kw,
    )

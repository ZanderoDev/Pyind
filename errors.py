"""
errors.py — Kelas error dengan pesan dalam Bahasa Indonesia.
Bagian dari proyek Pyind (Python Indonesia).

Semua error yang terjadi selama proses transpilasi akan menggunakan
kelas-kelas di bawah ini agar pesan kesalahan mudah dipahami.
"""


class PyindError(Exception):
    """Kelas dasar untuk semua error transpiler Pyind."""

    def __init__(self, pesan: str, baris: int = 0, kolom: int = 0):
        self.pesan = pesan
        self.baris = baris
        self.kolom = kolom
        lokasi = f" (baris {baris}, kolom {kolom})" if baris else ""
        super().__init__(f"[Pyind]{lokasi} {pesan}")


class KesalahanLeksikal(PyindError):
    """Error pada tahap tokenisasi (lexer)."""
    pass


class KesalahanSintaks(PyindError):
    """Error pada tahap parsing (parser) — sintaks tidak valid."""
    pass


class KesalahanTranspilasi(PyindError):
    """Error pada tahap pembangkitan kode (transpiler)."""
    pass


class KesalahanNama(PyindError):
    """Variabel atau nama yang digunakan belum didefinisikan."""
    pass


# ── Pesan error siap pakai ──────────────────────────────────────────────────

def err_karakter_tak_dikenal(karakter: str, baris: int, kolom: int) -> KesalahanLeksikal:
    return KesalahanLeksikal(
        f"Karakter tidak dikenal: '{karakter}'", baris, kolom
    )


def err_string_tidak_ditutup(baris: int, kolom: int) -> KesalahanLeksikal:
    return KesalahanLeksikal(
        "Tanda kutip string tidak ditutup dengan benar.", baris, kolom
    )


def err_token_diharapkan(diharapkan: str, didapat: str, baris: int, kolom: int) -> KesalahanSintaks:
    return KesalahanSintaks(
        f"Diharapkan '{diharapkan}', tetapi mendapat '{didapat}'.", baris, kolom
    )


def err_ekspresi_diharapkan(didapat: str, baris: int, kolom: int) -> KesalahanSintaks:
    return KesalahanSintaks(
        f"Diharapkan ekspresi, tetapi mendapat '{didapat}'.", baris, kolom
    )


def err_indentasi_tak_konsisten(baris: int) -> KesalahanSintaks:
    return KesalahanSintaks(
        "Indentasi tidak konsisten — periksa spasi atau tab pada blok kode.", baris
    )


def err_dedent_tak_cocok(baris: int) -> KesalahanSintaks:
    return KesalahanSintaks(
        "Dedentasi tidak cocok dengan level indentasi sebelumnya.", baris
    )


def err_variabel_belum_ada(nama: str, baris: int) -> KesalahanNama:
    return KesalahanNama(
        f"Nama '{nama}' belum didefinisikan atau tidak dapat ditemukan.", baris
    )


def err_simpul_tak_dikenal(jenis: str) -> KesalahanTranspilasi:
    return KesalahanTranspilasi(
        f"Jenis simpul AST tidak dikenal: '{jenis}'. "
        "Mungkin fitur ini belum didukung."
    )

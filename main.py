"""
main.py — CLI entry point untuk Pyind.
Bagian dari proyek Pyind (Python Indonesia).

Penggunaan:
    python main.py                              # masuk REPL
    python main.py jalankan file.pyind          # transpilasi + jalankan
    python main.py ekspor  file.pyind -o out.py # transpilasi + simpan
    python main.py repl                         # masuk REPL (eksplisit)
    python main.py file.pyind                   # shortcut jalankan
"""

from __future__ import annotations

import argparse
import sys
import os

# Tambahkan direktori ini ke path agar impor modul lokal bisa berjalan
sys.path.insert(0, os.path.dirname(__file__))

from lexer import Lexer
from parser import Parser
from transpiler import Transpiler
from errors import PyindError


# ── Warna terminal (ANSI, dinonaktifkan jika bukan TTY) ──────────────────────

_WARNA_AKTIF = sys.stderr.isatty()


def merah(teks: str) -> str:
    return f"\033[31m{teks}\033[0m" if _WARNA_AKTIF else teks


# ── Konstanta ─────────────────────────────────────────────────────────────────

EKSTENSI_PYIND = ".pyind"
VERSI = "1.0.0"
BANNER = f"Pyind v{VERSI} — Transpiler Bahasa Indonesia ke Python"


# ── Proses transpilasi ────────────────────────────────────────────────────────

def proses_transpilasi(source: str) -> str:
    """
    Jalankan pipeline penuh: Lexer → Parser → AST → Transpiler.
    Kembalikan kode Python yang siap dieksekusi.
    """
    tokens = Lexer(source).tokenisasi()
    ast    = Parser(tokens).parse()
    kode   = Transpiler().transpile(ast)
    return kode


def baca_file(path: str) -> str:
    """Baca file source .pyind dan kembalikan isinya."""
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(merah(f"[Pyind] Error: File '{path}' tidak ditemukan."), file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(merah(f"[Pyind] Error: Tidak ada izin membaca file '{path}'."), file=sys.stderr)
        sys.exit(1)


# ── Sub-perintah CLI ──────────────────────────────────────────────────────────

def cmd_jalankan(args: argparse.Namespace) -> None:
    """
    Perintah: python main.py jalankan file.pyind
    Transpilasi lalu langsung jalankan hasilnya.
    """
    source = baca_file(args.file)
    try:
        kode_python = proses_transpilasi(source)
    except PyindError as e:
        print(merah(str(e)), file=sys.stderr)
        sys.exit(1)

    if args.tampilkan:
        print("─── Kode Python yang dihasilkan ───")
        print(kode_python)
        print("─── Output eksekusi ───")

    namespace: dict = {}
    try:
        exec(compile(kode_python, args.file, "exec"), namespace)
    except Exception as e:
        tipe = type(e).__name__
        print(merah(f"[Pyind] Kesalahan saat menjalankan program: {tipe}: {e}"), file=sys.stderr)
        sys.exit(1)


def cmd_ekspor(args: argparse.Namespace) -> None:
    """
    Perintah: python main.py ekspor file.pyind [-o output.py]
    Transpilasi dan simpan hasil ke file .py tanpa menjalankannya.
    """
    source = baca_file(args.file)
    try:
        kode_python = proses_transpilasi(source)
    except PyindError as e:
        print(merah(str(e)), file=sys.stderr)
        sys.exit(1)

    if args.output:
        output_path = args.output
    else:
        base = os.path.splitext(args.file)[0]
        output_path = base + ".py"

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# Dihasilkan oleh Pyind dari: {args.file}\n")
            f.write(kode_python)
        print(f"[Pyind] Berhasil diekspor ke '{output_path}'")
    except PermissionError:
        print(merah(f"[Pyind] Error: Tidak ada izin menulis ke '{output_path}'."), file=sys.stderr)
        sys.exit(1)


# ── REPL — helpers ────────────────────────────────────────────────────────────

_KATA_KELUAR: frozenset[str] = frozenset({"keluar()", "exit()", "quit()", "q"})


def _baris_membuka_blok(baris: str) -> bool:
    """
    True jika baris ini membuka blok baru (diakhiri ':' setelah hapus komentar).
    Contoh: 'jika x > 0:', 'fungsi sapa(nama):', 'coba:'
    """
    stripped = baris.strip()
    if not stripped or stripped.startswith("#"):
        return False
    tanpa_komentar = stripped.split("#")[0].rstrip()
    return tanpa_komentar.endswith(":")


def _level_indentasi(baris: str) -> int:
    """Jumlah spasi/tab di awal baris."""
    return len(baris) - len(baris.lstrip())


def _buffer_selesai(buffer: list[str]) -> bool:
    """
    True jika buffer sudah membentuk blok yang lengkap tanpa menunggu baris kosong.

    Dipakai untuk mendukung pola seperti:
        jika x > 0:
            cetak("positif")
        cetak("selesai")   ← level 0, bukan pembuka blok → selesai otomatis

    Logika: lihat baris bermakna terakhir.
    - Jika masih indented → belum selesai.
    - Jika di level 0 tapi membuka blok (seperti 'lainnya:') → belum selesai.
    - Jika di level 0 dan bukan pembuka blok → selesai.
    """
    baris_bermakna = [b for b in buffer if b.strip() and not b.strip().startswith("#")]
    if not baris_bermakna:
        return True
    baris_terakhir = baris_bermakna[-1]
    if _level_indentasi(baris_terakhir) > 0:
        return False   # masih di dalam blok
    if _baris_membuka_blok(baris_terakhir):
        return False   # baris terakhir adalah header blok baru (lainnya:, kecuali:, dst.)
    return True


def _eksekusi_repl(kode_python: str, ns: dict) -> None:
    """
    Eksekusi kode Python hasil transpilasi di namespace REPL.

    - Coba eval dulu: jika berhasil, tampilkan repr hasil (seperti Python REPL).
    - Jika SyntaxError (bukan ekspresi), fallback ke exec.
    - Exception runtime ditampilkan tanpa keluar dari REPL.
    """
    kode_strip = kode_python.strip()
    try:
        nilai = eval(compile(kode_strip, "<repl>", "eval"), ns)  # type: ignore[arg-type]
        if nilai is not None:
            print(repr(nilai))
    except SyntaxError:
        # Bukan ekspresi tunggal (pernyataan, blok, dsb.) → exec
        try:
            exec(compile(kode_python, "<repl>", "exec"), ns)
        except Exception as e:
            print(merah(f"[Pyind] {type(e).__name__}: {e}"), file=sys.stderr)
    except Exception as e:
        print(merah(f"[Pyind] {type(e).__name__}: {e}"), file=sys.stderr)


def _flush_buffer(buffer: list[str], ns: dict) -> None:
    """Transpilasi dan eksekusi buffer jika tidak kosong."""
    source = "\n".join(buffer).rstrip() + "\n"
    buffer.clear()
    if not source.strip():
        return
    try:
        kode_python = proses_transpilasi(source)
    except PyindError as e:
        print(merah(str(e)), file=sys.stderr)
        return
    _eksekusi_repl(kode_python, ns)


# ── REPL — entry point ────────────────────────────────────────────────────────

def cmd_repl(_args: object = None) -> None:
    """
    Mode REPL interaktif Pyind.

    Perilaku:
    - Namespace persisten: variabel, fungsi, kelas, dan impor tetap hidup antar perintah.
    - Hasil ekspresi ditampilkan otomatis (seperti Python REPL).
    - Blok multi-baris (fungsi, jika, untuk, coba, kelas, dll.) dideteksi otomatis:
        * Prompt berubah ke '...'
        * Blok berakhir saat baris kosong dikirim, atau saat kembali ke level 0.
    - Ctrl+C → batalkan input saat ini (tidak keluar).
    - Ctrl+D (EOF) → eksekusi sisa buffer lalu keluar.
    - 'keluar()' / 'exit()' / 'quit()' → keluar.
    """
    py_ver = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    print(f"Pyind v{VERSI} (Python {py_ver})")
    print("Ketik 'q' atau tekan Ctrl+C untuk keluar.")

    ns: dict = {}          # namespace persisten antar perintah
    buffer: list[str] = [] # akumulasi baris untuk blok multi-baris

    while True:
        dalam_blok = bool(buffer)
        prompt_str = "... " if dalam_blok else ">>> "

        # ── Baca input ────────────────────────────────────────────────────
        try:
            baris = input(prompt_str)
        except EOFError:
            # Ctrl+D — eksekusi sisa buffer (jika ada) lalu keluar
            print()
            if buffer:
                _flush_buffer(buffer, ns)
            break
        except KeyboardInterrupt:
            # Ctrl+C — keluar dari REPL
            print()
            break

        # ── Periksa perintah keluar ───────────────────────────────────────
        if baris.strip() in _KATA_KELUAR:
            print("Sampai jumpa!")
            break

        buffer.append(baris)

        # ── Deteksi kelengkapan blok ──────────────────────────────────────
        baris_kosong = baris.strip() == ""

        if dalam_blok and baris_kosong:
            # Baris kosong saat di dalam blok → sinyal akhir blok multi-baris
            _flush_buffer(buffer, ns)
            continue

        if not dalam_blok and not _baris_membuka_blok(baris):
            # Baris tunggal yang tidak membuka blok → eksekusi langsung
            _flush_buffer(buffer, ns)
            continue

        if _buffer_selesai(buffer):
            # Buffer sudah kembali ke level 0 (misal: blok if+else lengkap
            # diikuti baris di level 0 yang bukan pembuka blok baru)
            _flush_buffer(buffer, ns)
            continue

        # Masih menunggu kelanjutan blok — tampilkan prompt '...' di iterasi berikutnya


# ── Setup argparse ────────────────────────────────────────────────────────────

def buat_parser() -> argparse.ArgumentParser:
    """Buat dan kembalikan argparse parser untuk CLI Pyind."""
    ap = argparse.ArgumentParser(
        prog="pyind",
        description=BANNER,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh penggunaan:
  python main.py                                  masuk REPL interaktif
  python main.py repl                             masuk REPL (eksplisit)
  python main.py jalankan contoh/halo_dunia.pyind
  python main.py jalankan contoh/kalkulator.pyind --tampilkan
  python main.py ekspor  contoh/kalkulator.pyind -o hasil.py
  python main.py contoh/halo_dunia.pyind          shortcut 'jalankan'
        """,
    )
    ap.add_argument("--versi", "-v", action="version", version=f"Pyind {VERSI}")
    ap.add_argument(
        "--bantuan", action="help",
        help="Tampilkan pesan bantuan ini dan keluar",
    )

    sub = ap.add_subparsers(dest="perintah", metavar="PERINTAH")

    # ── jalankan ──────────────────────────────────────────────────────────────
    p_run = sub.add_parser(
        "jalankan",
        help="Transpilasi dan langsung jalankan file .pyind",
        description="Transpilasi file Pyind lalu jalankan hasilnya.",
    )
    p_run.add_argument("file", help="File source Pyind (.pyind)")
    p_run.add_argument(
        "--tampilkan", "-t",
        action="store_true",
        help="Tampilkan kode Python yang dihasilkan sebelum dijalankan",
    )

    # ── ekspor ────────────────────────────────────────────────────────────────
    p_exp = sub.add_parser(
        "ekspor",
        help="Transpilasi dan simpan hasil ke file .py",
        description="Transpilasi file Pyind dan simpan hasilnya sebagai file Python.",
    )
    p_exp.add_argument("file", help="File source Pyind (.pyind)")
    p_exp.add_argument(
        "--output", "-o",
        metavar="OUTPUT.py",
        help="Nama file output (default: nama_file.py)",
    )

    # ── repl ──────────────────────────────────────────────────────────────────
    sub.add_parser(
        "repl",
        help="Jalankan REPL interaktif Pyind",
        description="Mode interaktif — ketik kode Bahasa Indonesia langsung.",
    )

    return ap


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    argv = sys.argv[1:]
    perintah_dikenal = {"jalankan", "ekspor", "repl"}

    # Tidak ada argumen → masuk REPL langsung (tanpa print --help)
    if not argv:
        cmd_repl()
        return

    # Shortcut: `pyind file.pyind` diperlakukan seperti `pyind jalankan file.pyind`
    if argv[0] not in perintah_dikenal and not argv[0].startswith("-"):
        argv = ["jalankan"] + argv

    ap = buat_parser()
    args = ap.parse_args(argv)

    if args.perintah == "jalankan":
        cmd_jalankan(args)
    elif args.perintah == "ekspor":
        cmd_ekspor(args)
    elif args.perintah == "repl":
        cmd_repl(args)
    else:
        ap.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()

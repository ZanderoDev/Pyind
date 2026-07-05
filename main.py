"""
main.py — CLI entry point untuk Pyind.
Bagian dari proyek Pyind (Python Indonesia).

Penggunaan:
    python main.py jalankan contoh/halo_dunia.pyind
    python main.py ekspor  contoh/kalkulator.pyind -o kalkulator.py
    python main.py repl
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
        print(f"[Pyind] Error: File '{path}' tidak ditemukan.", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(f"[Pyind] Error: Tidak ada izin membaca file '{path}'.", file=sys.stderr)
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
        print(str(e), file=sys.stderr)
        sys.exit(1)

    if args.tampilkan:
        print("─── Kode Python yang dihasilkan ───")
        print(kode_python)
        print("─── Output eksekusi ───")

    # Jalankan kode Python yang dihasilkan
    # exec() dipakai hanya di sini sebagai langkah akhir — bukan mekanisme transpilasi
    namespace: dict = {}
    try:
        exec(compile(kode_python, args.file, "exec"), namespace)
    except Exception as e:
        tipe = type(e).__name__
        print(f"[Pyind] Kesalahan saat menjalankan program: {tipe}: {e}", file=sys.stderr)
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
        print(str(e), file=sys.stderr)
        sys.exit(1)

    # Tentukan nama file output
    if args.output:
        output_path = args.output
    else:
        # Ganti ekstensi .pyind → .py secara otomatis
        base = os.path.splitext(args.file)[0]
        output_path = base + ".py"

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# Dihasilkan oleh Pyind dari: {args.file}\n")
            f.write(kode_python)
        print(f"[Pyind] Berhasil diekspor ke '{output_path}'")
    except PermissionError:
        print(f"[Pyind] Error: Tidak ada izin menulis ke '{output_path}'.", file=sys.stderr)
        sys.exit(1)


def cmd_repl(_args: argparse.Namespace) -> None:
    """
    Perintah: python main.py repl
    REPL interaktif — ketik kode Bahasa Indonesia baris per baris.
    Ketik 'keluar' atau Ctrl+C untuk keluar.
    """
    print(BANNER)
    print("Mode REPL — ketik kode Bahasa Indonesia (Ctrl+C atau 'keluar' untuk keluar)\n")

    buffer: list[str] = []
    indent_aktif = False

    while True:
        try:
            prompt = "...  " if indent_aktif else ">>> "
            baris = input(prompt)
        except (KeyboardInterrupt, EOFError):
            print("\nSampai jumpa!")
            break

        if baris.strip().lower() in ("keluar", "exit", "quit"):
            print("Sampai jumpa!")
            break

        buffer.append(baris)

        # Deteksi sederhana apakah blok masih terbuka
        indent_aktif = baris.endswith(":") or (indent_aktif and baris.startswith(("    ", "\t")))

        # Blok selesai saat baris kosong dikirim dalam mode indent
        if indent_aktif and baris.strip() == "":
            indent_aktif = False

        if not indent_aktif:
            source = "\n".join(buffer)
            buffer.clear()
            if source.strip():
                try:
                    kode = proses_transpilasi(source)
                    exec(compile(kode, "<repl>", "exec"), {})
                except PyindError as e:
                    print(str(e))
                except Exception as e:
                    print(f"Kesalahan: {type(e).__name__}: {e}")


# ── Setup argparse ────────────────────────────────────────────────────────────

def buat_parser() -> argparse.ArgumentParser:
    """Buat dan kembalikan argparse parser untuk CLI Pyind."""
    ap = argparse.ArgumentParser(
        prog="pyind",
        description=BANNER,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh penggunaan:
  python main.py jalankan contoh/halo_dunia.pyind
  python main.py jalankan contoh/kalkulator.pyind --tampilkan
  python main.py ekspor  contoh/kalkulator.pyind -o hasil.py
  python main.py repl
        """,
    )
    ap.add_argument("--versi", action="version", version=f"Pyind {VERSI}")

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
    ap = buat_parser()
    args = ap.parse_args()

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

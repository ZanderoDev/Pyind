# Changelog

Semua perubahan penting pada proyek Pyind dicatat di sini.

Format mengikuti [Keep a Changelog](https://keepachangelog.com/id/1.0.0/),
versi mengikuti [Semantic Versioning](https://semver.org/lang/id/).

---

## [1.0.0] — 2026-07-06

Rilis perdana Pyind — transpiler Bahasa Indonesia ke Python.

### Ditambahkan

#### Inti Transpiler
- **Lexer** (`lexer.py`) — tokenizer rekursif karakter-per-karakter; mendukung 46 kata kunci Bahasa Indonesia, string literal dijaga utuh (tidak diterjemahkan), longest-match-first untuk operator multi-karakter (`**=`, `//=`, dsb.)
- **Parser** (`parser.py`) — recursive descent parser; membangun AST lengkap; mendukung tuple unpacking, eksponen kanan-asosiatif, serta keyword yang valid sebagai identifier (mis. `fungsi kosong(diri):`)
- **Transpiler** (`transpiler.py`) — traversal AST rekursif; menghasilkan kode Python valid dengan indentasi otomatis; penanganan presedensi operator yang benar untuk `**`
- **Keywords** (`keywords.py`) — peta 46 kata kunci Indonesia→Python beserta operator satu, dua, dan tiga karakter
- **Errors** (`errors.py`) — hierarki `PyindError` dengan pesan kesalahan dalam Bahasa Indonesia

#### CLI (`main.py`)
- `pyind` — masuk REPL interaktif langsung tanpa argumen
- `pyind namafile.pyind` — shortcut jalankan file tanpa subperintah
- `pyind jalankan namafile.pyind` — transpilasi + eksekusi; flag `--tampilkan` untuk lihat kode Python hasil
- `pyind ekspor namafile.pyind` — transpilasi + simpan ke `.py`; flag `-o` untuk tentukan nama output
- `pyind --versi` — tampilkan versi
- `pyind --bantuan` — tampilkan bantuan

#### REPL Interaktif
- Prompt `>>> ` dan `... ` persis seperti Python REPL
- Namespace persisten — variabel, fungsi, kelas, dan impor tetap hidup antar perintah
- Hasil ekspresi ditampilkan otomatis (`repr`)
- Deteksi blok multi-baris otomatis (blok berakhir dengan baris kosong)
- `q`, `keluar()`, `exit()`, `quit()` → keluar dari REPL
- Ctrl+C → keluar dari REPL
- Ctrl+D → eksekusi sisa buffer lalu keluar
- Error runtime ditampilkan tanpa menutup REPL

#### Installer (`install.sh`)
- Deteksi environment otomatis: **Termux**, **Acode Terminal**, **Linux**
- Instalasi dependensi via `pkg` (Termux), `apt`, `apk`, `dnf`, atau `pacman`
- Cek versi Python minimum (3.7+) dengan pesan kesalahan jelas
- Update otomatis jika Pyind sudah terpasang (`git pull`)
- Buat symlink global `pyind` di `$PREFIX/bin` (Termux), `/usr/local/bin`, atau `~/.local/bin`
- Tambah `$BIN_DIR` ke PATH di `.bashrc`, `.bash_profile`, `.zshrc`, dan `.profile`

#### Lainnya
- **131 unit test** — mencakup Lexer, Parser, dan Transpiler (`pytest tests/ -v`)
- **3 file contoh** — `halo_dunia.pyind`, `kalkulator.pyind`, `loop_dan_fungsi.pyind`
- **VS Code Extension** (`pyind-syntax/`) — syntax highlighting untuk file `.pyind`
- **Lisensi MIT** — Copyright 2026 Zandero

---

## Kata Kunci yang Didukung (46)

| Indonesia       | Python      | Indonesia    | Python     |
|-----------------|-------------|--------------|------------|
| `fungsi`        | `def`       | `impor`      | `import`   |
| `kelas`         | `class`     | `dari`       | `from`     |
| `kembali`       | `return`    | `sebagai`    | `as`       |
| `kembalikan`    | `return`    | `menjadi`    | `as`       |
| `jika`          | `if`        | `coba`       | `try`      |
| `jika_tidak`    | `elif`      | `kecuali`    | `except`   |
| `lainnya`       | `else`      | `akhirnya`   | `finally`  |
| `untuk`         | `for`       | `naikkan`    | `raise`    |
| `selama`        | `while`     | `bersama`    | `with`     |
| `dalam`         | `in`        | `dan`        | `and`      |
| `hentikan`      | `break`     | `atau`       | `or`       |
| `lanjut`        | `continue`  | `bukan`      | `not`      |
| `lewati`        | `pass`      | `tidak`      | `not`      |
| `lewat`         | `pass`      | `benar`      | `True`     |
| `global`        | `global`    | `salah`      | `False`    |
| `nonlokal`      | `nonlocal`  | `kosong`     | `None`     |
| `hapus`         | `del`       | `cetak`      | `print`    |
| `lambda`        | `lambda`    | `masukkan`   | `input`    |
| `pernyataan`    | `assert`    | `panjang`    | `len`      |
| `bilangan`      | `int`       | `rentang`    | `range`    |
| `desimal`       | `float`     | `tipe`       | `type`     |
| `teks`          | `str`       | `daftar`     | `list`     |
| `himpunan`      | `set`       | `kamus`      | `dict`     |

---

[1.0.0]: https://github.com/ZanderoDev/Pyind/releases/tag/v1.0.0

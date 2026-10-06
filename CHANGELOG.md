# Changelog

Semua perubahan penting pada proyek Pyind dicatat di sini.

Format mengikuti [Keep a Changelog](https://keepachangelog.com/id/1.0.0/),
versi mengikuti [Semantic Versioning](https://semver.org/lang/id/).

---

## [1.1.0] — 2026-10-06

Penyempurnaan mendasar pada lexer, parser, transpiler, dan dokumentasi.

### Ditambahkan

#### API Bahasa Indonesia
- Metode utama kini berbahasa Indonesia; alias Inggris dipertahankan:
  - `Lexer.tokenisasi()` (alias `tokenize`)
  - `Parser.urai()` (alias `parse`)
  - `Transpiler.terjemahkan()` (alias `transpile`)
  - fungsi modul `urai(source)` dan `terjemahkan(ast)`
- `Token.teks_asli` menyimpan ejaan sumber apa adanya, terpisah dari
  `Token.nilai` yang berisi padanan Python.

#### Leksikon
- Pemisahan tegas antara kata kunci *reserved*, kata kunci *kontekstual*
  (soft keyword), dan fungsi bawaan — meniru perilaku Python.
- Kata kunci kontekstual (`cetak`, `panjang`, `dalam`, …) boleh identifier.
- Angka: basis biner/oktal/heksadesimal, underscore, eksponen, dan literal
  kompleks; galat untuk bentuk salah (`0123`, `0x`, `1.2e`, `1__2`, `123abc`).
- Prefiks string gabungan lengkap: `rb`, `br`, `fr`, `rf`, huruf besar-kecil.
- Operator `:=`, `>>=`, `<<=`, `&=`, `|=`, `^=`, `@=`, `...` ditambahkan.
- Identifier Unicode mengikuti XID_Start/XID_Continue.
- Indentasi tab dihitung kelipatan 8 kolom, sama seperti Python; indentasi
  pada baris pertama tanpa blok induk kini dilaporkan sebagai galat.

#### Parser
- Fungsi asinkron: `async fungsi`, `await`, `async untuk`, `async bersama`.
- Dekorator di atas fungsi dan kelas.
- Penghasil: `hasilkan` dan `hasilkan_dari` (padanan `yield` / `yield from`).
- Penugasan bertanda (`x: int = 5`), penugasan berbintang (`a, *b = data`),
  dan walrus `(n := panjang(a))`.
- Perbandingan berantai (`0 < x < 10`).
- Parameter posisional-only (`/`), keyword-only (`*`), dan anotasi tipe
  termasuk union (`int | str`) serta generik (`daftar[int]`).
- `with` menerima beberapa item dipisah koma; `raise … from …`didukung.
- Nama identifier kini dibaca dari `Token.teks_asli`, sehingga ejaan Bahasa
  Indonesia tidak lagi berubah menjadi padanan Python.
- Nama literal (`benar`/`salah`/`kosong`) sah sebagai nama fungsi, kelas,
  parameter, dan atribut — sesuai Python yang mengizinkan `None`/`True`
  sebagai nama atribut.

#### Transpiler
- Resolver simbol per-scope: `cetak("x")` menjadi `print("x")` selama
  `cetak` belum diikat, tetapi menjadi `cetak("x")` setelah di-bind.
- Bentuk sumber literal dipertahankan: `0x1f`, `1_000`, `rb"ab"` tidak
  ditulis ulang lewat `repr()`.
- Slice kosong distinguished dari ekspresi bernilai nol: `a[:]`, `a[0:0]`,
  `a[::2]`, `a[::0]` semuanya benar.
- Kurung eksplisit dari sumber dipertahankan agar makna tanda dan urutan
  evaluasi tidak berubah, mis. `(-2) ** 2`.
- Indentasi kompatibel Python.

#### Diagnostik
- `errors.py` diberi kode galat stabil (`E1001`, `E2001`, `E3001`, `E4001`),
  nama berkas, rentang lokasi, cuplikan sumber, dan penunjuk `^`.
- Pesan galat lebih spesifik dan menyebut ejaan sumber yang ditemukan.

#### Ekstensi editor

- **Syntax highlighting VS Code** (`extensi/vscode/`) — grammar TextMate
  dibangun ulang dari `keywords.py`; kini mencakup penghasil `hasilkan` /
  `hasilkan_dari`, dekorator, operator `:=` dan `...`, angka biner/oktal/
  heksa/kompleks, prefiks string gabungan `rb`/`br`/`fr`/`rf`, dan identifier
  Unicode. `publisher` diperbaiki menjadi `ZanderoDev` (sebelumnya
  `ilham-local` yang menunjuk repo orang lain).
- **Syntax highlighting Acode** (`extensi/acode/`) — plugin StreamLanguage
  ditulis ulang agar dapat dibaca dan memakai leksikon yang sama.
- **Generator** (`extensi/alat/sinkronkan_leksikon.py`) — membangun ulang
  grammar TextMate dan daftar kata kunci plugin dari `keywords.py`, sehingga
  highlight tidak akan tertinggal dari transpiler.
- **75 uji konsistensi** (`tests/test_highlight.py`) — memverifikasi grammar
  mencakup seluruh leksikon dan tidak salah menandai soft keyword.
- Ikon Acode diganti dari screenshot 900 KB menjadi ikon vektor-bentuk 3 KB.

#### Dokumentasi
- `docs/bahasa.md` — referensi bahasa lengkap: leksikon, literal,
  presedensi operator, fitur yang didukung dan belum didukung, serta
  format diagnostik.
- README diperbarui: klaim leksikon dan cakupan AST disesuaikan,
  bagian Fitur Lanjutan dan Arsitektur ditulis ulang.

### Diperbaiki
- Bug konsumsi token ganda pada daftar, dict, tuple, dan kelas (tanda baca
  kurung bisa terlewat sehingga galat menyesatkan).
- Slice bernilai nol tidak lagi salah dianggap kosong.
- `kelas Turunan(Induk):` gagal diurai karena `(` tidak dikonsumsi.
- Angka `0b2`, `1__2`, dan bentuk tidak valid lain kini ditolak.
- String multi-baris dan baris lanjutan dengan `\` ditangani.
- Operator `**=` dan `//=` tetap satu token (regresi longest-match).

### Installer
- Perbaikan `install.sh`:
  - Baris PATH tidak lagi menumpuk setiap installer dijalankan ulang; duplikat
    dari versi lama dibersihkan otomatis
  - Baris PATH ditulis ke `.bashrc` **dan** `.profile`, karena shell login
    membaca `.bash_profile` lalu `.profile`, bukan `.bashrc`
  - Installer tidak lagi mempercayai PATH sesi berjalan; yang ditulis ke konfigurasi
    shell sehingga `pyind` langsung bisa dipanggil di terminal baru
  - Menjalankan dari dalam salinan repo akan menyalin kode itu ke `~/.pyind`
    tanpa clone ulang
  - Lokasi instalasi bisa diatur lewat `PYIND_DIR`
  - Mode baru: `bash install.sh copot` menghapus salinan, symlink, dan baris PATH
  - `bash install.sh --help` menampilkan opsi
- Persyaratan Python dinaikkan ke **3.9+** (dari 3.7+).
- API utama proyek kini berbahasa Indonesia; alias Inggris tetap ada.

---

## [1.0.0] — 2026-07-06

Rilis perdana Pyind — transpiler Bahasa Indonesia ke Python.

### Ditambahkan

#### Inti Transpiler
- **Lexer** (`lexer.py`) — tokenizer karakter-per-karakter; mengenali leksikon Bahasa Indonesia, string literal dijaga utuh (tidak diterjemahkan), longest-match-first untuk operator multi-karakter (`**=`, `//=`, dsb.)
- **Parser** (`parser.py`) — recursive descent parser; membangun AST berbentuk `dict`; mendukung tuple unpacking, eksponen kanan-asosiatif, serta nama kontekstual yang valid sebagai identifier (mis. `fungsi kosong(diri):`)
- **Transpiler** (`transpiler.py`) — traversal AST rekursif; menghasilkan kode Python valid dengan indentasi otomatis; penanganan presedensi operator yang benar untuk `**`
- **Keywords** (`keywords.py`) — leksikon Bahasa Indonesia (reserved, kontekstual, fungsi bawaan) beserta operator satu, dua, dan tiga karakter
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
- Cek versi Python minimum dengan pesan kesalahan jelas
- Update otomatis jika Pyind sudah terpasang (`git pull`)
- Buat symlink global `pyind` di `$PREFIX/bin` (Termux), `/usr/local/bin`, atau `~/.local/bin`
- Tambah `$BIN_DIR` ke PATH di `.bashrc`, `.bash_profile`, `.zshrc`, dan `.profile`

#### Lainnya
- **Unit test** — mencakup Lexer, Parser, dan Transpiler (`pytest tests/ -v`)
- **3 file contoh** — `halo_dunia.pyind`, `kalkulator.pyind`, `loop_dan_fungsi.pyind`
- **Lisensi MIT** — Copyright 2026 Zandero

---

## Kata Kunci yang Didukung (46)

- **`fungsi`** — `def`
  - **`impor`** — `import`
- **`kelas`** — `class`
  - **`dari`** — `from`
- **`kembali`** — `return`
  - **`sebagai`** — `as`
- **`kembalikan`** — `return`
  - **`menjadi`** — `as`
- **`jika`** — `if`
  - **`coba`** — `try`
- **`jika_tidak`** — `elif`
  - **`kecuali`** — `except`
- **`lainnya`** — `else`
  - **`akhirnya`** — `finally`
- **`untuk`** — `for`
  - **`naikkan`** — `raise`
- **`selama`** — `while`
  - **`bersama`** — `with`
- **`dalam`** — `in`
  - **`dan`** — `and`
- **`hentikan`** — `break`
  - **`atau`** — `or`
- **`lanjut`** — `continue`
  - **`bukan`** — `not`
- **`lewati`** — `pass`
  - **`tidak`** — `not`
- **`lewat`** — `pass`
  - **`benar`** — `True`
- **`global`** — `global`
  - **`salah`** — `False`
- **`nonlokal`** — `nonlocal`
  - **`kosong`** — `None`
- **`hapus`** — `del`
  - **`cetak`** — `print`
- **`lambda`** — `lambda`
  - **`masukkan`** — `input`
- **`pernyataan`** — `assert`
  - **`panjang`** — `len`
- **`bilangan`** — `int`
  - **`rentang`** — `range`
- **`desimal`** — `float`
  - **`tipe`** — `type`
- **`teks`** — `str`
  - **`daftar`** — `list`
- **`himpunan`** — `set`
  - **`kamus`** — `dict`

---

[1.1.0]: https://github.com/ZanderoDev/Pyind/releases/tag/v1.1.0
[1.0.0]: https://github.com/ZanderoDev/Pyind/releases/tag/v1.0.0

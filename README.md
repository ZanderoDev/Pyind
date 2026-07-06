# Pyind 🇮🇩

**Pyind** adalah transpiler yang mengubah kode dengan sintaks **Bahasa Indonesia** menjadi kode Python valid, lalu langsung menjalankannya.

```
Kode .pyind  →  Lexer  →  Parser  →  AST  →  Transpiler  →  Python
```

---

## Instalasi

### Termux / Acode Terminal / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/ZanderoDev/Pyind/main/install.sh | bash
```

atau jika sudah di-clone:

```bash
bash install.sh
```

Setelah instalasi, buka terminal baru lalu jalankan:

```bash
pyind --versi
```

### Persyaratan

- Python 3.7 atau lebih baru
- Git (untuk instalasi otomatis)
- pytest — hanya untuk menjalankan unit test

```bash
pip install pytest
```

---

## Struktur Folder

```
Pyind/
├── main.py        # CLI entry point
├── lexer.py       # Tokenizer — teks → token
├── parser.py      # Parser   — token → AST
├── transpiler.py  # Generator — AST → kode Python
├── keywords.py    # Peta kata kunci Bahasa Indonesia → Python
├── errors.py      # Kelas error berbahasa Indonesia
├── install.sh     # Installer otomatis
├── tests/
│   ├── test_lexer.py
│   ├── test_parser.py
│   └── test_transpiler.py
└── contoh/
    ├── halo_dunia.pyind       # Contoh 1: Halo Dunia
    ├── kalkulator.pyind       # Contoh 2: Kalkulator
    └── loop_dan_fungsi.pyind  # Contoh 3: Loop & Fungsi
```

---

## Cara Pakai

### Setelah install global (`pyind`)

```bash
# Masuk REPL interaktif
pyind

# Jalankan file .pyind
pyind namafile.pyind
pyind jalankan namafile.pyind

# Lihat kode Python yang dihasilkan sebelum dijalankan
pyind jalankan namafile.pyind --tampilkan

# Ekspor ke file .py (tanpa menjalankan)
pyind ekspor namafile.pyind
pyind ekspor namafile.pyind -o output.py

# Cek versi
pyind --versi
```

### Tanpa install (langsung dari folder)

```bash
python main.py jalankan contoh/halo_dunia.pyind
python main.py ekspor  contoh/kalkulator.pyind -o hasil.py
python main.py repl
```

---

## REPL Interaktif

Jalankan `pyind` tanpa argumen untuk masuk ke mode interaktif:

```
$ pyind
Pyind v1.0.0 (Python 3.11.6)
Ketik 'keluar()' atau tekan Ctrl+D untuk keluar.
>>> x = 10
>>> x * 3
30
>>> cetak("halo dari REPL")
halo dari REPL
```

### Blok multi-baris

Blok yang dibuka dengan `:` otomatis masuk ke mode multi-baris. Tekan **Enter kosong** untuk mengeksekusi:

```
>>> fungsi kuadrat(n):
...      kembali n ** 2
...
>>> kuadrat(7)
49
```

### Pintasan keyboard

| Tombol | Aksi |
|--------|------|
| `keluar()` / `exit()` | Keluar dari REPL |
| Ctrl+D | Keluar dari REPL |
| Ctrl+C | Batalkan input saat ini (tidak keluar) |

---

## Kata Kunci yang Didukung

| Bahasa Indonesia  | Python      | Keterangan              |
|-------------------|-------------|-------------------------|
| `fungsi`          | `def`       | Definisi fungsi         |
| `kelas`           | `class`     | Definisi kelas          |
| `kembali`         | `return`    | Nilai kembalian         |
| `kembalikan`      | `return`    | Alias `kembali`         |
| `jika`            | `if`        | Kondisi                 |
| `jika_tidak`      | `elif`      | Kondisi lanjutan        |
| `lainnya`         | `else`      | Kondisi default         |
| `untuk`           | `for`       | Loop iterasi            |
| `selama`          | `while`     | Loop kondisi            |
| `dalam`           | `in`        | Operator keanggotaan    |
| `hentikan`        | `break`     | Keluar dari loop        |
| `lanjut`          | `continue`  | Lanjut iterasi          |
| `lewati`          | `pass`      | Pernyataan kosong       |
| `lewat`           | `pass`      | Alias `lewati`          |
| `impor`           | `import`    | Impor modul             |
| `dari`            | `from`      | Impor dari modul        |
| `sebagai`         | `as`        | Alias impor             |
| `menjadi`         | `as`        | Alias `sebagai`         |
| `coba`            | `try`       | Blok percobaan          |
| `kecuali`         | `except`    | Tangkap exception       |
| `akhirnya`        | `finally`   | Selalu dijalankan       |
| `naikkan`         | `raise`     | Lempar exception        |
| `bersama`         | `with`      | Context manager         |
| `dan`             | `and`       | Operator logika         |
| `atau`            | `or`        | Operator logika         |
| `bukan`           | `not`       | Negasi logika           |
| `tidak`           | `not`       | Alias `bukan`           |
| `benar`           | `True`      | Nilai boolean           |
| `salah`           | `False`     | Nilai boolean           |
| `kosong`          | `None`      | Nilai null              |
| `global`          | `global`    | Variabel global         |
| `nonlokal`        | `nonlocal`  | Variabel closure        |
| `hapus`           | `del`       | Hapus variabel          |
| `lambda`          | `lambda`    | Fungsi anonim           |
| `pernyataan`      | `assert`    | Pernyataan asersi       |
| `cetak`           | `print`     | Tampilkan output        |
| `masukkan`        | `input`     | Baca input              |
| `panjang`         | `len`       | Panjang koleksi         |
| `rentang`         | `range`     | Rentang angka           |
| `tipe`            | `type`      | Tipe data               |
| `bilangan`        | `int`       | Konversi ke bilangan    |
| `desimal`         | `float`     | Konversi ke desimal     |
| `teks`            | `str`       | Konversi ke teks        |
| `daftar`          | `list`      | Tipe list               |
| `kamus`           | `dict`      | Tipe dictionary         |
| `himpunan`        | `set`       | Tipe set                |

---

## Contoh Kode

### Halo Dunia

```pyind
cetak("Halo, Dunia!")
```

### Fungsi dan kondisi

```pyind
fungsi sapa(nama):
    jika nama == "":
        kembali "Halo, Anonim!"
    kembali "Halo, " + nama + "!"

cetak(sapa("Budi"))
```

### Loop

```pyind
untuk i dalam rentang(1, 6):
    cetak("Iterasi ke-" + teks(i))
```

### Kelas

```pyind
kelas Hewan:
    fungsi __init__(diri, nama):
        diri.nama = nama

    fungsi suara(diri):
        cetak(diri.nama, "bersuara!")

h = Hewan("Kucing")
h.suara()
```

### Penanganan error

```pyind
coba:
    hasil = 10 / 0
kecuali ZeroDivisionError:
    cetak("Tidak bisa membagi dengan nol!")
```

### Impor modul

```pyind
dari math impor sqrt sebagai akar_kuadrat

cetak(akar_kuadrat(16))   # → 4.0
```

---

## Keamanan String

Kata kunci di dalam tanda kutip **tidak** diterjemahkan:

```pyind
cetak("jika hujan, bawa payung")
# → print("jika hujan, bawa payung")   ✓ bukan "if hujan, bawa payung"
```

---

## Menjalankan Unit Test

```bash
pytest tests/ -v
```

---

## Arsitektur

```
Lexer (lexer.py)
  Membaca source code karakter per karakter.
  Menghasilkan token: KATA_KUNCI, NAMA, ANGKA, TEKS, OP, DELIMITER,
  INDENT, DEDENT, BARIS_BARU, EOF.
  Longest-match-first: operator tiga karakter (mis. **=) dicek sebelum dua karakter.
  String literal dijaga utuh — isinya tidak diproses.

Parser (parser.py)
  Recursive Descent Parser.
  Mengonsumsi token dan membangun AST (pohon dict Python).
  Mendukung: penugasan, if/elif/else, while, for, def, class,
  try/except/finally, with, import, return, break, continue, pass,
  lambda, assert, del, global, nonlocal, eksponen kanan-asosiatif, dsb.

Transpiler (transpiler.py)
  Menelusuri AST secara rekursif.
  Menghasilkan kode Python valid dengan indentasi otomatis.

main.py (CLI)
  Subperintah: jalankan | ekspor | repl
  pyind (tanpa argumen) → langsung masuk REPL.
  Mengorkestrasi Lexer → Parser → Transpiler → exec().
```

---

## Lisensi

MIT — bebas digunakan dan dimodifikasi.

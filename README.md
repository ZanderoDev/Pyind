# Pyind 🇮🇩

**Pyind** (Python Indonesia) adalah transpiler yang mengubah kode dengan
sintaks **Bahasa Indonesia** menjadi kode Python valid, lalu langsung
menjalankannya.

```
Kode .pyind  →  Lexer  →  Parser  →  AST  →  Transpiler  →  Python
```

---

## Persyaratan

- Python 3.11 atau lebih baru
- pytest (hanya untuk menjalankan unit test)

```bash
pip install pytest
```

---

## Struktur Folder

```
pyind/
├── main.py        # CLI entry point
├── lexer.py       # Tokenizer — teks → token
├── parser.py      # Parser   — token → AST
├── transpiler.py  # Generator — AST → kode Python
├── keywords.py    # Peta kata kunci Bahasa Indonesia → Python
├── errors.py      # Kelas error berbahasa Indonesia
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

Semua perintah dijalankan dari dalam folder `pyind/`.

### 1. Jalankan file `.pyind`

```bash
python main.py jalankan contoh/halo_dunia.pyind
python main.py jalankan contoh/kalkulator.pyind
python main.py jalankan contoh/loop_dan_fungsi.pyind
```

Tambahkan `--tampilkan` untuk melihat kode Python yang dihasilkan:

```bash
python main.py jalankan contoh/halo_dunia.pyind --tampilkan
```

### 2. Ekspor ke file `.py`

Transpilasi tanpa langsung menjalankan — simpan hasilnya ke file Python:

```bash
python main.py ekspor contoh/kalkulator.pyind
# → menghasilkan contoh/kalkulator.py

python main.py ekspor contoh/kalkulator.pyind -o hasil.py
# → menghasilkan hasil.py
```

### 3. REPL interaktif

Ketik kode Bahasa Indonesia langsung di terminal:

```bash
python main.py repl
```

```
>>> x = 10
>>> cetak(x * 2)
20
>>> keluar
```

---

## Kata Kunci yang Didukung

| Bahasa Indonesia | Python    |
|-----------------|-----------|
| `fungsi`        | `def`     |
| `kelas`         | `class`   |
| `cetak`         | `print`   |
| `jika`          | `if`      |
| `jika_tidak`    | `elif`    |
| `lainnya`       | `else`    |
| `untuk`         | `for`     |
| `selama`        | `while`   |
| `dalam`         | `in`      |
| `rentang`       | `range`   |
| `benar`         | `True`    |
| `salah`         | `False`   |
| `kosong`        | `None`    |
| `kembali`       | `return`  |
| `hentikan`      | `break`   |
| `lanjut`        | `continue`|
| `lewati`        | `pass`    |
| `impor`         | `import`  |
| `dari`          | `from`    |
| `sebagai`       | `as`      |
| `coba`          | `try`     |
| `kecuali`       | `except`  |
| `akhirnya`      | `finally` |
| `naikkan`       | `raise`   |
| `dan`           | `and`     |
| `atau`          | `or`      |
| `bukan`         | `not`     |
| `bilangan`      | `int`     |
| `desimal`       | `float`   |
| `teks`          | `str`     |
| `panjang`       | `len`     |

---

## Contoh Kode

### Halo Dunia

```
cetak("Halo, Dunia!")
```

### Fungsi dan kondisi

```
fungsi sapa(nama):
    jika nama == "":
        kembali "Halo, Anonim!"
    kembali "Halo, " + nama + "!"

cetak(sapa("Budi"))
```

### Loop

```
untuk i dalam rentang(1, 6):
    cetak("Iterasi ke-", i)
```

### Kelas

```
kelas Hewan:
    fungsi __init__(diri, nama):
        diri.nama = nama

    fungsi suara(diri):
        cetak(diri.nama, "bersuara!")

h = Hewan("Kucing")
h.suara()
```

### Penanganan error

```
coba:
    hasil = 10 / 0
kecuali ZeroDivisionError:
    cetak("Tidak bisa membagi dengan nol!")
```

---

## Keamanan String

Kata kunci di dalam tanda kutip **tidak** akan diterjemahkan:

```
cetak("jika hujan, bawa payung")
# → print("jika hujan, bawa payung")   ✓ (bukan "if hujan, bawa payung")
```

---

## Menjalankan Unit Test

```bash
cd pyind
pytest tests/ -v
```

---

## Arsitektur

```
Lexer (lexer.py)
  Membaca source code karakter per karakter.
  Menghasilkan token: KATA_KUNCI, NAMA, ANGKA, TEKS, OP, DELIMITER,
  INDENT, DEDENT, BARIS_BARU, EOF.
  String literal dijaga utuh — isinya tidak diproses.

Parser (parser.py)
  Recursive Descent Parser.
  Mengonsumsi token dari Lexer dan membangun AST (pohon dict Python).
  Mendukung: penugasan, if/elif/else, while, for, def, class,
  try/except/finally, import, return, break, continue, pass, dsb.

Transpiler (transpiler.py)
  Menelusuri AST secara rekursif.
  Menghasilkan kode Python valid dengan indentasi otomatis.
  exec() hanya dipakai di main.py sebagai langkah akhir eksekusi.

main.py (CLI)
  Perintah: jalankan | ekspor | repl
  Mengorkestrasi Lexer → Parser → Transpiler → exec().
```

---

## Lisensi

MIT — bebas digunakan dan dimodifikasi.

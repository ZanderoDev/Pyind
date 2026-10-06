# Pyind 🇮🇩

**Pyind** adalah transpiler yang mengubah kode dengan sintaks **Bahasa Indonesia** menjadi kode Python valid, lalu langsung menjalankannya.

```
Kode .pyind  →  Lexer  →  Parser  →  AST  →  Transpiler  →  Python
```

Setiap tahap punya API berbahasa Indonesia:

```python
from lexer import Lexer
from parser import Parser
from transpiler import Transpiler

tokens = Lexer(source).tokenisasi()
ast    = Parser(tokens).urai()
kode   = Transpiler().terjemahkan(ast)
```

Alias dalam Bahasa Inggris (`tokenize`, `parse`, `transpile`) tetap tersedia
untuk kompatibilitas.

---

## Instalasi

### Termux / Acode Terminal / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/ZanderoDev/Pyind/main/install.sh | bash
```

atau jika sudah di-clone:

```bash
git clone https://github.com/ZanderoDev/Pyind.git
cd Pyind
bash install.sh
```

Menjalankan installer dari dalam salinan repo akan **menyalin** kode itu ke
`~/.pyind` — tanpa perlu clone ulang dari GitHub. Kalau tidak dijalankan dari
dalam repo, installer melakukan clone dangkal otomatis.

Untuk memasang ke lokasi lain:

```bash
PYIND_DIR="$HOME/.local/share/pyind" bash install.sh
```

Setelah instalasi, buka terminal baru lalu jalankan:

```bash
pyind --versi
```

### Copot / uninstall

```bash
bash install.sh copot
```

Menghapus salinan di `~/.pyind`, symlink `pyind`, dan baris PATH yang
installer tambahkan. Baris PATH lama mungkin masih aktif di terminal yang
terbuka — jalankan `hash -r` atau buka terminal baru.

### Perintah lain

```bash
bash install.sh --help     # tampilkan opsi
```

### Persyaratan

- Python 3.9 atau lebih baru
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
├── keywords.py    # Leksikon: reserved, kontekstual, dan fungsi bawaan
├── errors.py      # Kelas error & diagnostik berbahasa Indonesia
├── install.sh     # Installer otomatis
├── docs/
│   └── bahasa.md  # Referensi bahasa lengkap
├── extensi/
│   ├── vscode/    # Syntax highlighting untuk VS Code
│   ├── acode/     # Syntax highlighting untuk Acode
│   └── alat/      # Generator grammar dari keywords.py
├── tests/
│   ├── test_lexer.py
│   ├── test_parser.py
│   ├── test_transpiler.py
│   ├── test_regresi.py
│   └── test_highlight.py
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

- **`keluar()` / `exit()`** — Keluar dari REPL
- **Ctrl+D** — Keluar dari REPL
- **Ctrl+C** — Batalkan input saat ini (tidak keluar)

---

## Kata Kunci yang Didukung

### Kata kunci khusus (tidak boleh jadi nama)

- **`fungsi`** — `def` — Definisi fungsi
- **`kelas`** — `class` — Definisi kelas
- **`kembali`** — `return` — Nilai kembalian
- **`kembalikan`** — `return` — Alias `kembali`
- **`jika`** — `if` — Kondisi
- **`jika_tidak`** — `elif` — Kondisi lanjutan
- **`lainnya`** — `else` — Kondisi default
- **`untuk`** — `for` — Loop iterasi
- **`selama`** — `while` — Loop kondisi
- **`dalam`** — `in` — Operator keanggotaan
- **`hentikan`** — `break` — Keluar dari loop
- **`lanjut`** — `continue` — Lanjut iterasi
- **`lewati`** — `pass` — Pernyataan kosong
- **`impor`** — `import` — Impor modul
- **`dari`** — `from` — Impor dari modul
- **`sebagai`** — `as` — Alias impor
- **`menjadi`** — `as` — Alias `sebagai`
- **`coba`** — `try` — Blok percobaan
- **`kecuali`** — `except` — Tangkap exception
- **`akhirnya`** — `finally` — Selalu dijalankan
- **`naikkan`** — `raise` — Lempar exception
- **`bersama`** — `with` — Context manager
- **`dan`** — `and` — Operator logika
- **`atau`** — `or` — Operator logika
- **`bukan`** — `not` — Negasi logika
- **`tidak`** — `not` — Alias `bukan`
- **`benar`** — `True` — Nilai boolean
- **`salah`** — `False` — Nilai boolean
- **`kosong`** — `None` — Nilai null
- **`global`** — `global` — Variabel global
- **`nonlokal`** — `nonlocal` — Variabel closure
- **`hapus`** — `del` — Hapus variabel
- **`lambda`** — `lambda` — Fungsi anonim
- **`pernyataan`** — `assert` — Pernyataan asersi
- **`hasilkan`** — `yield` — Penghasil nilai
- **`hasilkan_dari`** — `yield from` — Penghasil dari iterable

### Fungsi bawaan (boleh jadi identifier)

Nama di bawah ini tetap bisa dipakai sebagai nama variabel selama belum
diikat ke nilai lain:

- **`cetak`** — `print` — Tampilkan output
- **`masukkan`** — `input` — Baca input
- **`panjang`** — `len` — Panjang koleksi
- **`rentang`** — `range` — Rentang angka
- **`tipe`** — `type` — Tipe data
- **`bilangan`** — `int` — Konversi ke bilangan
- **`desimal`** — `float` — Konversi ke desimal
- **`teks` / `sebut`** — `str` — Konversi ke teks
- **`daftar`** — `list` — Tipe list
- **`kamus`** — `dict` — Tipe dictionary
- **`himpunan`** — `set` — Tipe set
- **`urut`** — `sorted` — Urutkan
- **`jumlah`** — `sum` — Jumlahkan

```pyind
cetak("halo")           # → print("halo")

cetak = fungsi_lain
cetak("halo")           # → cetak("halo")   alias sudah mati
```

---

## Fitur Lanjutan

### Fungsi asinkron

```pyind
async fungsi ambil_data():
    kembali await permintaan()

async fungsi main():
    async untuk item dalam aliran():
        cetak(item)
    async bersama berkas() sebagai f:
        lewati
```

### Dekorator

```pyind
@cache
fungsi mahal(x):
    kembali x * 2
```

### Penghasil (generator)

```pyind
fungsi deret(n):
    untuk i dalam rentang(n):
        hasilkan i
    hasilkan_dari sumber_lain
```

### Penugasan lanjutan

```pyind
x: int = 5              # penugasan bertanda
a, *sisa = data         # unpacking berbintang
jika (n := panjang(a)) > 2:   # walrus
    cetak(n)
```

### Parameter modern

```pyind
fungsi proses(a, b, /, c, *, d=1, **kwargs):
    """a dan b posisional-only; d keyword-only."""
    kembali a + b + c + d
```

### Perbandingan berantai

```pyind
jika 0 < x < 10 dan x != 5:
    cetak("dalam rentang")
```

### Literal lanjutan

```pyind
besar   = 0xDEAD_BEEF
besar2  = 0b1010_1010
besar3  = 1_000_000
kompleks = 2j
pola    = rb"\x41"
```

Rujukan lengkap ada di [`docs/bahasa.md`](docs/bahasa.md).

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

Butuh Python 3.9+ dan pytest (satu-satunya dependensi, hanya untuk test).

---

## Arsitektur

```
Lexer (lexer.py)
  Analisis leksikal iteratif — memakai loop + generator, tanpa rekursi,
  jadi program panjang tidak memicu RecursionError.
  Menghasilkan token: NAMA, KATA_KUNCI, ANGKA, TEKS, BENAR/SALAH/KOSONG,
  OP, DELIMITER, BARIS_BARU, INDENT, DEDENT, EOF.
  Operator memakai longest-match-first (3 → 2 → 1 karakter).
  String & komentar dijaga utuh — isinya tidak pernah diterjemahkan.
  Bentuk sumber angka & string dipertahankan (0x_1f, 1_000, rb"ab").
  Indentasi: tab dihitung kelipatan 8 kolom, sama seperti Python.
  Identifier mengikuti XID_Start / XID_Continue (Unicode valid).

Parser (parser.py)
  Recursive descent parser; tiap level operator punya metode sendiri
  sehingga urutan presedensi terbaca langsung di kode.
  Menghasilkan AST berupa dict Python dengan kunci "jenis".
  Nama identifier diambil dari Token.teks_asli sehingga ejaan Bahasa
  Indonesia tidak berubah jadi padanan Python.
  Mendukung: penugasan biasa/bertanda/gabungan/bintang/walrus,
  if/elif/else, while, for, try/except/else/finally, with, import,
  def, class, dekorator, async/await, yield, lambda, global, nonlocal,
  perbandingan berantai, komprehensi, slice, parameter posisional-only
  dan keyword-only, anotasi tipe.

Transpiler (transpiler.py)
  Menelusuri AST dan membangkitkan kode Python dengan indentasi otomatis.
  Resolver simbol memutuskan apakah nama kontekstual masih berarti
  builtin (cetak → print) atau sudah di-bind (jadi cetak apa adanya).
  Murni pembangkitan teks: tanpa eval()/exec()/compile() di modul ini.

errors.py
  Hierarki PyindError dengan kode galat stabil dan cuplikan sumber
  berikut penunjuk caret.

main.py (CLI)
  Subperintah: jalankan | ekspor | repl
  pyind (tanpa argumen) → langsung masuk REPL.
  Hanya di CLI/REPL yang dipakai compile()/exec()/eval().

docs/bahasa.md
  Referensi bahasa lengkap: leksikon, literal, presedensi operator,
  fitur yang didukung dan belum didukung, serta format diagnostik.
```

## Ekstensi Editor

Syntax highlighting untuk file `.pyind`, tersedia untuk dua editor:

- **VS Code** — `pyind-syntax-1.1.0.vsix`
  - Pasang: Extensions → `···` → **Install from VSIX...**
- **Acode** — `Pyind-Acode-Plugin-1.1.0.zip`
  - Pasang: Plugin → **Install plugin from file**

Unduh dari [Releases Pyind](https://github.com/ZanderoDev/Pyind/releases).

Keduanya menyorot kata kunci khusus, kata kunci kontekstual, penghasil,
literal, angka (biner/oktal/heksa/kompleks), string berawalan, dekorator,
dan identifier Unicode.

Leksikon highlight **dibangun dari `keywords.py`** — satu sumber kebenaran.
Kalau kata kunci berubah di transpiler, jalankan:

```bash
python extensi/alat/sinkronkan_leksikon.py
```

`tests/test_highlight.py` gagal bila grammar dan `keywords.py` tidak sinkron.

---

## Lisensi

MIT — bebas digunakan dan dimodifikasi.

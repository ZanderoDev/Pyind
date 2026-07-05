# Pyind

**Pyind** adalah transpiler yang menerjemahkan kode dengan sintaks Bahasa Indonesia menjadi Python asli, lalu menjalankannya. Tujuannya sederhana: mengurangi beban menghafal sintaks bagi pemula Indonesia yang baru belajar pemrograman, tanpa mengorbankan pemahaman logika pemrograman itu sendiri.

```
fungsi sapa(nama):
    jika panjang(nama) > 0:
        cetak("Halo,", nama)
    lainnya:
        cetak("Nama kosong")

untuk i dalam rentang(3):
    sapa("Dunia")
```

diterjemahkan menjadi:

```python
def sapa(nama):
    if len(nama) > 0:
        print("Halo,", nama)
    else:
        print("Nama kosong")

for i in range(3):
    sapa("Dunia")
```

---

## Arsitektur

Pyind **bukan** sekadar regex-replace kata per kata. Ia dibangun dengan arsitektur compiler yang sebenarnya:

```
Kode .pyind
     │
     ▼
  Lexer        (tokenisasi, sadar konteks string literal)
     │
     ▼
  Parser       (recursive descent → AST)
     │
     ▼
 Transpiler    (AST → kode Python, precedence-aware)
     │
     ▼
  program.py
```

Karena berbasis AST (bukan pencocokan teks mentah), Pyind aman terhadap kasus seperti variabel bernama `forum` (yang secara tekstual mengandung potongan kata `for`) — ia tidak akan salah diterjemahkan.

---

## Instalasi

### Cara cepat (Linux, Termux, atau terminal Acode)

```bash
curl -fsSL https://raw.githubusercontent.com/ZanderoDev/Pyind/main/install.sh | bash
```

Script ini otomatis mendeteksi environment kamu (Termux, VPS/Linux, atau terminal Acode) dan memasang command `pyind` secara global.

### Manual

```bash
git clone https://github.com/ZanderoDev/Pyind.git
cd Pyind
python3 main.py jalankan contoh/halo_dunia.pyind
```

**Prasyarat:** Python 3.11+ — tidak ada dependency eksternal, murni standard library.

---

## Penggunaan

```bash
# Jalankan langsung
pyind jalankan file.pyind

# Shortcut — kata 'jalankan' opsional
pyind file.pyind

# Lihat kode Python hasil transpilasi
pyind file.pyind --tampilkan

# Ekspor ke file .py tanpa menjalankan
pyind ekspor file.pyind -o hasil.py

# REPL interaktif
pyind repl
```

---

## Referensi Kata Kunci

| Bahasa Indonesia | Python | Kategori |
|---|---|---|
| `fungsi` | `def` | Definisi |
| `kelas` | `class` | Definisi |
| `impor` | `import` | Modul |
| `dari` | `from` | Modul |
| `sebagai` / `menjadi` | `as` | Modul |
| `kembalikan` / `kembali` | `return` | Definisi |
| `jika` | `if` | Kontrol alur |
| `lainnya` | `else` | Kontrol alur |
| `jika_tidak` | `elif` | Kontrol alur |
| `untuk` | `for` | Kontrol alur |
| `selama` | `while` | Kontrol alur |
| `hentikan` | `break` | Kontrol alur |
| `lanjut` | `continue` | Kontrol alur |
| `lewati` / `lewat` | `pass` | Kontrol alur |
| `dalam` | `in` | Iterasi |
| `rentang` | `range` | Iterasi |
| `coba` | `try` | Exception |
| `kecuali` | `except` | Exception |
| `akhirnya` | `finally` | Exception |
| `naikkan` | `raise` | Exception |
| `pernyataan` | `assert` | Exception |
| `benar` | `True` | Literal |
| `salah` | `False` | Literal |
| `kosong` | `None` | Literal |
| `dan` | `and` | Operator logika |
| `atau` | `or` | Operator logika |
| `bukan` / `tidak` | `not` | Operator logika |
| `cetak` | `print` | Fungsi bawaan |
| `masukkan` | `input` | Fungsi bawaan |
| `panjang` | `len` | Fungsi bawaan |
| `tipe` | `type` | Fungsi bawaan |
| `bilangan` | `int` | Fungsi bawaan |
| `desimal` | `float` | Fungsi bawaan |
| `teks` | `str` | Fungsi bawaan |
| `daftar` | `list` | Fungsi bawaan |
| `kamus` | `dict` | Fungsi bawaan |
| `himpunan` | `set` | Fungsi bawaan |
| `hapus` | `del` | Fungsi bawaan |
| `bersama` | `with` | Context manager |
| `global` | `global` | Scope |
| `nonlokal` | `nonlocal` | Scope |
| `lambda` | `lambda` | Ekspresi |

> Catatan: `yield` sengaja tidak dipetakan karena terlalu ambigu sebagai nama variabel/metode dalam Bahasa Indonesia. Gunakan `yield` Python langsung bila diperlukan.

Library Python standar tetap bisa dipakai apa adanya lewat `impor` — lihat bagian [Keterbatasan](#keterbatasan-yang-diketahui).

---

## Contoh

Folder [`contoh/`](./contoh) berisi beberapa program contoh:
- `halo_dunia.pyind` — variabel, kondisional, operator aritmatika
- `kalkulator.pyind` — fungsi, rekursi, penanganan error
- `loop_dan_fungsi.pyind` — kelas, higher-order function, iterasi

```bash
pyind contoh/kalkulator.pyind
```

---

## Menjalankan Test

```bash
pip install pytest --break-system-packages
pytest tests/ -v
```

---

## Keterbatasan yang Diketahui

- **Dict/list multi-baris belum didukung.** Tulis dalam satu baris:
  ```
  data = {"a": 1, "b": 2}   # jalan
  data = {                  # belum didukung
      "a": 1,
  }
  ```
- **Nama identifier yang bentrok dengan kata kunci.** Memberi nama method/variabel milikmu sendiri persis sama dengan salah satu kata di tabel di atas (misal `hapus`, `coba`, `kelas`) akan ikut diterjemahkan secara tidak sengaja.

Kontribusi untuk mengatasi keterbatasan ini sangat diterima lewat _pull request_.

---

## Proyek Terkait

- **Pyind Syntax Highlighting** — extension VS Code untuk highlighting file `.pyind`
- **Pyind Acode Plugin** — plugin syntax highlighting untuk editor Acode (Android)

Lihat halaman [Releases](../../releases) untuk file `.vsix` dan `.zip` siap pakai.

---

## Lisensi

[MIT](./LICENSE)

# Referensi Bahasa Pyind

Dokumen ini menjelaskan aturan bahasa `.pyind` secara lengkap: leksikon,
bentuk literal, presedensi operator, fitur yang didukung, dan cara
diagnostik dilaporkan.

Pyind adalah bahasa yang diterjemahkan ke Python. Berkas `.pyind` dibaca
oleh lexer, diurai parser menjadi AST berbentuk `dict`, lalu dibangkitkan
transpiler menjadi source Python yang bisa langsung dijalankan.

---

## 1. Leksikon

### 1.1 Kata kunci khusus (*reserved*)

Nama berikut tidak boleh dipakai sebagai identifier — persis seperti
`def`/`if`/`class` di Python:

- **`fungsi`** — `def`
  - **`dan`** — `and`
- **`kelas`** — `class`
  - **`atau`** — `or`
- **`impor`** — `import`
  - **`bukan` / `tidak`** — `not`
- **`dari`** — `from`
  - **`hapus`** — `del`
- **`sebagai` / `menjadi`** — `as`
  - **`bersama`** — `with`
- **`kembalikan` / `kembali`** — `return`
  - **`global`** — `global`
- **`jika`** — `if`
  - **`nonlokal`** — `nonlocal`
- **`jika_tidak`** — `elif`
  - **`pernyataan`** — `assert`
- **`lainnya`** — `else`
  - **`lambda`** — `lambda`
- **`untuk`** — `for`
  - **`hasilkan`** — `yield`
- **`selama`** — `while`
  - **`hasilkan_dari`** — `yield from`
- **`hentikan`** — `break`
  - **`benar`** — `True`
- **`lanjut`** — `continue`
  - **`salah`** — `False`
- **`lewati`** — `pass`
  - **`kosong`** — `None`
- **`coba`** — `try`
  - **** — 
- **`kecuali`** — `except`
  - **** — 
- **`akhirnya`** — `finally`
  - **** — 
- **`naikkan`** — `raise`
  - **** — 

### 1.2 Kata kunci kontekstual (*soft keyword*)

Nama berikut **boleh** dipakai sebagai identifier. Barronya hanya aktif
selama nama itu belum diikat ke nilai lain di scope tersebut:

- **`cetak`** — `print`
- **`masukkan`** — `input`
- **`panjang`** — `len`
- **`tipe`** — `type`
- **`bilangan`** — `int`
- **`desimal`** — `float`
- **`teks` / `sebut`** — `str`
- **`daftar`** — `list`
- **`kamus`** — `dict`
- **`himpunan`** — `set`
- **`rentang`** — `range`
- **`urut`** — `sorted`
- **`jumlah`** — `sum`
- **`nilai_abs`** — `abs`
- **`bulat`** — `round`
- **`muter`** — `iter`

Cara kerjanya:

```pyind
cetak("halo")            # → print("halo")

cetak = fungsi_lain
cetak("halo")            # → cetak("halo")   alias sudah mati
```

Diawali kata `cetak` di dalam fungsi tidak mematikan `print` di luar:

```pyind
fungsi f():
    cetak = 1            # ikat lokal
    kembali cetak

cetak("halo")            # → print("halo")    tetap alias
```

Binding dipantau pada: penugasan, parameter, fungsi, kelas, import/alias,
target loop, target comprehension, `kecuali … sebagai`, dan
`bersama … sebagai`.

### 1.3 Nama (*identifier*)

Mengikuti aturan Python: karakter pertama harus *XID_Start* atau `_`,
karakter berikutnya *XID_Continue*. Artinya nama Unicode valid:

```pyind
nama_variable = 1
_privat = 2
var1 = 3
đā_variabel = 4      # sah
```

Nama setelah titik (atribut/method) boleh berupa literal:

```pyind
diri.kosong()         # sah — 'kosong' boleh jadi nama method
```

---

## 2. Literal

### 2.1 Angka

Bentuk yang dikenali sama persis dengan Python:

```pyind
42              # desimal
3.14            # pecahan
1_000_000       # underscore untuk keterbacaan
0b1010          # biner
0o17            # oktal
0x1f            # heksadesimal
0x_1f           # underscore boleh setelah prefiks
0xDEAD_BEEF     # huruf besar-kecil bebas
1.5e10          # eksponen
1e-3            # eksponen negatif
10.             # pecahan kosong
.5              # bulat kosong
2j              # imajiner / kompleks
```

**Bentuk sumber dipertahankan apa adanya** di kode hasil, jadi `0x_1f`
tetap `0x_1f`, bukan `31`.

Ditolak (menghasilkan `KesalahanLeksikal`):

```pyind
0123            # nol di depan
0x              # tanpa digit
1.2e            # eksponen tanpa digit
1__2            # underscore ganda
123abc          # huruf menempel angka
0b2             # digit di luar basis
```

### 2.2 String

```pyind
"kutip_ganda"
'kutip_tunggal'
"""blok
multi_baris"""
r"regex\tidak\s\scapes"
rb"data_bersama"
```

Prefiks yang sah: `b`, `r`, `f`, `t`, `u`, dan gabungannya `rb`, `br`,
`fr`, `rf`, `tr`, `rt`. Huruf besar kecil tidak berpengaruh.

Isi string **tidak pernah diterjemahkan**:

```pyind
pesan = "jika hujan, bawa payung"
# tetap: pesan = "jika hujan, bawa payung"
```

---

## 3. Presedensi operator

Mengikuti tabel resmi Python, dari yang paling mengikat ke yang paling longgar:

1. `()`, `[]`, `.` — grouping, subscript, atribut
2. `await x`
3. `**` — mengikat ke kanan
4. `+x`, `-x`, `~x`
5. `*`, `/`, `//`, `%`, `@`
6. `+`, `-`
7. `<<`, `>>`
8. `&`
9. `^`
10. `|`
11. `==`, `!=`, `<`, `>`, `<=`, `>=`, `in`, `not in`, `is`, `is not`
12. `not x`
13. `and`
14. `or`
15. `a jika b lainnya c` — ekspresi kondisi
16. `lambda`
17. `:=` — penugasan ekspresi

Operator dengan presedensi sama mengikat ke kiri, kecuali `**` yang ke kanan.

```pyind
2 ** 3 ** 2       # = 2 ** (3 ** 2) = 512
-2 ** 2           # = -(2 ** 2)  = -4
(-2) ** 2         # = 4
2 + 3 * 4         # = 14
```

Perbandingan bisa dirantai seperti Python:

```pyind
jika 0 < x < 10:
    cetak("dalam rentang")
```

---

## 4. Fitur yang didukung

- **Penugasan** — `x = 1`, `x += 1`, `x: int = 1`
- **Penugasan tuple / bintang** — `a, *b = data`
- **Penugasan ekspresi (walrus)** — `jika (n := panjang(a)) > 2:`
- **Kontrol alur** — `jika` / `jika_tidak` / `lainnya` / `selama` / `untuk` / `hentikan` / `lanjut`
- **Fungsi** — `fungsi`, parameter beranotasi, nilai bawaan, `*args`, `**kwargs`
- **Parameter posisional-only** — `fungsi f(a, /, b):`
- **Parameter keyword-only** — `fungsi f(a, *, b):`
- **Fungsi asinkron** — `async fungsi`, `await`, `async untuk`, `async bersama`
- **Dekorator** — `@deco` di atas fungsi/kelas
- **Penghasil** — `hasilkan`, `hasilkan_dari`
- **Kelas** — `kelas`, `induk`, `__init__`
- **Penanganan galat** — `coba` / `kecuali` / `lainnya` / `akhirnya`
- **Konteks** — `bersama … sebagai`
- **Impor** — `impor x`, `dari x impor y`, `sebagai`/`menjadi`
- **Komprehensi** — list, dict, set, generator
- **Lambda** — `lambda x: x + 1`
- **Slice** — penuh, kosong, bertingkat, langkah negatif
- **Operator walrus** — `:=`
- **Baris lanjutan** — `\` di akhir baris

### 4.1 Yang belum didukung

Hal berikut **belum** tersedia dan akan menghasilkan
`KesalahanSintaks`:

* Pernyataan `match` … `case` (kata kuncinya dikenali tapi badan blok
  belum diurai).
* Anotasi tipe pada parameter posisional-only setelah `/` digabung dengan
  `*` dalam satu baris yang sama tanpa koma — gunakan koma seperti biasa.
* Dekorator dengan ekspresi yang melibatkan `*args` pada level modul.
* Pattern matching struktural, positional-only pada `lambda`, dan
  parameter `type_params` (PEP 695).

---

## 5. Diagnostik

Semua kegagalan memakai hierarki `PyindError`:

```
PyindError
├── KesalahanLeksikal     E1001  tokenisasi gagal
├── KesalahanSintaks      E2001  sintaks tidak valid
├── KesalahanTranspilasi  E3001  simpul AST tak dikenal
└── KesalahanNama         E4001  nama belum didefinisikan
```

Pesan selalu berbahasa Indonesia dan disertai lokasi:

```
[Pyind] E2001 (baris 12, kolom 5): Dються ')', tetapi mendapat ':'.
   |     return a +
   |            ^
```

Cuplikan sumber dengan penunjuk `^` ditampilkan bila nama berkas tersedia
(CLI menyediakan ini otomatis). Kode galat stabil sehingga bisa dipakai
dalam pengujian otomatis.

---

## 6. CLI & REPL

```bash
python main.py jalankan berkas.pyind          # transpilasi + jalankan
python main.py jalankan berkas.pyind -t       # tampilkan kode Python dulu
python main.py ekspor berkas.pyind -o out.py # simpan hasil
python main.py repl                           # REPL interaktif
python main.py berkas.pyind                   # pintasan 'jalankan'
```

REPL memakai namespace persisten antar perintah. Ekspresi tunggal
dicetak hasilnya seperti Python REPL; blok multi-baris diselesaikan saat
baris kosong atau saat kembali ke level 0. Perintah keluar: `q`,
`Ctrl+C`, atau `Ctrl+D`.

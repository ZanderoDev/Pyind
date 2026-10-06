# Pyind Syntax Highlighting untuk Acode

Syntax highlighting untuk file `.pyind` — bahasa dengan sintaks Bahasa
Indonesia yang diterjemahkan ke Python.

## Fitur

- Kata kunci khusus: `fungsi` `kelas` `jika` `jika_tidak` `lainnya` `untuk` `selama` `hapus` `bersama` `naikkan` `pernyataan` `lambda` `hasilkan` `hasilkan_dari`
- Kata kunci kontekstual (boleh jadi identifier): `cetak` `panjang` `dalam` `rentang` `teks` `daftar` `kamus` `himpunan` `tipe` `bilangan` `desimal` `urut` `jumlah` `bulat`
- Literal: `benar` `salah` `kosong`
- Angka: desimal, eksponen, biner, oktal, heksadesimal, underscore, kompleks (`2j`)
- String: kutip tunggal/ganda, triple-quote lintas baris, prefiks `rb` `br` `fr` `rf` `u`
- Identifier Unicode
- Batas kata: `forum` dan `danau` tidak ikut ter-highlight

## Instalasi

1. Unduh `Pyind-Acode-Plugin-1.1.0.zip` dari
   [Releases Pyind](https://github.com/ZanderoDev/Pyind/releases)
2. Di Acode: **Plugin** → **Install plugin from file** → pilih `.zip`
3. Aktifkan **Pyind Syntax Highlighting**

## Catatan

Daftar kata kunci pada `main.js` dibuat dari `keywords.py`. Jalankan
`python extensi/alat/sinkronkan_leksikon.py` bila leksikon berubah.

## Lisensi

MIT

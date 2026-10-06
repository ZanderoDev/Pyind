# Pyind Syntax Highlighting untuk VS Code

Syntax highlighting untuk file `.pyind` — bahasa dengan sintaks Bahasa
Indonesia yang diterjemahkan ke Python.

## Fitur

- **Kata kunci khusus** — `fungsi` `kelas` `jika` `jika_tidak` `lainnya` `untuk` `selama` `hapus` `bersama` `naikkan` `pernyataan` `lambda` `global` `nonlokal`, plus padanan Python (`if` `def` `class` …)
- **Kata kunci kontekstual** — `cetak` `panjang` `dalam` `rentang` `teks` `daftar` `kamus` `himpunan` `tipe` `bilangan` `desimal` `urut` `jumlah` `bulat`. Tetap sah sebagai identifier, jadi warnanya hanya petunjuk
- **Penghasil** — `hasilkan` dan `hasilkan_dari` (padanan `yield` / `yield from`)
- **Literal** — `benar` `salah` `kosong`, juga `True` `False` `None`
- **Dekorator** — `@nama`
- **Angka** — desimal, eksponen, biner, oktal, heksadesimal, underscore, kompleks (`2j`)
- **String** — kutip tunggal/ganda, triple-quote, prefiks gabungan `rb` `br` `fr` `rf` `u`
- **Identifier Unicode** — `đā_variabel` dikenali
- **Batas kata** — `forum` dan `danau` tidak ikut ter-highlight

## Instalasi dari `.vsix`

1. Unduh `pyind-syntax-1.1.0.vsix` dari [Releases Pyind](https://github.com/ZanderoDev/Pyind/releases)
2. Di VS Code: `Ctrl+Shift+X` (`Cmd+Shift+X` di macOS) → ikon `···` → **Install from VSIX...**
3. Pilih file `.vsix`, restart bila diminta

## Dari folder (pengembangan)

```bash
git clone https://github.com/ZanderoDev/Pyind.git
cp -r Pyind/extensi/vscode ~/.vscode/extensions/pyind-syntax
```

## Membangun paket

```bash
npm install -g @vscode/vsce
cd extensi/vscode
vsce package
```

## Catatan

Leksikon pada `syntaxes/pyind.tmLanguage.json` dibangun dari `keywords.py`.
Jalankan `python extensi/alat/sinkronkan_leksikon.py` bila leksikon berubah.

## Lisensi

MIT

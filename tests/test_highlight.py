"""
test_highlight.py — Uji konsistensi grammar syntax highlighting.
Jalankan dengan: pytest tests/test_highlight.py -v

Berkas ini menjaga agar grammar TextMate (VS Code) dan daftar kata kunci
plugin Acode selalu mengikuti `keywords.py`. Kalau leksikon transpiler
berubah, test ini akan gagal sampai `extensi/alat/sinkronkan_leksikon.py`
dijalankan ulang.
"""

import sys, os, json, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from keywords import KATA_KUNCI_KHUSUS, KATA_KUNCI_KONTEKSTUAL

AKAR = os.path.join(os.path.dirname(__file__), "..")
TMLANG = os.path.join(AKAR, "extensi", "vscode", "syntaxes", "pyind.tmLanguage.json")
ACODE_JS = os.path.join(AKAR, "extensi", "acode", "main.js")
VSC_PKG = os.path.join(AKAR, "extensi", "vscode", "package.json")
ACODE_PKG = os.path.join(AKAR, "extensi", "acode", "plugin.json")

#: Nama yang sah sebagai identifier sehingga tidak boleh jadi keyword.
SOFT = {"dalam", "rentang", "lewat", "menjadi"}


@pytest.fixture(scope="module")
def repo():
    with open(TMLANG, encoding="utf-8") as f:
        return json.load(f)["repository"]


def kata_kunci_dalam(repo, scope: str) -> set:
    """Keluarkan himpunan kata kunci dari satu scope grammar."""
    cocok = re.search(r"\\b\(\?:(.*?)\)\\b", repo[scope]["match"])
    assert cocok, f"Tidak bisa membaca pola dari scope {scope!r}"
    return set(cocok.group(1).split("|"))


# ── Kelengkapan leksikon ────────────────────────────────────────────────────

class TestLeksikonTercakup:
    @pytest.mark.parametrize("kata", sorted(KATA_KUNCI_KHUSUS))
    def test_reserved_ada_di_grammar(self, repo, kata):
        tercakup = (
            kata in kata_kunci_dalam(repo, "keywords-control")
            or kata in kata_kunci_dalam(repo, "keywords-exception")
            or kata in kata_kunci_dalam(repo, "constants")
            or kata in kata_kunci_dalam(repo, "keywords-logical")
            or kata in kata_kunci_dalam(repo, "keywords-yield")
            or kata in kata_kunci_dalam(repo, "keywords-del")
        )
        assert tercakup, f"Kata kunci reserved {kata!r} belum ada di grammar"

    @pytest.mark.parametrize("kata", sorted(KATA_KUNCI_KONTEKSTUAL))
    def test_kontekstual_ada_di_grammar(self, repo, kata):
        assert kata in kata_kunci_dalam(repo, "builtins"), \
            f"Nama kontekstual {kata!r} belum ada di scope builtins"

    @pytest.mark.parametrize("kata", sorted(SOFT))
    def test_soft_keyword_tak_jadi_keyword(self, repo, kata):
        assert kata not in kata_kunci_dalam(repo, "keywords-control"), \
            f"{kata!r} boleh jadi identifier, jangan masuk scope keyword"


# ── Elemen bahasa yang baru ────────────────────────────────────────────────

class TestElemenBaru:
    def test_angka_punya_seluruh_basis(self, repo):
        pola = repo["numbers"]["match"]
        for bagian in ["0[xX]", "0[oO]", "0[bB]", "[eE]", "[jJ]"]:
            assert bagian in pola, f"Pola angka kurang {bagian}"

    def test_angka_underscore(self, repo):
        assert "_" in repo["numbers"]["match"]

    def test_operator_walrus(self, repo):
        assert ":=" in repo["operators"]["match"]

    def test_elipsis(self, repo):
        assert r"\.\.\." in repo["operators"]["match"]

    def test_operator_penugasan_gabungan(self, repo):
        pola = repo["operators"]["match"]
        for bagian in ["\\*\\*=", "//=", ">>=", "<<="]:
            assert bagian in pola, f"Operator gabungan {bagian} hilang"

    def test_prefiks_string_gabungan(self, repo):
        for pola in repo["strings"]["patterns"]:
            assert "bBfFrRtTuU" in pola["begin"], \
                "Prefiks string harus menerima rb/br/fr/rf dan huruf besar"

    def test_dekorator_ada(self, repo):
        assert "decorator" in repo

    def test_unicode_identifier(self, repo):
        assert r"\p{L}" in repo["function-definition"]["match"]
        assert r"\p{L}" in repo["class-definition"]["match"]

    def test_word_pattern_unicode(self):
        with open(os.path.join(AKAR, "extensi", "vscode", "language-configuration.json"),
                  encoding="utf-8") as f:
            assert r"\p{L}" in json.load(f)["wordPattern"]


# ── Metadata paket ──────────────────────────────────────────────────────────

class TestMetadata:
    def test_versi_vsix_1_1_0(self):
        with open(VSC_PKG, encoding="utf-8") as f:
            assert json.load(f)["version"] == "1.1.0"

    def test_versi_plugin_acode_1_1_0(self):
        with open(ACODE_PKG, encoding="utf-8") as f:
            assert json.load(f)["version"] == "1.1.0"

    def test_publisher_bukan_tempat_lain(self):
        with open(VSC_PKG, encoding="utf-8") as f:
            assert json.load(f)["publisher"] == "ZanderoDev"

    def test_repository_merunjuk_repo_yang_benar(self):
        with open(VSC_PKG, encoding="utf-8") as f:
            assert "ZanderoDev/Pyind" in json.load(f)["repository"]["url"]

    def test_id_plugin_acode_tetap(self):
        with open(ACODE_PKG, encoding="utf-8") as f:
            assert json.load(f)["id"] == "com.Zandero.pyind"

    def test_grammar_json_valid(self):
        with open(TMLANG, encoding="utf-8") as f:
            json.load(f)

    def test_language_configuration_valid(self):
        jalur = os.path.join(AKAR, "extensi", "vscode", "language-configuration.json")
        with open(jalur, encoding="utf-8") as f:
            json.load(f)

    def test_indentasi_tahu_jika_tidak(self):
        jalur = os.path.join(AKAR, "extensi", "vscode", "language-configuration.json")
        with open(jalur, encoding="utf-8") as f:
            pola = json.load(f)["indentationRules"]["decreaseIndentPattern"]
        for kata in ["lainnya", "jika_tidak", "kecuali", "akhirnya"]:
            assert kata in pola, f"Indentasi tidak mengenali {kata!r}"


# ── Konsistensi Acode ───────────────────────────────────────────────────────

class TestAcode:
    def test_semua_kata_kunci_ada(self):
        with open(ACODE_JS, encoding="utf-8") as f:
            js = f.read()
        for kata in sorted(KATA_KUNCI_KHUSUS):
            assert f'"{kata}"' in js, f"{kata!r} hilang dari main.js Acode"

    def test_kontekstual_ada(self):
        with open(ACODE_JS, encoding="utf-8") as f:
            js = f.read()
        for kata in sorted(KATA_KUNCI_KONTEKSTUAL):
            assert f'"{kata}"' in js, f"{kata!r} hilang dari main.js Acode"

    def test_versi_ditandai(self):
        with open(ACODE_JS, encoding="utf-8") as f:
            assert "v1.1.0" in f.read()

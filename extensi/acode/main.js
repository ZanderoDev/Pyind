// Syntax highlighting Pyind untuk Acode.
// Leksikon di bawah dibuat dari keywords.py Pyind v1.1.0 —
// jangan diubah manual tanpa menyinkronkan keywords.py.
const KONTROL     = new Set(["akhirnya", "and", "as", "assert", "async", "atau", "await", "benar", "bersama", "break", "bukan", "case", "class", "coba", "continue", "dan", "dari", "def", "del", "elif", "else", "except", "finally", "for", "from", "fungsi", "global", "hapus", "hasilkan", "hasilkan_dari", "hentikan", "if", "impor", "import", "in", "is", "jika", "jika_tidak", "kecuali", "kelas", "kembali", "kembalikan", "kosong", "lainnya", "lambda", "lanjut", "lewati", "match", "naikkan", "nonlocal", "nonlokal", "not", "or", "pass", "pernyataan", "raise", "return", "salah", "sebagai", "selama", "tidak", "try", "untuk", "while", "with", "yield"]);
const EXCEPTION   = new Set(["akhirnya", "coba", "kecuali", "naikkan", "pernyataan"]);
const LITERAL     = new Set(["False", "None", "True", "benar", "kosong", "salah"]);
const LOGIKA      = new Set(["atau", "bukan", "dan", "tidak"]);
const PENGHASIL   = new Set(["hasilkan", "hasilkan_dari", "yield"]);
const HAPUS       = new Set(["del", "hapus"]);
const BAWAAN      = new Set(["bilangan", "bulat", "cetak", "daftar", "desimal", "himpunan", "jumlah", "kamus", "masukkan", "muter", "nilai_abs", "panjang", "rentang", "sebut", "teks", "tipe", "urut"]);

function tokenPyind(e, state) {
  // String triple-quote boleh melintasi baris
  if (state.triple) {
    const re = state.triple === "'"
      ? /^[\s\S]*?'''/
      : /^[\s\S]*?"""/;
    if (e.match(re)) { state.triple = null; return 'pyindString'; }
    e.skipToEnd();
    return 'pyindString';
  }

  if (e.eatSpace()) return null;
  if (e.match(/^#.*/)) return 'pyindComment';

  // Awalan string: b r f t u dan gabungannya (rb, br, fr, rf)
  const m = e.match(/^([bBfFrRtTuU]{0,2})("""|'''|"|')/);
  if (m) {
    const kutip = m[2];
    if (kutip.length === 3) {
      const re = kutip[0] === "'"
        ? /^[\s\S]*?'''/
        : /^[\s\S]*?"""/;
      if (!e.match(re)) { state.triple = kutip[0]; e.skipToEnd(); }
      return 'pyindString';
    }
    const esc = kutip[0] === "'"
      ? /^'([^'\\\n]|\\.)*'/
      : /^"([^"\\\n]|\\.)*"/;
    if (!e.match(esc)) { e.next(); return 'pyindString'; }
    return 'pyindString';
  }

  // Angka: heksa, oktal, biner, desimal, eksponen, kompleks
  if (e.match(/^(?:0[xX][0-9a-fA-F_]+|0[oO][0-7_]+|0[bB][01_]+|\d[\d_]*\.?[\d_]*(?:[eE][+-]?\d+)?)[jJ]?\b/))
    return 'pyindNumber';

  const id = e.match(/^[_\p{L}][_\p{L}\p{N}]*/u);
  if (id) {
    const a = id[0];
    if (a === 'fungsi' || a === 'kelas') { state.prev = a; return 'pyindKeyword'; }
    if (state.prev === 'fungsi') { state.prev = null; return 'pyindFunctionName'; }
    if (state.prev === 'kelas')  { state.prev = null; return 'pyindClassName'; }
    state.prev = null;
    if (PENGHASIL.has(a) || HAPUS.has(a)) return 'pyindKeyword';
    if (KONTROL.has(a)) return 'pyindKeyword';
    if (EXCEPTION.has(a)) return 'pyindException';
    if (LITERAL.has(a)) return 'pyindConstant';
    if (LOGIKA.has(a)) return 'pyindOperator';
    if (BAWAAN.has(a)) return 'pyindBuiltin';
    return 'pyindVariable';
  }

  e.next();
  return null;
}

const HIGHLIGHT = {
  pyindKeyword:      'keyword',
  pyindException:    'keyword',
  pyindConstant:     'atom',
  pyindOperator:     'operatorKeyword',
  pyindBuiltin:      'standard(name)',
  pyindFunctionName: 'function(definition(variableName))',
  pyindClassName:    'className',
  pyindVariable:     'variableName',
  pyindString:       'string',
  pyindComment:      'lineComment',
  pyindNumber:       'number',
};

function aktifkan(acode, p) {
  const { LanguageSupport } = p;
  const { tags: t } = acode.require('@lezer/highlight');
  const { HighlightStyle, syntaxHighlighting } = p;

  const bahasa = p.StreamLanguage.define({
    name: 'pyind',
    startState: () => ({ triple: null, prev: null }),
    token: tokenPyind,
    tokenTable: HIGHLIGHT,
    languageData: {
      commentTokens: { line: '#' },
      closeBrackets: { brackets: ['(', '[', '{', "'", '"'] },
    },
  });

  const gaya = HighlightStyle.define([
    { tag: t.keyword,                     color: '#c678dd', fontWeight: 'bold' },
    { tag: t.atom,                        color: '#56b6c2' },
    { tag: t.operatorKeyword,              color: '#c678dd' },
    { tag: t.standard(t.name),             color: '#61afef' },
    { tag: t.function(t.definition(t.variableName)), color: '#61afef', fontWeight: 'bold' },
    { tag: t.className,                   color: '#e5c07b', fontWeight: 'bold' },
    { tag: t.variableName,                color: '#e06c75' },
    { tag: t.string,                      color: '#98c379' },
    { tag: t.lineComment,                 color: '#5c6370', fontStyle: 'italic' },
    { tag: t.number,                      color: '#d19a66' },
  ]);

  return new LanguageSupport(bahasa, [syntaxHighlighting(gaya)]);
}

const ID = 'com.Zandero.pyind';

acode.setPluginInit(ID, () => {
  const p = acode.require('@codemirror/language');
  acode.require('editorLanguages').register(
    'pyind', ['pyind'], 'Pyind',
    async () => aktifkan(acode, p)
  );
});

acode.setPluginUnmount(ID, () => {
  const e = acode.require('editorLanguages');
  if (e && e.unregister) e.unregister('pyind');
});

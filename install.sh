#!/usr/bin/env bash
# install.sh — installer Pyind untuk Termux, Acode Terminal, dan Linux
#
# Penggunaan:
#   bash install.sh
#   curl -fsSL https://raw.githubusercontent.com/ZanderoDev/Pyind/main/install.sh | bash

set -Eeuo pipefail

REPO_URL="https://github.com/ZanderoDev/Pyind.git"
INSTALL_DIR="${PYIND_DIR:-$HOME/.pyind}"
PYTHON_MIN_MAJOR=3
PYTHON_MIN_MINOR=9

# Mode:pasang (bawaan) atau copot
MODE="pasang"

# Kalau dijalankan dari dalam salinan repo, pakai salinan itu sebagai sumber
# supaya tidak perlu clone ulang. Contoh:
#   git clone https://github.com/ZanderoDev/Pyind.git && cd Pyind && bash install.sh
SUMBER_LOCAL=""
if [ -f "$PWD/main.py" ] && [ -f "$PWD/lexer.py" ] && [ -f "$PWD/parser.py" ]; then
    SUMBER_LOCAL="$(cd "$PWD" && pwd)"
fi

# ── Warna ─────────────────────────────────────────────────────────────────────
if [ -t 1 ]; then
    RED='\033[31m'; GREEN='\033[32m'; YELLOW='\033[33m'; RESET='\033[0m'
else
    RED=''; GREEN=''; YELLOW=''; RESET=''
fi

info()  { printf "%b\n" "${GREEN}==>${RESET} $1"; }
warn()  { printf "%b\n" "${YELLOW}⚠ ${RESET} $1"; }
fail()  { printf "%b\n" "${RED}✗ $1${RESET}" >&2; exit 1; }
have()  { command -v "$1" >/dev/null 2>&1; }

trap 'fail "Gagal di baris $LINENO: $BASH_COMMAND"' ERR

# ── Deteksi environment ───────────────────────────────────────────────────────
is_termux()  { [ -n "${PREFIX:-}" ] && have pkg; }
is_android() { [ -n "${ANDROID_DATA:-}" ]; }   # Android (termasuk Acode)
is_root()    { [ "$(id -u)" -eq 0 ]; }

# ── Instalasi dependensi ──────────────────────────────────────────────────────
_apt()    { have apt    && { is_root && apt    install -y "$@" || sudo apt    install -y "$@"; }; }
_apk()    { have apk    && { is_root && apk    add        "$@" || sudo apk    add        "$@"; }; }
_dnf()    { have dnf    && { is_root && dnf    install -y "$@" || sudo dnf    install -y "$@"; }; }
_pacman() { have pacman && { is_root && pacman -Sy --noconfirm "$@" || sudo pacman -Sy --noconfirm "$@"; }; }

install_pkg() {
    # $1 = nama paket (generik); $2 = nama paket pacman (opsional)
    local pkg="$1" pkg_pacman="${2:-$1}"
    if   have apt;    then _apt    "$pkg"
    elif have apk;    then _apk    "$pkg"
    elif have dnf;    then _dnf    "$pkg"
    elif have pacman; then _pacman "$pkg_pacman"
    else warn "Tidak bisa menginstal '$pkg' — package manager tidak dikenal."; fi
}

install_termux() {
    info "Terdeteksi: Termux"
    pkg update -y -o Dpkg::Options::="--force-confdef"
    pkg install -y python git
}

install_acode() {
    info "Terdeteksi: Acode Terminal (Android)"
    # Acode Terminal biasanya sudah punya Python/git bawaan atau via plugin.
    # Tidak mencoba install via package manager karena sudo tidak tersedia.
    if ! have python3 && ! have python; then
        fail "Python tidak ditemukan. Install Python lewat plugin Acode atau Termux terlebih dahulu."
    fi
    if ! have git; then
        warn "Git tidak ditemukan. Mencoba metode download langsung..."
    fi
}

install_linux() {
    info "Terdeteksi: Linux"
    if ! have python3; then
        info "Python3 belum ada, menginstal..."
        install_pkg python3 python
    fi
    if ! have git; then
        info "Git belum ada, menginstal..."
        install_pkg git git
    fi
}

# ── Cek versi Python ──────────────────────────────────────────────────────────
check_python() {
    local py_bin=""
    have python3 && py_bin="python3" || { have python && py_bin="python"; }
    [ -n "$py_bin" ] || fail "Python tidak ditemukan setelah instalasi."

    local py_ver major minor
    py_ver=$("$py_bin" -c "import sys; print(sys.version_info.major, sys.version_info.minor)")
    major=$(echo "$py_ver" | cut -d' ' -f1)
    minor=$(echo "$py_ver" | cut -d' ' -f2)

    if [ "$major" -lt "$PYTHON_MIN_MAJOR" ] || \
       { [ "$major" -eq "$PYTHON_MIN_MAJOR" ] && [ "$minor" -lt "$PYTHON_MIN_MINOR" ]; }; then
        fail "Python $major.$minor terlalu lama. Pyind butuh Python ${PYTHON_MIN_MAJOR}.${PYTHON_MIN_MINOR}+."
    fi

    info "Python: $("$py_bin" --version)"
    PYTHON_BIN="$py_bin"
}

check_git() {
    have git || fail "Git tidak ditemukan."
    info "Git: $(git --version)"
}


# ── Copot / uninstall ─────────────────────────────────────────────────────────
hapus_path() {
    local cfg changed=0
    local configs=("$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile" "$HOME/.bash_profile")
    for cfg in "${configs[@]}"; do
        [ -f "$cfg" ] || continue
        grep -q 'local/bin.*\$PATH' "$cfg" 2>/dev/null || continue
        if have awk; then
            local tmp="$cfg.pyind.tmp"
            awk 'index($0, "local/bin") && index($0, "PATH") { next } { print }' \
                "$cfg" > "$tmp" && mv "$tmp" "$cfg"
        fi
        changed=1
    done
    [ "$changed" -eq 1 ] && info "Baris PATH Pyind dibersihkan." || true
}

copot() {
    echo
    printf "%b\n" "${RED}Pyind Uninstaller${RESET}"
    echo "────────────────────────────────"

    if [ -n "$INSTALL_DIR" ] && [ -e "$INSTALL_DIR" ]; then
        rm -rf "$INSTALL_DIR"
        info "Dihapus: $INSTALL_DIR"
    else
        info "Tidak ada instalasi di $INSTALL_DIR"
    fi

    for d in /usr/local/bin "$HOME/.local/bin" "${PREFIX:-}/bin"; do
        [ -n "$d" ] && [ "$d" != "/bin" ] || continue
        if [ -L "$d/pyind" ]; then
            rm -f "$d/pyind"
            info "Symlink dihapus: $d/pyind"
        fi
    done

    hapus_path

    echo
    printf "Pyind sudah dicopot. Baris PATH di shell mungkin masih memuat PATH lama;\n"
    printf "buka terminal baru atau jalankan: hash -r\n"
}

# ── Pilih direktori bin ───────────────────────────────────────────────────────
choose_bin_dir() {
    if is_termux && [ -n "${PREFIX:-}" ] && [ -d "$PREFIX/bin" ] && [ -w "$PREFIX/bin" ]; then
        BIN_DIR="$PREFIX/bin"
    elif [ -w "/usr/local/bin" ]; then
        BIN_DIR="/usr/local/bin"
    else
        BIN_DIR="$HOME/.local/bin"
        mkdir -p "$BIN_DIR"
    fi
    info "Command global akan dipasang di: $BIN_DIR/pyind"
}

# ── Clone atau update repo ────────────────────────────────────────────────────
clone_repo() {
    if [ -n "$SUMBER_LOCAL" ]; then
        if [ "$SUMBER_LOCAL" = "$INSTALL_DIR" ]; then
            info "Meny memakai salinan lokal: $INSTALL_DIR"
        else
            info "Menyalin dari repo lokal: $SUMBER_LOCAL"
            rm -rf "$INSTALL_DIR"
            mkdir -p "$INSTALL_DIR"
            # rsync bila ada (lebih cepat), kalau tidak pakai cp
            if have rsync; then
                rsync -a --exclude '.git' "$SUMBER_LOCAL/" "$INSTALL_DIR/"
            else
                cp -R "$SUMBER_LOCAL/." "$INSTALL_DIR/"
            fi
        fi
        return
    fi

    if [ -d "$INSTALL_DIR/.git" ]; then
        info "Memperbarui Pyind yang sudah ada..."
        git -C "$INSTALL_DIR" pull --ff-only origin main \
            || { warn "Pull gagal. Menghapus dan clone ulang..."; rm -rf "$INSTALL_DIR"; _clone_fresh; }
    else
        rm -rf "$INSTALL_DIR"
        _clone_fresh
    fi
}

_clone_fresh() {
    info "Meng-clone Pyind..."
    git clone --depth 1 --branch main "$REPO_URL" "$INSTALL_DIR"
}

# ── Cari entry point ──────────────────────────────────────────────────────────
find_entry() {
    MAIN_PY=""
    for f in \
        "$INSTALL_DIR/main.py" \
        "$INSTALL_DIR/pyind/main.py" \
        "$INSTALL_DIR/pyind.py" \
        "$INSTALL_DIR/__main__.py"
    do
        [ -f "$f" ] && { MAIN_PY="$f"; break; }
    done
    [ -n "$MAIN_PY" ] || fail "Entry point Python tidak ditemukan di $INSTALL_DIR."
    info "Entry point: $MAIN_PY"
}

# ── Tambah shebang & chmod ────────────────────────────────────────────────────
fix_shebang() {
    if ! head -1 "$MAIN_PY" | grep -q '^#!'; then
        # Pilih python yang tersedia
        local shebang="#!/usr/bin/env ${PYTHON_BIN:-python3}"
        sed -i "1i $shebang" "$MAIN_PY"
    fi
    chmod +x "$MAIN_PY"
}

# ── Buat symlink global ───────────────────────────────────────────────────────
link_global() {
    ln -sf "$MAIN_PY" "$BIN_DIR/pyind"
}

# ── Pastikan BIN_DIR ada di PATH ──────────────────────────────────────────────
ensure_path() {
    # Jangan hanya mempercayai PATH sesi ini: shell yang baru bisa belum
    # memuat BIN_DIR. Yang penting baris PATH di file konfigurasi shell.

    local export_line="export PATH=\"${BIN_DIR}:\$PATH\""

    # Untuk bash, tulis ke .bashrc DAN .profile: shell login membaca
    # .bash_profile lalu .profile, bukan .bashrc, sehingga .bashrc saja
    # tidak selalu terbaca.
    local cfg
    case "${SHELL:-}" in
        */zsh)  cfg="$HOME/.zshrc" ;;
        */bash) cfg="$HOME/.bashrc" ;;
        *)      cfg="$HOME/.profile" ;;
    esac

    touch "$cfg"
    local profile="$HOME/.profile"
    touch "$profile"

    # Bersihkan baris PATH lama dari installer sebelumnya, lalu tulis satu kali
    local f
    for f in "$cfg" "$profile"; do
        if have awk; then
            local tmp="$f.pyind.tmp"
            awk 'index($0, "export PATH=") && index($0, "local/bin") && index($0, "PATH") { next } { print }' \
                "$f" > "$tmp" && mv "$tmp" "$f"
        fi
        grep -qxF "$export_line" "$f" || echo "$export_line" >> "$f"
    done
    info "PATH diperbarui di: $cfg"
}

# ── Verifikasi ────────────────────────────────────────────────────────────────
verify() {
    hash -r 2>/dev/null || true
    echo
    if command -v pyind >/dev/null 2>&1; then
        info "✓ Instalasi berhasil!"
        printf "\nCoba sekarang:\n"
        printf "  pyind                          # masuk REPL interaktif\n"
        printf "  pyind --versi                  # cek versi\n"
        printf "  pyind jalankan file.pyind      # jalankan file\n"
        printf "  pyind ekspor  file.pyind       # ekspor ke .py\n"
    else
        warn "Symlink sudah dibuat, tapi PATH belum memuat $BIN_DIR"
        printf "\nJalankan perintah ini lalu buka terminal baru:\n"
        printf "  export PATH=\"%s:\$PATH\"\n" "$BIN_DIR"
    fi
}

# ── Main ──────────────────────────────────────────────────────────────────────
main() {
    echo
    printf "%b\n" "${GREEN}Pyind Installer${RESET}"
    echo "────────────────────────────────"

    if [ "$MODE" = "copot" ]; then
        copot
        return
    fi

    if is_termux; then
        install_termux
    elif is_android; then
        install_acode
    else
        install_linux
    fi

    check_python
    have git && check_git || { is_android || fail "Git diperlukan untuk instalasi."; }
    choose_bin_dir
    clone_repo
    find_entry
    fix_shebang
    link_global
    ensure_path
    verify
}

while [ $# -gt 0 ]; do
    case "$1" in
        copot|uninstall|hapus|--copot) MODE="copot" ;;
        pasang|install|"") ;;
        -h|--help)
            printf "Penggunaan: bash install.sh [pasang|copot]\n"
            printf "  pasang   (bawaan) — pasang atau perbarui Pyind\n"
            printf "  copot    — hapus Pyind, symlink, dan baris PATH\n"
            exit 0 ;;
        *) printf "Argumen tidak dikenal: %s\n" "$1" >&2; exit 1 ;;
    esac
    shift
done

main

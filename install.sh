#!/usr/bin/env bash
# install.sh — installer Pyind untuk Termux, Acode Terminal, dan Linux
#
# Penggunaan:
#   bash install.sh
#   curl -fsSL https://raw.githubusercontent.com/ZanderoDev/Pyind/main/install.sh | bash

set -Eeuo pipefail

REPO_URL="https://github.com/ZanderoDev/Pyind.git"
INSTALL_DIR="$HOME/.pyind"
PYTHON_MIN_MAJOR=3
PYTHON_MIN_MINOR=7

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
    case ":${PATH}:" in
        *":${BIN_DIR}:"*) return ;;  # sudah ada di PATH
    esac

    local export_line="export PATH=\"${BIN_DIR}:\$PATH\""

    # Daftar shell config yang mungkin ada
    local configs=(
        "$HOME/.bashrc"
        "$HOME/.bash_profile"
        "$HOME/.zshrc"
        "$HOME/.profile"
    )

    local added=0
    for cfg in "${configs[@]}"; do
        if [ -f "$cfg" ]; then
            grep -qxF "$export_line" "$cfg" \
                || { echo "$export_line" >> "$cfg"; added=1; }
        fi
    done

    # Jika tidak ada config yang cocok, buat .profile
    if [ "$added" -eq 0 ]; then
        echo "$export_line" >> "$HOME/.profile"
    fi
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

main "$@"

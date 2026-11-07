#!/usr/bin/env bash
# Bootstrap: install Homebrew (macOS) and Ansible, then the Ansible collections.
# Run once on a new machine, then run the playbook (see README).
set -euo pipefail
cd "$(dirname "$0")"

case "$(uname -s)" in
  Darwin)
    # Command Line Tools give git, make, and the compilers.
    if ! xcode-select -p >/dev/null 2>&1; then
      echo "Installing the Xcode Command Line Tools. Finish the dialog, then run this script again."
      xcode-select --install
      exit 1
    fi
    if [ -x /opt/homebrew/bin/brew ]; then
      BREW=/opt/homebrew/bin/brew
    elif [ -x /usr/local/bin/brew ]; then
      BREW=/usr/local/bin/brew
    else
      /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
      BREW=$([ "$(uname -m)" = arm64 ] && echo /opt/homebrew/bin/brew || echo /usr/local/bin/brew)
    fi
    eval "$("$BREW" shellenv)"
    brew install ansible
    ;;
  Linux)
    sudo apt-get update
    sudo apt-get install -y pipx git curl
    pipx install --include-deps ansible
    pipx ensurepath
    export PATH="$HOME/.local/bin:$PATH"
    ;;
  *)
    echo "Unsupported OS: $(uname -s)" >&2
    exit 1
    ;;
esac

ansible-galaxy collection install -r requirements.yml
echo
echo "Done. Next step:"
echo "  ./run.sh"

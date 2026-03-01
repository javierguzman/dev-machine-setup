# dev-machine-setup

Ansible playbook to bootstrap a development machine from scratch. Supports **macOS** (Homebrew) and **Linux** (Debian/Ubuntu via apt).

## What it installs

| Category | Tools |
|----------|-------|
| **Shell** | zsh, Oh-My-Zsh, Powerlevel10k, zsh-autosuggestions |
| **Terminal** | Alacritty, iTerm2 (macOS only), FiraCode Nerd Font |
| **Editor** | Neovim, VS Code |
| **Window manager** | Yabai + skhd (macOS only) |
| **Dev tools** | tmux, lazygit, fzf, ripgrep, stow, yt-dlp, tldr |
| **Languages** | Node.js (via nvm), Python 3.11 (via pyenv) |
| **Browsers** | Firefox, Brave, Google Chrome |
| **Productivity** | Obsidian, Thunderbird, draw.io, JetBrains Toolbox |
| **Communication** | WhatsApp, Signal, Discord |
| **VPN & Security** | ProtonVPN, Proton Mail Bridge, Wireguard, YubiKey tools |
| **Cloud** | Synology Drive |
| **Media** | Spotify, VLC |
| **Design** | GIMP, Darktable, Figma, Affinity Photo/Designer (macOS only) |
| **Dotfiles** | Clones and stows [javierguzman/.dotfiles](https://github.com/javierguzman/.dotfiles) |

## Requirements

- **macOS**: Nothing — the playbook installs Homebrew if missing
- **Linux**: `curl`, `python3`, `pip3`

Install Ansible first:
```bash
python3 -m pip install ansible
ansible-galaxy collection install community.general
```

## Usage

```bash
git clone https://github.com/javierguzman/dev-machine-setup.git
cd dev-machine-setup
ansible-playbook init.yml -K
```

`-K` prompts for your sudo password (needed for system-level installs).

### Run specific categories only

```bash
# Only install dev tools
ansible-playbook init.yml -K --tags "git"

# Skip design tools
ansible-playbook init.yml -K --skip-tags "design"
```

## Structure

```
dev-machine-setup/
├── init.yml                  # Main playbook entry point
├── install.sh                # Bootstrap: installs Ansible
└── tasks/
    ├── yubikey.yml           # YubiKey, GPG, SSH config
    ├── git-setup.yml         # Git global config + GPG signing
    ├── core-setup.yml        # Core CLI tools
    ├── zsh.yml               # Shell setup
    ├── prodev.yml            # Neovim, tmux, lazygit, yabai, skhd
    ├── node.yml              # Node.js via nvm
    ├── python.yml            # Python via pyenv
    ├── dev-tools.yml         # VSCode, Chrome, Insomnia
    ├── office.yml            # Browsers, Obsidian, Thunderbird, JetBrains, Proton, Synology
    ├── social.yml            # WhatsApp, Signal, Discord
    ├── design.yml            # GIMP, Darktable, Figma, draw.io
    ├── multimedia.yml        # Spotify, VLC
    └── dotfiles.yml          # Clone and stow dotfiles
```

---

## YubiKey Setup

The playbook installs all required tools and writes config files automatically. However, the GPG key and SSH key live on the physical YubiKey and **cannot be automated** — they require manual steps.

### What the playbook does automatically

- Installs `gpg-suite` / `gnupg2`, `scdaemon`, `pcscd`
- Installs `yubico-piv-tool` and `ykman`
- Writes `~/.gnupg/gpg-agent.conf`, `gpg.conf`, `dirmngr.conf`
- Writes `~/.ssh/config` with the correct PKCS#11 library path
- Configures git to sign commits with GPG
- On Linux: enables and starts `pcscd` service

### Manual steps after running the playbook

Do these steps with your YubiKey inserted.

#### 1. Verify the YubiKey is detected
```bash
gpg --card-status
```
You should see your card info and key stubs. If not, check that `pcscd` is running (Linux: `sudo systemctl start pcscd`).

#### 2. Import your public GPG key
Fetch from the keyserver:
```bash
gpg --recv-keys 34D3A6FB8181BEA7
```
Or import from a file if you have a backup:
```bash
gpg --import your-public-key.asc
```

#### 3. Trust the key
```bash
gpg --edit-key 34D3A6FB8181BEA7
```
Inside the GPG prompt:
```
gpg> trust
Your decision? 5  (ultimate trust — this is your own key)
gpg> quit
```

#### 4. Verify GPG commit signing works
```bash
echo "test" | gpg --clearsign
```
Your YubiKey should blink and ask for your PIN.

#### 5. Verify SSH key is available
```bash
ssh-add -L
```
You should see your public key prefixed with `cardno:`.

#### 6. Test SSH connection to GitHub
```bash
ssh -T git@github.com
```
Expected output: `Hi javierguzman! You've successfully authenticated...`

### Linux-specific notes

- The PKCS#11 library path is `/usr/lib/x86_64-linux-gnu/libykcs11.so`
- If `ssh-add -L` shows nothing, start the agent manually:
  ```bash
  ssh-agent -s -P '/usr/lib/x86_64-linux-gnu/libykcs11.so'
  ssh-add -s /usr/lib/x86_64-linux-gnu/libykcs11.so
  ```
- If GPG can't see the card, restart pcscd:
  ```bash
  sudo systemctl restart pcscd
  gpg-connect-agent reloadagent /bye
  ```

### macOS-specific notes

- GPG Suite provides `pinentry-mac` which shows a native macOS dialog for the PIN
- The SSH agent is configured in `~/.zshrc` and loads automatically on shell start via `libykcs11.dylib`
- If the card is not detected after re-inserting the YubiKey:
  ```bash
  gpg-connect-agent reloadagent /bye
  ```

# dev-machine-setup

Ansible playbook to bootstrap a development machine from scratch. Supports **macOS** (Homebrew) and **Linux** (Debian/Ubuntu via apt).

## Profiles

The playbook has three profiles. Each profile includes the profile before it.

| Profile | Use | Installs |
|---------|-----|----------|
| `minimal` | Any machine, locked-down work laptops | Developer tools only: shell, editors, terminals, yabai/skhd, languages, container runtime, Git, YubiKey, dotfiles |
| `work` | Work laptop | `minimal` + browsers, Slack, Obsidian, Figma, draw.io, LM Studio, desktop utilities |
| `personal` | Personal laptop | `work` + messaging, media, yt-dlp, VPN, Proton apps, Synology Drive, photo editing, own security tools |

The names in `code` are the names for `extra_apps` and `skip_apps` (see below).

| Category (tag) | `minimal` | `work` adds | `personal` adds |
|----------------|-----------|-------------|-----------------|
| `core` | `ripgrep`, `fzf`, `stow`, `tlrc` (tldr), `jq`, `mas` (App Store CLI) | | |
| `zsh` | zsh, Oh-My-Zsh, Powerlevel10k, zsh-autosuggestions | | |
| `terminal` | `neovim`, `tree-sitter-cli` (macOS), `tmux`, `lazygit`, `ghostty` (macOS and Linux), `iterm2` (macOS), `font-fira-code-nerd-font` | | |
| `window-manager` | `yabai`, `skhd` (macOS), `hyprland` (Linux, Ubuntu 26.04+) | | |
| `node`, `python` | Node.js LTS (nvm), Python 3.14 (`pyenv`) | | |
| `dev-tools` | `visual-studio-code`, `jetbrains-toolbox`, `yaak`, `beyond-compare`, `pgadmin4`, container runtime, `kubectl`, `helm`, Claude Code | `lm-studio` | `android-studio` |
| `yubikey`, `git` | `gnupg`, `pinentry-mac`, `ykman`, `yubico-piv-tool`, `yubico-authenticator`, Git config + signing, push over SSH | | `~/.ssh/config` (vaulted) |
| `browsers` | | `google-chrome`, `firefox`, `brave-browser` | |
| `productivity` | | `obsidian`, `onlyoffice`, `stirling-pdf`, `reverso` | `thunderbird` |
| `communication` | | `slack`, `zoom` | `discord`, `whatsapp`, `signal`, `telegram` |
| `design` | | `figma`, `drawio` | `gimp`, `affinity`, `darktable` (Linux) |
| `utilities` | | `alfred`, `keka`, `maccy`, `linearmouse`, `hiddenbar`, `bazecor`, `shottr`, `logi-options+` | `bitwarden`, `lulu`, `oversight`, `knockknock`, `cold-turkey-blocker`, `the-unarchiver`, `macdroid`, `home-assistant`, `autofirma`, `p-touch-editor` (App Store) |
| `vpn-cloud` | | | `protonvpn`, `proton-mail`, `proton-pass`, `proton-mail-bridge`, `proton-drive`, `synology-drive`, `syncthing-app`, `google-drive`, `wireguard` (App Store), `wireguard-tools` |
| `multimedia` | | | `spotify`, `vlc`, `ffmpeg`, `yt-dlp`, `obs`, `capcut`, `transmission`, `focusrite-control-2`, `davinci-resolve` (App Store) |
| `own-apps` | | | `pomodoro` (built from the home GitLab server, macOS) |
| `dotfiles` | Clones and stows [javierguzman/.dotfiles](https://github.com/javierguzman/.dotfiles) | | |

The `work` utilities on macOS:

| App | Purpose |
|-----|---------|
| Alfred | App launcher, clipboard search, and workflows (a Spotlight replacement) |
| Keka | Archive tool (zip, 7z, rar, and more) |
| Maccy | Clipboard history in the menu bar |
| LinearMouse | Separate settings for mouse and trackpad (scroll direction, acceleration) |
| Hidden Bar | Hides menu bar icons |
| Bazecor | Configures Dygma keyboards (layers, macros, lights). Also on Linux (AppImage) |
| Shottr | Screenshots with annotation and measurement |
| Logi Options+ | Settings for Logitech mice and keyboards |

To move an app to a different profile, change the `profile:` field of its line in `tasks/<category>.yml`.

### Extra apps and skipped apps

A profile is a starting point. Two settings change the app list:

- `extra_apps`: install these apps in any profile.
- `skip_apps`: never install these apps. For `yabai` and `skhd`, the playbook also does not stow their dotfiles.

Use the names from the category table. On the command line, give a comma-separated list:

```bash
# Developer tools, plus Obsidian and Slack
ansible-playbook init.yml -e profile=minimal -e extra_apps=obsidian,slack

# Work apps, without LM Studio
ansible-playbook init.yml -e profile=work -e skip_apps=lm-studio
```

In `local.yml`, use a YAML list:

```yaml
profile: minimal
extra_apps: [obsidian, slack]
```

### Container runtime (macOS)

Set `container_runtime` to choose the Docker replacement. All options run Docker images and support `docker compose`. On Linux, the playbook always installs Docker Engine from apt.

| Value | App | License | Notes |
|-------|-----|---------|-------|
| `docker-desktop` (default for `personal`) | Docker Desktop | Paid at companies with more than 250 employees or more than $10M yearly revenue | The original |
| `orbstack` | OrbStack | Free for personal use, paid for commercial use | Fastest and lightest, also runs Linux VMs |
| `colima` (default for `minimal` and `work`) | Colima + Docker CLI | Free, open source | Command line only. Starts at login with `brew services` |
| `rancher` | Rancher Desktop | Free, open source | GUI, built-in Kubernetes |
| `podman` | Podman + Podman Desktop | Free, open source | GUI. Uses `podman` instead of a Docker daemon (Docker-compatible) |
| `none` | | | No container runtime |

The defaults: `colima` for `minimal` and `work` (no license needed at work), `docker-desktop` for `personal`. Use `rancher` when you want a GUI.

All profiles also get the Kubernetes clients `kubectl` and `helm`. For a local cluster, start Colima with Kubernetes (k3s): `colima start --kubernetes`. kubectl then uses the `colima` context.

When a different runtime already exists, the playbook keeps it: it installs nothing and changes no Docker config. Example: this laptop has Docker Desktop, and `container_runtime: colima` then does nothing. The summary lists the runtime that the playbook found. Set `container_runtime_keep_existing: false` to install the selected runtime anyway.

CRI-O is not an option here: it is a Kubernetes runtime for Linux servers, with no `docker` CLI, no `docker compose`, and no image builds.

### Git

The identity (`git_user_name`, `git_user_email`) comes from `local.yml`: `./run.sh` asks for it, with your current Git config as the default. An empty value leaves `user.name` / `user.email` unchanged. The other settings: GPG signing with the YubiKey key, `pull.rebase=true`, and Beyond Compare as diff and merge tool (only when the app is installed). The playbook also adds `**/.claude/settings.local.json` to `~/.config/git/ignore`.

GitHub uses SSH where it makes sense:

- **Push** always uses SSH: `url.git@github.com:.pushInsteadOf https://github.com/`. A remote with an `https://github.com/` URL pushes to `git@github.com:`.
- **Fetch** stays on HTTPS. Clones then work before the YubiKey setup and when the YubiKey is not plugged in. For a private repository, clone with the `git@github.com:` URL.
- **The dotfiles clone** uses SSH when GitHub accepts the SSH key, else HTTPS.

For a work laptop, set `git_user_email` (and maybe `git_gpg_sign: false`) in `local.yml`.

### Terminal look

Ghostty is the terminal on macOS and Linux (snap on Linux). Ghostty and iTerm2 get the same look as the Alacritty config: FiraCode Nerd Font at 14 pt with ligatures, Tokyo Night Dark, 8 px padding, 95 % opacity, no title bar, a blinking block cursor, and left Option as Alt (with the same word-jump keys).

- The values are in `vars/terminal.yml`. Templates in `templates/ghostty/` and `templates/iterm2/` use them.
- Ghostty (both systems): `~/.config/ghostty/config.ghostty` and `~/.config/ghostty/themes/`. The macOS-only settings (no title bar, left Option as Alt) apply only on macOS. Put your own changes in `~/.config/ghostty/config.local`. The playbook does not touch that file.
- iTerm2: a Dynamic Profile named "Alacritty", set as the default profile. Quit iTerm2 before the run, because iTerm2 writes its settings back when it quits.
- To follow the macOS light/dark appearance, set `terminal_theme: "light:tokyo-night-light,dark:tokyo-night-dark"`.

### Window manager

The same keyboard window management on both systems:

- **macOS:** yabai + skhd. All windows float (`manage=off`). `shift+alt+t` tiles one window.
- **Linux:** Hyprland, with the same layout (dwindle = BSP), the same "all windows float" rule, and the same keys. The config is the dotfiles package `hypr`. Hyprland is a separate session: choose it on the login screen, and GNOME stays available. The playbook also installs Waybar (bar), Wofi (launcher), Mako (notifications), and the Hyprland portal and polkit agent. Ubuntu 26.04 or later only: older releases and Debian have no Hyprland, or a version that cannot read the config.

The skhd `alt` (Option) key is `SUPER` on Linux. On a PC keyboard, Super is in the same place as Option on a Mac keyboard. Terminals do not use Super, so Linux needs no terminal exceptions. On macOS, skhd lets `alt+h/j/k/l` pass through in Alacritty, Ghostty, and iTerm2, for tmux and Neovim.

| Action | macOS (skhd) | Linux (Hyprland) |
|--------|--------------|------------------|
| Focus left/down/up/right | `alt` + `h/j/k/l` | `SUPER` + `h/j/k/l` |
| Next/previous window | `ctrl+alt` + `right/left` | `CTRL+SUPER` + `right/left` |
| Swap with neighbor | `shift+alt` + `h/j/k/l` | `SHIFT+SUPER` + `h/j/k/l` |
| Move in the layout (warp) | `ctrl+alt` + `h/j/k/l` | `CTRL+SUPER` + `h/j/k/l` |
| Float/tile toggle | `shift+alt+t` | `SHIFT+SUPER+t` |
| Maximize toggle | `shift+alt+m` | `SHIFT+SUPER+m` |
| Left/right half | `shift+ctrl+alt` + `left/right` | `CTRL+SHIFT+SUPER` + `left/right` |
| Rotate / mirror / balance | `shift+alt` + `r` / `y`,`x` / `e` | `SHIFT+SUPER` + `r` (split) / `y`,`x` (swap split) / `e` |
| Resize | `shift+ctrl` + `hjkl` (grow), `+alt` (shrink) | `CTRL+SHIFT+SUPER` + `h/k` (shrink), `l/j` (grow) |
| Focus display left/right | `alt` + `s/g` | `SUPER` + `s/g` |
| Window to display left/right | `shift+alt` + `s/g` | `SHIFT+SUPER` + `s/g` |
| Window to space prev/next/1-7 | `shift+alt` + `p/n/1-7` | `SHIFT+SUPER` + `p/n/1-7` |
| Reload | `ctrl+alt+r` (restart yabai) | `CTRL+SUPER+r` |
| Go to space 1-7 | macOS shortcuts | `SUPER` + `1-7` |
| Terminal / launcher / close | macOS apps | `SUPER+Return` / `SUPER+Space` / `SHIFT+SUPER+q` |

Resize differs on purpose: on Linux, `Ctrl+Shift+J/K` are app shortcuts (browser dev tools), so the resize keys add `SUPER`.

### Mac App Store apps

Some apps exist only in the Mac App Store: WireGuard, DaVinci Resolve (the free version), and P-touch Editor. The playbook installs them with `mas get <id>`. An entry has the key `mas: <App Store ID>` and the app name in `app:`.

- Sign in to the App Store app before the run. `mas` cannot sign in for you.
- `mas get` installs free apps, and apps that your Apple account already has. It cannot buy a paid app.
- `mas` needs sudo. The playbook checks for the app first, so an existing app needs no password.
- With Touch ID for purchases turned on, macOS can ask you to confirm each new app.

Home Assistant and The Unarchiver also exist as Homebrew casks, so the playbook uses the casks.

### Own apps

`pomodoro` (tag `own-apps`, profile `personal`, macOS only) is built from source:

1. The playbook checks that your Git server (`own_git_host` in `local.yml`, asked by `./run.sh`) is reachable on port 443 (home network or VPN). Without `own_git_host`, the summary lists Pomodoro under `install_manually`. If the server is not reachable, the summary says so and the run continues.
2. It clones the repository to `~/Projects/pomodoro`, with SSH first (YubiKey) and HTTPS second (saved login). An existing folder stays as it is (no pull).
3. It runs `npm ci` and `npm run build`, then copies `Pomodoro.app` to `/Applications`.

When `Pomodoro.app` already exists, the playbook skips all steps. To update the app, delete it and run `--tags own-apps` again.

### macOS settings

The playbook copies your macOS settings to every Mac: keyboard (Spanish - ISO layout, key repeat, shortcuts such as Spotlight off and `Ctrl+1-5` for desktops), Dock, hot corners, Finder, trackpad, Spaces, Stage Manager, the menu bar clock, and screenshots. It needs no Apple ID, so a work laptop gets the same settings without your personal account. Settings that the company manages (MDM profiles) win over these values.

- `vars/macos_settings.yml` lists the keys. `files/macos-settings.json` holds the values.
- After you change a setting on your main Mac, export the values again and commit the file:
  ```bash
  ansible-playbook export.yml --tags macos
  ```
- The export writes only keys that exist on the Mac (a missing key means the macOS default). Paths in your home folder become `~`, so the file works for a different user name.
- The playbook changes only the listed keys, and keeps all other keys. After a change, it restarts Dock, Finder, or the menu bar, and it reloads the keyboard shortcuts.
- To add a setting: run `defaults read <domain>` before and after you change it in System Settings, add the key to `vars/macos_settings.yml`, and export.
- To skip this step: `-e macos_settings_apply=false`, or `--skip-tags macos-settings`.

iCloud does not replace this. iCloud syncs data (Keychain, Safari, Desktop and Documents), but not most System Settings.

### Obsidian settings

The playbook copies your Obsidian vault settings (the `.obsidian` folder) to new vaults, **without note content**: editor settings, appearance, enabled core plugins, community plugins (same versions), themes, hotkeys, and the settings of plugins without personal data.

- Export from your main vault (`obsidian_source_vault` in `vars/obsidian.yml`), then commit `files/obsidian/`:
  ```bash
  ansible-playbook export.yml --tags obsidian
  ```
- Set the vaults for a machine in `local.yml`, for example a new work vault:
  ```yaml
  obsidian_vaults: ["~/Documents/Work-Notes"]
  ```
  The playbook creates `<vault>/.obsidian` and downloads the plugins and themes from GitHub (like Obsidian does). Then open the folder as a vault in Obsidian. A vault that already has a `.obsidian` folder stays untouched, so your synced personal vault never changes.

**This repository is public**, so the export removes everything personal:

| Removed | Why |
|---------|-----|
| Plugin code, themes, icon packs | Downloaded again from GitHub (no 120 MB of files in Git) |
| LiveSync, LanguageTool, Vault Changelog, Settings Search (whole plugins) | LiveSync and LanguageTool need the home network; Vault Changelog is optional; Obsidian has settings search built in since 1.13 |
| `data.json` of Copilot, Local REST API | Secrets: API keys, certificate |
| `data.json` of QuickAdd, Templater, Projects, Iconize, Excalidraw | Personal structure: macros, template and folder paths, project names, folder icons |
| Hotkeys for QuickAdd macros and template files | They point to personal macros and files |
| Folder paths in `app.json`, search and color groups in `graph.json` | Personal folders and search text |
| `workspace*.json`, sync conflict copies | Open files and window layout |

The plugins in the `data.json` rows still get installed, with default settings. A final scan stops the export (and writes nothing) when a file still has a secret-like key with a value, your home path, or a top-level folder name of your vault. To keep the settings of more plugins out, add them to `plugin_data_exclude`. To not install a plugin at all, add it to `plugins_exclude`.

On the personal laptop, the vault gets its settings from LiveSync (home network), so `obsidian_vaults` stays empty there.

### Manual installs

At the end of a run, the summary has an `install_manually` list (macOS):

- Apps with no Homebrew cask and no App Store entry that are missing on the Mac, for the active profiles. They are in `manual_apps` in `vars/main.yml`, each with a hint where to get the app.
- App Store apps that `mas` could not install, for example when nobody signed in to the App Store (a work laptop without your Apple ID).

### Apps that already exist

- A cask app that already exists (for example, IT installed it, or you installed it by hand) is **skipped**. Homebrew does not manage it. The summary at the end lists these apps.
- A failed install does **not** stop the run. The summary at the end lists each failure.
- Formulae, apt, and snap packages that already exist do not change.

## Requirements

- **macOS**: Nothing. `install.sh` installs the Command Line Tools, Homebrew, and Ansible.
- **Linux** (Debian/Ubuntu): `sudo` rights. `install.sh` installs pipx and Ansible.

## Usage

```bash
git clone https://github.com/javierguzman/dev-machine-setup.git
cd dev-machine-setup
./install.sh     # once: Homebrew, Ansible, collections
./run.sh         # asks for the settings, writes local.yml, runs the playbook
```

`./run.sh` asks for the settings of this machine and writes them to `local.yml`:

| Question | Setting |
|----------|---------|
| Profile | `profile` (`minimal`, `work`, `personal`) |
| Git name and email (default: your current Git config) | `git_user_name`, `git_user_email` |
| Sign commits with the YubiKey GPG key | `git_gpg_sign` |
| Container runtime (macOS) | `container_runtime` |
| Admin rights (no = apps into `~/Applications`) | `cask_appdir` |
| Extra apps, apps to skip | `extra_apps`, `skip_apps` |
| Your own Git server for Pomodoro (personal) | `own_git_host` |
| Deploy the encrypted `~/.ssh/config` (personal) | `ssh_config_deploy` |
| Obsidian vaults to set up | `obsidian_vaults` |

Git ignores `local.yml`, so your email and your home server names never reach this public repository. Then `run.sh` shows the file and asks before it starts Ansible.

- The next `./run.sh` uses the existing `local.yml`. `./run.sh --edit` asks again, with the current values as defaults. In each answer, Enter keeps the default and `-` clears the value.
- Other arguments go to `ansible-playbook`: `./run.sh --check` shows what would change, and `./run.sh --tags git` runs one category.
- With `ssh_config_deploy: true`, `run.sh` adds `--ask-vault-pass`.

The playbook asks for your sudo password. Do **not** add `-K`: Homebrew needs the password as a variable for casks with a `.pkg` installer. Press Enter without a password to skip the tasks that need sudo.

A direct run without `run.sh` also works: `ansible-playbook init.yml -e profile=work`.

### Per-machine settings

`local.yml` can hold every setting from `vars/main.yml`, `vars/terminal.yml`, `vars/macos_settings.yml`, and `vars/obsidian.yml`, not only the `run.sh` questions. Edit it by hand for the others (see `local.yml.example`). Command-line `-e` values override `local.yml`.

### Run specific categories only

```bash
# Only the Git config
ansible-playbook init.yml -e profile=minimal --tags git

# Only the terminals and their config
ansible-playbook init.yml -e profile=minimal --tags terminal

# Everything except design tools
ansible-playbook init.yml -e profile=personal --skip-tags design

# Show what would change, without changes
ansible-playbook init.yml -e profile=work --check --diff
```

## Structure

```
dev-machine-setup/
├── init.yml                  # Main playbook
├── export.yml                # Exports macOS and Obsidian settings into files/
├── install.sh                # Bootstrap: Homebrew, Ansible, collections
├── run.sh                    # Asks for the settings, writes local.yml, runs init.yml
├── ansible.cfg
├── requirements.yml          # Ansible collections
├── local.yml.example         # Per-machine settings template
├── vars/
│   ├── main.yml              # Profiles, extra/skip apps, container runtime, settings
│   ├── terminal.yml          # Font, colors, and window values for Ghostty and iTerm2
│   ├── macos_settings.yml    # macOS settings keys to export and apply
│   └── obsidian.yml          # Obsidian export rules and vaults to set up
├── templates/
│   ├── ghostty/              # config.ghostty and theme files
│   └── iterm2/               # Dynamic Profile JSON
├── scripts/
│   ├── cask_status.py        # Finds casks that already exist outside Homebrew
│   ├── stow_backup.py        # Moves files that block stow to ~/.dotfiles-backup
│   ├── macos_settings.py     # Exports and applies macOS settings
│   └── obsidian_config.py    # Exports and applies Obsidian vault settings
└── tasks/
    ├── lib/packages.yml      # Shared installer: profile filter, extra/skip apps, report
    ├── yubikey.yml           # GnuPG, YubiKey tools, GPG and SSH config
    ├── git.yml               # Git global config + GPG signing
    ├── core.yml              # Core CLI tools
    ├── zsh.yml               # Shell setup
    ├── terminal.yml          # Neovim, tmux, lazygit, terminals + their config, fonts
    ├── node.yml              # Node.js via nvm
    ├── python.yml            # Python via pyenv
    ├── dev-tools.yml         # VS Code, JetBrains, Yaak, container runtime, LM Studio, Claude Code
    ├── window-manager.yml    # yabai, skhd
    ├── browsers.yml          # Chrome, Firefox, Brave
    ├── productivity.yml      # Obsidian, Thunderbird
    ├── communication.yml     # Slack, Discord, WhatsApp, Signal
    ├── design.yml            # Figma, draw.io, GIMP, Affinity, darktable
    ├── utilities.yml         # Desktop utilities, Bitwarden, Objective-See tools
    ├── vpn-cloud.yml         # Proton apps, Synology Drive, WireGuard
    ├── multimedia.yml        # Spotify, VLC, ffmpeg, yt-dlp, OBS, DaVinci Resolve
    ├── own-apps.yml          # Pomodoro (home GitLab)
    ├── macos-settings.yml    # Applies files/macos-settings.json
    └── dotfiles.yml          # Clone and stow dotfiles
```

### Apps that Homebrew no longer provides

| App | Status | What to do |
|-----|--------|------------|
| Alacritty | Cask disabled: the releases are not notarized by Apple | Ghostty replaces it on macOS and Linux, with the same look. An existing Alacritty install keeps working, and its dotfiles still get stowed |
| darktable | Cask disabled (fails the Gatekeeper check) | Download from darktable.org |
| Affinity Photo 2 / Designer 2 | Discontinued | The `affinity` cask installs the new app |
| VMware Fusion | Cask removed | Download from the Broadcom support portal |
| WireGuard (GUI) | Mac App Store only (the WireGuard project publishes no other macOS app) | The playbook installs it with `mas`, plus `wireguard-tools`. Homebrew alternative with a GUI: `passepartout` (open source, imports WireGuard `.conf` files) |
| GPG Suite | No release since 2023 | Homebrew `gnupg` + `pinentry-mac` replace it |

---

## YubiKey Setup

The playbook installs all required tools and writes config files automatically. However, the GPG key and SSH key live on the physical YubiKey and **cannot be automated** — they require manual steps.

### What the playbook does automatically

- Installs `gnupg` + `pinentry-mac` (macOS) / `gnupg`, `scdaemon`, `pcscd` (Linux)
- Installs `yubico-piv-tool`, `ykman`, and `ykcs11` (Linux)
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

- The PKCS#11 library path is `/usr/lib/x86_64-linux-gnu/libykcs11.so` (`aarch64-linux-gnu` on ARM)
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

- `pinentry-mac` shows a native macOS dialog for the PIN. The playbook sets it in `gpg-agent.conf`
- The SSH agent is configured in `~/.zshrc` and loads automatically on shell start via `libykcs11.dylib`
- If the card is not detected after re-inserting the YubiKey:
  ```bash
  gpg-connect-agent reloadagent /bye
  ```

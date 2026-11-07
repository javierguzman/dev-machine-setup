#!/usr/bin/env bash
# Ask for the per-machine settings, write local.yml, and run the playbook.
# local.yml is in .gitignore: personal values (Git email, home server) stay on
# this machine and never reach the public repository.
#
#   ./run.sh              use local.yml if it exists (or ask), then run
#   ./run.sh --edit       ask again, with the current values as defaults
#   ./run.sh --check      Ansible shows what would change, and changes nothing
#   ./run.sh --tags git   any other argument goes to ansible-playbook
#
# Works with the bash 3.2 that macOS ships.
set -euo pipefail
cd "$(dirname "$0")"

LOCAL=local.yml
EDIT=false
PASS=()
for arg in "$@"; do
  if [ "$arg" = "--edit" ]; then EDIT=true; else PASS+=("$arg"); fi
done

OS=$(uname -s)

# ─── Helpers ──────────────────────────────────────────────────────────────────

# ask VAR "question" "default": read one answer.
# Enter keeps the default; "-" clears the value.
ask() {
  local __ask_in="" __ask_prompt="$2: "
  [ -n "${3-}" ] && __ask_prompt="$2 [$3]: "
  # End of input (Ctrl+D, closed pipe): stop instead of asking forever.
  if ! read -r -p "$__ask_prompt" __ask_in && [ -z "$__ask_in" ]; then
    echo; echo "Input ended. Stopped; nothing was written." >&2; exit 1
  fi
  __ask_in=${__ask_in:-${3-}}
  [ "$__ask_in" = "-" ] && __ask_in=""
  printf -v "$1" '%s' "$__ask_in"
}

# ask_choice VAR "question" "default" option...: repeat until the answer is an option.
ask_choice() {
  local __var=$1 __q=$2 __def=$3 __choice_in __o
  shift 3
  while true; do
    ask __choice_in "$__q ($*)" "$__def"
    for __o in "$@"; do
      if [ "$__choice_in" = "$__o" ]; then printf -v "$__var" '%s' "$__choice_in"; return; fi
    done
    echo "  Choose one of: $*"
  done
}

# ask_yn VAR "question" "true|false": store true or false.
ask_yn() {
  local __yn_in __def=y
  [ "$3" = "false" ] && __def=n
  while true; do
    ask __yn_in "$2 (y/n)" "$__def"
    case "$__yn_in" in
      y|Y|yes) printf -v "$1" true; return ;;
      n|N|no) printf -v "$1" false; return ;;
      *) echo "  Answer y or n." ;;
    esac
  done
}

# local_value KEY: read a value that this script wrote to local.yml.
# A list comes back as "a, b". A missing key gives an empty string.
local_value() {
  [ -f "$LOCAL" ] || return 0
  local line
  line=$(sed -n "s/^$1: //p" "$LOCAL" | head -1)
  case "$line" in
    \[*) line=${line#[}; line=${line%]}
         line=$(printf '%s' "$line" | sed -e "s/^'//" -e "s/'\$//" -e "s/', '/, /g" -e "s/''/'/g") ;;
    \'*) line=${line#\'}; line=${line%\'}; line=$(printf '%s' "$line" | sed "s/''/'/g") ;;
  esac
  printf '%s' "$line"
}

# yaml_str VALUE: a single-quoted YAML string.
yaml_str() { printf "'%s'" "$(printf '%s' "$1" | sed "s/'/''/g")"; }

# yaml_list "a, b": a YAML flow list of strings.
yaml_list() {
  local out="" item IFS=,
  for item in $1; do
    item="${item#"${item%%[![:space:]]*}"}"
    item="${item%"${item##*[![:space:]]}"}"
    [ -n "$item" ] && out="$out${out:+, }$(yaml_str "$item")"
  done
  printf '[%s]' "$out"
}

# ─── Questions ────────────────────────────────────────────────────────────────

write_local() {
  echo "Settings for this machine. Enter keeps the value in [brackets]; \"-\" clears it."
  echo

  local profile git_name git_email gpg runtime extra skip appdir admin host ssh_deploy vaults default

  ask_choice profile "Profile" "$(local_value profile)" minimal work personal

  # Defaults: local.yml first, then the current global Git config.
  default=$(local_value git_user_name)
  [ -n "$default" ] || default=$(git config --global user.name 2>/dev/null || true)
  ask git_name "Git user.name (empty = do not change)" "$default"
  default=$(local_value git_user_email)
  [ -n "$default" ] || default=$(git config --global user.email 2>/dev/null || true)
  ask git_email "Git user.email (empty = do not change)" "$default"

  default=$(local_value git_gpg_sign)
  if [ -z "$default" ]; then
    default=false; [ "$(git config --global commit.gpgsign 2>/dev/null || true)" = "true" ] && default=true
    [ "$profile" = "personal" ] && default=true
  fi
  ask_yn gpg "Sign Git commits with the YubiKey GPG key" "$default"

  runtime=""
  if [ "$OS" = "Darwin" ]; then
    default=$(local_value container_runtime)
    if [ -z "$default" ]; then default=colima; [ "$profile" = "personal" ] && default=docker-desktop; fi
    ask_choice runtime "Container runtime" "$default" colima docker-desktop orbstack rancher podman none

    default=true
    [ -n "$(local_value cask_appdir)" ] && default=false
    id -Gn | tr ' ' '\n' | grep -qx admin || default=false
    ask_yn admin "Admin rights on this Mac (no = install apps into ~/Applications)" "$default"
    appdir=""; [ "$admin" = "false" ] && appdir="~/Applications"
  fi

  ask extra "Extra apps outside the profile, comma-separated (for example obsidian,slack)" "$(local_value extra_apps)"
  ask skip "Apps to skip, comma-separated" "$(local_value skip_apps)"

  host=""; ssh_deploy=false
  if [ "$profile" = "personal" ]; then
    ask host "Your own Git server for Pomodoro (empty = skip)" "$(local_value own_git_host)"
    default=$(local_value ssh_config_deploy); [ -n "$default" ] || default=true
    ask_yn ssh_deploy "Deploy the encrypted ~/.ssh/config (needs the vault password)" "$default"
  fi

  vaults=""
  if [ "$profile" != "minimal" ] || printf '%s' "$extra" | grep -q obsidian; then
    echo "  Obsidian: a vault with LiveSync gets its settings from LiveSync. Leave empty then."
    ask vaults "Obsidian vaults to set up, comma-separated (for example ~/Documents/Work-Notes)" "$(local_value obsidian_vaults)"
  fi

  {
    echo "# Written by run.sh on $(date '+%Y-%m-%d %H:%M'). Git ignores this file."
    echo "# Run ./run.sh --edit to change it, or edit it by hand (see local.yml.example)."
    echo "profile: $profile"
    echo "git_user_name: $(yaml_str "$git_name")"
    echo "git_user_email: $(yaml_str "$git_email")"
    echo "git_gpg_sign: $gpg"
    [ -n "$runtime" ] && echo "container_runtime: $runtime"
    [ "$OS" = "Darwin" ] && echo "cask_appdir: $(yaml_str "$appdir")"
    echo "extra_apps: $(yaml_list "$extra")"
    echo "skip_apps: $(yaml_list "$skip")"
    echo "own_git_host: $(yaml_str "$host")"
    echo "ssh_config_deploy: $ssh_deploy"
    echo "obsidian_vaults: $(yaml_list "$vaults")"
  } > "$LOCAL.tmp"
  mv "$LOCAL.tmp" "$LOCAL"
  chmod 600 "$LOCAL"
}

# ─── Main ─────────────────────────────────────────────────────────────────────

if [ "$EDIT" = "true" ] || [ ! -f "$LOCAL" ]; then
  write_local
fi

while true; do
  echo
  echo "── $LOCAL ──"
  cat "$LOCAL"
  echo
  go=""
  read -r -p "Run the playbook with these settings? (y = run, e = edit, n = stop) [y]: " go || go=n
  case "${go:-y}" in
    y|Y) break ;;
    e|E) echo; write_local ;;
    *) echo "Stopped. $LOCAL is saved."; exit 0 ;;
  esac
done

# Homebrew is not in PATH right after its install.
for b in /opt/homebrew/bin/brew /usr/local/bin/brew; do
  [ -x "$b" ] && eval "$("$b" shellenv)" && break
done
export PATH="$HOME/.local/bin:$PATH"

if ! command -v ansible-playbook >/dev/null 2>&1; then
  echo "Ansible is missing. Running ./install.sh first."
  ./install.sh
fi
ansible-galaxy collection list community.general >/dev/null 2>&1 \
  || ansible-galaxy collection install -r requirements.yml

VAULT=()
grep -q '^ssh_config_deploy: true' "$LOCAL" && VAULT=(--ask-vault-pass)

exec ansible-playbook init.yml ${VAULT[@]+"${VAULT[@]}"} ${PASS[@]+"${PASS[@]}"}

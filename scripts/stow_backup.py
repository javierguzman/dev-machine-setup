#!/usr/bin/env python3
"""Move files that block `stow` into a backup folder.

stow refuses to replace a real file (for example a ~/.zshrc that an installer
created). For each file in the given stow packages, this script checks the
matching path in the target folder. If that path exists and does not already
resolve into the dotfiles folder, the script moves it to the backup folder.

Usage:
  stow_backup.py --dotfiles ~/.dotfiles --target ~ --backup ~/.dotfiles-backup/2026-01-01T10-00 PKG ...

Prints one "MOVED <path>" line per moved file.
"""

import argparse
import os
import shutil
import sys

IGNORE = {".DS_Store", ".git", ".gitignore"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dotfiles", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--backup", required=True)
    parser.add_argument("packages", nargs="+")
    args = parser.parse_args()

    dotfiles = os.path.realpath(os.path.expanduser(args.dotfiles))
    target = os.path.expanduser(args.target)
    backup = os.path.expanduser(args.backup)

    for pkg in args.packages:
        pkg_dir = os.path.join(dotfiles, pkg)
        if not os.path.isdir(pkg_dir):
            print(f"MISSING package {pkg}")
            continue
        for root, dirs, files in os.walk(pkg_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE]
            for name in files:
                if name in IGNORE:
                    continue
                rel = os.path.relpath(os.path.join(root, name), pkg_dir)
                dest = os.path.join(target, rel)
                if not os.path.lexists(dest):
                    continue
                if os.path.realpath(dest).startswith(dotfiles + os.sep):
                    continue  # already a stow link (or inside a folded stow link)
                saved = os.path.join(backup, rel)
                os.makedirs(os.path.dirname(saved), exist_ok=True)
                shutil.move(dest, saved)
                print(f"MOVED {dest} -> {saved}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

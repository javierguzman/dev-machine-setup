#!/usr/bin/env python3
"""Report the install status of Homebrew casks.

For each cask, print one of these statuses (as JSON on stdout):

  brew         Homebrew already manages the cask.
  external     The software exists, but Homebrew did not install it
               (for example, IT installed it, or you dragged it to /Applications).
               `brew install --cask` fails in this case, so the playbook skips it.
  absent       The software is not present. The playbook installs it.
  unavailable  Homebrew does not know the cask, or the cask is disabled.

Usage:
  cask_status.py --brew /opt/homebrew/bin/brew [--appdir DIR] CASK[=App Name.app] ...

The optional "=App Name.app" suffix names the app bundle to look for, for casks
whose metadata does not list one (for example casks with an installer script).
"""

import argparse
import fnmatch
import json
import os
import subprocess
import sys


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def cask_info(brew, tokens):
    """Return {token: info-dict}. Unknown casks are missing from the result."""
    env_cmd = [brew, "info", "--cask", "--json=v2"]
    res = run(env_cmd + tokens)
    if res.returncode == 0:
        data = json.loads(res.stdout, strict=False)
        return {c["token"]: c for c in data.get("casks", [])}
    # One unknown cask makes the whole call fail. Retry one at a time.
    out = {}
    for token in tokens:
        res = run(env_cmd + [token])
        if res.returncode == 0:
            for c in json.loads(res.stdout, strict=False).get("casks", []):
                out[token] = c
    return out


def app_dirs(extra_appdir):
    dirs = ["/Applications", os.path.expanduser("~/Applications")]
    if extra_appdir:
        dirs.insert(0, os.path.expanduser(extra_appdir))
    return dirs


def as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def find_existing(info, app_override, extra_appdir, installed_pkgs):
    """Return a path or pkg id that proves the cask software exists, or None."""
    candidates = []
    if app_override:
        candidates += [os.path.join(d, app_override) for d in app_dirs(extra_appdir)]

    pkg_ids = []
    for artifact in info.get("artifacts", []):
        for key, value in artifact.items():
            if key == "app":
                for entry in as_list(value):
                    name = entry.get("target") if isinstance(entry, dict) else entry
                    if not name:
                        continue
                    name = os.path.basename(name)
                    candidates += [os.path.join(d, name) for d in app_dirs(extra_appdir)]
                if artifact.get("target"):
                    candidates.append(artifact["target"])
            elif key == "font" and artifact.get("target"):
                candidates.append(artifact["target"])
            elif key == "uninstall":
                for step in as_list(value):
                    if not isinstance(step, dict):
                        continue
                    pkg_ids += as_list(step.get("pkgutil"))
                    for path in as_list(step.get("delete")):
                        if isinstance(path, str) and path.endswith(".app"):
                            candidates.append(os.path.expanduser(path))

    for path in candidates:
        if os.path.exists(path):
            return path

    for pattern in pkg_ids:
        if not isinstance(pattern, str):
            continue
        for pkg in installed_pkgs:
            if fnmatch.fnmatch(pkg, pattern):
                return f"pkg {pkg}"
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--brew", required=True)
    parser.add_argument("--appdir", default="")
    parser.add_argument("casks", nargs="+")
    args = parser.parse_args()

    overrides = {}
    for raw in args.casks:
        token, _, app = raw.partition("=")
        overrides[token] = app or None
    tokens = list(overrides)

    listed = run([args.brew, "list", "--cask", "-1"])
    brew_casks = set(listed.stdout.split()) if listed.returncode == 0 else set()

    pkgs = run(["/usr/sbin/pkgutil", "--pkgs"])
    installed_pkgs = pkgs.stdout.split() if pkgs.returncode == 0 else []

    infos = cask_info(args.brew, tokens)

    result = {}
    for token in tokens:
        if token in brew_casks:
            result[token] = {"status": "brew", "detail": "managed by Homebrew"}
            continue
        info = infos.get(token)
        if info is None:
            result[token] = {"status": "unavailable", "detail": "Homebrew does not know this cask"}
            continue
        if info.get("disabled"):
            reason = info.get("disable_reason") or "no reason given"
            result[token] = {"status": "unavailable", "detail": f"cask is disabled ({reason})"}
            continue
        found = find_existing(info, overrides[token], args.appdir, installed_pkgs)
        if found:
            result[token] = {"status": "external", "detail": f"already present: {found}"}
        else:
            result[token] = {"status": "absent", "detail": ""}

    json.dump(result, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Export or apply selected macOS settings (`defaults` domains).

export: read the listed keys from this Mac and write them to a JSON file.
        Only keys that exist get exported; a missing key means "macOS default".
apply:  write the keys from the JSON file to this Mac. Other keys in each
        domain stay. A dict value (for example AppleSymbolicHotKeys) merges
        into the existing dict, entry by entry.

Paths under the home folder become "~" in the file, so the file works for a
different user name. Values that JSON cannot hold (dates, binary data) are
skipped with a message.

Usage:
  macos_settings.py export --keys-json '{"com.apple.dock": ["autohide"]}' --out FILE
  macos_settings.py apply --file FILE [--check]

`apply` prints one "CHANGED <domain> <key>" line per changed key, and one
"RESTART <process>" line per process that must restart to load the change.
"""

import argparse
import json
import os
import plistlib
import subprocess
import sys

HOME = os.path.expanduser("~")

# Processes that cache these domains. They restart after a change.
RESTART = {
    "com.apple.dock": "Dock",
    "com.apple.spaces": "Dock",
    "com.apple.WindowManager": "Dock",
    "com.apple.finder": "Finder",
    "com.apple.menuextra.clock": "SystemUIServer",
    "com.apple.screencapture": "SystemUIServer",
}


def read_domain(domain):
    res = subprocess.run(["defaults", "export", domain, "-"], capture_output=True)
    if res.returncode != 0 or not res.stdout:
        return {}
    return plistlib.loads(res.stdout)


def write_domain(domain, data):
    subprocess.run(["defaults", "import", domain, "-"], input=plistlib.dumps(data), check=True)


class Unsupported(Exception):
    pass


def to_portable(value):
    if isinstance(value, bool) or isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        if value.startswith("file://" + HOME):
            return "file://~" + value[len("file://" + HOME):]
        if value == HOME or value.startswith(HOME + "/"):
            return "~" + value[len(HOME):]
        return value
    if isinstance(value, list):
        return [to_portable(v) for v in value]
    if isinstance(value, dict):
        return {k: to_portable(v) for k, v in value.items()}
    raise Unsupported(type(value).__name__)


def from_portable(value):
    if isinstance(value, str):
        if value.startswith("file://~"):
            return "file://" + HOME + value[len("file://~"):]
        if value == "~" or value.startswith("~/"):
            return HOME + value[1:]
        return value
    if isinstance(value, list):
        return [from_portable(v) for v in value]
    if isinstance(value, dict):
        return {k: from_portable(v) for k, v in value.items()}
    return value


def export(keys, out):
    result = {}
    for domain, names in keys.items():
        data = read_domain(domain)
        for key in names:
            if key not in data:
                continue
            try:
                result.setdefault(domain, {})[key] = to_portable(data[key])
            except Unsupported as exc:
                print(f"SKIP {domain} {key}: {exc} values are not supported", file=sys.stderr)
    with open(out, "w") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
        fh.write("\n")
    count = sum(len(v) for v in result.values())
    print(f"EXPORTED {count} keys from {len(result)} domains to {out}")


def apply(path, check):
    with open(path) as fh:
        wanted = json.load(fh)
    restart = set()
    for domain, values in wanted.items():
        current = read_domain(domain)
        changed = []
        for key, value in values.items():
            value = from_portable(value)
            if isinstance(value, dict) and isinstance(current.get(key), dict):
                value = {**current[key], **value}
            if current.get(key) != value:
                current[key] = value
                changed.append(key)
        for key in changed:
            print(f"CHANGED {domain} {key}")
        if changed:
            if domain in RESTART:
                restart.add(RESTART[domain])
            if domain == "com.apple.symbolichotkeys":
                restart.add("activateSettings")
            if not check:
                write_domain(domain, current)
    for name in sorted(restart):
        print(f"RESTART {name}")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_exp = sub.add_parser("export")
    p_exp.add_argument("--keys-json", required=True)
    p_exp.add_argument("--out", required=True)
    p_app = sub.add_parser("apply")
    p_app.add_argument("--file", required=True)
    p_app.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.cmd == "export":
        export(json.loads(args.keys_json), args.out)
    else:
        apply(args.file, args.check)
    return 0


if __name__ == "__main__":
    sys.exit(main())

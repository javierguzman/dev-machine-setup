#!/usr/bin/env python3
"""Export or apply Obsidian vault settings (the .obsidian folder), without note content.

export: copy selected settings from a vault to an output folder.
        - Plugin code, themes, and icon packs are not copied. The output lists
          plugin versions (plugins.json) and theme names (themes.json); apply
          downloads them from GitHub, like Obsidian does.
        - Plugin data (data.json) is copied only for plugins that are not in
          plugin_data_exclude (plugins with secrets or personal structure).
        - Keys in strip_keys and hotkeys that match drop_hotkeys are removed.
        - Template notes in "templates" are copied from the vault's templates
          folder (Templater or core Templates setting) to templates/.
        - A final scan fails the export when an output file contains a secret-like
          key with a value, the home folder path, or a top-level folder name of
          the vault. The output can go into a public repository.

apply:  create <vault>/.obsidian from the output folder and download the plugins
        and themes. A vault that already has a .obsidian folder stays untouched.
        Templates go to <vault>/Templates (existing files stay untouched), and
        Templater and core Templates use that folder.

Usage:
  obsidian_config.py export [--vault VAULT] --out DIR --rules-json JSON
  obsidian_config.py apply --src DIR --vault VAULT [--check] [--repos-json '{"id": "owner/repo"}']
"""

import argparse
import json
import os
import re
import shutil
import sys
import urllib.request

HOME = os.path.expanduser("~")
TEMPLATES_DIR = "Templates"   # templates folder in the vault, on apply
SECRET_KEY = re.compile(r"(api[_-]?key|token|secret|passw|passphrase|private[_-]?key|cert|credential|couchdb)", re.I)
PLUGIN_LIST = "https://raw.githubusercontent.com/obsidianmd/obsidian-releases/master/community-plugins.json"
THEME_LIST = "https://raw.githubusercontent.com/obsidianmd/obsidian-releases/master/community-css-themes.json"


def load(path):
    with open(path) as fh:
        return json.load(fh)


def dump(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")


def walk(obj, path=""):
    """Yield (path, key, value) for every key and leaf value."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            yield p, k, None
            yield from walk(v, p)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v, path + "[]")
    else:
        yield path, None, obj


# ─── export ───────────────────────────────────────────────────────────────────

def detect_vault():
    """Return the open vault from Obsidian's own vault list (or the only vault)."""
    for cfg in ("~/Library/Application Support/obsidian/obsidian.json", "~/.config/obsidian/obsidian.json"):
        path = os.path.expanduser(cfg)
        if os.path.exists(path):
            vaults = list(load(path).get("vaults", {}).values())
            open_vaults = [v["path"] for v in vaults if v.get("open")]
            if len(open_vaults) == 1:
                return open_vaults[0]
            if len(vaults) == 1:
                return vaults[0]["path"]
            sys.exit("ERROR several vaults found: set obsidian_source_vault in local.yml")
    sys.exit("ERROR no Obsidian vault list found: set obsidian_source_vault in local.yml")


def export(vault, out, rules):
    if not vault:
        vault = detect_vault()
        print(f"VAULT {vault} (from Obsidian's vault list)")
    src = os.path.join(os.path.expanduser(vault), ".obsidian")
    if not os.path.isdir(src):
        sys.exit(f"ERROR no .obsidian folder in {vault}")
    out = os.path.abspath(out)
    if os.path.basename(out) != "obsidian":
        sys.exit("ERROR the output folder must be named 'obsidian' (it gets replaced)")
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)

    strip = rules.get("strip_keys", {})
    drop_hotkeys = rules.get("drop_hotkeys", [])
    data_exclude = set(rules.get("plugin_data_exclude", []))
    plugins_exclude = set(rules.get("plugins_exclude", []))

    for name in rules.get("files", []):
        path = os.path.join(src, name)
        if not os.path.exists(path):
            continue
        data = load(path)
        if isinstance(data, dict):
            for key in strip.get(name, []):
                data.pop(key, None)
        if name == "hotkeys.json":
            # Commands are "<plugin id>:<command>"; drop those of excluded plugins too.
            data = {k: v for k, v in data.items()
                    if not any(d in k for d in drop_hotkeys) and k.split(":")[0] not in plugins_exclude}
        if name == "types.json" and isinstance(data.get("types"), dict):
            drop = tuple(rules.get("drop_type_prefixes", []))
            data["types"] = {k: v for k, v in data["types"].items() if not (drop and k.startswith(drop))}
        if name == "community-plugins.json":
            data = [p for p in data if p not in plugins_exclude]
        dump(os.path.join(out, name), data)

    plugins = {}
    enabled = load(os.path.join(src, "community-plugins.json")) if os.path.exists(os.path.join(src, "community-plugins.json")) else []
    for pid in enabled:
        if pid in plugins_exclude:
            continue
        manifest = os.path.join(src, "plugins", pid, "manifest.json")
        if not os.path.exists(manifest):
            print(f"SKIP plugin {pid}: no manifest.json")
            continue
        plugins[pid] = load(manifest)["version"]
        data = os.path.join(src, "plugins", pid, "data.json")
        if os.path.exists(data) and pid not in data_exclude:
            dump(os.path.join(out, "plugins", pid, "data.json"), load(data))
    dump(os.path.join(out, "plugins.json"), plugins)

    themes = {}
    for theme in sorted(os.listdir(os.path.join(src, "themes"))) if os.path.isdir(os.path.join(src, "themes")) else []:
        manifest = os.path.join(src, "themes", theme, "manifest.json")
        if os.path.exists(manifest):
            themes[load(manifest).get("name", theme)] = load(manifest).get("version", "")
    dump(os.path.join(out, "themes.json"), themes)

    templates = export_templates(src, out, rules.get("templates", []))

    problems = scan(out, os.path.expanduser(vault))
    if problems:
        shutil.rmtree(out)
        print("ERROR the export contains personal data or secrets. Nothing was written:")
        for p in problems:
            print("  " + p)
        print("Add the plugin to plugin_data_exclude, or the key to strip_keys.")
        sys.exit(1)
    count = sum(len(f) for _, _, f in os.walk(out))
    print(f"EXPORTED {count} files, {len(plugins)} plugins, {len(themes)} themes, "
          f"{templates} templates to {out}")


def templates_folder(src):
    """Return the vault's templates folder: Templater setting first, then core Templates."""
    for path, key in ((os.path.join(src, "plugins", "templater-obsidian", "data.json"), "templates_folder"),
                      (os.path.join(src, "templates.json"), "folder")):
        if os.path.exists(path):
            folder = load(path).get(key, "").strip("/")
            if folder:
                return folder
    return ""


def export_templates(src, out, names):
    """Copy the template notes in names to <out>/templates. Return the count."""
    if not names:
        return 0
    folder = templates_folder(src)
    if not folder:
        sys.exit("ERROR templates are set, but the vault has no templates folder setting")
    vault = os.path.dirname(src)
    for name in names:
        path = os.path.join(vault, folder, name)
        if not os.path.exists(path):
            sys.exit(f"ERROR template not found in the templates folder: {name}")
        os.makedirs(os.path.join(out, "templates"), exist_ok=True)
        shutil.copy2(path, os.path.join(out, "templates", name))
    return len(names)


def scan(out, vault):
    """Return a list of 'file: key path' problems. Values are never printed."""
    folders = [d for d in os.listdir(vault)
               if os.path.isdir(os.path.join(vault, d)) and not d.startswith(".") and len(d) > 3]
    problems = []
    for root, _, files in os.walk(out):
        for name in files:
            path = os.path.join(root, name)
            rel = os.path.relpath(path, out)
            if not name.endswith(".json"):
                with open(path) as fh:
                    text = fh.read()
                if HOME in text or any(f in text for f in folders):
                    problems.append(f"{rel}: has a vault folder name or home path")
                continue
            for p, key, value in walk(load(path)):
                if key is not None:
                    if any(f in key for f in folders) or HOME in key:
                        problems.append(f"{rel}: key {p} has a vault folder name or home path")
                    continue
                if isinstance(value, str) and value.strip():
                    leaf = p.split(".")[-1].rstrip("[]")
                    if SECRET_KEY.search(leaf):
                        problems.append(f"{rel}: {p} looks like a secret")
                    elif HOME in value or any(f in value for f in folders):
                        problems.append(f"{rel}: {p} has a vault folder name or home path")
    return problems


# ─── apply ────────────────────────────────────────────────────────────────────

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "dev-machine-setup"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def apply_templates(src, vault, target):
    """Copy the templates to <vault>/Templates and point Templater and core Templates there."""
    tsrc = os.path.join(src, "templates")
    if not os.path.isdir(tsrc):
        return
    tdir = os.path.join(vault, TEMPLATES_DIR)
    os.makedirs(tdir, exist_ok=True)
    for name in sorted(os.listdir(tsrc)):
        dest = os.path.join(tdir, name)
        if os.path.exists(dest):
            print(f"SKIP template {name}: already exists")
            continue
        shutil.copy2(os.path.join(tsrc, name), dest)
        print(f"TEMPLATE {name}")
    dump(os.path.join(target, "templates.json"), {"folder": TEMPLATES_DIR})
    plugins = load(os.path.join(src, "plugins.json"))
    tp_data = os.path.join(target, "plugins", "templater-obsidian", "data.json")
    if "templater-obsidian" in plugins and not os.path.exists(tp_data):
        # Templater fills the other settings with its defaults.
        dump(tp_data, {"templates_folder": TEMPLATES_DIR})


def apply(src, vault, check, extra_repos):
    vault = os.path.expanduser(vault)
    target = os.path.join(vault, ".obsidian")
    if os.path.exists(target):
        print(f"SKIP {target} already exists")
        return 0
    print(f"CREATE {target}")
    if check:
        return 0
    os.makedirs(target)
    for root, _, files in os.walk(src):
        for name in files:
            rel = os.path.relpath(os.path.join(root, name), src)
            if rel in ("plugins.json", "themes.json") or rel.startswith("templates" + os.sep):
                continue
            os.makedirs(os.path.dirname(os.path.join(target, rel)), exist_ok=True)
            shutil.copy2(os.path.join(src, rel), os.path.join(target, rel))

    apply_templates(src, vault, target)

    failed = 0
    plugins = load(os.path.join(src, "plugins.json"))
    repos = {p["id"]: p["repo"] for p in json.loads(fetch(PLUGIN_LIST))}
    # Plugins that left the community list (archived or moved) but still have releases
    for pid, repo in extra_repos.items():
        repos.setdefault(pid, repo)
    for pid, version in plugins.items():
        repo = repos.get(pid)
        if not repo:
            print(f"FAILED plugin {pid}: not in the community plugin list")
            failed += 1
            continue
        pdir = os.path.join(target, "plugins", pid)
        os.makedirs(pdir, exist_ok=True)
        ok = True
        for name, required in (("main.js", True), ("manifest.json", True), ("styles.css", False)):
            try:
                content = fetch(f"https://github.com/{repo}/releases/download/{version}/{name}")
                with open(os.path.join(pdir, name), "wb") as fh:
                    fh.write(content)
            except Exception as exc:
                if required:
                    print(f"FAILED plugin {pid} {version}: {name}: {exc}")
                    ok = False
        if ok:
            print(f"PLUGIN {pid} {version}")
        else:
            failed += 1

    themes = load(os.path.join(src, "themes.json"))
    theme_repos = {t["name"]: t["repo"] for t in json.loads(fetch(THEME_LIST))}
    for name in themes:
        repo = theme_repos.get(name)
        if not repo:
            print(f"FAILED theme {name}: not in the community theme list")
            failed += 1
            continue
        tdir = os.path.join(target, "themes", name)
        os.makedirs(tdir, exist_ok=True)
        try:
            for f in ("theme.css", "manifest.json"):
                with open(os.path.join(tdir, f), "wb") as fh:
                    fh.write(fetch(f"https://raw.githubusercontent.com/{repo}/HEAD/{f}"))
            print(f"THEME {name}")
        except Exception as exc:
            print(f"FAILED theme {name}: {exc}")
            failed += 1
    return 1 if failed else 0


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_exp = sub.add_parser("export")
    p_exp.add_argument("--vault", default="", help="empty = the open vault in Obsidian")
    p_exp.add_argument("--out", required=True)
    p_exp.add_argument("--rules-json", required=True)
    p_app = sub.add_parser("apply")
    p_app.add_argument("--src", required=True)
    p_app.add_argument("--vault", required=True)
    p_app.add_argument("--check", action="store_true")
    p_app.add_argument("--repos-json", default="{}")
    args = parser.parse_args()
    if args.cmd == "export":
        export(args.vault, args.out, json.loads(args.rules_json))
        return 0
    return apply(args.src, args.vault, args.check, json.loads(args.repos_json))


if __name__ == "__main__":
    sys.exit(main())

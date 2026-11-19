"""Build custom_components/smartthings from a Home Assistant core checkout.

The integration code is the core code at CORE_REF plus the overlay in overlay/.
Never edit custom_components/smartthings by hand: change the overlay or CORE_REF
and run this script again.

    python3 scripts/sync_from_core.py --core ../core          # write
    python3 scripts/sync_from_core.py --core ../core --check  # verify (CI)

Translations are regenerated in core first, with
`python3 -m script.translations develop --integration smartthings`, because core
resolves the `[%key:...%]` references in strings.json and custom integrations
can't. --check skips translations/en.json so CI only needs a sparse checkout.
"""

import argparse
import filecmp
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
OVERLAY = ROOT / "overlay"
TARGET = ROOT / "custom_components" / "smartthings"
CORE_SUBDIR = Path("homeassistant", "components", "smartthings")
# Core-only files the custom integration doesn't ship.
SKIP = {"__pycache__", "quality_scale.yaml", "strings.json"}

INIT_PATCHES = (
    (
        "\n_LOGGER = logging.getLogger(__name__)\n",
        "from .retire import async_check_core_merged\n"
        "\n_LOGGER = logging.getLogger(__name__)\n",
    ),
    (
        '    """Initialize config entry which represents an installed SmartApp."""\n',
        '    """Initialize config entry which represents an installed SmartApp."""\n'
        "    await async_check_core_merged(hass)\n",
    ),
)


def _patch_init(path: Path) -> None:
    text = path.read_text()
    for anchor, replacement in INIT_PATCHES:
        if text.count(anchor) != 1:
            sys.exit(f"Patch anchor not found exactly once in __init__.py: {anchor!r}")
        text = text.replace(anchor, replacement)
    path.write_text(text)


def _bound(requirement: str) -> str:
    """Turn core's exact pin into a range within the same major version.

    Hassfest rejects custom integrations that pin a package core also uses.
    """
    package, sep, version = requirement.partition("==")
    if not sep:
        return requirement
    return f"{package}>={version},<{int(version.split('.')[0]) + 1}"


def _merge(base: dict, extra: dict) -> dict:
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge(base[key], value)
        else:
            base[key] = value
    return base


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def build(core: Path, out: Path, *, with_translations: bool) -> None:
    """Write the custom integration into out."""
    src = core / CORE_SUBDIR
    ref = (ROOT / "CORE_REF").read_text().strip()
    head = subprocess.run(
        ["git", "-C", str(core), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if head != ref:
        sys.exit(f"Core checkout is at {head}, but CORE_REF is {ref}")

    for item in src.iterdir():
        if item.name in SKIP or item.name == "translations":
            continue
        shutil.copy2(item, out / item.name)
    shutil.copy2(OVERLAY / "retire.py", out / "retire.py")
    # HACS requires brand assets in the repository, even for a core domain.
    shutil.copytree(OVERLAY / "brand", out / "brand")
    _patch_init(out / "__init__.py")

    overlay = json.loads((OVERLAY / "manifest.json").read_text())
    manifest = json.loads((src / "manifest.json").read_text())
    for key in overlay["remove"]:
        manifest.pop(key, None)
    manifest["requirements"] = [_bound(req) for req in manifest["requirements"]]
    manifest.update(overlay["set"])
    # Home Assistant wants domain and name first, then the rest sorted.
    head_keys = {"domain": manifest.pop("domain"), "name": manifest.pop("name")}
    _write_json(out / "manifest.json", head_keys | dict(sorted(manifest.items())))

    if with_translations:
        en = src / "translations" / "en.json"
        if not en.is_file():
            sys.exit(f"{en} is missing, generate it in core first")
        (out / "translations").mkdir()
        translations = json.loads(en.read_text())
        _merge(
            translations, json.loads((OVERLAY / "translations" / "en.json").read_text())
        )
        _write_json(out / "translations" / "en.json", translations)


def _files(root: Path) -> set[Path]:
    return {p.relative_to(root) for p in root.rglob("*") if p.is_file()}


def main() -> None:
    """Run the sync."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--core", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        build(args.core, out, with_translations=not args.check)
        if not args.check:
            if TARGET.exists():
                shutil.rmtree(TARGET)
            shutil.copytree(out, TARGET)
            print(f"Wrote {TARGET.relative_to(ROOT)}")
            return

        expected = _files(out)
        actual = {
            n
            for n in _files(TARGET)
            if n.parts[0] != "translations" and "__pycache__" not in n.parts
        }
        problems = [f"missing: {n}" for n in sorted(expected - actual)]
        problems += [f"unexpected: {n}" for n in sorted(actual - expected)]
        problems += [
            f"differs from core: {n}"
            for n in sorted(expected & actual)
            if not filecmp.cmp(out / n, TARGET / n, shallow=False)
        ]
        if problems:
            sys.exit("\n".join(problems))
        print("custom_components/smartthings matches core at CORE_REF plus the overlay")


if __name__ == "__main__":
    main()

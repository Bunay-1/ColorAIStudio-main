import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHANGELOG_FILE = ROOT / "CHANGELOG.md"

VERSION_HEADER_RE = re.compile(r"^## \[(?P<version>\d+\.\d+\.\d+)\] — (?P<date>\d{4}-\d{2}-\d{2})$", re.MULTILINE)


def get_changelog_section(version: str | None = None) -> str:
    content = CHANGELOG_FILE.read_text(encoding="utf-8")
    if version:
        marker = f"## [{version}] —"
        start = content.find(marker)
    else:
        match = VERSION_HEADER_RE.search(content)
        if not match:
            raise SystemExit("Unable to find any release section in CHANGELOG.md")
        start = match.start()
        version = match.group("version")

    if start == -1:
        raise SystemExit(f"Unable to find release section for version '{version}' in CHANGELOG.md")

    next_section = content.find("\n## [", start + 1)
    section = content[start:] if next_section == -1 else content[start:next_section]
    return section.strip()


def normalize_release_body(section: str) -> str:
    lines = section.splitlines()
    if not lines:
        return section
    if lines[0].startswith("## ["):
        title = lines[0].strip()
        body = "\n".join(lines[1:]).strip()
        return f"{title}\n{body}\n"
    return section


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract the top release notes section from CHANGELOG.md.")
    parser.add_argument("--version", help="Release version to extract (e.g. 8.9.7). If omitted, uses the latest release section.")
    parser.add_argument("--output", help="Write extracted release notes to a file.")
    args = parser.parse_args()

    section = get_changelog_section(args.version)
    body = normalize_release_body(section)

    if args.output:
        Path(args.output).write_text(body, encoding="utf-8")
    else:
        print(body)


if __name__ == "__main__":
    main()

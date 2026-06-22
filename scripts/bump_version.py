import argparse
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = ROOT / "utils" / "version.py"
README_FILE = ROOT / "README.md"
DOCKERFILE = ROOT / "Dockerfile"
DOCKER_COMPOSE = ROOT / "docker-compose.yml"
DOCKER_COMPOSE_PROD = ROOT / "docker-compose.prod.yml"
K8S_DEPLOYMENT = ROOT / "k8s" / "icap-deployment.yaml"
IRM_API_FILE = ROOT / "irm_api.py"
CHANGELOG = ROOT / "CHANGELOG.md"
POSTMAN = ROOT / "postman" / "ICAP_Enterprise_Collection.json"
REQUIREMENTS = ROOT / "requirements.txt"

SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
DRY_RUN = False


def read_version_file():
    text = VERSION_FILE.read_text(encoding="utf-8")
    version_match = re.search(r'ICAP_VERSION\s*=\s*["\'](?P<version>\d+\.\d+\.\d+)["\']', text)
    display_match = re.search(r'ICAP_VERSION_DISPLAY\s*=\s*["\'](?P<display>[^"\']+)["\']', text)
    if not version_match or not display_match:
        raise SystemExit("Unable to parse version metadata from utils/version.py")
    return version_match.group("version"), display_match.group("display")


def bump_semver(version: str, bump_type: str) -> str:
    match = SEMVER_RE.match(version)
    if not match:
        raise ValueError(f"Invalid semantic version: {version}")
    major, minor, patch = map(int, match.groups())
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        raise ValueError(f"Unknown bump type: {bump_type}")
    return f"{major}.{minor}.{patch}"


def replace_file(path: Path, patterns):
    content = path.read_text(encoding="utf-8")
    original = content
    for pattern, repl in patterns:
        content, count = re.subn(pattern, repl, content, flags=re.MULTILINE)
        if count == 0:
            raise SystemExit(f"Pattern not found in {path}: {pattern}")
    if content != original:
        if DRY_RUN:
            print(f"[DRY RUN] Would update {path}")
            return
        path.write_text(content, encoding="utf-8")


def update_version_file(version: str, display: str):
    replace_file(VERSION_FILE, [
        (r'ICAP_VERSION\s*=\s*["\']\d+\.\d+\.\d+["\']', f'ICAP_VERSION = "{version}"'),
        (r'ICAP_VERSION_DISPLAY\s*=\s*["\'][^"\']+["\']', f'ICAP_VERSION_DISPLAY = "{display}"'),
    ])


def update_readme(version: str):
    replace_file(README_FILE, [
        (r'Industrial Color AI Platform \(ICAP\) v\d+\.\d+\.\d+ Enterprise', f'Industrial Color AI Platform (ICAP) v{version} Enterprise'),
        (r'https://img\.shields\.io/badge/Industrial_AI-v\d+\.\d+\.\d+-blue\?style=for-the-badge&logo=ai',
         f'https://img.shields.io/badge/Industrial_AI-v{version}-blue?style=for-the-badge&logo=ai'),
        (rf'### 🌟 Ключови подобрения в v\d+\.\d+\.\d+ Enterprise \[Stable\]:',
         f'### 🌟 Ключови подобрения в v{version} Enterprise [Stable]:'),
        (rf'docker build -t icap-v\d+\.\d+\.\d+ \.', f'docker build -t icap-v{version} .'),
        (rf'docker run -p 8000:8000 --env-file \.env icap-v\d+\.\d+\.\d+', f'docker run -p 8000:8000 --env-file .env icap-v{version}'),
        (rf'\*Изготвено от: ICAP Engineering Team \| v\d+\.\d+\.\d+ \| \d+\*', f'*Изготвено от: ICAP Engineering Team | v{version} | {datetime.now().year}*'),
    ])


def update_irm_api_version(version: str, display: str):
    replace_file(IRM_API_FILE, [
        (r'Version: \d+\.\d+\.\d+ Enterprise', f'Version: {display}'),
    ])


def update_dockerfile(version: str):
    replace_file(DOCKERFILE, [
        (r'# ICAP Platform Dockerfile — v\d+\.\d+\.\d+ Enterprise', f'# ICAP Platform Dockerfile — v{version} Enterprise'),
        (r'LABEL org\.opencontainers\.image\.version="\d+\.\d+\.\d+"', f'LABEL org.opencontainers.image.version="{version}"'),
    ])


def update_docker_compose(version: str):
    replace_file(DOCKER_COMPOSE, [
        (r'image: icap-v\d+\.\d+\.\d+', f'image: icap-v{version}'),
        (r'ICAP_VERSION=\d+\.\d+\.\d+', f'ICAP_VERSION={version}'),
    ])
    replace_file(DOCKER_COMPOSE_PROD, [
        (r'ICAP_VERSION=\d+\.\d+\.\d+', f'ICAP_VERSION={version}'),
    ])


def update_k8s_deployment(version: str):
    replace_file(K8S_DEPLOYMENT, [
        (r'version: v\d+\.\d+\.\d+', f'version: v{version}'),
        (r'image: icap-api:\d+\.\d+\.\d+', f'image: icap-api:{version}'),
    ])


def update_postman(version: str):
    replace_file(POSTMAN, [
        (r'"description": "Postman collection for ICAP v\d+\.\d+\.\d+ Enterprise API testing"',
         f'"description": "Postman collection for ICAP v{version} Enterprise API testing"'),
    ])


def update_requirements(version: str):
    replace_file(REQUIREMENTS, [
        (r'# --- ICAP PRODUCTION REQUIREMENTS \(v\d+\.\d+\.\d+ Enterprise\) ---',
         f'# --- ICAP PRODUCTION REQUIREMENTS (v{version} Enterprise) ---'),
    ])


def update_changelog(version: str, added_message: str | None = None, changed_message: str | None = None):
    content = CHANGELOG.read_text(encoding="utf-8")
    section_marker = f"## [{version}] —"
    section_exists = section_marker in content

    if section_exists:
        if not added_message and not changed_message:
            print(f"[SKIP] CHANGELOG already contains version {version}")
            return

        section_start = content.index(section_marker)
        next_section = content.find("\n## [", section_start + len(section_marker))
        section = content[section_start:] if next_section == -1 else content[section_start:next_section]
        updated_section = section

        if added_message:
            updated_section, count = re.subn(
                r"(### Добавено\s*\n- ).*", f"\\1{added_message}",
                updated_section,
                count=1,
            )
            if count == 0:
                raise SystemExit("Unable to update 'Добавено' section in existing CHANGELOG entry")

        if changed_message:
            updated_section, count = re.subn(
                r"(### Променено\s*\n- ).*", f"\\1{changed_message}",
                updated_section,
                count=1,
            )
            if count == 0:
                raise SystemExit("Unable to update 'Променено' section in existing CHANGELOG entry")

        if updated_section == section:
            print(f"[SKIP] No changelog updates applied for v{version}")
            return

        new_content = content.replace(section, updated_section, 1)
        if DRY_RUN:
            print(f"[DRY RUN] Would update existing CHANGELOG entry for v{version}")
            return

        CHANGELOG.write_text(new_content, encoding="utf-8")
        return

    added_message = added_message or "TODO: Добавете описание на новите функции и корекции."
    changed_message = changed_message or "TODO: Добавете описание на промените."

    header = (
        f"## [{version}] — {datetime.now():%Y-%m-%d}\n\n"
        f"### Добавено\n"
        f"- {added_message}\n\n"
        f"### Променено\n"
        f"- {changed_message}\n\n"
    )

    insert_marker = (
        "# CHANGELOG — ICAP Platform\n\n"
        "Всички значими промени по проекта се записват в този файл. Форматът е базиран на [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).\n\n"
    )
    if insert_marker not in content:
        raise SystemExit("Unexpected CHANGELOG.md format; cannot insert new version section")

    new_content = content.replace(insert_marker, insert_marker + header, 1)
    if new_content == content:
        raise SystemExit("Failed to update CHANGELOG.md")

    if DRY_RUN:
        print(f"[DRY RUN] Would add changelog entry for v{version}")
        return

    CHANGELOG.write_text(new_content, encoding="utf-8")


def validate_semver(version: str):
    if not SEMVER_RE.match(version):
        raise ValueError(f"Version must be semantic format X.Y.Z, got '{version}'")


def main():
    current_version, current_display = read_version_file()

    parser = argparse.ArgumentParser(description="Bump ICAP version across repository files.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--new", help="Set an explicit semantic version (e.g. 8.9.7)")
    group.add_argument("--patch", action="store_true", help="Bump patch version")
    group.add_argument("--minor", action="store_true", help="Bump minor version")
    group.add_argument("--major", action="store_true", help="Bump major version")
    parser.add_argument("--added", help="One-line release note for the added section")
    parser.add_argument("--changed", help="One-line release note for the changed section")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing files")
    args = parser.parse_args()

    global DRY_RUN
    DRY_RUN = args.dry_run

    if args.new:
        new_version = args.new.strip()
        validate_semver(new_version)
    elif args.patch:
        new_version = bump_semver(current_version, "patch")
    elif args.minor:
        new_version = bump_semver(current_version, "minor")
    elif args.major:
        new_version = bump_semver(current_version, "major")
    else:
        raise SystemExit("No version bump option provided")

    new_display = f"{new_version} Enterprise"

    print(f"Bumping ICAP from {current_version} to {new_version}")
    update_version_file(new_version, new_display)
    update_irm_api_version(new_version, new_display)
    update_readme(new_version)
    update_dockerfile(new_version)
    update_docker_compose(new_version)
    update_k8s_deployment(new_version)
    update_postman(new_version)
    update_requirements(new_version)
    update_changelog(new_version, args.added, args.changed)

    print("Version bump complete.")
    print("Review and fill in the CHANGELOG TODO items before committing.")


if __name__ == "__main__":
    main()

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = ROOT / "utils" / "version.py"
CHANGELOG_FILE = ROOT / "CHANGELOG.md"


def read_version_file(path: Path):
    text = path.read_text(encoding="utf-8")
    match_short = re.search(r'ICAP_VERSION\s*=\s*["\'](?P<version>\d+\.\d+\.\d+)["\']', text)
    match_display = re.search(r'ICAP_VERSION_DISPLAY\s*=\s*["\'](?P<display>[^"\']+)["\']', text)
    if not match_short or not match_display:
        raise SystemExit("Unable to parse ICAP_VERSION or ICAP_VERSION_DISPLAY from utils/version.py")
    return match_short.group("version"), match_display.group("display")


def assert_contains(file_path: Path, pattern: str, label: str):
    content = file_path.read_text(encoding="utf-8")
    if pattern not in content:
        raise SystemExit(f"[FAIL] {label}: expected '{pattern}' in {file_path}")
    print(f"[OK] {label}")


def get_top_changelog_section(version: str) -> str:
    content = CHANGELOG_FILE.read_text(encoding="utf-8")
    marker = f"## [{version}] —"
    start = content.find(marker)
    if start == -1:
        raise SystemExit(f"[FAIL] CHANGELOG top version: could not find section for v{version}")

    next_section = content.find("\n## [", start + len(marker))
    if next_section == -1:
        return content[start:]
    return content[start:next_section]


def validate_changelog_content(version: str):
    section = get_top_changelog_section(version)
    if "TODO:" in section:
        raise SystemExit(
            f"[FAIL] CHANGELOG content for v{version} contains TODO placeholders. Fill release notes before merge."
        )
    if not re.search(r"###\s*Добавено\s*\n- .+", section):
        raise SystemExit(
            f"[FAIL] CHANGELOG v{version} does not contain an 'Добавено' bullet list."
        )
    if not re.search(r"###\s*Променено\s*\n- .+", section):
        raise SystemExit(
            f"[FAIL] CHANGELOG v{version} does not contain a 'Променено' bullet list."
        )
    print(f"[OK] CHANGELOG content for v{version}")


def main():
    version, display_version = read_version_file(VERSION_FILE)
    expected_image_tag = f"icap-v{version}"
    expected_k8s_label = f"version: v{version}"
    expected_k8s_image = f"image: icap-api:{version}"
    expected_env = f"ICAP_VERSION={version}"
    expected_postman = f'"description": "Postman collection for ICAP v{version} Enterprise API testing"'
    expected_requirements = f"# --- ICAP PRODUCTION REQUIREMENTS (v{version} Enterprise) ---"

    print(f"Validating ICAP version consistency for {display_version}")

    assert_contains(ROOT / "README.md", f"v{version} Enterprise", "README version")
    assert_contains(ROOT / "README.md", expected_image_tag, "README Docker tag")
    assert_contains(ROOT / "Dockerfile", f"v{version} Enterprise", "Dockerfile version comment")
    assert_contains(ROOT / "Dockerfile", f'org.opencontainers.image.version="{version}"', "Dockerfile OCI label")
    assert_contains(ROOT / "docker-compose.yml", expected_image_tag, "docker-compose image tag")
    assert_contains(ROOT / "docker-compose.yml", expected_env, "docker-compose ICAP_VERSION")
    assert_contains(ROOT / "docker-compose.prod.yml", expected_env, "docker-compose.prod ICAP_VERSION")
    assert_contains(ROOT / "k8s" / "icap-deployment.yaml", expected_k8s_label, "k8s version label")
    assert_contains(ROOT / "k8s" / "icap-deployment.yaml", expected_k8s_image, "k8s image tag")
    assert_contains(ROOT / "CHANGELOG.md", f"## [{version}] —", "CHANGELOG top version")
    assert_contains(ROOT / "postman" / "ICAP_Enterprise_Collection.json", expected_postman, "Postman collection version")
    assert_contains(ROOT / "requirements.txt", expected_requirements, "requirements metadata version")
    validate_changelog_content(version)

    print("All version consistency checks passed.")


if __name__ == "__main__":
    main()

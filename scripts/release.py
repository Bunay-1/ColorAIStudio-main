import argparse
import subprocess
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parent.parent
BUMP_SCRIPT = ROOT / "scripts" / "bump_version.py"
VERSION_FILE = ROOT / "utils" / "version.py"

RELEASE_FILES = [
    ROOT / "utils" / "version.py",
    ROOT / "irm_api.py",
    ROOT / "README.md",
    ROOT / "Dockerfile",
    ROOT / "docker-compose.yml",
    ROOT / "docker-compose.prod.yml",
    ROOT / "k8s" / "icap-deployment.yaml",
    ROOT / "postman" / "ICAP_Enterprise_Collection.json",
    ROOT / "requirements.txt",
    ROOT / "CHANGELOG.md",
]


def run_command(command: List[str], dry_run: bool = False, **kwargs) -> subprocess.CompletedProcess:
    print(f"> {' '.join(command)}")
    if dry_run:
        return subprocess.CompletedProcess(command, 0)
    return subprocess.run(command, check=True, text=True, **kwargs)


def read_current_version() -> str:
    text = VERSION_FILE.read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("ICAP_VERSION"):
            return line.split("=")[1].strip().strip('"').strip("'")
    raise SystemExit("Unable to read current version from utils/version.py")


def repo_is_clean() -> bool:
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
    return result.stdout.strip() == ""


def git_add_and_commit(version: str, dry_run: bool = False) -> None:
    run_command(["git", "add", *(str(path) for path in RELEASE_FILES)], dry_run=dry_run)
    run_command(["git", "commit", "-m", f"chore(release): v{version}"], dry_run=dry_run)


def git_tag(version: str, dry_run: bool = False) -> None:
    run_command(["git", "tag", "-a", f"v{version}", "-m", f"Release v{version}"], dry_run=dry_run)


def git_push(push: bool, tag: bool, dry_run: bool = False) -> None:
    if not push:
        return
    run_command(["git", "push"], dry_run=dry_run)
    if tag:
        run_command(["git", "push", "--tags"], dry_run=dry_run)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a release by bumping ICAP version, updating changelog, and optionally committing and tagging.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--new", help="Set an explicit semantic version (e.g. 8.9.8)")
    group.add_argument("--patch", action="store_true", help="Bump patch version")
    group.add_argument("--minor", action="store_true", help="Bump minor version")
    group.add_argument("--major", action="store_true", help="Bump major version")

    parser.add_argument("--added", required=True, help="One-line release note for the added section")
    parser.add_argument("--changed", required=True, help="One-line release note for the changed section")
    parser.add_argument("--commit", action="store_true", help="Commit release files")
    parser.add_argument("--tag", action="store_true", help="Create annotated git tag")
    parser.add_argument("--push", action="store_true", help="Push commit and tags to remote")
    parser.add_argument("--dry-run", action="store_true", help="Show the release actions without executing them")
    args = parser.parse_args()

    bump_args = ["python", str(BUMP_SCRIPT)]
    if args.new:
        bump_args.extend(["--new", args.new])
    elif args.patch:
        bump_args.append("--patch")
    elif args.minor:
        bump_args.append("--minor")
    elif args.major:
        bump_args.append("--major")

    bump_args.extend(["--added", args.added, "--changed", args.changed])
    if args.dry_run:
        bump_args.append("--dry-run")

    run_command(bump_args, dry_run=args.dry_run)

    if args.dry_run:
        print("[DRY RUN] Release helper finished without making changes.")
        return

    version = args.new or read_current_version()

    if args.commit or args.tag:
        if not repo_is_clean():
            raise SystemExit("Git repository is not clean. Commit or stash changes before running release.")

        if args.commit:
            git_add_and_commit(version, dry_run=args.dry_run)
        if args.tag:
            git_tag(version, dry_run=args.dry_run)
        git_push(push=args.push, tag=args.tag, dry_run=args.dry_run)
        print(f"Release v{version} created successfully.")
    else:
        print("Release files updated. Commit and tag manually if desired.")


if __name__ == "__main__":
    main()

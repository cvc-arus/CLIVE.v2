#!/usr/bin/env python3
"""Check that nothing private is in the repository (ADR-017).

Reads ``docs/simpro/private/public-deny-list.txt`` (untracked; one
``<id><TAB><regex>[<TAB>meta]`` per line, ``#`` for comments; ``meta``
limits a pattern to commit authors and committers) and reports every match as
``location:line:pattern-id``. It never prints the matched text, so it is safe
to run where output is shared.

Usage::

    python3 scripts/check-public-safe.py              # tracked files
    python3 scripts/check-public-safe.py --history    # every blob on every ref,
                                                      # plus commit messages,
                                                      # authors and committers
    python3 scripts/check-public-safe.py --history --repo <path-to-clone-or-mirror>

Exit status: 0 clean, 1 at least one match, 2 deny-list missing or invalid.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DENY_LIST = REPO_ROOT / "docs" / "simpro" / "private" / "public-deny-list.txt"


Pattern = tuple[str, re.Pattern[str], bool]


def load_deny_list(path: Path) -> list[Pattern]:
    """Return ``(id, compiled regex, meta_only)`` triples from a deny-list file.

    Raises:
        FileNotFoundError: if the file does not exist.
        ValueError: if a line is malformed or a regex does not compile. The
            message names the line number only, never the pattern.
    """
    patterns: list[Pattern] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        fields = raw.split("\t")
        if len(fields) not in (2, 3) or not all(fields[:2]):
            raise ValueError(f"deny-list line {number}: expected <id><TAB><regex>")
        if len(fields) == 3 and fields[2] != "meta":
            raise ValueError(f"deny-list line {number}: scope must be 'meta'")
        try:
            regex = re.compile(fields[1])
        except re.error as exc:
            raise ValueError(
                f"deny-list line {number}: invalid regex ({exc.msg})"
            ) from None
        patterns.append((fields[0], regex, len(fields) == 3))
    if not patterns:
        raise ValueError("deny-list has no patterns")
    return patterns


def scan_text(
    location: str, text: str, patterns: list[Pattern], *, meta: bool = False
) -> Iterator[str]:
    """Yield ``location:line:id`` for every pattern match in ``text``.

    ``meta`` marks ``text`` as a commit author or committer field; patterns
    scoped to ``meta`` are applied only then.
    """
    for pattern_id, regex, meta_only in patterns:
        if meta_only and not meta:
            continue
        for match in regex.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            yield f"{location}:{line}:{pattern_id}"


def git(repo: Path, *args: str) -> bytes:
    """Run a git command in ``repo`` and return its stdout."""
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, check=True
    ).stdout


def tracked_files(repo: Path) -> Iterator[tuple[str, str]]:
    """Yield ``(path, text)`` for every tracked file in the working tree."""
    for name in git(repo, "ls-files", "-z").decode().split("\0"):
        path = repo / name
        if name and path.is_file():
            yield name, path.read_bytes().decode("utf-8", errors="replace")


def history_blobs(repo: Path) -> Iterator[tuple[str, str]]:
    """Yield ``(label, text)`` for every distinct blob reachable from any ref."""
    seen: dict[str, str] = {}
    for line in git(repo, "rev-list", "--all", "--objects").decode().splitlines():
        sha, _, path = line.partition(" ")
        if path and sha not in seen:
            seen[sha] = path
    listing = "\n".join(seen).encode()
    batch = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "--batch"],
        input=listing,
        capture_output=True,
        check=True,
    ).stdout
    offset = 0
    while offset < len(batch):
        header_end = batch.index(b"\n", offset)
        sha, kind, size = batch[offset:header_end].decode().split()
        start = header_end + 1
        body = batch[start : start + int(size)]
        offset = start + int(size) + 1
        if kind == "blob":
            yield f"{seen[sha]}@{sha[:8]}", body.decode("utf-8", errors="replace")


def commit_metadata(repo: Path) -> Iterator[tuple[str, str]]:
    """Yield ``(label, text)`` for every commit's identities and message."""
    fmt = "%H%x00%an <%ae>%x00%cn <%ce>%x00%B%x01"
    for record in git(repo, "log", "--all", f"--format={fmt}").decode().split("\x01"):
        fields = record.strip("\n").split("\0")
        if len(fields) != 4:
            continue
        sha, author, committer, message = fields
        yield f"commit {sha[:8]} author", author
        yield f"commit {sha[:8]} committer", committer
        yield f"commit {sha[:8]} message", message
    for tag in git(repo, "tag", "-l").decode().split():
        yield f"tag {tag}", git(repo, "tag", "-l", "-n999", tag).decode()


def main() -> int:
    """Run the check and return the exit status."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--history", action="store_true", help="scan all history")
    parser.add_argument("--repo", type=Path, default=REPO_ROOT, help="repository")
    parser.add_argument("--deny-list", type=Path, default=DEFAULT_DENY_LIST)
    args = parser.parse_args()

    try:
        patterns = load_deny_list(args.deny_list)
    except FileNotFoundError:
        print(
            f"deny-list not found: {args.deny_list} "
            "(restore docs/simpro/private/ from backup; see "
            "docs/simpro/private-notes.template.md)",
            file=sys.stderr,
        )
        return 2
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.history:
        sources = [history_blobs(args.repo), commit_metadata(args.repo)]
    else:
        sources = [tracked_files(args.repo)]

    hits = 0
    scanned = 0
    for source in sources:
        for location, text in source:
            scanned += 1
            meta = location.endswith((" author", " committer"))
            for hit in scan_text(location, text, patterns, meta=meta):
                print(hit)
                hits += 1
    scope = "history objects" if args.history else "tracked files"
    print(
        f"{hits} match(es) in {scanned} {scope}; {len(patterns)} patterns",
        file=sys.stderr,
    )
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())

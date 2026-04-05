#!/usr/bin/env python3

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable


TITLE_DIFF_THRESHOLD = 4
AUTHOR_DIFF_THRESHOLD = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Precheck whether a candidate paper may already exist in papers.json. "
            "A match is reported only when both title and author similarity pass."
        )
    )
    parser.add_argument("--title", required=True, help="Candidate paper title.")
    parser.add_argument(
        "--author",
        action="append",
        dest="authors",
        default=[],
        help=(
            "Candidate author name. Repeat this flag for multiple authors. "
            "Example: --author 'Ye, Weihao' --author 'Wu, Qiong'"
        ),
    )
    parser.add_argument(
        "--authors-json",
        help="Alternative to --author: a JSON array of author strings.",
    )
    parser.add_argument(
        "--db",
        default=str(Path(__file__).resolve().parents[1] / "papers.json"),
        help="Path to the papers JSON database. Defaults to workspace papers.json.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of suspected matches to print.",
    )
    return parser.parse_args()


def normalize_text(value: str) -> str:
    lowered = value.lower()
    no_punct = re.sub(r"[^\w\s]", " ", lowered)
    collapsed = re.sub(r"\s+", " ", no_punct).strip()
    return collapsed


def title_counter(title: str) -> Counter[str]:
    normalized = normalize_text(title)
    if not normalized:
        return Counter()
    return Counter(normalized.split())


def author_to_initials(author: str) -> str:
    normalized = normalize_text(author)
    if not normalized:
        return ""
    initials = [part[0] for part in normalized.split() if part]
    return " ".join(initials)


def author_counter(authors: Iterable[str]) -> Counter[str]:
    normalized_authors = []
    for author in authors:
        initials = author_to_initials(author)
        if not initials:
            continue
        normalized_authors.append(" ".join(sorted(initials.split())))
    filtered = [author for author in normalized_authors if author]
    return Counter(filtered)


def counter_diff_size(left: Counter[str], right: Counter[str]) -> int:
    left_only = left - right
    right_only = right - left
    return sum(left_only.values()) + sum(right_only.values())


def load_authors(args: argparse.Namespace) -> list[str]:
    if args.authors_json:
        try:
            parsed = json.loads(args.authors_json)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"--authors-json is not valid JSON: {exc}") from exc
        if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
            raise SystemExit("--authors-json must be a JSON array of strings.")
        if args.authors:
            raise SystemExit("Use either --author or --authors-json, not both.")
        return parsed
    return args.authors


def load_database(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Failed to parse JSON database {path}: {exc}") from exc
    if not isinstance(data, list):
        raise SystemExit(f"JSON database {path} must contain a top-level list.")
    return data


def main() -> int:
    args = parse_args()
    query_authors = load_authors(args)
    db_path = Path(args.db).resolve()
    database = load_database(db_path)

    query_title_counter = title_counter(args.title)
    query_author_counter = author_counter(query_authors)

    matches = []
    for index, entry in enumerate(database):
        entry_title = entry.get("title", "")
        entry_authors = entry.get("authors", [])
        if not isinstance(entry_title, str) or not isinstance(entry_authors, list):
            continue
        if not all(isinstance(author, str) for author in entry_authors):
            continue

        entry_title_counter = title_counter(entry_title)
        entry_author_counter = author_counter(entry_authors)

        title_diff = counter_diff_size(query_title_counter, entry_title_counter)
        author_diff = counter_diff_size(query_author_counter, entry_author_counter)

        # Primary match: title similarity only
        if title_diff <= TITLE_DIFF_THRESHOLD:
            matches.append(
                {
                    "index": index,
                    "title": entry_title,
                    "authors": entry_authors,
                    "date": entry.get("date"),
                    "url": entry.get("url"),
                    "keywords": entry.get("keywords"),
                    "is_tex_downloaded": entry.get("is_tex_downloaded"),
                    "title_diff_words": title_diff,
                    "author_diff_count": author_diff,
                    "author_match": author_diff <= AUTHOR_DIFF_THRESHOLD,
                }
            )

    matches.sort(key=lambda item: (item["title_diff_words"], item["author_diff_count"], item["index"]))
    if args.limit >= 0:
        matches = matches[: args.limit]

    result = {
        "query": {
            "title": args.title,
            "authors": query_authors,
            "db": str(db_path),
            "title_diff_threshold": TITLE_DIFF_THRESHOLD,
            "author_diff_threshold": AUTHOR_DIFF_THRESHOLD,
        },
        "match_count": len(matches),
        "matches": matches,
    }
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Sync local bibliography PDFs for the thesis report.

This script reads ``informe/bibliography.bib`` and downloads one local PDF
per paper into ``informe/bibliografia/papers/``. It also writes a manifest with
the resolved source URL and the download status of each bibliography entry.

The current bibliography mixes journal/conference papers with web references.
Web-only entries are kept in the manifest but do not produce local PDFs.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterator
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin, urlparse
from urllib.request import Request, urlopen


USER_AGENT = "go2-marine-platform bibliography sync/1.0"
REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/pdf,text/html,application/json;q=0.9,*/*;q=0.8",
}

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BIB_PATH = REPO_ROOT / "informe" / "bibliography.bib"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "informe" / "bibliografia" / "papers"
DEFAULT_MANIFEST_PATH = REPO_ROOT / "informe" / "bibliografia" / "manifest.json"

# Curated direct sources for the papers currently used in the report. Entries
# without an override fall back to OpenAlex-based discovery when possible.
MANUAL_PDF_SOURCES = {
    "Fossen1995": {
        "pdf_url": "https://fossen.biz/publications/1995%20Fossen%20and%20Fjellstad%20JMMS.pdf",
        "source_note": "Author-hosted PDF",
    },
    "Fahmi2019": {
        "pdf_url": "https://hal.science/hal-02086071v1/file/wbcontrol18ral.pdf",
        "source_note": "HAL repository copy",
    },
    "Bellicoso2017": {
        "pdf_url": (
            "https://www.research-collection.ethz.ch/bitstreams/"
            "2b57711c-bfb1-4db3-ad1e-478b3d2175c5/download"
        ),
        "source_note": "ETH Zurich repository copy",
    },
    "GarridoJurado2014": {
        "pdf_url": (
            "https://web.archive.org/web/20170722163146id_/http://www.uco.es:80/"
            "investiga/grupos/ava/sites/default/files/GarridoJurado2014.pdf"
        ),
        "source_note": "Wayback snapshot of the author-hosted PDF",
    },
    "Lepetit2009": {
        "pdf_url": (
            "https://upcommons.upc.edu/bitstreams/"
            "e2b554f3-168f-4421-9dea-2949d6665020/download"
        ),
        "source_note": "UPC repository copy",
    },
    "Schweighofer2006": {
        "pdf_url": (
            "https://web.archive.org/web/20240504151408id_/https://citeseerx.ist.psu.edu/"
            "document?repid=rep1&type=pdf&doi=85ad143e7fe0eafe536bb769de3cc5324500dd58"
        ),
        "source_note": "Archived CiteSeerX PDF",
    },
    "Alarcon2019": {
        "pdf_url": "https://personal.us.es/imaza/papers/journals/alarcon_sensors19/alarcon_sensors19_web.pdf",
        "source_note": "Author-hosted PDF",
    },
    "Delbene2022": {
        "pdf_url": (
            "https://unige.iris.cineca.it/retrieve/e268c4ce-b962-a6b7-e053-3a05fe0adea1/"
            "2022_05_sensors_Visual%20Servoed%20Autonomous%20Landing%20of%20an%20UAV%20on%20a%20catamaran.pdf"
        ),
        "source_note": "University of Genoa repository copy",
    },
    "Morales2023": {
        "pdf_url": "https://pdfs.semanticscholar.org/5719/dd13008955af434192ab1db9a97b305b235d.pdf",
        "source_note": "Indexed PDF copy via Semantic Scholar",
    },
}


@dataclass
class BibEntry:
    entry_type: str
    key: str
    fields: dict[str, str]

    @property
    def title(self) -> str:
        return strip_braces(self.fields.get("title", "")).strip()

    @property
    def year(self) -> str:
        return self.fields.get("year", "").strip()

    @property
    def doi(self) -> str:
        return self.fields.get("doi", "").strip()

    @property
    def url(self) -> str:
        return self.fields.get("url", "").strip()

    @property
    def is_academic_paper(self) -> bool:
        if self.entry_type in {
            "article",
            "inproceedings",
            "incollection",
            "book",
            "phdthesis",
            "mastersthesis",
        }:
            return True
        return bool(self.doi)


def strip_braces(text: str) -> str:
    return text.replace("{", "").replace("}", "")


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_bibtex(text: str) -> list[BibEntry]:
    entries: list[BibEntry] = []
    index = 0
    while True:
        at = text.find("@", index)
        if at == -1:
            return entries
        cursor = at + 1
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        type_start = cursor
        while cursor < len(text) and text[cursor].isalpha():
            cursor += 1
        entry_type = text[type_start:cursor].lower()
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if cursor >= len(text) or text[cursor] not in "{(":
            index = cursor
            continue
        opener = text[cursor]
        closer = "}" if opener == "{" else ")"
        cursor += 1
        key_start = cursor
        while cursor < len(text) and text[cursor] != ",":
            cursor += 1
        key = text[key_start:cursor].strip()
        cursor += 1
        body_start = cursor
        depth = 1
        in_quote = False
        escaped = False
        while cursor < len(text) and depth > 0:
            char = text[cursor]
            if in_quote:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_quote = False
            else:
                if char == '"':
                    in_quote = True
                elif char == opener:
                    depth += 1
                elif char == closer:
                    depth -= 1
            cursor += 1
        body = text[body_start : cursor - 1]
        entries.append(BibEntry(entry_type=entry_type, key=key, fields=parse_fields(body)))
        index = cursor


def parse_fields(body: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    cursor = 0
    length = len(body)
    while cursor < length:
        while cursor < length and body[cursor] in " \t\r\n,":
            cursor += 1
        if cursor >= length:
            return fields
        name_start = cursor
        while cursor < length and body[cursor] not in "=\r\n":
            cursor += 1
        name = body[name_start:cursor].strip().lower()
        while cursor < length and body[cursor].isspace():
            cursor += 1
        if cursor >= length or body[cursor] != "=":
            break
        cursor += 1
        while cursor < length and body[cursor].isspace():
            cursor += 1
        if cursor >= length:
            break
        value, cursor = parse_value(body, cursor)
        fields[name] = normalize_whitespace(value)
    return fields


def parse_value(text: str, cursor: int) -> tuple[str, int]:
    if text[cursor] == "{":
        return parse_braced_value(text, cursor)
    if text[cursor] == '"':
        return parse_quoted_value(text, cursor)
    value_start = cursor
    while cursor < len(text) and text[cursor] not in ",\r\n":
        cursor += 1
    return text[value_start:cursor].strip(), cursor


def parse_braced_value(text: str, cursor: int) -> tuple[str, int]:
    cursor += 1
    depth = 1
    value_chars: list[str] = []
    while cursor < len(text) and depth > 0:
        char = text[cursor]
        if char == "{":
            depth += 1
            value_chars.append(char)
        elif char == "}":
            depth -= 1
            if depth > 0:
                value_chars.append(char)
        else:
            value_chars.append(char)
        cursor += 1
    return "".join(value_chars), cursor


def parse_quoted_value(text: str, cursor: int) -> tuple[str, int]:
    cursor += 1
    escaped = False
    value_chars: list[str] = []
    while cursor < len(text):
        char = text[cursor]
        if escaped:
            value_chars.append(char)
            escaped = False
        elif char == "\\":
            value_chars.append(char)
            escaped = True
        elif char == '"':
            cursor += 1
            break
        else:
            value_chars.append(char)
        cursor += 1
    return "".join(value_chars), cursor


def read_url(url: str) -> tuple[bytes, str, dict[str, str]]:
    request = Request(url, headers=REQUEST_HEADERS)
    with urlopen(request, timeout=45) as response:
        payload = response.read()
        headers = dict(response.info().items())
        return payload, response.geturl(), headers


def read_text_url(url: str) -> str:
    payload, _, _ = read_url(url)
    return payload.decode("utf-8", "ignore")


def fetch_openalex_record(doi: str) -> dict | None:
    if not doi:
        return None
    openalex_url = f"https://api.openalex.org/works/https://doi.org/{quote(doi, safe='')}"
    try:
        payload, _, _ = read_url(openalex_url)
        return json.loads(payload)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return None


def html_pdf_candidates(page_url: str) -> Iterator[str]:
    try:
        html = read_text_url(page_url)
    except (HTTPError, URLError, TimeoutError):
        return
    meta_match = re.findall(
        r'<meta[^>]+name=["\']citation_pdf_url["\'][^>]+content=["\']([^"\']+)["\']',
        html,
        flags=re.IGNORECASE,
    )
    for match in meta_match:
        yield urljoin(page_url, match)
    for pattern in (
        r'https?://[^\s"\'<>]+\.pdf(?:\?[^\s"\'<>]+)?',
        r'/bitstreams/[^\s"\'<>]+/download',
        r'https?://hal\.science/[^\s"\'<>]+/(?:file|document)[^\s"\'<>]*',
    ):
        for match in re.findall(pattern, html, flags=re.IGNORECASE):
            yield urljoin(page_url, match)


def expand_candidate_url(candidate: str) -> Iterator[str]:
    yield candidate
    parsed = urlparse(candidate)
    lowered = candidate.lower()
    if parsed.netloc == "hal.science" and "/document" not in parsed.path:
        yield candidate.rstrip("/") + "/document"
    if "doi.org" in parsed.netloc:
        yield from html_pdf_candidates(candidate)
    if "research-collection.ethz.ch" in parsed.netloc and "/bitstreams/" not in parsed.path:
        yield from html_pdf_candidates(candidate)
    if "upcommons.upc.edu" in parsed.netloc and "/bitstreams/" not in parsed.path:
        yield from html_pdf_candidates(candidate)
    if lowered.endswith("/abs") and "arxiv.org" in parsed.netloc:
        paper_id = parsed.path.rsplit("/", 1)[-1]
        yield f"https://arxiv.org/pdf/{paper_id}.pdf"


def iter_candidate_urls(entry: BibEntry) -> Iterator[tuple[str, str]]:
    seen: set[str] = set()

    def emit(url: str | None, note: str) -> Iterator[tuple[str, str]]:
        if not url:
            return
        for expanded_url in expand_candidate_url(url):
            if expanded_url and expanded_url not in seen:
                seen.add(expanded_url)
                yield expanded_url, note

    manual_override = MANUAL_PDF_SOURCES.get(entry.key)
    if manual_override:
        yield from emit(manual_override.get("pdf_url"), manual_override["source_note"])

    record = fetch_openalex_record(entry.doi)
    if record:
        primary_location = record.get("primary_location") or {}
        yield from emit(primary_location.get("pdf_url"), "OpenAlex primary PDF")

        open_access = record.get("open_access") or {}
        yield from emit(open_access.get("oa_url"), "OpenAlex OA URL")

        best_oa_location = record.get("best_oa_location") or {}
        yield from emit(best_oa_location.get("pdf_url"), "OpenAlex best OA PDF")
        yield from emit(best_oa_location.get("landing_page_url"), "OpenAlex best OA landing page")

        for location in record.get("locations") or []:
            yield from emit(location.get("pdf_url"), "OpenAlex location PDF")
            yield from emit(location.get("landing_page_url"), "OpenAlex location landing page")

    if entry.url:
        yield from emit(entry.url, "BibTeX URL")


def download_pdf(url: str, destination: Path) -> tuple[bool, str]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=destination.parent, delete=False) as temp_file:
        temp_path = Path(temp_file.name)
    curl_command = [
        "curl",
        "--location",
        "--silent",
        "--show-error",
        "--fail",
        "--connect-timeout",
        "20",
        "--max-time",
        "120",
        "--user-agent",
        USER_AGENT,
        "--header",
        "Accept: application/pdf,text/html,application/json;q=0.9,*/*;q=0.8",
        "--output",
        str(temp_path),
        "--write-out",
        "%{url_effective}",
        url,
    ]
    try:
        result = subprocess.run(
            curl_command,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        temp_path.unlink(missing_ok=True)
        error_text = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        return False, error_text

    payload = temp_path.read_bytes()
    if not payload.startswith(b"%PDF"):
        temp_path.unlink(missing_ok=True)
        return False, "Downloaded file did not start with a PDF header"

    temp_path.replace(destination)
    return True, result.stdout.strip() or url


def is_valid_pdf(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return False
    try:
        return path.read_bytes().startswith(b"%PDF")
    except OSError:
        return False


def build_manifest(
    entries: list[BibEntry],
    output_dir: Path,
) -> list[dict[str, str | bool | None]]:
    manifest_entries: list[dict[str, str | bool | None]] = []
    for entry in entries:
        print(f"Processing {entry.key}...", flush=True)
        local_relpath = Path("informe") / "bibliografia" / "papers" / f"{entry.key}.pdf"
        manifest_record: dict[str, str | bool | None] = {
            "key": entry.key,
            "entry_type": entry.entry_type,
            "title": entry.title,
            "year": entry.year,
            "doi": entry.doi or None,
            "url": entry.url or None,
            "is_academic_paper": entry.is_academic_paper,
            "local_pdf": str(local_relpath) if entry.is_academic_paper else None,
            "status": None,
            "source_url": None,
            "source_note": None,
            "error": None,
        }

        if not entry.is_academic_paper:
            manifest_record["status"] = "web_reference"
            manifest_entries.append(manifest_record)
            continue

        destination = output_dir / f"{entry.key}.pdf"
        success = False
        last_error: str | None = None
        for candidate_url, candidate_note in iter_candidate_urls(entry):
            ok, detail = download_pdf(candidate_url, destination)
            if ok:
                manifest_record["status"] = "downloaded"
                manifest_record["source_url"] = detail
                manifest_record["source_note"] = candidate_note
                success = True
                break
            last_error = detail
        if not success:
            if is_valid_pdf(destination):
                manifest_record["status"] = "downloaded"
                manifest_record["source_note"] = "Existing local copy"
            else:
                manifest_record["status"] = "missing_pdf"
                manifest_record["error"] = last_error or "No downloadable PDF source was resolved"
        manifest_entries.append(manifest_record)
    return manifest_entries


def write_manifest(manifest_path: Path, entries: list[dict[str, str | bool | None]]) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "source_bib": "informe/bibliography.bib",
        "papers_dir": "informe/bibliografia/papers",
        "downloaded_count": sum(1 for entry in entries if entry["status"] == "downloaded"),
        "missing_count": sum(1 for entry in entries if entry["status"] == "missing_pdf"),
        "web_reference_count": sum(1 for entry in entries if entry["status"] == "web_reference"),
        "entries": entries,
    }
    manifest_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bib", type=Path, default=DEFAULT_BIB_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    entries = parse_bibtex(args.bib.read_text())
    manifest_entries = build_manifest(entries, output_dir=args.output_dir)
    write_manifest(args.manifest, manifest_entries)

    downloaded = [entry["key"] for entry in manifest_entries if entry["status"] == "downloaded"]
    missing = [entry["key"] for entry in manifest_entries if entry["status"] == "missing_pdf"]
    web_refs = [entry["key"] for entry in manifest_entries if entry["status"] == "web_reference"]

    print(f"Downloaded PDFs: {len(downloaded)}")
    if downloaded:
        print("  " + ", ".join(downloaded))
    print(f"Web references: {len(web_refs)}")
    if web_refs:
        print("  " + ", ".join(web_refs))
    print(f"Missing PDFs: {len(missing)}")
    if missing:
        print("  " + ", ".join(missing))

    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())

"""Safe text extraction for upload -> sentinel-ml enrichment.

The extractor treats every upload as untrusted input. It never executes macros,
renders documents, follows links, or shells out to desktop tooling. For the
Office Open XML formats it only reads ZIP members and XML text nodes.
"""

from __future__ import annotations

import csv
import io
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET


MAX_EXTRACTED_TEXT_CHARS = 10_000
MAX_ZIP_ENTRIES = 200
MAX_UNCOMPRESSED_BYTES = 5_000_000
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


TEXT_PLAIN_TYPES = {
    "text/plain",
    "text/markdown",
    "text/csv",
}

DOCX_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
PPTX_TYPE = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


@dataclass(frozen=True)
class ExtractedText:
    text: str
    truncated: bool
    extractor: str


def extract_text(filename: str, content_type: str, content: bytes) -> ExtractedText | None:
    """Return extracted text for supported upload types, otherwise None.

    Supported now:
    - txt / md / csv
    - docx / xlsx / pptx
    """
    ext = Path(filename).suffix.lower()
    ctype = (content_type or "").strip().lower()

    if ctype in TEXT_PLAIN_TYPES or ext in {".txt", ".md", ".csv"}:
        return _extract_plain_text(ext, content)
    if ctype == DOCX_TYPE or ext == ".docx":
        return _extract_docx(content)
    if ctype == XLSX_TYPE or ext == ".xlsx":
        return _extract_xlsx(content)
    if ctype == PPTX_TYPE or ext == ".pptx":
        return _extract_pptx(content)
    return None


def _extract_plain_text(ext: str, content: bytes) -> ExtractedText:
    raw = content.decode("utf-8", errors="replace")
    if ext == ".csv":
        reader = csv.reader(io.StringIO(raw))
        rows = []
        for idx, row in enumerate(reader):
            rows.append(", ".join(cell.strip() for cell in row))
            if idx >= 200:
                break
        raw = "\n".join(rows)
    return _finalize(raw, extractor="plain")


def _extract_docx(content: bytes) -> ExtractedText | None:
    xml = _read_zip_member(content, "word/document.xml")
    if xml is None:
        return None
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return None
    parts = [node.text or "" for node in root.iter() if node.tag.endswith("}t")]
    return _finalize("\n".join(_nonempty(parts)), extractor="docx")


def _extract_xlsx(content: bytes) -> ExtractedText | None:
    xml_members = _read_zip_xml_members(content, prefix="xl/")
    if xml_members is None:
        return None
    parts: list[str] = []
    for xml in xml_members:
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            continue
        for node in root.iter():
            # Enough for a safe first pass: shared strings, inline text and
            # cell values. Exact spreadsheet structure can be refined later.
            if node.tag.endswith("}t") or node.tag.endswith("}v"):
                value = (node.text or "").strip()
                if value:
                    parts.append(value)
    return _finalize("\n".join(parts), extractor="xlsx")


def _extract_pptx(content: bytes) -> ExtractedText | None:
    xml_members = _read_zip_xml_members(content, prefix="ppt/slides/")
    if xml_members is None:
        return None
    parts: list[str] = []
    for xml in xml_members:
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            continue
        parts.extend((node.text or "") for node in root.iter() if node.tag.endswith("}t"))
    return _finalize("\n".join(_nonempty(parts)), extractor="pptx")


def _read_zip_member(content: bytes, member_name: str) -> bytes | None:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            if not _zip_is_safe(zf):
                return None
            try:
                return zf.read(member_name)
            except KeyError:
                return None
    except zipfile.BadZipFile:
        return None


def _read_zip_xml_members(content: bytes, prefix: str) -> list[bytes] | None:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            if not _zip_is_safe(zf):
                return None
            members = [
                name
                for name in zf.namelist()
                if name.startswith(prefix) and name.endswith(".xml")
            ]
            return [zf.read(name) for name in members]
    except zipfile.BadZipFile:
        return None


def _zip_is_safe(zf: zipfile.ZipFile) -> bool:
    infos = zf.infolist()
    if len(infos) > MAX_ZIP_ENTRIES:
        return False
    total_size = sum(info.file_size for info in infos)
    return total_size <= MAX_UNCOMPRESSED_BYTES


def _finalize(text: str, extractor: str) -> ExtractedText:
    cleaned = _CONTROL_CHAR_RE.sub("", text).replace("\r\n", "\n").replace("\r", "\n")
    cleaned = cleaned.strip()
    truncated = len(cleaned) > MAX_EXTRACTED_TEXT_CHARS
    return ExtractedText(
        text=cleaned[:MAX_EXTRACTED_TEXT_CHARS],
        truncated=truncated,
        extractor=extractor,
    )


def _nonempty(values: list[str]) -> list[str]:
    return [value.strip() for value in values if value and value.strip()]

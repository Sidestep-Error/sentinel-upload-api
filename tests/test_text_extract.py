from __future__ import annotations

import io
import zipfile

from app.services.text_extract import extract_text


DOCX_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
XLSX_CT = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
PPTX_CT = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


def _zip_bytes(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


def test_extract_text_returns_none_for_unsupported_type():
    assert extract_text("image.png", "image/png", b"png") is None


def test_extract_text_supports_txt():
    result = extract_text("note.txt", "text/plain", b"hello\nindicator.example")
    assert result is not None
    assert result.extractor == "plain"
    assert "indicator.example" in result.text


def test_extract_text_supports_csv():
    result = extract_text("data.csv", "text/csv", b"name,url\nalice,http://evil.example")
    assert result is not None
    assert result.extractor == "plain"
    assert "alice, http://evil.example" in result.text


def test_extract_text_supports_docx():
    content = _zip_bytes(
        {
            "word/document.xml": (
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                "<w:body><w:p><w:r><w:t>Hello DOCX</w:t></w:r></w:p></w:body></w:document>"
            )
        }
    )
    result = extract_text("report.docx", DOCX_CT, content)
    assert result is not None
    assert result.extractor == "docx"
    assert "Hello DOCX" in result.text


def test_extract_text_supports_xlsx():
    content = _zip_bytes(
        {
            "xl/workbook.xml": '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"/>',
            "xl/worksheets/sheet1.xml": (
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                "<sheetData><row><c><v>Invoice 123</v></c></row></sheetData></worksheet>"
            ),
        }
    )
    result = extract_text("report.xlsx", XLSX_CT, content)
    assert result is not None
    assert result.extractor == "xlsx"
    assert "Invoice 123" in result.text


def test_extract_text_supports_pptx():
    content = _zip_bytes(
        {
            "ppt/slides/slide1.xml": (
                '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
                'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
                "<p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>Hello PPTX</a:t></a:r></a:p>"
                "</p:txBody></p:sp></p:spTree></p:cSld></p:sld>"
            )
        }
    )
    result = extract_text("slides.pptx", PPTX_CT, content)
    assert result is not None
    assert result.extractor == "pptx"
    assert "Hello PPTX" in result.text


def test_extract_text_rejects_zip_with_too_many_entries(monkeypatch):
    from app.services import text_extract

    content = _zip_bytes({f"ppt/slides/{idx}.xml": "<x/>" for idx in range(3)})
    monkeypatch.setattr(text_extract, "MAX_ZIP_ENTRIES", 2)
    assert extract_text("slides.pptx", PPTX_CT, content) is None

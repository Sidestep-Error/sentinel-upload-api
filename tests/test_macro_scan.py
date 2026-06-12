"""Tests for static VBA-macro analysis and its effect on risk scoring."""

import io
import zipfile

from app.main import compute_risk
from app.services.macro_scan import analyze_macros

XLSX_CT = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _minimal_xlsx_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>',
        )
        z.writestr("xl/workbook.xml", "<workbook/>")
    return buf.getvalue()


def test_analyze_macros_skips_non_office_types():
    assert analyze_macros("a.txt", "text/plain", b"hello") is None
    assert analyze_macros("a.pdf", "application/pdf", b"%PDF-1.4") is None


def test_analyze_macros_macro_free_xlsx():
    result = analyze_macros("clean.xlsx", XLSX_CT, _minimal_xlsx_bytes())
    assert result == {
        "has_macros": False,
        "autoexec_keywords": 0,
        "suspicious_keywords": 0,
        "ioc_count": 0,
    }


def test_analyze_macros_unparseable_office_bytes_returns_none():
    # olevba falls back to "Text" mode for unrecognized bytes and would
    # otherwise report has_macros=True for any corrupt upload.
    assert analyze_macros("bad.xls", "application/vnd.ms-excel", b"not an ole file") is None


def _risk(macro: dict | None) -> tuple[int, str, list[str]]:
    return compute_risk(
        filename="report.xlsx",
        content=b"x" * 100,
        scan_status="clean",
        scan_engine="clamav",
        scan_detail="No signature matched",
        macro=macro,
    )


def test_compute_risk_without_macro_unchanged():
    score, decision, reasons = _risk(None)
    assert score < 30
    assert decision == "accepted"


def test_compute_risk_plain_macro_goes_to_review():
    score, decision, reasons = _risk(
        {"has_macros": True, "autoexec_keywords": 0, "suspicious_keywords": 0}
    )
    assert score >= 30
    assert decision == "review"
    assert any("VBA" in r for r in reasons)


def test_compute_risk_autoexec_plus_suspicious_rejected():
    score, decision, reasons = _risk(
        {"has_macros": True, "autoexec_keywords": 2, "suspicious_keywords": 5}
    )
    assert score >= 70
    assert decision == "rejected"
    assert any("auto-execution" in r for r in reasons)


def test_compute_risk_many_suspicious_goes_to_review():
    score, decision, _ = _risk(
        {"has_macros": True, "autoexec_keywords": 0, "suspicious_keywords": 4}
    )
    assert 30 <= score < 70
    assert decision == "review"


def test_upload_with_risky_macro_is_rejected(client, monkeypatch):
    def fake_analyze(_filename, _content_type, _content):
        return {"has_macros": True, "autoexec_keywords": 1, "suspicious_keywords": 3}

    monkeypatch.setattr("app.main.analyze_macros", fake_analyze)
    files = {"file": ("quarterly.xlsx", _minimal_xlsx_bytes(), XLSX_CT)}
    r = client.post("/upload", files=files)
    assert r.status_code == 200
    body = r.json()
    assert body["decision"] == "rejected"
    assert body["risk_score"] >= 70
    assert any("auto-execution" in reason for reason in body["risk_reasons"])
    assert body["macro"]["has_macros"] is True


def test_upload_macro_free_office_file_unaffected(client):
    files = {"file": ("clean.xlsx", _minimal_xlsx_bytes(), XLSX_CT)}
    r = client.post("/upload", files=files)
    assert r.status_code == 200
    body = r.json()
    assert body["decision"] == "accepted"
    assert body["macro"] == {
        "has_macros": False,
        "autoexec_keywords": 0,
        "suspicious_keywords": 0,
        "ioc_count": 0,
    }

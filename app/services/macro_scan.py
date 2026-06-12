"""Static VBA-macro analysis for Office uploads (oletools/olevba).

Runs in the upload path right after the antivirus scan — this service already
holds the file bytes, so content inspection belongs here. Only aggregated
counts leave the process (stored on the upload record and forwarded to
sentinel-ml); macro source code is never logged or persisted.

Fail-safe by design: unsupported types return None and any parser error
returns None, so the upload flow continues without macro features.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("sentinel")

# Content types that can carry VBA macros and that olevba can parse.
# OpenDocument (odt/ods/odp) uses Basic, not VBA — olevba does not cover it.
MACRO_CAPABLE_CONTENT_TYPES = {
    "application/msword",
    "application/vnd.ms-excel",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}


def analyze_macros(filename: str, content_type: str, content: bytes) -> dict | None:
    """Return macro feature counts for Office files, None otherwise.

    The returned shape matches sentinel-ml's ``MacroAnalysis`` schema:
    ``has_macros``, ``autoexec_keywords``, ``suspicious_keywords``,
    ``ioc_count``.
    """
    if content_type not in MACRO_CAPABLE_CONTENT_TYPES:
        return None
    try:
        # Local import: oletools pulls in a parser stack we only want loaded
        # (and only exercised) for macro-capable uploads.
        from oletools.olevba import VBA_Parser

        parser = VBA_Parser(filename, data=content)
        try:
            # olevba falls back to "Text" mode for bytes it cannot parse as an
            # Office container and then treats the whole content as macro
            # source — that would mislabel every corrupt upload as macro-
            # bearing. Only trust real container types (OLE/OpenXML/...).
            if parser.type == "Text":
                return None
            if not parser.detect_vba_macros():
                return {
                    "has_macros": False,
                    "autoexec_keywords": 0,
                    "suspicious_keywords": 0,
                    "ioc_count": 0,
                }
            autoexec = suspicious = iocs = 0
            for kw_type, _keyword, _description in parser.analyze_macros():
                if kw_type == "AutoExec":
                    autoexec += 1
                elif kw_type == "Suspicious":
                    suspicious += 1
                elif kw_type == "IOC":
                    iocs += 1
            return {
                "has_macros": True,
                "autoexec_keywords": autoexec,
                "suspicious_keywords": suspicious,
                "ioc_count": iocs,
            }
        finally:
            parser.close()
    except Exception:
        logger.warning(
            "Macro analysis failed for %s — continuing without macro features",
            filename,
            exc_info=True,
        )
        return None

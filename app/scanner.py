from dataclasses import dataclass


EICAR_MARKER = b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE"


@dataclass
class ScanResult:
    status: str
    engine: str
    detail: str


def scan_bytes(filename: str, content: bytes) -> ScanResult:
    """Mock scanner used until ClamAV integration is in place."""
    lowered = filename.lower()
    if EICAR_MARKER in content:
        return ScanResult(
            status="malicious",
            engine="mock",
            detail="EICAR test signature detected",
        )
    if "malicious" in lowered or "eicar" in lowered:
        return ScanResult(
            status="malicious",
            engine="mock",
            detail="Filename pattern flagged by mock policy",
        )
    return ScanResult(status="clean", engine="mock", detail="No signature matched")

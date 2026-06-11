"""Security response headers (set by middleware in app.main).

The headers must come from the app itself: in prod (k3s ingress -> uvicorn)
and on Render there is no nginx in front to add them.
"""


def test_security_headers_present(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "camera=()" in response.headers["Permissions-Policy"]
    # Deprecated header must stay gone (removed 2026-06; can cause more harm
    # than good in older browsers).
    assert "X-XSS-Protection" not in response.headers


def test_csp_on_ui_routes(client):
    response = client.get("/")
    csp = response.headers["Content-Security-Policy"]
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    # The UI script is external (/static/app.js); inline scripts stay blocked.
    assert "unsafe-inline" not in csp


def test_csp_exempt_for_api_docs(client):
    # Swagger UI loads assets from a CDN the UI policy does not allow.
    response = client.get("/docs")
    assert response.status_code == 200
    assert "Content-Security-Policy" not in response.headers
    # The other security headers still apply.
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_headers_on_static_files(client):
    response = client.get("/static/app.js")
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "Content-Security-Policy" in response.headers

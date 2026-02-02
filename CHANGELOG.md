# CHANGELOG

## 2026-02-02

- Identified a UI bug where the file picker could open twice for some users.
- Patched `app/static/index.html` to prevent double-trigger from dropzone/label clicks.
- Added safer file input handling so the same file can be selected again after upload.

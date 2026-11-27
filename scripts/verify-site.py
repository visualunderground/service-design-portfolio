"""Verify built pages, local links and media without any external service."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote, urljoin
import hashlib

root = Path("dist")
base = "/service-design-portfolio/"
origin = "https://visualunderground.github.io"
pages = sorted(root.rglob("*.html"))
errors = []
targets = set()
external = set()
images = set()
pdfs = set()
class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
        self.ids = set()
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        for key in ("href", "src", "poster"):
            if a.get(key):
                self.refs.append((tag, a[key]))
parsed = {}
for page in pages:
    p = Page()
    p.feed(page.read_text())
    parsed[page] = p
for page, parser in parsed.items():
    relative = page.relative_to(root).as_posix()
    route = base + relative.removesuffix("index.html")
    for tag, ref in parser.refs:
        url = urlsplit(urljoin(origin + route, ref))
        if url.scheme not in ("http", "https"):
            continue
        host = url.hostname or ""
        if host in ("super.so", "super.site", "notion.so", "notion.site") or host.endswith((".super.so", ".super.site", ".notion.so", ".notion.site")):
            errors.append(f"Legacy platform: {relative}: {ref}")
        if host != "visualunderground.github.io":
            external.add(host)
            continue
        if not url.path.startswith(base):
            errors.append(f"Outside site: {relative}: {ref}")
            continue
        path = root / unquote(url.path[len(base):])
        if path.is_dir():
            path /= "index.html"
        elif not path.exists() and (path / "index.html").exists():
            path /= "index.html"
        if not path.is_file() or not path.stat().st_size:
            errors.append(f"Missing target: {relative}: {ref}")
            continue
        targets.add(path)
        if tag == "img":
            images.add(path)
        if path.suffix.lower() == ".pdf":
            pdfs.add(path)
            if not path.read_bytes().startswith(b"%PDF-"):
                errors.append(f"Invalid PDF: {path}")
        if url.fragment and path in parsed and unquote(url.fragment) not in parsed[path].ids:
            errors.append(f"Missing fragment: {relative}: {ref}")
assets = [p for p in Path("public/assets").rglob("*") if p.is_file()]
for p in assets:
    target = root / p.relative_to("public")
    if not target.is_file() or hashlib.sha256(p.read_bytes()).digest() != hashlib.sha256(target.read_bytes()).digest():
        errors.append(f"Asset differs from source: {p}")
print(f"Pages: {len(pages)}; unique local targets: {len(targets)}; rendered images: {len(images)}; linked PDFs: {len(pdfs)}; copied assets: {len(assets)}")
print("External hosts (not checked): " + ", ".join(sorted(external)))
for error in errors:
    print(error)
if errors:
    raise SystemExit(1)
print("All local targets and copied assets passed.")

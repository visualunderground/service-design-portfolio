"""Archive only assets matched to existing case-study references on the public Super site."""
import collections
import html
import json
import pathlib
import re
import sys
import urllib.parse as u
import urllib.request as req
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = "https://tomcarrington.super.site/"
CDN = "assets.super.so"
SITE_ID = "5a468d72-dc70-4542-bbd5-f06872521400"
known = json.loads((ROOT / "src/images.json").read_text())
refs = json.loads((ROOT / "reference/core-assets.json").read_text())
refs += json.loads((ROOT / "reference/attachment-assets.json").read_text())
groups = collections.defaultdict(list)
for item in refs:
    if item["sourceFile"].startswith("content/projects/") and item["kind"] != "project-cover" and item["filename"] not in known:
        groups[item["sourceFile"]].append(item)

def fetch(url):
    request = req.Request(url, headers={"User-Agent": "Mozilla/5.0 portfolio migration"})
    with req.urlopen(request, timeout=35) as response:
        return response.read(95 * 1024 * 1024 + 1), response.headers.get_content_type()

def cdn_url(value):
    value = html.unescape(str(value)).strip()
    if value.startswith("//"):
        value = "https:" + value
    p = u.urlsplit(value)
    if p.path.endswith("/_next/image") or p.path.endswith("/image"):
        nested = u.parse_qs(p.query).get("url", [""])[0]
        if nested:
            return cdn_url(nested)
    if p.scheme == "https" and p.hostname == CDN and p.path.startswith("/" + SITE_ID + "/"):
        return u.urlunsplit((p.scheme, p.netloc, p.path, "", ""))
    return None

def candidates(node):
    out = set()
    for tag in [node, *node.find_all(["img", "source", "a", "video", "object", "embed"])]:
        for attr in ("src", "href", "data-src", "data", "poster", "data-original", "srcset"):
            val = tag.get(attr)
            if not val:
                continue
            vals = [v.strip().split()[0] for v in val.split(",") if v.strip()] if attr == "srcset" else [val]
            for value in vals:
                url = cdn_url(value)
                if url:
                    out.add(url)
    return out

def filename(url):
    return u.unquote(u.urlsplit(url).path.rsplit("/", 1)[-1])

def normalized(value):
    return re.sub(r"[^a-z0-9]", "", str(value).lower())

def matches_type(url, item):
    ext = pathlib.Path(filename(url)).suffix.lower()
    if item["kind"] == "attachment":
        return ext == ".pdf"
    return ext in {".png", ".jpeg", ".jpg", ".gif", ".webp", ".svg", ".avif"}

def valid(data, mime, item):
    if not data or len(data) > 95 * 1024 * 1024:
        return False
    ext = pathlib.Path(item["filename"]).suffix.lower()
    if ext == ".pdf":
        return data.startswith(b"%PDF-")
    if ext == ".png":
        return data.startswith(b"\x89PNG\r\n\x1a\n")
    if ext in (".jpg", ".jpeg"):
        return data.startswith(b"\xff\xd8\xff")
    if ext == ".gif":
        return data.startswith((b"GIF87a", b"GIF89a"))
    if ext == ".svg":
        return mime == "image/svg+xml" and b"<svg" in data[:4096]
    if ext == ".webp":
        return data.startswith(b"RIFF") and data[8:12] == b"WEBP"
    return False

results = []
for source, items in groups.items():
    slug = pathlib.Path(source).stem
    soup = None
    for route in (slug, "projects/" + slug):
        try:
            data, mime = fetch(SITE + route)
            if mime == "text/html":
                candidate = BeautifulSoup(data, "html.parser")
                if candidate.title and candidate.find_all(["img", "a"]):
                    soup = candidate
                    break
        except Exception as exc:
            print(f"Page {route}: {type(exc).__name__}", flush=True)
    if soup is None:
        for item in items:
            results.append({"path": item["path"], "status": "page-unavailable"})
        continue
    page_urls = candidates(soup)
    print(f"{slug}: {len(page_urls)} public CDN candidates", flush=True)
    name_counts = collections.Counter(normalized(x["filename"]) for x in items)
    for item in items:
        path = item["path"]
        dst = ROOT / "public" / path.lstrip("/")
        if dst.is_file() and dst.stat().st_size:
            results.append({"path": path, "status": "already-archived"})
            continue
        ref = item.get("notionReference", "")
        block_id = ref.split("://")[-1].split("/")[0]
        asset_id = path.split("/")[2]
        ids = {normalized(block_id), normalized(asset_id)} - {""}
        matches = set()
        for tag in soup.find_all(True):
            attrs = [tag.get(k, "") for k in ("id", "data-block-id", "data-notion-block-id", "class")]
            if any(x in normalized(v) for x in ids for v in attrs):
                matches.update(candidates(tag))
        matches = {url for url in matches if matches_type(url, item)}
        exact = {url for url in matches if normalized(filename(url)) == normalized(item["filename"])}
        if len(exact) == 1:
            matches = exact
        if not matches:
            exact = {url for url in page_urls if matches_type(url, item) and normalized(filename(url)) == normalized(item["filename"])}
            if len(exact) == 1 and name_counts[normalized(item["filename"])] == 1:
                matches = exact
        if len(matches) != 1:
            results.append({"path": path, "status": "unmatched" if not matches else "ambiguous", "candidates": len(matches)})
            continue
        url = next(iter(matches))
        try:
            data, mime = fetch(url)
            if not valid(data, mime, item):
                results.append({"path": path, "status": "invalid-file"})
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(data)
            results.append({"path": path, "status": "archived", "bytes": len(data)})
        except Exception as exc:
            results.append({"path": path, "status": "download-failed", "error": type(exc).__name__})

for result in results:
    print(json.dumps(result), flush=True)
counts = collections.Counter(x["status"] for x in results)
print("Recovery summary: " + json.dumps(counts), flush=True)

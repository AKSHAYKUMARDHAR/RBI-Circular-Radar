"""Download the RBI notification PDFs listed in data/documents.json and check each one's SHA-256.

    python -m scripts.fetch_documents                 # fetch what's missing into data/pdfs/, verify all
    python -m scripts.fetch_documents --from-sample   # (maintainer) build the manifest from data/sample.json
    python -m scripts.fetch_documents --freeze        # (maintainer) write hashes and page counts into the manifest

The PDFs are RBI's own, fetched from rbidocs.rbi.org.in rather than redistributed here. A hash mismatch
means RBI changed the file; the evaluation results apply to the hashed version only.
"""
import argparse
import hashlib
import json
import os
import pathlib
import sys
import time

import httpx

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "data" / "documents.json"
PDFS = ROOT / "data" / "pdfs"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/130.0 Safari/537.36 rbi-circular-radar/1.0"}


def save(manifest: dict) -> None:
    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")


def from_sample() -> None:
    sample = json.loads((ROOT / "data" / "sample.json").read_text(encoding="utf-8"))
    docs = [{"id": f"R{d['id']}", "split": d["split"], "tag": d["tag"], "title": d["title"], "rbi_no": d["rbi_no"],
             "date": d["date"], "url": d["url"], "pdf_url": d["pdf"]} for d in sample["documents"]]
    save({"note": "RBI notifications from 1 April to 7 October 2026, drawn from the full population by "
                  "scripts/draw_sample.py (seed in data/sample.json) and frozen before any prompt or label existed. "
                  "dev = used to build the reader; holdout = labelled before any prompt and run once for the release gate.",
          "documents": docs})
    print(f"{len(docs)} documents written to {MANIFEST}")


def fetch(doc: dict) -> pathlib.Path:
    path = PDFS / f"{doc['id']}.pdf"
    if not path.exists():
        r = httpx.get(doc["pdf_url"], follow_redirects=True, timeout=float(os.getenv("FETCH_TIMEOUT", "120")), headers=UA)
        r.raise_for_status()
        if not r.content.startswith(b"%PDF"):
            raise ValueError(f"{doc['id']}: the URL did not return a PDF")
        path.write_bytes(r.content)
        time.sleep(1.0)   # be polite to RBI's servers
    return path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--from-sample", action="store_true")
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    if args.from_sample:
        from_sample()
    PDFS.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    bad = 0
    for doc in manifest["documents"]:
        try:
            path = fetch(doc)
        except (httpx.HTTPError, ValueError) as e:
            print(f"  {doc['id']}: download failed: {e}")
            bad += 1
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if args.freeze or args.from_sample:
            from pypdf import PdfReader
            doc["sha256"], doc["pages"] = digest, len(PdfReader(str(path)).pages)
        elif digest != doc.get("sha256"):
            print(f"  {doc['id']}: hash differs from the frozen version (RBI may have updated the file)")
            bad += 1
            continue
        print(f"  {doc['id']}: ok ({doc['split']}, {doc.get('pages', '?')} pages)")
    if args.freeze or args.from_sample:
        save(manifest)
    print(f"{len(manifest['documents']) - bad}/{len(manifest['documents'])} documents ready in {PDFS}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

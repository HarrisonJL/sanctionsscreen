"""
Captures the two OFAC files the contract reads, byte for byte as served, and
writes them gzipped (so the repo stays small) with tests/fixtures/manifest.json
(URL, HTTP status, Last-Modified, SHA-256 and size of the *uncompressed* bytes -
the same SHA-256 the contract records on-chain with every verdict).

Run from the repo root:   python3 scripts/capture_fixtures.py
Source: OFAC's publication service, sanctionslistservice.ofac.treas.gov.
"""

import gzip
import hashlib
import json
import pathlib
import sys
import urllib.request

OUT = pathlib.Path(__file__).resolve().parent.parent / "tests" / "fixtures"
FILES = {
    "sdn": "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.CSV",
    "alt": "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/ALT.CSV",
}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, url in FILES.items():
        req = urllib.request.Request(url, headers={"user-agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as r:
            body, status, modified = r.read(), r.status, r.headers.get("Last-Modified", "")
        (OUT / f"{name}.csv.gz").write_bytes(gzip.compress(body, 9, mtime=0))
        manifest[name] = {"url": url, "status": status, "last_modified": modified, "bytes": len(body),
                          "sha256": hashlib.sha256(body).hexdigest()}
        print(f"{status} {len(body):>8} {modified}  {name}  {manifest[name]['sha256'][:16]}")
    (OUT / "manifest.json").write_text(json.dumps({"captured": "2026-10-11", "fixtures": manifest}, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

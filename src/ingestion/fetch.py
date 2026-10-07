import sys
from pathlib import Path
from typing import Optional
import requests

PEP_NUMBERS = [
    483, 484, 526,
    544,
    563, 649, 749,
    585, 604, 612, 646, 695, 696,
    677,
    589, 655, 692, 705,
    647, 724, 742,
    586, 591, 673, 698,
]

GITHUB_RAW_BASE = "https://raw.githubusercontent.com/python/peps/main/peps"
OUTPUT_DIR = Path("data/raw")
TIMEOUT = 30


def fetch_pep(pep_num: int) -> Optional[str]:
    url = f"{GITHUB_RAW_BASE}/pep-{pep_num:04d}.rst"
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        if resp.status_code == 200:
            return resp.text
        print(f"PEP {pep_num}: HTTP {resp.status_code}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"PEP {pep_num}: {e}", file=sys.stderr)
        return None


def save_pep(pep_num: int, content: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"pep-{pep_num:04d}.rst"
    path.write_text(content, encoding="utf-8")
    print(f"Saved {path}")


def main() -> int:
    print(f"Fetching {len(PEP_NUMBERS)} PEPs from {GITHUB_RAW_BASE}")
    success = 0
    for num in PEP_NUMBERS:
        content = fetch_pep(num)
        if content:
            save_pep(num, content)
            success += 1
    print(f"Fetched {success}/{len(PEP_NUMBERS)} PEPs")
    return 0 if success == len(PEP_NUMBERS) else 1


if __name__ == "__main__":
    sys.exit(main())
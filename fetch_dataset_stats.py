# La Canasta: how many people view and download the open dataset on Kaggle and Zenodo.
# Runs once a day (.github/workflows/datos-stats.yml) and writes index/datos-stats.json
# (latest numbers, read by admin.html) and adds a row to index/datos-stats.csv (history).
# Kaggle needs an API token in the repo secrets (KAGGLE_USERNAME + KAGGLE_KEY, or KAGGLE_API_TOKEN);
# without it, only Zenodo is filled in.

import csv
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

ZENODO_ID = "23856045"   # concept record: all versions of the dataset
KAGGLE_OWNER = "ramonpepa"
KAGGLE_SLUG = "la-canasta-daily-supermarket-prices"

out = {"updated": datetime.now(ZoneInfo("Europe/Madrid")).strftime("%Y-%m-%d %H:%M"),
       "zenodo": None, "kaggle": None, "errors": []}


def zenodo():
    rec = None
    r = requests.get(f"https://zenodo.org/api/records/{ZENODO_ID}", timeout=30)
    if r.ok:
        rec = r.json()
    else:
        r = requests.get("https://zenodo.org/api/records",
                         params={"q": f"conceptrecid:{ZENODO_ID}", "sort": "mostrecent"}, timeout=30)
        hits = r.json().get("hits", {}).get("hits", []) if r.ok else []
        rec = hits[0] if hits else None
    if not rec:
        raise RuntimeError(f"Zenodo record {ZENODO_ID} not found")
    s = rec.get("stats", {})
    s = s.get("all_versions", s)  # newer Zenodo: {"this_version": {...}, "all_versions": {...}}
    return {"views": s.get("unique_views", s.get("views")), "downloads": s.get("unique_downloads", s.get("downloads")),
            "url": f"https://doi.org/10.5281/zenodo.{ZENODO_ID}"}


def kaggle():
    if not (os.environ.get("KAGGLE_KEY") or os.environ.get("KAGGLE_API_TOKEN")):
        return None
    from kaggle.api.kaggle_api_extended import KaggleApi
    api = KaggleApi()
    api.authenticate()
    for d in api.dataset_list(user=KAGGLE_OWNER):
        ref = getattr(d, "ref", "") or ""
        if ref.endswith("/" + KAGGLE_SLUG):
            g = lambda *names: next((getattr(d, n) for n in names if getattr(d, n, None) is not None), None)
            return {"views": g("view_count", "viewCount"), "downloads": g("download_count", "downloadCount"),
                    "votes": g("vote_count", "voteCount"), "usability": g("usability_rating", "usabilityRating"),
                    "url": f"https://www.kaggle.com/datasets/{KAGGLE_OWNER}/{KAGGLE_SLUG}"}
    raise RuntimeError("Kaggle dataset not found in the list")


for name, fn in (("zenodo", zenodo), ("kaggle", kaggle)):
    try:
        out[name] = fn()
    except Exception as e:  # one site failing never stops the other
        out["errors"].append(f"{name}: {e}")

os.makedirs("index", exist_ok=True)
json.dump(out, open("index/datos-stats.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
path = "index/datos-stats.csv"
new = not os.path.exists(path)
with open(path, "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    if new:
        w.writerow(["date", "kaggle_views", "kaggle_downloads", "zenodo_views", "zenodo_downloads"])
    k, z = out["kaggle"] or {}, out["zenodo"] or {}
    w.writerow([out["updated"][:10], k.get("views", ""), k.get("downloads", ""), z.get("views", ""), z.get("downloads", "")])
print(json.dumps(out, ensure_ascii=False))

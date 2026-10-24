# La Canasta: downloads the government's daily supermarket price files
# (Precios Claros, called "SEPA") and saves each one on GitHub as a Release,
# so we never lose a day of prices.

import csv
import datetime
import os
import re
import subprocess
import requests

API = "https://datos.produccion.gob.ar/api/3/action/package_show?id=sepa-precios"
HEADERS = {"User-Agent": "La Canasta research project (github.com/ramonpepapolo-lang/la-canasta)"}


def already_saved(tag):
    result = subprocess.run(["gh", "release", "view", tag], capture_output=True)
    return result.returncode == 0


# 1. Ask the government website for the list of price files
info = requests.get(API, headers=HEADERS, timeout=60).json()
files = [r for r in info["result"]["resources"] if r["url"].lower().endswith(".zip")]
print(f"Found {len(files)} files")

for f in files:
    date = (f.get("last_modified") or f.get("created") or "")[:10]
    name = re.sub(r"[^a-z0-9]+", "-", f.get("name", "file").lower()).strip("-")
    tag = f"sepa-{date}-{name}"

    # 2. Skip files we already saved
    if already_saved(tag):
        print("Already saved:", tag)
        continue

    # 3. Download the file in small pieces (it's about 300 MB)
    print("Downloading:", tag)
    with requests.get(f["url"], headers=HEADERS, stream=True, timeout=900) as r:
        r.raise_for_status()
        with open("sepa.zip", "wb") as out:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                out.write(chunk)
    size_mb = round(os.path.getsize("sepa.zip") / 1_000_000)

    # 4. Save it on GitHub as a Release
    subprocess.run(["gh", "release", "create", tag, "sepa.zip",
                    "--title", f"SEPA prices {date} ({f.get('name')})",
                    "--notes", f"Source: {f['url']}"], check=True)
    os.remove("sepa.zip")

    # 5. Write one line in the log
    with open("download_log.csv", "a", newline="") as log:
        csv.writer(log).writerow([datetime.date.today(), date, f.get("name"), size_mb, tag])
    print("Saved:", tag, size_mb, "MB")

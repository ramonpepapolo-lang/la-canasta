# La Canasta: downloads the government's daily supermarket price files
# (Precios Claros, called "SEPA") and saves each one on GitHub as a Release,
# so we never lose a day of prices.

import csv
import datetime
import os
import re
import subprocess
import sys
import time
import requests

API = "https://datos.produccion.gob.ar/api/3/action/package_show?id=sepa-precios"

# Different "ID cards" to show the website. If one gets blocked, try the next.
USER_AGENTS = [
    "Java-http-client/21",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "curl/8.5.0",
]


def get_file_list():
    for ua in USER_AGENTS:
        for attempt in range(3):
            try:
                r = requests.get(API, headers={"User-Agent": ua}, timeout=30)
                print(f"Tried '{ua[:20]}...' attempt {attempt + 1}: status {r.status_code}")
                if r.status_code == 200 and r.text.strip().startswith("{"):
                    return r.json()["result"]["resources"], ua
                print("Got this instead of data:", r.text[:300].replace("\n", " "))
            except requests.RequestException as e:
                print("Connection problem:", e)
            time.sleep(10)
    sys.exit("Could not get the file list from the government site. See messages above.")


def already_saved(tag):
    result = subprocess.run(["gh", "release", "view", tag], capture_output=True)
    return result.returncode == 0


# 1. Ask the government website for the list of price files
resources, ua = get_file_list()
files = [r for r in resources
         if r.get("url") and (r["url"].lower().endswith(".zip") or str(r.get("format", "")).lower() == "zip")]
print(f"Found {len(files)} files")

for f in files:
    # The date is written in the description, e.g. "Precios SEPA Minoristas miercoles, 2026-09-23"
    found = re.search(r"\d{4}-\d{2}-\d{2}", f.get("description", "") or "")
    date = found.group(0) if found else (f.get("last_modified") or f.get("created") or "nodate")[:10]
    tag = f"sepa-{date}"

    # 2. Skip files we already saved
    if already_saved(tag):
        print("Already saved:", tag)
        continue

    # 3. Download the file in small pieces (it's about 300 MB)
    print("Downloading:", tag)
    with requests.get(f["url"], headers={"User-Agent": ua}, stream=True, timeout=900) as r:
        r.raise_for_status()
        with open("sepa.zip", "wb") as out:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                out.write(chunk)
    size_mb = round(os.path.getsize("sepa.zip") / 1_000_000)

    # 4. Save it on GitHub as a Release
    subprocess.run(["gh", "release", "create", tag, "sepa.zip",
                    "--title", f"SEPA prices {date}",
                    "--notes", f"{f.get('description', '')}\nSource: {f['url']}"], check=True)
    os.remove("sepa.zip")

    # 5. Write one line in the log
    with open("download_log.csv", "a", newline="") as log:
        csv.writer(log).writerow([datetime.date.today(), date, size_mb, tag])
    print("Saved:", tag, size_mb, "MB")

"""How far from the requested date is the capture that the archive serves?

wayback40_served.json comes from the Website Content Crawler run in ../wcc_wayback40_items_runmeta.json.
That run requested 40 Wikipedia articles at one fixed date, web.archive.org/web/20210601000000id_/<url>.
Usage: python archive_redirects.py
"""
import json
import re
from datetime import datetime

REQUESTED = datetime(2021, 6, 1)
rows = json.load(open("wayback40_served.json"))
days = []
for row in rows:
    served = re.search(r"/web/(\d{14})id_/", row["served"]).group(1)
    days.append((datetime.strptime(served, "%Y%m%d%H%M%S") - REQUESTED).days)
newer = [d for d in days if d > 0]
print(f"{len(rows)} requests: {len(newer)} served a newer capture, {sum(d < 0 for d in days)} an older one")
print(f"largest gap: {max(newer)} days newer ({max(newer) / 365.25:.1f} years)")

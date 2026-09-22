#!/usr/bin/env python3
"""Fetch HK recycling collection points from CSDI Geoportal → GeoJSON for the map.
Dataset: epd_rcd_1630899452408_9505 (EPD Waste Less - Recyclable Collection Points)
"""
import sys, json, time, urllib.request

DATASET_ID = "epd_rcd_1630899452408_9505"
BASE = f"https://portal.csdi.gov.hk/server/rest/services/common/{DATASET_ID}/FeatureServer/0/query"
UA = {"User-Agent": "Mozilla/5.0 (Recycling-Points-Map)"}
OUT = "recycling_data.json"

LEGEND_TC = {
    "Recycling Bins at Public Place": "公眾地方回收桶",
    "Private Collection Points": "私人收集點",
    "Smart Bin": "智能回收桶",
    "Recycling Spots": "回收點",
    "Street Corner Recycling Shops": "街角回收店",
    "Recycling Stations/Recycling Stores": "回收環保站",
}

def fetch_batch(offset, size=2000):
    """CSDI paginates with resultOffset; fetch one page of `size`."""
    where = "1%3D1"
    url = (f"{BASE}?where={where}&outFields=*&f=json&outSR=4326"
           f"&resultOffset={offset}&resultRecordCount={size}")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read())

def main():
    all_feats = []
    offset = 1
    while True:
        d = fetch_batch(offset)
        feats = d.get("features", [])
        print(f"fetched offset={offset} got={len(feats)}", file=sys.stderr)
        if not feats:
            break
        all_feats.extend(feats)
        offset += len(feats)
        if offset > 9000:  # safety cap
            break
        time.sleep(0.3)

    print(f"total raw features: {len(all_feats)}", file=sys.stderr)

    out_features = []
    seen = set()
    for f in all_feats:
        a = f.get("attributes", {})
        lat, lng = a.get("lat"), a.get("lgt")
        if not lat or not lng:
            continue
        legend = a.get("legend") or ""
        kind_tc = LEGEND_TC.get(legend, legend)
        out_features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [float(lng), float(lat)]},
            "properties": {
                "cp_id": a.get("cp_id"),
                "district": a.get("district_id"),
                "name_tc": a.get("address_tc") or a.get("address_en"),
                "name_en": a.get("address_en"),
                "address_tc": a.get("address_tc"),
                "address_en": a.get("address_en"),
                "waste_type": a.get("waste_type"),
                "legend": legend,
                "kind_tc": kind_tc,
                "openhour_tc": a.get("openhour_tc"),
                "contact_tc": a.get("contact_tc"),
                "access": a.get("accessibilty_notes"),
            },
        })

    geojson = {"type": "FeatureCollection", "features": out_features}
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(geojson, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"WROTE {len(out_features)} features to {OUT}", file=sys.stderr)

if __name__ == "__main__":
    main()
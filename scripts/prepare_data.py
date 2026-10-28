"""Turn the raw downloads into small, clean CSV files for the Vega-Lite charts.

Usage: python3 -I prepare_data.py <raw_dir> <out_dir> <natural_earth_geojson>
"""
import json
import sys
from pathlib import Path

import pandas as pd

RAW, OUT, NE = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
OUT.mkdir(parents=True, exist_ok=True)

STATE_NAMES = {"WA": "Western Australia", "NT": "Northern Territory", "SA": "South Australia",
               "QLD": "Queensland", "NSW": "New South Wales", "VIC": "Victoria",
               "TAS": "Tasmania", "ACT": "Australian Capital Territory"}
# Geoscience Australia, Area of Australia - States and Territories (km2)
LAND_KM2 = {"WA": 2527013, "QLD": 1729742, "NT": 1347791, "SA": 984321,
            "NSW": 801150, "VIC": 227444, "TAS": 68401, "ACT": 2358}

# ---------------- CAPAD 2024: national parks ----------------
capad = pd.read_csv(RAW / "Collaborative_Australian_Protected_Areas_Database_(CAPAD)_2024_-_Terrestrial__.csv",
                    low_memory=False)
is_np = capad.TYPE.isin(["National Park", "National Park (Commonwealth)"]) & (capad.OVERLAP == 1)
# Bimberi Wilderness Zone lies inside Namadgi National Park (ACT) but CAPAD types it separately.
is_bimberi = (capad.STATE == "ACT") & (capad.NAME == "Bimberi") & (capad.TYPE == "Wilderness Zone") & (capad.OVERLAP == 1)
nps = capad[is_np | is_bimberi].copy()
namadgi_id = nps.loc[nps.NAME == "Namadgi", "PA_ID"].iloc[0]
nps.loc[nps.NAME == "Bimberi", ["PA_ID", "NAME"]] = [namadgi_id, "Namadgi"]
nps = nps.sort_values("GIS_AREA", ascending=False)  # so "first" picks the main record's name
nps["w_lon"] = nps.LONGITUDE * nps.GIS_AREA
nps["w_lat"] = nps.LATITUDE * nps.GIS_AREA
parks = nps.groupby("PA_ID").agg(name=("NAME", "first"), state=("STATE", "first"), type=("TYPE", "first"),
                                 ha=("GIS_AREA", "sum"), w_lon=("w_lon", "sum"), w_lat=("w_lat", "sum")).reset_index()
parks["area_km2"] = (parks.ha / 100).round(2)
parks["lon"] = (parks.w_lon / parks.ha).round(4)
parks["lat"] = (parks.w_lat / parks.ha).round(4)
parks = parks[parks.state.isin(LAND_KM2)]  # drop external territories and Jervis Bay
parks["state_name"] = parks.state.map(STATE_NAMES)
parks = parks.sort_values("area_km2", ascending=False)
parks[["name", "state", "state_name", "area_km2", "lon", "lat"]].to_csv(OUT / "national_parks.csv", index=False)

by_state = parks.groupby("state").agg(parks=("name", "count"), np_km2=("area_km2", "sum")).reset_index()
by_state["land_km2"] = by_state.state.map(LAND_KM2)
by_state["pct_np"] = (by_state.np_km2 / by_state.land_km2 * 100).round(1)
by_state["np_km2"] = by_state.np_km2.round(0).astype(int)
by_state["state_name"] = by_state.state.map(STATE_NAMES)
# label positions for the choropleth (ACT and TAS get call-out labels placed in the sea)
LABELS = {"WA": (121.5, -25.5, 121.5, -25.5), "NT": (133.4, -19.5, 133.4, -19.5), "SA": (135.3, -29.8, 135.3, -29.8),
          "QLD": (144.5, -22.0, 144.5, -22.0), "NSW": (146.6, -32.3, 146.6, -32.3), "VIC": (144.2, -37.0, 144.2, -37.0),
          "ACT": (149.0, -35.5, 155.0, -36.6), "TAS": (146.6, -42.0, 151.5, -42.6)}
by_state["anchor_lon"] = by_state.state.map(lambda s: LABELS[s][0])
by_state["anchor_lat"] = by_state.state.map(lambda s: LABELS[s][1])
by_state["label_lon"] = by_state.state.map(lambda s: LABELS[s][2])
by_state["label_lat"] = by_state.state.map(lambda s: LABELS[s][3])
by_state["callout"] = by_state.state.isin(["ACT", "TAS"]).astype(int)
by_state.sort_values("pct_np", ascending=False).to_csv(OUT / "np_by_state.csv", index=False)

# ---------------- NSW NPWS Parks Visitation Survey FY24-25 ----------------
top20 = [("Blue Mountains", "National Park", 7828608), ("Royal", "National Park", 4907255),
         ("Ku-ring-gai Chase", "National Park", 4302126), ("Lane Cove", "National Park", 2399260),
         ("Kosciuszko", "National Park", 2355402), ("Sydney Harbour", "National Park", 2208696),
         ("Brisbane Water", "National Park", 2068192), ("Morton", "National Park", 1889384),
         ("Bouddi", "National Park", 1573516), ("Glenrock", "State Conservation Area", 1564384),
         ("Tomaree", "National Park", 1442481), ("Kamay Botany Bay", "National Park", 1405052),
         ("Garigal", "National Park", 1388905), ("Eurobodalla", "National Park", 1305299),
         ("Berowra Valley", "National Park", 1184377), ("Worimi", None, 1164024),
         ("Illawarra Escarpment", "State Conservation Area", 1112495), ("Coffs Coast", "Regional Park", 1040218),
         ("Cape Byron", "State Conservation Area", 997706), ("Georges River", "National Park", 963684)]
nsw = capad[capad.STATE == "NSW"]
rows = []
for rank, (name, ptype, visits) in enumerate(top20, 1):
    m = nsw[nsw.NAME == name]
    if ptype:
        m = m[m.TYPE == ptype]
    assert len(m), name
    a = m.GIS_AREA.sum()
    full = "Worimi Conservation Lands" if name == "Worimi" else f"{name} {ptype}"
    rows.append({"rank": rank, "park": full, "short": name, "visits": visits,
                 "lon": round((m.LONGITUDE * m.GIS_AREA).sum() / a, 4),
                 "lat": round((m.LATITUDE * m.GIS_AREA).sum() / a, 4)})
pd.DataFrame(rows).to_csv(OUT / "nsw_top20_parks.csv", index=False)

pd.DataFrame({"year": ["2008", "2010", "2012", "2014", "2016", "2018", "2020", "2022", "FY24-25"],
              "x": [2008, 2010, 2012, 2014, 2016, 2018, 2020, 2022, 2025],
              "visits": [37927616, 33843626, 35495625, 39167370, 51661944, 60236009, 50163728, 53005703, 65590112]}
             ).to_csv(OUT / "nsw_visits_trend.csv", index=False)

pd.DataFrame({"region": ["Greater Sydney", "Blue Mountains", "Hunter Central Coast", "South Coast", "North Coast",
                         "West", "Southern Ranges", "Northern Inland"],
              "visits": [28242772, 8690619, 8104462, 7504389, 6814841, 2530504, 2282771, 1419754]}
             ).assign(share=lambda d: (d.visits / 65590112 * 100).round(1)).to_csv(OUT / "nsw_visits_by_region.csv", index=False)

origins = pd.DataFrame([
    ("Melbourne", 2260821, 144.9631, -37.8136), ("Brisbane", 1955529, 153.0251, -27.4698),
    ("Canberra (ACT)", 1692130, 149.1300, -35.2809), ("Adelaide", 340212, 138.6007, -34.9285),
    ("Hobart", 85825, 147.3272, -42.8821), ("Perth", 79059, 115.8605, -31.9505)],
    columns=["origin", "visits", "lon", "lat"])
origins["dest_lon"], origins["dest_lat"] = 147.6, -32.6  # visual anchor for "NSW parks"
origins["label"] = origins.apply(lambda d: f"{d.origin.split(' (')[0]} {d.visits / 1e6:.1f}M" if d.visits >= 1e5 else f"{d.origin} {d.visits / 1e6:.2f}M", axis=1)
LABEL_POS = {"Melbourne": (144.4, -38.5, "right"), "Brisbane": (153.6, -27.2, "left"), "Canberra (ACT)": (150.4, -35.9, "left"),
             "Adelaide": (138.0, -35.6, "right"), "Hobart": (148.0, -43.2, "left"), "Perth": (115.8, -30.6, "center")}
origins["label_lon"] = origins.origin.map(lambda o: LABEL_POS[o][0])
origins["label_lat"] = origins.origin.map(lambda o: LABEL_POS[o][1])
origins["label_align"] = origins.origin.map(lambda o: LABEL_POS[o][2])
origins.to_csv(OUT / "nsw_interstate_origins.csv", index=False)

# Curved flow lines: points along a quadratic Bezier from each city to the NSW anchor (lon/lat space)
curve_rows = []
for _, o in origins.iterrows():
    x0, y0, x2, y2 = o.lon, o.lat, o.dest_lon, o.dest_lat
    mx, my, dx, dy = (x0 + x2) / 2, (y0 + y2) / 2, x2 - x0, y2 - y0
    cx, cy = mx + dy * 0.25, my - dx * 0.25  # bend each line to the same side
    for i in range(25):
        t = i / 24
        curve_rows.append({"origin": o.origin, "visits": o.visits, "step": i,
                           "lon": round((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t ** 2 * x2, 4),
                           "lat": round((1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t ** 2 * y2, 4)})
pd.DataFrame(curve_rows).to_csv(OUT / "nsw_interstate_flow_lines.csv", index=False)

pd.DataFrame({"group": ["NSW residents", "NSW residents", "Interstate visitors", "Interstate visitors"],
              "trip": ["Day trip", "Overnight", "Day trip", "Overnight"], "pct": [88, 12, 69, 31]}
             ).to_csv(OUT / "nsw_trip_length.csv", index=False)

waffle = [{"id": i, "row": i // 10, "col": i % 10, "group": "NSW residents" if i < 84 else "Interstate"} for i in range(100)]
pd.DataFrame(waffle).to_csv(OUT / "nsw_visitor_waffle.csv", index=False)

# ---------------- Tasmania PWS reference sites (thousands) ----------------
tas = [("Freycinet", [265, 265, 251, 287, 281, 287]), ("Cradle Mountain (Dove Lake)", [219, 170, 186, 264, 272, 268]),
       ("Mount Field", [177, 159, 182, 200, 232, None]), ("Tasman Arch", [169, 97, 104, 140, 139, 145]),
       ("Gordon River", [69, 44, 72, 111, 104, 99]), ("Lake St Clair", [77, 72, 78, 90, 82, 82]),
       ("Maria Island", [38, 33, 35, 46, 53, 74]), ("Hastings Caves", [36, 25, 31, 53, 58, 61]),
       ("Narawntapu", [48, 61, 58, 62, 63, 60]), ("Tamar Island Wetlands", [44, 42, 41, 44, 51, 51]),
       ("Mole Creek Karst", [43, 25, 31, 35, 47, 47]), ("Highfield House", [11, 12, 13, 17, 15, 14]),
       ("Three Capes Track", [9, 9, 10, 15, 14, 13]), ("Overland Track", [7, 8, 10, 11, 11, 11])]
years = ["2019-20", "2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]
long = [{"site": s, "year": y, "visitors_k": v, "index_vs_2019_20": None if v is None else round(v / vals[0], 3)}
        for s, vals in tas for y, v in zip(years, vals)]
tas_df = pd.DataFrame(long)
tas_df["change_vs_2019_20"] = (tas_df.index_vs_2019_20 - 1).round(3)
latest = tas_df.dropna(subset=["visitors_k"]).groupby("site").change_vs_2019_20.last()
tas_df["latest_change"] = tas_df.site.map(latest)
tas_df["group"] = tas_df.site.map(lambda s: "Multi-day walk" if s in ("Three Capes Track", "Overland Track") else "Day-visit site")
tas_df.to_csv(OUT / "tas_reference_sites.csv", index=False)

# ---------------- TRA National Visitor Survey via Austrade ----------------
pd.DataFrame({"activity": ["Botanic or public gardens", "Bushwalking and rainforest walks", "National or state parks",
                           "Cycling", "Wildlife parks, zoos and aquariums", "Beaches", "Golf", "Caravanning or camping",
                           "Snorkelling", "Whale or dolphin watching", "Farm visits", "Surfing", "Fishing"],
              "growth_pct": [85, 81, 73, 53, 46, 44, 44, 40, 38, 26, 12, 9, 8]}
             ).to_csv(OUT / "nature_activity_growth.csv", index=False)

# ---------------- ABS 3401.0 Table 5: short-term visitor arrivals ----------------
abs5 = pd.read_excel(RAW / "340105.xlsx", "Data1", header=None)
headers = abs5.iloc[0].tolist()
col = next(i for i, h in enumerate(headers) if "Total (Country of stay/residence)" in str(h))
ts = abs5.iloc[10:, [0, col]].dropna()
ts.columns = ["date", "arrivals"]
ts["date"] = pd.to_datetime(ts.date)
ts = ts[ts.date >= "2015-01-01"]
ts["year"] = ts.date.dt.year
ts["month"] = ts.date.dt.month
ts["month_name"] = ts.date.dt.strftime("%b")
ts["arrivals"] = ts.arrivals.astype(int)
ts.assign(date=ts.date.dt.strftime("%Y-%m")).to_csv(OUT / "abs_arrivals_monthly.csv", index=False)

# ---------------- Geography: Natural Earth state boundaries ----------------
ne = json.load(open(NE))
code = {"WA": "WA", "NT": "NT", "SA": "SA", "QL": "QLD", "TS": "TAS", "VI": "VIC", "CT": "ACT", "NS": "NSW", "JB": "JBT"}
feats = []
for f in ne["features"]:
    p = f["properties"]
    if p.get("adm0_a3") == "AUS" and code[p["postal"]] != "JBT":
        feats.append({"type": "Feature", "properties": {"state": code[p["postal"]], "name": p["name"]},
                      "geometry": f["geometry"]})
json.dump({"type": "FeatureCollection", "features": feats}, open(OUT / "_states_raw.geojson", "w"))

print("done")

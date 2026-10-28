# Into the Wild: Australia's National Parks Tourism

FIT3179 Data Visualisation 2.

## Folder layout

| Folder / file | What it holds |
|---|---|
| `index.html` | The page |
| `css/style.css` | Layout, colours and typography |
| `js/main.js` | Embeds every chart and links Figure 1 to 2 and Figure 10 to 11 |
| `js/offline-bundle.js` | Copies of `specs/` and `data/`, used only when the page is opened straight from disk |
| `specs/` | One readable JSON spec per chart (`.vl.json` = Vega-Lite, `.vg.json` = Vega) |
| `data/` | Small, clean CSV and TopoJSON files used by the specs (about 100 KB in total) |
| `scripts/prepare_data.py` | Turns the raw downloads (CAPAD 2024, ABS Table 5) into the files in `data/` |
| `sketch/` | Put the PDF of the hand-drawn sketch here |

## Charts

| # | Idiom | Spec |
|---|---|---|
| 1 | Choropleth map | `specs/01_choropleth.vl.json` |
| 2 | Beeswarm (Vega force layout) | `specs/02_beeswarm.vg.json` |
| 3 | Line chart | `specs/03_line_visits.vl.json` |
| 4 | Bar chart | `specs/04_bar_activities.vl.json` |
| 5 | Radial line chart | `specs/05_radial_arrivals.vl.json` |
| 6 | Proportional symbol map with inset | `specs/06_symbol_map.vl.json`, `specs/06b_symbol_map_inset.vl.json` |
| 7 | Flow map | `specs/07_flow_map.vl.json` |
| 8 | Treemap (Vega) | `specs/08_treemap.vg.json` |
| 9 | Waffle chart | `specs/09_waffle.vl.json` |
| 10 | Heatmap | `specs/10_heatmap.vl.json` |
| 11 | Isotype chart | `specs/11_isotype.vl.json` |
| 12 | 100% stacked bar chart | `specs/12_stacked_trip.vl.json` |

## Data sources

See the "Sources and credits" section at the bottom of the page.

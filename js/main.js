/* Into the Wild: embeds the 12 Vega / Vega-Lite charts and links them together. */

// Shared look for every chart (colours and fonts match css/style.css)
const THEME = {
  background: 'transparent',
  font: '"Nunito Sans", Arial, sans-serif',
  padding: 5,
  view: { stroke: null },
  axis: {
    labelFontSize: 12,
    labelColor: '#5d665f',
    titleFontSize: 12,
    titleColor: '#5d665f',
    titleFontWeight: 600,
    domainColor: '#c9cdc5',
    tickColor: '#c9cdc5',
    gridColor: '#ecebe4'
  },
  legend: {
    labelFontSize: 12,
    labelColor: '#3d4740',
    titleFontSize: 12,
    titleColor: '#26302a',
    titleFontWeight: 600
  },
  text: { font: '"Nunito Sans", Arial, sans-serif', fontSize: 12, color: '#26302a' },
  // Vega (not Vega-Lite) specs read fonts from these keys rather than the top-level "font"
  title: { font: '"Nunito Sans", Arial, sans-serif' }
};
['axis', 'legend'].forEach(k => {
  THEME[k].labelFont = THEME.font;
  THEME[k].titleFont = THEME.font;
});

const CHARTS = [
  ['#fig1', 'specs/01_choropleth.vl.json'],
  ['#fig2', 'specs/02_beeswarm.vg.json'],
  ['#fig3', 'specs/03_line_visits.vl.json'],
  ['#fig4', 'specs/04_bar_activities.vl.json'],
  ['#fig5', 'specs/05_radial_arrivals.vl.json'],
  ['#fig6a', 'specs/06_symbol_map.vl.json'],
  ['#fig6b', 'specs/06b_symbol_map_inset.vl.json'],
  ['#fig7', 'specs/07_flow_map.vl.json'],
  ['#fig8', 'specs/08_treemap.vg.json'],
  ['#fig9', 'specs/09_waffle.vl.json'],
  ['#fig10', 'specs/10_heatmap.vl.json'],
  ['#fig11', 'specs/11_isotype.vl.json'],
  ['#fig12', 'specs/12_stacked_trip.vl.json']
];

const EMBED_OPTIONS = {
  renderer: 'svg',
  config: THEME,
  actions: false
};

// Browsers block a page opened straight from disk (file://) from loading its JSON and CSV files.
// In that case, load js/offline-bundle.js (copies of specs/ and data/) and serve the files from it.
async function offlineLoader() {
  if (location.protocol !== 'file:') return null;
  await new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = 'js/offline-bundle.js';
    script.onload = resolve;
    script.onerror = reject;
    document.head.appendChild(script);
  });
  const loader = vega.loader();
  const loadFromWeb = loader.load.bind(loader);
  loader.load = (uri, options) =>
    uri in window.DV2_FILES ? Promise.resolve(window.DV2_FILES[uri]) : loadFromWeb(uri, options);
  return loader;
}

// Point selections store their value as {field: [value]}. Pull out the first value or a fallback.
const firstValue = (selection, field, fallback) =>
  selection && selection[field] && selection[field].length ? selection[field][0] : fallback;

async function init() {
  // Wait for web fonts so Vega measures label widths with the right font
  if (document.fonts && document.fonts.ready) {
    try { await document.fonts.ready; } catch (e) { /* carry on with fallback fonts */ }
  }

  const options = { ...EMBED_OPTIONS };
  try {
    const loader = await offlineLoader();
    if (loader) options.loader = loader;
  } catch (e) {
    console.error('Could not load js/offline-bundle.js', e);
  }

  const results = await Promise.all(CHARTS.map(async ([el, url]) => {
    try {
      const result = await vegaEmbed(el, url, options);
      return [el, result.view];
    } catch (err) {
      console.error('Could not draw ' + url, err);
      document.querySelector(el).innerHTML = '<p class="chart-error">This chart could not load. Please refresh the page.</p>';
      return [el, null];
    }
  }));
  const views = Object.fromEntries(results);
  window.dv2Views = views; // handy for debugging in the browser console

  // Figure 1 to Figure 2: clicking a state on the map highlights its parks in the beeswarm
  if (views['#fig1'] && views['#fig2']) {
    views['#fig1'].addSignalListener('pickState', (name, value) => {
      views['#fig2'].signal('selectedState', firstValue(value, 'state', 'All')).runAsync();
    });
  }

  // Figure 10 to Figure 11: hovering a heatmap row highlights the same park in the isotype chart
  if (views['#fig10'] && views['#fig11']) {
    views['#fig10'].addSignalListener('hoverSite', (name, value) => {
      views['#fig11'].signal('hl', firstValue(value, 'site', '')).runAsync();
    });
  }
}

init();

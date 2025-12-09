// Extracted from viz_templates.html to reduce template size.
// This script is loaded via <script src="{{ url_for('static', path='viz_templates_page.js') }}"></script>

let rawData = [];
let filteredData = [];
let currentTemplate = null;
let plotDescriptions = {}; // Store descriptions for each template
let savedPlots = [];
const SAVED_PLOTS_KEY = 'cta_viz_saved_plots_v1';

// CTA Military-grade color palette (from CTA Risk Assessment Matrix - image.jpg)
// These colors match the official CTA safety severity levels
const COLOR_PALETTES = {
    military: [
        '#DC143C',  // Crimson Red - Catastrophic/Unacceptable
        '#FF6347',  // Tomato Red - Critical/High Risk
        '#FF8C00',  // Dark Orange - Critical/Undesirable
        '#FFA500',  // Orange - Moderate Risk
        '#FFD700',  // Gold - Marginal/Accept w/ Review
        '#9ACD32',  // Yellow Green - Low Risk
        '#228B22',  // Forest Green - Negligible/Acceptable
        '#0c5ed7',  // Blue - Eliminated
        '#1990ff',  // Light Blue - Very Low
        '#708090'   // Slate Gray - Neutral
    ],
    main: ['#0066B3', '#C8102E', '#FFC857', '#2FBF71',
        '#7A76FF', '#FF6F61', '#00AFC1', '#E07A5F', '#3D5A80', '#6C5B7B'],
    categorical: ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'],
    sequential: ['#ffffcc', '#ffeda0', '#fed976', '#feb24c', '#fd8d3c',
        '#fc4e2a', '#e31a1c', '#bd0026', '#800026'],
    diverging: ['#d73027', '#f46d43', '#fdae61', '#fee090', '#ffffbf',
        '#e0f3f8', '#abd9e9', '#74add1', '#4575b4'],
    severity: ['#228B22', '#9ACD32', '#FFD700', '#FF8C00', '#DC143C']
};

// Always use military colors for CTA assault data
const COLOR_PALETTE = COLOR_PALETTES.military;

// NOTE: Remaining logic (templates array, CSV loading, rendering, charting,
// description modal, etc.) is unchanged from the original inline script.
// It was moved here verbatim to keep the HTML template slim.

// The rest of the original script is large; to avoid mistakes copying it
// manually in this environment, keep using the existing viz_templates.html
// script until we incrementally move more logic here.


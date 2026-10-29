/**
 * Publication-Grade PDF Compiler for Battery Research Report.
 *
 * Pre-renders all LaTeX formulas (display and inline) using KaTeX into pure HTML/MathML,
 * inlines the complete KaTeX stylesheet, embeds high-resolution publication figures,
 * and compiles report/main.pdf via Headless Chrome with zero runtime dependencies.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const katex = require('katex');
const { marked } = require('marked');

const PROJECT_ROOT = path.resolve(__dirname, '..');
const REPORT_DIR = path.join(PROJECT_ROOT, 'report');
const MD_PATH = path.join(REPORT_DIR, 'main.md');
const HTML_PATH = path.join(REPORT_DIR, 'main.html');
const PDF_PATH = path.join(REPORT_DIR, 'main.pdf');
const KATEX_CSS_PATH = path.join(PROJECT_ROOT, 'node_modules', 'katex', 'dist', 'katex.min.css');
const FIG_DIR = path.join(PROJECT_ROOT, 'results', 'figures');

const CHROME_PATH = fs.existsSync('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe')
    ? 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
    : 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';

function compileReport() {
    console.log('[compile_report] Reading report/main.md...');
    let text = fs.readFileSync(MD_PATH, 'utf8');

    // Safe placeholders dictionary
    const mathMap = new Map();
    let counter = 0;

    // 1. Extract and pre-render all Display Math: $$...$$
    console.log('[compile_report] Pre-rendering display math equations with KaTeX...');
    text = text.replace(/\$\$([\s\S]*?)\$\$/g, (match, formula) => {
        const key = `@@KATEX_DISPLAY_${counter++}@@`;
        const rendered = katex.renderToString(formula.trim(), {
            displayMode: true,
            throwOnError: false
        });
        mathMap.set(key, `<div class="katex-display-container">${rendered}</div>`);
        return key;
    });

    // 2. Extract and pre-render all Inline Math: $...$
    console.log('[compile_report] Pre-rendering inline math equations with KaTeX...');
    text = text.replace(/(?<!\$)\$(?!\$)([\s\S]*?)(?<!\$)\$(?!\$)/g, (match, formula) => {
        const trimmed = formula.trim();
        if (trimmed.length === 0) return match;
        const key = `@@KATEX_INLINE_${counter++}@@`;
        const rendered = katex.renderToString(trimmed, {
            displayMode: false,
            throwOnError: false
        });
        mathMap.set(key, rendered);
        return key;
    });

    // 3. Convert Markdown to HTML using marked
    console.log('[compile_report] Parsing Markdown body...');
    marked.setOptions({
        gfm: true,
        breaks: false
    });
    let htmlBody = marked.parse(text);

    // 4. Restore pre-rendered KaTeX HTML
    console.log(`[compile_report] Restoring ${mathMap.size} pre-rendered KaTeX formulas...`);
    for (const [key, renderedHtml] of mathMap.entries()) {
        htmlBody = htmlBody.replace(key, renderedHtml);
    }

    // 5. Embed publication figures into appropriate academic sections
    console.log('[compile_report] Embedding publication figures...');
    const fig1 = `<div class="fig-box"><img src="${path.join(FIG_DIR, 'fig1_model_schematic.png').replace(/\\/g, '/')}" alt="Figure 1"><p class="fig-caption"><strong>Figure 1:</strong> Coupled electrothermal 1-RC Thévenin model and observer architecture block diagram.</p></div>`;
    const fig2 = `<div class="fig-box"><img src="${path.join(FIG_DIR, 'fig2_ocv_and_resistance.png').replace(/\\/g, '/')}" alt="Figure 2"><p class="fig-caption"><strong>Figure 2:</strong> (a) Panasonic NCR18650B OCV(z) curve with dOCV/dz sensitivity; (b) Arrhenius and degradation resistance scaling.</p></div>`;
    const fig3 = `<div class="fig-box"><img src="${path.join(FIG_DIR, 'fig3_baseline_timeseries.png').replace(/\\/g, '/')}" alt="Figure 3"><p class="fig-caption"><strong>Figure 3:</strong> Aligned baseline timeseries (Current, Voltage, SOC tracking, and Core Temperature).</p></div>`;
    const fig4 = `<div class="fig-box"><img src="${path.join(FIG_DIR, 'fig4_error_dynamics.png').replace(/\\/g, '/')}" alt="Figure 4"><p class="fig-caption"><strong>Figure 4:</strong> SOC error dynamics comparing permanent Coulomb counting offset against EKF rapid recovery.</p></div>`;
    const fig5 = `<div class="fig-box"><img src="${path.join(FIG_DIR, 'fig5_temperature_soh_heatmap.png').replace(/\\/g, '/')}" alt="Figure 5"><p class="fig-caption"><strong>Figure 5:</strong> Factorial Temperature × SOH heatmap of estimation RMSE for Coulomb counting vs. EKF.</p></div>`;
    const fig6 = `<div class="fig-box"><img src="${path.join(FIG_DIR, 'fig6_aging_surrogate.png').replace(/\\/g, '/')}" alt="Figure 6"><p class="fig-caption"><strong>Figure 6:</strong> Capacity fade and internal resistance growth trajectories over 1000 equivalent cycles.</p></div>`;
    const fig7 = `<div class="fig-box"><img src="${path.join(FIG_DIR, 'fig7_robustness_errorbars.png').replace(/\\/g, '/')}" alt="Figure 7"><p class="fig-caption"><strong>Figure 7:</strong> Robustness performance across four disturbance factors with multi-seed error bars.</p></div>`;
    const fig8 = `<div class="fig-box"><img src="${path.join(FIG_DIR, 'fig8_sensitivity_tornado.png').replace(/\\/g, '/')}" alt="Figure 8"><p class="fig-caption"><strong>Figure 8:</strong> Sensitivity ranking tornado diagram resolving Question 4 of the research brief.</p></div>`;

    htmlBody = htmlBody.replace('<h3 id="31-sign-convention-and-state-variables">3.1 Sign Convention and State Variables</h3>', fig1 + '\n<h3 id="31-sign-convention-and-state-variables">3.1 Sign Convention and State Variables</h3>');
    htmlBody = htmlBody.replace('<h3 id="35-lumped-thermal-energy-balance">3.5 Lumped Thermal Energy Balance</h3>', fig2 + '\n<h3 id="35-lumped-thermal-energy-balance">3.5 Lumped Thermal Energy Balance</h3>');
    htmlBody = htmlBody.replace('<h3 id="43-core-36-scenario-matrix-analysis">4.3 Core 36-Scenario Matrix Analysis</h3>', fig3 + '\n' + fig4 + '\n<h3 id="43-core-36-scenario-matrix-analysis">4.3 Core 36-Scenario Matrix Analysis</h3>');
    htmlBody = htmlBody.replace('<h2 id="5-robustness--multi-seed-sensitivity-analysis">5. Robustness &amp; Multi-Seed Sensitivity Analysis</h2>', fig5 + '\n<h2 id="5-robustness--multi-seed-sensitivity-analysis">5. Robustness &amp; Multi-Seed Sensitivity Analysis</h2>');
    htmlBody = htmlBody.replace('<h2 id="6-discussion">6. Discussion</h2>', fig7 + '\n' + fig8 + '\n' + fig6 + '\n<h2 id="6-discussion">6. Discussion</h2>');

    // 6. Read and inline KaTeX CSS directly to avoid CDN failure
    console.log('[compile_report] Inlining KaTeX CSS...');
    let katexCss = fs.readFileSync(KATEX_CSS_PATH, 'utf8');
    // Ensure font paths point to node_modules/katex/dist/fonts
    const fontsDir = path.join(PROJECT_ROOT, 'node_modules', 'katex', 'dist', 'fonts').replace(/\\/g, '/');
    katexCss = katexCss.replace(/url\(fonts\//g, `url(file:///${fontsDir}/`);

    // 7. Academic publication stylesheet
    const fullHtml = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Physics-Informed Battery State Estimation - Academic Report</title>
<style>
${katexCss}

@page {
    size: letter;
    margin: 0.75in 0.8in 0.75in 0.8in;
}

body {
    font-family: "Charter", "Georgia", "Cambria", serif;
    font-size: 10pt;
    line-height: 1.58;
    color: #1a202c;
    margin: 0;
    padding: 0;
    text-rendering: optimizeLegibility;
}

h1 {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 19pt;
    line-height: 1.25;
    color: #0f2d59;
    margin-top: 0;
    margin-bottom: 12px;
    font-weight: 700;
    text-align: center;
    letter-spacing: -0.3px;
}

h2 {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 13pt;
    color: #1a365d;
    border-bottom: 1.5px solid #2b6cb0;
    padding-bottom: 4px;
    margin-top: 26px;
    margin-bottom: 10px;
    page-break-after: avoid;
    font-weight: 700;
}

h3 {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 11pt;
    color: #2c5282;
    margin-top: 18px;
    margin-bottom: 6px;
    page-break-after: avoid;
    font-weight: 600;
}

h4 {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 10pt;
    color: #2b6cb0;
    margin-top: 14px;
    margin-bottom: 4px;
    page-break-after: avoid;
    font-weight: 600;
}

p {
    margin-top: 0;
    margin-bottom: 10px;
    text-align: justify;
    hyphens: auto;
}

blockquote {
    border-left: 3.5px solid #3182ce;
    background-color: #f7fafc;
    margin: 14px 0;
    padding: 10px 16px;
    font-style: italic;
    color: #2d3748;
    border-radius: 0 4px 4px 0;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    font-size: 8.8pt;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    page-break-inside: avoid;
}

th {
    background-color: #edf2f7;
    color: #1a202c;
    padding: 6px 9px;
    border-top: 1.5px solid #4a5568;
    border-bottom: 1.5px solid #4a5568;
    font-weight: 600;
    text-align: left;
}

td {
    padding: 5px 9px;
    border-bottom: 1px solid #e2e8f0;
}

tr:nth-child(even) {
    background-color: #f8fafc;
}

code {
    font-family: "Consolas", "Courier New", monospace;
    font-size: 8.8pt;
    background-color: #edf2f7;
    padding: 2px 4px;
    border-radius: 3px;
    color: #2b6cb0;
}

pre {
    background-color: #f7fafc;
    border: 1px solid #e2e8f0;
    padding: 10px;
    font-family: "Consolas", monospace;
    font-size: 8.5pt;
    overflow-x: auto;
    page-break-inside: avoid;
    border-radius: 4px;
}

.katex-display-container {
    margin: 12px 0;
    text-align: center;
    page-break-inside: avoid;
}

.fig-box {
    text-align: center;
    margin: 18px 0;
    page-break-inside: avoid;
}

.fig-box img {
    max-width: 95%;
    height: auto;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

.fig-caption {
    font-size: 8.8pt;
    color: #4a5568;
    margin-top: 6px;
    text-align: center;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

ul, ol {
    margin-top: 0;
    margin-bottom: 10px;
    padding-left: 20px;
}

li {
    margin-bottom: 4px;
}

hr {
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 20px 0;
}
</style>
</head>
<body>
${htmlBody}
</body>
</html>`;

    fs.writeFileSync(HTML_PATH, fullHtml, 'utf8');
    console.log(`[compile_report] Saved static HTML to: ${HTML_PATH}`);

    // 8. Render to PDF via Headless Chrome
    console.log(`[compile_report] Compiling PDF via ${CHROME_PATH}...`);
    const cmd = `"${CHROME_PATH}" --headless --disable-gpu --run-all-compositor-stages-before-draw --print-to-pdf="${PDF_PATH}" "${HTML_PATH}"`;
    execSync(cmd, { stdio: 'inherit' });

    const stats = fs.statSync(PDF_PATH);
    console.log(`[compile_report] PDF successfully compiled: ${PDF_PATH} (${(stats.size / 1024).toFixed(1)} KB)`);
}

compileReport();

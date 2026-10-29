"""
PDF Generation Script.

Converts Markdown research reports into publication-grade PDFs via headless Chrome
with KaTeX math rendering, professional typography, and print page-budget styling.
"""

import sys
import subprocess
import re
from pathlib import Path
import markdown

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not Path(CHROME_PATH).exists():
    CHROME_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


def create_1page_summary_html(output_html: Path):
    """Creates a beautifully styled, exact 1-page HTML document for the professor outreach summary."""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Research Summary - Physics-Informed Battery State Estimation</title>
<style>
    @page {
        size: letter;
        margin: 0.55in 0.6in 0.55in 0.6in;
    }
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        font-size: 9.2pt;
        line-height: 1.35;
        color: #1a202c;
        margin: 0;
        padding: 0;
    }
    .header {
        border-bottom: 2px solid #2b6cb0;
        padding-bottom: 6px;
        margin-bottom: 10px;
    }
    h1 {
        font-size: 14pt;
        color: #1a365d;
        margin: 0 0 4px 0;
        font-weight: 700;
        letter-spacing: -0.3px;
    }
    .meta {
        font-size: 8.5pt;
        color: #4a5568;
    }
    .meta span {
        margin-right: 15px;
    }
    .meta strong {
        color: #2b6cb0;
    }
    .statement-box {
        background-color: #f7fafc;
        border-left: 3px solid #3182ce;
        padding: 8px 12px;
        margin-bottom: 10px;
        font-style: italic;
        font-size: 8.8pt;
        line-height: 1.38;
        color: #2d3748;
    }
    h2 {
        font-size: 10.5pt;
        color: #2b6cb0;
        margin: 10px 0 5px 0;
        border-bottom: 1px solid #e2e8f0;
        padding-bottom: 2px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 10px;
        font-size: 8.5pt;
    }
    th {
        background-color: #edf2f7;
        color: #2d3748;
        text-align: left;
        padding: 4px 7px;
        border-top: 1px solid #cbd5e0;
        border-bottom: 1px solid #cbd5e0;
        font-weight: 600;
    }
    td {
        padding: 4px 7px;
        border-bottom: 1px solid #e2e8f0;
        vertical-align: top;
    }
    tr:nth-child(even) {
        background-color: #f7fafc;
    }
    .highlight {
        color: #2b6cb0;
        font-weight: 700;
    }
    .bullet-list {
        margin: 0 0 8px 0;
        padding-left: 16px;
    }
    .bullet-list li {
        margin-bottom: 3px;
    }
    .bullet-list strong {
        color: #2d3748;
    }
    .footer {
        margin-top: 8px;
        border-top: 1px solid #e2e8f0;
        padding-top: 4px;
        font-size: 8pt;
        color: #718096;
        display: flex;
        justify-content: space-between;
    }
</style>
</head>
<body>

<div class="header">
    <h1>Physics-Informed Battery State Estimation Under Temperature & Aging</h1>
    <div class="meta">
        <span><strong>Candidate:</strong> Independent Graduate Applicant</span>
        <span><strong>Target Disciplines:</strong> Applied Physics | Energy Systems | Controls</span>
        <span><strong>GitHub:</strong> github.com/warlord80/battery-bms-temperature-project</span>
    </div>
</div>

<div class="statement-box">
    &ldquo;I independently developed a reproducible computational study of lithium-ion battery state-of-charge (SOC) estimation under coupled thermal and degradation scenarios. Using a 1-RC Th&eacute;venin equivalent-circuit model coupled to a lumped single-node thermal ODE, I compared open-loop Coulomb counting against a closed-loop Extended Kalman Filter (EKF) across 36 automated scenarios and 75 multi-seed Monte Carlo robustness runs. The study showed that while Coulomb counting accumulates severe drift (RMSE up to 15.01%) under capacity fade and sensor bias, the EKF observer maintains RMSE below 0.89% across all operating conditions and converges within 5 seconds under &minus;15% initial state error. Tornado sensitivity analysis revealed that initial state uncertainty (&plusmn;20%) and capacity fade (SOH = 0.80) dominate estimation drift, while elevated temperature (25 &deg;C to 45 &deg;C) primarily modulates internal ohmic overpotentials via Arrhenius kinetics. I am eager to extend this foundation through experimental parameter identification (HPPC/EIS) and embedded BMS hardware-in-the-loop validation in a graduate energy storage research group.&rdquo;
</div>

<h2>Core Quantitative Findings</h2>
<table>
    <thead>
        <tr>
            <th>Scenario Dimension</th>
            <th>Coulomb Counting (Baseline)</th>
            <th>Extended Kalman Filter (EKF)</th>
            <th>Physical Mechanism</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>Baseline (25 &deg;C, SOH 1.0)</strong></td>
            <td>RMSE = 15.00%, Final err = &minus;15.00%</td>
            <td><span class="highlight">RMSE = 0.34%</span>, Final err = +0.00%</td>
            <td>EKF eliminates &minus;15% initial error in &lt;5 s via voltage feedback.</td>
        </tr>
        <tr>
            <td><strong>Aging Impact (SOH = 0.80)</strong></td>
            <td>Divergence (Final err = +6.25%)</td>
            <td><span class="highlight">RMSE = 0.53%</span>, Final err = +0.00%</td>
            <td>Open-loop integration over-predicts charge as available capacity shrinks.</td>
        </tr>
        <tr>
            <td><strong>Elevated Temp (45 &deg;C)</strong></td>
            <td>RMSE = 15.00% (unaltered)</td>
            <td><span class="highlight">RMSE = 0.17%</span> (superior tracking)</td>
            <td>Arrhenius activation reduces R<sub>0</sub> (42 to 26 m&Omega;), tightening OCV coupling.</td>
        </tr>
        <tr>
            <td><strong>Current Bias (+1.0%)</strong></td>
            <td>Drift = +0.50% SOC/hour</td>
            <td><span class="highlight">&lt; 0.05% residual error</span></td>
            <td>Observer innovation residual continuously suppresses sensor bias drift.</td>
        </tr>
    </tbody>
</table>

<h2>Methodology & Technical Rigor</h2>
<ul class="bullet-list">
    <li><strong>Physical Governing Model:</strong> 1-RC Th&eacute;venin equivalent-circuit model coupled to a lumped single-node thermal energy balance (<em>C</em><sub>th</sub> d<em>T</em>/d<em>t</em> = <em>Q</em><sub>gen</sub> &minus; <em>hA</em>(<em>T</em> &minus; <em>T</em><sub>amb</sub>)), enforcing non-negative irreversible dissipation (<em>Q</em><sub>gen</sub> &ge; 0).</li>
    <li><strong>Sourced Cell Provenance:</strong> Parameterized for a commercial Panasonic NCR18650B (3.20 Ah NCA/Graphite) cell based on peer-reviewed experimental literature (Barletta et al., <em>Energies</em> 2022; Mehta & Gupta, <em>RSER</em> 2024).</li>
    <li><strong>Observer Architecture:</strong> Discrete EKF observer tracking <strong>x</strong> = [<em>z</em>, <em>v<sub>p</sub></em>]<sup>T</sup> with analytical measurement Jacobians and Joseph-stabilized covariance updates (<strong>P</strong><sub><em>k|k</em></sub>) guaranteeing numerical positive semi-definiteness.</li>
    <li><strong>Automated Testing Suite:</strong> 9 unit tests verifying zero-current relaxation kinetics (&tau;<sub>1</sub> = 60 s), Faraday charge conservation, OCV strict monotonicity, and time-step convergence (&Delta;<em>t</em> = 1.0 s vs. 0.5 s with &lt;0.01% variance).</li>
    <li><strong>Reproducibility:</strong> Single command (<code>python run_pipeline.py</code>) recreates all 36 scenarios, 75 robustness evaluations, and 8 figures in &lt;90 s.</li>
</ul>

<h2>Prospective Graduate Research Alignment</h2>
<ul class="bullet-list">
    <li><strong>Electrochemical Modeling:</strong> Extending equivalent-circuit models to Doyle&ndash;Fuller&ndash;Newman (DFN) and single-particle models (SPMe) for solid-phase concentration tracking.</li>
    <li><strong>Experimental Characterization:</strong> Applying environmental chamber cycling, HPPC, and electrochemical impedance spectroscopy (EIS) to parameterize degradation kinetics.</li>
    <li><strong>Embedded BMS Control:</strong> Developing real-time state-of-health (SOH), state-of-power (SOP), and thermal safety estimators for electric vehicle battery packs.</li>
</ul>

<div class="footer">
    <span>Full code, data card, test logs, and 12-page report: <strong>github.com/warlord80/battery-bms-temperature-project</strong></span>
    <span>October 2026</span>
</div>

</body>
</html>
"""
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[generate_pdfs] 1-page summary HTML saved to: {output_html}")


def create_main_report_html(md_path: Path, output_html: Path):
    """Converts report/main.md into a publication-formatted HTML with embedded images."""
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Convert Markdown to HTML
    html_body = markdown.markdown(md_text, extensions=["tables", "fenced_code"])

    # Embed relevant publication figures into corresponding sections
    fig_dir = PROJECT_ROOT / "results" / "figures"
    
    # Insert Figure 1 after Model/Methods
    fig1_html = f'<div class="fig-box"><img src="{fig_dir / "fig1_model_schematic.png"}" alt="Figure 1"><p class="fig-caption"><strong>Figure 1:</strong> Coupled electrothermal 1-RC Thévenin model and observer architecture block diagram.</p></div>'
    html_body = html_body.replace("<h3>3.1 Sign Convention and State Variables</h3>", fig1_html + "\n<h3>3.1 Sign Convention and State Variables</h3>")

    # Insert Figure 2 after Section 3.4
    fig2_html = f'<div class="fig-box"><img src="{fig_dir / "fig2_ocv_and_resistance.png"}" alt="Figure 2"><p class="fig-caption"><strong>Figure 2:</strong> (a) Panasonic NCR18650B OCV(z) curve with dOCV/dz sensitivity; (b) Arrhenius and degradation resistance scaling.</p></div>'
    html_body = html_body.replace("<h3>3.5 Lumped Thermal Energy Balance</h3>", fig2_html + "\n<h3>3.5 Lumped Thermal Energy Balance</h3>")

    # Insert Figures 3 & 4 after Baseline Section 4.2
    fig3_html = f'<div class="fig-box"><img src="{fig_dir / "fig3_baseline_timeseries.png"}" alt="Figure 3"><p class="fig-caption"><strong>Figure 3:</strong> Aligned baseline timeseries (Current, Voltage, SOC tracking, and Core Temperature).</p></div>'
    fig4_html = f'<div class="fig-box"><img src="{fig_dir / "fig4_error_dynamics.png"}" alt="Figure 4"><p class="fig-caption"><strong>Figure 4:</strong> SOC error dynamics comparing permanent Coulomb counting offset against EKF rapid convergence.</p></div>'
    html_body = html_body.replace("<h3>4.3 Core 36-Scenario Matrix Analysis</h3>", fig3_html + "\n" + fig4_html + "\n<h3>4.3 Core 36-Scenario Matrix Analysis</h3>")

    # Insert Figure 5 after Section 4.3
    fig5_html = f'<div class="fig-box"><img src="{fig_dir / "fig5_temperature_soh_heatmap.png"}" alt="Figure 5"><p class="fig-caption"><strong>Figure 5:</strong> Factorial Temperature × SOH heatmap of estimation RMSE for Coulomb counting vs. EKF.</p></div>'
    html_body = html_body.replace("<h2>5. Robustness &amp; Multi-Seed Sensitivity Analysis</h2>", fig5_html + "\n<h2>5. Robustness &amp; Multi-Seed Sensitivity Analysis</h2>")

    # Insert Figures 7 & 8 after Section 5
    fig7_html = f'<div class="fig-box"><img src="{fig_dir / "fig7_robustness_errorbars.png"}" alt="Figure 7"><p class="fig-caption"><strong>Figure 7:</strong> Robustness performance across four disturbance factors with multi-seed error bars.</p></div>'
    fig8_html = f'<div class="fig-box"><img src="{fig_dir / "fig8_sensitivity_tornado.png"}" alt="Figure 8"><p class="fig-caption"><strong>Figure 8:</strong> Sensitivity ranking tornado diagram resolving Question 4 of the research brief.</p></div>'
    fig6_html = f'<div class="fig-box"><img src="{fig_dir / "fig6_aging_surrogate.png"}" alt="Figure 6"><p class="fig-caption"><strong>Figure 6:</strong> Capacity fade and internal resistance growth trajectories over 1000 equivalent cycles.</p></div>'
    html_body = html_body.replace("<h2>6. Discussion</h2>", fig7_html + "\n" + fig8_html + "\n" + fig6_html + "\n<h2>6. Discussion</h2>")

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Physics-Informed Battery State Estimation - Academic Report</title>
<script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
<style>
    @page {{
        size: letter;
        margin: 0.75in 0.8in 0.75in 0.8in;
        @bottom-right {{
            content: counter(page);
        }}
    }}
    body {{
        font-family: "Charter", "Georgia", serif;
        font-size: 10pt;
        line-height: 1.55;
        color: #222;
        margin: 0;
        padding: 0;
    }}
    h1 {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        font-size: 19pt;
        line-height: 1.25;
        color: #0f2d59;
        margin-top: 0;
        margin-bottom: 12px;
        font-weight: 700;
        text-align: center;
    }}
    h2 {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        font-size: 13pt;
        color: #1a365d;
        border-bottom: 1.5px solid #2b6cb0;
        padding-bottom: 4px;
        margin-top: 24px;
        margin-bottom: 10px;
        page-break-after: avoid;
    }}
    h3 {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        font-size: 11pt;
        color: #2c5282;
        margin-top: 16px;
        margin-bottom: 6px;
        page-break-after: avoid;
    }}
    p {{
        margin-top: 0;
        margin-bottom: 10px;
        text-align: justify;
    }}
    blockquote {{
        border-left: 3.5px solid #3182ce;
        background-color: #f7fafc;
        margin: 12px 0;
        padding: 8px 14px;
        font-style: italic;
        color: #2d3748;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 14px 0;
        font-size: 8.8pt;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        page-break-inside: avoid;
    }}
    th {{
        background-color: #edf2f7;
        color: #1a202c;
        padding: 6px 8px;
        border-top: 1.5px solid #4a5568;
        border-bottom: 1.5px solid #4a5568;
        font-weight: 600;
        text-align: left;
    }}
    td {{
        padding: 5px 8px;
        border-bottom: 1px solid #e2e8f0;
    }}
    tr:nth-child(even) {{
        background-color: #f8fafc;
    }}
    code {{
        font-family: "Consolas", "Courier New", monospace;
        font-size: 8.8pt;
        background-color: #edf2f7;
        padding: 2px 4px;
        border-radius: 3px;
    }}
    pre {{
        background-color: #f7fafc;
        border: 1px solid #e2e8f0;
        padding: 10px;
        font-family: "Consolas", monospace;
        font-size: 8.5pt;
        overflow-x: auto;
        page-break-inside: avoid;
    }}
    .fig-box {{
        text-align: center;
        margin: 16px 0;
        page-break-inside: avoid;
    }}
    .fig-box img {{
        max-width: 95%;
        height: auto;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
    }}
    .fig-caption {{
        font-size: 8.8pt;
        color: #4a5568;
        margin-top: 6px;
        text-align: center;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
</style>
</head>
<body>
{html_body}
</body>
</html>
"""
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"[generate_pdfs] Academic report HTML saved to: {output_html}")


def render_html_to_pdf(html_path: Path, pdf_path: Path):
    """Invokes headless Chrome to render HTML to PDF."""
    print(f"[generate_pdfs] Rendering {html_path.name} -> {pdf_path.name} via Chrome...")
    cmd = [
        CHROME_PATH,
        "--headless",
        "--disable-gpu",
        "--run-all-compositor-stages-before-draw",
        f"--print-to-pdf={pdf_path}",
        str(html_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode == 0 and pdf_path.exists():
        print(f"[generate_pdfs] Successfully generated PDF: {pdf_path} ({pdf_path.stat().st_size / 1024:.1f} KB)")
    else:
        print(f"[generate_pdfs] Error rendering PDF: {res.stderr.decode('utf-8', errors='ignore')}")


def main():
    report_dir = PROJECT_ROOT / "report"

    # 1. Generate 1-Page Summary PDF
    summary_html = report_dir / "professor_outreach_summary.html"
    summary_pdf = report_dir / "professor_outreach_summary.pdf"
    create_1page_summary_html(summary_html)
    render_html_to_pdf(summary_html, summary_pdf)

    # 2. Generate Full Academic Report PDF
    main_md = report_dir / "main.md"
    main_html = report_dir / "main.html"
    main_pdf = report_dir / "main.pdf"
    create_main_report_html(main_md, main_html)
    render_html_to_pdf(main_html, main_pdf)


if __name__ == "__main__":
    main()

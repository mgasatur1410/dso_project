#!/usr/bin/env python3
"""
Simple script to convert ruff JSON output to HTML report.
Used in CI/CD pipeline for artifact generation.
"""
import json
import sys
from datetime import datetime
from pathlib import Path


def generate_html(json_path: Path, html_path: Path):
    """Convert ruff JSON report to HTML."""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        html_path.write_text(
            "<html><body><h1>Ruff Report</h1>"
            "<p>No issues found or report not available.</p></body></html>"
        )
        return

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ruff Linting Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        h1 {{ color: #333; }}
        .issue {{ background: white; padding: 15px; margin: 10px 0;
                 border-left: 4px solid #e74c3c; border-radius: 4px; }}
        .location {{ color: #7f8c8d; font-size: 0.9em; }}
        .code {{ background: #ecf0f1; padding: 5px; border-radius: 3px;
                font-family: monospace; }}
        .message {{ color: #2c3e50; margin-top: 5px; }}
        .no-issues {{ background: #2ecc71; color: white; padding: 20px;
                     border-radius: 4px; text-align: center; }}
        .summary {{ background: white; padding: 15px; margin-bottom: 20px; border-radius: 4px; }}
    </style>
</head>
<body>
    <h1>Ruff Linting Report</h1>
    <div class="summary">
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        <p><strong>Total Issues:</strong> {len(data)}</p>
    </div>
"""

    if not data:
        html_content += (
            '<div class="no-issues"><h2>✅ No linting issues found!</h2></div>'
        )
    else:
        for item in data:
            filename = item.get("filename", "unknown")
            line = item.get("location", {}).get("row", "?")
            col = item.get("location", {}).get("column", "?")
            code = item.get("code", "")
            message = item.get("message", "")

            html_content += f"""
    <div class="issue">
        <div class="location"><strong>{filename}:{line}:{col}</strong></div>
        <div class="code">{code}</div>
        <div class="message">{message}</div>
    </div>
"""

    html_content += """
</body>
</html>
"""

    html_path.write_text(html_content, encoding="utf-8")
    print(f"Generated HTML report: {html_path}")


if __name__ == "__main__":
    json_file = (
        Path(sys.argv[1]) if len(sys.argv) > 1 else Path("reports/ruff-report.json")
    )
    html_file = (
        Path(sys.argv[2]) if len(sys.argv) > 2 else Path("reports/ruff-report.html")
    )

    generate_html(json_file, html_file)

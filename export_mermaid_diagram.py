#!/usr/bin/env python3
"""Export Mermaid diagram from project_spec.md as PNG."""

import re
import os
from pathlib import Path

def extract_mermaid_diagram(markdown_file: str) -> str:
    """Extract Mermaid diagram code from markdown file."""
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find mermaid code block
    pattern = r'```mermaid\n(.*?)```'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        raise ValueError("No Mermaid diagram found in the file")
    
    return match.group(1).strip()

def render_mermaid_to_png(mermaid_code: str, output_path: str):
    """Render Mermaid diagram to PNG using playwright."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise ImportError(
            "playwright is required. Install it with: pip install playwright && playwright install chromium"
        )
    
    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background: white;
        }}
        .mermaid {{
            display: flex;
            justify-content: center;
            align-items: center;
        }}
    </style>
</head>
<body>
    <div class="mermaid">
{mermaid_code}
    </div>
    <script>
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
    </script>
</body>
</html>"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_template)
        page.wait_for_selector('.mermaid svg', timeout=10000)
        
        # Wait a bit for rendering to complete
        page.wait_for_timeout(2000)
        
        # Take screenshot
        mermaid_element = page.query_selector('.mermaid')
        if mermaid_element:
            mermaid_element.screenshot(path=output_path)
        else:
            # Fallback: screenshot entire page
            page.screenshot(path=output_path, full_page=True)
        
        browser.close()

def main():
    """Main function to export diagram."""
    project_root = Path(__file__).parent
    spec_file = project_root / "memory" / "project_spec.md"
    output_file = project_root / "memory" / "data_flow_diagram.png"
    
    print(f"Extracting Mermaid diagram from {spec_file}...")
    mermaid_code = extract_mermaid_diagram(str(spec_file))
    
    print(f"Rendering diagram to {output_file}...")
    render_mermaid_to_png(mermaid_code, str(output_file))
    
    print(f"✓ Successfully exported diagram to {output_file}")

if __name__ == "__main__":
    main()

import re

def polish_apple_ui():
    with open("web_ui.py", "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update CSS for macOS Traffic Lights & Terminal
    mac_css = """
        /* Apple macOS Developer Terminal */
        .mac-traffic-lights {
            display: inline-flex;
            gap: 6px;
            align-items: center;
        }
        .mac-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
        }
        .mac-dot-red { background: #ff5f56; border: 1px solid #e0443e; }
        .mac-dot-yellow { background: #ffbd2e; border: 1px solid #dea123; }
        .mac-dot-green { background: #27c93f; border: 1px solid #1aab29; }
        .mac-console-header {
            padding: 10px 16px;
            background: #242426;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px 14px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .mac-console-title {
            font-size: 11.5px;
            font-weight: 600;
            color: #e5e5ea;
            letter-spacing: 0.01em;
        }
        .mac-clear-btn {
            padding: 3px 10px;
            font-size: 11px;
            font-weight: 500;
            background: rgba(255, 255, 255, 0.1);
            color: #e5e5ea;
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .mac-clear-btn:hover {
            background: rgba(255, 255, 255, 0.2);
            color: #ffffff;
        }
    """

    # Insert mac_css right before </style>
    if "/* Apple macOS Developer Terminal */" not in content:
        content = content.replace("</style>", mac_css + "\n    </style>")

    # 2. Update .plg-subnav-btn.active to Apple Segmented Pill style
    old_plg_active = """        .plg-subnav-btn.active {
            background: #1d1d1f;
            color: #ffffff;
            font-weight: 600;
        }"""
    new_plg_active = """        .plg-subnav-btn.active {
            background: #ffffff;
            color: #1d1d1f;
            font-weight: 600;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }"""
    content = content.replace(old_plg_active, new_plg_active)

    # 3. Update Tab 1 primary button to btn btn-accent
    content = content.replace(
        '<button id="btn-start-audit" class="btn" onclick="startAudit()">START LIVE AUDIT</button>',
        '<button id="btn-start-audit" class="btn btn-accent" onclick="startAudit()">START LIVE AUDIT</button>'
    )

    # 4. Remove harsh border-left from Tab 2 and Tab 3 cards
    content = content.replace(
        '<div class="card" style="border-left: 3px solid #111827;">',
        '<div class="card">'
    )
    content = content.replace(
        '<div class="card" style="border-left: 3px solid #15803d;">',
        '<div class="card">'
    )

    # 5. Remove harsh border from Tab 5 executive score banner
    content = content.replace(
        '<div class="card" style="border: 2px solid #111827; background: #f9fafb;">',
        '<div class="card" style="background: #ffffff;">'
    )

    # 6. Replace Tab 1 Terminal Header with macOS Window Bar
    old_term1_header = """            <div class="card" style="padding: 0;">
                <div style="padding: 10px 14px; border-bottom: 1px solid #111827; background: #111827; color: #ffffff; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; display: flex; justify-content: space-between; align-items: center;">
                    <span>Execution Stream</span>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <span id="log-count" style="color: #9ca3af;">0 lines</span>
                        <button class="btn btn-outline" style="padding: 2px 8px; font-size: 10px; background: transparent; color: #f3f4f6; border-color: #4b5563;" onclick="resetAllEnginesAndCache()" title="Clear logs and reset engine">CLEAR</button>
                    </div>
                </div>
                <div id="audit-terminal" class="terminal">Awaiting execution command...</div>
            </div>"""

    new_term1_header = """            <div class="card" style="padding: 0; overflow: hidden;">
                <div class="mac-console-header">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div class="mac-traffic-lights">
                            <span class="mac-dot mac-dot-red"></span>
                            <span class="mac-dot mac-dot-yellow"></span>
                            <span class="mac-dot mac-dot-green"></span>
                        </div>
                        <span class="mac-console-title">Execution Stream — Terminal Console</span>
                    </div>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <span id="log-count" style="color: #86868b; font-size: 11px; font-weight: 500;">0 lines</span>
                        <button class="mac-clear-btn" onclick="resetAllEnginesAndCache()" title="Clear logs and reset engine">Clear</button>
                    </div>
                </div>
                <div id="audit-terminal" class="terminal" style="border-radius: 0 0 16px 16px;">Awaiting execution command...</div>
            </div>"""
    content = content.replace(old_term1_header, new_term1_header)

    # 7. Replace Tab 5 Terminal Header with macOS Window Bar
    old_term5_header = """            <div class="card" style="padding: 0;">
                <div style="padding: 10px 14px; border-bottom: 1px solid #111827; background: #111827; color: #ffffff; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; display: flex; justify-content: space-between; align-items: center;">
                    <span>Security Audit Stream</span>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <span id="sec-log-count" style="color: #9ca3af;">0 lines</span>
                        <button class="btn btn-outline" style="padding: 2px 8px; font-size: 10px; background: transparent; color: #f3f4f6; border-color: #4b5563;" onclick="resetAllEnginesAndCache()" title="Clear logs and reset engine">CLEAR</button>
                    </div>
                </div>
                <div id="sec-terminal" class="terminal">Awaiting security execution command...</div>
            </div>"""

    new_term5_header = """            <div class="card" style="padding: 0; overflow: hidden;">
                <div class="mac-console-header">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div class="mac-traffic-lights">
                            <span class="mac-dot mac-dot-red"></span>
                            <span class="mac-dot mac-dot-yellow"></span>
                            <span class="mac-dot mac-dot-green"></span>
                        </div>
                        <span class="mac-console-title">Security Audit Stream — Terminal Console</span>
                    </div>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <span id="sec-log-count" style="color: #86868b; font-size: 11px; font-weight: 500;">0 lines</span>
                        <button class="mac-clear-btn" onclick="resetAllEnginesAndCache()" title="Clear logs and reset engine">Clear</button>
                    </div>
                </div>
                <div id="sec-terminal" class="terminal" style="border-radius: 0 0 16px 16px;">Awaiting security execution command...</div>
            </div>"""
    content = content.replace(old_term5_header, new_term5_header)

    # 8. Clean up Tab 4 subnav bar container to segmented capsule
    old_tab4_subnav = """            <!-- Mode Switcher: 3 Modes -->
            <div style="display: flex; gap: 12px; margin-bottom: 22px; padding-bottom: 14px; align-items: center; justify-content: space-between; flex-wrap: wrap; border-bottom: 1px solid rgba(0, 0, 0, 0.06);">
                <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                    <button type="button" id="btn-opt-mode-crawl" class="plg-subnav-btn active" onclick="switchOptSubMode('crawl')">
                        1. Live URL &amp; Plugin Improver (Side-by-Side)
                    </button>
                    <button type="button" id="btn-opt-mode-plugin" class="plg-subnav-btn" onclick="switchOptSubMode('plugin')">
                        2. WordPress Plugin Metadata Suite
                    </button>
                    <button type="button" id="btn-opt-mode-single" class="plg-subnav-btn" onclick="switchOptSubMode('single')">
                        3. Single Element &amp; GEO Optimizer
                    </button>
                </div>
                <div style="font-size: 11px; font-weight: 700; color: #4b5563; text-transform: uppercase;">
                    Active Mode: <span id="opt-active-mode-label" style="color: #111827;">Live URL &amp; Plugin Notice Improver</span>
                </div>
            </div>"""

    new_tab4_subnav = """            <!-- Mode Switcher: 3 Modes — Apple Segmented Control -->
            <div style="display: flex; gap: 12px; margin-bottom: 22px; padding-bottom: 14px; align-items: center; justify-content: space-between; flex-wrap: wrap; border-bottom: 1px solid rgba(0, 0, 0, 0.06);">
                <div style="display: inline-flex; background: rgba(0, 0, 0, 0.05); padding: 3px; border-radius: 12px; gap: 3px; flex-wrap: wrap;">
                    <button type="button" id="btn-opt-mode-crawl" class="plg-subnav-btn active" onclick="switchOptSubMode('crawl')">
                        1. Live URL &amp; Plugin Improver (Side-by-Side)
                    </button>
                    <button type="button" id="btn-opt-mode-plugin" class="plg-subnav-btn" onclick="switchOptSubMode('plugin')">
                        2. WordPress Plugin Metadata Suite
                    </button>
                    <button type="button" id="btn-opt-mode-single" class="plg-subnav-btn" onclick="switchOptSubMode('single')">
                        3. Single Element &amp; GEO Optimizer
                    </button>
                </div>
                <div style="font-size: 11.5px; font-weight: 500; color: #86868b;">
                    Active Mode: <span id="opt-active-mode-label" style="color: #0071e3; font-weight: 600;">Live URL &amp; Plugin Notice Improver</span>
                </div>
            </div>"""
    content = content.replace(old_tab4_subnav, new_tab4_subnav)

    # 9. Clean up reset toast inline style
    old_toast = '<div id="reset-toast" style="display: none; position: fixed; bottom: 24px; right: 24px; background: #111827; color: #ffffff; padding: 12px 20px; font-size: 12px; font-weight: 700; border-left: 4px solid #15803d; z-index: 9999; letter-spacing: 0.05em; text-transform: uppercase;">'
    new_toast = '<div id="reset-toast" style="display: none;">'
    content = content.replace(old_toast, new_toast)

    with open("web_ui.py", "w", encoding="utf-8") as f:
        f.write(content)

    print("SUCCESS: web_ui.py polished with refined Apple UI details!")

if __name__ == "__main__":
    polish_apple_ui()

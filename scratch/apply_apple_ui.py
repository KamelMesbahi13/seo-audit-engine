import sys

apple_css = """        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
            background: #f5f5f7;
            color: #1d1d1f;
            line-height: 1.5;
            font-size: 13.5px;
            padding: 24px 20px 80px 20px;
        }

        .container {
            max-width: 1140px;
            margin: 0 auto;
        }

        /* Apple Navigation Header */
        .header {
            border-bottom: 1px solid rgba(0, 0, 0, 0.08);
            padding-bottom: 20px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        }

        .org-label {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.02em;
            text-transform: uppercase;
            color: #0071e3;
            background: rgba(0, 113, 227, 0.08);
            padding: 3px 10px;
            border-radius: 980px;
            margin-bottom: 6px;
        }

        .main-title {
            font-size: 26px;
            font-weight: 700;
            letter-spacing: -0.03em;
            color: #1d1d1f;
            line-height: 1.2;
        }

        .header-meta {
            font-size: 11px;
            color: #86868b;
            text-align: right;
            font-weight: 500;
            letter-spacing: 0.02em;
        }

        /* Tabs Navigation — Apple Segmented Control */
        .tabs-nav {
            display: flex;
            background: rgba(0, 0, 0, 0.05);
            padding: 4px;
            border-radius: 14px;
            gap: 3px;
            margin-bottom: 26px;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            border: none;
        }

        .tab-btn {
            flex: 1;
            min-width: max-content;
            background: transparent;
            color: #6e6e73;
            border: none;
            border-radius: 10px;
            padding: 9px 16px;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            text-transform: none;
            letter-spacing: -0.01em;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            text-align: center;
            white-space: nowrap;
        }

        .tab-btn:hover {
            color: #1d1d1f;
            background: rgba(255, 255, 255, 0.5);
        }

        .tab-btn.active {
            background: #ffffff;
            color: #1d1d1f;
            font-weight: 600;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04);
        }

        .tab-content {
            display: none;
            animation: fadeIn 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .tab-content.active {
            display: block;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(4px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Shared Form & Card Components — Apple Surfaces */
        .card {
            background: #ffffff;
            border-radius: 18px;
            border: 1px solid rgba(0, 0, 0, 0.06);
            padding: 24px 28px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03), 0 1px 2px rgba(0, 0, 0, 0.02);
            transition: box-shadow 0.2s ease, border-color 0.2s ease;
        }

        .card-title {
            font-size: 15px;
            font-weight: 600;
            letter-spacing: -0.015em;
            color: #1d1d1f;
            border-bottom: 1px solid rgba(0, 0, 0, 0.06);
            padding-bottom: 12px;
            margin-bottom: 18px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
            text-transform: none;
        }

        .form-grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }

        .form-grid-3 {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 16px;
        }

        .form-grid-4 {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
        }

        @media (max-width: 900px) {
            .form-grid-2, .form-grid-3, .form-grid-4 {
                grid-template-columns: 1fr;
            }
        }

        .field-group {
            margin-bottom: 16px;
        }

        .field-label {
            display: block;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: -0.01em;
            color: #1d1d1f;
            margin-bottom: 6px;
            text-transform: none;
        }

        .field-help {
            font-size: 12px;
            color: #86868b;
            margin-top: 5px;
            line-height: 1.4;
        }

        input[type="text"], input[type="number"], input[type="url"], select, textarea {
            width: 100%;
            padding: 10px 14px;
            font-size: 13.5px;
            border: 1px solid #d2d2d7;
            border-radius: 10px;
            color: #1d1d1f;
            background: #ffffff;
            font-family: inherit;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }

        input[type="text"]::placeholder, input[type="url"]::placeholder, textarea::placeholder {
            color: #a1a1a6;
        }

        input[type="text"]:focus, input[type="number"]:focus, input[type="url"]:focus, select:focus, textarea:focus {
            outline: none;
            border-color: #0071e3;
            box-shadow: 0 0 0 4px rgba(0, 113, 227, 0.15);
        }

        /* Buttons — Apple HIG Pill Styles */
        .btn-row {
            display: flex;
            gap: 10px;
            margin-top: 18px;
            flex-wrap: wrap;
            align-items: center;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            padding: 10px 22px;
            font-size: 13px;
            font-weight: 600;
            letter-spacing: -0.01em;
            border-radius: 980px;
            cursor: pointer;
            text-decoration: none;
            border: 1px solid transparent;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            white-space: nowrap;
            text-transform: none;
        }

        .btn:hover {
            transform: translateY(-1px);
        }

        .btn:active {
            transform: translateY(0);
        }

        .btn-outline {
            background: #ffffff;
            color: #1d1d1f;
            border-color: #d2d2d7;
        }

        .btn-outline:hover {
            background: #f5f5f7;
            border-color: #86868b;
        }

        .btn-accent {
            background: #0071e3;
            color: #ffffff;
        }

        .btn-accent:hover {
            background: #0077ed;
            box-shadow: 0 4px 14px rgba(0, 113, 227, 0.25);
        }

        .btn-accent:active {
            background: #0062c4;
            box-shadow: none;
        }

        .btn-reset {
            background: rgba(255, 59, 48, 0.08);
            color: #ff3b30;
            border: 1px solid rgba(255, 59, 48, 0.2);
            border-radius: 980px;
            font-size: 12px;
            font-weight: 600;
            padding: 6px 14px;
        }

        .btn-reset:hover {
            background: #ff3b30;
            color: #ffffff;
            border-color: #ff3b30;
            box-shadow: 0 2px 8px rgba(255, 59, 48, 0.25);
        }

        .btn:disabled, .btn-outline:disabled, .btn-accent:disabled, .btn-reset:disabled {
            opacity: 0.45;
            cursor: not-allowed;
            transform: none !important;
            box-shadow: none !important;
        }

        /* Status Indicator */
        .status-box {
            padding: 12px 18px;
            border: 1px solid rgba(0, 0, 0, 0.06);
            background: #ffffff;
            border-radius: 14px;
            font-size: 12.5px;
            margin-bottom: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
        }

        .status-badge {
            display: inline-block;
            padding: 4px 11px;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.02em;
            text-transform: uppercase;
            border-radius: 980px;
            background: rgba(0, 0, 0, 0.06);
            color: #1d1d1f;
        }

        .status-badge.running {
            background: rgba(0, 113, 227, 0.12);
            color: #0071e3;
        }

        .status-badge.success {
            background: rgba(52, 199, 89, 0.14);
            color: #28cd41;
        }

        /* Terminal Console — macOS Developer Window */
        .terminal {
            background: #1c1c1e;
            color: #f5f5f7;
            padding: 18px 20px;
            font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
            font-size: 12px;
            height: 290px;
            overflow-y: auto;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            white-space: pre-wrap;
            line-height: 1.6;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
        }

        /* Tables — Apple Minimal Clean */
        table.data-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 13px;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid rgba(0, 0, 0, 0.06);
        }

        table.data-table th {
            text-align: left;
            padding: 12px 14px;
            background: #fbfbfd;
            border-bottom: 1px solid rgba(0, 0, 0, 0.06);
            font-weight: 600;
            font-size: 12px;
            color: #6e6e73;
            letter-spacing: -0.01em;
            text-transform: none;
        }

        table.data-table td {
            padding: 12px 14px;
            border-bottom: 1px solid rgba(0, 0, 0, 0.04);
            color: #1d1d1f;
        }

        table.data-table tr:last-child td {
            border-bottom: none;
        }

        table.data-table tr:hover td {
            background: #fafafc;
        }

        /* Blueprint Interactive Viewer */
        .blueprint-viewer {
            border: 1px solid rgba(0, 0, 0, 0.06);
            border-radius: 16px;
            margin-top: 24px;
            padding: 26px;
            background: #ffffff;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
        }

        .blueprint-viewer h2 {
            font-size: 16px;
            font-weight: 600;
            letter-spacing: -0.02em;
            border-bottom: 1px solid rgba(0, 0, 0, 0.06);
            padding-bottom: 8px;
            margin: 24px 0 14px 0;
            color: #1d1d1f;
        }

        .blueprint-viewer h2:first-child {
            margin-top: 0;
        }

        .code-container {
            position: relative;
            margin: 14px 0;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid rgba(0, 0, 0, 0.08);
        }

        .code-box {
            background: #1c1c1e;
            color: #f5f5f7;
            padding: 16px;
            font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
            font-size: 12px;
            overflow-x: auto;
            white-space: pre;
            line-height: 1.5;
        }

        .copy-btn {
            position: absolute;
            top: 8px;
            right: 8px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 600;
            background: rgba(255, 255, 255, 0.15);
            color: #ffffff;
            border: 1px solid rgba(255, 255, 255, 0.25);
            border-radius: 980px;
            cursor: pointer;
            backdrop-filter: blur(8px);
            transition: all 0.2s ease;
        }

        .copy-btn:hover {
            background: rgba(255, 255, 255, 0.3);
        }

        .anti-pattern-item {
            border-left: 3px solid #ff3b30;
            padding: 10px 14px;
            background: rgba(255, 59, 48, 0.05);
            border-radius: 0 10px 10px 0;
            margin-bottom: 10px;
            font-size: 12.5px;
            color: #1d1d1f;
        }

        .checklist-item {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            padding: 8px 0;
            border-bottom: 1px solid rgba(0, 0, 0, 0.04);
            font-size: 13px;
        }

        .checklist-item input[type="checkbox"] {
            margin-top: 3px;
            accent-color: #0071e3;
        }

        .downloads-banner {
            background: rgba(52, 199, 89, 0.08);
            border: 1px solid rgba(52, 199, 89, 0.25);
            border-radius: 14px;
            padding: 16px 20px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .downloads-banner-text {
            font-size: 13px;
            color: #15803d;
        }
        .downloads-banner-text strong {
            display: block;
            font-size: 14px;
            color: #14532d;
            margin-bottom: 2px;
        }

        /* Tab 3: Content Architect Styles */
        .badge-metric {
            display: inline-block;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: 600;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            border-radius: 980px;
        }
        .badge-good { background: rgba(52, 199, 89, 0.12); color: #15803d; border: 1px solid rgba(52, 199, 89, 0.25); }
        .badge-warn { background: rgba(255, 149, 0, 0.12); color: #c25e00; border: 1px solid rgba(255, 149, 0, 0.25); }
        .badge-bad  { background: rgba(255, 59, 48, 0.1); color: #d70015; border: 1px solid rgba(255, 59, 48, 0.25); }

        .content-layout {
            display: grid;
            grid-template-columns: 290px 1fr;
            gap: 16px;
            margin-top: 16px;
            align-items: start;
        }
        .content-pages-sidebar {
            border: 1px solid rgba(0, 0, 0, 0.06);
            background: #ffffff;
            border-radius: 14px;
            max-height: 720px;
            overflow-y: auto;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
        }
        .sidebar-page-item {
            padding: 12px 14px;
            border-bottom: 1px solid rgba(0, 0, 0, 0.04);
            cursor: pointer;
            transition: all 0.15s ease;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .sidebar-page-item:hover {
            background: #fafafc;
        }
        .sidebar-page-item.active {
            background: #1d1d1f;
            color: #ffffff;
        }
        .sidebar-page-item.active .badge-metric {
            background: rgba(255, 255, 255, 0.2);
            color: #ffffff;
            border-color: transparent;
        }
        .sidebar-page-item.active .page-sub {
            color: #a1a1a6 !important;
        }
        .aeo-callout {
            border-left: 3px solid #34c759;
            background: rgba(52, 199, 89, 0.06);
            border-radius: 0 12px 12px 0;
            padding: 14px 16px;
            margin-bottom: 16px;
            font-size: 13px;
            color: #15803d;
            line-height: 1.6;
        }
        .section-block {
            border: 1px solid rgba(0, 0, 0, 0.06);
            border-radius: 14px;
            padding: 18px 20px;
            margin-bottom: 16px;
            background: #ffffff;
        }
        .section-block h3 {
            font-size: 14px;
            font-weight: 600;
            letter-spacing: -0.01em;
            margin-bottom: 8px;
            color: #1d1d1f;
        }
        .section-block h4 {
            font-size: 13px;
            font-weight: 600;
            margin-top: 12px;
            margin-bottom: 6px;
            color: #48484a;
        }
        .tag-pill {
            display: inline-block;
            font-size: 11px;
            font-weight: 600;
            padding: 2px 9px;
            background: rgba(0, 0, 0, 0.05);
            color: #1d1d1f;
            border: 1px solid rgba(0, 0, 0, 0.06);
            border-radius: 980px;
            text-transform: none;
        }
        .tag-pill.good {
            background: rgba(52, 199, 89, 0.12);
            color: #15803d;
            border-color: rgba(52, 199, 89, 0.25);
        }
        .tag-pill.req {
            background: rgba(255, 59, 48, 0.08);
            color: #d70015;
            border-color: rgba(255, 59, 48, 0.2);
        }

        /* Optimizer Tab 4 Styles — Apple Design System */
        /* Side-by-Side Crawl & Plugin Notice Comparison Styles */
        .opt-side-by-side-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-top: 12px;
        }
        @media (max-width: 900px) {
            .opt-side-by-side-grid {
                grid-template-columns: 1fr;
            }
        }
        .opt-side-col {
            border: 1px solid rgba(0, 0, 0, 0.06);
            background: #ffffff;
            border-radius: 14px;
            padding: 16px 18px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: all 0.2s ease;
        }
        .opt-side-col.current {
            border: 1px solid rgba(255, 59, 48, 0.2);
            background: rgba(255, 59, 48, 0.02);
        }
        .opt-side-col.improved {
            border: 1px solid rgba(52, 199, 89, 0.35);
            background: rgba(52, 199, 89, 0.03);
            box-shadow: 0 2px 10px rgba(52, 199, 89, 0.04);
        }
        .opt-side-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            padding-bottom: 8px;
            border-bottom: 1px solid rgba(0, 0, 0, 0.06);
        }
        .opt-side-title {
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .opt-side-col.current .opt-side-title {
            color: #ff3b30;
        }
        .opt-side-col.improved .opt-side-title {
            color: #34c759;
        }
        .opt-side-text {
            font-family: inherit;
            font-size: 13.5px;
            line-height: 1.6;
            color: #1d1d1f;
            white-space: pre-wrap;
            word-break: break-word;
            margin-bottom: 12px;
            flex: 1;
        }
        .opt-side-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 10px;
        }
        .opt-badge-violation {
            display: inline-block;
            font-size: 10px;
            font-weight: 600;
            background: rgba(255, 59, 48, 0.08);
            color: #ff3b30;
            border: 1px solid rgba(255, 59, 48, 0.2);
            border-radius: 980px;
            padding: 3px 9px;
            letter-spacing: 0.01em;
        }
        .opt-badge-benefit {
            display: inline-block;
            font-size: 10px;
            font-weight: 600;
            background: rgba(52, 199, 89, 0.12);
            color: #15803d;
            border: 1px solid rgba(52, 199, 89, 0.25);
            border-radius: 980px;
            padding: 3px 9px;
            letter-spacing: 0.01em;
        }
        .opt-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }
        @media (max-width: 900px) {
            .opt-grid {
                grid-template-columns: 1fr;
            }
        }
        .opt-score-card {
            background: #ffffff;
            border-radius: 14px;
            border: 1px solid rgba(0, 0, 0, 0.06);
            padding: 16px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
        }
        .opt-score-badge {
            font-size: 28px;
            font-weight: 700;
            line-height: 1;
            letter-spacing: -0.02em;
        }
        .opt-score-badge.good { color: #34c759; }
        .opt-score-badge.warn { color: #ff9500; }
        .opt-score-badge.bad { color: #ff3b30; }
        .opt-diff-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-top: 14px;
        }
        @media (max-width: 900px) {
            .opt-diff-container {
                grid-template-columns: 1fr;
            }
        }
        .opt-diff-panel {
            border: 1px solid rgba(0, 0, 0, 0.06);
            background: #ffffff;
            border-radius: 14px;
            padding: 16px;
            display: flex;
            flex-direction: column;
        }
        .opt-diff-panel.optimized {
            border-color: rgba(52, 199, 89, 0.35);
            background: rgba(52, 199, 89, 0.02);
        }
        .opt-diff-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            padding-bottom: 8px;
            border-bottom: 1px solid rgba(0, 0, 0, 0.05);
        }
        .opt-diff-text {
            font-family: inherit;
            font-size: 13.5px;
            line-height: 1.65;
            white-space: pre-wrap;
            word-break: break-word;
            flex: 1;
            color: #1d1d1f;
            padding: 6px 0;
        }
        .opt-issue-item {
            display: flex;
            gap: 10px;
            padding: 11px 14px;
            border-left: 3px solid #86868b;
            background: #fafafc;
            border-radius: 0 10px 10px 0;
            margin-bottom: 8px;
            font-size: 13px;
        }
        .opt-issue-item.sev-critical {
            border-left-color: #ff3b30;
            background: rgba(255, 59, 48, 0.05);
        }
        .opt-issue-item.sev-high {
            border-left-color: #ff9500;
            background: rgba(255, 149, 0, 0.05);
        }
        .opt-issue-item.sev-medium {
            border-left-color: #ffcc00;
            background: rgba(255, 204, 0, 0.08);
        }
        .opt-issue-item.sev-low {
            border-left-color: #0071e3;
            background: rgba(0, 113, 227, 0.05);
        }
        .opt-issue-item.sev-info {
            border-left-color: #86868b;
            background: #f5f5f7;
        }
        .opt-pill-preset {
            padding: 5px 13px;
            font-size: 12px;
            font-weight: 500;
            background: #ffffff;
            border: 1px solid #d2d2d7;
            border-radius: 980px;
            color: #1d1d1f;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .opt-pill-preset:hover {
            border-color: #0071e3;
            background: #0071e3;
            color: #ffffff;
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(0, 113, 227, 0.2);
        }

        /* Multi-Variant Selector Styles */
        .opt-variant-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 16px;
        }
        @media (max-width: 900px) {
            .opt-variant-grid {
                grid-template-columns: 1fr;
            }
        }
        .opt-variant-card {
            border: 1.5px solid rgba(0, 0, 0, 0.08);
            border-radius: 14px;
            background: #ffffff;
            padding: 14px 16px;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            position: relative;
        }
        .opt-variant-card:hover {
            border-color: #86868b;
            background: #fafafc;
        }
        .opt-variant-card.active {
            border-color: #0071e3;
            background: rgba(0, 113, 227, 0.03);
            box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.12);
        }
        .opt-variant-title {
            font-size: 13.5px;
            font-weight: 600;
            letter-spacing: -0.01em;
            color: #1d1d1f;
            margin-bottom: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .opt-variant-desc {
            font-size: 11.5px;
            color: #86868b;
            line-height: 1.4;
        }
        
        /* Word Diff Styles */
        .diff-del {
            background-color: rgba(255, 59, 48, 0.12);
            color: #d70015;
            text-decoration: line-through;
            padding: 1px 5px;
            border-radius: 4px;
            font-weight: 500;
        }
        .diff-ins {
            background-color: rgba(52, 199, 89, 0.15);
            color: #15803d;
            text-decoration: none;
            padding: 1px 5px;
            border-radius: 4px;
            font-weight: 600;
        }
        .opt-diff-view-box {
            border: 1px solid rgba(0, 0, 0, 0.06);
            background: #ffffff;
            border-radius: 12px;
            padding: 16px;
            font-size: 13.5px;
            line-height: 1.7;
            color: #1d1d1f;
        }

        /* SERP Google Preview Card */
        .serp-box {
            border: 1px solid #dfe1e5;
            background: #ffffff;
            padding: 16px 18px;
            border-radius: 12px;
            font-family: Arial, sans-serif;
            max-width: 650px;
        }
        .serp-url-row {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 4px;
        }
        .serp-favicon {
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: #1a73e8;
            display: inline-block;
        }
        .serp-site-name {
            font-size: 12px;
            color: #202124;
            font-weight: normal;
        }
        .serp-breadcrumb {
            font-size: 12px;
            color: #5f6368;
        }
        .serp-title {
            font-size: 20px;
            line-height: 1.3;
            color: #1a0dab;
            text-decoration: none;
            font-weight: normal;
            margin-bottom: 4px;
            display: block;
            cursor: pointer;
        }
        .serp-title:hover {
            text-decoration: underline;
        }
        .serp-snippet {
            font-size: 14px;
            line-height: 1.58;
            color: #4d5156;
            word-wrap: break-word;
        }
        .serp-pixel-bar {
            height: 4px;
            background: #e5e5ea;
            border-radius: 980px;
            overflow: hidden;
            margin-top: 4px;
        }
        .serp-pixel-fill {
            height: 100%;
            background: #34c759;
            transition: width 0.2s ease;
            border-radius: 980px;
        }
        .serp-pixel-fill.warn { background: #ff9500; }
        .serp-pixel-fill.danger { background: #ff3b30; }

        /* AI Overview / Perplexity Citation Box */
        .ai-preview-box {
            border: 1px solid rgba(0, 113, 227, 0.2);
            background: rgba(0, 113, 227, 0.02);
            padding: 18px;
            border-radius: 14px;
            margin-bottom: 16px;
        }
        .ai-preview-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .ai-preview-badge {
            font-size: 11px;
            font-weight: 600;
            color: #0071e3;
            background: rgba(0, 113, 227, 0.08);
            padding: 3px 10px;
            border-radius: 980px;
            letter-spacing: 0.02em;
        }
        .ai-preview-quote {
            font-size: 14px;
            line-height: 1.65;
            color: #1d1d1f;
            margin-bottom: 12px;
        }
        .ai-sources-row {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }
        .ai-source-chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 11px;
            background: #ffffff;
            border: 1px solid rgba(0, 113, 227, 0.2);
            border-radius: 980px;
            font-size: 11px;
            color: #0071e3;
            font-weight: 500;
        }

        /* View Mode Tabs & Exporter Styles */
        .opt-view-tabs {
            display: flex;
            gap: 4px;
            background: rgba(0, 0, 0, 0.05);
            padding: 3px;
            border-radius: 10px;
            margin-bottom: 16px;
            overflow-x: auto;
        }
        .opt-view-tab {
            padding: 7px 14px;
            font-size: 12px;
            font-weight: 500;
            color: #6e6e73;
            background: transparent;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            letter-spacing: -0.01em;
            transition: all 0.2s ease;
            white-space: nowrap;
        }
        .opt-view-tab:hover {
            color: #1d1d1f;
        }
        .opt-view-tab.active {
            background: #ffffff;
            color: #1d1d1f;
            font-weight: 600;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
        }
        .opt-code-box {
            background: #1c1c1e;
            color: #f5f5f7;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 12px;
            line-height: 1.6;
            padding: 16px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            overflow-x: auto;
            white-space: pre-wrap;
            word-break: break-all;
        }
        .opt-export-bar {
            display: flex;
            gap: 8px;
            align-items: center;
            justify-content: flex-end;
            margin-bottom: 12px;
            flex-wrap: wrap;
        }

        /* Security Badges & Cards — Apple Translucent Pills */
        .badge-crit {
            background: rgba(255, 59, 48, 0.1);
            color: #ff3b30;
            border: 1px solid rgba(255, 59, 48, 0.25);
            padding: 3px 9px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 980px;
        }
        .badge-high {
            background: rgba(255, 149, 0, 0.12);
            color: #c25e00;
            border: 1px solid rgba(255, 149, 0, 0.25);
            padding: 3px 9px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 980px;
        }
        .badge-med {
            background: rgba(255, 204, 0, 0.14);
            color: #946800;
            border: 1px solid rgba(255, 204, 0, 0.3);
            padding: 3px 9px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 980px;
        }
        .badge-low {
            background: rgba(0, 113, 227, 0.1);
            color: #0071e3;
            border: 1px solid rgba(0, 113, 227, 0.25);
            padding: 3px 9px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 980px;
        }
        .badge-pass {
            background: rgba(52, 199, 89, 0.12);
            color: #15803d;
            border: 1px solid rgba(52, 199, 89, 0.25);
            padding: 3px 9px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 980px;
        }
        .finding-card {
            border: 1px solid rgba(0, 0, 0, 0.06);
            background: #ffffff;
            border-radius: 14px;
            padding: 18px 20px;
            margin-bottom: 12px;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.02);
            transition: all 0.2s ease;
        }
        .finding-card:hover {
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.05);
            border-color: rgba(0, 0, 0, 0.1);
        }
        .code-block {
            background: #1c1c1e;
            color: #f5f5f7;
            padding: 14px 16px;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 11.5px;
            line-height: 1.5;
            overflow-x: auto;
            white-space: pre-wrap;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 10px;
            max-height: 380px;
        }

        /* WordPress SEO Plugin Suite Styles */
        .plg-subnav-btn {
            padding: 7px 16px;
            font-size: 12px;
            font-weight: 500;
            background: transparent;
            color: #6e6e73;
            border: none;
            border-radius: 980px;
            cursor: pointer;
            letter-spacing: -0.01em;
            transition: all 0.2s ease;
        }
        .plg-subnav-btn:hover {
            color: #1d1d1f;
            background: rgba(0, 0, 0, 0.04);
        }
        .plg-subnav-btn.active {
            background: #1d1d1f;
            color: #ffffff;
            font-weight: 600;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
        }
        .plg-test-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }
        @media (max-width: 800px) {
            .plg-test-grid {
                grid-template-columns: 1fr;
            }
        }
        .plg-test-item {
            border: 1px solid rgba(0, 0, 0, 0.06);
            background: #ffffff;
            border-radius: 12px;
            padding: 12px 14px;
            display: flex;
            gap: 10px;
            align-items: flex-start;
        }
        .plg-test-badge {
            font-size: 10px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 980px;
            letter-spacing: 0.02em;
            white-space: nowrap;
        }
        .plg-test-badge.passed {
            background: rgba(52, 199, 89, 0.12);
            color: #15803d;
            border: 1px solid rgba(52, 199, 89, 0.25);
        }
        .plg-test-badge.failed {
            background: rgba(255, 59, 48, 0.1);
            color: #ff3b30;
            border: 1px solid rgba(255, 59, 48, 0.25);
        }
        .plg-test-badge.warning {
            background: rgba(255, 149, 0, 0.12);
            color: #c25e00;
            border: 1px solid rgba(255, 149, 0, 0.25);
        }
        .plg-field-row {
            margin-bottom: 14px;
        }
        .plg-field-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
        }
        .plg-field-label {
            font-size: 12px;
            font-weight: 600;
            color: #1d1d1f;
            letter-spacing: -0.01em;
        }
        .plg-copy-input-group {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        .plg-copy-input-group input, .plg-copy-input-group textarea {
            flex: 1;
            background: #ffffff;
            border: 1px solid #d2d2d7;
            border-radius: 10px;
            font-family: inherit;
            font-size: 13px;
            padding: 9px 12px;
            color: #1d1d1f;
        }
        .plg-copy-input-group input:focus, .plg-copy-input-group textarea:focus {
            outline: none;
            border-color: #0071e3;
            box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.15);
        }
        .plg-btn-copy {
            padding: 8px 16px;
            font-size: 12px;
            font-weight: 600;
            background: #ffffff;
            color: #0071e3;
            border: 1px solid #d2d2d7;
            border-radius: 980px;
            cursor: pointer;
            letter-spacing: -0.01em;
            white-space: nowrap;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .plg-btn-copy:hover {
            background: #0071e3;
            color: #ffffff;
            border-color: #0071e3;
            box-shadow: 0 2px 8px rgba(0, 113, 227, 0.2);
        }
        .plg-btn-copy.copied {
            background: #34c759 !important;
            border-color: #34c759 !important;
            color: #ffffff !important;
        }

        /* Floating Toast Notification */
        #reset-toast {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: rgba(29, 29, 31, 0.88);
            color: #ffffff;
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            padding: 12px 22px;
            border-radius: 980px;
            font-size: 13px;
            font-weight: 500;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.18);
            border: 1px solid rgba(255, 255, 255, 0.12);
            z-index: 9999;
            transition: opacity 0.3s ease, transform 0.3s ease;
        }
"""

def update_web_ui():
    with open("web_ui.py", "r", encoding="utf-8") as f:
        content = f.read()

    style_start = content.find("<style>")
    style_end = content.find("</style>")

    if style_start == -1 or style_end == -1:
        print("ERROR: <style> or </style> not found")
        sys.exit(1)

    new_content = content[:style_start + len("<style>\n")] + apple_css + content[style_end:]

    # Also update inline borders in Tab 4 subnav bar if present
    old_subnav_bar = '<div style="display: flex; gap: 8px; margin-bottom: 20px; border-bottom: 2px solid #111827; padding-bottom: 12px; align-items: center; justify-content: space-between; flex-wrap: wrap;">'
    new_subnav_bar = '<div style="display: flex; gap: 12px; margin-bottom: 22px; padding-bottom: 14px; align-items: center; justify-content: space-between; flex-wrap: wrap; border-bottom: 1px solid rgba(0, 0, 0, 0.06);">'
    if old_subnav_bar in new_content:
        new_content = new_content.replace(old_subnav_bar, new_subnav_bar)

    with open("web_ui.py", "w", encoding="utf-8") as f:
        f.write(new_content)

    print("SUCCESS: web_ui.py updated with Apple UI Design System.")

if __name__ == "__main__":
    update_web_ui()

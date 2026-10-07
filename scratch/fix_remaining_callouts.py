def fix_callouts():
    with open("web_ui.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Line 2172
    content = content.replace(
        'style="margin-bottom: 14px; padding: 16px; border-left: 3px solid #b91c1c;"',
        'style="margin-bottom: 14px; padding: 16px; border-left: 3px solid #ff3b30; border-radius: 14px; background: rgba(255, 59, 48, 0.04);"'
    )

    # Line 4291
    content = content.replace(
        'style="margin-bottom: 14px; padding: 12px 16px; background: #fdf2f2; border: 1px solid #fecaca; border-left: 3px solid #b91c1c;"',
        'style="margin-bottom: 14px; padding: 12px 16px; background: rgba(255, 59, 48, 0.05); border: 1px solid rgba(255, 59, 48, 0.15); border-left: 3px solid #ff3b30; border-radius: 12px;"'
    )

    # Line 5431
    content = content.replace(
        'style="padding: 8px 12px; background: #f0fdf4; border-left: 3px solid #15803d; font-size: 12px; color: #15803d; font-weight: 600;"',
        'style="padding: 8px 14px; background: rgba(52, 199, 89, 0.08); border-left: 3px solid #34c759; border-radius: 10px; font-size: 12px; color: #248a3d; font-weight: 600;"'
    )

    # Line 5436
    content = content.replace(
        'style="padding: 8px 12px; background: #f0fdf4; border-left: 3px solid #15803d; font-size: 12px; color: #111827;"',
        'style="padding: 8px 14px; background: rgba(52, 199, 89, 0.06); border-left: 3px solid #34c759; border-radius: 10px; font-size: 12px; color: #1d1d1f;"'
    )

    # Line 5488 (Optimization Rationale)
    content = content.replace(
        'color: #4b5563; margin-bottom: 10px; background: #f9fafb; padding: 6px 10px; border-left: 2px solid #111827;',
        'color: #1d1d1f; margin-bottom: 10px; background: rgba(0, 113, 227, 0.05); padding: 7px 12px; border-left: 3px solid #0071e3; border-radius: 8px;'
    )

    # Line 6295 (Remediation callout in Security tab)
    content = content.replace(
        'line-height: 1.5; background: #f0fdf4; padding: 6px 10px; border-left: 3px solid #15803d;',
        'line-height: 1.5; background: rgba(52, 199, 89, 0.06); padding: 8px 12px; border-left: 3px solid #34c759; border-radius: 8px;'
    )

    with open("web_ui.py", "w", encoding="utf-8") as f:
        f.write(content)

    print("SUCCESS: Callouts updated to Apple HIG styling.")

if __name__ == "__main__":
    fix_callouts()

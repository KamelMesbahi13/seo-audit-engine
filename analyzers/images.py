"""agy-seo: Image optimization analyzer."""

import re
from urllib.parse import urlparse
from utils import clamp_score


def analyze_images(page_data: dict) -> dict:
    """Analyze image SEO and optimization."""
    findings = []
    fixes = []
    score = 100

    images = page_data.get("images", [])
    url = page_data["url"]

    if not images:
        findings.append({"category": "Images", "severity": "info",
            "issue": "No images found on this page",
            "detail": "Pages with relevant images can improve engagement and appear in Google Images."})
        return {"analyzer": "images", "score": 100, "findings": findings, "fixes": fixes,
                "total_images": 0}

    # -------------------------------------------------------------------
    # 1. Alt text analysis
    # -------------------------------------------------------------------
    no_alt = []
    empty_alt = []
    long_alt = []
    keyword_stuffed_alt = []
    file_name_alt = []

    for img in images:
        src = img.get("src", "")
        alt = img.get("alt")

        if alt is None:
            # No alt attribute at all
            no_alt.append(src)
        elif alt.strip() == "":
            # Empty alt (might be decorative)
            empty_alt.append(src)
        else:
            alt_text = alt.strip()
            if len(alt_text) > 125:
                long_alt.append({"src": src, "alt": alt_text, "length": len(alt_text)})
            
            # Check for file-name-as-alt pattern
            if re.match(r'^[\w-]+\.(jpg|jpeg|png|gif|webp|svg|avif)$', alt_text, re.I):
                file_name_alt.append({"src": src, "alt": alt_text})
            
            # Check for keyword stuffing (many commas or repeated words)
            if alt_text.count(",") > 3:
                keyword_stuffed_alt.append({"src": src, "alt": alt_text})

    if no_alt:
        ratio = len(no_alt) / len(images)
        if ratio > 0.5:
            score -= 35
        elif ratio > 0.2:
            score -= 25
        else:
            score -= min(len(no_alt) * 5, 15)
        findings.append({"category": "Alt Text", "severity": "critical",
            "issue": f"{len(no_alt)}/{len(images)} image(s) missing alt attribute ({ratio:.0%})",
            "detail": "Images without alt attributes are inaccessible to screen readers and invisible to search engines.\n"
                      + "\n".join(f"  - {src}" for src in no_alt[:8])})
        fixes.append({"issue": "Missing alt attributes",
            "fix": "Add descriptive alt text to every image:\n\n" +
                   "\n".join(f'<img src="{src}" alt="Describe what this image shows" />'
                             for src in no_alt[:5]) +
                   "\n\nFor decorative images, use an empty alt: alt=\"\""})

    if file_name_alt:
        score -= min(len(file_name_alt) * 2, 8)
        findings.append({"category": "Alt Text", "severity": "high",
            "issue": f"{len(file_name_alt)} image(s) using file name as alt text",
            "detail": "File names like 'IMG_2045.jpg' provide no value.\n" +
                      "\n".join(f'  - alt="{fa["alt"]}" src="{fa["src"]}"' for fa in file_name_alt[:5])})
        fixes.append({"issue": "File name as alt text",
            "fix": "Replace file-name alt text with descriptive text:\n" +
                   "\n".join(f'  Change: alt="{fa["alt"]}"\n  To: alt="Descriptive text about the image content"'
                             for fa in file_name_alt[:3])})

    if keyword_stuffed_alt:
        score -= min(len(keyword_stuffed_alt) * 2, 6)
        findings.append({"category": "Alt Text", "severity": "medium",
            "issue": f"{len(keyword_stuffed_alt)} image(s) with keyword-stuffed alt text",
            "detail": "Alt text with many comma-separated keywords is seen as spam.\n" +
                      "\n".join(f'  - alt="{ka["alt"][:80]}..."' for ka in keyword_stuffed_alt[:5])})

    if long_alt:
        findings.append({"category": "Alt Text", "severity": "low",
            "issue": f"{len(long_alt)} image(s) with overly long alt text (>125 chars)",
            "detail": "Keep alt text concise — screen readers read the entire text.\n" +
                      "\n".join(f'  - {la["length"]} chars: "{la["alt"][:60]}..."' for la in long_alt[:5])})

    # -------------------------------------------------------------------
    # 2. Image dimensions (CLS prevention)
    # -------------------------------------------------------------------
    def _display_src(src: str) -> str:
        if not src:
            return ""
        if src.startswith("data:"):
            return "[inline base64 image data]"
        return src

    no_dimensions = [img for img in images if img.get("src") and
                     (not img.get("width") or not img.get("height"))]
    if no_dimensions:
        score -= min(len(no_dimensions) * 2, 10)
        findings.append({"category": "CLS Prevention", "severity": "high",
            "issue": f"{len(no_dimensions)} image(s) missing width/height — causes layout shift",
            "detail": "Without explicit dimensions, the browser can't reserve space before the image loads.\n" +
                      "\n".join(f"  - {_display_src(img['src'])}" for img in no_dimensions[:5])})
        sample_fix_srcs = [img['src'] for img in no_dimensions if not img.get('src', '').startswith('data:')]
        if not sample_fix_srcs:
            sample_fix_srcs = ["image.webp"]
        fixes.append({"issue": "Missing image width/height dimensions",
            "fix": "Specify explicit width and height attributes on all <img> tags to eliminate Cumulative Layout Shift (CLS):\n"
                   + "\n".join(f'<img src="{s}" width="800" height="600" alt="..." />' for s in sample_fix_srcs[:3])
                   + "\nOr use CSS aspect-ratio: img { aspect-ratio: 16/9; width: 100%; height: auto; }"})

    # -------------------------------------------------------------------
    # 3. Lazy loading
    # -------------------------------------------------------------------
    below_fold_no_lazy = [img for img in images[3:] if img.get("src") and
                          img.get("loading", "") != "lazy"]
    if len(below_fold_no_lazy) > 2:
        score -= 3
        findings.append({"category": "Lazy Loading", "severity": "medium",
            "issue": f"{len(below_fold_no_lazy)} below-the-fold images not using lazy loading",
            "detail": "Add loading=\"lazy\" to images below the fold to improve initial page load."})
        sample_lazy_srcs = [img['src'] for img in below_fold_no_lazy if not img.get('src', '').startswith('data:')]
        if not sample_lazy_srcs:
            sample_lazy_srcs = ["image.webp"]
        fixes.append({"issue": "Missing lazy loading",
            "fix": "Add loading=\"lazy\" to below-the-fold images:\n" +
                   "\n".join(f'<img src="{s}" loading="lazy" alt="..." />'
                             for s in sample_lazy_srcs[:3])})

    # -------------------------------------------------------------------
    # 4. Image format analysis
    # -------------------------------------------------------------------
    format_counts = {"jpg/jpeg": 0, "png": 0, "gif": 0, "svg": 0,
                     "webp": 0, "avif": 0, "other": 0}
    for img in images:
        src = img.get("src", "").lower()
        if ".jpg" in src or ".jpeg" in src:
            format_counts["jpg/jpeg"] += 1
        elif ".png" in src:
            format_counts["png"] += 1
        elif ".gif" in src:
            format_counts["gif"] += 1
        elif ".svg" in src:
            format_counts["svg"] += 1
        elif ".webp" in src:
            format_counts["webp"] += 1
        elif ".avif" in src:
            format_counts["avif"] += 1
        elif src:
            format_counts["other"] += 1

    legacy_count = format_counts["jpg/jpeg"] + format_counts["png"] + format_counts["gif"]
    modern_count = format_counts["webp"] + format_counts["avif"]

    if legacy_count > 0 and modern_count == 0:
        score -= 5
        findings.append({"category": "Image Format", "severity": "medium",
            "issue": f"No modern image formats used ({legacy_count} legacy images)",
            "detail": f"Format breakdown: " +
                      ", ".join(f"{k}: {v}" for k, v in format_counts.items() if v > 0) +
                      "\nWebP/AVIF can reduce file sizes by 25-50%."})

    # -------------------------------------------------------------------
    # 5. Srcset / responsive images
    # -------------------------------------------------------------------
    has_srcset = [img for img in images if img.get("srcset")]
    if images and not has_srcset:
        findings.append({"category": "Responsive Images", "severity": "low",
            "issue": "No responsive images (srcset) found",
            "detail": "Using srcset serves optimally-sized images for each device, reducing bandwidth."})
        fixes.append({"issue": "No responsive images",
            "fix": "Add srcset for key images:\n\n"
                   '<img src="image-800.webp"\n'
                   '     srcset="image-400.webp 400w,\n'
                   '            image-800.webp 800w,\n'
                   '            image-1200.webp 1200w"\n'
                   '     sizes="(max-width: 600px) 400px,\n'
                   '           (max-width: 1200px) 800px,\n'
                   '           1200px"\n'
                   '     alt="Description" width="800" height="600" />'})

    return {
        "analyzer": "images",
        "score": clamp_score(score),
        "findings": findings,
        "fixes": fixes,
        "total_images": len(images),
        "missing_alt": len(no_alt),
        "format_counts": format_counts,
    }

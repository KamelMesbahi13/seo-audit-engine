#!/usr/bin/env python3
"""
agy-seo: Main orchestrator — Full-site SEO audit toolkit for Antigravity.

Usage:
    python agy_seo.py audit <URL> [--max-pages N] [--output PATH]

This is the single entry point. It orchestrates:
    1. Full-site crawl (sitemap + internal link discovery)
    2. Per-page analysis (8 analyzers)
    3. Site-wide analysis (robots, sitemaps, cross-page patterns)
    4. PDF report generation
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from urllib.parse import urlparse

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add the skill directory to path
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SKILL_DIR)

from crawler import SiteCrawler
from utils import normalize_url, clamp_score
from analyzers.technical import analyze_technical, analyze_robots_and_sitemaps
from analyzers.onpage import analyze_onpage
from analyzers.content import analyze_content
from analyzers.schema_analyzer import analyze_schema
from analyzers.performance import analyze_performance
from analyzers.geo import analyze_geo
from analyzers.images import analyze_images
from analyzers.links import analyze_links
from reporter import build_report_html, render_pdf
from remediation import generate_all_remediation_files


def run_audit(url: str, max_pages: int = None, output_path: str = None,
              report_mode: str = "detailed", cancel_check: callable = None) -> dict:
    """Run a complete SEO audit on a website.
    
    Args:
        report_mode: "detailed", "short", or "both"
        cancel_check: optional callable returning True if audit should abort
    """
    
    start_time = time.monotonic()
    domain = urlparse(url).netloc
    
    effective_max_pages = max_pages if (max_pages is not None and max_pages > 0) else None
    pages_display = f"{effective_max_pages} pages" if effective_max_pages is not None else "Unlimited (All Pages of the Website)"

    print(f"\n{'='*60}")
    print(f"  InersiaLab Software Department — SEO Audit Engine")
    print(f"  Target: {url}")
    print(f"  Crawl Scope: {pages_display}")
    print(f"  Report Mode: {report_mode.upper()}")
    print(f"{'='*60}\n")

    # ------------------------------------------------------------------
    # PHASE 1: Crawl the entire site
    # ------------------------------------------------------------------
    print("[Phase 1/4] Crawling site...")
    crawler = SiteCrawler(url, max_pages=effective_max_pages, max_depth=None, cancel_check=cancel_check)
    crawl_result = crawler.crawl()
    
    if cancel_check and cancel_check():
        print("  [audit] Audit stopped during crawl by user.")
        raise KeyboardInterrupt("Audit cancelled by user.")
    
    pages = crawl_result["pages"]
    robots_data = crawl_result["robots_data"]
    robots_raw = crawl_result["robots_txt"]
    sitemap_urls = crawl_result["sitemap_urls"]
    crawl_errors = crawl_result["errors"]
    
    # Filter to pages with parsed content
    valid_pages = {
        norm_url: page for norm_url, page in pages.items() 
        if page.get("parsed") is not None
    }
    
    print(f"\n  Crawled {len(pages)} pages, {len(valid_pages)} with content, {len(crawl_errors)} errors\n")

    # ------------------------------------------------------------------
    # PHASE 2: Analyze each page (with ETA timer)
    # ------------------------------------------------------------------
    total_pages = len(valid_pages)
    est_seconds_per_page = 4.5
    print(f"[Phase 2/4] Analyzing {total_pages} pages...")
    
    page_results = {}
    page_count = 0
    phase2_start = time.monotonic()
    
    for norm_url, page_info in valid_pages.items():
        if cancel_check and cancel_check():
            print("\n  [audit] Analysis interrupted by user stop request.")
            break
        page_count += 1
        page_data = page_info["parsed"]
        fetch_data = page_info["fetch"]
        page_url = page_data["url"]
        
        # Calculate ETA
        if page_count > 1:
            elapsed_p2 = time.monotonic() - phase2_start
            avg_per_page = elapsed_p2 / (page_count - 1)
            remaining_pages = total_pages - page_count + 1
            eta_seconds = int(avg_per_page * remaining_pages)
        else:
            eta_seconds = int(est_seconds_per_page * total_pages)
        
        eta_min, eta_sec = divmod(eta_seconds, 60)
        eta_str = f"{eta_min}m {eta_sec:02d}s" if eta_min > 0 else f"{eta_sec}s"
        
        print(f"  Analyzing [{page_count}/{total_pages}] (ETA: ~{eta_str} remaining): {page_url}")
        
        results = {}
        
        # Run all 8 analyzers
        try:
            results["technical"] = analyze_technical(
                page_data, fetch_data, robots_data, sitemap_urls, robots_raw)
        except Exception as e:
            results["technical"] = {"analyzer": "technical", "score": 0, 
                                    "findings": [{"category": "Error", "severity": "critical",
                                    "issue": f"Analyzer error: {e}", "detail": ""}], "fixes": []}
        
        try:
            results["on_page"] = analyze_onpage(page_data)
        except Exception as e:
            results["on_page"] = {"analyzer": "onpage", "score": 0,
                                  "findings": [{"category": "Error", "severity": "critical",
                                  "issue": f"Analyzer error: {e}", "detail": ""}], "fixes": []}
        
        try:
            results["content_quality"] = analyze_content(page_data)
        except Exception as e:
            results["content_quality"] = {"analyzer": "content", "score": 0,
                                          "findings": [{"category": "Error", "severity": "critical",
                                          "issue": f"Analyzer error: {e}", "detail": ""}], "fixes": []}
        
        try:
            results["schema"] = analyze_schema(page_data)
        except Exception as e:
            results["schema"] = {"analyzer": "schema", "score": 0,
                                  "findings": [{"category": "Error", "severity": "critical",
                                  "issue": f"Analyzer error: {e}", "detail": ""}], "fixes": []}
        
        try:
            results["performance"] = analyze_performance(page_data, fetch_data)
        except Exception as e:
            results["performance"] = {"analyzer": "performance", "score": 0,
                                       "findings": [{"category": "Error", "severity": "critical",
                                       "issue": f"Analyzer error: {e}", "detail": ""}], "fixes": []}
        
        try:
            results["ai_search_geo"] = analyze_geo(page_data, fetch_data, robots_data, all_pages=valid_pages)
        except Exception as e:
            results["ai_search_geo"] = {"analyzer": "geo", "score": 0,
                                         "findings": [{"category": "Error", "severity": "critical",
                                         "issue": f"Analyzer error: {e}", "detail": ""}], "fixes": []}
        
        try:
            results["images"] = analyze_images(page_data)
        except Exception as e:
            results["images"] = {"analyzer": "images", "score": 0,
                                  "findings": [{"category": "Error", "severity": "critical",
                                  "issue": f"Analyzer error: {e}", "detail": ""}], "fixes": []}
        
        try:
            results["links"] = analyze_links(page_data, all_pages=valid_pages)
        except Exception as e:
            results["links"] = {"analyzer": "links", "score": 0,
                                 "findings": [{"category": "Error", "severity": "critical",
                                 "issue": f"Analyzer error: {e}", "detail": ""}], "fixes": []}
        
        page_results[page_url] = results

    # ------------------------------------------------------------------
    # PHASE 3: Site-wide analysis
    # ------------------------------------------------------------------
    print(f"\n[Phase 3/4] Running site-wide analysis...")
    
    site_findings = {}
    
    # Robots & Sitemaps
    site_findings["Robots & Sitemaps"] = analyze_robots_and_sitemaps(
        robots_raw, robots_data, sitemap_urls, url)
    
    # Cross-page pattern detection
    site_findings["Cross-Page Patterns"] = _analyze_cross_page(page_results)

    # ------------------------------------------------------------------
    # Compute aggregate scores (WITH PENALTY FLOOR SYSTEM)
    # ------------------------------------------------------------------
    analyzer_names = ["technical", "on_page", "content_quality", "schema", 
                      "performance", "ai_search_geo", "images", "links"]
    
    site_scores = {}
    for analyzer in analyzer_names:
        scores = []
        finding_count = 0
        has_critical = False
        has_high = False
        for page_url, results in page_results.items():
            if analyzer in results and "score" in results[analyzer]:
                scores.append(results[analyzer]["score"])
            if analyzer in results and "findings" in results[analyzer]:
                for f in results[analyzer].get("findings", []):
                    finding_count += 1
                    sev = f.get("severity", "")
                    if sev == "critical":
                        has_critical = True
                    elif sev == "high":
                        has_high = True
        
        if scores:
            raw_avg = round(sum(scores) / len(scores))
            
            # PENALTY FLOOR: cap score based on total finding count
            if finding_count >= 15:
                raw_avg = min(raw_avg, 60)
            elif finding_count >= 8:
                raw_avg = min(raw_avg, 72)
            elif finding_count >= 4:
                raw_avg = min(raw_avg, 82)
            elif finding_count >= 1:
                raw_avg = min(raw_avg, 92)
            
            # Additional severity caps
            if has_critical:
                raw_avg = min(raw_avg, 75)
            elif has_high:
                raw_avg = min(raw_avg, 85)
            
            site_scores[analyzer.replace("_", " ").title()] = clamp_score(raw_avg)
    
    # Add site-level scores
    for name, result in site_findings.items():
        if isinstance(result, dict) and "score" in result:
            site_scores[name] = result["score"]
    
    # Overall score calculation
    all_scores = list(site_scores.values())
    category_avg = round(sum(all_scores) / len(all_scores)) if all_scores else 0

    # Count issues across all pages and site-wide findings
    total_critical = 0
    total_high = 0
    for page_url, results in page_results.items():
        for an_name, res in results.items():
            if isinstance(res, dict):
                for f in res.get("findings", []):
                    sev = f.get("severity", "")
                    if sev == "critical": total_critical += 1
                    elif sev == "high": total_high += 1
    
    for name, res in site_findings.items():
        if isinstance(res, dict):
            for f in res.get("findings", []):
                sev = f.get("severity", "")
                if sev == "critical": total_critical += 1
                elif sev == "high": total_high += 1

    # Apply strict quality caps based on actual unresolved critical/high defects
    overall_score = category_avg
    if total_critical >= 6:
        overall_score = min(overall_score, 55)
    elif total_critical >= 3:
        overall_score = min(overall_score, 65)
    elif total_critical >= 1:
        overall_score = min(overall_score, 75)
    elif total_high >= 5:
        overall_score = min(overall_score, 80)

    overall_score = clamp_score(overall_score)

    elapsed = time.monotonic() - start_time
    print(f"\n  Analysis complete in {elapsed:.1f}s")
    print(f"  Overall score: {overall_score}/100")

    audit_result = {
        "domain": domain,
        "base_url": url,
        "pages_crawled": len(valid_pages),
        "overall_score": overall_score,
        "site_scores": site_scores,
        "page_results": page_results,
        "site_findings": site_findings,
        "crawl_errors": crawl_errors,
        "elapsed_seconds": round(elapsed, 1),
        "_all_pages": valid_pages,  # Needed by remediation engine
    }

    # ------------------------------------------------------------------
    # PHASE 4: Generate PDF report(s) based on report_mode
    # ------------------------------------------------------------------
    if output_path is None:
        # Default to Downloads folder
        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        safe_domain = domain.replace(".", "_").replace(":", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(downloads, f"SEO_Audit_{safe_domain}_{timestamp}.pdf")
    
    modes_to_generate = []
    if report_mode == "both":
        modes_to_generate = ["detailed", "short"]
    else:
        modes_to_generate = [report_mode]
    
    for mode in modes_to_generate:
        if mode == "short":
            mode_path = output_path.replace(".pdf", "_SHORT.pdf")
        else:
            mode_path = output_path
        
        print(f"\n[Phase 4/4] Generating {mode.upper()} PDF report...")
        print(f"  Output: {mode_path}")
        
        html_content = build_report_html(audit_result, report_mode=mode)
        
        # Save HTML for inspection
        html_path = mode_path.replace(".pdf", ".html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"  HTML saved: {html_path}")
        
        # Save JSON (only for detailed/first mode)
        if mode == modes_to_generate[0]:
            json_path = output_path.replace(".pdf", ".json")
            try:
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(audit_result, f, ensure_ascii=False, indent=2, default=str)
            except Exception:
                pass
        
        # Render PDF
        try:
            render_pdf(html_content, mode_path)
            print(f"  PDF saved: {mode_path}")
        except Exception as e:
            print(f"\n  [ERROR] PDF rendering failed: {e}")
            print(f"  HTML report is available at: {html_path}")

    # ------------------------------------------------------------------
    # PHASE 5: Generate remediation files
    # ------------------------------------------------------------------
    print(f"\n[Phase 5/5] Generating remediation files...")
    remediation_dir = output_path.replace(".pdf", "_remediation")
    try:
        generated_files = generate_all_remediation_files(audit_result, remediation_dir)
        if generated_files:
            print(f"  Generated {len(generated_files)} remediation files:")
            for fname, fpath in generated_files.items():
                print(f"    - {fname}")
            print(f"  Remediation folder: {remediation_dir}")
    except Exception as e:
        print(f"  [WARNING] Remediation generation failed: {e}")

    print(f"\n{'='*60}")
    print(f"  [SUCCESS] AUDIT COMPLETE")
    print(f"  Report: {output_path}")
    if "short" in modes_to_generate:
        print(f"  Short Report: {output_path.replace('.pdf', '_SHORT.pdf')}")
    print(f"  Overall Score: {overall_score}/100")
    print(f"  Pages Analyzed: {len(valid_pages)}")
    print(f"  Remediation Files: {remediation_dir}")
    print(f"  Time: {elapsed:.1f}s")
    print(f"{'='*60}\n")

    return audit_result


def _analyze_cross_page(page_results: dict) -> dict:
    """Detect patterns across multiple pages."""
    findings = []
    fixes = []
    score = 100

    if len(page_results) < 2:
        return {"analyzer": "cross_page", "score": 100, "findings": [], "fixes": []}

    # Check for duplicate titles
    titles = {}
    for page_url, results in page_results.items():
        onpage = results.get("on_page", {})
        # Get title from findings context
        for f in onpage.get("findings", []):
            if f.get("category") == "Title":
                pass  # Title issues already flagged per-page

    # Check for site-wide schema consistency
    pages_without_schema = []
    for page_url, results in page_results.items():
        schema_result = results.get("schema", {})
        if schema_result.get("schemas_found", 0) == 0:
            pages_without_schema.append(page_url)

    if pages_without_schema and len(pages_without_schema) > len(page_results) * 0.5:
        score -= 10
        findings.append({
            "category": "Schema", "severity": "high",
            "issue": f"{len(pages_without_schema)}/{len(page_results)} pages have NO structured data",
            "detail": "More than half of crawled pages lack JSON-LD schema.\n" +
                      "\n".join(f"  - {url}" for url in pages_without_schema[:10]),
        })
        fixes.append({
            "issue": "Site-wide missing schema",
            "fix": "Implement a site-wide schema strategy:\n"
                   "1. Add WebSite + Organization schema to every page (via a shared template/header)\n"
                   "2. Add BreadcrumbList to all interior pages\n"
                   "3. Add page-specific schema (Article for blog posts, Product for products, Service for services)\n"
                   "4. Use a WordPress plugin (Rank Math, Yoast) or a CMS-level JSON-LD template",
        })

    # Check for site-wide image alt issues
    total_images = 0
    missing_alt = 0
    for page_url, results in page_results.items():
        img_result = results.get("images", {})
        total_images += img_result.get("total_images", 0)
        missing_alt += img_result.get("missing_alt", 0)

    if total_images > 0 and missing_alt / total_images > 0.3:
        score -= 8
        findings.append({
            "category": "Images", "severity": "high",
            "issue": f"{missing_alt}/{total_images} images site-wide have no alt text ({missing_alt/total_images:.0%})",
            "detail": "More than 30% of images across the site lack alt attributes.",
        })

    # Average scores report
    avg_scores = {}
    for page_url, results in page_results.items():
        for analyzer_name, result in results.items():
            if isinstance(result, dict) and "score" in result:
                if analyzer_name not in avg_scores:
                    avg_scores[analyzer_name] = []
                avg_scores[analyzer_name].append(result["score"])

    weakest = None
    weakest_score = 100
    for name, scores in avg_scores.items():
        avg = sum(scores) / len(scores)
        if avg < weakest_score:
            weakest_score = avg
            weakest = name

    if weakest and weakest_score < 60:
        findings.append({
            "category": "Site-Wide", "severity": "high",
            "issue": f"Weakest area: {weakest.replace('_', ' ').title()} (avg {weakest_score:.0f}/100)",
            "detail": f"The {weakest.replace('_', ' ')} category has the lowest average score across all pages. "
                      f"Prioritize fixing issues in this category for maximum impact.",
        })

    return {
        "analyzer": "cross_page",
        "score": clamp_score(score),
        "findings": findings,
        "fixes": fixes,
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="agy-seo",
        description="AGY-SEO: Full-site SEO audit toolkit for Antigravity",
    )
    subparsers = parser.add_subparsers(dest="command")

    # Audit command
    audit_parser = subparsers.add_parser("audit", help="Run a full SEO audit")
    audit_parser.add_argument("url", help="Target website URL")
    audit_parser.add_argument("--max-pages", type=int, default=0,
                             help="Maximum pages to crawl (default: 0 = unlimited, crawls all pages)")
    audit_parser.add_argument("--mode", "--format", dest="report_mode", choices=["detailed", "short", "both"],
                             default="detailed", help="Report format: detailed, short, or both (default: detailed)")
    audit_parser.add_argument("--output", "-o", help="Output PDF path (default: ~/Downloads/)")

    args = parser.parse_args()

    if args.command == "audit":
        # Ensure URL has scheme
        url = args.url
        if not url.startswith("http"):
            url = "https://" + url
        
        run_audit(url, max_pages=args.max_pages if args.max_pages > 0 else None,
                  output_path=args.output, report_mode=args.report_mode)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

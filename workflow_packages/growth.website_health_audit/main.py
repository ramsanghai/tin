#!/usr/bin/env python3
"""
Website Health & SEO Audit Workflow
Analyzes website performance, SEO signals, and growth readiness.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional


def run(ctx: Any, inputs: Dict[str, Any]) -> Dict[str, str]:
    """
    Analyze website health metrics and generate actionable audit report.
    
    Expected input format:
    {
        "project_id": "uuid-string",
        "website_data": JSON string containing:
            {
                "domain": "example.com",
                "pages": [
                    {
                        "url": "https://example.com",
                        "title": "Page Title",
                        "meta_description": "Description",
                        "word_count": 500,
                        "h1_count": 1,
                        "images_with_alt": 5,
                        "images_without_alt": 2,
                        "internal_links": 10,
                        "external_links": 3,
                        "broken_links": 0,
                        "load_time_ms": 1200,
                        "mobile_friendly": true,
                        "has_schema": true,
                        "indexed": true,
                        "canonical": "https://example.com"
                    }
                ],
                "seo_signals": {
                    "domain_age_months": 24,
                    "estimated_monthly_traffic": 5000,
                    "backlink_count": 150,
                    "referring_domains": 45,
                    "indexed_pages": 120
                },
                "security": {
                    "has_ssl": true,
                    "has_robots_txt": true,
                    "has_sitemap": true,
                    "core_web_vitals_pass": true
                },
                "social": {
                    "og_tags_pages": 15,
                    "twitter_cards_pages": 12,
                    "avg_social_shares": 8
                }
            }
    }
    """
    try:
        # Parse inputs
        project_id = inputs.get("project_id", "unknown")
        website_json = inputs.get("website_data", "{}")
        
        try:
            website_data = json.loads(website_json)
        except json.JSONDecodeError:
            website_data = {}
        
        # Generate report
        report = generate_report(website_data)
        
        return {
            "path": "reports/WEBSITE_HEALTH_AUDIT.md",
            "content": report
        }
    except Exception as e:
        error_report = f"# Website Health Audit - Error\n\n"
        error_report += f"Failed to process website data: {str(e)}\n\n"
        error_report += f"Please ensure the JSON format is valid and includes required fields.\n"
        return {
            "path": "reports/WEBSITE_HEALTH_AUDIT.md",
            "content": error_report
        }


def generate_report(data: Dict[str, Any]) -> str:
    """Generate markdown audit report."""
    report = []
    
    # Header
    report.append("# Website Health & SEO Audit Report\n")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Domain Info
    domain = data.get("domain", "Unknown")
    report.append(f"\n## Website Overview\n")
    report.append(f"**Domain:** `{domain}`\n")
    
    pages = data.get("pages", [])
    report.append(f"**Pages Audited:** {len(pages)}\n")
    
    seo = data.get("seo_signals", {})
    if seo:
        report.append(f"**Indexed Pages:** {seo.get('indexed_pages', 'N/A')}\n")
        report.append(f"**Est. Monthly Traffic:** {seo.get('estimated_monthly_traffic', 'N/A'):,}\n")
        report.append(f"**Domain Age:** {seo.get('domain_age_months', 'N/A')} months\n")
        report.append(f"**Backlinks:** {seo.get('backlink_count', 'N/A')}\n")
        report.append(f"**Referring Domains:** {seo.get('referring_domains', 'N/A')}\n")
    
    # Security & Technical
    security = data.get("security", {})
    report.append(f"\n## Security & Technical Health\n")
    has_ssl = security.get("has_ssl", False)
    has_robots = security.get("has_robots_txt", False)
    has_sitemap = security.get("has_sitemap", False)
    core_web = security.get("core_web_vitals_pass", False)
    
    report.append(f"- SSL/HTTPS: {'✅ Enabled' if has_ssl else '❌ Missing'}\n")
    report.append(f"- robots.txt: {'✅ Present' if has_robots else '❌ Missing'}\n")
    report.append(f"- XML Sitemap: {'✅ Present' if has_sitemap else '❌ Missing'}\n")
    report.append(f"- Core Web Vitals: {'✅ Pass' if core_web else '⚠️ Needs Work'}\n")
    
    # Page-Level Analysis
    if pages:
        report.append(f"\n## Page-Level Analysis\n")
        
        # Performance metrics
        load_times = [p.get("load_time_ms", 0) for p in pages if isinstance(p.get("load_time_ms"), (int, float))]
        if load_times:
            avg_load = sum(load_times) / len(load_times)
            report.append(f"**Average Page Load Time:** {avg_load:.0f}ms")
            if avg_load > 3000:
                report.append(f" ⚠️ Slow (target: <3000ms)\n")
            else:
                report.append(f" ✅ Good\n")
        
        # Mobile friendliness
        mobile_friendly = sum(1 for p in pages if p.get("mobile_friendly"))
        report.append(f"**Mobile-Friendly Pages:** {mobile_friendly}/{len(pages)}\n")
        if mobile_friendly < len(pages):
            report.append(f"  ⚠️ {len(pages) - mobile_friendly} pages need mobile optimization\n")
        
        # SEO signals
        pages_with_h1 = sum(1 for p in pages if p.get("h1_count", 0) > 0)
        pages_with_meta = sum(1 for p in pages if p.get("meta_description"))
        pages_with_schema = sum(1 for p in pages if p.get("has_schema"))
        
        report.append(f"**Meta Descriptions:** {pages_with_meta}/{len(pages)} pages\n")
        report.append(f"**H1 Tags:** {pages_with_h1}/{len(pages)} pages\n")
        report.append(f"**Schema Markup:** {pages_with_schema}/{len(pages)} pages\n")
        
        # Image optimization
        total_alt_missing = sum(1 for p in pages for _ in range(p.get("images_without_alt", 0)))
        if total_alt_missing > 0:
            report.append(f"**Images Without Alt Text:** {total_alt_missing} (SEO miss + accessibility issue)\n")
        
        # Link health
        total_broken = sum(1 for p in pages if p.get("broken_links", 0) > 0)
        if total_broken > 0:
            report.append(f"**Pages with Broken Links:** {total_broken} (fix for user experience & crawlability)\n")
    
    # Social Signals
    social = data.get("social", {})
    if social:
        report.append(f"\n## Social & Sharing Readiness\n")
        og_pages = social.get("og_tags_pages", 0)
        twitter_pages = social.get("twitter_cards_pages", 0)
        report.append(f"- **Open Graph Tags:** {og_pages} pages\n")
        report.append(f"- **Twitter Cards:** {twitter_pages} pages\n")
        report.append(f"- **Avg Shares Per Page:** {social.get('avg_social_shares', 0)}\n")
        if og_pages < len(pages) * 0.5:
            report.append(f"  ⚠️ Add OG tags to more pages for better social sharing\n")
    
    # Recommendations
    report.append(f"\n## Growth Opportunities (Prioritized)\n")
    
    recommendations = generate_recommendations(data, pages)
    for i, rec in enumerate(recommendations, 1):
        report.append(f"\n**{i}. {rec['title']}**\n")
        report.append(f"Impact: {rec['impact']}\n")
        report.append(f"Action: {rec['action']}\n")
    
    # Summary Score
    report.append(f"\n## Overall Health Score\n")
    score = calculate_health_score(data, pages)
    report.append(f"**{score}/100** - ")
    if score >= 80:
        report.append("Excellent. Continue monitoring and testing improvements.\n")
    elif score >= 60:
        report.append("Good. Address 1-2 high-impact items for quick wins.\n")
    elif score >= 40:
        report.append("Fair. Implement recommended improvements to increase growth potential.\n")
    else:
        report.append("Needs Work. Prioritize security, mobile, and core web vitals.\n")
    
    report.append(f"\n---\n")
    report.append(f"*This audit identifies growth signals and technical readiness. ")
    report.append(f"Test changes before/after to measure impact.*\n")
    
    return "".join(report)


def generate_recommendations(data: Dict[str, Any], pages: List[Dict]) -> List[Dict[str, str]]:
    """Generate prioritized recommendations based on audit data."""
    recs = []
    
    security = data.get("security", {})
    seo = data.get("seo_signals", {})
    social = data.get("social", {})
    
    # Security
    if not security.get("has_ssl"):
        recs.append({
            "title": "Enable SSL/HTTPS",
            "impact": "Critical for trust & SEO ranking",
            "action": "Install SSL certificate (free via Let's Encrypt). Redirect HTTP → HTTPS."
        })
    
    if not security.get("has_sitemap"):
        recs.append({
            "title": "Add XML Sitemap",
            "impact": "Helps search engines crawl all pages",
            "action": "Generate sitemap.xml listing all pages. Submit to Google Search Console."
        })
    
    if not security.get("core_web_vitals_pass"):
        recs.append({
            "title": "Optimize Core Web Vitals",
            "impact": "Google ranking factor; improves UX",
            "action": "Use PageSpeed Insights to identify bottlenecks. Focus on LCP, FID, CLS."
        })
    
    # SEO & Content
    if pages:
        load_times = [p.get("load_time_ms", 0) for p in pages if isinstance(p.get("load_time_ms"), (int, float))]
        if load_times and sum(load_times) / len(load_times) > 3000:
            recs.append({
                "title": "Reduce Page Load Time",
                "impact": "Improves UX, bounce rate, SEO ranking",
                "action": "Compress images, enable caching, use CDN. Test with WebPageTest."
            })
        
        mobile_friendly = sum(1 for p in pages if p.get("mobile_friendly"))
        if mobile_friendly < len(pages):
            recs.append({
                "title": "Fix Mobile Responsiveness",
                "impact": "60%+ traffic is mobile; Google mobile-first indexing",
                "action": "Test on mobile. Use responsive design. Fix viewport meta tags."
            })
        
        pages_with_meta = sum(1 for p in pages if p.get("meta_description"))
        if pages_with_meta < len(pages) * 0.8:
            recs.append({
                "title": "Write Meta Descriptions",
                "impact": "Improves CTR from search results",
                "action": f"Add unique 150-160 char meta descriptions to {len(pages) - pages_with_meta} pages."
            })
    
    # Social
    og_pages = social.get("og_tags_pages", 0)
    if og_pages < len(pages) * 0.7:
        recs.append({
            "title": "Add Open Graph Tags",
            "impact": "Better social sharing appearance; drives referral traffic",
            "action": "Add og:title, og:description, og:image to all pages. Test with Share Debugger."
        })
    
    # Growth signals
    if seo.get("backlink_count", 0) < 50:
        recs.append({
            "title": "Build Backlinks & Referrals",
            "impact": "Domain authority; top ranking factor",
            "action": "Guest post on relevant sites. Reach out to industry publications. Build partnerships."
        })
    
    if seo.get("estimated_monthly_traffic", 0) < 1000:
        recs.append({
            "title": "Expand Content Strategy",
            "impact": "Long-tail keywords; organic growth compounding",
            "action": "Identify 10 keywords with search volume. Create pillar + cluster content."
        })
    
    return recs[:7]  # Return top 7


def calculate_health_score(data: Dict[str, Any], pages: List[Dict]) -> int:
    """Calculate overall health score 0-100."""
    score = 50  # Base
    
    security = data.get("security", {})
    seo = data.get("seo_signals", {})
    
    # Security +20
    if security.get("has_ssl"):
        score += 5
    if security.get("has_robots_txt"):
        score += 5
    if security.get("has_sitemap"):
        score += 5
    if security.get("core_web_vitals_pass"):
        score += 5
    
    # Content +20
    if pages:
        pages_with_meta = sum(1 for p in pages if p.get("meta_description"))
        score += int((pages_with_meta / max(len(pages), 1)) * 10)
        
        mobile_friendly = sum(1 for p in pages if p.get("mobile_friendly"))
        score += int((mobile_friendly / max(len(pages), 1)) * 10)
    
    # SEO Signals +10
    if seo.get("backlink_count", 0) > 50:
        score += 5
    if seo.get("indexed_pages", 0) > 20:
        score += 5
    
    return min(100, score)


if __name__ == "__main__":
    # Test
    test_input = {
        "project_id": "test-uuid",
        "website_data": json.dumps({
            "domain": "example.com",
            "pages": [
                {
                    "url": "https://example.com",
                    "title": "Home",
                    "meta_description": "Welcome",
                    "mobile_friendly": True,
                    "load_time_ms": 1200,
                    "has_schema": True,
                    "indexed": True
                }
            ],
            "seo_signals": {
                "indexed_pages": 50,
                "estimated_monthly_traffic": 3000,
                "backlink_count": 80,
                "referring_domains": 30
            },
            "security": {
                "has_ssl": True,
                "has_robots_txt": True,
                "has_sitemap": True,
                "core_web_vitals_pass": True
            }
        })
    }
    
    result = run(None, test_input)
    print(result["content"])

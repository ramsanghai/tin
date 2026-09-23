"""
Analyze GitHub repository engagement signals.

Parse repository metadata, commits, issues and releases to identify:
- Commit velocity and consistency
- Issue resolution rate and age
- Release frequency and adoption
- Contributor participation trends
"""

import json
import re
from datetime import datetime, timedelta
from collections import defaultdict, Counter


def run(ctx, inputs):
    """Parse GitHub repository data and generate engagement summary."""
    
    try:
        data = json.loads(inputs["repo_data"])
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in repo_data: {str(e)}")
    
    # Extract and validate required fields
    repo = data.get("repository", data)
    if not isinstance(repo, dict):
        raise ValueError("repo_data must contain repository metadata")
    
    repo_name = repo.get("name", "Unknown")
    repo_url = repo.get("html_url") or repo.get("url", "")
    description = repo.get("description", "")
    
    # Extract components
    commits = data.get("recent_commits", [])
    if not isinstance(commits, list):
        commits = []
    
    issues = data.get("issues", [])
    if not isinstance(issues, list):
        issues = []
    
    releases = data.get("releases", [])
    if not isinstance(releases, list):
        releases = []
    
    # Validate we have reasonable data
    if not commits and not issues:
        raise ValueError("repo_data must include commits or issues")
    
    # Analyze metrics
    metrics = {
        "repo_name": repo_name,
        "repo_url": repo_url,
        "stars": repo.get("stargazers_count", 0),
        "forks": repo.get("forks_count", 0),
        "watchers": repo.get("watchers_count", 0),
        "open_issues": repo.get("open_issues_count", 0),
        "language": repo.get("language", "Not specified"),
    }
    
    # Commit analysis
    commit_analysis = analyze_commits(commits)
    
    # Issue analysis
    issue_analysis = analyze_issues(issues)
    
    # Release analysis
    release_analysis = analyze_releases(releases)
    
    # Generate report
    report = generate_report(metrics, commit_analysis, issue_analysis, release_analysis)
    
    return {
        "path": "reports/REPO_ENGAGEMENT_SUMMARY.md",
        "content": report,
    }


def analyze_commits(commits):
    """Analyze commit patterns and velocity."""
    if not commits:
        return {"total": 0, "velocity": "No data"}
    
    commit_dates = []
    commit_authors = Counter()
    
    for commit in commits:
        # Handle nested commit object structure
        commit_obj = commit.get("commit", commit)
        author = commit_obj.get("author", {})
        author_name = author.get("name") if isinstance(author, dict) else "Unknown"
        
        if author_name and author_name != "Unknown":
            commit_authors[author_name] += 1
        
        # Parse commit date
        date_str = commit_obj.get("committer", {})
        if isinstance(date_str, dict):
            date_str = date_str.get("date", "")
        
        if date_str:
            try:
                date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                commit_dates.append(date)
            except (ValueError, AttributeError):
                pass
    
    analysis = {
        "total": len(commits),
        "authors": len(commit_authors),
        "top_contributors": commit_authors.most_common(3) if commit_authors else [],
    }
    
    # Calculate velocity
    if len(commit_dates) > 1:
        commit_dates.sort()
        time_span = (commit_dates[-1] - commit_dates[0]).days
        if time_span > 0:
            analysis["commits_per_day"] = round(len(commit_dates) / time_span, 2)
            analysis["velocity_status"] = (
                "Active" if analysis["commits_per_day"] > 0.5 else
                "Moderate" if analysis["commits_per_day"] > 0.2 else
                "Inactive"
            )
        else:
            analysis["velocity_status"] = "Recent activity only"
    
    return analysis


def analyze_issues(issues):
    """Analyze issue patterns and resolution."""
    if not issues:
        return {"total": 0, "health": "No issues tracked"}
    
    open_count = 0
    closed_count = 0
    ages = []
    resolution_times = []
    
    now = datetime.now(datetime.now().astimezone().tzinfo)
    
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        
        state = issue.get("state", "").lower()
        
        if state == "open":
            open_count += 1
            created_at = issue.get("created_at", "")
            if created_at:
                try:
                    created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    age_days = (now - created).days
                    if age_days >= 0:
                        ages.append(age_days)
                except (ValueError, TypeError):
                    pass
        
        elif state == "closed":
            closed_count += 1
            created_at = issue.get("created_at", "")
            closed_at = issue.get("closed_at", "")
            
            if created_at and closed_at:
                try:
                    created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    closed = datetime.fromisoformat(closed_at.replace("Z", "+00:00"))
                    resolution_days = (closed - created).days
                    if resolution_days >= 0:
                        resolution_times.append(resolution_days)
                except (ValueError, TypeError):
                    pass
    
    total = open_count + closed_count
    analysis = {
        "total": total,
        "open": open_count,
        "closed": closed_count,
        "closure_rate": round((closed_count / total * 100), 1) if total > 0 else 0,
    }
    
    if ages:
        avg_age = sum(ages) / len(ages)
        analysis["avg_open_issue_age_days"] = round(avg_age)
        analysis["oldest_open_issue_days"] = max(ages)
        
        if avg_age > 180:
            analysis["age_concern"] = "Old open issues: consider triaging"
        elif avg_age > 60:
            analysis["age_concern"] = "Some stale issues: review prioritization"
    
    if resolution_times:
        avg_resolution = sum(resolution_times) / len(resolution_times)
        analysis["avg_resolution_time_days"] = round(avg_resolution)
        
        if avg_resolution > 30:
            analysis["resolution_concern"] = "Slow resolution: may indicate bottleneck"
        elif avg_resolution > 7:
            analysis["resolution_concern"] = "Moderate pace: consider SLA goals"
    
    analysis["health"] = (
        "Strong" if analysis.get("closure_rate", 0) > 80 and open_count < 10 else
        "Good" if analysis.get("closure_rate", 0) > 60 else
        "Attention needed" if open_count > closed_count * 2 else
        "Fair"
    )
    
    return analysis


def analyze_releases(releases):
    """Analyze release patterns and frequency."""
    if not releases:
        return {"total": 0, "frequency": "No releases found"}
    
    release_dates = []
    
    for release in releases:
        if not isinstance(release, dict):
            continue
        
        published_at = release.get("published_at", "")
        if published_at:
            try:
                date = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                release_dates.append(date)
            except (ValueError, TypeError):
                pass
    
    analysis = {"total": len(releases)}
    
    if len(release_dates) > 1:
        release_dates.sort(reverse=True)
        days_between = (release_dates[0] - release_dates[-1]).days
        
        if days_between > 0:
            avg_interval = days_between / (len(release_dates) - 1)
            analysis["avg_release_interval_days"] = round(avg_interval)
            
            if avg_interval < 7:
                analysis["release_cadence"] = "Rapid (< 1 week)"
            elif avg_interval < 30:
                analysis["release_cadence"] = "Regular (weekly-monthly)"
            elif avg_interval < 90:
                analysis["release_cadence"] = "Moderate (quarterly)"
            else:
                analysis["release_cadence"] = "Infrequent (> 3 months)"
        
        # Latest release age
        days_since_last = (datetime.now(release_dates[0].tzinfo) - release_dates[0]).days
        analysis["days_since_latest_release"] = days_since_last
        
        if days_since_last > 180:
            analysis["release_concern"] = "No releases in 6+ months"
        elif days_since_last > 60:
            analysis["release_concern"] = "Stale: consider shipping"
    
    return analysis


def generate_report(metrics, commits, issues, releases):
    """Generate markdown report."""
    
    report = f"""# GitHub Engagement Summary

## Repository Overview

**Name:** {metrics["repo_name"]}
**URL:** {metrics["repo_url"]}
**Language:** {metrics["language"]}
**Description:** {metrics["description"] or "—"}

### Growth Metrics
- **Stars:** {metrics["stars"]}
- **Forks:** {metrics["forks"]}
- **Watchers:** {metrics["watchers"]}
- **Open Issues:** {metrics["open_issues"]}

---

## Development Activity

### Commits ({commits.get("total", 0)} total)
- **Status:** {commits.get("velocity_status", "Unknown")}
- **Commit Velocity:** {commits.get("commits_per_day", "N/A")} commits/day
- **Active Contributors:** {commits.get("authors", 0)}
"""
    
    if commits.get("top_contributors"):
        report += "\n**Top Contributors:**\n"
        for author, count in commits["top_contributors"]:
            report += f"- {author}: {count} commits\n"
    
    report += f"""
### Issue Health
- **Total Issues:** {issues.get("total", 0)} ({issues.get("open", 0)} open, {issues.get("closed", 0)} closed)
- **Closure Rate:** {issues.get("closure_rate", 0)}%
- **Health Status:** {issues.get("health", "Unknown")}
"""
    
    if issues.get("avg_open_issue_age_days"):
        report += f"- **Avg Open Issue Age:** {issues['avg_open_issue_age_days']} days\n"
    
    if issues.get("avg_resolution_time_days"):
        report += f"- **Avg Resolution Time:** {issues['avg_resolution_time_days']} days\n"
    
    if issues.get("age_concern"):
        report += f"- ⚠️ {issues['age_concern']}\n"
    
    if issues.get("resolution_concern"):
        report += f"- ⚠️ {issues['resolution_concern']}\n"
    
    report += f"""
### Release Cadence
- **Total Releases:** {releases.get("total", 0)}
- **Release Frequency:** {releases.get("release_cadence", "No data")}
"""
    
    if releases.get("avg_release_interval_days"):
        report += f"- **Avg Interval:** {releases['avg_release_interval_days']} days\n"
    
    if releases.get("days_since_latest_release") is not None:
        report += f"- **Days Since Latest:** {releases['days_since_latest_release']} days\n"
    
    if releases.get("release_concern"):
        report += f"- ⚠️ {releases['release_concern']}\n"
    
    report += """
---

## Growth Opportunities

"""
    
    opportunities = []
    
    # Issue-based opportunities
    if issues.get("closure_rate", 0) < 50:
        opportunities.append("**Improve Issue Resolution:** Low closure rate may block community engagement. Prioritize triage.")
    
    if issues.get("avg_open_issue_age_days", 0) > 60:
        opportunities.append("**Reduce Issue Backlog:** Old open issues reduce contributor confidence. Schedule a triage day.")
    
    # Commit-based opportunities
    if commits.get("velocity_status") == "Inactive" or commits.get("commits_per_day", 0) < 0.2:
        opportunities.append("**Increase Development Activity:** Low commit velocity signals project stagnation. Share your roadmap publicly.")
    
    if commits.get("authors", 0) <= 1:
        opportunities.append("**Grow Contributor Base:** Few contributors increases maintenance burden. Add contribution guidelines.")
    
    # Release-based opportunities
    if releases.get("days_since_latest_release", 9999) > 90:
        opportunities.append("**Ship More Often:** Infrequent releases slow feedback loops. Consider smaller, frequent releases.")
    
    if releases.get("total", 0) == 0:
        opportunities.append("**Create First Release:** Tagging releases builds credibility. Start with 1.0.0.")
    
    # Star-based opportunity
    if metrics["stars"] < 10 and metrics["forks"] == 0:
        opportunities.append("**Increase Visibility:** Low stars and no forks. Share on dev communities (GitHub Discussions, HN, Reddit).")
    
    if opportunities:
        for opp in opportunities:
            report += f"- {opp}\n"
    else:
        report += "- **Maintain momentum:** Your repository shows healthy engagement. Focus on consistency.\n"
    
    return report

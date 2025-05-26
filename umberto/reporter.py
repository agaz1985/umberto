import json
from typing import Dict, List
from collections import defaultdict, Counter

from .inspector import InheritanceIssue


def generate_report(issues: List[InheritanceIssue]) -> None:
    """Generate a formatted console report of inheritance issues."""
    if not issues:
        print("✅ No inheritance issues found.")
        return

    # Group issues by type
    issues_by_type = defaultdict(list)
    for issue in issues:
        issues_by_type[issue.issue_type].append(issue)

    print(f"🔍 Found {len(issues)} inheritance issue(s)")
    print("=" * 60)

    # Issue type symbols and descriptions
    type_info = {
        "MultipleInheritance": ("🔀", "Multiple Inheritance"),
        "InheritanceDepth": ("📏", "Inheritance Depth"),
        "DiamondInheritance": ("💎", "Diamond Inheritance"),
        "SyntaxError": ("❌", "Syntax Error"),
    }

    for issue_type, issue_list in issues_by_type.items():
        symbol, description = type_info.get(issue_type, ("⚠️", issue_type))
        print(f"\n{symbol} {description} ({len(issue_list)} issue(s)):")
        print("-" * 40)
        
        for issue in issue_list:
            print(f"  📁 {issue.filename}:{issue.line_number}")
            print(f"     Class: {issue.class_name}")
            print(f"     Issue: {issue.message}")
            print()

    # Summary statistics
    print("📊 Summary:")
    print("-" * 20)
    files_affected = len(set(issue.filename for issue in issues))
    classes_affected = len(set(issue.class_name for issue in issues))
    print(f"  Files affected: {files_affected}")
    print(f"  Classes affected: {classes_affected}")
    
    # Issue type breakdown
    print(f"  Issue breakdown:")
    for issue_type, count in Counter(issue.issue_type for issue in issues).items():
        symbol, description = type_info.get(issue_type, ("⚠️", issue_type))
        print(f"    {symbol} {description}: {count}")


def save_report(issues: List[InheritanceIssue], filepath: str) -> None:
    """Save the report as a JSON file."""
    report_data = {
        "summary": {
            "total_issues": len(issues),
            "files_affected": len(set(issue.filename for issue in issues)),
            "classes_affected": len(set(issue.class_name for issue in issues)),
            "issue_types": dict(Counter(issue.issue_type for issue in issues))
        },
        "issues": [
            {
                "filename": issue.filename,
                "class_name": issue.class_name,
                "line_number": issue.line_number,
                "issue_type": issue.issue_type,
                "message": issue.message,
            }
            for issue in issues
        ]
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)


def generate_html_report(issues: List[InheritanceIssue], filepath: str) -> None:
    """Generate an HTML report of inheritance issues."""
    if not issues:
        html_content = """
        <!DOCTYPE html>
        <html><head><title>Inheritance Report</title></head>
        <body><h1>✅ No inheritance issues found.</h1></body></html>
        """
    else:
        issues_by_type = defaultdict(list)
        for issue in issues:
            issues_by_type[issue.issue_type].append(issue)

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Inheritance Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; }}
                .issue-type {{ margin: 20px 0; }}
                .issue {{ background-color: #fff; border-left: 4px solid #007acc; padding: 10px; margin: 10px 0; }}
                .issue.multiple {{ border-left-color: #ff6b6b; }}
                .issue.depth {{ border-left-color: #ffa500; }}
                .issue.diamond {{ border-left-color: #9b59b6; }}
                .issue.syntax {{ border-left-color: #e74c3c; }}
                .filename {{ font-weight: bold; color: #007acc; }}
                .class-name {{ font-weight: bold; color: #2ecc71; }}
                .summary {{ background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔍 Inheritance Analysis Report</h1>
                <p>Found {len(issues)} inheritance issue(s)</p>
            </div>
            
            <div class="summary">
                <h2>📊 Summary</h2>
                <ul>
                    <li>Files affected: {len(set(issue.filename for issue in issues))}</li>
                    <li>Classes affected: {len(set(issue.class_name for issue in issues))}</li>
                </ul>
            </div>
        """

        type_classes = {
            "MultipleInheritance": "multiple",
            "InheritanceDepth": "depth", 
            "DiamondInheritance": "diamond",
            "SyntaxError": "syntax"
        }

        for issue_type, issue_list in issues_by_type.items():
            html_content += f"""
            <div class="issue-type">
                <h2>{issue_type.replace('Inheritance', ' Inheritance')} ({len(issue_list)} issue(s))</h2>
            """
            
            for issue in issue_list:
                css_class = type_classes.get(issue_type, "")
                html_content += f"""
                <div class="issue {css_class}">
                    <div class="filename">{issue.filename}:{issue.line_number}</div>
                    <div>Class: <span class="class-name">{issue.class_name}</span></div>
                    <div>Issue: {issue.message}</div>
                </div>
                """
            
            html_content += "</div>"
        
        html_content += "</body></html>"

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
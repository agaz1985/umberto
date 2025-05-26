import argparse
import os
import sys

from umberto.inspector import inspect_codebase
from umberto.reporter import generate_report, save_report, generate_html_report
from umberto.refactoring import refactor_inheritance_issues, OPENAI_AVAILABLE


def main():
    parser = argparse.ArgumentParser(
        description="Detect problematic inheritance patterns in a Python codebase."
    )
    parser.add_argument(
        "path", type=str, help="Path to the directory or file to inspect"
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=3,
        help="Maximum allowed inheritance depth (default: 3)",
    )
    parser.add_argument(
        "--allow-multiple",
        action="store_true",
        help="Allow multiple inheritance (default: disallow)",
    )
    parser.add_argument(
        "--allow-diamond",
        action="store_true",
        help="Allow diamond inheritance (default: disallow)",
    )
    parser.add_argument(
        "--save", type=str, help="Path to save the report as a JSON file"
    )
    parser.add_argument(
        "--html", type=str, help="Path to save the report as an HTML file"
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Only show summary, no detailed output"
    )
    parser.add_argument(
        "--refactor", action="store_true", 
        help="Generate AI-powered refactoring suggestions (requires OpenAI API key)"
    )
    parser.add_argument(
        "--api-key", type=str, 
        help="OpenAI API key (or set OPENAI_API_KEY environment variable)"
    )
    parser.add_argument(
        "--refactor-output", type=str, default="refactoring_suggestions",
        help="Directory to save refactoring suggestions (default: refactoring_suggestions)"
    )

    args = parser.parse_args()

    if not os.path.exists(args.path):
        print(f"Error: Path '{args.path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    # Inspect the codebase
    issues = inspect_codebase(
        path=args.path,
        max_depth=args.max_depth,
        allow_multiple=args.allow_multiple,
        allow_diamond=args.allow_diamond,
    )

    # Generate console report (unless quiet mode for saves)
    if not args.quiet or (not args.save and not args.html):
        generate_report(issues)

    # Save JSON report if requested
    if args.save:
        try:
            save_report(issues, args.save)
            print(f"\n💾 JSON report saved to {args.save}")
        except Exception as e:
            print(f"Error saving JSON report: {e}", file=sys.stderr)
            sys.exit(1)

    # Save HTML report if requested
    if args.html:
        try:
            generate_html_report(issues, args.html)
            print(f"\n🌐 HTML report saved to {args.html}")
        except Exception as e:
            print(f"Error saving HTML report: {e}", file=sys.stderr)
            sys.exit(1)

    # Generate refactoring suggestions if requested
    if args.refactor:
        if not OPENAI_AVAILABLE:
            print("Error: OpenAI package not available. Install with: pip install openai", file=sys.stderr)
            sys.exit(1)
        
        api_key = args.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Error: OpenAI API key required. Set OPENAI_API_KEY environment variable or use --api-key", file=sys.stderr)
            sys.exit(1)
        
        print("\n🤖 Generating AI-powered refactoring suggestions...")
        try:
            suggestions = refactor_inheritance_issues(
                issues, api_key=api_key, output_dir=args.refactor_output
            )
            if suggestions:
                print(f"✨ Generated {len(suggestions)} refactoring suggestions")
            else:
                print("No refactoring suggestions generated")
        except Exception as e:
            print(f"Error generating refactoring suggestions: {e}", file=sys.stderr)

    # Exit with error code if issues found
    if issues:
        sys.exit(1)


if __name__ == "__main__":
    main()
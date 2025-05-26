import ast
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .inspector import InheritanceIssue


@dataclass
class RefactoringSuggestion:
    issue: InheritanceIssue
    original_code: str
    suggested_code: str
    explanation: str


class RefactoringAssistant:
    """AI-powered assistant for suggesting composition-based refactoring."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI package not available. Install with: pip install openai"
            )

        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model

        # Templates for different issue types
        self.prompt_templates = {
            "MultipleInheritance": (
                """
You're an expert Python developer. The following class uses multiple inheritance which can be problematic:

Filename: {filename}
Class: {class_name}
Line: {line_number}
Issue: {issue_type}
Detail: {message}

Original code:
```python
{code}
```

Please rewrite this using composition instead of multiple inheritance. Show:
1. The refactored class using composition
2. Any helper methods or properties needed
3. A brief explanation of the changes

Focus on maintaining the same interface while using composition patterns like delegation or mixins.
"""
            ),
            "InheritanceDepth": (
                """
You're an expert Python developer. The following class has excessive inheritance depth:

Filename: {filename}
Class: {class_name}
Line: {line_number}
Issue: {issue_type}
Detail: {message}

Original code:
```python
{code}
```

Please suggest how to reduce inheritance depth using composition. Show:
1. A flattened class structure using composition
2. How to maintain the same functionality
3. A brief explanation of the benefits

Consider extracting common functionality into separate components.
"""
            ),
            "DiamondInheritance": (
                """
You're an expert Python developer. The following class has diamond inheritance which can cause method resolution issues:

Filename: {filename}
Class: {class_name}
Line: {line_number}
Issue: {issue_type}
Detail: {message}

Original code:
```python
{code}
```

Please rewrite this to eliminate diamond inheritance using composition. Show:
1. How to restructure using composition
2. How to handle method delegation
3. A brief explanation of how this solves the diamond problem

Focus on clear delegation patterns and avoiding MRO conflicts.
"""
            ),
            "default": (
                """
You're an expert Python developer. The following class has problematic inheritance:

Filename: {filename}
Class: {class_name}
Line: {line_number}
Issue: {issue_type}
Detail: {message}

Original code:
```python
{code}
```

Please suggest how to improve this code using composition instead of inheritance. Show:
1. The refactored code
2. Key improvements made
3. A brief explanation of the benefits
"""
            ),
        }

    def get_class_code(
        self, filename: str, class_name: str, line_number: int
    ) -> Optional[str]:
        """Extract the class code from the file."""
        try:
            with open(filename, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)

            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.ClassDef)
                    and node.name == class_name
                    and node.lineno == line_number
                ):

                    # Extract the class code
                    lines = source.split("\n")
                    start_line = node.lineno - 1

                    # Find the end of the class
                    end_line = start_line + 1
                    base_indent = len(lines[start_line]) - len(
                        lines[start_line].lstrip()
                    )

                    for i in range(start_line + 1, len(lines)):
                        line = lines[i]
                        if line.strip() == "":
                            continue
                        current_indent = len(line) - len(line.lstrip())
                        if current_indent <= base_indent and line.strip():
                            break
                        end_line = i + 1

                    return "\n".join(lines[start_line:end_line])

        except Exception as e:
            print(f"Error extracting class code: {e}")
            return None

        return None

    def get_refactoring_suggestion(
        self, issue: InheritanceIssue
    ) -> Optional[RefactoringSuggestion]:
        """Get AI-powered refactoring suggestion for an inheritance issue."""
        if not self.client.api_key:
            raise ValueError("OpenAI API key not provided")

        # Get the class code
        class_code = self.get_class_code(
            issue.filename, issue.class_name, issue.line_number
        )
        if not class_code:
            return None

        # Select appropriate prompt template
        template = self.prompt_templates.get(
            issue.issue_type, self.prompt_templates["default"]
        )

        prompt = template.format(
            filename=issue.filename,
            class_name=issue.class_name,
            line_number=issue.line_number,
            issue_type=issue.issue_type,
            message=issue.message,
            code=class_code,
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert Python developer specializing in clean code architecture and design patterns."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=1000,
            )

            content = response.choices[0].message.content

            # Try to separate code and explanation
            parts = content.split("```python")
            if len(parts) > 1:
                code_part = parts[1].split("```")[0].strip()
                explanation_parts = parts[0] + (
                    "```".join(parts[1].split("```")[1:])
                    if len(parts[1].split("```")) > 1
                    else ""
                )
                explanation = explanation_parts.strip()
            else:
                # Fallback if no code blocks found
                code_part = content
                explanation = "AI-generated refactoring suggestion"

            return RefactoringSuggestion(
                issue=issue,
                original_code=class_code,
                suggested_code=code_part,
                explanation=explanation,
            )

        except Exception as e:
            print(f"Error getting AI suggestion: {e}")
            return None

    def batch_refactor_suggestions(
        self, issues: List[InheritanceIssue], issue_types: Optional[List[str]] = None
    ) -> List[RefactoringSuggestion]:
        """Get refactoring suggestions for multiple issues."""
        suggestions = []

        # Filter by issue types if specified
        if issue_types:
            issues = [issue for issue in issues if issue.issue_type in issue_types]

        for issue in issues:
            suggestion = self.get_refactoring_suggestion(issue)
            if suggestion:
                suggestions.append(suggestion)

        return suggestions

    def save_suggestions(
        self,
        suggestions: List[RefactoringSuggestion],
        output_dir: str = "refactoring_suggestions",
    ):
        """Save refactoring suggestions to files."""
        os.makedirs(output_dir, exist_ok=True)

        for i, suggestion in enumerate(suggestions):
            filename = f"suggestion_{i+1}_{suggestion.issue.class_name}.md"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(
                    f"# Refactoring Suggestion for {suggestion.issue.class_name}\n\n"
                )
                f.write(
                    f"**File:** {suggestion.issue.filename}:{suggestion.issue.line_number}\n"
                )
                f.write(f"**Issue:** {suggestion.issue.issue_type}\n")
                f.write(f"**Detail:** {suggestion.issue.message}\n\n")

                f.write("## Original Code\n\n")
                f.write("```python\n")
                f.write(suggestion.original_code)
                f.write("\n```\n\n")

                f.write("## Suggested Refactoring\n\n")
                f.write("```python\n")
                f.write(suggestion.suggested_code)
                f.write("\n```\n\n")

                f.write("## Explanation\n\n")
                f.write(suggestion.explanation)
                f.write("\n")


def get_composition_suggestion(
    issue: InheritanceIssue, api_key: Optional[str] = None, model: str = "gpt-4"
) -> Optional[str]:
    """
    Legacy function for backward compatibility.
    Get a composition-based refactoring suggestion for a single issue.
    """
    try:
        assistant = RefactoringAssistant(api_key=api_key, model=model)
        suggestion = assistant.get_refactoring_suggestion(issue)
        return suggestion.suggested_code if suggestion else None
    except Exception as e:
        print(f"Error getting composition suggestion: {e}")
        return None


# Example usage and integration
def refactor_inheritance_issues(
    issues: List[InheritanceIssue],
    api_key: Optional[str] = None,
    output_dir: str = "refactoring_suggestions",
) -> List[RefactoringSuggestion]:
    """
    Main function to get refactoring suggestions for inheritance issues.
    """
    if not OPENAI_AVAILABLE:
        print("OpenAI package not available. Install with: pip install openai")
        return []

    assistant = RefactoringAssistant(api_key=api_key)

    # Focus on the most problematic inheritance patterns
    target_issues = ["MultipleInheritance", "InheritanceDepth", "DiamondInheritance"]
    suggestions = assistant.batch_refactor_suggestions(issues, target_issues)

    if suggestions:
        assistant.save_suggestions(suggestions, output_dir)
        print(f"Generated {len(suggestions)} refactoring suggestions in {output_dir}/")

    return suggestions

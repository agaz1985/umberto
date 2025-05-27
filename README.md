# 🔍 Umberto
![Umberto Logo](/umberto/icon/logo.png)

> *A comprehensive Python inheritance analyzer and refactoring assistant*

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Umberto is a powerful static analysis tool that detects problematic inheritance patterns in Python codebases and provides AI-powered refactoring suggestions to improve code maintainability and design.

## ✨ Features

### 🕵️ **Comprehensive Inheritance Analysis**
- **Multiple Inheritance Detection**: Identifies classes with multiple base classes
- **Inheritance Depth Analysis**: Finds deeply nested inheritance hierarchies
- **Diamond Inheritance Detection**: Spots complex diamond patterns that can cause MRO issues
- **Circular Inheritance Detection**: Catches impossible inheritance cycles
- **Abstract Method Validation**: Ensures proper ABC usage with abstract methods
- **Problematic Built-in Inheritance**: Warns about inheriting from problematic built-in types

### 🤖 **AI-Powered Refactoring Assistant**
- **Smart Composition Suggestions**: AI-generated alternatives using composition patterns
- **Issue-Specific Prompts**: Tailored refactoring strategies for different inheritance problems
- **Detailed Explanations**: Clear reasoning behind each refactoring suggestion
- **Batch Processing**: Handle multiple inheritance issues at once

### 📊 **Rich Reporting**
- **Console Reports**: Beautiful, emoji-rich terminal output
- **JSON Export**: Machine-readable reports for CI/CD integration
- **HTML Reports**: Professional web-based reports for sharing
- **Markdown Suggestions**: Detailed refactoring documentation

## 🚀 Installation

### Basic Installation
```bash
pip install umberto
```

### With AI Refactoring Support
```bash
pip install umberto[ai]
# or
pip install umberto openai
```

### Development Installation
```bash
git clone https://github.com/yourusername/umberto.git
cd umberto
pip install -e ".[dev,ai]"
```

## 📖 Quick Start

### Basic Usage
```bash
# Analyze a single file
umberto myfile.py

# Analyze entire project
umberto /path/to/project

# Strict analysis (no multiple or diamond inheritance allowed)
umberto /path/to/project --max-depth 2
```

### Advanced Analysis
```bash
# Allow multiple inheritance but catch deep hierarchies
umberto /path/to/project --allow-multiple --max-depth 3

# Generate comprehensive reports
umberto /path/to/project --save report.json --html report.html
```

### AI-Powered Refactoring
```bash
# Set your OpenAI API key
export OPENAI_API_KEY="sk-your-api-key-here"

# Generate refactoring suggestions
umberto /path/to/project --refactor

# Custom output directory for suggestions
umberto /path/to/project --refactor --refactor-output ./my-suggestions
```

## 🎯 Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `path` | Directory or file to analyze | Required |
| `--max-depth` | Maximum allowed inheritance depth | 3 |
| `--allow-multiple` | Allow multiple inheritance | False |
| `--allow-diamond` | Allow diamond inheritance | False |
| `--save` | Save JSON report to file | None |
| `--html` | Save HTML report to file | None |
| `--refactor` | Generate AI refactoring suggestions | False |
| `--api-key` | OpenAI API key for refactoring | `$OPENAI_API_KEY` |
| `--refactor-output` | Directory for refactoring suggestions | `refactoring_suggestions` |
| `--quiet` | Suppress detailed output | False |

## 📋 Detected Issues

### Inheritance Problems
- **MultipleInheritance**: Classes inheriting from multiple base classes
- **InheritanceDepth**: Classes with inheritance chains exceeding the maximum depth
- **DiamondInheritance**: Complex inheritance patterns forming diamond shapes
- **CircularInheritance**: Impossible circular inheritance dependencies

### Code Quality Issues
- **AbstractMethodWithoutABC**: Abstract methods without proper ABC inheritance
- **ProblematicBuiltinInheritance**: Inheritance from problematic built-in types
- **EmptyInheritanceClass**: Classes that only inherit without adding functionality

### File Issues
- **SyntaxError**: Files with syntax errors that prevent analysis
- **EncodingError**: Files that can't be decoded as UTF-8
- **IOError**: Files that can't be read due to permissions or other issues

## 📊 Example Output

### Console Report
```
🔍 Found 3 inheritance issue(s)
============================================================

🔀 Multiple Inheritance (1 issue(s)):
----------------------------------------
  📁 src/models.py:45
     Class: UserProfile
     Issue: UserProfile inherits from multiple classes: User, Profile

📏 Inheritance Depth (2 issue(s)):
----------------------------------------
  📁 src/base.py:12
     Class: DeepChild
     Issue: Inheritance depth of DeepChild is 5 (max allowed is 3)

📊 Summary:
--------------------
  Files affected: 2
  Classes affected: 3
  Issue breakdown:
    🔀 Multiple Inheritance: 1
    📏 Inheritance Depth: 2
```

### AI Refactoring Suggestion
```markdown
# Refactoring Suggestion for UserProfile

**File:** src/models.py:45
**Issue:** MultipleInheritance
**Detail:** UserProfile inherits from multiple classes: User, Profile

## Original Code
```python
class UserProfile(User, Profile):
    def __init__(self, username, email, bio):
        User.__init__(self, username, email)
        Profile.__init__(self, bio)
```

## Suggested Refactoring
```python
class UserProfile:
    def __init__(self, username, email, bio):
        self.user = User(username, email)
        self.profile = Profile(bio)
    
    # Delegate user methods
    @property
    def username(self):
        return self.user.username
    
    # Delegate profile methods
    @property
    def bio(self):
        return self.profile.bio
```

## Explanation
This refactoring eliminates multiple inheritance by using composition...
```

## 🔧 API Usage

### Programmatic Analysis
```python
from umberto import inspect_codebase, generate_report

# Analyze codebase
issues = inspect_codebase(
    path="/path/to/code",
    max_depth=3,
    allow_multiple=False,
    allow_diamond=False
)

# Generate report
generate_report(issues)
```

### AI Refactoring
```python
from umberto import refactor_inheritance_issues

# Get AI suggestions
suggestions = refactor_inheritance_issues(
    issues,
    api_key="your-openai-key",
    output_dir="suggestions"
)
```

## 🎨 Integration Examples

### Pre-commit Hook
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: umberto
        name: Inheritance Analysis
        entry: umberto
        language: system
        args: ['.', '--max-depth', '3']
        pass_filenames: false
```

### GitHub Actions
```yaml
name: Code Quality
on: [push, pull_request]

jobs:
  inheritance-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install Umberto
        run: pip install umberto
      - name: Check Inheritance
        run: umberto . --save inheritance-report.json
      - name: Upload Report
        uses: actions/upload-artifact@v3
        with:
          name: inheritance-report
          path: inheritance-report.json
```

### CI/CD Pipeline
```bash
#!/bin/bash
# ci-check.sh

echo "Running inheritance analysis..."
umberto . --quiet --save inheritance-report.json

if [ $? -ne 0 ]; then
    echo "❌ Inheritance issues found!"
    echo "Check inheritance-report.json for details"
    exit 1
else
    echo "✅ No inheritance issues detected"
fi
```

## 🤝 Contributing

We welcome contributions!

### Development Setup
```bash
git clone https://github.com/yourusername/umberto.git
cd umberto
poetry install
```

### Running Tests
```bash
pytest
pytest --cov=umberto  # with coverage
```

## 🐛 Issues and Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/agaz1985/umberto/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/agaz1985/umberto/discussions)
- 📧 **Email**: agaz1985 at gmail.com

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by the need for better inheritance analysis in Python codebases
- Built on top of Python's powerful AST module
- AI refactoring powered by OpenAI's GPT models
- Thanks to all contributors and the Python community

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=agaz1985/umberto&type=Date)](https://star-history.com/#agaz1985/umberto&Date)

---

**Made with ❤️ by the Umberto team**

*"Clean inheritance leads to clean code"* - Umberto Philosoph*y*
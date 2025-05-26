import ast
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple


@dataclass(frozen=True)
class InheritanceIssue:
    filename: str
    class_name: str
    line_number: int
    issue_type: str
    message: str


class InheritanceInspector(ast.NodeVisitor):
    def __init__(
        self,
        filename: str,
        max_depth: int = 3,
        allow_multiple: bool = True,
        allow_diamond: bool = True,
    ):
        self.filename = filename
        self.max_depth = max_depth
        self.allow_multiple = allow_multiple
        self.allow_diamond = allow_diamond
        self.issues: List[InheritanceIssue] = []
        self.class_bases: Dict[str, List[str]] = {}  # class -> direct base classes
        self.class_nodes: Dict[str, ast.ClassDef] = {}  # class -> AST node
        self.all_classes: Set[str] = set()  # all classes found in this file

    def visit_ClassDef(self, node: ast.ClassDef):
        class_name = node.name
        bases = [
            self._get_base_name(base)
            for base in node.bases
            if self._get_base_name(base) != "<unknown>"
        ]

        self.class_bases[class_name] = bases
        self.class_nodes[class_name] = node
        self.all_classes.add(class_name)

        # Check multiple inheritance
        if not self.allow_multiple and len(bases) > 1:
            self.issues.append(
                InheritanceIssue(
                    filename=self.filename,
                    class_name=class_name,
                    line_number=node.lineno,
                    issue_type="MultipleInheritance",
                    message=f"{class_name} inherits from multiple classes: {', '.join(bases)}",
                )
            )

        # Check for abstract base classes without implementation
        self._check_abstract_methods(node, class_name)

        # Check for suspicious inheritance patterns
        self._check_suspicious_patterns(node, class_name, bases)

        self.generic_visit(node)

    def check(self):
        """Perform post-processing checks that require all classes to be collected."""
        # Check inheritance depth
        for class_name in self.class_bases:
            depth = self._compute_inheritance_depth(class_name)
            if depth > self.max_depth:
                node = self.class_nodes[class_name]
                self.issues.append(
                    InheritanceIssue(
                        filename=self.filename,
                        class_name=class_name,
                        line_number=node.lineno,
                        issue_type="InheritanceDepth",
                        message=f"Inheritance depth of {class_name} is {depth} (max allowed is {self.max_depth})",
                    )
                )

        # Check diamond inheritance
        if not self.allow_diamond:
            for class_name in self.class_bases:
                diamond_paths = self._find_diamond_inheritance(class_name)
                if diamond_paths:
                    node = self.class_nodes[class_name]
                    diamond_classes = set()
                    for path in diamond_paths:
                        diamond_classes.update(path[1:-1])  # exclude start and end
                    self.issues.append(
                        InheritanceIssue(
                            filename=self.filename,
                            class_name=class_name,
                            line_number=node.lineno,
                            issue_type="DiamondInheritance",
                            message=f"{class_name} has diamond inheritance through: {', '.join(sorted(diamond_classes))}",
                        )
                    )

        # Check for circular inheritance
        self._check_circular_inheritance()

    def _get_base_name(self, base) -> str:
        """Extract base class name from AST node."""
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            # Handle cases like module.ClassName
            parts = []
            node = base
            while isinstance(node, ast.Attribute):
                parts.append(node.attr)
                node = node.value
            if isinstance(node, ast.Name):
                parts.append(node.id)
            return ".".join(reversed(parts))
        elif isinstance(base, ast.Subscript):
            # Handle generics like List[str], Optional[Type]
            return self._get_base_name(base.value)
        else:
            return "<unknown>"

    def _compute_inheritance_depth(
        self, class_name: str, visited: Optional[Set[str]] = None, depth: int = 0
    ) -> int:
        """Compute the maximum inheritance depth for a class."""
        if visited is None:
            visited = set()

        if class_name in visited:
            # Circular inheritance detected, return current depth
            return depth

        visited.add(class_name)
        bases = self.class_bases.get(class_name, [])

        if not bases:
            return depth + 1

        max_depth = 0
        for base in bases:
            if base in self.all_classes:  # Only count classes we can analyze
                base_depth = self._compute_inheritance_depth(
                    base, visited.copy(), depth + 1
                )
                max_depth = max(max_depth, base_depth)
            else:
                # External class, assume depth of 1
                max_depth = max(max_depth, depth + 2)

        return max_depth

    def _find_diamond_inheritance(self, class_name: str) -> List[List[str]]:
        """Find all diamond inheritance paths for a class."""

        def find_paths_to_base(
            current: str, target: str, path: List[str], all_paths: List[List[str]]
        ):
            if current == target and len(path) > 1:
                all_paths.append(path.copy())
                return

            for base in self.class_bases.get(current, []):
                if base not in path:  # Avoid infinite loops
                    path.append(base)
                    find_paths_to_base(base, target, path, all_paths)
                    path.pop()

        # Find all common ancestors
        diamond_paths = []
        ancestors = self._get_all_ancestors(class_name)

        for ancestor in ancestors:
            paths = []
            find_paths_to_base(class_name, ancestor, [class_name], paths)
            if len(paths) > 1:
                diamond_paths.extend(paths)

        return diamond_paths

    def _get_all_ancestors(
        self, class_name: str, visited: Optional[Set[str]] = None
    ) -> Set[str]:
        """Get all ancestor classes for a given class."""
        if visited is None:
            visited = set()

        if class_name in visited:
            return set()

        visited.add(class_name)
        ancestors = set()

        for base in self.class_bases.get(class_name, []):
            if base in self.all_classes:
                ancestors.add(base)
                ancestors.update(self._get_all_ancestors(base, visited))

        return ancestors

    def _check_circular_inheritance(self):
        """Check for circular inheritance patterns."""

        def has_cycle(class_name: str, visited: Set[str], rec_stack: Set[str]) -> bool:
            visited.add(class_name)
            rec_stack.add(class_name)

            for base in self.class_bases.get(class_name, []):
                if base in self.all_classes:
                    if base not in visited:
                        if has_cycle(base, visited, rec_stack):
                            return True
                    elif base in rec_stack:
                        return True

            rec_stack.remove(class_name)
            return False

        visited = set()
        for class_name in self.all_classes:
            if class_name not in visited:
                if has_cycle(class_name, visited, set()):
                    node = self.class_nodes[class_name]
                    self.issues.append(
                        InheritanceIssue(
                            filename=self.filename,
                            class_name=class_name,
                            line_number=node.lineno,
                            issue_type="CircularInheritance",
                            message=f"{class_name} is part of a circular inheritance chain",
                        )
                    )

    def _check_abstract_methods(self, node: ast.ClassDef, class_name: str):
        """Check for abstract methods and proper ABC usage."""
        has_abc_import = False
        has_abstract_methods = False
        inherits_from_abc = False

        # Check if ABC is imported (simplified check)
        # This would need more sophisticated import tracking for full accuracy
        for base_name in self.class_bases.get(class_name, []):
            if "ABC" in base_name or "abc" in base_name.lower():
                inherits_from_abc = True
                break

        # Check for @abstractmethod decorators
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                for decorator in item.decorator_list:
                    if (
                        isinstance(decorator, ast.Name)
                        and decorator.id == "abstractmethod"
                    ):
                        has_abstract_methods = True
                    elif (
                        isinstance(decorator, ast.Attribute)
                        and decorator.attr == "abstractmethod"
                    ):
                        has_abstract_methods = True

        if has_abstract_methods and not inherits_from_abc:
            self.issues.append(
                InheritanceIssue(
                    filename=self.filename,
                    class_name=class_name,
                    line_number=node.lineno,
                    issue_type="AbstractMethodWithoutABC",
                    message=f"{class_name} has abstract methods but doesn't inherit from ABC",
                )
            )

    def _check_suspicious_patterns(
        self, node: ast.ClassDef, class_name: str, bases: List[str]
    ):
        """Check for suspicious inheritance patterns."""
        # Check for inheriting from built-in types that shouldn't be inherited from
        problematic_builtins = {"dict", "list", "tuple", "str", "int", "float"}
        for base in bases:
            if base in problematic_builtins:
                self.issues.append(
                    InheritanceIssue(
                        filename=self.filename,
                        class_name=class_name,
                        line_number=node.lineno,
                        issue_type="ProblematicBuiltinInheritance",
                        message=f"{class_name} inherits from built-in type '{base}' which may cause issues",
                    )
                )

        # Check for empty classes that only inherit
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass) and bases:
            self.issues.append(
                InheritanceIssue(
                    filename=self.filename,
                    class_name=class_name,
                    line_number=node.lineno,
                    issue_type="EmptyInheritanceClass",
                    message=f"{class_name} is an empty class that only inherits from {', '.join(bases)}",
                )
            )


def inspect_file(
    filepath: str, max_depth: int, allow_multiple: bool, allow_diamond: bool
) -> List[InheritanceIssue]:
    """Inspect a single Python file for inheritance issues."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
    except UnicodeDecodeError:
        return [
            InheritanceIssue(
                filename=filepath,
                class_name="<unknown>",
                line_number=0,
                issue_type="EncodingError",
                message="Could not decode file (not UTF-8)",
            )
        ]
    except IOError as e:
        return [
            InheritanceIssue(
                filename=filepath,
                class_name="<unknown>",
                line_number=0,
                issue_type="IOError",
                message=f"Could not read file: {e}",
            )
        ]

    try:
        tree = ast.parse(source, filename=filepath)
        inspector = InheritanceInspector(
            filepath, max_depth, allow_multiple, allow_diamond
        )
        inspector.visit(tree)
        inspector.check()
        return inspector.issues
    except SyntaxError as e:
        return [
            InheritanceIssue(
                filename=filepath,
                class_name="<unknown>",
                line_number=e.lineno or 0,
                issue_type="SyntaxError",
                message=f"Could not parse file: {e}",
            )
        ]


def inspect_codebase(
    path: str,
    max_depth: int = 3,
    allow_multiple: bool = True,
    allow_diamond: bool = True,
    exclude_patterns: Optional[List[str]] = None,
) -> List[InheritanceIssue]:
    """Inspect a Python codebase for inheritance issues."""
    issues: List[InheritanceIssue] = []
    exclude_patterns = exclude_patterns or [
        "__pycache__",
        ".git",
        ".venv",
        "venv",
        "env",
    ]

    if os.path.isfile(path):
        # Single file
        if path.endswith(".py"):
            return inspect_file(path, max_depth, allow_multiple, allow_diamond)
        else:
            return []

    # Directory traversal
    for root, dirs, files in os.walk(path):
        # Filter out excluded directories
        dirs[:] = [
            d for d in dirs if not any(pattern in d for pattern in exclude_patterns)
        ]

        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                file_issues = inspect_file(
                    full_path, max_depth, allow_multiple, allow_diamond
                )
                issues.extend(file_issues)

    return issues

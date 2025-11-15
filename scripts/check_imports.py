import os
import sys
import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

IGNORE_DIRS = {
    'venv', '.venv', '__pycache__', 'build', 'dist',
    'node_modules', 'staticfiles', '.git'
}

def iter_python_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        rel = Path(dirpath).relative_to(root)
        # skip ignored
        if any(part in IGNORE_DIRS for part in rel.parts):
            continue
        for fn in filenames:
            if fn.endswith('.py'):
                yield Path(dirpath) / fn

def analyze_file(path: Path):
    try:
        src = path.read_text(encoding='utf-8')
    except Exception:
        return []
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError:
        return []

    imported = set()
    used = set()

    class ImportVisitor(ast.NodeVisitor):
        def visit_Import(self, node: ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name.split('.')[0]
                imported.add(name)
        def visit_ImportFrom(self, node: ast.ImportFrom):
            for alias in node.names:
                name = alias.asname or alias.name
                imported.add(name)
        def visit_Name(self, node: ast.Name):
            used.add(node.id)
        def visit_Attribute(self, node: ast.Attribute):
            if isinstance(node.value, ast.Name):
                used.add(node.value.id)
            self.generic_visit(node)

    ImportVisitor().visit(tree)

    unused = sorted(name for name in imported if name not in used)
    if unused:
        return [(str(path.relative_to(PROJECT_ROOT)), unused)]
    return []

def main():
    root = PROJECT_ROOT
    results = []
    for py in iter_python_files(root):
        results.extend(analyze_file(py))
    if not results:
        print('No se detectaron imports sin uso.')
        return 0
    print('Imports sin uso detectados:')
    for filename, names in results:
        print(f'- {filename}: {", ".join(names)}')
    return 0

if __name__ == '__main__':
    sys.exit(main())
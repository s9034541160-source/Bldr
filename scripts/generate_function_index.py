#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate a function/class signature index across the repository.
Outputs Markdown to stdout. Excludes heavy non-code dirs and tests by default.
"""
import ast
import os
import sys
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE_DIRS = {
    '.git','node_modules','dist','build','out','coverage','target','bin','obj',
    '__pycache__','.tox','.cache','venv','.venv','web/bldr_dashboard','tests'
}
INCLUDE_TOP = {
    'core','backend','system_launcher','integrations','plugins','scripts'
}


def should_scan_dir(p: Path) -> bool:
    rel = p.relative_to(ROOT).as_posix()
    parts = rel.split('/')
    if parts[0] in EXCLUDE_DIRS:
        return False
    if parts[0] in INCLUDE_TOP:
        return True
    # allow scanning top-level .py files
    if p == ROOT:
        return True
    return False


def iter_python_files(root: Path) -> List[Path]:
    files: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # filter dirs in-place for efficiency
        rel = Path(dirpath).resolve().relative_to(ROOT)
        # prune excluded dirs
        pruned = []
        for d in list(dirnames):
            rel_child = (rel / d).as_posix()
            top = rel_child.split('/')[0]
            if top in EXCLUDE_DIRS:
                continue
            # Only include whitelisted top-level dirs or stay under allowed trees
            if str(rel) == '.':
                if d in INCLUDE_TOP:
                    pruned.append(d)
                # also allow staying at root (for root-level .py)
            else:
                pruned.append(d)
        dirnames[:] = pruned
        for f in filenames:
            if f.endswith('.py'):
                files.append(Path(dirpath) / f)
    return files


def get_function_signature(func: ast.FunctionDef) -> str:
    args = []
    def fmt_arg(a: ast.arg, default=None):
        if default is not None:
            return f"{a.arg}={default}"
        return a.arg

    defaults = [None] * (len(func.args.args) - len(func.args.defaults)) + func.args.defaults
    for a, d in zip(func.args.args, defaults):
        if d is None:
            args.append(a.arg)
        else:
            args.append(f"{a.arg}={ast.unparse(d) if hasattr(ast, 'unparse') else '...'}")

    if func.args.vararg:
        args.append(f"*{func.args.vararg.arg}")
    if func.args.kwonlyargs:
        if not func.args.vararg:
            args.append('*')
        for a, d in zip(func.args.kwonlyargs, func.args.kw_defaults):
            if d is None:
                args.append(a.arg)
            else:
                args.append(f"{a.arg}={ast.unparse(d) if hasattr(ast, 'unparse') else '...'}")
    if func.args.kwarg:
        args.append(f"**{func.args.kwarg.arg}")

    returns = ''
    if func.returns is not None:
        try:
            returns = f" -> {ast.unparse(func.returns) if hasattr(ast, 'unparse') else ''}"
        except Exception:
            returns = ''
    return f"def {func.name}({', '.join(args)}){returns}"


def get_class_signature(cls: ast.ClassDef) -> str:
    bases = []
    for b in cls.bases:
        try:
            bases.append(ast.unparse(b) if hasattr(ast, 'unparse') else '')
        except Exception:
            bases.append('')
    base_str = f"({', '.join(bases)})" if bases else ''
    return f"class {cls.name}{base_str}"


def parse_file(path: Path) -> Tuple[List[str], List[Tuple[str, List[str]]]]:
    """Return (functions, classes_with_methods)."""
    try:
        src = path.read_text(encoding='utf-8', errors='ignore')
        tree = ast.parse(src)
    except Exception:
        return [], []
    funcs: List[str] = []
    classes: List[Tuple[str, List[str]]] = []

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            funcs.append(get_function_signature(node))
        elif isinstance(node, ast.AsyncFunctionDef):
            # represent async as def for brevity
            sig = get_function_signature(node)
            funcs.append('async ' + sig)
        elif isinstance(node, ast.ClassDef):
            class_sig = get_class_signature(node)
            methods: List[str] = []
            for ch in node.body:
                if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    m_sig = get_function_signature(ch)
                    if isinstance(ch, ast.AsyncFunctionDef):
                        m_sig = 'async ' + m_sig
                    methods.append(m_sig)
            classes.append((class_sig, methods))
    return funcs, classes


def main():
    files = iter_python_files(ROOT)
    print("# Function/Class Signature Index\n")
    print(f"Root: {ROOT}")
    print("Scanned directories: core, backend, system_launcher, integrations, plugins, scripts (excluding tests)")
    print("")
    for f in sorted(files, key=lambda p: p.as_posix()):
        rel = f.relative_to(ROOT).as_posix()
        funcs, classes = parse_file(f)
        if not funcs and not classes:
            continue
        print(f"## {rel}\n")
        if classes:
            print("### Classes\n")
            for cls_sig, methods in classes:
                print(f"- {cls_sig}")
                for m in methods:
                    print(f"  - {m}")
            print("")
        if funcs:
            print("### Functions\n")
            for s in funcs:
                print(f"- {s}")
            print("")

if __name__ == '__main__':
    main()

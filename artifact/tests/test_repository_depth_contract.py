import ast
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
pkg_files = sorted((ROOT / 'latticeguard').glob('*.py'))
script_files = sorted((ROOT / 'scripts').glob('*.py'))
assert len(pkg_files) >= 40, len(pkg_files)
assert len(script_files) >= 30, len(script_files)
public_api = 0
for path in pkg_files:
    tree = ast.parse(path.read_text(encoding='utf-8'))
    public_api += sum(1 for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and not n.name.startswith('_'))
assert public_api >= 90, public_api
print('repository_depth_contract PASS')

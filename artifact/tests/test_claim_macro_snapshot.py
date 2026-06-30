import json
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
macros = (ROOT / 'results' / 'claim_macros_snapshot.tex').read_text()
summary = json.loads((ROOT / 'results' / 'summary.json').read_text())
def macro(name):
    m = re.search(r'\\newcommand\{\\' + re.escape(name) + r'\}\{([^}]*)\}', macros)
    assert m, name
    return m.group(1)
assert macro('LGPrimaryObligations') == str(summary['primary_evaluated_obligations'])
assert macro('LGSources') == str(summary['source_ids_covered'])
assert macro('LGNativeSelftests') == str(summary['native_selftest_rows'])
print('claim_macro_snapshot PASS')

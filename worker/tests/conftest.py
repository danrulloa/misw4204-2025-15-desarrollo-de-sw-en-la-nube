# Ensure the worker root is importable so `import tasks...` works reliably in CI
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # worker/
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

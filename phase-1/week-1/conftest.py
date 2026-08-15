"""Makes `notes_service` importable from the tests folder next door.

Without this, `from notes_service.main import app` in the test file fails
with "no module named notes_service" — pytest doesn't automatically know
this folder exists as an import root. This file exists purely to fix that,
and pytest picks it up on its own; nothing else needs to reference it.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

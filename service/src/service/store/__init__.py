"""Local prediction store — persists generated draws and scenario paths to a
JSON Lines file so results survive service restarts.

The store is intentionally simple: append-only JSON Lines, process-wide
in-memory index. Later this module can be replaced by a proper database
adapter without touching any other code — the public surface is stable.

Public surface:
- `save_next_draw(prediction)` — persist a generated next-draw prediction.
- `save_scenario_path(prediction)` — persist a generated scenario-path prediction.
- `list_predictions(kind, page, page_size)` — paginate stored predictions.
- `reset_store()` — clear in-memory state (tests only).
"""

from service.store.predictions import (
    list_predictions,
    reset_store,
    save_next_draw,
    save_scenario_path,
)

__all__ = [
    "list_predictions",
    "reset_store",
    "save_next_draw",
    "save_scenario_path",
]

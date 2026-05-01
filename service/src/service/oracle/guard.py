"""Input guard for the dream-oracle to prevent prompt injection.

Validates the raw dream description before it is passed to the LLM.
Raises ``DreamGuardError`` (a subclass of ``ValueError``) when the input
contains patterns associated with prompt injection attempts.
"""

from __future__ import annotations

import re
import unicodedata

# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------


class DreamGuardError(ValueError):
    """Raised when the dream description fails the safety guard."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


# ---------------------------------------------------------------------------
# Injection pattern registry
# ---------------------------------------------------------------------------

# These patterns target classic prompt-injection phrasing.
# They are intentionally focused to minimise false positives on legitimate
# dream descriptions written in English or Portuguese.
_INJECTION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bignore\s+(all\s+)?(previous|prior|above|earlier)\b", re.I), "instruction-override phrase"),
    (re.compile(r"\bdisregard\s+(all\s+)?(previous|prior|above|earlier|instructions?)\b", re.I), "instruction-override phrase"),
    (re.compile(r"\bforget\s+(all\s+)?(previous|prior|above|instructions?|rules?)\b", re.I), "instruction-override phrase"),
    (re.compile(r"\bnew\s+(system\s+)?instructions?\s*(start|begin|follow|:)", re.I), "instruction-injection marker"),
    (re.compile(r"\boverride\s+(all\s+)?(previous|prior|system)\b", re.I), "instruction-override phrase"),
    (re.compile(r"\byou\s+are\s+now\b", re.I), "persona-hijack phrase"),
    (re.compile(r"\bact\s+as\s+(if\s+you\s+are|a\b)", re.I), "persona-hijack phrase"),
    (re.compile(r"\bpretend\s+(you\s+are|to\s+be)\b", re.I), "persona-hijack phrase"),
    (re.compile(r"\byour\s+(new\s+)?role\s+is\b", re.I), "persona-hijack phrase"),
    # Structural injection markers used in fine-tuning / chat templates
    (re.compile(r"<\s*/?\s*system\s*>", re.I), "system-tag injection"),
    (re.compile(r"\[INST\]", re.I), "instruction-template marker"),
    (re.compile(r"###\s*(instruction|system|assistant|human|user)\b", re.I), "instruction-template marker"),
    (re.compile(r"<\|im_start\|>", re.I), "chat-template marker"),
    (re.compile(r"<\|endoftext\|>", re.I), "chat-template marker"),
    # Attempts to extract the system prompt
    (re.compile(r"\b(print|repeat|reveal|output|show|tell\s+me)\s+(your\s+)?(full\s+)?(system\s+prompt|instructions?|rules?)\b", re.I), "system-prompt extraction attempt"),
    # Jailbreak classics
    (re.compile(r"\bDAN\b"), "jailbreak keyword"),
    (re.compile(r"\bjailbreak\b", re.I), "jailbreak keyword"),
    (re.compile(r"\bdeveloper\s+mode\b", re.I), "jailbreak keyword"),
]

# Maximum ratio of non-alphabetic, non-space characters allowed.
# Very high symbol density is a signal for encoded or obfuscated payloads.
_MAX_SYMBOL_RATIO = 0.35

# Maximum run of the same character (catches "aaaa..." padding attacks).
_MAX_CHAR_RUN = 40


# ---------------------------------------------------------------------------
# Guard function
# ---------------------------------------------------------------------------


def check_dream_description(description: str) -> None:
    """Validate a dream description for prompt-injection signals.

    Raises
    ------
    DreamGuardError
        If any injection pattern is detected or structural heuristics fail.
    """
    # 1. Normalise unicode to NFC to prevent look-alike bypass attempts.
    normalised = unicodedata.normalize("NFC", description)

    # 2. Pattern matching.
    for pattern, label in _INJECTION_PATTERNS:
        if pattern.search(normalised):
            raise DreamGuardError(
                f"A descrição contém conteúdo não permitido ({label}). "
                "Por favor, descreva apenas o seu sonho ou situação."
            )

    # 3. Excessive symbol density check.
    non_alpha_space = sum(
        1 for ch in normalised if not ch.isalpha() and not ch.isspace()
    )
    if len(normalised) > 0 and (non_alpha_space / len(normalised)) > _MAX_SYMBOL_RATIO:
        raise DreamGuardError(
            "A descrição contém muitos caracteres especiais. "
            "Por favor, escreva em texto simples."
        )

    # 4. Repeated-character run check.
    run_pattern = re.compile(r"(.)\1{" + str(_MAX_CHAR_RUN) + r",}")
    if run_pattern.search(normalised):
        raise DreamGuardError(
            "A descrição contém sequências de caracteres repetidos que não são permitidas."
        )

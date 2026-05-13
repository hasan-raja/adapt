"""
Compression pipeline with 3 layers:
1. Semantic - summarization of old conversation turns
2. Token-level - abbreviations, fillers, formatting
3. Context pruning - keep only relevant recent turns
"""

import re
from typing import Optional
from app.models import CompressionLevel


# Common Hindi/English/Hinglish filler words to remove
FILLERS_EN = {
    "actually", "basically", "literally", "honestly", "simply", "just",
    "you know", "i mean", "kind of", "sort of", "pretty much", "so basically",
    "well basically", "like", "um", "uh", "er", "ah", "basically", "essentially"
}

FILLERS_HI = {
    "वास्तव में", "मूल रूप से", "सच में", "बस", "अभी", "तो", "मतलब", "यानी",
    "basically", "vakai mein", "sach mein", "bilkul", "thoda", "shayad"
}

# Abbreviations for common phrases (English & Hinglish)
ABBREVIATIONS: dict[str, str] = {
    "i want to": "→",
    "i need to": "→",
    "can you please": "pls",
    "could you please": "pls",
    "please help me": "help",
    "i am having": "having",
    "i'm having": "having",
    "there is a problem": "issue:",
    "there is an issue": "issue:",
    "not working": "broken",
    "how do i": "how to",
    "how can i": "how to",
    "what is the": "what's",
    "what are the": "what're",
    "information": "info",
    "application": "app",
    "registration": "reg",
    "verification": "verify",
    "available": "avail",
    "karna chahta hoon": "→",
    "karna hai": "→",
    "nahi chal raha": "broken",
    "kaise karein": "how to",
    "kya hai": "what is",
    "batayein": "tell",
}


# Indic script patterns - these chars take 2x space in some encodings
INDIC_RANGES = [
    (0x0900, 0x097F),  # Devanagari (Hindi)
    (0x0980, 0x09FF),  # Bengali
    (0x0A80, 0x0AFF),  # Gujarati
    (0x0B00, 0x0B7F),  # Oriya
    (0x0B80, 0x0BFF),  # Tamil
    (0x0C00, 0x0C7F),  # Telugu
    (0x0C80, 0x0CFF),  # Kannada
    (0x0D00, 0x0D7F),  # Malayalam
    (0x0E00, 0x0E7F),  # Thai
]

def is_indic_char(char: str) -> bool:
    codepoint = ord(char)
    return any(start <= codepoint <= end for start, end in INDIC_RANGES)


def detect_indic_content(text: str) -> float:
    """Return ratio of Indic characters (0-1)."""
    if not text:
        return 0.0
    indic_chars = sum(1 for c in text if is_indic_char(c))
    return indic_chars / len(text)


def compress_layer_fillers(text: str) -> str:
    """Layer 1: Remove filler words."""
    text = text.lower()
    for filler in FILLERS_EN:
        text = re.sub(rf'\b{re.escape(filler)}\b', '', text, flags=re.IGNORECASE)
    for filler in FILLERS_HI:
        text = text.replace(filler, '')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def compress_layer_abbreviations(text: str) -> str:
    """Layer 2: Apply abbreviations."""
    text_lower = text.lower()
    for phrase, abbrev in ABBREVIATIONS.items():
        text_lower = text_lower.replace(phrase, abbrev)
        text = text.replace(phrase.capitalize(), abbrev)
    return text_lower if text_lower != text.lower() else text


def compress_whitespace(text: str) -> str:
    """Normalize whitespace."""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'([.!?,])\s*', r'\1 ', text)
    text = re.sub(r'\s+([.!?,])', r'\1', text)
    return text.strip()


def compress_conversation_history(history: list[dict], max_turns: int, compression: CompressionLevel) -> list[dict]:
    """
    Context pruning: Keep only the most recent N turns.
    Layer 3 (semantic): For older turns, summarize instead of discard.
    """
    if not history:
        return []

    if compression == CompressionLevel.NONE:
        return history

    # Determine keep ratio based on compression level
    keep_ratios = {
        CompressionLevel.LIGHT: 0.8,
        CompressionLevel.MEDIUM: 0.5,
        CompressionLevel.AGGRESSIVE: 0.2,
    }
    keep_ratio = keep_ratios.get(compression, 0.5)

    total_turns = len(history)
    keep_count = max(1, int(total_turns * keep_ratio))

    # Keep recent turns
    recent = history[-keep_count:]

    # Summarize older turns if we have any
    if total_turns > keep_count and keep_count > 0:
        older_turns = history[:-keep_count]

        # Simple summary: just the first user message and last assistant response
        if older_turns:
            summary_parts = []
            for turn in older_turns:
                if turn.get("role") == "user":
                    compressed = compress_layer_fillers(turn.get("content", ""))
                    compressed = compress_whitespace(compressed)
                    if compressed:
                        summary_parts.append(f"U: {compressed[:50]}")
                elif turn.get("role") == "assistant":
                    compressed = compress_layer_fillers(turn.get("content", ""))
                    compressed = compress_whitespace(compressed)
                    if compressed:
                        summary_parts.append(f"A: {compressed[:50]}")

            if summary_parts:
                summary_entry = {
                    "role": "system",
                    "content": "[Earlier: " + " | ".join(summary_parts[:4]) + "]"
                }
                return [summary_entry] + recent
        return recent

    return recent


def compress_message(message: str, compression: CompressionLevel) -> str:
    """
    Apply L1 (fillers) + L2 (abbreviations) + L3 (whitespace) compression to a message.
    """
    if compression == CompressionLevel.NONE:
        return message

    text = message
    text = compress_layer_fillers(text)
    text = compress_layer_abbreviations(text)
    text = compress_whitespace(text)

    if compression == CompressionLevel.AGGRESSIVE:
        # Additional aggressive compression: truncate long messages
        if len(text) > 200:
            text = text[:200] + "..."

    return text


def calculate_compression_ratio(original: str, compressed: str) -> float:
    """Return compression ratio (lower = more compressed)."""
    if not original:
        return 1.0
    orig_len = len(original)
    comp_len = len(compressed)
    return comp_len / orig_len if orig_len > 0 else 1.0
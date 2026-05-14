import asyncio
import unittest

from app.core.cache import SemanticCache
from app.core.compression import compress_conversation_history, compress_message
from app.core.router import classify_task, select_model_for_request
from app.main import adapt_request
from app.models import CompressionLevel, NetworkTier, RequestPayload


class CoreBehaviorTests(unittest.TestCase):
    def test_sensitive_prompts_do_not_use_aggressive_compression(self):
        _, compression, task = select_model_for_request(
            NetworkTier.TIER_2G,
            "I have fever and chest pain, what should I do?",
        )

        self.assertEqual(task, "health")
        self.assertEqual(compression, CompressionLevel.MEDIUM)

    def test_general_2g_prompt_can_be_aggressive(self):
        _, compression, task = select_model_for_request(
            NetworkTier.TIER_2G,
            "Summarize crop rotation in simple words",
        )

        self.assertEqual(task, "summarization")
        self.assertEqual(compression, CompressionLevel.AGGRESSIVE)

    def test_cache_skips_sensitive_terms(self):
        cache = SemanticCache()

        self.assertFalse(cache.should_cache("My UPI PIN is not working"))
        self.assertTrue(cache.should_cache("Explain crop rotation simply"))

    def test_history_compression_adds_summary(self):
        history = [
            {"role": "user", "content": "I want to understand crop rotation"},
            {"role": "assistant", "content": "Crop rotation improves soil health."},
            {"role": "user", "content": "Can you please explain water saving?"},
            {"role": "assistant", "content": "Use drip irrigation and mulch."},
        ]

        compressed = compress_conversation_history(history, 6, CompressionLevel.MEDIUM)

        self.assertLess(len(compressed), len(history))
        self.assertEqual(compressed[0]["role"], "system")

    def test_adapt_response_contains_routing_metadata(self):
        payload = RequestPayload(
            session_id="test-session",
            message="UPI PIN safety for a first-time user",
            force_tier=NetworkTier.TIER_2G,
        )

        result = asyncio.run(adapt_request(payload))

        self.assertEqual(result.tier_used, NetworkTier.TIER_2G)
        self.assertTrue(result.model_used)
        self.assertTrue(result.task_type)
        self.assertGreaterEqual(result.tokens_used, 0)


if __name__ == "__main__":
    unittest.main()

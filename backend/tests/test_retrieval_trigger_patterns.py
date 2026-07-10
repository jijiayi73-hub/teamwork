"""Test retrieval trigger patterns with Chinese characters.

This test validates that the regex patterns work correctly for Chinese
continuity expressions and memory references.
"""
import re
import pytest
from app.services.retrieval_trigger_service import (
    EXPLICIT_MEMORY_PATTERNS,
    CONTINUITY_PATTERNS,
    NEGATIVE_PATTERNS,
)


class TestChineseRegexPatterns:
    """Test suite for Chinese regex pattern matching."""

    def test_explicit_memory_patterns_compile(self):
        """Test all explicit memory patterns compile successfully."""
        for pattern_str in EXPLICIT_MEMORY_PATTERNS:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            assert pattern is not None

    def test_xiangxi_pattern_matches(self):
        """Test memory-related patterns match expected strings."""
        # Test all explicit patterns
        explicit_patterns = [re.compile(p, re.IGNORECASE) for p in EXPLICIT_MEMORY_PATTERNS]

        test_cases = [
            # Should match - memory related expressions (explicit references)
            ("回想一下", True),
            ("让我回想", True),
            ("我在回想", True),
            ("帮我回想一下", True),
            ("回想上次", True),
            ("慢慢回想", True),
            ("让我想一想", True),
            ("我想起来了", True),
            ("我想想", True),
            ("想起一件事", True),
            ("还记得吗", True),
            ("你记得吗", True),
            ("有没有记得", True),
            ("那个时候", True),

            # Should not match - these don't explicitly reference memory
            ("普通的问候", False),
            ("今天天气不错", False),
            ("我在看书", False),
            ("还是那样", False),  # "还是那样" is continuity, not explicit memory
            ("再次遇到", False),  # "再次遇到" is continuity, not explicit memory
            ("又一次", False),  # "又一次" is continuity, not explicit memory
        ]

        for test_str, should_match in test_cases:
            matched = any(pattern.search(test_str) for pattern in explicit_patterns)
            assert matched == should_match, f"Pattern failed for: {test_str} (expected: {should_match}, got: {matched})"

    def test_explicit_memory_patterns_in_context(self):
        """Test explicit memory patterns in real user message context."""
        # Compile all patterns like the service does
        explicit_patterns = [re.compile(p, re.IGNORECASE) for p in EXPLICIT_MEMORY_PATTERNS]

        test_messages = [
            ("帮我回想一下上次我们聊了什么", "回想"),
            ("还记得我们之前说过的话吗", "还记得.*吗"),
            ("以前我也遇到过类似的情况", "以前.*过"),
            ("后来怎么样了", "后来"),
            ("记得那件事吗", "记得"),
            ("记不记得我们一起去过的那个地方", "记.*不.*得"),
        ]

        for message, expected_pattern in test_messages:
            matched = False
            for pattern in explicit_patterns:
                if pattern.search(message):
                    matched = True
                    break

            assert matched, f"No pattern matched for: {message} (expected: {expected_pattern})"

    def test_negative_patterns_do_not_match_memory_queries(self):
        """Test negative patterns don't incorrectly block memory queries."""
        negative_patterns = [re.compile(p, re.IGNORECASE) for p in NEGATIVE_PATTERNS]

        memory_queries = [
            "帮我回想一下",
            "还记得吗",
            "上次说的那件事",
            "让我回忆一下",
            "想起以前的事",
        ]

        for query in memory_queries:
            for pattern in negative_patterns:
                # negative patterns use match() (start of string)
                assert not pattern.match(query), f"Negative pattern incorrectly matched: {query}"

    def test_continuity_patterns_match(self):
        """Test continuity patterns match expected strings."""
        continuity_patterns = [re.compile(p, re.IGNORECASE) for p in CONTINUITY_PATTERNS]

        test_cases = [
            ("我又遇到了同样的情况", True),
            ("还是老样子", True),
            ("一直这样", True),
            ("每次都是这样", True),
            ("越来越严重", True),
            ("又来了", True),
            ("像以前一样", True),
            ("一切如故", True),
            ("还在继续", True),
            ("依旧是这样", True),
            ("照旧处理", True),
            ("照样进行", True),
            ("还是那样", True),
            ("再次遇到", True),
            ("又一次", True),
            ("正常的问候", False),
            ("今天天气不错", False),
        ]

        for test_str, should_match in test_cases:
            matched = any(pattern.search(test_str) for pattern in continuity_patterns)
            assert matched == should_match, f"Continuity pattern failed for: {test_str} (expected: {should_match}, got: {matched})"

    def test_xiangxi_case_sensitivity(self):
        """Test that Chinese characters work with IGNORECASE flag."""
        pattern = re.compile(r"回想", re.IGNORECASE)

        # Chinese characters don't have case, but should still work
        assert pattern.search("回想一下") is not None
        assert pattern.search("回想") is not None

from __future__ import annotations

# Each entry names a set of switch-field names (matching
# switches.py::_AGENT_FLAG_NAMES) that has been proven, via its own dedicated
# interaction test, to produce a genuine data handoff when both agents are
# LLM-backed simultaneously — not merely that both happen to run in the same
# request. See RULES.md §17.2 and MAIN.md §7.8.3/§7.8.4.
#
# Adding an entry here without a corresponding interaction test and phase
# recap is a violation of RULES.md §17.2, even though nothing at runtime can
# enforce that a test actually exists.
VALIDATED_COMBINATIONS: frozenset[frozenset[str]] = frozenset(
    {
        # Rebuild-22C: load_curriculum persists the curriculum agent's real
        # output; load_critic_review reads it back and feeds it to the critic
        # agent — a genuine LLM->LLM handoff already exists structurally in
        # app/orchestration/nodes.py, requiring no graph change. Proven by
        # test_multi_agent_curriculum_critic_agent_interaction.py.
        frozenset({"critic_agent_mode", "curriculum_agent_mode"}),
    },
)

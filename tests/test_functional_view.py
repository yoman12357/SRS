"""Actor-visible security requirements remain visible in the functional section."""

from copy import deepcopy

from cybersrs.validation import assign_ids, rebuild_functional_view


def test_actor_security_actions_are_indexed_without_new_normative_rows(analysis, sections):
    """Reproduce security-only classification and rebuild a view after a later section exists."""
    content = {
        name: assign_ids(name, deepcopy(sections[name]))
        for name in ("functional", "security", "data")
    }
    content["functional"]["requirements"] = []
    content["functional"]["applicability_reason"] = "No functional behavior supplied."
    original = deepcopy(content["security"])
    rebuild_functional_view(content, analysis)
    assert content["functional"]["related_requirement_ids"] == ["SEC-001"]
    assert not content["functional"]["requirements"]
    assert "Actor-visible" in content["functional"]["applicability_reason"]
    assert content["security"] == original
    first = deepcopy(content)
    rebuild_functional_view(content, analysis)
    assert content == first


def test_background_controls_do_not_manufacture_functional_actor_links(analysis, sections):
    """A retention process does not become a user action merely to fill a section."""
    content = {
        name: assign_ids(name, deepcopy(sections[name])) for name in ("functional", "security")
    }
    content["security"]["requirements"][0]["statement"] = "The system shall retain logs."
    rebuild_functional_view(content, analysis)
    assert content["functional"]["related_requirement_ids"] == []

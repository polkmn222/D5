"""
Unit tests for Phase 169: Responsive UI and Form Refinement
Tests verify:
1. The CSS file contains the rule to hide Save & New inside agent form shell.
2. The CSS file contains overflow-x: auto for responsive tables.
3. The secondary action button style exists.
4. The JS wireAgentInlineForm still has the save-new handler as fallback.
"""

import os

CSS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..",
    "ai_agent", "frontend", "static", "css", "ai_agent.css"
)

JS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..",
    "ai_agent", "frontend", "static", "js", "ai_agent.js"
)


def _read(path: str) -> str:
    abs_path = os.path.normpath(path)
    with open(abs_path, "r") as f:
        return f.read()


class TestSaveNewButtonHidden:
    """Verify CSS hides Save & New in AI Agent form shell."""

    def test_css_has_save_new_hide_rule(self):
        css = _read(CSS_PATH)
        assert 'button[data-submit-mode="save-new"]' in css
        assert "display: none" in css

    def test_hide_rule_scoped_to_agent_form_shell(self):
        css = _read(CSS_PATH)
        assert '.agent-inline-form-shell button[data-submit-mode="save-new"]' in css

    def test_js_still_has_save_new_fallback(self):
        """Ensure the JS handler for save-new still exists even though the button is hidden."""
        js = _read(JS_PATH)
        assert "save-new" in js


class TestResponsiveTables:
    """Verify CSS enables horizontal table scrolling."""

    def test_results_container_has_overflow_x_auto(self):
        css = _read(CSS_PATH)
        # Extract the results-container block
        idx = css.index(".results-container {")
        block = css[idx:css.index("}", idx) + 1]
        assert "overflow-x: auto" in block


class TestSecondaryActionButtonStyle:
    """Verify the secondary action button style exists for Send Message."""

    def test_secondary_action_style_exists(self):
        css = _read(CSS_PATH)
        assert ".agent-paste-action-secondary" in css

    def test_secondary_action_hover_style_exists(self):
        css = _read(CSS_PATH)
        assert ".agent-paste-action-secondary:hover" in css

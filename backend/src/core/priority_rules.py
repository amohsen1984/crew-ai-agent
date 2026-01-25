"""Priority rules configuration management."""

import json
import logging
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)


class PriorityRulesManager:
    """Manages priority rules configuration with file persistence."""

    def __init__(self, output_dir: Path):
        """Initialize PriorityRulesManager.

        Args:
            output_dir: Directory where priority rules file will be stored.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.priority_rules_file = self.output_dir / "priority_rules.json"
        self._rules: Dict = self._load_rules()

    def _get_default_rules(self) -> Dict:
        """Get default priority rules for all categories.

        Returns:
            Dictionary with default priority rules.
        """
        return {
            "Bug": {
                "default": "Medium",
                "critical_keywords": [
                    "data loss",
                    "complete data loss",
                    "all data",
                    "unusable",
                    "cannot access",
                    "app won't start",
                    "startup crash",
                    "crashes every time",
                    "crashes immediately",
                    "crashes on startup",
                ],
                "high_keywords": [
                    "blank screen",
                    "freeze",
                    "notifications not working",
                    "not responding",
                    "crash",
                    "crashes",
                    "crashing",
                    "slow",
                    "performance",
                    "lag",
                    "frozen",
                    "stuck",
                ],
                "medium_keywords": [
                    "permission",
                    "security",
                    "unexpected",
                    "question",
                    "concern",
                    "explanation",
                ],
                "low_keywords": ["cosmetic", "minor", "typo", "spelling", "text"],
            },
            "Feature Request": {
                "default": "Low",
                "critical_keywords": [],
                "high_keywords": [],
                "medium_keywords": [
                    "integration",
                    "calendar",
                    "recurring",
                    "offline",
                    "sync",
                    "collaboration",
                    "team",
                ],
                "low_keywords": [
                    "widget",
                    "dark mode",
                    "theme",
                    "color",
                    "shortcut",
                    "voice",
                    "Siri",
                    "simple",
                ],
            },
            "Complaint": {
                "default": "Medium",
                "critical_keywords": [],
                "high_keywords": [
                    "duplicate charge",
                    "refund",
                    "billing",
                    "payment",
                    "charge",
                ],
                "medium_keywords": [
                    "pricing",
                    "price",
                    "expensive",
                    "cost",
                    "subscription",
                    "premium",
                    "paid",
                    "support",
                    "response time",
                    "customer service",
                    "performance",
                    "UI",
                    "design",
                    "slow",
                ],
                "low_keywords": ["suggestion", "preference", "minor"],
            },
        }

    def _load_rules(self) -> Dict:
        """Load priority rules from JSON file.

        Returns:
            Priority rules dictionary, or empty dict if file doesn't exist.
        """
        if self.priority_rules_file.exists():
            try:
                with open(self.priority_rules_file, "r") as f:
                    rules = json.load(f)
                    logger.info(
                        f"Loaded priority rules from {self.priority_rules_file}"
                    )
                    return rules
            except Exception as e:
                logger.warning(
                    f"Could not load priority rules from file: {e}"
                )
                return {}
        return {}

    def _save_rules(self) -> bool:
        """Save priority rules to JSON file.

        Returns:
            True if successful, False otherwise.
        """
        try:
            self.priority_rules_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.priority_rules_file, "w") as f:
                json.dump(self._rules, f, indent=2)
            logger.info(f"Saved priority rules to {self.priority_rules_file}")
            return True
        except Exception as e:
            logger.error(
                f"Error saving priority rules to file: {e}", exc_info=True
            )
            return False

    def set_rules(self, rules: Dict) -> Dict:
        """Set priority rules configuration.

        Merges incoming rules with existing rules (or defaults) to ensure
        all categories are present.

        Args:
            rules: Dictionary with priority rules for each category (may be partial).

        Returns:
            Result dictionary with status.
        """
        try:
            # Get defaults for all categories
            default_rules = self._get_default_rules()

            # Start with existing rules (or defaults if first time)
            merged_rules = (
                self._rules.copy() if self._rules else default_rules.copy()
            )

            # Merge incoming rules with existing/defaults
            # This ensures if user updates one category, others are preserved
            for category, category_rules in rules.items():
                if category in default_rules:
                    # Merge category rules: use incoming if provided, otherwise keep existing/default
                    if category not in merged_rules:
                        merged_rules[category] = default_rules[category].copy()

                    # Update with incoming rules for this category
                    merged_rules[category].update(category_rules)
                else:
                    logger.warning(
                        f"Unknown category '{category}' in priority rules, ignoring"
                    )

            # Ensure all categories are present (use defaults if missing)
            for category in default_rules:
                if category not in merged_rules:
                    merged_rules[category] = default_rules[category].copy()

            self._rules = merged_rules

            # Save to file
            if not self._save_rules():
                return {
                    "status": "error",
                    "error": "Failed to save priority rules to file",
                }

            logger.info(
                "Priority rules updated successfully (merged with existing/defaults)"
            )
            return {"status": "success", "message": "Priority rules updated and saved"}
        except Exception as e:
            logger.error(f"Error setting priority rules: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    def get_rules(self) -> Dict:
        """Get current priority rules configuration.

        Returns:
            Current priority rules dictionary (with defaults if none set).
        """
        if not self._rules:
            return self._get_default_rules()

        # Ensure all categories are present (merge with defaults if missing)
        default_rules = self._get_default_rules()
        merged_rules = default_rules.copy()
        merged_rules.update(self._rules)

        # Ensure each category has all required fields
        for category in default_rules:
            if category in merged_rules:
                # Merge category-level defaults with existing rules
                merged_rules[category] = {
                    **default_rules[category],
                    **merged_rules[category],
                }
            else:
                merged_rules[category] = default_rules[category]

        return merged_rules

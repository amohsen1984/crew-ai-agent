"""Unit tests for agents."""

import pytest

from agents.feedback_agents import (
    create_classifier_agent,
    create_bug_analyzer_agent,
    create_feature_extractor_agent,
    create_ticket_creator_agent,
    create_quality_critic_agent,
    create_csv_reader_agent,
)


class TestClassifierAgent:
    """Test classifier agent creation."""

    @pytest.fixture
    def classifier(self):
        """Create classifier agent for testing."""
        return create_classifier_agent()

    def test_agent_has_correct_role(self, classifier):
        """Classifier should have correct role defined."""
        assert "classifier" in classifier.role.lower() or \
               "classification" in classifier.role.lower()

    def test_agent_has_goal(self, classifier):
        """Classifier should have a goal defined."""
        assert classifier.goal is not None
        assert len(classifier.goal) > 10

    def test_agent_has_backstory(self, classifier):
        """Classifier should have backstory defined."""
        assert classifier.backstory is not None


class TestBugAnalyzerAgent:
    """Test bug analyzer agent creation."""

    @pytest.fixture
    def bug_analyzer(self):
        """Create bug analyzer agent for testing."""
        return create_bug_analyzer_agent()

    def test_agent_has_correct_role(self, bug_analyzer):
        """Bug analyzer should have correct role."""
        assert "bug" in bug_analyzer.role.lower()


class TestFeatureExtractorAgent:
    """Test feature extractor agent creation."""

    @pytest.fixture
    def feature_extractor(self):
        """Create feature extractor agent for testing."""
        return create_feature_extractor_agent()

    def test_agent_has_correct_role(self, feature_extractor):
        """Feature extractor should have correct role."""
        assert "feature" in feature_extractor.role.lower()


class TestTicketCreatorAgent:
    """Test ticket creator agent creation."""

    @pytest.fixture
    def ticket_creator(self):
        """Create ticket creator agent for testing."""
        return create_ticket_creator_agent()

    def test_agent_has_tools(self, ticket_creator):
        """Ticket creator should have tools assigned."""
        assert ticket_creator.tools is not None
        assert len(ticket_creator.tools) > 0


class TestQualityCriticAgent:
    """Test quality critic agent creation."""

    @pytest.fixture
    def quality_critic(self):
        """Create quality critic agent for testing."""
        return create_quality_critic_agent()

    def test_agent_has_correct_role(self, quality_critic):
        """Quality critic should have correct role."""
        assert "quality" in quality_critic.role.lower() or \
               "reviewer" in quality_critic.role.lower()


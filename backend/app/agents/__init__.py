"""
Multi-Agent System for Legal Aid Platform.

This package contains the three core agents:
- Researcher: Analyzes grievances and identifies legal provisions
- Drafter: Creates formal legal petitions
- Expert Reviewer: Audits and validates legal documents
"""
from .researcher import ResearcherAgent
from .drafter import DrafterAgent
from .expert_reviewer import ExpertReviewerAgent

__all__ = ["ResearcherAgent", "DrafterAgent", "ExpertReviewerAgent"]

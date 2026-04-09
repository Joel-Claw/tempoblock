"""
Tests for Tempoblock
"""



from tempoblock.blocker import WEBSITE_ALIASES
from tempoblock.cli import parse_duration


class TestBlocker:
    """Test Blocker class."""

    def test_website_aliases(self):
        """Test that website aliases expand correctly."""
        assert "twitter.com" in WEBSITE_ALIASES["twitter"]
        assert "x.com" in WEBSITE_ALIASES["twitter"]
        assert "youtube.com" in WEBSITE_ALIASES["youtube"]
        assert "youtu.be" in WEBSITE_ALIASES["youtube"]

    def test_parse_duration_minutes(self):
        """Test duration parsing."""
        assert parse_duration("30m") == 30
        assert parse_duration("1h") == 60
        assert parse_duration("2h") == 120
        assert parse_duration("1h30m") == 90
        assert parse_duration("45") == 45  # Plain number = minutes


class TestAliases:
    """Test command aliases."""

    def test_twitter_alias(self):
        """Test that 'twitter' expands to twitter.com and x.com."""
        assert "twitter.com" in WEBSITE_ALIASES["twitter"]
        assert "x.com" in WEBSITE_ALIASES["twitter"]

    def test_youtube_alias(self):
        """Test YouTube aliases."""
        assert "youtube.com" in WEBSITE_ALIASES["youtube"]
        assert "youtu.be" in WEBSITE_ALIASES["youtube"]
"""Tests for CFDatabaseCreation test database safety guard."""
import pytest
from unittest.mock import MagicMock
from django.core.exceptions import ImproperlyConfigured

from django_cf.db.base_engine import CFDatabaseCreation


class TestCFDatabaseCreationTestSafety:
    """Tests for CFDatabaseCreation _create_test_db safety guard."""

    def _get_creation(self, test_settings=None):
        """Create a CFDatabaseCreation instance with mocked connection."""
        mock_connection = MagicMock()
        mock_connection.settings_dict = {"TEST": test_settings or {}}
        return CFDatabaseCreation(mock_connection)

    def test_create_test_db_always_raises_error(self):
        """Test that _create_test_db ALWAYS raises ImproperlyConfigured."""
        creation = self._get_creation(test_settings={})
        
        with pytest.raises(ImproperlyConfigured) as exc_info:
            creation._create_test_db(verbosity=0, autoclobber=False)
        
        error_msg = str(exc_info.value)
        assert "Running Django tests against Cloudflare D1/Durable Objects is not supported" in error_msg
        assert "DESTROY your production data" in error_msg
        assert "settings/test.py" in error_msg
        assert "django.db.backends.sqlite3" in error_msg

    def test_create_test_db_raises_even_when_test_name_is_set(self):
        """Test that _create_test_db still raises when TEST['NAME'] is configured."""
        # Setting TEST['NAME'] does NOT isolate D1 databases because the D1
        # backend connects via CLOUDFLARE_DATABASE_ID, not NAME.
        creation = self._get_creation(test_settings={"NAME": ":memory:"})
        
        with pytest.raises(ImproperlyConfigured) as exc_info:
            creation._create_test_db(verbosity=0, autoclobber=False)
        
        error_msg = str(exc_info.value)
        assert "DESTROY your production data" in error_msg

    def test_error_message_includes_safe_config_example(self):
        """Test that error message includes example safe configuration."""
        creation = self._get_creation(test_settings={})
        
        with pytest.raises(ImproperlyConfigured) as exc_info:
            creation._create_test_db(verbosity=0, autoclobber=False)
        
        error_msg = str(exc_info.value)
        assert "settings/test.py" in error_msg
        assert "--settings=settings.test" in error_msg
        assert "django.db.backends.sqlite3" in error_msg

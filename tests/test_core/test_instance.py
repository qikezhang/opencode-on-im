"""Tests for InstanceRegistry."""

import pytest
from pathlib import Path
import tempfile
import json

from opencode_on_im.core.config import Settings
from opencode_on_im.core.instance import InstanceRegistry, Instance


@pytest.fixture
def temp_settings():
    """Create settings with temporary data directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Settings(data_dir=Path(tmpdir), secret_key="test-secret-key")


@pytest.fixture
def registry(temp_settings):
    """Create an InstanceRegistry."""
    return InstanceRegistry(temp_settings)


class TestInstanceRegistry:
    """Tests for InstanceRegistry class."""

    def test_create_instance(self, registry):
        """Test creating a new instance."""
        instance = registry.create_instance(name="my-project")

        assert instance.name == "my-project"
        assert instance.id is not None
        assert instance.connect_secret is not None
        assert instance.qr_version == 1

    def test_create_instance_auto_name(self, registry):
        """Test auto-naming when no name provided."""
        instance = registry.create_instance()

        assert instance.name == "instance"

    def test_create_instance_auto_name_increments(self, registry):
        """Test auto-naming increments for duplicates."""
        registry.create_instance()  # "instance"
        instance2 = registry.create_instance()  # "instance-1"
        instance3 = registry.create_instance()  # "instance-2"

        assert instance2.name == "instance-1"
        assert instance3.name == "instance-2"

    def test_get_instance(self, registry):
        """Test getting instance by ID."""
        created = registry.create_instance(name="test")

        fetched = registry.get_instance(created.id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == "test"

    def test_get_instance_nonexistent(self, registry):
        """Test getting non-existent instance returns None."""
        result = registry.get_instance("does-not-exist")
        assert result is None

    def test_get_instance_by_name(self, registry):
        """Test getting instance by name."""
        registry.create_instance(name="my-project")

        instance = registry.get_instance_by_name("my-project")

        assert instance is not None
        assert instance.name == "my-project"

    def test_list_instances(self, registry):
        """Test listing all instances."""
        registry.create_instance(name="proj-1")
        registry.create_instance(name="proj-2")

        instances = registry.list_instances()

        assert len(instances) == 2
        names = [i.name for i in instances]
        assert "proj-1" in names
        assert "proj-2" in names

    def test_rename_instance(self, registry):
        """Test renaming an instance."""
        instance = registry.create_instance(name="old-name")

        result = registry.rename_instance(instance.id, "new-name")

        assert result is True
        fetched = registry.get_instance(instance.id)
        assert fetched.name == "new-name"

    def test_rename_instance_duplicate_fails(self, registry):
        """Test renaming to existing name fails."""
        registry.create_instance(name="existing")
        instance = registry.create_instance(name="other")

        result = registry.rename_instance(instance.id, "existing")

        assert result is False

    def test_delete_instance(self, registry):
        """Test deleting an instance."""
        instance = registry.create_instance(name="to-delete")

        result = registry.delete_instance(instance.id)

        assert result is True
        assert registry.get_instance(instance.id) is None

    def test_reset_qr(self, registry):
        """Test resetting QR code."""
        instance = registry.create_instance(name="test")
        old_secret = instance.connect_secret

        updated = registry.reset_qr(instance.id)

        assert updated is not None
        assert updated.qr_version == 2
        assert updated.connect_secret != old_secret

    def test_verify_connect_secret(self, registry):
        """Test verifying connect secret."""
        instance = registry.create_instance(name="test")

        assert registry.verify_connect_secret(instance.id, instance.connect_secret) is True
        assert registry.verify_connect_secret(instance.id, "wrong-secret") is False

    def test_generate_qr_data(self, registry):
        """Test generating QR code data."""
        instance = registry.create_instance(name="test")

        qr_data = registry.generate_qr_data(instance)

        assert qr_data is not None
        # Should be base64 encoded
        import base64
        decoded = json.loads(base64.urlsafe_b64decode(qr_data))
        assert decoded["instance_id"] == instance.id
        assert decoded["instance_name"] == "test"
        assert decoded["connect_secret"] == instance.connect_secret

    def test_generate_qr_image(self, registry):
        """Test generating QR code image."""
        instance = registry.create_instance(name="test")

        image_bytes = registry.generate_qr_image(instance)

        assert image_bytes is not None
        assert len(image_bytes) > 0
        # PNG magic bytes
        assert image_bytes[:8] == b'\x89PNG\r\n\x1a\n'

    def test_persistence(self, temp_settings):
        """Test that instances persist across registry instances."""
        # Create and save
        registry1 = InstanceRegistry(temp_settings)
        instance = registry1.create_instance(name="persistent")

        # Load in new registry
        registry2 = InstanceRegistry(temp_settings)

        fetched = registry2.get_instance(instance.id)
        assert fetched is not None
        assert fetched.name == "persistent"

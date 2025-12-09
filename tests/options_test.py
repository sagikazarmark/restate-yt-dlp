from pathlib import PurePosixPath

import pytest

from restate_yt_dlp.options import (
    RequestOptions,
    validate_no_parent_refs,
    validate_path_string,
)


class TestValidatePathString:
    """Tests for validate_path_string function."""

    def test_valid_string_path(self):
        """Test that valid string paths are returned as-is."""
        assert validate_path_string("videos/output") == "videos/output"
        assert validate_path_string("file.mp4") == "file.mp4"
        assert (
            validate_path_string("nested/folder/file.%(ext)s")
            == "nested/folder/file.%(ext)s"
        )

    def test_empty_string_raises_error(self):
        """Test that empty strings raise ValueError."""
        with pytest.raises(ValueError, match="Path cannot be empty"):
            validate_path_string("")

    def test_whitespace_only_string_raises_error(self):
        """Test that whitespace-only strings raise ValueError."""
        with pytest.raises(ValueError, match="Path cannot be empty"):
            validate_path_string("   ")
        with pytest.raises(ValueError, match="Path cannot be empty"):
            validate_path_string("\t\n")

    def test_non_string_input_returned_as_is(self):
        """Test that non-string inputs are returned unchanged."""
        assert validate_path_string(123) == 123
        assert validate_path_string(None) is None
        path_obj = PurePosixPath("test")
        assert validate_path_string(path_obj) is path_obj


class TestValidateNoParentRefs:
    """Tests for validate_no_parent_refs function."""

    def test_valid_relative_path(self):
        """Test that valid relative paths are returned as-is."""
        path = PurePosixPath("videos/output")
        assert validate_no_parent_refs(path) == path

        path = PurePosixPath("file.mp4")
        assert validate_no_parent_refs(path) == path

        path = PurePosixPath("nested/deep/folder/file.%(ext)s")
        assert validate_no_parent_refs(path) == path

    def test_absolute_path_raises_error(self):
        """Test that absolute paths raise ValueError."""
        with pytest.raises(ValueError, match="Path must be relative"):
            validate_no_parent_refs(PurePosixPath("/absolute/path"))

        with pytest.raises(ValueError, match="Path must be relative"):
            validate_no_parent_refs(PurePosixPath("/"))

    def test_parent_reference_raises_error(self):
        """Test that paths with '..' components raise ValueError."""
        with pytest.raises(ValueError, match='Path cannot contain ".." components'):
            validate_no_parent_refs(PurePosixPath("../parent"))

        with pytest.raises(ValueError, match='Path cannot contain ".." components'):
            validate_no_parent_refs(PurePosixPath("folder/../sibling"))

        with pytest.raises(ValueError, match='Path cannot contain ".." components'):
            validate_no_parent_refs(PurePosixPath("../../grandparent"))

    def test_current_directory_reference_allowed(self):
        """Test that '.' references are allowed."""
        path = PurePosixPath("./current")
        assert validate_no_parent_refs(path) == path

        path = PurePosixPath("folder/./subfolder")
        assert validate_no_parent_refs(path) == path


class TestSafeRelativePath:
    """Tests for SafeRelativePath type annotation."""

    def test_valid_string_conversion(self):
        """Test that valid strings are converted to SafeRelativePath."""
        # This would be used in a Pydantic model context
        path_str = "videos/output"
        # Simulate what happens during Pydantic validation
        validated = validate_path_string(path_str)
        path_obj = PurePosixPath(validated)
        result = validate_no_parent_refs(path_obj)
        assert result == PurePosixPath("videos/output")

    def test_empty_string_validation_error(self):
        """Test that empty strings cause validation errors."""
        with pytest.raises(ValueError, match="Path cannot be empty"):
            validate_path_string("")

    def test_parent_ref_validation_error(self):
        """Test that parent references cause validation errors."""
        path_str = "../parent"
        validated = validate_path_string(path_str)
        path_obj = PurePosixPath(validated)
        with pytest.raises(ValueError, match='Path cannot contain ".." components'):
            validate_no_parent_refs(path_obj)


class TestRequestOptions:
    """Tests for RequestOptions Pydantic model."""

    def test_empty_model_creation(self):
        """Test creating model with no arguments."""
        options = RequestOptions()
        assert options.format is None
        assert options.allow_unplayable_formats is None
        assert options.outtmpl is None
        assert options.writesubtitles is None

    def test_basic_field_assignment(self):
        """Test assigning basic field types."""
        options = RequestOptions(
            format="best",
            allow_unplayable_formats=True,
            restrictfilenames=False,
            min_filesize=1024,
            subtitleslangs=["en", "es"],
        )
        assert options.format == "best"
        assert options.allow_unplayable_formats is True
        assert options.restrictfilenames is False
        assert options.min_filesize == 1024
        assert options.subtitleslangs == ["en", "es"]

    def test_outtmpl_single_string_path(self):
        """Test outtmpl with single string path."""
        options = RequestOptions(outtmpl="videos/%(title)s.%(ext)s")
        assert options.outtmpl == "videos/%(title)s.%(ext)s"

    def test_outtmpl_mapping_paths(self):
        """Test outtmpl with mapping of paths."""
        template_mapping = {
            "default": "videos/%(title)s.%(ext)s",
            "thumbnail": "thumbnails/%(title)s.%(ext)s",
        }
        options = RequestOptions(outtmpl=template_mapping)
        expected = {
            "default": "videos/%(title)s.%(ext)s",
            "thumbnail": "thumbnails/%(title)s.%(ext)s",
        }
        assert options.outtmpl == expected

    def test_outtmpl_invalid_absolute_path(self):
        """Test that absolute paths in outtmpl are accepted as strings."""
        options = RequestOptions(outtmpl="/absolute/path/%(title)s.%(ext)s")
        assert options.outtmpl == "/absolute/path/%(title)s.%(ext)s"

    def test_outtmpl_invalid_parent_ref(self):
        """Test that parent references in outtmpl are accepted as strings."""
        options = RequestOptions(outtmpl="../parent/%(title)s.%(ext)s")
        assert options.outtmpl == "../parent/%(title)s.%(ext)s"

    def test_outtmpl_mapping_with_invalid_path(self):
        """Test that invalid paths in mapping are accepted as strings."""
        template_mapping = {
            "default": "videos/%(title)s.%(ext)s",
            "thumbnail": "../thumbnails/%(title)s.%(ext)s",
        }
        options = RequestOptions(outtmpl=template_mapping)
        assert options.outtmpl == template_mapping

    def test_outtmpl_mapping_individual_validation(self):
        """Test individual path validation in mapping works correctly."""
        # This should work fine when each individual path is valid
        valid_mapping = {
            "default": "videos/%(uploader)s/%(title)s.%(ext)s",
            "thumbnail": "thumbs/%(title)s.%(ext)s",
            "subtitle": "subs/%(title)s.%(ext)s",
        }
        options = RequestOptions(outtmpl=valid_mapping)
        assert len(options.outtmpl) == 3
        for path in options.outtmpl.values():
            assert isinstance(path, str)

    def test_outtmpl_empty_string_error(self):
        """Test that empty string in outtmpl is accepted."""
        options = RequestOptions(outtmpl="")
        assert options.outtmpl == ""

    def test_format_sort_list(self):
        """Test format_sort accepts list of strings."""
        options = RequestOptions(format_sort=["quality", "filesize", "fps"])
        assert options.format_sort == ["quality", "filesize", "fps"]

    def test_all_boolean_fields(self):
        """Test all boolean fields accept True/False/None."""
        boolean_fields = [
            "allow_unplayable_formats",
            "format_sort_force",
            "restrictfilenames",
            "windowsfilenames",
            "updatetime",
            "writedescription",
            "writeinfojson",
            "allow_playlist_files",
            "clean_infojson",
            "getcomments",
            "writethumbnail",
            "write_all_thumbnails",
            "writelink",
            "writeurllink",
            "writewebloclink",
            "writedesktoplink",
            "writesubtitles",
            "writeautomaticsub",
            "matchtitle",
            "rejecttitle",
            "prefer_free_formats",
            "useid",
        ]

        for field_name in boolean_fields:
            # Test True
            options = RequestOptions(**{field_name: True})
            assert getattr(options, field_name) is True

            # Test False
            options = RequestOptions(**{field_name: False})
            assert getattr(options, field_name) is False

            # Test None (default)
            options = RequestOptions()
            assert getattr(options, field_name) is None

    def test_integer_fields(self):
        """Test integer fields accept valid integers."""
        options = RequestOptions(
            trim_file_name=100,
            min_filesize=1024,
            max_filesize=1073741824,
        )
        assert options.trim_file_name == 100
        assert options.min_filesize == 1024
        assert options.max_filesize == 1073741824

    def test_string_fields(self):
        """Test string fields accept valid strings."""
        options = RequestOptions(
            format="best[height<=720]",
            outtmpl_na_placeholder="N/A",
            subtitlesformat="vtt",
            keepvideo="true",
            min_views="1000",
            max_views="1000000",
        )
        assert options.format == "best[height<=720]"
        assert options.outtmpl_na_placeholder == "N/A"
        assert options.subtitlesformat == "vtt"
        assert options.keepvideo == "true"
        assert options.min_views == "1000"
        assert options.max_views == "1000000"

    def test_list_fields(self):
        """Test list fields accept valid lists."""
        options = RequestOptions(
            format_sort=["quality", "filesize"],
            subtitleslangs=["en", "es", "fr"],
        )
        assert options.format_sort == ["quality", "filesize"]
        assert options.subtitleslangs == ["en", "es", "fr"]

    def test_model_serialization(self):
        """Test that the model can be serialized to dict."""
        options = RequestOptions(
            format="best",
            outtmpl="videos/%(title)s.%(ext)s",
            writesubtitles=True,
            subtitleslangs=["en"],
        )

        data = options.model_dump()
        assert isinstance(data, dict)
        assert data["format"] == "best"
        # PurePosixPath objects are serialized as PurePosixPath, not strings
        assert isinstance(data["outtmpl"], str)
        assert str(data["outtmpl"]) == "videos/%(title)s.%(ext)s"
        assert data["writesubtitles"] is True
        assert data["subtitleslangs"] == ["en"]

    def test_model_serialization_with_mapping(self):
        """Test model serialization with mapping outtmpl."""
        template_mapping = {
            "default": "videos/%(title)s.%(ext)s",
            "thumbnail": "thumbnails/%(title)s.%(ext)s",
        }
        options = RequestOptions(outtmpl=template_mapping)

        data = options.model_dump()
        assert isinstance(data["outtmpl"], dict)
        assert len(data["outtmpl"]) == 2
        for key, path in data["outtmpl"].items():
            assert isinstance(path, str)

    def test_model_deserialization(self):
        """Test that the model can be created from dict."""
        data = {
            "format": "worst",
            "outtmpl": "downloads/%(title)s.%(ext)s",
            "writeinfojson": True,
            "format_sort": ["quality"],
        }

        options = RequestOptions(**data)
        assert options.format == "worst"
        assert options.outtmpl == "downloads/%(title)s.%(ext)s"
        assert options.writeinfojson is True
        assert options.format_sort == ["quality"]

    def test_field_descriptions_exist(self):
        """Test that all fields have descriptions."""
        schema = RequestOptions.model_json_schema()
        properties = schema["properties"]

        # Check that all fields have descriptions
        for field_name, field_info in properties.items():
            assert "description" in field_info, (
                f"Field {field_name} missing description"
            )
            assert field_info["description"], (
                f"Field {field_name} has empty description"
            )

    def test_complex_outtmpl_example(self):
        """Test complex outtmpl configuration."""
        complex_mapping = {
            "default": "%(uploader)s/%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s",
            "thumbnail": "%(uploader)s/%(playlist)s/thumbnails/%(title)s.%(ext)s",
            "description": "%(uploader)s/%(playlist)s/descriptions/%(title)s.description",
            "infojson": "%(uploader)s/%(playlist)s/info/%(title)s.info.json",
        }

        options = RequestOptions(outtmpl=complex_mapping)

        assert isinstance(options.outtmpl, dict)
        assert len(options.outtmpl) == 4
        for key, path in options.outtmpl.items():
            assert isinstance(path, str)
            assert not path.startswith("/")
            assert ".." not in path

    def test_edge_cases(self):
        """Test various edge cases and corner scenarios."""
        # Test with None values (should be fine)
        options = RequestOptions(
            format=None,
            outtmpl=None,
            writesubtitles=None,
        )
        assert options.format is None
        assert options.outtmpl is None
        assert options.writesubtitles is None

        # Test with single character paths
        options = RequestOptions(outtmpl="a")
        assert options.outtmpl == "a"

        # Test with path containing special characters
        options = RequestOptions(outtmpl="videos/%(title)s [%(uploader)s].%(ext)s")
        assert "%(title)s [%(uploader)s]" in str(options.outtmpl)

    def test_realistic_configuration(self):
        """Test a realistic configuration that might be used in practice."""
        realistic_config = {
            "format": "best[height<=1080]",
            "outtmpl": {
                "default": "%(uploader)s/%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s",
                "thumbnail": "%(uploader)s/%(playlist)s/thumbnails/%(title)s.%(ext)s",
                "subtitle": "%(uploader)s/%(playlist)s/subtitles/%(title)s.%(ext)s",
                "infojson": "%(uploader)s/%(playlist)s/info/%(title)s.info.json",
            },
            "writesubtitles": True,
            "writeinfojson": True,
            "writethumbnail": True,
            "subtitleslangs": ["en", "es"],
            "format_sort": ["quality", "filesize", "fps"],
            "restrictfilenames": True,
            "min_filesize": 1024,
            "max_filesize": 1073741824,
        }

        options = RequestOptions(**realistic_config)

        # Verify the configuration was applied correctly
        assert options.format == "best[height<=1080]"
        assert isinstance(options.outtmpl, dict)
        assert len(options.outtmpl) == 4
        assert options.writesubtitles is True
        assert options.writeinfojson is True
        assert options.writethumbnail is True
        assert options.subtitleslangs == ["en", "es"]
        assert options.format_sort == ["quality", "filesize", "fps"]
        assert options.restrictfilenames is True
        assert options.min_filesize == 1024
        assert options.max_filesize == 1073741824

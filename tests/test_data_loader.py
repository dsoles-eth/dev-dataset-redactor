import pytest
from unittest.mock import patch, MagicMock, mock_open
import data_loader
import os
import io

@pytest.fixture
def mock_filesystem(monkeypatch):
    """
    Mocks os and open functions to simulate file system without writes.
    """
    # Mock os.path.exists
    def mock_exists(path):
        return path in ['./data/sample.json', './data/empty.json', './data/subdir/test.txt']

    # Mock os.listdir
    def mock_listdir(path):
        if path == './data':
            return ['sample.json', 'empty.json', 'subdir']
        elif path == './data/subdir':
            return ['test.txt']
        else:
            return []

    # Mock os.path.join
    def mock_join(path1, path2):
        return path1 + '/' + path2

    monkeypatch.setattr(os.path, 'exists', mock_exists)
    monkeypatch.setattr(os.path, 'listdir', mock_listdir)
    monkeypatch.setattr(os.path, 'join', mock_join)
    
    # Mock file content for open
    def mock_open_file(path, *args, **kwargs):
        if 'sample.json' in path:
            return mock_open(read_data='{"id": 123, "name": "Test"}')()
        elif 'empty.json' in path:
            return mock_open(read_data='{"status": "ok"}')()
        elif 'test.txt' in path:
            return mock_open(read_data='Sample Log Content')()
        raise FileNotFoundError(f"File not found: {path}")

    monkeypatch.setattr('builtins.open', mock_open_file)


@pytest.fixture
def mock_api_client(monkeypatch):
    """
    Mocks the external API client used by the module.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"valid": True}
    
    mock_timeout = MagicMock()
    mock_timeout.side_effect = Exception("Network Timeout")
    
    with patch('data_loader.requests') as mock_requests:
        # Setup default behavior
        mock_requests.get.return_value = mock_response
        yield mock_requests, mock_timeout


class TestLoadData:
    """
    Tests for the main data loading functionality.
    """
    def test_load_files_recursively_happy_path(self, mock_filesystem):
        """
        Verify that files are discovered recursively in a mock directory structure.
        """
        paths = data_loader.get_file_paths('./data', extensions=['.json', '.txt'])
        assert len(paths) == 3
        assert './data/sample.json' in paths
        assert './data/subdir/test.txt' in paths

    def test_load_files_filters_extensions(self, mock_filesystem):
        """
        Verify that only files with specific extensions are returned.
        """
        paths = data_loader.get_file_paths('./data', extensions=['.json'])
        assert len(paths) == 2
        assert './data/sample.json' in paths
        assert './data/subdir/test.txt' not in paths

    def test_load_files_handling_empty_directory(self, mock_filesystem):
        """
        Verify behavior when directory exists but contains no matching files.
        """
        def mock_listdir_empty(path):
            if path == './data/empty_dir':
                return []
            return []
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr('data_loader.os.path.listdir', mock_listdir_empty)
        
        try:
            paths = data_loader.get_file_paths('./data/empty_dir', extensions=['.json'])
            assert paths == []
        finally:
            monkeypatch.undo()

class TestFileReader:
    """
    Tests for individual file reading and parsing.
    """
    def test_read_file_success_json(self, mock_filesystem):
        """
        Test successful reading and parsing of a JSON file.
        """
        content = data_loader.read_file_content('./data/sample.json')
        assert content['id'] == 123
        assert content['name'] == 'Test'

    def test_read_file_success_txt(self, mock_filesystem):
        """
        Test successful reading of a text file.
        """
        content = data_loader.read_file_content('./data/subdir/test.txt')
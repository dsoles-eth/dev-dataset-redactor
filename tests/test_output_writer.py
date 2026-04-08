import pytest
from unittest import mock
import sys
import json
import output_writer


@pytest.fixture
def sample_data():
    return {"name": "John Doe", "ssn": "***-**-1234", "email": "john@example.com"}


@pytest.fixture
def mock_file_path(tmp_path):
    return str(tmp_path / "output.json")


@pytest.fixture
def mock_stdout():
    return mock.patch("sys.stdout", new_callable=mock.mock_open())


@pytest.fixture
def mock_open():
    return mock
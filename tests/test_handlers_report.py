import pytest

from handlers_report import (
    CollectorData,
    LogMerger,
    LogParser,
    LogValidator,
    Report,
    ReportPrinter,
)
from main import ConfigFabric, validate_files


@pytest.fixture
def log_parser():
    pattern = (
        r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}\s+"
        r"(\w+)\s+django\.request:\s+"
        r"(?:.*?(?:GET|POST|PUT|DELETE|PATCH)\s+(\S+)|.*?:\s+(\S+))"
    )
    return LogParser(pattern)


@pytest.fixture
def report_config():
    return {
        "validator": LogValidator("django.request"),
        "parser": LogParser(
            r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}\s+"
            r"(\w+)\s+django\.request:\s+"
            r"(?:.*?(?:GET|POST|PUT|DELETE|PATCH)\s+(\S+)|.*?:\s+(\S+))",
        ),
        "collector": CollectorData(),
        "printer": ReportPrinter(),
    }


def test_log_validator_valid():
    validator = LogValidator("django.request")
    valid_line = "2023-01-01 12:00:00,000 INFO django.request: GET /api"
    assert validator.is_valid(valid_line) is True


def test_log_validator_invalid():
    validator = LogValidator("django.request")
    invalid_line = "2023-01-01 12:00:00,000 INFO another.module: Some message"
    assert validator.is_valid(invalid_line) is False


def test_parser_valid_request(log_parser):
    line = "2023-01-01 12:00:00,000 INFO django.request: GET /api/users"
    assert log_parser.parse(line) == ("/api/users", "INFO")


def test_parser_valid_error(log_parser):
    line = "2025-03-26 12:49:53,000 ERROR django.request: Internal Server Error: /api/login [192.168.1.64] - "
    assert log_parser.parse(line) == ("/api/login", "ERROR")


def test_parser_invalid_line(log_parser):
    line = "Invalid log line without required pattern"
    assert log_parser.parse(line) is None


def test_collector_data():
    collector = CollectorData()
    collector.add("/api", "INFO")
    collector.add("/api", "INFO")
    collector.add("/login", "ERROR")

    assert collector.data == {"/api": {"INFO": 2}, "/login": {"ERROR": 1}}
    assert collector.count == 3


def test_log_merger():
    data1 = {"/api": {"INFO": 2}, "/login": {"ERROR": 1}}
    data2 = {"/api": {"INFO": 3}, "/users": {"DEBUG": 2}}

    merged, total = LogMerger.merge([data1, data2])
    assert merged == {
        "/api": {"INFO": 5},
        "/login": {"ERROR": 1},
        "/users": {"DEBUG": 2},
    }
    assert total == 8


def test_report_printer(capsys):
    data = {"/api": {"INFO": 5, "ERROR": 2}, "/login": {"DEBUG": 3}}
    printer = ReportPrinter(column_step=5)
    printer.print_report(data, total_requests=10)

    captured = capsys.readouterr()
    assert "Total requests: 10" in captured.out
    assert "HANDLER" in captured.out
    assert "INFO" in captured.out
    assert "5" in captured.out


def test_report_processing(report_config):
    report = Report(report_config)
    lines = [
        "2023-01-01 12:00:00,000 INFO django.request: GET /api",
        "2023-01-01 12:00:01,000 ERROR django.request: POST /login",
        "Invalid line without pattern",
    ]

    for line in lines:
        report.process_line(line)

    assert report.collector.data == {
        "/api": {"INFO": 1},
        "/login": {"ERROR": 1},
    }
    assert report.collector.count == 2


def test_config_fabric():
    config = ConfigFabric.get("handlers")
    assert "validator" in config
    assert "parser" in config
    assert "collector" in config
    assert "printer" in config


def test_validate_files_valid(tmp_path):
    valid_file = tmp_path / "valid.log"
    valid_file.touch()
    validate_files([str(valid_file)])


def test_validate_files_invalid():
    with pytest.raises(FileNotFoundError):
        validate_files(["nonexistent.log"])


__all__ = ()

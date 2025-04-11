import argparse
from functools import partial
import multiprocessing
import pathlib

from handlers_report import (
    CollectorData,
    LogMerger,
    LogParser,
    LogValidator,
    Report,
    ReportPrinter,
)


class ConfigFabric:
    @staticmethod
    def get(report_name: str) -> dict:
        config_report = {
            "handlers": {
                "validator": LogValidator("django.request"),
                "parser": LogParser(
                    r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}\s+"
                    r"(\w+)\s+django\.request:\s+"
                    r"(?:.*?(?:GET|POST|PUT|DELETE|PATCH)\s+(\S+)|.*?:\s+(\S+))",
                ),
                "collector": CollectorData(),
                "printer": ReportPrinter(),
            },
        }
        return config_report[report_name]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Analyze Django application logs and generate reports.",
    )
    parser.add_argument("files", nargs="+", help="Paths to log files")
    parser.add_argument(
        "--report",
        required=True,
        choices=["handlers"],
        help="Type of report to generate",
    )
    return parser.parse_args()


def validate_files(files):
    for file in files:
        if not pathlib.Path(file).exists():
            raise FileNotFoundError(f"File not found: {file}")


def process_single_file(file_path: str, config: str) -> dict:
    config = ConfigFabric.get(config)
    report = Report(config)

    with pathlib.Path(file_path).open("r", encoding="utf-8") as f:
        for line in f:
            report.process_line(line)
    return report.collector.data


def main():
    args = parse_args()
    validate_files(args.files)

    with multiprocessing.Pool() as pool:
        process_func = partial(process_single_file, config=args.report)
        results = pool.map(process_func, args.files)

    merger = LogMerger()
    merged_data, total = merger.merge(results)

    ReportPrinter().print_report(merged_data, total)


if __name__ == "__main__":
    main()


__all__ = ()

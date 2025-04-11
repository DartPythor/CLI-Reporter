import re


class LogValidator:
    def __init__(self, key: str):
        self.key = key

    def is_valid(self, line: str) -> bool:
        return self.key in line


class LogParser:
    def __init__(self, pattern_extract: str):
        self.pattern_extract = pattern_extract
        self.re_pattern = re.compile(pattern_extract)

    def parse(self, line: str) -> tuple[str, str] | None:
        match = self.re_pattern.match(line)
        if not match:
            return None
        level = match.group(1)
        endpoint = match.group(2) or match.group(3)
        return endpoint, level


class CollectorData:
    def __init__(self):
        self.data = {}
        self.count = 0

    def add(self, key: str, value: str):
        if key not in self.data:
            self.data[key] = {}
        if value not in self.data[key]:
            self.data[key][value] = 0
        self.data[key][value] += 1
        self.count += 1


class LogMerger:
    @staticmethod
    def merge(reports_data: list[dict]) -> dict:
        merged = {}
        count_element = 0

        for data in reports_data:
            for key, subkeys in data.items():
                if key not in merged:
                    merged[key] = {}

                for sum_key, sum_subkey in subkeys.items():
                    merged[key][sum_key] = merged[key].get(sum_key, 0) + sum_subkey
                    count_element += sum_subkey

        return merged, count_element


class ReportPrinter:
    def __init__(self, column_step: int = 5):
        self.column_step = column_step

    def print_report(self, data: dict, total_requests: int = None):
        level_names = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        size_back = (
            max(len(handler) for handler in data.keys()) + self.column_step
        )
        header = ["HANDLER"] + level_names
        print(f"Total requests: {total_requests}")
        print(" ".join(f"{col:<{size_back}}" for col in header))
        print("-" * (size_back * len(header)))

        for handler, levels in data.items():
            row = [handler]
            for level in level_names:
                row.append(str(levels.get(level, 0)))
            print(" ".join(f"{item:<{size_back}}" for item in row))


class Report:
    def __init__(self, config: dict):
        self.data = {}
        self.validator: LogValidator = config["validator"]
        self.parser: LogParser = config["parser"]
        self.collector: CollectorData = config["collector"]
        self.printer: ReportPrinter = config["printer"]

    def process_line(self, line: str) -> None:
        if not self.validator.is_valid(line):
            return
        data = self.parser.parse(line)
        self.collector.add(*data)

    def print_report(self) -> None:
        self.printer.print_report(self.collector.data, self.collector.count)


__all__ = ()

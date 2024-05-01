"""Functionality for working with short rates."""

import ftplib
import html
import tempfile

from deephaven import read_csv
from deephaven.table import Table


class IBFtpWriter:
    """Writer for downloading text pipe-separated-value files from the IB FTP site.

    Closing the writer causes the temporary file containing the data to be deleted.
    """

    header: str
    source: str
    file: tempfile.NamedTemporaryFile

    def __init__(self):
        self.header = None
        self.source = None
        self.file = tempfile.NamedTemporaryFile(mode="w", suffix=".psv")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def file_name(self) -> str:
        """Name of the temporary file."""
        return self.file.name

    def flush(self) -> None:
        """Flush writes to the temporary file."""
        self.file.flush()

    def close(self) -> None:
        """Close the temporary file.  This makes the temporary file unavailable."""
        self.file.close()

    def write(self, line: str) -> None:
        """Write a line to the temporary file."""

        if line.startswith("#BOF") or line.startswith("#EOF"):
            return

        line = html.unescape(line)

        # REMOVE TRAILING "|" that breaks CSV parser
        # https://github.com/deephaven/deephaven-core/issues/1800
        if line.endswith("|"):
            line = line[:-1]

        if line.startswith("#"):
            line = f"Source|{line[1:]}"

            if self.header is None:
                self.header = line
                self.file.write(f"{line}\n")
            elif self.header != line:
                raise Exception(f"Mismatched headers: {self.header} {line}")
            else:
                return
        else:
            self.file.write(f"{self.source}|{line}\n")


def load_short_rates() -> Table:
    """Downloads the short rates from the IB FTP site and returns them as a table."""

    # See: https://www.ibkrguides.com/kb/article-2024.htm
    host: str = "ftp2.interactivebrokers.com"
    user: str = "shortstock"

    with ftplib.FTP(host=host, user=user) as ftp, IBFtpWriter() as p:
        try:
            files = ftp.nlst("*.txt")

            for file in files:
                p.source = file[:-4]
                res = ftp.retrlines(f'RETR {file}', p.write)

                if not res.startswith('226 Transfer complete'):
                    raise Exception(f"FTP download failed: {user}@{host} {file} {res}")

        except ftplib.all_errors as e:
            print('FTP error:', e)

        p.flush()

        return read_csv(p.file_name(), delimiter="|") \
            .rename_columns([
                "Sym=SYM",
                "Currency=CUR",
                "Name=NAME",
                "Contract=CON",
                "RebateRate=REBATERATE",
                "FeeRate=FEERATE",
                "Available=AVAILABLE"])

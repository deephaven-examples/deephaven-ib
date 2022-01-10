"""Functionality for working with error codes."""

from typing import Dict, Tuple

import pandas as pd


def load_error_codes() -> Tuple[Dict[int, str], Dict[int, str]]:
    """Load dictionaries of error code messages and notes."""

    html_tables = pd.read_html('https://interactivebrokers.github.io/tws-api/message_codes.html')

    error_messages = {}
    error_notes = {}

    for df in html_tables:
        try:
            codes = df['Code']
            messages = df['TWS message']
            notes = df['Additional notes']

            for code, message in zip(codes, messages):
                error_messages[code] = message

            for code, note in zip(codes, notes):
                error_notes[code] = note
        except KeyError:
            pass

    return error_messages, error_notes

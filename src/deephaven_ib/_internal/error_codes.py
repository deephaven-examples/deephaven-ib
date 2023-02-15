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
            df = df.fillna('')
            codes = df['Code']
            messages = df['TWS message']
            notes = df['Additional notes']

            for code, message in zip(codes, messages):
                error_messages[code] = message

            for code, note in zip(codes, notes):
                error_notes[code] = note
        except KeyError:
            pass

    overrides = {
        0: "Warning: Approaching max rate of 50 messages per second",
        504: "Not connected",
        502: "Couldn't connect to TWS. Confirm that 'Enable ActiveX and Socket EClients' is enabled and connection port is the same as 'Socket Port' on the TWS 'Edit->Global Configuration...->API->Settings' menu. Live Trading ports: TWS: 7496; IB Gateway: 4001. Simulated Trading ports for new installations of version 954.1 or newer:  TWS: 7497; IB Gateway: 4002",
        2113: "The order size for Bonds (Bills) is entered as a nominal par value of the order, and must be a multiple",
        2157: "Sec-def data farm connection is broken:secdefil",
        10089: "Requested market data requires additional subscription for API.See link in 'Market Data Connections' dialog for more details.",
        10147: "OrderId that needs to be cancelled is not found.",
        10168: "Requested market data is not subscribed.Delayed market data is not enabled.",
        10172: "Failed to request news article: No data available",
        10187: "Failed to request historical ticks",
        10189: "Failed to request tick-by-tick data",
        10190: "Maxnumber of tick-by-tick requests has been reached.",
        10311: "This order will be directly routed to NYSE. Direct routed orders may result in higher trade fees. Restriction is specified in Precautionary Settings of Global Configuration/API.",
    }

    for k, v in overrides.items():
        if k not in error_messages:
            error_messages[k] = v
            error_notes[k] = ""

    return error_messages, error_notes

# pip install lxml

import pandas as pd

html_tables = pd.read_html('https://interactivebrokers.github.io/tws-api/message_codes.html')

error_codes = {}

for df in html_tables:
    print(df)
    try:
        codes = df['Code']
        messages = df['TWS message']
        print(codes)
        print(messages)

        for code, message in zip(codes, messages):
            error_codes[code] = message
    except KeyError:
        pass

print("-------")
print(error_codes)

import dateutil.parser
import pandas as pd
import arrow
import pendulum
import dateparser
import datetime
from pprint import pformat as pf

def parse_date(date_string):
    parsers = [
        {'name': 'dateutil',   'fn': dateutil.parser.parse, 'dt': lambda x: x},
        {'name': 'pandas',     'fn': pd.to_datetime,        'dt': lambda x: x.to_pydatetime()},
        {'name': 'arrow',      'fn': arrow.get,             'dt': lambda x: x.datetime.replace(tzinfo=None)},
        {'name': 'pendulum',   'fn': pendulum.parse,        'dt': lambda x: datetime.datetime.fromtimestamp(x.timestamp())},
        {'name': 'dateparser', 'fn': dateparser.parse,      'dt': lambda x: x}
    ]
    
    detail = {'error': {}, 'success': {}}
    
    for p in parsers:
        try:
            parsed_date = p['fn'](date_string)  # Use parser
            parsed_date = p['dt'](parsed_date)  # Standardize into datetime.datetime
            parsed_date = parsed_date.replace(microsecond=0)  # Remove microseconds
            if parsed_date is None:
                raise Exception
            detail['success'][p['name']] = parsed_date
        except Exception as e:
            detail['error'][p['name']] = f"failed:\n{str(e)}"
    
    parsed_dates = list(detail['success'].values())
    
    if len(detail['success']) == 0:
        consensus = None
        text = ''.join([
            f"Your input:\n> {date_string}\n...is so incoherent",
            f" that among {len(parsers)} parsers, none of them could make",
            f" any sense of your rambling.\nTry again with a valid date!\n",
            pf(detail),
        ])
    elif all(date == parsed_dates[0] for date in parsed_dates):
        consensus = True
        text = None
    else:
        consensus = False
        readable = { k: v.strftime('%Y-%m-%d %H:%M:%S') for k, v in detail['success'].items() }
        text = f"The parsers disagree on the parsed date:\n```\n{str(readable)}\n```\nTry something less ambiguous."
        
    return consensus, detail, text

import pickle
import json

import pandas as pd
from pathlib import Path
pd.set_option('max_colwidth',300)
from pprint import pprint



columns_long_list = ['repo', 'path', 'url', 'code',
                        'code_tokens', 'docstring', 'docstring_tokens',
                        'language', 'partition']

columns_short_list = ['code_tokens', 'docstring_tokens',
                        'language', 'partition']


def jsonl_list_to_dataframe(file_list, columns=columns_long_list):
    return pd.concat([pd.read_json(f,
                                orient='records',
                                compression='gzip',
                                lines=True)[columns]
                    for f in file_list], sort=False)


if __name__ == "__main__":
    print("loading data... \n")
    python_files = sorted(Path('./data/python/').glob('**/*.gz'))
    pydf = jsonl_list_to_dataframe(python_files)
    arr = pydf["code"].to_numpy()
    print(arr[:4])

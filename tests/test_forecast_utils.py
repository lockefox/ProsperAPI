from os import path
from datetime import datetime
import pandas as pd
import requests

import pytest

import publicAPI.forecast_utils as forecast_utils
import helpers

HERE = path.abspath(path.dirname(__file__))
ROOT = path.dirname(HERE)

CONFIG_FILENAME = path.join(HERE, 'test_config.cfg')

CONFIG = helpers.get_config(CONFIG_FILENAME)

def test_fetch_emd_history(config=CONFIG):
    """happypath test for `fetch_market_history_emd`"""
    data = forecast_utils.fetch_market_history_emd(
        region_id=config.get('TEST', 'region_id'),
        type_id=config.get('TEST', 'type_id'),
        data_range=config.get('TEST', 'history_count'),
        config=config
    )

    ## validate contents ##
    assert data['version'] == 2
    data_keys = data['columns'].split(',')
    for entry in data['result']:
        assert set(data_keys) == set(entry['row'].keys())

    ## validate count ##
    db_data = helpers.check_db_values(
        region_id=config.get('TEST', 'region_id'),
        type_id=config.get('TEST', 'type_id'),
        data_range=config.get('TEST', 'history_count'),
        config=config
    )
    if db_data:
        mismatch_dates = helpers.compare_dates(
            data['result'],
            db_data
        )
        assert len(mismatch_dates) <= int(config.get('TEST', 'miss_budget'))
    else:
        pytest.xfail(
            'Unable to validate date counts: {0}/{1}'.format(
                len(data['result']),
                config.get('TEST', 'history_count')
        ))

def test_fetch_emd_history_fail(config=CONFIG):
    """happypath test for `fetch_market_history_emd`"""
    with pytest.raises(requests.exceptions.HTTPError):
        data = forecast_utils.fetch_market_history_emd(
            region_id=config.get('TEST', 'region_id'),
            type_id=config.get('TEST', 'type_id'),
            data_range=config.get('TEST', 'history_count'),
            config=config,
            endpoint_addr='http://www.eveprosper.com/noendpoint'
        )

    with pytest.raises(forecast_utils.NoDataReturned):
        data = forecast_utils.fetch_market_history_emd(
            region_id=config.get('TEST', 'region_id'),
            type_id=config.get('TEST', 'bad_typeid'),
            data_range=config.get('TEST', 'history_count'),
            config=config
        )
DEMO_DATA = {
    'version': 2,
    'currentTime': datetime.now().isoformat(),
    'name':'history',
    'key': 'typeID,regionID,date',
    'columns': 'typeID,regionID,date,lowPrice,highPrice,avgPrice,volume,orders',
    'result':[
        {"row": {
            "typeID": "38",
            "regionID": "10000002",
            "date": "2015-03-28",
            "lowPrice": "674.02",
            "highPrice": "682.65",
            "avgPrice": "681.99",
            "volume": "43401081",
            "orders": "1808"
        }},
        {"row": {
            "typeID": "38",
            "regionID": "10000002",
            "date": "2015-03-29",
            "lowPrice": "677.29",
            "highPrice": "681.95",
            "avgPrice": "681.89",
            "volume": "46045538",
            "orders": "1770"
        }},
        {"row": {
            "typeID": "38",
            "regionID": "10000002",
            "date": "2015-03-30",
            "lowPrice": "678.93",
            "highPrice": "684",
            "avgPrice": "679.14",
            "volume": "56083217",
            "orders": "1472"
        }}
    ]
}
def test_parse_emd_data():
    """happypath test for refactoring EMD data"""

    cleandata = forecast_utils.parse_emd_data(DEMO_DATA['result'])

    assert isinstance(cleandata, pd.DataFrame)  #check output type

    headers = list(cleandata.columns.values)
    expected_rows = DEMO_DATA['columns'].split(',')

    assert set(headers) == set(expected_rows)   #check row headers

    assert len(cleandata.index) == len(DEMO_DATA['result'])

def test_parse_emd_data_fail():
    """make sure behavior is expected for failure"""
    with pytest.raises(TypeError):
        data = forecast_utils.parse_emd_data(DEMO_DATA)

TEST_DATA_PATH = path.join(HERE, 'sample_emd_data.csv')
def test_build_forecast(config=CONFIG):
    """try to build a forecast"""
    test_data = pd.read_csv(TEST_DATA_PATH)

    expected_rows = [
        'date',
        'avgPrice',
        'yhat',
        'yhat_low',
        'yhat_high',
        'prediction'
    ]
    predict_data = forecast_utils.build_forecast(
        test_data,
        int(config.get('TEST', 'forecast_range'))
    )

    headers = list(predict_data.columns.values)
    assert set(expected_rows) == set(headers)



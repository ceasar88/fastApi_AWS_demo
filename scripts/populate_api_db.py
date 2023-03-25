"""Script to populate api table_dev with JSON data"""
import argparse
import json
import logging
import glob
import os
from typing import Dict
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


dynamodb = boto3.resource("dynamodb", "us-west-1")

msg = "Populating the api table with JSON prompts data..."
parser = argparse.ArgumentParser(description=msg)
args = parser.parse_args()
api_table_name: str = (
        "cdk-solution-ApiDBApiTable9B6DE511-4CSR3FGGI5VI"
    )

table = dynamodb.Table(api_table_name)


def parse_raw_data(item: Dict, api_key: str) -> Dict:
    """clean raw data before saving to table"""
    configuration_parameters = {}
    rows = item["rows"][1:]
    for parameter in rows:
        configuration_parameters[parameter[0]] = parameter[1]
    table_item = {"id": "action",
                  "sk": item["ts"],
                  "name": item["name"],
                  "event_time": item["ts"],
                  "user_id": api_key,
                  "data": configuration_parameters}

    return json.loads(json.dumps(table_item), parse_float=Decimal)


def add_new_item(new_item):
    """Add an item to api table_dev"""
    table_item = parse_raw_data(new_item, "master_key")
    try:
        response = table.put_item(Item=table_item)
        print(f"Added new record to api table: {table_item}")
    except ClientError as e:
        logger.info("ERROR when adding new item to api table")
        logger.error(e.response["Error"]["Message"])
    else:
        return response


def get_json():
    """Get json weather data from json files"""
    path = '/home/satori/Desktop/source.ag/cdk_solution/scripts/data/may/14'
    print(path)
    try:
        items = []

        for filename in glob.glob(os.path.join(path, '*.json')):
            # print("got here")
            with open(filename, encoding='utf-8', mode='r') as json_file:
                items.append(json.loads(json_file.read()))
    except ClientError as e:
        logger.info("ERROR when fetching json data from file")
        logger.error(e.response["Error"]["Message"])
    else:
        return items


if __name__ == "__main__":

    items = get_json()
    for item in items:
        add_new_item(item)

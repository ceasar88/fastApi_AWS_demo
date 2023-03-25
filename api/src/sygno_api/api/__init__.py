"""Functions and classes to support the API"""
import json
import pandas as pd
from decimal import Decimal
from datetime import datetime, timedelta
from dateutil import parser
from typing import List, Dict
from statistics import mean

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from fastapi.logger import logger
from pydantic import BaseSettings

from sygno_api.api.schema import (
    WriteResponse,
    ExposeResponse,
    ExposeRequest,
    WriteRequest,
    ApiRecord,
    FraudItem,
)
from sygno_api.utils import dbmethods as dbutils

today = "2021-05-14"
now = "2021-05-14T10:34:21+02:00"
num_of_parameters = 21


def parse_raw_data(item: Dict, api_key: str) -> Dict:
    """clean raw data before saving to table"""

    fraud_parameters = {}
    rows = item.data["rows"][1:]
    for parameter in rows:
        fraud_parameters[parameter[0]] = parameter[1]
    table_item = ApiRecord(id="action",
                           sk=item.data["ts"],
                           name=item.data["name"],
                           event_time=item.data["ts"],
                           user_id=api_key,
                           data=fraud_parameters)

    return json.loads(json.dumps(table_item.dict()), parse_float=Decimal)


def parse_raw_into_fraud_schema(item: Dict) -> FraudItem:
    """ clean raw data to return a fraud dict"""
    fraud_item = FraudItem(name=item["name"], timestamp=item["event_time"], fraud_data=item["data"])
    logger.info(f"parsed item: {fraud_item}")
    return fraud_item


def get_15min_increments(items: List) -> Dict:
    """ cleans list of fraud items into 15min increments"""
    count = 0
    results = {}
    for item in items:
        if (count == 0) or (count % 3 == 0):
            results[item["event_time"]] = parse_raw_into_fraud_schema(item)
            count = count + 1
        else:
            count = count + 1
            continue
    return results


def get_averages(items: List) -> Dict:
    """ cleans list of fraud items into averages"""
    results = {}
    dict_parameters = ["wind_direction_compass", "status_meteo_station", "status_meteo_station_communication"]
    fraud_parameter_list = [[] for i in range(num_of_parameters)]
    df = pd.DataFrame(columns=list(items[0]["data"].keys()))

    for item in items:
        for i in range(len(item["data"])):
            if list(item["data"].keys())[i] in dict_parameters:
                fraud_parameter_list[i].append(list(item["data"].values())[i]["key"])
            else:
                fraud_parameter_list[i].append(list(item["data"].values())[i])

    for column in df:
        df[column] = fraud_parameter_list[df.columns.get_loc(column)]

    # Iterate over columns using DataFrame.iteritems()
    for (column_name, column_value) in df.iteritems():
        results[f"average_{column_name}"] = mean(column_value.values)
    return results


def get_1day_increments(items: List) -> Dict:
    """ cleans list of fraud items into 15min increments"""
    count = 0
    results = {}
    for item in items:
        if (count == 0) or (count % 3 == 0):
            results[item["event_time"]] = parse_raw_into_fraud_schema(item)
            count = count + 1
        else:
            count = count + 1
            continue
    return results


class sygnoAPI:
    """Class containing methods for servicing API endpoints"""

    def __init__(self, settings: BaseSettings):
        """Initialize sygno API object"""
        self.api_table_name = settings.api_table_name
        self.api_table = dbutils.get_db_table(self.api_table_name)

        logger.info(f"API Table Name: {self.api_table_name}\n")
        logger.info(f"API Table: {self.api_table}\n")
        logger.info(f"sygno API package initialized!")

    def get_latest(self):
        """ method to query table and get the latest fraud data"""
        try:
            response = self.api_table.query(
                KeyConditionExpression=Key("id").eq("weather") & Key("sk").begins_with(today),
                ScanIndexForward=False,
                Limit=1
            )
            logger.info(f"got {response} for the latest fraud data")

        except ClientError as e:
            logger.info(e.response["Error"]["Message"])
            return None

        else:
            return ExposeResponse(status=200, description="latest fraud data",
                                  data={"latest": parse_raw_into_fraud_schema(response["Items"][0])})

    def get_24h_devt(self):
        """ Expose the development of the fraud parameters over the last 24h in 15 min increments"""
        try:
            low = str((parser.parse(now) - timedelta(days=1)).isoformat())
            response = self.api_table.query(
                KeyConditionExpression=Key("id").eq("weather") & Key("sk").between(low, now),
                ScanIndexForward=False,
            )
            logger.info(f"got {response} for 24h fraud data")
        except ClientError as e:
            logger.info(e.response["Error"]["Message"])
            return None

        else:
            return ExposeResponse(status=200, description="last 24h fraud data in 15 min increments",
                                  data=get_15min_increments(response["Items"]))

    def get_24h_average(self):
        """" Expose the average for each of the fraud parameters for the last 24h"""
        try:
            low = str((parser.parse(now) - timedelta(days=1)).isoformat())
            response = self.api_table.query(
                KeyConditionExpression=Key("id").eq("weather") & Key("sk").between(low, now),
                ScanIndexForward=False,
            )
            logger.info(f"got {response} for the latest fraud data")
        except ClientError as e:
            logger.info(e.response["Error"]["Message"])
            return None
        else:
            return ExposeResponse(status=200, description="last 24h fraud data averages",
                                  data={"24h averages": FraudItem(name="24h averages",
                                                                    timestamp=f"from {low} to {now}",
                                                                    fraud_data=get_averages(response["Items"]))})

    def get_7d_devt(self):
        """ Expose the development of the fraud parameters over the last 7 days in 1 day increments
        (average per day) """
        try:
            result = {}
            high = "2021-05-14T10:34:21+02:00"
            low = str((parser.parse(high) - timedelta(days=1)).isoformat())
            for i in range(7):
                response = self.api_table.query(
                    KeyConditionExpression=Key("id").eq("weather") & Key("sk").between(low, high),
                    ScanIndexForward=False,
                )
                logger.info(f"got {response} for the 1 day fraud data")
                result[f"day_{i+1}"] = FraudItem(name="24h averages", timestamp=f"from {low} to {high}",
                                                   fraud_data=get_averages(response["Items"]))
                high = low
                low = str((parser.parse(high) - timedelta(days=1)).isoformat())

        except ClientError as e:
            logger.info(e.response["Error"]["Message"])
            return None
        else:
            return ExposeResponse(status=200, description="last 7 days fraud data in 1 day increments",
                                  data=result)

    def get_7d_average(self):
        """ Expose the average of the fraud parameters over the last 7 days """
        try:
            low = str((parser.parse(now) - timedelta(days=7)).isoformat())
            response = self.api_table.query(
                KeyConditionExpression=Key("id").eq("weather") & Key("sk").between(low, now),
                ScanIndexForward=False,
            )
            logger.info(f"got {response} for the 7d fraud data")
        except ClientError as e:
            logger.info(e.response["Error"]["Message"])
            return None
        else:
            return ExposeResponse(status=200, description="average 7 days fraud data",
                                  data={"7 day Averages": FraudItem(name="7 day Averages",
                                                                      timestamp=f"from {low} to {now}",
                                                                      fraud_data=get_averages(response["Items"]))})

    def get_data(self, item):
        """ check type and call appropriate get method"""
        if item.type == "latest":
            return self.get_latest()
        elif item.type == "24h_devt":
            return self.get_24h_devt()
        elif item.type == "24h_average":
            return self.get_24h_average()
        elif item.type == "7d_devt":
            return self.get_7d_devt()
        elif item.type == "7d_average":
            return self.get_7d_average()
        return None

    def save_raw_data(self, item: Dict, api_key: str) -> WriteResponse:
        """ get and save a new fraud item"""
        table_item = parse_raw_data(item, api_key)
        try:
            response = self.api_table.put_item(Item=table_item)
            logger.info(f"Added new record to api table: {table_item} with {response}")
        except ClientError as e:
            logger.info("ERROR when adding new item to Api table")
            logger.info(e.response["Error"]["Message"])
            return WriteResponse(status="500", description=f"Failed to add raw data to database",  data=table_item)
        else:
            return WriteResponse(status="200", description=f"Successfully added raw data to database",  data=table_item)


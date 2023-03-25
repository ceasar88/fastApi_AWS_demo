"""Event logging for the API service"""
import logging
from datetime import datetime, timezone
from botocore.exceptions import ClientError
from pydantic import BaseSettings
from sygno_api.api.schema import ApiRecord
from sygno_api.utils import dbmethods as dbutils

logger = logging.getLogger(__name__)


def add_to_events_table(new_item, event_table):
    """Add a new event to the events table"""

    try:
        response = event_table.put_item(Item=new_item)
        logger.info("new event added to table!", new_item)
        return response

    except ClientError as e:
        logger.error(e.response["Error"]["Message"])
        return None


class EventLogger:
    """
    Event logger that takes an api service request or response
    and populates the event table with a new item
    """

    def __init__(self, settings: BaseSettings):
        """Initialize logger"""

        logger.info(
            f"Initializing Api Service event logger with, "
            f"event table name: {settings.events_table_name}, app version: {settings.app_version}"
        )
        self.events_table_name = settings.events_table_name
        self.events_table = dbutils.get_db_table(self.events_table_name)
        self.app_version = settings.app_version

    def log(self, api_key, name, event_data={}):
        """Log event to the event table"""

        current_time_zone = datetime.now(timezone.utc)
        # id = nanoid.generate()
        # create event item
        event = ApiRecord(id="event",
                          sk=f"{current_time_zone}",
                          name=name,
                          event_time=f"{current_time_zone}",
                          user_id=api_key,
                          data=event_data)

        # add to events table
        item = event.dict(by_alias=True)
        logger.info(f"Logging new event to Api events table, {item}")
        add_to_events_table(item, self.events_table)

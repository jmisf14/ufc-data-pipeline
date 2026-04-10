from ufcstats_scrape.items import UpcomingEvent, UpcomingFight
from dotenv import load_dotenv

import logging
import psycopg2
import psycopg2.extras
import os


class UpcomingPipeline:
    def __init__(self):
        self.upcoming_events = []
        self.upcoming_fights = []

        load_dotenv()
        hostname = os.environ.get("POSTGRES_HOST", "Hostname not found")
        username = os.environ.get("POSTGRES_USER", "Username not found")
        password = os.environ.get("POSTGRES_PASSWORD", "Password not found")
        database = os.environ.get("POSTGRES_DB", "Database name not found")
        port = os.environ.get("POSTGRES_PORT", "Port not found")

        logging.debug("Connecting to database (upcoming pipeline)...")

        try:
            self.connection = psycopg2.connect(
                host=hostname,
                user=username,
                password=password,
                dbname=database,
                port=port,
            )
            self.cursor = self.connection.cursor()
            logging.info("Connected to database (upcoming pipeline).")
        except:
            logging.error("Could not connect to database (upcoming pipeline).")
            raise

        self.cursor.execute(
            open("ufcstats_scrape/sql/create_upcoming_events_table.sql", "r").read()
        )
        self.cursor.execute(
            open("ufcstats_scrape/sql/create_upcoming_fights_table.sql", "r").read()
        )
        self.connection.commit()

    def process_item(self, item, spider):
        if isinstance(item, UpcomingEvent):
            self.upcoming_events.append(item)
        elif isinstance(item, UpcomingFight):
            self.upcoming_fights.append(item)
        return item

    def open_spider(self, spider):
        logging.info("Upcoming events spider opened.")

    def close_spider(self, spider):
        # Clear old upcoming data and replace with fresh scrape
        logging.info("Clearing old upcoming data...")
        try:
            self.cursor.execute("DELETE FROM upcoming_fights;")
            self.cursor.execute("DELETE FROM upcoming_events;")
            self.connection.commit()
            logging.info("Cleared old upcoming data.")
        except Exception as e:
            logging.error(f"Could not clear old upcoming data: {e}")
            self.connection.rollback()
            raise

        logging.info("Inserting upcoming events into database...")
        try:
            if self.upcoming_events:
                psycopg2.extras.execute_batch(
                    self.cursor,
                    open("ufcstats_scrape/sql/upsert_upcoming_events.sql", "r").read(),
                    [
                        (
                            event.id,
                            event.name,
                            event.date,
                            event.location,
                            event.link,
                        )
                        for event in self.upcoming_events
                    ],
                )
                self.connection.commit()
                logging.info(
                    f"Inserted {len(self.upcoming_events)} upcoming events."
                )
        except Exception as e:
            logging.error(f"Could not insert upcoming events: {e}")
            self.connection.rollback()
            raise

        logging.info("Inserting upcoming fights into database...")
        try:
            if self.upcoming_fights:
                psycopg2.extras.execute_batch(
                    self.cursor,
                    open("ufcstats_scrape/sql/insert_upcoming_fights.sql", "r").read(),
                    [
                        (
                            fight.event_id,
                            fight.red_name,
                            fight.blue_name,
                            fight.red_link,
                            fight.blue_link,
                            fight.weight_class,
                        )
                        for fight in self.upcoming_fights
                    ],
                )
                self.connection.commit()
                logging.info(
                    f"Inserted {len(self.upcoming_fights)} upcoming fights."
                )
        except Exception as e:
            logging.error(f"Could not insert upcoming fights: {e}")
            self.connection.rollback()
            raise

        self.cursor.close()
        self.connection.close()

from stat_scrape.items import (
    Event,
    Fight,
    Fighter,
    FighterImage,
    ScheduledEvent,
    ScheduledFight,
)
from dotenv import load_dotenv
from datetime import date

import logging
import psycopg2
import psycopg2.extras
import os


class StatScrapePipeline:
    def __init__(self):

        self.events = []
        self.fights = []
        self.new_fighters = []
        self.existing_fighters = []
        self.fighter_images = []
        self.scheduled_events = []
        self.scheduled_fights = []

        load_dotenv()
        hostname = os.environ.get("POSTGRES_HOST", "Hostname not found")
        username = os.environ.get("POSTGRES_USER", "Username not found")
        password = os.environ.get("POSTGRES_PASSWORD", "Password not found")
        database = os.environ.get("POSTGRES_DB", "Database name not found")
        port = os.environ.get("POSTGRES_PORT", "Port not found")

        logging.debug("Connecting to database...")

        try:
            self.connection = psycopg2.connect(
                host=hostname,
                user=username,
                password=password,
                dbname=database,
                port=port,
            )
            self.cursor = self.connection.cursor()
            logging.info("Connected to database.")
        except:
            logging.error("Could not connect to database.")
            raise

        self.cursor.execute(
            open("stat_scrape/sql/create_events_table.sql", "r").read())
        self.cursor.execute(
            open("stat_scrape/sql/create_fights_table.sql", "r").read())
        self.cursor.execute(
            open("stat_scrape/sql/create_fighters_table.sql", "r").read()
        )
        # Auxiliary tables (images and scheduled bouts)
        self.cursor.execute(
            open("stat_scrape/sql/create_fighter_images_table.sql", "r").read()
        )
        self.cursor.execute(
            open("stat_scrape/sql/create_scheduled_events_table.sql", "r").read()
        )
        self.cursor.execute(
            open("stat_scrape/sql/create_scheduled_fights_table.sql", "r").read()
        )

    def process_item(self, item, spider):
        if isinstance(item, Event):
            self.events.append(item)
        elif isinstance(item, Fight):
            self.fights.append(item)
        elif isinstance(item, Fighter):
            self.cursor.execute(
                open("stat_scrape/sql/select_fighters.sql", "r").read(),
                (item.id,))
            if (
                self.cursor.fetchone()
            ):
                self.existing_fighters.append(item)

            else:
                self.new_fighters.append(item)

        elif isinstance(item, FighterImage):
            # Always upsert via ON CONFLICT in SQL
            self.fighter_images.append(item)

        elif isinstance(item, ScheduledEvent):
            self.scheduled_events.append(item)

        elif isinstance(item, ScheduledFight):
            self.scheduled_fights.append(item)

        self.connection.commit()
        return item

    def open_spider(self, spider):
        spider.last_event_date = date(1, 1, 1)
        logging.debug("Getting last event date from database...")
        self.cursor.execute("SELECT COUNT(*) from events;")
        if self.cursor.fetchone()[0] != 0:
            self.cursor.execute("SELECT MAX(date) FROM events")
            spider.last_event_date = self.cursor.fetchone()[0]
        logging.debug(f"Last event date: {spider.last_event_date}")


    def close_spider(self, spider):
        logging.debug("Inserting events into database...")
        try:
            if self.events:
                psycopg2.extras.execute_batch(
                    self.cursor,
                    open("stat_scrape/sql/insert_into_events.sql", "r").read(),
                    list([(event.id,
                           event.name,
                           event.date,
                           event.location,
                           event.link) for event in self.events]),
                )
                self.connection.commit()
                logging.debug("Inserted events into database.")
        except Exception as e:
            logging.error(f"Could not insert events into database: {e}")
            self.connection.commit()
            raise

        logging.debug("Inserting fights into database...")
        try:
            if self.fights:
                psycopg2.extras.execute_batch(
                    self.cursor,
                    open("stat_scrape/sql/insert_into_fights.sql", "r").read(),
                    list([(
                        fight.id,
                        fight.event_id,
                        fight.red_id,
                        fight.blue_id,
                        fight.winner,
                        fight.loser,
                        fight.division,
                        fight.time_format,
                        fight.ending_round,
                        fight.ending_time,
                        fight.method,
                        fight.details,
                        fight.referee,
                        fight.title_fight,
                        fight.perf_bonus,
                        fight.fotn_bonus,
                        fight.red_kd,
                        fight.blue_kd,
                        fight.red_sig_strike,
                        fight.blue_sig_strike,
                        fight.red_sig_attempt,
                        fight.blue_sig_attempt,
                        fight.red_takedown,
                        fight.blue_takedown,
                        fight.red_takedown_attempt,
                        fight.blue_takedown_attempt,
                        fight.red_sub,
                        fight.blue_sub,
                        fight.red_reversal,
                        fight.blue_reversal,
                        fight.red_control,
                        fight.blue_control,
                        fight.red_head,
                        fight.blue_head,
                        fight.red_head_attempt,
                        fight.blue_head_attempt,
                        fight.red_body,
                        fight.blue_body,
                        fight.red_body_attempt,
                        fight.blue_body_attempt,
                        fight.red_leg,
                        fight.blue_leg,
                        fight.red_leg_attempt,
                        fight.blue_leg_attempt,
                        fight.red_dist,
                        fight.blue_dist,
                        fight.red_dist_attempt,
                        fight.blue_dist_attempt,
                        fight.red_clinch,
                        fight.blue_clinch,
                        fight.red_clinch_attempt,
                        fight.blue_clinch_attempt,
                        fight.red_ground,
                        fight.blue_ground,
                        fight.red_ground_attempt,
                        fight.blue_ground_attempt,
                        fight.link,
                    ) for fight in self.fights]),
                )
                self.connection.commit()
                logging.debug("Inserted fights into database.")
        except Exception as e:
            logging.error(f"Could not insert fights into database: {e}")
            self.connection.commit()
            raise
        logging.debug("Inserting new fighters into database...")

        try:
            if self.new_fighters:
                psycopg2.extras.execute_batch(
                    self.cursor,
                    open("stat_scrape/sql/insert_into_fighters.sql", "r").read(),
                    list([(
                        fighter.id,
                        fighter.first_name,
                        fighter.last_name,
                        fighter.t_wins,
                        fighter.t_losses,
                        fighter.t_draws,
                        fighter.t_no_contests,
                        fighter.nickname,
                        fighter.ufc_wins,
                        fighter.ufc_losses,
                        fighter.ufc_draws,
                        fighter.ufc_no_contests,
                        fighter.height,
                        fighter.reach,
                        fighter.stance,
                        fighter.date_of_birth,
                        fighter.sig_strike_landed,
                        fighter.sig_strike_acc,
                        fighter.sig_strike_abs,
                        fighter.strike_def,
                        fighter.takedown_avg,
                        fighter.takedown_acc,
                        fighter.takedown_def,
                        fighter.sub_avg,
                        fighter.link,
                    ) for fighter in self.new_fighters]),
                )
                self.connection.commit()
                logging.debug("Inserted fighters into database.")
        except Exception as e:
            logging.error(f"Could not insert fighters into database: {e}")
            self.connection.commit()
            raise

        logging.debug("Updating fighters in database")
        try:
            if self.existing_fighters:
                psycopg2.extras.execute_batch(
                    self.cursor,
                    open('stat_scrape/sql/update_fighters.sql', 'r').read(),
                    list([(
                        fighter.first_name,
                        fighter.last_name,
                        fighter.t_wins,
                        fighter.t_losses,
                        fighter.t_draws,
                        fighter.t_no_contests,
                        fighter.nickname,
                        fighter.ufc_wins,
                        fighter.ufc_losses,
                        fighter.ufc_draws,
                        fighter.ufc_no_contests,
                        fighter.height,
                        fighter.reach,
                        fighter.stance,
                        fighter.sig_strike_landed,
                        fighter.sig_strike_acc,
                        fighter.sig_strike_abs,
                        fighter.strike_def,
                        fighter.takedown_avg,
                        fighter.takedown_acc,
                        fighter.takedown_def,
                        fighter.sub_avg,
                        fighter.id) for fighter in self.existing_fighters]))
                self.connection.commit()
                logging.info("Updated fighter in database.")
        except Exception as e:
            logging.error(f"Could not update fighter in database: {e}")
            self.connection.commit()
            raise

        # Upsert fighter images
        logging.debug("Upserting fighter images into database")
        try:
            if self.fighter_images:
                psycopg2.extras.execute_batch(
                    self.cursor,
                    open(
                        "stat_scrape/sql/insert_into_fighter_images.sql", "r"
                    ).read(),
                    list(
                        [
                            (
                                img.fighter_id,
                                img.image_url,
                            )
                            for img in self.fighter_images
                            if img.image_url
                        ]
                    ),
                )
                self.connection.commit()
                logging.info("Upserted fighter images.")
        except Exception as e:
            logging.error(f"Could not upsert fighter images: {e}")
            self.connection.commit()
            raise

        # Upsert scheduled events
        logging.debug("Upserting scheduled events into database")
        try:
            if self.scheduled_events:
                psycopg2.extras.execute_batch(
                    self.cursor,
                    open(
                        "stat_scrape/sql/insert_into_scheduled_events.sql", "r"
                    ).read(),
                    list(
                        [
                            (
                                ev.id,
                                ev.name,
                                ev.date,
                                ev.location,
                                ev.link,
                            )
                            for ev in self.scheduled_events
                        ]
                    ),
                )
                self.connection.commit()
                logging.info("Upserted scheduled events.")
        except Exception as e:
            logging.error(f"Could not upsert scheduled events: {e}")
            self.connection.commit()
            raise

        # Upsert scheduled fights
        logging.debug("Upserting scheduled fights into database")
        try:
            if self.scheduled_fights:
                psycopg2.extras.execute_batch(
                    self.cursor,
                    open(
                        "stat_scrape/sql/insert_into_scheduled_fights.sql", "r"
                    ).read(),
                    list(
                        [
                            (
                                sf.id,
                                sf.event_id,
                                sf.red_id,
                                sf.blue_id,
                                sf.division,
                                sf.link,
                            )
                            for sf in self.scheduled_fights
                        ]
                    ),
                )
                self.connection.commit()
                logging.info("Upserted scheduled fights.")
        except Exception as e:
            logging.error(f"Could not upsert scheduled fights: {e}")
            self.connection.commit()
            raise

        self.cursor.close()
        self.connection.close()

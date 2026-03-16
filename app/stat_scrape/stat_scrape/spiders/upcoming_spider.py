import logging

from scrapy import Spider, Request
from datetime import datetime
from stat_scrape.items import UpcomingEvent, UpcomingFight


def clean_text(response, path):
    return [data.strip() for data in response.xpath(path).getall() if data.strip()]


class UpcomingEventsSpider(Spider):
    name = "upcoming"
    start_urls = ["http://ufcstats.com/statistics/events/upcoming"]

    custom_settings = {
        "ITEM_PIPELINES": {
            "stat_scrape.upcoming_pipeline.UpcomingPipeline": 300,
        }
    }

    def parse(self, response):
        source_date_format = "%B %d, %Y"
        logging.info("Parsing upcoming events...")

        all_rows = response.xpath(
            '//*[@class="b-statistics__table-events"]//tbody//tr'
        )

        for row in all_rows:
            # Extract the event link and text from the first column
            event_link = row.xpath('td[1]//a/@href').get()
            # Skip rows without an event link (header rows, spacers)
            if not event_link:
                continue

            event_name_raw = row.xpath('td[1]//a//text()').getall()
            event_name = " ".join(
                [t.strip() for t in event_name_raw if t.strip()]
            )
            if not event_name:
                continue

            # Extract date — it's in a <span> or loose text after the link
            date_texts = [
                t.strip() for t in row.xpath('td[1]//text()').getall()
                if t.strip()
            ]
            event_date = None
            for text in date_texts:
                try:
                    event_date = datetime.strptime(text, source_date_format)
                    break
                except ValueError:
                    continue

            if event_date is None:
                logging.warning(
                    f"Could not parse date for event: {event_name}"
                )
                continue

            event_id = event_link.split("/")[-1]

            # Extract location from second column
            location_texts = row.xpath('td[2]//text()').getall()
            location = " ".join(
                [t.strip() for t in location_texts if t.strip()]
            ) if location_texts else None

            event = UpcomingEvent(
                id=event_id,
                name=event_name,
                date=event_date,
                location=location,
                link=event_link,
            )
            yield event

            # Follow the event detail page to get the fight card
            yield Request(
                event_link,
                callback=self.parse_event_card,
                cb_kwargs={"event_id": event_id},
                dont_filter=False,
            )

    def parse_event_card(self, response, event_id):
        """Parse the fight card from an upcoming event detail page.
        Extracts fighter matchups and weight classes only (no stats)."""

        for row in response.xpath(
            '//*[@class="b-fight-details__table '
            'b-fight-details__table_style_margin-top '
            'b-fight-details__table_type_event-details '
            'js-fight-table"]//tbody//tr'
        ):
            # Get all fighter links and names from the row
            # The FIGHTER column contains <a> tags with fighter names
            fighter_links = row.xpath('.//td[2]//a/@href').getall()
            fighter_names = [
                " ".join(name.split())
                for name in row.xpath('.//td[2]//a/text()').getall()
                if name.strip()
            ]

            # Weight class is in its own column (column 7 in the table)
            weight_class_raw = row.xpath('.//td[7]//text()').getall()
            weight_class = " ".join(
                [w.strip() for w in weight_class_raw if w.strip()]
            ) if weight_class_raw else None

            # We need at least 2 fighters for a matchup
            if len(fighter_names) >= 2 and len(fighter_links) >= 2:
                fight = UpcomingFight(
                    event_id=event_id,
                    red_name=fighter_names[0],
                    blue_name=fighter_names[1],
                    red_link=fighter_links[0],
                    blue_link=fighter_links[1],
                    weight_class=weight_class,
                )
                yield fight

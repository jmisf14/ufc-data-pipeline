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

        for row in response.xpath(
            '//*[@class="b-statistics__table-events"]//tbody//tr'
        )[2:]:
            content = row.xpath("td[1]//text() | td[1]//@href").getall()
            # Skip rows that don't have enough data (e.g. empty rows)
            if len(content) < 6:
                continue

            event_link = content[2]
            event_id = event_link.split("/")[-1]
            event_name = " ".join(content[3].split())
            try:
                event_date = datetime.strptime(
                    " ".join(content[5].split()), source_date_format
                )
            except (ValueError, IndexError):
                logging.warning(f"Could not parse date for event: {event_name}")
                continue

            location = " ".join(row.xpath("td[2]//text()").getall()[0].split())

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
            # Get fighter names and links
            fighter_links = row.xpath(
                'td[@class="b-fight-details__table-col '
                'b-fight-details__table-col_style_align-top"]'
                '//a/@href'
            ).getall()

            fighter_names = [
                " ".join(name.split())
                for name in row.xpath(
                    'td[@class="b-fight-details__table-col '
                    'b-fight-details__table-col_style_align-top"]'
                    '//a/text()'
                ).getall()
                if name.strip()
            ]

            # Get weight class
            weight_class_raw = row.xpath(
                'td[@class="b-fight-details__table-col '
                'l-page_align_left"]//text()'
            ).getall()
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

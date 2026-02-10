import logging
import re

from scrapy import Spider, Request
from datetime import datetime

from stat_scrape.items import ScheduledEvent, ScheduledFight, FighterImage, Fighter
from .ufcstats_spiders import clean_text, convert_height  # reuse helpers where possible


class UFCStatsUpcomingSpider(Spider):
    """
    Scrapes upcoming UFC events and scheduled fights from ufcstats.com.
    This spider is additive and does NOT change the behaviour of the main
    completed-events spider.
    """

    name = "ufcstatsupcomingspider"
    start_urls = ["http://ufcstats.com/statistics/events/upcoming?page=all"]

    def parse(self, response):
        source_date_format = "%B %d, %Y"
        logging.debug("Parsing upcoming events...")
        for row in response.xpath(
            '//*[@class="b-statistics__table-events"]//tbody//tr'
        )[2:]:
            content = row.xpath("td[1]//text() | td[1]//@href").getall()
            if not content:
                continue

            event_link = content[2]
            event = ScheduledEvent(
                id=event_link.split("/")[-1],
                name=" ".join(content[3].split()),
                date=datetime.strptime(
                    " ".join(content[5].split()), source_date_format
                ),
                location=" ".join(row.xpath("td[2]//text()").getall()[0].split()),
                link=event_link,
            )

            yield event
            yield Request(
                event.link,
                callback=self.parse_event,
                cb_kwargs={"event_id": event.id},
                dont_filter=False,
            )

    def parse_event(self, response, event_id):
        """
        Parse an upcoming event page and schedule one request per fight details page.
        """
        for row in response.xpath(
            '//*[@class="b-fight-details__table b-fight-details__table_style_margin-top b-fight-details__table_type_event-details js-fight-table"]//tbody//tr'
        ):
            fight_link = row.xpath("td//a/@href").get()
            if fight_link:
                yield Request(
                    fight_link,
                    callback=self.parse_fight,
                    cb_kwargs={"event_id": event_id},
                    dont_filter=False,
                )

    def parse_fight(self, response, event_id):
        """
        Upcoming fight: no stats yet, but we can record the matchup and division.
        """
        event_link = response.xpath('//*[@class="b-content__title"]//a/@href').get()
        fighter_links = response.xpath(
            '//*[@class="b-fight-details__person"]//a/@href'
        ).getall()

        if len(fighter_links) < 2:
            return

        fight_division = " ".join(
            response.xpath('normalize-space(//*[@class="b-fight-details__fight-head"])')
            .get()
            .split()[:-1]
        )

        scheduled_fight = ScheduledFight(
            id=response.url.split("/")[-1],
            event_id=event_id or (event_link.split("/")[-1] if event_link else None),
            red_id=fighter_links[0].split("/")[-1],
            blue_id=fighter_links[1].split("/")[-1],
            division=fight_division,
            link=response.url,
        )
        yield scheduled_fight

        # Also ensure we have fighter image URLs available for these fighters
        for fighter_url in fighter_links:
            yield Request(
                fighter_url,
                callback=self.parse_fighter_image,
                cb_kwargs={
                    "fighter_id": fighter_url.split("/")[-1],
                },
                dont_filter=False,
            )

    def parse_fighter_image(self, response, fighter_id):
        """
        Parse a fighter page to capture profile image URL and also yield a core
        Fighter item if needed (so the main pipeline logic can still manage stats).
        """
        image_url = response.xpath(
            '//*[@class="b-content__fighter"]//img/@src | //*[@class="b-content__profile"]//img/@src'
        ).get()

        if image_url:
            yield FighterImage(fighter_id=fighter_id, image_url=image_url)


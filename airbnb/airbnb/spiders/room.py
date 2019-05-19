# -*- coding: utf-8 -*-
import json
from datetime import datetime, date, timedelta
import calendar
import scrapy
from scrapy.http import Request
from .setting import listing_id_array

def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year,month)[1])
    return date(year, month, day)

class RoomSpider(scrapy.Spider):
    name = 'room'
    allowed_domains = ['www.airbnb.com']
    start_urls = ['https://www.airbnb.com']
    drop_folder = "d:/data/drop"
    num_of_month = 1

    listing_detail_url_template = "{}/v2/pdp_listing_booking_details?_format=for_web_dateless&_intents=p3_book_it&_interaction_type=pageload&guests=1&key={}&listing_id={}&locale=en&number_of_adults=1&number_of_children=0&number_of_infants=0&show_smart_promotion=0"
    
    calendar_month_url_template = "{}/v2/calendar_months?_format=with_conditions&count=4&currency=USD&key={}&listing_id={}&locale=en&year={}&month={}"

    def __init__(self, *args, **kwargs):
        self.detail_data = {}
        self.calendar_data = {}
        self.date = datetime.today()

    def parse(self, response):
        json_data = json.loads(response.css("script[type=application\/json]::text").extract()[3][4:-3])
        api_config = json_data["bootstrapData"]["layout-init"]["api_config"]        
        baseUrl = api_config["baseUrl"]
        key = api_config["key"]        
        for listing_id in listing_id_array:        
            listing_detail_url = self.listing_detail_url_template.format(baseUrl, key, listing_id)
            

            yield Request(listing_detail_url, callback=self.parse_detail, meta={"listing_id": listing_id})

            today = datetime.today()

            for i in range(0, self.num_of_month):
                calendar_date = add_months(today, i)
                calendar_month_url = self.calendar_month_url_template.format(baseUrl, key, listing_id, calendar_date.year, calendar_date.month)
                yield Request(calendar_month_url, callback=self.parse_calendar, meta={"listing_id": listing_id})

    def _add_detail_data(self, listing_id, data):
        if listing_id not in self.detail_data:
            self.detail_data[listing_id] = []
    
        self.detail_data[listing_id].append(data)

    def _add_calendar_data(self, listing_id, data):
        if listing_id not in self.calendar_data:
            self.calendar_data[listing_id] = []
    
        self.calendar_data[listing_id].append(data)

    def parse_detail(self, response):
        listing_id = response.meta["listing_id"]
        data = json.loads(response.body)
        self._add_detail_data(listing_id, data)
    
    def parse_calendar(self, response):
        listing_id = response.meta["listing_id"]
        data = json.loads(response.body)        
        self._add_calendar_data(listing_id, data)
    
    def close(self):
        with open(f"{self.drop_folder}/{self.date.strftime('%Y%m%d_detail')}.json", "w") as f:
            f.write(json.dumps(self.detail_data, indent=4))
        
        with open(f"{self.drop_folder}/{self.date.strftime('%Y%m%d_calendar')}.json", "w") as f:
            f.write(json.dumps(self.calendar_data, indent=4))
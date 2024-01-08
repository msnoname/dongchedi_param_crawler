# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class BrandItem(scrapy.Item):
    code_brand = scrapy.Field()
    brand = scrapy.Field()
    url = scrapy.Field()


class ColItem(scrapy.Item):
    name = scrapy.Field()
    description = scrapy.Field()


class DongchediItem(scrapy.Item):
    crawl_index = scrapy.Field()
    code_brand = scrapy.Field()
    code_car_series = scrapy.Field()
    code_car_type = scrapy.Field()
    brand = scrapy.Field()
    car_series = scrapy.Field()
    car_type = scrapy.Field()
    year = scrapy.Field()
    url = scrapy.Field()
    sale = scrapy.Field()
    dealer_price = scrapy.Field()
    market_time_year = scrapy.Field()
    market_time_month = scrapy.Field()



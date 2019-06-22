# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class DoubanItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    title = scrapy.Field()
    author = scrapy.Field()
    pub = scrapy.Field()
    date = scrapy.Field()
    price = scrapy.Field()
    rating_nums = scrapy.Field()
    comment_nums = scrapy.Field()
    introduction = scrapy.Field()

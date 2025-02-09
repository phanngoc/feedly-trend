# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class RssCrawlerItem(scrapy.Item):
    url = scrapy.Field()
    title = scrapy.Field()
    text_content = scrapy.Field()
    published_date = scrapy.Field()
    author = scrapy.Field()
    is_rss = scrapy.Field()

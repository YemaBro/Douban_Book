# -*- coding: utf-8 -*-
import scrapy
from Douban.items import DoubanItem
from scrapy_redis.spiders import RedisSpider


class DoubanSpider(RedisSpider):
    name = 'douban'
    allowed_domains = ['book.douban.com']
    base_url = 'https://book.douban.com/tag/{tag}?start={start}'
    start_urls = []
    tag_list = ['小说', '历史', '外国文学', '中国文学', '心理学', '散文', '计算机', '编程', '艺术', '金融']
    redis_key = 'douban:urls'

    for tag in tag_list:
        for page in range(0, 50):
            url = base_url.format(tag=tag, start=page*20)
            start_urls.append(url)

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        elements = response.css("#subject_list ul li")
        for ele in elements:
            item = DoubanItem()
            item['title'] = ele.css(".info h2 a::text").get().strip()
            pub_all = ele.css(".info .pub::text").get().strip().split(' / ')
            item['author'] = '/'.join(pub_all[:-3])
            item['pub'] = ''.join(pub_all[-3:-2])
            item['date'] = ''.join(pub_all[-2:-1])
            item['price'] = ''.join(pub_all[-1:])
            item['rating_nums'] = ele.css(".info .star span.rating_nums::text").get()
            item['comment_nums'] = ele.css(".info .star span.pl::text").get().strip().strip('()')
            item['introduction'] = ele.css(".info p::text").get()
            yield item

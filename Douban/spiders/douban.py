# -*- coding: utf-8 -*-
import scrapy
from Douban.items import DoubanItem


class DoubanSpider(scrapy.Spider):
    name = 'douban'
    allowed_domains = ['book.douban.com']
    base_url = 'https://book.douban.com/tag/{tag}'
    tag_list = ['小说', '历史', '外国文学', '中国文学', '心理学', '散文', '计算机', '编程', '艺术', '金融']

    def start_requests(self):
        for tag in self.tag_list:
            book_list_url = self.base_url.format(tag=tag)
            yield scrapy.Request(url=book_list_url, callback=self.parse, dont_filter=False)

    def parse(self, response):
        elements = response.xpath("//div[@id='subject_list']/ul[@class='subject-list']")
        for ele in elements:
            item = DoubanItem()
            item['title'] = ele.xpath("//li[@class='subject-item']/div[@class='info']/h2/a/text()").get().strip()
            pub_all = ele.xpath("//li[@class='subject-item']/div[@class='info']/div[@class='pub']/text()").get()\
                .strip().split(' / ')
            item['author'] = ''.join(pub_all[:-3])
            item['pub'] = ''.join(pub_all[-3:-2])
            item['date'] = ''.join(pub_all[-2:-1])
            item['price'] = ''.join(pub_all[-1:])
            item['rating_nums'] = ele.xpath("//li[@class='subject-item']/div[@class='info']/div[@class='star clearfix']"
                                            "/span[@class='rating_nums']/text()").get()
            item['comment_nums'] = ele.xpath("//li[@class='subject-item'][1]/div[@class='info']/div[@class='star clearf"
                                             "ix']/span[@class='pl']/text()").get().strip().strip('()')
            item['introduction'] = ele.xpath("//li[@class='subject-item'][1]/div[@class='info']/p/text()").get()
            yield item

        next_url = 'https://book.douban.com' + \
                   response.xpath("//div[@id='subject_list']/div[@class='paginator']/span[@class='next']/a/@href").get()

        if next_url is not None:
            yield scrapy.Request(url=next_url, callback=self.parse)

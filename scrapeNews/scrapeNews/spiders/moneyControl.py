# -*- coding: utf-8 -*-
import scrapy
from scrapeNews.items import ScrapenewsItem
from scrapeNews.settings import logger

class MoneycontrolSpider(scrapy.Spider):

    name = 'moneyControl'
    allowed_domains = ['moneycontrol.com']

    custom_settings = {
        'site_name': "moneyControl",
        'site_url': "http://www.moneycontrol.com/news/business/",
    }

    start_url = "http://www.moneycontrol.com/news/business/page-"

    def start_requests(self):
        yield scrapy.Request(self.start_url+"1", self.parse)

    def parse(self, response):
        if response.status != 200:
            logger.error(__name__ + " Non-200 Response Received : " + response.status + " for url " + response.url)
            return False
        try:
            item = ScrapenewsItem()  # Scraper Items
            newsContainer = response.xpath("//ul[@id='cagetory']/li[@class='clearfix']")
            for newsBox in newsContainer:
                item = ScrapenewsItem()  # Scraper Items
                self.url_stats['parsed'] += 1
                item['image'] = self.getPageImage(newsBox)
                item['title'] = self.getPageTitle(newsBox)
                item['content'] = self.getPageContent(newsBox)
                item['newsDate'] = self.getPageDate(newsBox)
                item['link'] = self.getPageLink(newsBox)

                if item['image'] is not 'Error' or item['title'] is not 'Error' or item['content'] is not 'Error' or item['link'] is not 'Error' or item['newsDate'] is not 'Error':
                    if not self.dbconn.urlExists(item['link']):
                        self.url_stats['scraped'] += 1
                        yield item
                    else:
                        self.url_stats['dropped'] += 1
                        yield None
                else:
                    self.url_stats['dropped'] += 1
                    yield None
            pagenation = response.xpath("//div[@class='pagenation']/a/@data-page").extract()
            next_page = response.urljoin(self.start_url+pagenation[-2])
            last_page = response.urljoin(self.start_url+pagenation[-1])

            if response.url != last_page:
                yield scrapy.Request(next_page, self.parse)
        except Exception as e:
            logger.error(__name__ + " Unhandled: " + str(e))

    def getPageContent(self, newsBox):
        try:
            data = newsBox.xpath('p/text()').extract_first()
            if (data is None):
                data = newsBox.xpath('h2/a/@title').extract_first()
                if (data is None):
                    logger.error(__name__ + " Error Extracting Content: " + str(newsBox.extract_first()))
                    data = 'Error'
        except Exception as e:
            logger.error(__name__ + " Error Extracting Content: " + str(e) + " :: " + str(newsBox.extract_first()))
            data = "Error"
        return data

    def getPageTitle(self, newsBox):
        try:
            data = newsBox.xpath('h2/a/text()').extract_first()
            if (data is None):
                logger.error(__name__ + " Error Extracting Title: " + str(newsBox.extract_first()))
                data = 'Error'
        except Exception as e:
            logger.error(__name__ + " Error Extracting Title: " + str(e) + " :: " + str(newsBox.extract_first()))
            data = "Error"
        return data

    def getPageLink(self, newsBox):
        try:
            data = newsBox.xpath('a/@href').extract_first()
            if (data is None):
                logger.error(__name__ + " Error Extracting Link: " + str(newsBox.extract_first()))
                data = 'Error'
        except Exception as e:
            logger.error(__name__ + " Error Extracting Link: " + str(e) + " :: " + str(newsBox.extract_first()))
            data = "Error"
        return data

    def getPageImage(self, newsBox):
        try:
            data = newsBox.xpath('a/img/@src').extract_first()
            if (data is None):
                logger.error(__name__ + " Error Extracting Image: " + str(newsBox.extract_first()))
                data = 'Error'
        except Exception as e:
            logger.error(__name__ + " Error Extracting Image: " + str(e) + " :: " + str(newsBox.extract_first()))
            data = "Error"
        return data

    def getPageDate(self, newsBox):
        try:
            data = newsBox.xpath('span/text()').extract_first()
            if (data is None):
                logger.error(__name__ + " Error Extracting Date: " + str(newsBox.extract_first()))
                data = 'Error'
        except Exception as e:
            logger.error(__name__ + " Error Extracting Date: " + str(e) + " :: " + str(newsBox.extract_first()))
            data = "Error"
        
        return data
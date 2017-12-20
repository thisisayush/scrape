# -*- coding: utf-8 -*-
import scrapy
import json
from scrapeNews.items import ScrapenewsItem
from scrapy.http import FormRequest
from scrapy.selector import Selector

class InshortsSpider(scrapy.Spider):
    name = 'inshorts'
    allowed_domains = ['www.inshorts.com']
    start_url = 'https://www.inshorts.com/en/ajax/more_news'

    custom_settings = {
        'site_name': "Inshorts",
        'site_url': "http://www.inshorts.com/en/read/",
    }

    def start_requests(self):
        return [FormRequest(self.start_url, formdata={'news_offset':''}, callback = self.parse)]


    def parse(self, response):
        if response.status != 200:
            logger.error(__name__ + " Non-200 Response Received : " + response.status + " for url " + response.url)
            return False
        try:
            response_data = json.loads(response.text)

            response_data['min_news_id']    # Intentional, this will throw KeyError on reaching last page

            body = Selector(text=response_data['html'])
            for news in body.css('div.news-card'):
                item = ScrapenewsItem()
                self.url_stats['parsed'] += 1
                item['image'] = news.css('div.news-card-image::attr(style)').extract_first()[23:-3]
                item['title'] = news.css('a.clickable>span::text').extract_first()
                item['content'] = news.css('div[itemprop*=articleBody]::text').extract_first()
                item['newsDate'] = news.css('span.time::attr(content)').extract_first()[:-5]
                item['link'] = news.css('div.read-more>a::attr(href)').extract_first()
                #item['source'] = 105
                self.url_stats['scraped'] += 1
                yield item

            yield FormRequest(self.start_url, formdata={"news_offset": response_data['min_news_id']}, callback=self.parse)
        except KeyError as e:
            # Do nothing
            return False
        except Exception as e:
            logger.error(__name__+" Unhandled: "+str(e))
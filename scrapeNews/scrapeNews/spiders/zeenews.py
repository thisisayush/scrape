import scrapy
from scrapeNews.items import ScrapenewsItem
from scrapeNews.settings import logger

class zeespider(scrapy.Spider):
    name = "zee"
    start_urls = ['http://zeenews.india.com/india',]

    custom_settings = {
        'site_name': "Zee News",
        'site_url': "http://zeenews.india.com/india",
    }

    #Scraping the main page for article links
    def parse(self, response):
        if reponse.status != 200:
            logger.error(__name__ + " Non-200 Response Received " + response.status + " for url " + response.url)
            return False
        try:
            articles = response.xpath('//section[contains(@class, "maincontent")]//div[contains(@class, "section-article")]') #extracts HTML from the start_url
            for article in articles:
                x = article.xpath('.//h3/a[2]') #extracts <a> tag from start _url
                link = x.xpath('.//@href').extract_first()  #extracts URL for the articles recursively
                self.url_stats['parsed'] += 1
                yield response.follow(link, callback = self.parse_news)

            #For scraping the links on the next page of the website
            next_page = response.xpath('//link[@rel = "next"]/@href').extract_first()
            if next_page is not None:
               yield response.follow(next_page, callback = self.parse)
        except Exception as e:
            logger.error(__name_ + " Unhandled: " + str(e))

    #For scraping a particular article listed on the main page
    def parse_news(self,response):
        try:
            i = ScrapenewsItem()
            i['title'] = response.xpath('//h1[contains(@class, "article-heading margin")]/text()').extract_first() #scrapes headline 
            i['newsDate'] = response.xpath('//span[contains(@class, "date")]/text()').extract_first()[10:-4] #scrapes datetime
            i['image'] = response.xpath('//div[contains(@class, "field-item")]/img/@src').extract_first() #scrapes image url
            i['content'] = self.getcontent(response)
            i['link'] = response.url #scrapes link; article page

            self.url_stats['scraped'] += 1

            yield i
        except Exception as e:
            self.url_stats['dropped'] += 1
            yield None

    def getcontent(self,response):
        try:
            data = response.xpath('//div[contains(@class, "article")]/div[contains(@class, "field")]//p/text()').extract_first()
            if (data is None):
                logger.error(__name__ + " Unable to Extract Content : " + response.url)
                data = 'Error'
        except Exception as e:
            logger.error(__name__ + " Unable to Extract Content : " + response.url + " :: " + str(e))
            data = 'Error'
        return data
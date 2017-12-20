# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import re
from dateutil import parser
from scrapeNews.settings import logger, DbDateFormat
from scrapy.exceptions import DropItem, CloseSpider
import scrapy.signals
from scrapeNews.db import DatabaseManager, LogsManager, ConnectionManager
import requests

class ScrapenewsPipeline(object):
    """
    This Pipeline Does Initial Spider Tasks,
    - Fetch/Assign SiteId to Spider on Start
    - Log Stats On Spider Close
    - Stores Job ID from Scrapyd Server
    """
    def open_spider(self, spider):
        logger.info(__name__+" [Spider Started]: "+spider.name)
        spider.dbconn = DatabaseManager()
        if spider.dbconn.conn == None:
            raise CloseSpider("Unable to Establish a Database Connection!")
        # Get/Assign Site Id
        site_id = self.checkSite(spider)
        # Assign Site ID
        spider.site_id = site_id
        # Get Job ID (Assume Runnning Through Scrapyd)
        job_id = self.getJobId(spider.name)
        # Start a New Log
        spider.log_id = LogsManager(spider.dbconn).start_log(site_id, job_id)
        # Spider Stats
        spider.url_stats = {'scraped': 0, 'parsed': 0, 'stored': 0, 'dropped': 0}

    def checkSite(self, spider):
        """ Check if website exists in database and fetch site id, else create new """
        #Connect To DATABASE
        if not ConnectionManager(spider.dbconn).checkConnection():
            raise CloseSpider("Unable to Establish a Database Connection")

        #Fetch Current Spider Details
        spider_name = spider.name
        site_name = spider.custom_settings['site_name']
        spider_url = spider.custom_settings['site_url']

        #Try to get SITE_ID from Database
        site_id = spider.dbconn.getSiteId(site_name)

        if site_id == False:
            # SITE_ID == False, Add Site to Database
            try:
                logger.debug(__name__+" Site "+site_name+" was Not Found! Creating Now!")
                if spider.dbconn.connect() != None:
                    spider.dbconn.cursor.execute(database.insert_site_str, (site_name, spider_url, spider_name))
                    spider.dbconn.conn.commit()
                    site_id = spider.dbconn.cursor.fetchone()['id']
                    #Save SITE_ID to Spider
                    spider.site_id = site_id
                else:
                    logger.error(__name__+' ['+spider_name+'::'+spider_url+'] Database Connection Failed ')

            except Exception as e:
                logger.error(__name__+' ['+spider_name+'::'+spider_url+'] Unable to add site :: '+str(e))
        else:
            # SITE Exists
            logger.info("Site "+site_name+" exists in database with id "+ str(site_id))
            # Save SITE_ID to Spider
            spider.site_id = site_id

        if site_id == False:
            # Send Spider Send Signal here
            raise CloseSpider("Unable to Assign SiteId to Spider "+spider.name)

        return site_id

    def getJobId(self, spiderName):
        api_url = "http://127.0.0.1:6800/"
        payload = {'project':'scrapeNews'}
        try:
            response = requests.get(api_url + "listjobs.json", params=payload)
            if response.status_code == 200:
                jobs = response.json()
                for job in jobs['running']:
                    if job['spider'] == spiderName:
                        return job['id']
            return None
        except Exception as e:
            logger.error(__name__ + " Unhandled: " + str(e))
        return None

    @classmethod
    def from_crawler(cls, crawler):
        temp = cls()
        crawler.signals.connect(temp.spider_closed, signal=scrapy.signals.spider_closed)
        crawler.signals.connect(temp.item_dropped, signal=scrapy.signals.item_dropped)
        return temp

    def spider_closed(self, spider, reason):
        if not ConnectionManager(spider.dbconn).checkConnection():
            raise CloseSpider("Unable to Establish a Database Connection")

        if not LogsManager(spider.dbconn).end_log(spider.log_id, spider.url_stats, reason):
            logger.error(__name__ + " Unable to End Log for Spider " + spider.name + " with stats: " + str(spider.url_stats))
        spider.dbconn.conn.commit()
        spider.dbconn.conn.close()
        logger.info(__name__ + spider.name +"SPIDER CLOSED")

    def item_dropped(self, item, response, exception, spider):
        spider.url_stats['dropped'] += 1
        logger.error(__name__ + " [Dropped] <Spider>: " + spider.name + " <Reason>: " + str(exception) + " <Link>: " + str(item['link']))

class DuplicatesPipeline(object):
    """
    This Pipeline Drops any Duplicate URL Missed by Spiders
    Please Use DatabaseManager().urlExists(url) in your spiders to preserve bandwidth and speed up process
    """
    def process_item(self, item, spider):
        if not ConnectionManager(spider.dbconn).checkConnection():
            raise CloseSpider("Unable to Establish a Database Connection")

        if spider.dbconn.urlExists(item['link']):
            #logger.info(__name__+" [Dropped URL] "+item['link']+" Url Already in Database")
            #spider.url_stats['dropped'] += 1
            raise DropItem("Url Already in Database")
        else:
            return item

class DataFormatterPipeline(object):
    """
    This Pipeline Formats The Data for Database
    - Convert Date into specified common format
    - Removes Unncessary Data from the item
    """

    regex_match = {
        "line_end": {
            'test':r'\n',
            'replace':''
            },
        "multi_space": {
            'test':r'\s{2,}',
            'replace':' '
            },
        "white_space_beg_end": {
            'test':r"^\s{0,}|\s{0,}$",
            'replace': ''
            }
    }

    def process_item(self, item, spider):

        for x in item:
            if item[x] == None:
                #logger.error(__name__ + " [" + spider.name + "] [DROPPED] " + x + " is None ")
                raise DropItem("Item Property '" + x + "' Missing from Item!")
            if len(item[x]) == 0:
                #logger.error(__name__ + " [" + spider.name + "] [DROPPED] " + x + " is Empty")
                raise DropItem("Item Property '" + x + "' is empty!")

        # Format Date
        item['newsDate'] = self.processDate(item['newsDate'], spider)

        # Format Data
        item['title'] = self.processRegex(item['title'])
        item['content'] = self.processRegex(item['content'])

        return item

    def processDate(self, dateStr, spider):
        try:
            date_parsed = parser.parse(dateStr, ignoretz=False, fuzzy=True)
            return date_parsed.strftime(DbDateFormat)
        except ValueError as e:
            #logger.error(__name__ + " [" + spider.name + "] [DROPPED] Error Parsing Date: "+str(e))
            #spider.custom_settings['url_stats']['dropped'] += 1
            raise DropItem(" Unable to parse Date due to " + str(e))

    def processRegex(self, text):
        for test in self.regex_match:
            text = re.sub(self.regex_match[test]['test'], self.regex_match[test]['replace'], text)
        return text

class DatabasePipeline(object):
    """
    This Pipeline Manages and Stores Processed Data into Database
    """
    def process_item(self, item, spider):
        if not ConnectionManager(spider.dbconn).checkConnection():
            raise CloseSpider("Unable to Establish a Database Connection")

        # Get Site Id for Spider
        logger.debug(__name__+" Received Item for SITE_ID: "+str(spider.site_id))

        try:
            # Insert into Database
            spider.dbconn.cursor.execute(spider.dbconn.insert_item_str,
                                         (item['title'],
                                          item['link'],
                                          item['content'],
                                          item['image'],
                                          item['newsDate'],
                                          spider.site_id,
                                          spider.log_id
                                         )
                                        )
            # Commit
            spider.dbconn.conn.commit()
            logger.info(__name__+" Finish Scraping "+str(item['link']))
            spider.url_stats['stored'] += 1

        except Exception as e:
            #logger.error(__name__ + " [" + spider.name + "] Database Insertion Failed  due to " + str(e))
            raise DropItem(" Database Insertion Failed: " + str(e))

        LogsManager(spider.dbconn).update_log(spider.log_id, spider.url_stats)

        return item

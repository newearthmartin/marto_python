from billiard.context import Process
from scrapy.crawler import Crawler
from scrapy import signals
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor
from celery import shared_task

# Wrap in a celery task.
# Can't define task here because spider is not json serializable
def crawl_task_fn(spider):
    crawler = CrawlerProcess(spider)
    crawler.start()
    crawler.join()


class CrawlerProcess(Process):
    def __init__(self, spider):
        Process.__init__(self)
        settings = get_project_settings()
        self.crawler = Crawler(spider.__class__, settings)
        self.crawler.signals.connect(reactor.stop, signal=signals.spider_closed)
        self.spider = spider

    def run(self):
        self.crawler.crawl(self.spider)
        reactor.run()

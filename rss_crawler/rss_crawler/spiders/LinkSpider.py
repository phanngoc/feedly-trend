import scrapy
from scrapy.linkextractors import LinkExtractor
from bs4 import BeautifulSoup
import sqlite3
import html2text
from urllib.parse import urlparse
import json
import feedparser

class LinkSpider(scrapy.Spider):
    name = "link_spider"

    def __init__(self, start_url=None, assistant_id=None, max_urls=500, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [start_url] if start_url else ['https://vnexpress.net/rss']
        self.allowed_domains = [urlparse(start_url).hostname] if start_url else []
        self.assistant_id = assistant_id
        self.max_urls = max_urls
        self.crawled_urls = 0

    def is_allowed_domain(self, url):
        if not self.allowed_domains:  # If no allowed domains specified, allow all
            return True
        domain = urlparse(url).hostname
        return any(domain == allowed or domain.endswith('.' + allowed) 
                  for allowed in self.allowed_domains)

    def is_rss_link(self, url):
        """Kiểm tra xem URL có phải là RSS feed không"""
        return any(pattern in url.lower() for pattern in [
            '/rss', 
            '.rss',
            '/feed',
            '.xml',
            'feed.xml',
            'rss.xml',
            'atom.xml'
        ])

    def parse_rss_feed(self, response):
        """Parse RSS feed using feedparser"""
        feed = feedparser.parse(response.body)
        
        for entry in feed.entries:
            yield {
                'url': entry.link if hasattr(entry, 'link') else '',
                'title': entry.title if hasattr(entry, 'title') else '',
                'text_content': entry.description if hasattr(entry, 'description') else '',
                'published_date': entry.published if hasattr(entry, 'published') else '',
                'author': entry.author if hasattr(entry, 'author') else '',
                'is_rss': True
            }

    def parse(self, response):
        if self.crawled_urls >= self.max_urls:
            return
        
        if not self.is_allowed_domain(response.url):
            self.logger.info(f"Skipping URL from different domain: {response.url}")
            return
            
        self.crawled_urls += 1

        # Nếu là RSS feed, xử lý bằng feedparser
        if self.is_rss_link(response.url):
            self.logger.info(f"Parsing RSS feed: {response.url}")
            yield from self.parse_rss_feed(response)
            return

        # Nếu không phải RSS feed, xử lý như trang HTML bình thường
        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = html2text.html2text(str(soup))
        
        title = soup.title.string if soup.title else ""
        if not title and soup.h1:
            title = soup.h1.get_text(strip=True)

        yield {
            'url': response.url,
            'title': title,
            'text_content': text_content,
            'is_rss': False
        }

        # Follow RSS links
        link_extractor = LinkExtractor()
        links = link_extractor.extract_links(response)
        
        for link in links:
            if self.is_allowed_domain(link.url) and self.is_rss_link(link.url):
                self.logger.info(f"Following RSS link: {link.url}")
                yield response.follow(link.url, callback=self.parse)

    def closed(self, reason):
        print('closed:reason:', reason)
        # assistant = Assistant.get(Assistant.id == self.assistant_id)
        # assistant.is_crawled = True
        # assistant.save()
        self.connection.close()

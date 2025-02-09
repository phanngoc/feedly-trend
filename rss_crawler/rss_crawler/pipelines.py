import csv
import os
from itemadapter import ItemAdapter


class RssCrawlerPipeline:
    def __init__(self):
        self.file = None
        self.writer = None

    def open_spider(self, spider):
        output_dir = 'output'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        filename = os.path.join(output_dir, f'{spider.name}_results.csv')
        self.file = open(filename, 'w', newline='', encoding='utf-8')
        self.writer = csv.DictWriter(self.file, fieldnames=['url', 'title', 'text_content'])
        self.writer.writeheader()

    def close_spider(self, spider):
        if self.file:
            self.file.close()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        self.writer.writerow(adapter.asdict())
        return item

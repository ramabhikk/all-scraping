# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

class MusgravePipeline:
    def process_item(self, item, spider):
        return item

class DuplicatesPipeline(object):  
   def __init__(self): 
      self.ids_seen = set() 

   def process_item(self, item, spider): 
      if item['Product Code'] in self.ids_seen:
        item['On Promo'] = 'Yes'
        raise DropItem("Repeated items found: %s" % item) 
      else: 
        self.ids_seen.add(item['Product Code']) 
        item['On Promo'] = 'No'
        return item    

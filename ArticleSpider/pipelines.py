# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import codecs
import json

from scrapy.pipelines.images import ImagesPipeline
from scrapy.exporters import JsonItemExporter
from twisted.enterprise import adbapi

import MySQLdb
import MySQLdb.cursors

class ArticlespiderPipeline(object):
    def process_item(self, item, spider):
        return item

class JsonWithEncodingPipeline(object):
    def __init__(self):
        self.file = codecs.open('article.json', 'w', encoding="utf-8")

    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(lines)
        return item

    def spider_closed(self, spider):
        self.file.close()

class JsonExporterPipeline(object):
    #调用scrapy中的JsonItemExporter
    def __init__(self):
        self.file = open('articleexport.json', 'wb')
        self.exporter = JsonItemExporter(self.file, encoding="utf-8", ensure_ascii=False)
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item

class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        if "front_image_url" in item:
            #如果url中有front_image_url才进行下面的处理
            for ok, value in results:
                image_file_path = value['path']
            item["front_image_path"] = image_file_path

        return item

#同步操作，会造成插入阻塞
class MysqlPipeline(object):
    def __init__(self):
        self.conn = MySQLdb.Connect('127.0.0.1', 'root', '123', 'article_spider', charset = "utf8", use_unicode=True)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        insert_sql = "insert into article_item(title, url, url_object_id, create_date, favorite_nums) values(%s, %s, %s, %s, %s)"
        self.cursor.execute(insert_sql, (item['title'], item['url'], item['url_object_id'], item['create_date'], item['favorite_nums']))
        self.conn.commit()

#使用异步操作来完成
class MysqlTwistedPipeline(object):
    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        dbparams = dict(
            host = settings['MYSQL_HOST'],
            db = settings['MYSQL_DBNAME'],
            user = settings['MYSQL_USER'],
            password = settings['MYSQL_PASSWORD'],
            charset = "utf8",
            cursorclass = MySQLdb.cursors.DictCursor,
            use_unicode = True,
        )
        dbpool = adbapi.ConnectionPool("MySQLdb", **dbparams)

        return cls(dbpool)

    def process_item(self, item, spider):
        #使用twisted将mysql插入变成异步
        query = self.dbpool.runInteraction(self.do_insert, item)
        #出现错误时
        query.addErrback(self.handle_error)

    def handle_error(self, failure):
        #处理异步插入的异常
        print (failure)

    def do_insert(self, cursor, item):
        #执行具体插入
        insert_sql = "insert into article_item(title, url, url_object_id, create_date, favorite_nums) values(%s, %s, %s, %s, %s)"
        cursor.execute(insert_sql, (item['title'], item['url'], item['url_object_id'], item['create_date'], item['favorite_nums']))
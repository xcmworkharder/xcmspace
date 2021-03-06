# -*- coding: utf-8 -*-
import re
import scrapy
import datetime
from scrapy.http import Request
from urllib import parse
from scrapy.loader import ItemLoader

from ArticleSpider.items import JobBoleArticleItem, ArticleItemLoader
from ArticleSpider.utils.common import get_md5


class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobble.com']
    start_urls = ['http://blog.jobbole.com/all-posts/']       #http://blog.jobble.com/

    def parse(self, response):
        """
        1.获取文章列表中的文章url并交给scrapy下载后进行解析
        2.获取下一页的url并交给scrapy进行下载，下载完成后交给parse
        """
        #解析列表页中的所有文章url并交给scrapy下载后并进行解析
        post_nodes = response.css("#archive .floated-thumb .post-thumb a")
        for post_node in post_nodes:
            image_url = post_node.css("img::attr(src)").extract_first("")
            post_url = post_node.css("a::attr(href)").extract_first("")
            yield Request(url=parse.urljoin(response.url, post_url), meta={"front_image_url":image_url}, callback=self.parse_detail, dont_filter=True)  #要request的地址和allow_domain里面的冲突，从而被过滤掉,要停用过滤功能。

        #提取下一页并交给scrapy进行下载
        next_url = response.css(".next.page-numbers::attr(href)").extract_first("")
        if next_url:
            yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse, dont_filter=True)

    def parse_detail(self, response):
        #提取文章的具体字段
        # 使用xpath提取字段
        """
        title = response.xpath('//*[@class="entry-header"]/h1/text()').extract_first("")  #也可以使用extract_first()，存在数组越界的风险
        create_date =response.xpath('//p[@class="entry-meta-hide-on-mobile"]/text()').extract_first("").strip().replace("·","").strip()

        praise_nums = response.xpath("//span[contains(@class,'vote-post-up')]/h10/text()").extract_first("")
        favorite_nums = response.xpath("//span[contains(@class,'bookmark-btn')]/text()").extract_first("")
        match_re = re.match(".*?(\d+).*", favorite_nums)
        if match_re:
            favorite_nums = match_re.group(1)
        else:
            favorite_nums = 0
        comment_nums = response.xpath("//a[@href='#article-comment']/span/text()").extract_first("")
        match_re = re.match(".*?(\d+).*", comment_nums)
        if match_re:
            comment_nums = match_re.group(1)
        else:
            comment_nums = 0
        content = response.xpath("//div[@class='entry']").extract_first("")

        tag_list = response.xpath('//p[@class="entry-meta-hide-on-mobile"]/a/text()').extract()
        tag_list = [element for element in tag_list if not element.strip().endswith("评论")]
        tags = ",".join(tag_list)
        """

        article_item = JobBoleArticleItem()

        #通过css选择器提取字段
        # front_image_url = response.meta.get("front_image_url","")   #文章封面图
        # title = response.css(".entry-header h1::text").extract_first("")
        # create_date = response.css("p.entry-meta-hide-on-mobile::text").extract_first("").strip().replace("·","").strip()
        # praise_nums = response.css(".vote-post-up h10::text").extract_first("")
        # match_re = re.match(".*?(\d+).*", praise_nums)
        # if match_re:
        #     praise_nums = int(match_re.group(1))
        # else:
        #     praise_nums = 0
        # favorite_nums = response.css(".bookmark-btn::text").extract_first("")
        # match_re = re.match(".*?(\d+).*", favorite_nums)
        # if match_re:
        #     favorite_nums = int(match_re.group(1))
        # else:
        #     favorite_nums = 0
        # comment_nums = response.css("a[href='#article-comment'] span::text").extract_first("")
        # match_re = re.match(".*?(\d+).*", comment_nums)
        # if match_re:
        #     comment_nums = int(match_re.group(1))
        # else:
        #     comment_nums = 0
        # content = response.css("div.entry").extract_first("")
        #
        # tag_list = response.css('p.entry-meta-hide-on-mobile a::text').extract()
        # tag_list = [element for element in tag_list if not element.strip().endswith("评论")]
        # tags = ",".join(tag_list)
        #
        # article_item['url_object_id'] = get_md5(response.url)
        # article_item["title"] = title
        # try:
        #     create_date = datetime.datetime.strptime(create_date, "%Y/%m/%d").date()
        # except Exception as e:
        #     create_date = datetime.datetime.now().date()
        # article_item["create_date"] = create_date
        # article_item["url"] = response.url
        # article_item["front_image_url"] = [front_image_url]
        # article_item["praise_nums"] = praise_nums
        # article_item["favorite_nums"] = favorite_nums
        # article_item["comment_nums"] = comment_nums
        # article_item["tags"] = tags
        # article_item["content"] = content

        #通过itemloader来加载item
        front_image_url = response.meta.get("front_image_url", "")  # 文章封面图
        item_loader = ArticleItemLoader(item=JobBoleArticleItem(), response=response)
        item_loader.add_css("title", ".entry-header h1::text")
        # item_loader.add_xpath()
        item_loader.add_value("url", response.url)  #不使用css或xpath,而是直接赋值的方式用add_value
        item_loader.add_value("url_object_id", get_md5(response.url))
        item_loader.add_css("create_date", "p.entry-meta-hide-on-mobile::text")
        item_loader.add_value("front_image_url", [front_image_url])
        item_loader.add_css("praise_nums", ".vote-post-up h10::text")
        item_loader.add_css("comment_nums","a[href='#article-comment'] span::text")
        item_loader.add_css("favorite_nums",".bookmark-btn::text")
        item_loader.add_css("tags", "p.entry-meta-hide-on-mobile a::text")
        item_loader.add_css("content", "div.entry")

        article_item = item_loader.load_item()

        yield article_item
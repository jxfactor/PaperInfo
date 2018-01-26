# -*- coding: utf-8 -*-
import sys
import httplib
import urllib2
import os
import time
import re
from bs4 import BeautifulSoup
from pymongo import MongoClient

reload(sys)
sys.setdefaultencoding('utf-8')
httplib.HTTPConnection._http_vsn = 10
httplib.HTTPConnection._http_vsn_str = 'HTTP/1.0'


class TheSpider:
    def __init__(self):
        # self.user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) ' \
        #                   'AppleWebKit/537.36 (KHTML, like Gecko) ' \
        #                   'Chrome/58.0.3029.81 ' \
        #                   'Safari/537.36'
        self.user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
        self.headers = {'User-Agent': self.user_agent}
        self.conn = MongoClient('localhost', 27017)

    def get_post_set(self):
        db = self.conn.paper_info
        return db.post_set

    def close_db_conn(self):
        self.conn.close()

    def get_html_doc(self, s_url):
        req = urllib2.Request(s_url, headers=self.headers)
        return urllib2.urlopen(req).read()

    def find_paper_list(self, s_url, s_year, s_conf):
        paper_urls = []
        counts = 0

        soup = BeautifulSoup(self.get_html_doc(s_url), "lxml")
        soup_li = soup.find_all("li", class_="entry inproceedings")
        for li_row in soup_li:
            soup_text = li_row.find_all("a", attrs={"itemprop": "url"})
            paper_urls.append(soup_text[0].attrs['href'])

        for paper_url in paper_urls:
            counts = counts + 1
            while True:
                print "No.{id}    {year}".format(id=counts, year=s_year)
                is_Ok = self.execute_paper_url(paper_url, s_year, s_conf, counts)
                if is_Ok:
                    break
                else:
                    print 'error happen!'
                    print 'wait 10 seconds \n'
                    time.sleep(10)

        return counts, s_year

    def execute_paper_url(self, s_url, s_year, s_conf, s_counts):
        try:
            print s_url
            soup = BeautifulSoup(self.get_html_doc(s_url), "lxml")
            soup_paper_title = soup.find_all("meta", attrs={"name": "citation_title"})
            if len(soup_paper_title) == 0:
                print 'access denied'
            else:
                author_list = []
                institution_list = []
                print soup_paper_title[0].attrs['content']
                print '\n'
                soup_table = soup.find_all("table", class_="medium-text")
                soup_author = soup_table[0].find_all("a", attrs={"title": "Author Profile Page"})
                soup_institution = soup_table[0].find_all("a", attrs={"title": "Institutional Profile Page"})
                for j in range(0, len(soup_author), 1):
                    print soup_author[j].text
                    author_list.append(soup_author[j].text)
                    if len(soup_institution) > j:
                        print soup_institution[j].text
                        institution_list.append(soup_institution[j].text)
                    else:
                        institution_list.append("Nothing")
                    print '\n'
                print '\n'

                co_author_dict = {}
                for j in range(1, len(soup_author), 1):
                    author_key = "co_author_{id}".format(id=j)
                    co_author_dict[author_key] = {"author": author_list[j],
                                                  "institution": institution_list[j]}

                paper_record = {"title": soup_paper_title[0].attrs['content'],
                                "url": s_url,
                                "year": s_year,
                                "conference": s_conf,
                                "first_author": {
                                    "author": author_list[0],
                                    "institution": institution_list[0]},
                                "co_author": co_author_dict,
                                "no": s_counts}
                print paper_record
                print "connect"
                post_set = self.get_post_set()
                post_set.insert(paper_record)

                print paper_record

            return True
        except Exception as e:
            print e
            return False

    def find_acm_conference_paper(self, s_urls_str, s_conf_name, s_begin_year):
        years = range(s_begin_year, 2018, 1)
        urls = [s_urls_str.format(str(y)) for y in years]
        counts = 0
        year_paper = {}
        for url in urls:
            paper_counts, paper_year = self.find_paper_list(url, years[counts], s_conf_name)
            year_paper[str(paper_year)] = paper_counts
            counts = counts + 1

        print year_paper

    def conference_list(self):
        # CHI
        self.find_acm_conference_paper('http://dblp.uni-trier.de/db/conf/chi/chi{}.html',   "CHI",  1989)
        # UIST
        self.find_acm_conference_paper('http://dblp.uni-trier.de/db/conf/uist/uist{}.html', "UIST", 1988)
        # IUI
        self.find_acm_conference_paper('http://dblp.uni-trier.de/db/conf/iui/iui{}.html',   "IUI",  1993)
        # MobileHCI
        self.find_acm_conference_paper('http://dblp.uni-trier.de/db/conf/mhci/mhci{}.html', "MobileHCI", 2006)

mySpider = TheSpider()
mySpider.conference_list()

print "end"

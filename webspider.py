#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import bs4
import requests
import os
import sys
import re


reload(sys)
sys.setdefaultencoding('utf-8')

if __name__ == '__main__':
    #try向网页发送请求，并对可能的异常做出处理
    def get_url_response(url):
        try:
            response = requests.get(url, timeout=6)#发送请求，url为网址，一般正常打开网页为3到4秒，如果超过六秒就重试
        except requests.ConnectionError:#ConnectionError：采用递归重试打开网页，直到成功打开
            print 'retrying open url:' + url
            response = get_url_response(url)
        except (requests.exceptions.ReadTimeout) as e:#requests.exceptions.ReadTimeout：网页可能会拒绝访问，可能是访问太频繁，设置sleep并重试以防止程序中断
            if str(e) == "403 Client Error: Forbidden":
                print "praw_call(): 403 forbidden"
                return False
            if str(e) == "404 Client Error: Not Found":
                print "praw_call(): 404 not found"
                return False
            print "praw_call(): Reddit is down (%s), sleeping...", e
            time.sleep(30)
            print 'retrying open url:' + url
            response = get_url_response(url)
        return response

    #用bs4 获取某些数据比较方便，这是获取soup的方法，需要先获取response
    def get_url_soup(response):
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        return soup

    #获取当前页面中新闻的种类的链接
    def get_news_category_urls(html):
        b = []
        for a in re.findall(r'(http://(.{0,15}).mb.com.ph/category/(.+?)/)"',html):
            b.append(a[0])#获取HTML文档中a标签的以“mb.com.ph/category/”为结尾的href健及其内容
        print b
        return b

    #获取当前页面中包含的新闻的链接（每页6条）
    def get_new_urls_in_this_page(category_url_soup):
        return [a.attrs.get('data-permalink') for a in
                category_url_soup.select('div.uk-width-medium-1-1 article[data-permalink]')]

    #获取下一页的链接
    def get_next_page_soup(current_page_soup):
        current_page = int(
            re.search(r'\d+', str(current_page_soup.select('ul.uk-pagination li.uk-active span'))).group())
        if (not current_page_soup.select('ul.uk-pagination a[href$=' + str(current_page + 1) + '/]')):
            return None
        else:
            next_page_url = [a.attrs.get('href') for a in
                             current_page_soup.select('ul.uk-pagination a[href$=' + str(current_page + 1) + '/]')][0]
            print next_page_url
            return get_url_soup(get_url_response(next_page_url))

    #把获取到的时间转换成要求的格式
    def get_pub_time(pub_time_prototype):
        match = re.search(r'(\D+?) (\d{1,2}), (\d{4})-(\d{1,2}):(\d{2}) (\D+?)', pub_time_prototype)

        month = match.group(1)
        if (month == 'January'):
            month = 1
        if (month == 'February'):
            month = 2
        if (month == 'March'):
            month = 3
        if (month == 'April'):
            month = 4
        if (month == 'May'):
            month = 5
        if (month == 'June'):
            month = 6
        if (month == 'July'):
            month = 7
        if (month == 'August'):
            month = 8
        if (month == 'September'):
            month = 9
        if (month == 'October'):
            month = 10
        if (month == 'November'):
            month = 11
        if (month == 'December'):
            month = 12

        pub_hour = int(match.group(4))
        pub_period_of_day = match.group(6)
        if (pub_period_of_day == 'PM'):
            pub_hour = pub_hour + 12

        pub_time = str(match.group(3)) + '-' + \
                   str(month) + '-' + \
                   str(match.group(2)) + ' ' + \
                   str(pub_hour) + ':' + \
                   str(match.group(5)) + ':' + \
                   '00'
        return pub_time

    #对一个分类进行爬取
    def handle_one_category(news_category_url):
        # pool = Pool(6)   本来想用线程池，在windows用不了…
        current_page_response = get_url_response(news_category_url)  #先获取给来的分类的url
        current_page_soup = get_url_soup(current_page_response)  #调用bs4 工具
        print news_category_url#打印一下当前处理的分类

        #仿其他语言的do...while()语句，循环爬取分类中的每一页中的新闻（每页6条）
        while (True):
            new_urls_in_this_page = get_new_urls_in_this_page(current_page_soup)   #获取当前页面中各条新闻的链接储存为list形式

            new_images_url = [a.attrs.get('src') for a in current_page_soup.select('div.uk-overlay img[src]')]#每条新闻的图片都会显示在这一页，而新闻内却不一定会有，所以在这一页先获取每个新闻的图片，储存为list形式
            page_and_image_list = []#先定义一个空的列表以打包每条新闻的信息（图片，当前新闻id（即当前爬取到的第几条），新闻链接）
            for i in range(len(new_urls_in_this_page)):
                dict = {'page_url': new_urls_in_this_page[i], 'image_url': new_images_url[i], 'new_id': new_id[i]}#把新闻的信息包装好，三个list中第i个元素都对应同一条新闻，拿出来存放在dick打包好
                page_and_image_list.append(dict)#把每一个打包好的新闻的信息加在预先定义好的list里，page_and_image_list[i]包含了该页面第i+1条（i从零开始）新闻的信息

            # 用来跳过已经爬取的新闻，但是不包含新加的，也会因此而有重复，但是如果爬虫出错了重新开可以快速到达断点
            #方法：判断爬取保存的新闻中该序号是否已经存在，如果存在了，就跳过这页，如果不 就开始爬
            if (os.path.exists('D:/DOCUMENTS/spider/json/' + str(page_and_image_list[len(new_urls_in_this_page) - 1]['new_id']) + '.json') == False):
                for i in page_and_image_list:#对list里打包好的新闻信息逐一处理
                    save_news_data(i)#调用保存数据方法，在下面有定义
                # result = pool.map(save_news_data, page_and_image_list)
            for i in range(6):#处理完之后，每个新闻id都加6，防止重写已爬取的网页
                new_id[i] = new_id[i] + 6

            next_page_soup = get_next_page_soup(current_page_soup)#获取下一页的链接，可能为None，表示到了最后一页
            if (next_page_soup is None):#如果到了最后一页，表示这个分类已经爬完，跳出循环。
                break
            else:#如果还没有爬到最后一页，继续爬，把当前循环里的当前页面改成下一页
                current_page_soup = next_page_soup


    def save_news_data(page_and_image_url):
        response = get_url_response(page_and_image_url['page_url'])#拿到传进来的每条新闻的信息（链接、图片、id），先get response，就相当于URLopen
        response_url = response.url#获取当前新闻的url，当然也可以用page_and_image_url['page_url']
        news_html = response.text
        news_soup = get_url_soup(response)

        news_id = page_and_image_url['new_id']
        source_id = 1
        language = 'chi'
        requests_url = page_and_image_url['page_url']
        response_url = response_url
        classification = news_soup.select('ul.uk-breadcrumb a[href^=http://news.mb.com.ph/category/]')[0].string
        abstract = None
        title = news_soup.title.string

        body = ''
        for a in news_soup.select('div.tm-main p'):
            if (re.match('<p>Tags', str(a)) is not None):
                break
            if (a.string is not None):
                body = body + a.string + ' '

        pub_time_prototype = re.search(r'<time datetime="(.+?)">', news_html).group(1)
        pub_time = get_pub_time(pub_time_prototype)
        cole_time = time.time()
        out_links = [a.attrs.get('href') for a in news_soup.select('a[href]')]
        images = page_and_image_url['image_url']

        html = open('D:/DOCUMENTS/spider/html/' + str(news_id) + '.html', 'w')
        html.write(news_html)
        html.close()

        json_f = open('D:/DOCUMENTS/spider/json/' + str(news_id) + '.json', 'w')
        json_f.write('{"news_id":' + str(news_id) + ','
                     + '"source_id":' + str(source_id) + ','
                     + '"language":' + language + ','
                     + '"requests_url":' + str(requests_url) + ','
                     + '"response_url":' + str(response_url) + ','
                     + '"classification":' + classification + ','
                     + '"abstract":' + str(abstract) + ','
                     + '"title":' + title + ','
                     + '"body":' + str(body) + ','
                     + '"pub_time":' + pub_time + ','
                     + '"cole_time":' + str(cole_time) + ','
                     + '"out_links":' + str(out_links) + ','
                     + '"images":' + str(images) + ','
                     + '}')
        json_f.close()
        print page_and_image_url['new_id']

    parent_url_response = get_url_response('http://www.mb.com.ph/')
    parent_url_soup = get_url_soup(parent_url_response)
    print 'GET_PARENT_SOUP:OK'
    new_id = [1, 2, 3, 4, 5, 6]
    for news_category_url in get_news_category_urls(parent_url_response.text):
        handle_one_category(news_category_url)
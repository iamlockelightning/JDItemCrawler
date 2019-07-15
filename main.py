# coding=utf-8
import os
import urllib.parse

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

from bs4 import BeautifulSoup
import time
import json


def get_item_classes(browser, url):
    browser.get(url)
    time.sleep(2)
    browser.find_element_by_css_selector('a[class="sl-e-more J_extMore"]').click()
    time.sleep(1)
    html_page = browser.page_source
    soup = BeautifulSoup(html_page, "html.parser")
    classes = []
    for li in soup.select('li[id*=brand-]'):
        classes.append("https://search.jd.com/" + li.a.get('href'))
    return classes


def get_item_urls(browser, url, limit=-1):
    browser.get(url)
    item_urls = []
    pg_cnt = 0
    while True:
        time.sleep(2)
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        info = browser.find_elements_by_class_name('gl-i-wrap')
        page_urls = []
        for line in info:
            page_urls.append(line.find_element_by_class_name('p-img').find_element_by_tag_name('a').get_attribute('href'))
        pg_cnt += 1
        print("page:", pg_cnt, "\titem num:", len(page_urls))
        item_urls += page_urls
        if len(browser.find_elements_by_css_selector('a[class="pn-next"]')) == 0:
            break
        else:
            if limit == -1 or pg_cnt < limit:
                browser.find_element_by_css_selector('a[class="pn-next"]').click()
            else:
                break
    return item_urls


def parse_item_pages(browser, urls, limit=-1):
    pages = []
    for i, url in enumerate(urls):
        print(i, url)
        if i % 20 == 0:
            print("current url NO.", i, "\ttotal:", len(urls))
        page = {}
        browser.get(url)
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        if len(browser.find_elements_by_class_name("sku-name")) != 0:
            page["title"] = browser.find_element_by_class_name("sku-name").text
        else:
            page["title"] = ""
        if len(browser.find_elements_by_class_name("p-price")) != 0 and len(browser.find_element_by_class_name("p-price").find_elements_by_xpath("span")) > 1:
            page["price"] = browser.find_element_by_class_name("p-price").find_elements_by_xpath("span")[1].text
        else:
            page["price"] = ""
        if len(browser.find_elements_by_id('comment-count')) != 0:
            if len(browser.find_element_by_id('comment-count').find_elements_by_tag_name('a')) != 0:
                page["total_comment_num"] = browser.find_element_by_id('comment-count').find_element_by_tag_name('a').text
            else:
                page["total_comment_num"] = ""
        else:
            page["total_comment_num"] = ""

        if len(browser.find_elements_by_class_name('percent-con')) != 0:
            page["overall_score"] = browser.find_element_by_class_name('percent-con').text
        else:
            page["overall_score"] = ""
        
        tag_list = []
        tags = browser.find_elements_by_class_name(' tag-1')
        for tag in tags:
            tag_list.append(tag.text)
        page["overall_tag_list"] = tag_list

        if len(browser.find_elements_by_id('comm-curr-sku')) != 0:
            browser.find_element_by_id('comm-curr-sku').send_keys(Keys.SPACE)
            time.sleep(1)

        if len(browser.find_elements_by_class_name('filter-list')) != 0:
            page["current_comment_num"] = browser.find_element_by_class_name('filter-list').find_elements_by_tag_name('em')[0].text
        else:
            page["current_comment_num"] = ""
        current_tag_list = []
        if len(browser.find_elements_by_class_name('filter-list')) != 0:
            single_tags = browser.find_element_by_class_name('filter-list').find_elements_by_tag_name('li')[1:7]
            for each in single_tags:
                current_tag_list.append(each.find_element_by_tag_name('a').text)
        page["current_tag_list"] = current_tag_list

        
        attr_val = []
        if len(browser.find_elements_by_css_selector('li[data-tab="trigger"][clstag="shangpin|keycount|product|pcanshutab"]')) != 0:
            browser.find_element_by_css_selector('li[data-tab="trigger"][clstag="shangpin|keycount|product|pcanshutab"]').click()        
            time.sleep(2)
            dt = [x.text for x in browser.find_element_by_class_name("Ptable").find_elements_by_tag_name("dt") if x.text.strip() != ""]
            dd = [x.text for x in browser.find_element_by_class_name("Ptable").find_elements_by_tag_name("dd") if x.text.strip() != ""]
            if len(dt) == len(dd):
                attr_val = [[dt[i], dd[i]] for i in range(len(dt))]
            else:
                print("error in parsing attr_val")
        page["attr_val"] = attr_val

        comments_in_pages = []
        if len(browser.find_elements_by_css_selector('li[data-tab="trigger"][data-anchor="#comment"]')) != 0:
            browser.find_element_by_css_selector('li[data-tab="trigger"][data-anchor="#comment"]').click()
            time.sleep(2)
            pg_cnt = 0
            while True:
                time.sleep(2)
                browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)

                divs = browser.find_element_by_id('comment-0').find_elements_by_class_name('comment-item')
                page_comment = []
                for each in divs:
                    single = {}
                    if each.find_element_by_class_name("user-level").find_elements_by_tag_name('a'):
                        single["membership"] = "PLUS会员"
                    else:
                        single["membership"] = "普通会员"
                    single["star"] = each.find_element_by_class_name('comment-column').find_element_by_tag_name('div').get_attribute('class').split("comment-star star")[1]
                    single["text"] = each.find_element_by_class_name('comment-column').find_element_by_tag_name('p').text
                    spans = each.find_element_by_class_name('order-info').find_elements_by_tag_name('span')
                    order_detail = []
                    for index, everyone in enumerate(spans):
                        order_detail.append(spans[index].text)
                    single["order_detail"] = order_detail
                    page_comment.append(single)
                pg_cnt += 1
                print("page:", pg_cnt, "\tcomment num:", len(page_comment))
                comments_in_pages += page_comment

                if len(browser.find_elements_by_css_selector('a[class="ui-pager-next"][href="#comment"][clstag="shangpin|keycount|product|pinglunfanye-nextpage"]')) == 0:
                    break
                else:
                    if limit == -1 or pg_cnt < limit:
                        browser.find_elements_by_class_name('ui-pager-next')[0].send_keys(Keys.ENTER)
                    else:
                        break

        page["comments_in_pages"] = comments_in_pages
        pages.append(page)

    return pages


def get_brand(c):
    return urllib.parse.unquote(c.split("ev=exbrand_")[1].split("%5E&uc=0#J_searchWrap")[0])



if __name__ == "__main__":
    options = Options()
    options.add_argument("--headless")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # 选定浏览器内核
    browser = webdriver.Chrome(options=options) # Chrome # Edge # Safari # Firefox

    CLASS_LIMIT = 36            # 爬取的目标类别下的品牌数上限
    PAGE_LIMIT = -1             # 爬取的每一品牌下商品的页数（每页60个商品，-1表示爬取全部商品）
    COMMENT_LIMIT = 5           # 爬取的每一商品评论的页数（每页10条评价，-1表示爬取全部评价）

    # 爬取类别下的品牌名称
    CLASS_URL = "https://search.jd.com/Search?keyword=%E6%89%8B%E6%9C%BA&enc=utf-8&pvid=c4aedc3cb84146e89fde7b8901f19cf5"   # 需制定类别URL
    if os.path.exists("classes.txt"):
        classes = []
        with open("classes.txt", "r") as fr:
            for line in fr:
                classes.append(line.strip())
    else:
        classes = get_item_classes(browser, CLASS_URL)
        with open("classes.txt", "w") as fw:
            for c in classes:
                fw.write(c + "\n")
    print("__Done! classes")

    # 依据品牌列表，爬取每一品牌下的商品
    matches = [f for f in os.listdir() if f.startswith("item_urls")]
    if len(matches) != 0:
        item_urls = []
        for m in matches:
            i_u = []
            with open(m, "r") as fr:
                for line in fr:
                    i_u.append(line.strip())
            item_urls.append(i_u)
    else:
        item_urls = []
        for c in classes[:min(CLASS_LIMIT, len(classes))]:
            print("extract brand:", get_brand(c))
            item_urls.append(get_item_urls(browser, c, limit=PAGE_LIMIT))
        for i in range(len(item_urls)):
            with open("item_urls_" + get_brand(classes[i]) + ".txt", "w") as fw:
                for item in item_urls[i]:
                    fw.write(item + "\n")
    print("__Done! item_urls")

    # 依据商品列表，爬去每一商品的信息
    for i, urls in enumerate(item_urls):
        if len(matches) == 0:
            brand = get_brand(c)
        else:
            brand = matches[i].split("urls_")[1][:-4]
        print("extract brand:", brand)
        data = parse_item_pages(browser, urls, limit=COMMENT_LIMIT)
        print("brand:", brand, "\tdata num:", len(data))
        with open("data_" + brand + ".txt", "w") as fw:
            for d in data:
                fw.write(json.dumps(d) + "\n")
    print("__Done! data")


    browser.close()
    browser.quit()

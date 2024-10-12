from typing import Any
import scrapy
from selenium import webdriver
from scrapy.http import HtmlResponse
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import html
import time
import re
import os

path_dict = {"https://flk.npc.gov.cn/fl.html": "法律"}
page_num = {"https://flk.npc.gov.cn/fl.html": 68, "https://flk.npc.gov.cn/xf.html": 1, "https://flk.npc.gov.cn/dfxfg.html": 2250}

class MySpiderSpider(scrapy.Spider):
    name = "my_spider"
    allowed_domains = ["flk.npc.gov.cn"]
    # start_urls = ["https://flk.npc.gov.cn/fl.html", "https://flk.npc.gov.cn/xf.html", "https://flk.npc.gov.cn/dfxfg.html"]
    start_urls = ["https://flk.npc.gov.cn/dfxfg.html"]

    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--allow-insecure-localhost')  # 可选，针对本地自签名证书
        chrome_options.add_argument('--allow-running-insecure-content')  # 允许加载不安全的内容


        self.driver = webdriver.Chrome(chrome_options)
        self.log_file = 'log.txt'
        if os.path.exists(self.log_file):
            os.remove(self.log_file)

    def log(self, msg):
        with open(self.log_file, 'a') as f:
            f.write(msg + '\n')
    
    def _scraw_page(self, idx, response):
        self.log(f"start to crawl {response.url} page {idx}")

        if idx != 1:
            try:
                page_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'span.layui-laypage-skip input.layui-input'))
                )
                page_input.clear()
                page_input.send_keys(str(idx))
                confirm_button = self.driver.find_element(By.CSS_SELECTOR, 'span.layui-laypage-skip button.layui-laypage-btn')
                confirm_button.click()
                time.sleep(1)
            except Exception as e:
                self.log(f"failed to jump to page {idx} of {response.url}: {e}")
                self.driver.get(response.url)
                self.driver.implicitly_wait(10)
                time.sleep(5)
                return False

        rendered_body = self.driver.page_source
        response = HtmlResponse(url=response.url, body=rendered_body, encoding='utf-8')
        urls = re.findall("showDetail\(['\"](.+?)['\"]\)", html.unescape(response.text))

        if len(urls) == 0:
            self.log(f"retrying {response.url} page {idx}")
            self.driver.refresh()
            return False
        else:
            with open(response.url.split('/')[-1].split('.')[0] + '_urls.txt', 'a') as f:
                f.write('\n'.join(urls) + '\n')
            return True

    def parse(self, response):
        self.driver.get(response.url)
        self.driver.implicitly_wait(10)
        time.sleep(5)

        for i in range(1, page_num[response.url] + 1):
            while not self._scraw_page(i, response):
                pass
    
    def __del__(self):
        self.driver.quit()
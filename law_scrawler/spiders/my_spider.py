from typing import Any
import scrapy
from selenium import webdriver
from scrapy.http import HtmlResponse
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import html
import time
import re
import os

path_dict = {"https://flk.npc.gov.cn/fl.html": "法律"}

class MySpiderSpider(scrapy.Spider):
    name = "my_spider"
    allowed_domains = ["flk.npc.gov.cn"]
    start_urls = ["https://flk.npc.gov.cn/fl.html", "https://flk.npc.gov.cn/xf.html", "https://flk.npc.gov.cn/dfxfg.html"]

    def __init__(self):
        self.driver = webdriver.Chrome()
        self.log_file = 'log.txt'
        if os.path.exists(self.log_file):
            os.remove(self.log_file)

    def log(self, msg):
        with open(self.log_file, 'a') as f:
            f.write(msg + '\n')

    def parse(self, response):
        self.driver.get(response.url)
        self.driver.implicitly_wait(10)
        time.sleep(5)

        idx = 1
        while True:
            self.log(f"Start crawling {response.url}, page {idx}") 
            
            rendered_body = self.driver.page_source
            response = HtmlResponse(url=response.url, body=rendered_body, encoding='utf-8')

            urls = re.findall("showDetail\(['\"](.+?)['\"]\)", html.unescape(response.text))

            # with open('text.html', 'w', encoding='utf-8') as f:
                # f.write(response.text)
            # print(response.text)
            # print(urls, len(urls))

            if len(urls) == 0:
                self.log(f"retrying {response.url}, page {idx}")

                self.driver.refresh()
                page_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'span.layui-laypage-skip input.layui-input'))
                )

                # 输入目标页码，比如第5页
                page_input.clear()  # 清空输入框
                page_input.send_keys(str(idx))  # 输入目标页码

                # 找到并点击“确定”按钮
                confirm_button = self.driver.find_element(By.CSS_SELECTOR, 'span.layui-laypage-skip button.layui-laypage-btn')
                confirm_button.click()
                time.sleep(2)
                continue

            with open(response.url.split('/')[-1].split('.')[0] + '_urls.txt', 'a') as f:
                f.write('\n'.join(urls) + '\n')

            try:
                next_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.layui-laypage-next'))
                )

                if "disabled" in next_button.get_attribute("class"):
                    self.log(f"Finished crawling {response.url}, the last page is {idx}")
                    break

                next_button.click()
                time.sleep(2)
            except:
                self.log(f"retrying {response.url}, page {idx}")

                self.driver.refresh()
                page_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'span.layui-laypage-skip input.layui-input'))
                )

                # 输入目标页码，比如第5页
                page_input.clear()  # 清空输入框
                page_input.send_keys(str(idx))  # 输入目标页码

                # 找到并点击“确定”按钮
                confirm_button = self.driver.find_element(By.CSS_SELECTOR, 'span.layui-laypage-skip button.layui-laypage-btn')
                confirm_button.click()
                time.sleep(2) 

                break
            
            idx +=  1
            
        self.log(f"Unusual end of {response.url}, page {idx}")
    
    def __del__(self):
        self.driver.quit()
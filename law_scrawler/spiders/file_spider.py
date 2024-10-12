import scrapy
import requests
import os
from urllib.parse import urljoin
from selenium import webdriver
import time
from selenium.webdriver.support.ui import WebDriverWait

CATE = "xf"

class Logger():
    def __init__(self):
        if os.path.exists(f'result/logs/{CATE}_words_log.txt'):
            os.remove(f'result/logs/{CATE}_words_log.txt')
        if not os.path.exists('result/logs'):
            os.mkdir('result/logs')

    def log(self, msg):
        with open(f'result/logs/{CATE}_words_log.txt', 'a') as f:
            f.write(msg + '\n')

    def error(self, msg):
        with open(f'result/logs/{CATE}_words_log.txt', 'a') as f:
            f.write(f"[ERROR]: {msg}\n")

class FileSpiderSpider(scrapy.Spider):
    base_url = "https://flk.npc.gov.cn/{}.html"
    name = "file_spider"
    allowed_domains = ["flk.npc.gov.cn"]
    category = ["xf", "fl", "dfxfg"]
    start_urls = []

    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        self.driver = webdriver.Chrome(options=options)

        self.my_logger = Logger()
        self.urls = {}
        for c in self.category:
            with open(f"result/urls/{c}_urls.txt", 'r') as f:
                lines = f.readlines()
            self.urls[c] = [urljoin(self.base_url.format(c), line.strip()) for line in lines]
        self.start_urls = self.urls[CATE]

    def download_file(self, url, category):
        exit()
        self.driver.get(url)
        for i in range(10): 
            try:
                download_url = WebDriverWait(self.driver, 10).until(
                    lambda: self.driver.execute_script("return typeof window.getDownLoadUrl !== 'undefined' && getDownLoadUrl();")
                )

                if download_url:
                    download_filename = download_url.split('/')[-1]
                    response = requests.get(download_url)

                    if not os.path.exists(f"result/words/{category}"):
                        os.makedirs(f"result/words/{category}")

                    with open(os.path.join(f"result/words/{category}", download_filename), 'wb') as f:
                        f.write(response.content)

                    self.my_logger.log(f"downloaded {download_filename} from {url}")
                else:
                    raise Exception("Download URL is empty")
                
                return 
            except Exception as e:
                self.my_logger.log(f"{i}-th failure to download {url}: {e}")
                self.driver.get(url)
                time.sleep(2)  

        self.my_logger.error(f"Failed to download {url}")

    def parse(self, response):
        self.driver.implicitly_wait(10)
        self.download_file(response.url, CATE)
import scrapy
import requests
import os
from urllib.parse import urljoin
from selenium import webdriver
import time
from selenium.webdriver.support.ui import WebDriverWait
import re

class Logger():
    def __init__(self, category, remove_log):
        if remove_log and os.path.exists(f'result/logs/{category}_words_log.txt'):
            os.remove(f'result/logs/{category}_words_log.txt')
        if not os.path.exists('result/logs'):
            os.mkdir('result/logs')
        self.category = category

    def log(self, msg):
        with open(f'result/logs/{self.category}_words_log.txt', 'a') as f:
            f.write(msg + '\n')

    def error(self, msg):
        with open(f'result/logs/{self.category}_words_log.txt', 'a') as f:
            f.write(f"[ERROR]: {msg}\n")

class FileSpiderSpider(scrapy.Spider):
    base_url = "https://flk.npc.gov.cn/{}.html"
    name = "file_spider"
    allowed_domains = ["flk.npc.gov.cn"]
    category = ["xf", "fl", "dfxfg"]

    def __init__(self, category, resume: bool):
        resume = resume == 'True'
        self.my_logger = Logger(category, remove_log=not resume)
        self.category = category
        
        with open(f"result/urls/{category}_urls.txt", 'r') as f:
            lines = f.readlines()
        self.urls = [urljoin(self.base_url.format(category), line.strip()) for line in lines]

        if resume and os.path.exists(f"result/logs/{category}_words_log.txt"):
            with open(f"result/logs/{category}_words_log.txt", 'r') as f:
                context = f.read()
            finished_urls = re.findall(r"^downloaded .+? from (.+?)$", context, re.MULTILINE) 


            self.urls = [url for url in self.urls if url not in finished_urls]

        self.remaining_urls = len(self.urls)
    
    def _get_driver(self, headless):
        proxy_pool_url = "https://269900.xyz/fetch_https"
        for i in range(10):
            try:
                response = requests.get(proxy_pool_url)
                proxy = response.text

                if response.status_code != 200:
                    raise Exception("Failed to fetch proxy")
                break
            except Exception as e:
                self.my_logger.log(f"{i}-th failure to fetch proxy: {e}")
                pass  

        options = webdriver.ChromeOptions()
        options.add_argument(f'--proxy-server={proxy}')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--allow-insecure-localhost')  # 可选，针对本地自签名证书
        options.add_argument('--allow-running-insecure-content')  # 允许加载不安全的内容

        if headless:
            options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        return driver
 
    def start_requests(self):
        for url in self.urls:
            yield scrapy.Request(url, callback=self.parse)

    def download_file(self, url, category):
        driver = self._get_driver(True)
        driver.get(url)
        for i in range(10): 
            try:
                download_url = WebDriverWait(driver, 10).until(
                    lambda b: b.execute_script("return typeof window.getDownLoadUrl !== 'undefined' && getDownLoadUrl();")
                )

                if download_url:
                    download_filename = download_url.split('/')[-1]
                    response = requests.get(download_url)

                    if not os.path.exists(f"result/words/{category}"):
                        os.makedirs(f"result/words/{category}")

                    with open(os.path.join(f"result/words/{category}", download_filename), 'wb') as f:
                        f.write(response.content)

                    self.my_logger.log(f"downloaded {download_filename} from {url}")
                    self.remaining_urls -= 1
                    self.my_logger.log(f"remaining urls: {self.remaining_urls}")
                else:
                    raise Exception("Download URL is empty")
                
                return 
            except Exception as e:
                self.my_logger.log(f"{i}-th failure to download {url}: {e}")
                driver.quit()
                driver = self._get_driver(True)
                driver.get(url)
                time.sleep(2)  

        self.my_logger.error(f"Failed to download {url}")
        time.sleep(10)

    def parse(self, response):
        self.download_file(response.url, self.category)
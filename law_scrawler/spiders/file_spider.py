import scrapy
import os
from urllib.parse import urljoin
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
import re
import asyncio
import aiohttp
import aiofiles
import random
import pywifi
from pywifi import const
import subprocess
from docx import Document

class Logger():
    def __init__(self, category, remove_log):
        if remove_log and os.path.exists(f'result/logs/{category}_words_log.txt'):
            os.remove(f'result/logs/{category}_words_log.txt')
        os.makedirs('result/logs', exist_ok=True)
        os.makedirs('result/file_urls', exist_ok=True)
        self.category = category

    def log(self, msg):
        with open(f'result/logs/{self.category}_words_log.txt', 'a') as f:
            f.write(msg + '\n')

    def error(self, msg):
        with open(f'result/logs/{self.category}_words_log.txt', 'a') as f:
            f.write(f"[ERROR]: {msg}\n")

    def save_url(self, url):
        with open(f'result/file_urls/{self.category}_file_urls.txt', 'a') as f:
            f.write(url + '\n')

class FileSpiderSpider(scrapy.Spider):
    base_url = "https://flk.npc.gov.cn/{}.html"
    name = "file_spider"
    allowed_domains = ["flk.npc.gov.cn"]
    category = ["xf", "fl", "dfxfg"]

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        return cls(user_agent=crawler.settings.get('USER_AGENT_LIST'), proxy=crawler.settings.get('PROXY_LIST'), crawler=crawler, *args, **kwargs)

    def __init__(self, user_agent, proxy, crawler, category, resume: bool, *args, **kwargs):
        super(FileSpiderSpider, self).__init__(*args, **kwargs)

        self.crawler = crawler
        self.user_agent = user_agent
        self.proxy = proxy
        resume = resume == 'True'
        self.my_logger = Logger(category, remove_log=not resume)
        self.category = category

        with open(f"result/urls/{category}_urls.txt", 'r') as f:
            lines = f.readlines()
        self.urls = [urljoin(self.base_url.format(category), line.strip()) for line in lines]

        if resume and os.path.exists(f"result/logs/{category}_words_log.txt"):
            with open(f"result/logs/{category}_words_log.txt", 'r') as f:
                context = f.read()
            finished_urls = re.findall(r"^[Dd]ownloaded .+? from (.+?)$", context, re.MULTILINE) 

            self.urls = [url for url in self.urls if url not in finished_urls]

        self.remaining_urls = len(self.urls)

        # self.start_urls = ["https://www.httpbin.org/get"]
    
    def start_requests(self):
        for url in self.urls:
            yield scrapy.Request(url, callback=self.parse)

    async def _get_driver(self, headless=True, use_dynamic_proxy=False, save_dir=None):
        options = webdriver.ChromeOptions()

        # set download path
        options.add_experimental_option("prefs", {
           "download.default_directory": save_dir,
        })

        if use_dynamic_proxy:
            proxy_pool_url = "https://269900.xyz/fetch_random?region=cn"
            for i in range(10):
                try:
                    async with aiohttp.request('GET', proxy_pool_url) as response:
                        if response.status != 200:
                            raise Exception("Failed to fetch proxy")
                        proxy = await response.text()
                    break
                except Exception as e:
                    self.my_logger.log(f"{i}-th failure to fetch proxy")
        else:
            proxy = random.choice(self.proxy)

        user_agent = random.choice(self.user_agent)
        # self.my_logger.log(f"use proxy: {proxy}")
        # self.my_logger.log(f"use user agent: {user_agent}")
        if proxy != "direct":
            options.add_argument(f'--proxy-server={proxy}')
        options.add_argument(f'--user-agent={user_agent}')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--allow-insecure-localhost') 
        options.add_argument('--allow-running-insecure-content') 

        if headless:
            options.add_argument('--headless')

        driver = webdriver.Chrome(options=options)
        return driver

    async def download_file(self, url, category):
        self.my_logger.log(f"Downloading {url}")
        driver = await self._get_driver() 
        driver.get(url)
        
        for i in range(7):
            if driver.current_url == "https://flk.npc.gov.cn/waf_text_verify.html":
                time.sleep(500)

            try:
                await asyncio.sleep(random.randint(1, 2 ** i)) 

                download_url = driver.execute_script("return getDownLoadUrl();")
                if download_url:
                    download_filename = download_url.split('/')[-1]
                    save_dir = f"result/words/{category}"
                    
                    if not os.path.exists(save_dir):
                        os.makedirs(save_dir)

                    if await self.save_file(download_url, save_dir, download_filename):
                        self.remaining_urls -= 1
                        self.my_logger.log(f"Downloaded {download_filename} from {url}\nRemaining URLs: {self.remaining_urls}")
                        self.my_logger.save_url(download_url)
                    else:
                        raise Exception(f"Failed to download file {download_filename} from {url}")
                    
                    return
                else:
                    raise Exception("Download URL is empty")
            
            except Exception as e:
                self.my_logger.log(f"{i}-th failure to download {url}: {e}")
                driver.quit()
                driver = await self._get_driver()
                driver.get(url)

        self.my_logger.error(f"Failed to download {url}")
        time.sleep(600)

    def is_valid_word_file(self, file_path):
        if not file_path.endswith('.docx'):
            return True
        try:
            doc = Document(file_path)
            return True
        except Exception:
            return False
    
    async def save_file(self, url, save_dir, filename):
        driver = await self._get_driver(True, False, save_dir=os.path.abspath(save_dir))
        driver.get(url)
        await asyncio.sleep(10)

        return self.is_valid_word_file(os.path.join(save_dir, filename))

    async def parse(self, response):
        await self.download_file(response.url, self.category) 
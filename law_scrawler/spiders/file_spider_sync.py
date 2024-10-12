import scrapy
import asyncio
from playwright.async_api import async_playwright
import requests
import os
from urllib.parse import urljoin
import time

CATE = "xf"

class Logger():
    def __init__(self):
        if(os.path.exists(f'result/logs/{CATE}_words_log.txt')):
            os.remove(f'result/logs/{CATE}_words_log.txt')
        if not (os.path.exists('result/logs')):
            os.mkdir('result/logs')

    def log(self, msg):
        with open('result/logs/words_log.txt', 'a') as f:
            f.write(msg + '\n')

    def error(self, msg):
        with open('result/logs/words_log.txt', 'a') as f:
            f.write(f"[ERROR]: {msg}\n")

class FileSpiderSpider(scrapy.Spider):
    base_url = "https://flk.npc.gov.cn/{}.html"
    name = "file_spider"
    allowed_domains = ["flk.npc.gov.cn"]
    category = ["xf", "fl", "dfxfg"]
    start_urls = []

    def __init__(self):
        self.my_logger = Logger()
        self.urls = {}
        for c in self.category:
            with open(f"result/urls/{c}_urls.txt", 'r') as f:
                lines = f.readlines()
            self.urls[c] = [urljoin(self.base_url.format(c), line.strip()) for line in lines]
        self.start_urls = self.urls[CATE] 
        self.semaphore = asyncio.Semaphore(10)

    async def download_file(self, url, catogery, semaphore):
        async with semaphore:
            for i in range(10):
                try:
                    async with async_playwright() as p:
                        browser = await p.chromium.launch()
                        page = await browser.new_page()

                        await page.goto(url)
                        await page.wait_for_function('window.getDownLoadUrl !== undefined')
                        await page.wait_for_function("typeof window.$ !== 'undefined'")

                        download_url = await page.evaluate("getDownLoadUrl();")
                        if download_url:
                            download_filename = download_url.split('/')[-1]
                            response = requests.get(download_url)
                            
                            if not os.path.exists(f"result/words/{catogery}"):
                                os.makedirs(f"result/words/{catogery}")
                            with open(os.path.join(f"result/words/{catogery}", download_filename), 'wb') as f:
                                f.write(response.content)
                            self.my_logger.log(f"downloaded {download_filename} from {url}")
                        else:
                            raise Exception("download url is empty")
                        await browser.close()
                    return
                except Exception as e:
                    self.my_logger.log(f"{i}-th failure to download {url}: {e}")
                    await asyncio.sleep(5)

            self.my_logger.error(f"failed to download {url}")

    async def parse(self, response):
        await self.download_file(response.url, CATE, self.semaphore)
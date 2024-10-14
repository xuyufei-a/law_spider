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

    def _reset_network(self):
        return
        ssid = "wifi"
        password = "qqxxyyff"
        
        wifi = pywifi.PyWiFi()
        iface = wifi.interfaces()[0]
        profile = pywifi.Profile()
        profile.ssid = ssid
        profile.auth = const.AUTH_ALG_OPEN
        profile.akm.append(const.AKM_TYPE_WPA2PSK)
        profile.cipher = const.CIPHER_TYPE_CCMP
        profile.key = password

        iface.remove_all_network_profiles()
        tmp_profile = iface.add_network_profile(profile)
        iface.connect(tmp_profile)  

        time.sleep(3)
        for i in range(10):
            if iface.status() != const.IFACE_CONNECTED:
                time.sleep(1)
            else:
                return
        
        self.my_logger.log("fail to reset wifi")


    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        return cls(user_agent=crawler.settings.get('USER_AGENT_LIST'), proxy=crawler.settings.get('PROXY_LIST'), *args, **kwargs)

    def __init__(self, user_agent, proxy, category, resume: bool):
        super(FileSpiderSpider, self).__init__()

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

    async def _get_driver(self, headless=True, use_dynamic_proxy=False):
        options = webdriver.ChromeOptions()

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
                self._reset_network()
            
            try:
                # await asyncio.sleep(random.randint(1, 2 ** i)) 
                await asyncio.sleep(2 + i)
                download_url = driver.execute_script("return getDownLoadUrl();")
                if download_url:
                    download_filename = download_url.split('/')[-1]
                    
                    async with aiohttp.request('GET', download_url) as response:
                        if response.status == 200:
                            content = await response.read()

                            if not os.path.exists(f"result/words/{category}"):
                                os.makedirs(f"result/words/{category}")

                            # file_path = os.path.join(f"result/words/{category}", download_filename)
                            # async with aiofiles.open(file_path, 'wb') as f:
                            #     await f.write(content)

                            self.remaining_urls -= 1
                            self.my_logger.log(f"Downloaded {download_filename} from {url}\nRemaining URLs: {self.remaining_urls}")
                            self.my_logger.save_url(download_url)

                            if self.remaining_urls % 10 == 0:
                                self._reset_network()
                        else:
                            raise Exception(f"Failed to download file, status code: {response.status}")
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

    async def parse(self, response):
        await self.download_file(response.url, self.category) 
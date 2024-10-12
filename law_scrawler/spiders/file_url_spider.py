import asyncio
from playwright.async_api import async_playwright
import requests
import os
from urllib.parse import urljoin
import time

class logger():
    def __init__(self):
        if(os.path.exists('result/logs/words_log.txt')):
            os.remove('result/logs/words_log.txt')
        if not (os.path.exists('result/logs')):
            os.mkdir('result/logs')

    def log(self, msg):
        with open('result/logs/words_log.txt', 'a') as f:
            f.write(msg + '\n')

    def error(self, msg):
        with open('result/logs/words_log.txt', 'a') as f:
            f.write(f"[ERROR]: {msg}\n")

class spider():
    base_url = "https://flk.npc.gov.cn/{}.html"
    category = ["xf", "fl", "dfxfg"]

    def __init__(self):
        self.logger = logger()
        
        self.urls = {}
        for c in self.category:
            with open(f"result/urls/{c}_urls.txt", 'r') as f:
                lines = f.readlines()
            self.urls[c] = [urljoin(self.base_url.format(c), line.strip()) for line in lines]

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
                            self.logger.log(f"downloaded {download_filename} from {url}")
                        else:
                            raise Exception("download url is empty")
                        await browser.close()
                    return
                except Exception as e:
                    self.logger.log(f"{i}-th failure to download {url}: {e}")
                    time.sleep(5)

            self.logger.error(f"failed to download {url}")
    
    async def download_files(self):
        semaphore = asyncio.Semaphore(9)

        tasks = []
        for catogery, urls in self.urls.items():
            self.logger.log(f"start to add {catogery} task")
            for url in urls:
                task = asyncio.create_task(self.download_file(url, catogery, semaphore))
                tasks.append(task)
            self.logger.log(f"finish adding {catogery} task")

        return await asyncio.gather(*tasks)
    
    def run(self):
        asyncio.run(self.download_files())


if __name__ == '__main__':
    s = spider()
    s.run()
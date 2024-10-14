import scrapy
import requests
from docx import Document
import argparse
import time
import random
import os
import re
from selenium import webdriver

class Logger():
    def __init__(self, log_file, remove_log=True):
        self.log_file = log_file
        if remove_log and os.path.exists(log_file):
            os.remove(log_file)
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

    def log(self, message):
        with open(self.log_file, 'a') as f:
            f.write(message + '\n')
    
    def error(self, message):
        with open(self.log_file, 'a') as f:
            f.write(f"[ERROR]: {message}\n")

class DownloadSpiderSpider(scrapy.Spider):
    name = "download_spider"
    allowed_domains = ["flk.npc.gov.cn"]

    def __init__(self, urls_path, files_path, log_file, resume=False):
        if resume == False:
            with open(urls_path, 'r') as f:
                self.start_urls = [line.strip() for line in f.readlines()]
            self.files_path = files_path
            os.makedirs(files_path, exist_ok=True)
            self.my_logger = Logger(log_file, remove_log=True)
        else:
            with open(log_file, 'r') as f:
                content = f.read()
            self.start_urls = re.findall(r"[ERROR]: Failed to download .+? from (.+?)#", content, re.MULTILINE)
            self.my_logger = Logger(log_file, remove_log=False)

    def is_valid_word_file(self, file_path):
        if not file_path.endswith('.docx'):
            return True
        try:
            doc = Document(file_path)
            return True
        except Exception:
            return False
    
    def parse(self, response):
        url = response.url
        file_name = url.split('/')[-1]

        for i in range(10):
            driver = webdriver.Chrome()
            driver.get(url)
            with open(os.path.join(self.files_path, file_name), 'wb') as f:
                f.write(response.body)

            if self.is_valid_word_file(os.path.join(self.files_path, file_name)):
                self.my_logger.log(f"Downloaded {file_name} from {url}")
                break
        
            if i == 9:
                self.my_logger.error(f"Failed to download {file_name} from {url}")

# scrapy crawl download_spider -a urls_path=process/result/urls/fl_urls.txt -a files_path=flies/fl -a log_file=files/logs/fl_logs.txt
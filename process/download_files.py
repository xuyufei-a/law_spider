import requests
from docx import Document
import argparse
import time
import random
import os
import wget
import subprocess
from tqdm import tqdm

def is_valid_word_file(file_path):
    if not file_path.endswith('.docx'):
        return True
    try:
        doc = Document(file_path)
        return True
    except Exception:
        return False

def main(CATEGORY):
    with open(f"result/urls/{CATEGORY}_urls.txt", 'r') as f:
        urls = [line.strip() for line in f.readlines()]

    cnt = 0
    for url in tqdm(urls):
        file_name = url.split('/')[-1]
        save_path = f"D:\Documents/python_work/law_scrawler/process/result/files/{CATEGORY}/{file_name}"
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        command = [
            "D:\Internet Download Manager\IDMan.exe",
            "/d", url,
            "/p", os.path.dirname(save_path),
            "/f", file_name,
            "/n",
            '/hiden',
            '/s'
        ]

        for i in range(10):
            if is_valid_word_file(save_path):
                cnt += 1
                break

            subprocess.run(command)
            if i == 9:
                print(f"Failed to download {file_name} from {url}")

    print(f'successfully downloaded {cnt} files') 

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--category', type=str, required=True)
    args = parser.parse_args() 

    main(args.category)
import requests
from docx import Document
import argparse
import time
import random
import os
import wget
import subprocess

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
    
    path = f"result/files/{CATEGORY}"

    for file_name in os.listdir(path):
        if not is_valid_word_file(os.path.join(path, file_name)):
            name = file_name.split('.')[0]

            for url in urls:
                if name in url:
                    print(f"{file_name} is not a valid word file, url: {url}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--category', type=str, required=True)
    args = parser.parse_args() 

    main(args.category)
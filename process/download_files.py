import requests
from docx import Document

def is_valid_word_file(file_path):
    try:
        doc = Document(file_path)
        return True
    except Exception:
        return False

def main(CATEGORY):
    with open(f"result/urls/{CATEGORY}_urls.txt", 'r') as f:
        urls = [line.strip() for line in f.readlines()]

    for url in urls:
        file_name = url.split('/')[-1]
        save_path = f"result/files/{CATEGORY}/{file_name}"

        while True: 
            response = requests.get(url)
            with open(save_path, 'wb') as f:
                f.write(response.content)

            if is_valid_word_file(save_path):
                break


if __name__ == "__main__":
    category = 'fl'
    main(category)
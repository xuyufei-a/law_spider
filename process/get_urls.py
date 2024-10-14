import argparse
import re

def get_urls(log_path, base_url, save_path):
    with open(log_path, 'r') as f:
        context = f.read()
    filenames = re.findall(r"^[Dd]ownloaded (.+?) from .+?$", context, re.MULTILINE)

    def _get_type_dir(file_name):
        t = file_name.split('.')[-1]

        if t == 'pdf':
            return 'PDF'
        else:
            return 'WORD'

    urls = [base_url + _get_type_dir(file_name)  + '/' + file_name for file_name in filenames]  
    urls = list(set(urls))

    with open(save_path, 'w') as f:
        for url in urls:
            f.write(url + '\n')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--log_path', type=str, required=True)

    # https://wb.flk.npc.gov.cn/flfg/
    # https://wb.flk.npc.gov.cn/dfxfg/
    parser.add_argument('--base_url', type=str, required=True)
    parser.add_argument('--save_path', type=str, required=True)

    args = parser.parse_args()
    get_urls(args.log_path, args.base_url, args.save_path)

    # python .\get_urls.py --log_path ..\result\logs\fl_words_log.txt --base_url 'https://wb.flk.npc.gov.cn/flfg/' --save_path .\result\urls\fl_urls.txt
    # python .\get_urls.py --log_path ..\result\logs\dfxfg_words_log.txt --base_url 'https://wb.flk.npc.gov.cn/dfxfg/' --save_path .\result\urls\dfxfg_urls.txt
    # python .\get_urls.py --log_path ..\result\logs\xf_words_log.txt --base_url 'https://wb.flk.npc.gov.cn/xffl/' --save_path .\result\urls\xf_urls.txt
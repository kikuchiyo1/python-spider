import requests
import re
import time
import random
import os
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

MAX_THREADS = 5  # 最多5线程
RETRY_TIMES = 3
SLEEP_BETWEEN_RETRIES = 2

class Colors:
    RED = '\033[1;91m'
    GREEN = '\033[92m'
    LIGHT = '\033[1m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    l_BLUE = '\033[36m'

class NovelGetter:
    def __init__(self):
        self.base_url = 'http://www.xbiqushu.com'
        self.session = requests.Session()
        cookies = {
            "getsite": "afb0ab732.xyz",
            "hm": "3c84707a53fc1c688539e6ffcd1e5423",
            "hmt": "1758905695"
        }
        self.session.cookies.update(cookies)

    def get_novel_dict(self, q: str):
        books_dict = {}

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            "Referer": "http://www.xbiqushu.com/",
            "Origin": "http://www.xbiqushu.com",
        }
        data = {
            "searchkey": q,
        }
        time.sleep(random.uniform(0.5, 1))
        resp = self.session.post(self.base_url + '/search/', headers=headers, data=data)
        resp.encoding = 'utf-8'
        html = resp.text
        soup = BeautifulSoup(html, "lxml")
        for box in soup.select(".bookbox"):
            title = box.select_one(".bookname").text.strip()
            author = box.select(".author")[0].text.strip()
            reading = box.select(".author")[1].text.strip()
            new_page = box.select("a")[1].text
            url = self.base_url + box.select("a")[0].attrs['href']

            books_dict[title] = {"author": author, "reading": reading, "new_page": new_page, "url": url, "order": 0}
        # 排序
        sorted_books = dict(
            sorted(
                books_dict.items(),
                key=lambda x: int(re.sub(r'\D', '', x[1]['reading'])),
                reverse=True
            )
        )
        temp: int = 0
        for title, data in sorted_books.items():
            temp += 1
            data['order'] = temp
        return sorted_books

    def get_content_list(self, url: str):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        }
        time.sleep(random.uniform(0.5, 1))
        resp = self.session.get(url, headers=headers)
        content_list = []
        soup = BeautifulSoup(resp.text, "lxml")
        for i in soup.select("#list-chapterAll dd a"):
            title: str = i.text.strip()
            url: str = self.base_url + i.attrs['href']
            content_list.append((title, url))
            base, ext = url.rsplit(".", 1)
            url = base + '_2.' + ext
            content_list.append((title + "(2)", url))
        return content_list

    def fetch_chapter(self, title, url, index, novel_dir: str):
        safe_title = f"{index:04d}_{title}.txt"
        filepath = os.path.join(novel_dir, safe_title)
        for a in range(RETRY_TIMES):
            try:
                time.sleep(random.uniform(0.6, 1.2))
                resp = self.session.get(url, timeout=15)
                resp.encoding = 'utf-8'
                soup = BeautifulSoup(resp.text, "lxml")
                paragraphs = [p.get_text(strip=True) for p in soup.select(".readcontent p")]
                text = "\n".join(paragraphs)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(text)
                print(f"{Colors.GREEN}下载完成：{title}{Colors.RESET}")
                return
            except Exception as e:
                print(f"{Colors.RED}下载失败：{title}{Colors.RESET}")

    def download_all_chapters(self, content_list, book_name: str='books'):
        os.makedirs(book_name, exist_ok=True)
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = {executor.submit(self.fetch_chapter, title, url, idx ,book_name):
                           (title, url, idx) for idx, (title, url) in enumerate(content_list, 1)}

            completed = 0
            for future in as_completed(futures):
                title, url, idx = futures[future]
                try:
                    result = future.result()
                    if result:
                        completed += 1
                except Exception as e:
                    print(f"{Colors.RED}章节下载异常：{title}，错误：{e}{Colors.RESET}")

            print(f"{Colors.GREEN}所有章节下载完成{Colors.RESET}")

    #合并章节
    def merge_chapters(self,novel_title: str):
        os.makedirs(novel_title, exist_ok=True)
        files = [f for f in os.listdir(novel_title) if f.endswith('.txt')]
        files.sort()
        with open(f"{novel_title}_full.txt",'w',encoding='utf-8') as f_out:
            for file in files:
                with open(os.path.join(novel_title,file), 'r', encoding='utf-8') as f_in:
                    f_out.write(f_in.read()+"\n\n")
        print(f"{Colors.GREEN}合并完成{Colors.RESET}")

def main() -> None:
    novel = NovelGetter()
    while True:
        print(
            Colors.GREEN + 'Ciallo～(∠・ω< )⌒★' + Colors.RESET + '\n' + Colors.LIGHT + '温馨提示：搜索间隔为30s 尽量输入全名 可以少写不要缩写 握握手🤝握握双手🤝' + Colors.RESET + '\n请输入想搜索的小说 (输入q退出)')
        q: str = input()
        if q == 'q':
            break
        print('⌛️' * 10 + Colors.RED + '少女祈祷中' + Colors.RESET + '⌛️' * 10)
        books_dict = novel.get_novel_dict(q)
        index_map = {}
        if not books_dict:
            print(Colors.RED + 'ERROR: 搜索无结果或触发30s搜索限制' + Colors.RESET)
            continue
        for title, data in books_dict.items():
            num = re.search(r'\d+', data['reading']).group() if data['reading'] and re.search(r'\d+',
                                                                                              data['reading']) else ""
            print(
                f"{Colors.LIGHT + str(data['order']) + Colors.RESET}. {Colors.l_BLUE + title + Colors.RESET} {data['author']} 阅读量：{Colors.l_BLUE + str(num) + Colors.RESET} 最新章节：{data['new_page']}\n")
            index_map[str(data['order'])] = title
        while True:
            try:
                ask: str = input('请输入想要下载小说的序号(输入q返回上一步)\n')
                if ask == 'q':
                    break
                elif ask not in index_map:
                    print(Colors.RED + '序号无效' + Colors.RESET)
                    break
                else:
                    content_list = novel.get_content_list(books_dict[index_map[ask]]['url'])
                    novel.download_all_chapters(content_list,str(index_map[ask]))
                    novel.merge_chapters(str(index_map[ask]))

            except  Exception as e:
                print(Colors.RED + '发生未知错误' + Colors.RESET)

if __name__ == '__main__':
    main()

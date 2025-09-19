import random
import requests
import time
import re
import os


#配置获取类
class Config:
    def __init__(self, file_path="config.txt"):
        self.config = {}
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"配置文件 {file_path} 不存在！")

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):  # 跳过空行和注释
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    self.config[key.strip()] = value.strip()

    def get(self, key, default=None):
        return self.config.get(key, default)

config = Config("config.txt")
QB_URL = config.get("QB_URL")
USERNAME = config.get("USERNAME")
PASSWORD = config.get("PASSWORD")
SAVE_PATH = config.get("SAVE_PATH", "D:/番剧")
#下载类
class QBittorrentClient:
    def __init__(self, url=QB_URL, username=USERNAME, password=PASSWORD):
        self.session = requests.Session()
        self.url = url
        self.login(username, password)

    def login(self, username, password):
        r = self.session.post(f"{self.url}/api/v2/auth/login",
                              data={"username": username, "password": password})
        if r.text != "Ok.":
            raise Exception("qBittorrent 登录失败，请检查用户名/密码")

    def add_magnet(self, magnet, save_path=None):
        data = {"urls": magnet}
        if save_path:
            data["savepath"] = save_path
        r = self.session.post(f"{self.url}/api/v2/torrents/add", data=data)
        if r.status_code == 200:
            print("已添加下载任务:", magnet)
        else:
            print("添加失败:", r.text)

class Colors:
    RED = '\033[1;91m'
    GREEN = '\033[92m'
    LIGHT = '\033[1m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    l_BLUE = '\033[36m'

class AnimeGetter:
    def __init__(self):
        self.base_url = 'https://www.kisssub.org/search.php'
        self.session = requests.Session()
        self.session.cookies.set('visitor_test', 'human', domain='www.kisssub.org')
        self.headers = {
            'authority': 'www.kisssub.org',
            'method': 'GET',
            'scheme': 'https',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'cache-control': 'max-age=0',
            'priority': 'u=0, i',
            'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
        }

    def get_num(self,keyword):
        params = {'keyword': keyword}
        time.sleep(random.uniform(0.2, 1))
        rule3 = re.compile(r'共找到(?P<num>.*?)条匹配资源', re.S)
        try:
            resp = self.session.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=10
            )
            content = resp.text
            result = rule3.search(content)
            num = int(result.group('num'))
            resp.close()
            return int(num)
        except Exception as e:
            print('发生未知错误')

    def get_page(self,num):
        if num % 50 != 0:
            page = (num - num%50)/50 + 1
        else:
            page = num/50
        return int(page)

    def get_anime_url(self, keyword, page):
        const = 0
        magnet = []
        qb = QBittorrentClient()
        rule1 = re.compile(r'<td nowrap="nowrap">.*?<td style="text-align:left;">.*?'
                           r'<a href="(?P<child_url>.*?)" target="_blank">(?P<name>.*?)</a>', re.S)
        rule2 = re.compile(r'<li><a id="magnet" href="(?P<download>.*?)&tr', re.S)

        params = {'keyword': keyword ,'page': page}
        time.sleep(random.uniform(0.2, 1))

        child_href_list = []
        try:
            resp = self.session.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=10
            )
            content = resp.text
            result = rule1.finditer(content)
            resp.close()
            for it in result:
                child_href = 'https://www.kisssub.org/' + it.group('child_url')
                child_href_list.append(child_href)
                new_name = it.group('name').replace('<span class="keyword">', '')
                final_name = new_name.replace('</span>', '')

                try:
                    resp1 = self.session.get(
                        child_href,
                        params=params,
                        headers=self.headers,
                        timeout=10
                    )
                    content1 = resp1.text
                    result1 = rule2.search(content1)
                    magnet.append(result1.group('download'))
                    const+=1
                    print(Colors.RED+str(const)+'. '+Colors.RESET+final_name.strip()+'\n磁力链接: '+Colors.l_BLUE+result1.group('download')+Colors.RESET+'\n')
                    resp1.close()
                except Exception as e:
                    print('资源获取异常')
            while True:
                num = input('请输入要下载资源的序号,输入q退出')
                if num == 'q':
                    break
                else:
                    qb.add_magnet(magnet[int(num)+1], save_path=SAVE_PATH)



        except Exception as e:
            print('搜索过程发生错误')


def main():
    anime_getter = AnimeGetter()
    while True:
        print(Colors.GREEN+'Ciallo～(∠・ω< )⌒★'+Colors.RESET+'\n'+Colors.LIGHT+'温馨提示：尽量输入全名 可以少写不要缩写 握握手🤝握握双手🤝'+Colors.RESET+'\n请输入想搜索的番剧 (输入q退出)')
        anime_name = input()
        if anime_name == 'q':
            break
        else:
            print('⌛️'*10+Colors.RED+'少女祈祷中'+Colors.RESET+'⌛️'*10)
            num = anime_getter.get_num(anime_name)
            page = anime_getter.get_page(num)
            if page > 1 :
                while True:
                    try:
                        print('=' * 60)
                        print(f'搜索关键词\033[1m「\033[0m\033[1;91m{anime_name}\033'
                              f'[0m\033[1m」\033[0m有 \033[91m{page}\033[0m页 共 \033[91m{num}\033[0m'
                            f'条 结果\n请问要显示哪一页? (输入q返回上一步)')
                        search_page = input()
                        if search_page == 'q':
                            break
                        if int(search_page) > page or int(search_page) < 1:
                            raise ValueError('请输入正确的页码!')
                        anime_getter.get_anime_url(anime_name, int(search_page))
                    except Exception as e:
                        print(Colors.RED+'请输入正确的页码!'+Colors.RESET)
            else:
                anime_getter.get_anime_url(anime_name, page)


if __name__ == '__main__':
    main()
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import re
import shogi.KIF
options = Options()
options.binary_location = "/usr/bin/google-chrome"
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("window-size=1280x800")
options.add_argument("--start-maximized")
driver = webdriver.Chrome("chromedriver", chrome_options=options)
from tqdm import tqdm

BASE_URL = "https://shogidb2.com"
FMT_NEWEST_KIF_URL = "https://shogidb2.com/latest/page/{page}"
FMT_FLOODGATE_KIF_URL = "https://shogidb2.com/floodgate/page/{page}"


def get_newest_kif_url_list(base, page=1):

    url = base.format(page=page)
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "lxml")

    kif_urls = []
    for a_tag in soup.find_all("a"):
        url = a_tag.get("href")
        if url is not None and 'games/' in url:
            url = BASE_URL + url
            kif_urls.append(url)
    return kif_urls


def get_kif(url):
    kif_id = url.split('/')[-1]
    filename = 'kif/{}.kif'.format(kif_id)
    """
    if os.path.exists(filename):
        try:
            shogi.KIF.Parser.parse_file(filename)
            return
        except Exception:
            pass
    """
    driver.get(url)

    kif = driver.execute_script('return new KifExporter(data)["export"]()')
    new_kif = []
    cnt = 0
    for line in kif.split("\n"):
        if re.match("^[0-9]", line) is not None:
            cnt += 1
            tmp = line.split(" ")
            num = tmp[0]
            move = tmp[1]
            move = re.sub('　+', '　', move)
            while len(num) < 4:
                num = ' ' + num
            line = ' '.join([num, move])
        new_kif.append(line)
    kif = "\n".join(new_kif)
    with open(filename, 'wb') as f:
        f.write(kif.encode('cp932'))


for i in range(1, 1001):
    print(i)
    urls = get_newest_kif_url_list(FMT_NEWEST_KIF_URL, page=i)
    for url in tqdm(urls):
        get_kif(url)
        time.sleep(1)

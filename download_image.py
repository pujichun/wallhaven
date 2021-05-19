import requests
from requests.exceptions import RequestException
from lxml import etree
from typing import List
from rich.progress import Progress


def download_html(url) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            return resp.content.decode("utf8")
        return ""
    except RequestException:
        return ""


def parse_image_link(html: str) -> List:
    element = etree.HTML(html)
    links = element.xpath('//img[@alt="loading"]/@data-src')
    return links


def image_link_process(image_link: str) -> str:
    # https://w.wallhaven.cc/full/v9/wallhaven-v9gk6l.jpg
    # https://th.wallhaven.cc/small/v9/v9gk6l.jpg
    if "small" in image_link:
        image_link = image_link.replace("th", "w")
        image_link = image_link.replace("small", "full")
        url_path = image_link.split("/")
        url_path[-1] = f"wallhaven-{url_path[-1]}"
        return "/".join(url_path)
    return ""


def download_image(image_link):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
    }
    resp = requests.get(image_link, headers=headers, stream=True)
    try:
        file_size = int(resp.headers['content-length'])
        if resp.status_code == 200:
            with open(file=f'images/{image_link.split("/")[-1]}', mode="wb") as f:
                with Progress() as progress:
                    task1 = progress.add_task(f'[red]Downloading...{f.name}', total=file_size)
                    for chunk in resp.iter_content(chunk_size=1024):
                        f.write(chunk)
                        progress.update(task1, advance=1024)
        else:
            print("No")
    except:
        pass


def run():
    link_list = []
    for i in range(1, 9):
        url = f"https://wallhaven.cc/search?q=like%3Arddgwm&page={i}"
        html = download_html(url)
        links = parse_image_link(html)
        link_list.extend(links)
    for image_link in link_list:
        image_link = image_link_process(image_link)
        download_image(image_link)


if __name__ == '__main__':
    run()

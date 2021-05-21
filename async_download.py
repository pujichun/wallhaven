import asyncio
import aiohttp
from aiohttp import ClientSession
from lxml import etree
import aiofiles
from aiohttp.client_exceptions import ClientResponseError
from rich.progress import Progress


class WallHaven(object):
    def __init__(self) -> None:
        self.base_url = "https://wallhaven.cc/search?q=like%3Arddgwm&page="
        self.progress = Progress()

    async def get_list_image_page(self, session: ClientSession, url: str) -> None:
        """获取图片列表页"""
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    html = await resp.text(encoding="utf8")
                    if html:
                        await self.parse_image_link(session, html)
                    return
                return
        except ClientResponseError:
            return

    async def parse_image_link(self, session: ClientSession, html: str) -> None:
        """解析列表页小图链接"""
        element = etree.HTML(html)
        links = element.xpath('//img[@alt="loading"]/@data-src')
        for image_link in links:
            image_link = await self.image_link_process(image_link)
            await self.download_image(session, image_link)

    @staticmethod
    async def image_link_process(image_link: str) -> str:
        """转换图片链接"""
        if "small" in image_link:
            image_link = image_link.replace("th", "w")
            image_link = image_link.replace("small", "full")
            url_path = image_link.split("/")
            url_path[-1] = f"wallhaven-{url_path[-1]}"
            image_link = "/".join(url_path)
            return image_link

    async def download_image(self, session: ClientSession, image_link: str) -> None:
        """下载图片"""
        async with session.get(image_link) as resp:
            try:
                # 获取图片字节总长度
                file_size = int(resp.headers['content-length'])
                if resp.status == 200:
                    file_name = image_link.split("/")[-1]
                    async with aiofiles.open(file=f"images/{file_name}", mode="ab") as f:
                        self.progress.start()
                        task = self.progress.add_task(f'[red]Downloading...{file_name}', total=file_size)
                        while True:
                            chunk = await resp.content.read(1024)
                            if not chunk:
                                break
                            await f.write(chunk)
                            self.progress.update(task, advance=1024)
                        self.progress.stop()
            except Exception:
                return

    async def run(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
        }
        # 限制最大连接数
        async with aiohttp.TCPConnector(
                limit=200,
                force_close=True,
                enable_cleanup_closed=True, ) as tc:
            # 创建session对象
            async with ClientSession(connector=tc, headers=headers) as session:
                urls = [f"{self.base_url}{i}" for i in range(1, 9)]
                # 创建任务
                tasks = [asyncio.ensure_future(self.get_list_image_page(session, url)) for url in urls]
                # 等待任务完成
                await asyncio.gather(*tasks)


if __name__ == '__main__':
    wh = WallHaven()
    asyncio.run(wh.run())

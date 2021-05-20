实不相瞒，作为一个喜欢收集壁纸的boy，我盯上[wallhaven](https://wallhaven.cc/)很久了

你可能觉得我在说这种风格的![](https://w.wallhaven.cc/full/8o/wallhaven-8ogk2o.jpg)

实不相瞒我其实不喜欢，我喜欢的是这种

![](https://w.wallhaven.cc/full/95/wallhaven-95qjpd.jpg)

哈哈哈~anyways！

起因是我的电脑用的是动态壁纸（写了个自动切换的shell脚本），而一个月前我电脑上只有三张壁纸，当我看到[wallhaven](https://wallhaven.cc/)的壁纸时我第一想法是我该拥有它们，如果你喜欢壁纸可能也和我一样😁😁😁

![](https://gitee.com/pujichun/BlogImage/raw/master/img/L3TTVIR7OIJCTFW%60I%5DWOKV4.jpg)

![](https://gitee.com/pujichun/BlogImage/raw/master/img/6XDNIDS9J3WCOS2_.jpg)

想要这些壁纸一张一张的手动下载当然是行不通的，需要借助一些特殊手段

![](https://gitee.com/pujichun/BlogImage/raw/master/img/_20210519194905.png)

**正片开始**

![效果演示](https://raw.githubusercontent.com/pujichun/img/main/wallhaven.gif)

## 解析网页

笔者要抓取的壁纸地址：https://wallhaven.cc/search?q=like%3Arddgwm

观察列表页，发现向下滚动后，`url`中的`page`参数会改变

![](https://gitee.com/pujichun/BlogImage/raw/master/img/20210519195344.png)

然后简单测试一下反爬虫（手段过于暴躁就不展示了），发现没有发爬虫，但出于尊敬还是携带上`User-Agent`，简单封装一下列表页的请求，一共只有8页，如果读者比较闲也可以自行破解一下`total page`

```python
import requests
from requests.exceptions import RequestException


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


def run():
    link_list = []
    for i in range(1, 9):
        url = f"https://wallhaven.cc/search?q=like%3Arddgwm&page={i}"
        html = download_html(url)

if __name__ == "__main__":
    run()
```

那么接下来就要解析html获取到图片url了

当打开浏览器开发者工具定位到图片的时候发现`src`的值是小图的链接

![](https://gitee.com/pujichun/BlogImage/raw/master/img/QQ%E6%88%AA%E5%9B%BE20210519201606.png)

点击封面进去之后发现图片是这样的

![](https://gitee.com/pujichun/BlogImage/raw/master/img/QQ%E6%88%AA%E5%9B%BE20210519200554.png)

很显然这个页面是由前端程序渲染出来的，这个页面不是图片，因此需要鼠标右键点击这个页面中的大图片，选中`在新标签页中打开图片`

![](https://gitee.com/pujichun/BlogImage/raw/master/img/20210519201145.png)

当然也可以从这个页面中解析到图片链接，但是没有必要

在新打开的窗口中发现url变成了这样`https://w.wallhaven.cc/full/rd/wallhaven-rddgwm.jpg`，这个链接和列表页中`src`的值很像，简单写个函数转换一下

```python
def image_link_process(image_link: str) -> str:
    # https://w.wallhaven.cc/full/rd/wallhaven-rddgwm.jpg
    # https://th.wallhaven.cc/small/rd/rddgwm.jpg
    if "small" in image_link:
        image_link = image_link.replace("th", "w")
        image_link = image_link.replace("small", "full")
        url_path = image_link.split("/")
        url_path[-1] = f"wallhaven-{url_path[-1]}"
        return "/".join(url_path)
    return ""
```

欧克！运行之后发现能转换成功，那么下一步就是提取到`src`的值，编写一个简单的脚本测试一下

```python
import requests
from lxml import etree


def test():
    url = "https://wallhaven.cc/search?q=like%3Arddgwm&page=1"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
    }
    resp = requests.get(url, headers=headers)
    html = resp.content.decode("utf8")
    print(html, end="\n\n\n")
    element = etree.HTML(html)
    image_links = element.xpath('//img[@alt="loading"]/@src')
    print(image_links)


if __name__ == '__main__':
    test()

```

发现不对啊

![](http://img.doutula.com/production/uploads/image/2016/07/11/20160711198823_aAEDKy.jpg)

查看输出的html，发现对应标签没有`src`属性，但是有`data-src`属性，因此提取`data-src`的值，将`xpath`表达式改为

```
//img[@alt="loading"]/@data-src
```

再次运行！这下欧克了！

接下来就是重头戏了！下载图片！

## 下载图片

通常在用`requests`获取网页的时候，我们会使用`text`或者`content.decode()`的方法将请求返回的整个`body`读出来，但是对于[wallhaven](https://wallhaven.cc/)上分辨率普遍都很高的图片而言，我们应该分块读取。

因为图片传输的过程本来就是一个流式传输，使用`response.get(stream=True)`将推迟响应内容的下载，当我们读取的时候才会下载

因为要分块读取，所以我们需要每次读一定数量的字节的文件出来，所以要使用`response.iter_content(chunk)`的方式去读，一次读`chunk`个字节的内容

```python
def download_image(image_link):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
    }
    resp = requests.get(image_link, headers=headers, stream=True)
    try:
        if resp.status_code == 200:
            with open(file=f'images/{image_link.split("/")[-1]}', mode="wb") as f:
                for chunk in resp.iter_content(chunk_size=1024):
                    f.write(chunk)
			print("下载成功")
        else:
            print("下载失败")
    except:
        print("下载失败")
```

## 进度条

本文使用的支持进度条的第三方库为`rich`，`rich`功能十分强大

安装后在终端中使用下面的命令就能看到样例展示

```shell
python -m rich.progress
```

因为代码简单所以就不废话了

```python
def download_image(image_link):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
    }
    resp = requests.get(image_link, headers=headers, stream=True)
    try:
        # 获取图片总字节数
        file_size = int(resp.headers['content-length'])
        if resp.status_code == 200:
            with open(file=f'images/{image_link.split("/")[-1]}', mode="wb") as f:
                # 创建并启动Progress（进度条）对象
                with Progress() as progress:
                    # 给Progress对象添加一个任务，并指定任务大小
                    task1 = progress.add_task(f'[red]Downloading...{f.name}', total=file_size)
                    for chunk in resp.iter_content(chunk_size=1024):
                        f.write(chunk)
                        # 更新进度条
                        progress.update(task1, advance=1024)
        else:
            print("下载失败")
    except:
        print("下载失败")
```

通过`Progress`对象可以创建多条进度条

## 完整程序如下

```python
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
            print("下载失败")
    except:
        print("下载失败")


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
    
```

![](http://img.doutula.com/production/uploads/image/2020/03/28/20200328365125_DSQGkA.jpg)

这就完了？当然没有，可能各位读者已经想好怎么用多线程或者多进程加速了，但是啊！就是这个但是！多线程多没意思！协程~~~冲！

![](http://img.doutula.com/production/uploads/image/2017/12/14/20171214258818_lMAnGx.jpg)

~~协程写法待更新~~


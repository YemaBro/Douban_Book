# Douban_Book

## 目标站点

本次抓取选取了豆瓣图书中的10个分类标签，对10个标签下的图书信息进行抓取。

URL构成为：***https://book.douban.com/tag/{tag}?start={start}***

tag：标签名称；

start：起始数据量，每页20条数据。

## 抓取思路与实现

本项目为分布式爬虫项目，使用scrapy-redis组件搭建分布式爬虫。本项目有一主机两从机，主机只负责维护去重指纹和请求队列，爬取到的数据不返回主机的redis中，分别保存在两从机的MongoDB数据库中。

### scrapy-redis

#### 配置

一下配置在settings中添加：

```python
# 调度器
'''
scrapy-redis分布式的中心思想是更换scrapy本身的调度器改为scrapy-redis的调度器，在远程redis中维护共同的请求队列、去重指纹和爬取到的数据。
'''
SCHEDULER = "scrapy_redis.scheduler.Scheduler"

# 去重
'''
scrapy-redis的去重继承了scrapy中的BaseDupeFilter。scrapy-redis调度器从引擎中接受请求，将请求的的指纹存入redis中的set中检查是否重复，将不重复的请求写入请求队列中。
'''
DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"

# redis远程连接
REDIS_URL = 'redis://user:pass@hostname:9001'
```

可选配置：

```python
'''
开启此配置后，爬取到的数据将返回到redis中。
'''
ITEM_PIPELINES = {
    'scrapy_redis.pipelines.RedisPipeline': 301

}
```

#### RedisSpider

在RedisSpider中没有start_urls，在爬虫就绪之后使用**lpush redis-key url**启动爬虫。

在本项目中的**redis_key = 'douban:urls'**指定了redis中储存请求的建。

在本项目中，起始URL选择了10个。如果等待爬虫就绪之后再使用命令添加请求队列太麻烦，因此通过覆写**start_requests**构造请求队列。

### IP代理与用户代理

#### IP代理

在调试抓取的过程中发现有IP封锁的反爬措施，使用IP代理解决此问题。

使用的是阿布云动态版HTTP隧道。添加中间件代码如下（应在settings中添加的相同的开启中间件操作）：

```python
import base64

class ProxyMiddleware(object):
    def __init__(self):
        self.proxyServer = 'http://http-dyn.abuyun.com:9020'
        self.proxyUser = USER
        self.proxyPass = PASS
        self.proxyAuth = "Basic " + base64.urlsafe_b64encode(bytes((self.proxyUser + ":" + self.proxyPass), "ascii"))\
            .decode("utf8")

    def process_request(self, request, spider):
        request.meta["proxy"] = self.proxyServer
        request.headers["Proxy-Authorization"] = self.proxyAuth
```

#### 用户代理

使用基于fake_useragent的scrapy拓展scrapy_fake_useragent构造用户代理。

需要先关闭scrapy的默认中间件，然后在settings中开启中间件：

```python
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy_fake_useragent.middleware.RandomUserAgentMiddleware': 400,
}

```



### 爬虫空跑问题

所谓爬虫空跑，即在维护的请求队列中已没有可以发起请求的URL，但爬虫还在运行。

#### scrapy单机下的spider终止流程

scrapy内部的信号系统会在爬虫耗尽内部队列中的请求时触发spider_idle信号；爬虫信号管理器在收到spider_idle信号后将调用注册spider_idle信号的处理器进行处理；当该信号的所有处理器被调用后，如果spider仍然保持空闲状态，引擎将会关闭该spider。

#### scrapy-redis下的spider终止思路

spider关闭的关键是spider_idle信号，类比scrapy单机下的spider_idle信号终止处理，可以在信号管理处理器上注册一个对应spider_idle信号下的spider_idle()方法，编写条件以结束爬虫，这里以判断redis中的键key是否为空为条件。

需开启scrapy拓展：

```python
EXTENSIONS = {
   'Douban.extensions.RedisSpiderSmartIdleClosedExensions': 500
}
```



### 数据处理思路

本次计划抓取7个字段，分别为书名（title），作者（author），出版社（pub），出版时间（date），价格（price），评分（rating_nums），评价人数（comment_nums）。

7个字段或多或少都存在单位不统一、数据缺失或不对应的情况。以下将对数据后续处理提出思路：

单位不统一：单位不统一的情况主要出现在价格和时间上。在价格上，相关的数据比如售价按照美元换算都会以USD开头或结尾，在抓取到数据之后可通过正则匹配去除字母然后乘以汇率；在时间上，有效数据分别精确到月或日，中间以'-'分割，在抓取到数据后可采用字符串分割的方式，将时间统一精确到月；

数据缺失或不对应：数据不对应或缺失在7个字段中或多或少都存在。主要原因是网页中的原数据与抓取规则不匹配，匹配规则只适用于大部分原数据，采用字符串分割的方式分别提取在固定位置的数据。如价格、评分、评价人数等数据缺失，可用平均数或中位数填充，其他字段的数据缺失难以有效填充；对于大部分字段都缺失或不对应的数据可视为无效数据。


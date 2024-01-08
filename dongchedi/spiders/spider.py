import scrapy
from dongchedi.items import DongchediItem
from dongchedi.items import BrandItem
import pandas as pd
import re
from datetime import datetime


def get_space_num(s):
    length = 0
    for char in s:
        if '\u4e00' <= char <= '\u9fff' or char in ['（', '）']:  # 判断字符是否为中文
            length += 2
        else:
            length += 1
    return 70 - length if length < 70 else 10


MONTH = datetime.now().strftime('%Y%m')


class BrandSpider(scrapy.Spider):
    """
    品牌爬虫：汽车品牌以字母归类，点到字母对应的页面，爬取该页面下所有品牌
    命令：scrapy crawl brand
    """
    name = "brand"
    allowed_domains = ["dongchedi.com"]
    custom_settings = {'ITEM_PIPELINES': {'dongchedi.pipelines.BrandPipeline': 1}}
    start_urls = [
        "https://www.dongchedi.com/auto/library-brand/2",    # A 奥迪
        "https://www.dongchedi.com/auto/library-brand/3",    # B 奔驰
        "https://www.dongchedi.com/auto/library-brand/35",   # C 长安
        "https://www.dongchedi.com/auto/library-brand/1",    # D 大众
        "https://www.dongchedi.com/auto/library-brand/293",  # E Elemental
        "https://www.dongchedi.com/auto/library-brand/5",    # F 丰田
        "https://www.dongchedi.com/auto/library-brand/40",   # G 广汽传祺
        "https://www.dongchedi.com/auto/library-brand/17",   # H 哈弗
        "https://www.dongchedi.com/auto/library-brand/165",  # I Icona
        "https://www.dongchedi.com/auto/library-brand/73",   # J 吉利汽车
        "https://www.dongchedi.com/auto/library-brand/30",   # k 凯迪拉克
        "https://www.dongchedi.com/auto/library-brand/174",  # L 领克
        "https://www.dongchedi.com/auto/library-brand/15",   # M 马自达
        "https://www.dongchedi.com/auto/library-brand/199",  # N 哪吒汽车
        "https://www.dongchedi.com/auto/library-brand/238",  # O 欧拉
        "https://www.dongchedi.com/auto/library-brand/196",  # P Polestar极星
        "https://www.dongchedi.com/auto/library-brand/18",   # Q 奇瑞
        "https://www.dongchedi.com/auto/library-brand/10",   # R 日产
        "https://www.dongchedi.com/auto/library-brand/23",   # S 斯科达
        "https://www.dongchedi.com/auto/library-brand/63",   # T 特斯拉
        "https://www.dongchedi.com/auto/library-brand/339",  # U Ultima
        "https://www.dongchedi.com/auto/library-brand/289",  # V Venturi
        "https://www.dongchedi.com/auto/library-brand/39",   # W 五菱汽车
        "https://www.dongchedi.com/auto/library-brand/6",    # X 雪佛兰
        "https://www.dongchedi.com/auto/library-brand/29",   # Y 英菲尼迪
        "https://www.dongchedi.com/auto/library-brand/28",   # Z 中华
    ]

    def parse(self, response):
        # e.g. 林肯 https://www.dongchedi.com/auto/library-brand/62
        brands = response.xpath("//span[starts-with(@class,'brand_name')]/text()").extract()
        urls = response.xpath("//a[starts-with(@class,'brand_link')]/@href").extract()
        for i in range(len(brands)):
            item = BrandItem()
            item["brand"] = brands[i]
            item["code_brand"] = int(urls[i].split("/")[-1])
            item["url"] = "https://www.dongchedi.com" + urls[i]
            yield item


class ParamSpider(scrapy.Spider):
    """
    参数爬虫：爬取每个车型的具体参数信息（全部，包括在售、停售、未上市）
    命令：scrapy crawl param -s JOBDIR=data/202312/param_1
    """
    name = "param"
    custom_settings = {'ITEM_PIPELINES': {'dongchedi.pipelines.ParamPipeline': 1}}
    allowed_domains = ["dongchedi.com"]
    try:
        brand_df = pd.read_excel(f'data/{MONTH}/brand/brand_{MONTH}.xlsx', skiprows=[1])
        start_urls = brand_df['url'].tolist()
    except FileNotFoundError:
        pass

    def parse(self, response):
        """
        爬取每个品牌brand下的车系car_series和对应url，保留meta信息传入下一级parse
        车型页面 & 响应页面 https://www.dongchedi.com/auto/library-brand/62
        """
        code_brand = int(response.url.split('/')[-1])
        brand = response.xpath("//a[contains(@class, 'brand_selected')]/span/@title").extract_first()
        car_series = response.xpath("//a[starts-with(@class,'series-card_name')]/text()").extract()
        urls = response.xpath("//a[starts-with(@class,'series-card_name')]/@href").extract()
        for i in range(len(car_series)):
            code_car_series = int(urls[i].split('/')[-1])
            url = "https://www.dongchedi.com/motor/pc/car/series/car_list?series_id=" + str(code_car_series)
            yield scrapy.Request(url=url, meta={"brand": brand, "code_brand": code_brand,
                                                "car_series": car_series[i], "code_car_series": code_car_series},
                                 callback=self.parse_url, dont_filter=True)

    def parse_url(self, response):
        """
        爬取每个车系car_series下的车型car_type和对应url，保留meta信息传入下一级parse
        车系页面 https://www.dongchedi.com/auto/series/957
        响应页面 https://www.dongchedi.com/motor/pc/car/series/car_list?series_id=957
        """
        info = response.json()
        if info["message"] != "success":  # 有些车还没挂出信息，或者网络错误
            self.state["fail"] = self.state.get("fail", {})
            self.state["fail"]["interior error"] = self.state.get("fail", {}).get("interior error", set())
            fail_url = f"https://www.dongchedi.com/auto/series/{response.url.split('=')[-1]}"
            self.state["fail"]["interior error"].add(fail_url)
            print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")}            '
                  f'<Series Failure> No Car Type: {fail_url}')
            return
        brand = response.meta["brand"]
        code_brand = response.meta["code_brand"]
        car_series = response.meta["car_series"]
        code_car_series = response.meta["code_car_series"]

        tab_list = info["data"]["tab_list"]
        for tab in tab_list:
            if tab["tab_text"] in ["在售", "停售", "未上市"]:  # 最新年款的会重复，要筛掉
                data = tab["data"]
                for d in data:
                    if d["info"].get("id"):  # 题头筛掉
                        sale = tab["tab_text"]
                        url = "https://www.dongchedi.com/auto/params-carIds-" + str(d["info"].get("id"))
                        yield scrapy.Request(url=url, meta={"brand": brand,
                                                            "code_brand": code_brand,
                                                            "car_series": car_series,
                                                            "code_car_series": code_car_series,
                                                            "sale": sale},
                                             callback=self.parse_param, dont_filter=True)

    def parse_param(self, response):
        """
        爬取每个车型car_type的参数
        车型页面 https://www.dongchedi.com/auto/series/957/model-13604?cityName=%E5%8C%97%E4%BA%AC
        响应页面 https://www.dongchedi.com/auto/params-carIds-13604
        价格页面 https://www.dongchedi.com/motor/pc/car/series/car_dealer_price?car_ids=13604&city_name=%E5%8C%97%E4%BA%AC
        """
        item = DongchediItem()
        car_type = response.xpath("//@title").extract()[1]
        if not car_type:  # 通常是网络错误
            self.state["fail"] = self.state.get("fail", {})
            self.state["fail"]["network error"] = self.state.get("fail", {}).get("network error", set())
            self.state["fail"]["network error"].add(response.url)
            print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")}            '
                  f'<Param Failure> Network Error: {response.url}')
            return

        url = response.xpath("//a[@title]/@href").extract()[1]

        item["code_brand"] = response.meta["code_brand"]
        item["code_car_series"] = response.meta["code_car_series"]
        item["code_car_type"] = int(url.split('-')[-1])
        item["brand"] = response.meta["brand"]
        item["car_series"] = response.meta["car_series"]
        item["car_type"] = car_type
        item["year"] = int(re.search(r"([0-9]{4})款", car_type).group(1))
        item["url"] = "https://www.dongchedi.com" + url
        item["sale"] = response.meta["sale"]
        item["dealer_price"] = response.xpath("//span[starts-with(@class,'cell_price')]/text()").extract_first()

        col_name = response.xpath("//div/@data-row-anchor").extract()
        col_description = response.xpath("//label/text()").extract()
        self.state["columns"] = self.state.get("columns",
                                               {'crawl_index': '序号',
                                                'code_brand': '品牌编码', 'code_car_series': '车系编码',
                                                'code_car_type': '车型编码',
                                                'brand': '品牌', 'car_series': '车系', 'car_type': '车型',
                                                'year': '年款', 'url': '网址', 'sale': '销售状态',
                                                'dealer_price': '经销商价格(万)', 'official_price': '官方指导价(万)'})

        for i in range(len(col_name)):
            col = col_name[i]
            des = col_description[i]
            item.fields[col] = scrapy.Field()
            if col not in self.state["columns"]:
                self.state["columns"][col] = des
                if col == "market_time":
                    self.state["columns"]["market_time_year"] = "上市时间_年"
                    self.state["columns"]["market_time_month"] = "上市时间_月"
            item_raw = response.xpath(f"//div[@data-row-anchor='{col}']/*[last()]/*//text()").extract()
            if item_raw:
                item_raw = list(filter(lambda a: a != '图示', item_raw))
                while len(item_raw) > 1 and item_raw[0] == item_raw[1]:  # 从头去除连续的重复项（直至前两项不一样）
                    item_raw.pop(0)
                item[col] = ' '.join(item_raw)

        self.state["succeed"] = self.state.get("succeed", 0) + 1
        item["crawl_index"] = self.state["succeed"]
        print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")}   {str(self.state["succeed"]).rjust(6)}   '
              f'{car_type}{" " * get_space_num(car_type)}{response.url}')
        yield item


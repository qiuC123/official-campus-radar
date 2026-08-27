import re
from collections.abc import Iterable


SPECIAL_LOCATIONS = {"全国", "远程"}
SUFFIXES = ("特别行政区", "自治区", "自治州", "地区", "省", "盟", "市")
PROVINCE_NAMES = (
    "北京", "天津", "河北", "山西", "内蒙古", "辽宁", "吉林", "黑龙江",
    "上海", "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南",
    "湖北", "湖南", "广东", "广西", "海南", "重庆", "四川", "贵州",
    "云南", "西藏", "陕西", "甘肃", "青海", "宁夏", "新疆", "香港",
    "澳门", "台湾",
)

_PROVINCE_CITIES = {
    "河北": "石家庄 唐山 秦皇岛 邯郸 邢台 保定 张家口 承德 沧州 廊坊 衡水 雄安",
    "山西": "太原 大同 阳泉 长治 晋城 朔州 晋中 运城 忻州 临汾 吕梁",
    "内蒙古": "呼和浩特 包头 乌海 赤峰 通辽 鄂尔多斯 呼伦贝尔 巴彦淖尔 乌兰察布 兴安 锡林郭勒 阿拉善",
    "辽宁": "沈阳 大连 鞍山 抚顺 本溪 丹东 锦州 营口 阜新 辽阳 盘锦 铁岭 朝阳 葫芦岛",
    "吉林": "长春 吉林 四平 辽源 通化 白山 松原 白城 延边",
    "黑龙江": "哈尔滨 齐齐哈尔 鸡西 鹤岗 双鸭山 大庆 伊春 佳木斯 七台河 牡丹江 黑河 绥化 大兴安岭",
    "江苏": "南京 无锡 徐州 常州 苏州 南通 连云港 淮安 盐城 扬州 镇江 泰州 宿迁",
    "浙江": "杭州 宁波 温州 嘉兴 湖州 绍兴 金华 衢州 舟山 台州 丽水",
    "安徽": "合肥 芜湖 蚌埠 淮南 马鞍山 淮北 铜陵 安庆 黄山 滁州 阜阳 宿州 六安 亳州 池州 宣城",
    "福建": "福州 厦门 莆田 三明 泉州 漳州 南平 龙岩 宁德",
    "江西": "南昌 景德镇 萍乡 九江 新余 鹰潭 赣州 吉安 宜春 抚州 上饶",
    "山东": "济南 青岛 淄博 枣庄 东营 烟台 潍坊 济宁 泰安 威海 日照 临沂 德州 聊城 滨州 菏泽",
    "河南": "郑州 开封 洛阳 平顶山 安阳 鹤壁 新乡 焦作 濮阳 许昌 漯河 三门峡 南阳 商丘 信阳 周口 驻马店 济源",
    "湖北": "武汉 黄石 十堰 宜昌 襄阳 鄂州 荆门 孝感 荆州 黄冈 咸宁 随州 恩施 仙桃 潜江 天门 神农架",
    "湖南": "长沙 株洲 湘潭 衡阳 邵阳 岳阳 常德 张家界 益阳 郴州 永州 怀化 娄底 湘西",
    "广东": "广州 韶关 深圳 珠海 汕头 佛山 江门 湛江 茂名 肇庆 惠州 梅州 汕尾 河源 阳江 清远 东莞 中山 潮州 揭阳 云浮",
    "广西": "南宁 柳州 桂林 梧州 北海 防城港 钦州 贵港 玉林 百色 贺州 河池 来宾 崇左",
    "海南": "海口 三亚 三沙 儋州 五指山 琼海 文昌 万宁 东方 定安 屯昌 澄迈 临高 白沙 昌江 乐东 陵水 保亭 琼中",
    "四川": "成都 自贡 攀枝花 泸州 德阳 绵阳 广元 遂宁 内江 乐山 南充 眉山 宜宾 广安 达州 雅安 巴中 资阳 阿坝 甘孜 凉山",
    "贵州": "贵阳 六盘水 遵义 安顺 毕节 铜仁 黔西南 黔东南 黔南",
    "云南": "昆明 曲靖 玉溪 保山 昭通 丽江 普洱 临沧 楚雄 红河 文山 西双版纳 大理 德宏 怒江 迪庆",
    "西藏": "拉萨 日喀则 昌都 林芝 山南 那曲 阿里",
    "陕西": "西安 铜川 宝鸡 咸阳 渭南 延安 汉中 榆林 安康 商洛",
    "甘肃": "兰州 嘉峪关 金昌 白银 天水 武威 张掖 平凉 酒泉 庆阳 定西 陇南 临夏 甘南",
    "青海": "西宁 海东 海北 黄南 海南 果洛 玉树 海西",
    "宁夏": "银川 石嘴山 吴忠 固原 中卫",
    "新疆": "乌鲁木齐 克拉玛依 吐鲁番 哈密 昌吉 博尔塔拉 巴音郭楞 阿克苏 克孜勒苏 喀什 和田 伊犁 塔城 阿勒泰 石河子 阿拉尔 图木舒克 五家渠 北屯 铁门关 双河 可克达拉 昆玉 胡杨河 新星 白杨",
}

CITY_TO_PROVINCE = {
    city: province
    for province, cities in _PROVINCE_CITIES.items()
    for city in cities.split()
}
CITY_TO_PROVINCE.update({
    "Beijing": "北京", "Shanghai": "上海", "Tianjin": "天津",
    "Chongqing": "重庆", "Shenzhen": "广东", "Guangzhou": "广东",
    "Dongguan": "广东", "Foshan": "广东", "Zhuhai": "广东",
    "Suzhou": "江苏", "Nanjing": "江苏", "Wuxi": "江苏",
    "Hangzhou": "浙江", "Ningbo": "浙江", "Chengdu": "四川",
    "Wuhan": "湖北", "Xi'an": "陕西", "Xian": "陕西",
    "Qingdao": "山东", "Jinan": "山东", "Shenyang": "辽宁",
    "Dalian": "辽宁", "Changsha": "湖南", "Xiamen": "福建",
    "Hefei": "安徽", "Zhengzhou": "河南", "Changchun": "吉林",
    "Harbin": "黑龙江",
    "Hebei": "河北", "Shanxi": "山西", "Inner Mongolia": "内蒙古",
    "Liaoning": "辽宁", "Jilin": "吉林", "Heilongjiang": "黑龙江",
    "Jiangsu": "江苏", "Zhejiang": "浙江", "Anhui": "安徽",
    "Fujian": "福建", "Jiangxi": "江西", "Shandong": "山东",
    "Henan": "河南", "Hubei": "湖北", "Hunan": "湖南",
    "Guangdong": "广东", "Guangxi": "广西", "Hainan": "海南",
    "Sichuan": "四川", "Guizhou": "贵州", "Yunnan": "云南",
    "Tibet": "西藏", "Shaanxi": "陕西", "Gansu": "甘肃",
    "Qinghai": "青海", "Ningxia": "宁夏", "Xinjiang": "新疆",
    "Hong Kong": "香港", "Macao": "澳门", "Macau": "澳门",
    "Taiwan": "台湾",
})


def _parts(value: str | Iterable[str] | None) -> list[str]:
    values = [value] if isinstance(value, str) or value is None else list(value)
    parts: list[str] = []
    for item in values:
        parts.extend(
            part.strip()
            for part in re.split(r"[\s,，、/|;；·]+", str(item or ""))
            if part.strip()
        )
    return parts


def normalize_locations(value: str | Iterable[str] | None) -> list[str]:
    """Normalize common Chinese place suffixes while retaining unknown text."""
    result: list[str] = []
    for part in _parts(value):
        normalized = part
        if normalized not in SPECIAL_LOCATIONS:
            for suffix in SUFFIXES:
                if normalized.endswith(suffix) and len(normalized) > len(suffix):
                    normalized = normalized[: -len(suffix)]
                    break
        if normalized and normalized not in result:
            result.append(normalized)
    return result


def province_for_location(location: str) -> str | None:
    """Map a public job location to a province-level display value."""

    text = str(location or "").strip()
    if not text or text.isdigit() or text in {"地区", "CN", "China"}:
        return None
    if text in SPECIAL_LOCATIONS:
        return text
    if text in {"全部", "全国各地"}:
        return "全国"
    if "其他国家" in text:
        return "海外"
    for province in PROVINCE_NAMES:
        if province in text:
            return province
    folded = text.casefold()
    for city, province in CITY_TO_PROVINCE.items():
        if city.casefold() in folded:
            return province
    if re.search(r"[A-Za-z]", text):
        return "海外"
    if text.endswith(("区", "县", "镇", "乡")):
        return None
    return text


def province_locations(locations: Iterable[str]) -> tuple[str, ...]:
    """Collapse a city-heavy location collection into stable province labels."""

    recognized: list[str] = []
    unknown: list[str] = []
    recognized_values = set(PROVINCE_NAMES) | SPECIAL_LOCATIONS | {"海外"}
    for location in locations:
        province = province_for_location(location)
        if not province:
            continue
        target = recognized if province in recognized_values else unknown
        if province not in target:
            target.append(province)
    return tuple(recognized or unknown)


def normalized_target_locations(value: str | Iterable[str] | None) -> list[str]:
    """Compatibility name: Phase 02 accepts every location, not only four cities."""
    return normalize_locations(value)


def is_target_location(value: str | Iterable[str] | None) -> bool:
    return bool(normalize_locations(value))


def matches_selected_cities(locations: Iterable[str], selected: Iterable[str]) -> bool:
    selected_set = set(province_locations(selected))
    if not selected_set:
        return True
    location_set = set(province_locations(locations))
    has_concrete_city = bool(selected_set - SPECIAL_LOCATIONS)
    return bool(location_set & selected_set) or (
        has_concrete_city and bool(location_set & SPECIAL_LOCATIONS)
    )

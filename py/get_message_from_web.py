import dataclasses
import time
from dataclasses import field
from typing import List

import pymysql
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from tools.py.const import MovieType, DouBanSource, TVType
from tools.py.orm.model import MovieMessageModel, database, MovieTagsModel
from tools.py.utils import SnowflakeIDGenerator, MyTimer


@dataclasses.dataclass
class MovieMessage:
    uni_id: str = field(init=False)
    name: str
    tags: [] = field(init=False)
    score: []
    image_url: []
    common: str
    source: str
    type: str


def get_movie_message() -> List[MovieMessage]:
    # 配置webdriver,https://developer.chrome.com/docs/chromedriver/get-started?hl=zh-cn
    service = Service('D:\easy_code\chromedriver-win64\chromedriver.exe')
    service.start()
    options = Options()
    options.add_argument("--start-maximized")  # 启动时最大化窗口
    options.add_argument("--disable-blink-features=AutomationControlled")  # 使浏览器不显示自动化控制的信息
    options.add_argument("--incognito")  # 启动无痕模式

    hot_movie_message = []
    with webdriver.Chrome(service=service, options=options) as driver:
        web_url = 'https://movie.douban.com/'
        driver.get(web_url)
        time.sleep(5)
        # 图片的滚动条，下面需要用到
        print('获取滚动条')
        slides = driver.find_elements(By.CLASS_NAME, "slider")
        if len(slides) == 0:
            print('no slides')
            return []
        # 热门电影栏目
        slide = slides[0]

        print('获取图片位置')
        images = slide.find_elements(By.CSS_SELECTOR, "div.cover-wp img")
        print(f'get images len:{len(images)}')


        for image in images:
            # 鼠标悬停在图片上
            print('鼠标悬停图片上')
            move_to_image(image, driver)
            time.sleep(3)

            # 提取信息
            hot_movie_message.append(
                format_movie_message(driver, image.get_attribute('alt'), image.get_attribute('src')))

    return hot_movie_message


def format_movie_message(driver, movie_name, image_url):
    try:
        print('提取标题')
        pop_up_windows = driver.find_element(By.CSS_SELECTOR, 'div.detail-pop')
        # 提取标题
        title_element = pop_up_windows.find_element(By.CSS_SELECTOR, "h3 a")
        title = title_element.text.strip()
        if title == '':
            title = movie_name

        # 提取评分
        print('提取评分')
        score_element = pop_up_windows.find_element(By.CSS_SELECTOR, "p.rank strong")
        score = score_element.text.strip()

        # 提取标签
        print('提取标签')
        meta_element = pop_up_windows.find_element(By.CSS_SELECTOR, "p.meta")
        meta_info = meta_element.text.strip().split('\n')

        # 提取评论
        try:
            print('提取评论')
            comment_element = pop_up_windows.find_element(By.CSS_SELECTOR, "p.comment")
            comment = comment_element.text.strip()
        except Exception:
            comment = ""

        movie_message = MovieMessage(name=title, score=score, image_url=image_url, common=comment, type=MovieType,
                                     source=DouBanSource)
        movie_message.tags = meta_info
        return movie_message
    except Exception as e:
        print(f'could not find pop up windows:{e}')


def move_to_image(image, driver):
    # 只需要绑定鼠标事件，不需要在页面上出现这个图片。。。
    hover_script = """
                    const event = new MouseEvent('mouseover', {
                        bubbles: true,
                        cancelable: true,
                        view: window
                    });
                    arguments[0].dispatchEvent(event);
                """
    driver.execute_script(hover_script, image)


def generate_id(messages: List[MovieMessage], movie_type) -> List[MovieMessage]:
    prefix = ""
    if movie_type == MovieType:
        prefix = "mv"
    if movie_type == TVType:
        prefix = "tv"
    generator = SnowflakeIDGenerator(id_length=20, prefix=prefix)
    for message in messages:
        message.uni_id = str(generator.generate_id())
    return messages


def create_movie_message(messages: List[MovieMessage]):
    movie_message_model_list = []
    for m in messages:
        movie_message_model_list.append(
            MovieMessageModel(uni_id=m.uni_id, name=m.name, score=m.score, image_url=m.image_url, common=m.common,
                              source=m.source,
                              type=m.type))
    with database.atomic():
        MovieMessageModel.bulk_create(movie_message_model_list,batch_size=100)

    # 存入标签
    return create_tags(messages)


def create_tags(messages: List[MovieMessage]):
    tags_model_list = []
    for m in messages:
        for tag in m.tags:
            tags_model_list.append(MovieTagsModel(movie_id=m.uni_id, tag=tag, source=m.source))
    with database.atomic():
        MovieTagsModel.bulk_create(tags_model_list,batch_size=100)


def list_movie_message_by_type(movie_type):
    model_list = MovieMessageModel.select().where(MovieMessageModel.type == movie_type)
    result = []
    for l in model_list:
        movie_message = MovieMessage(name=l.name, image_url=l.image_url, score=l.score, source=l.source, type=l.type,
                                     common=l.common)
        movie_message.id = l.id
        result.append(movie_message)
    return result


def start():
    # 获取豆瓣信息
    timer1 = MyTimer()
    timer1.start()
    movie_messages = get_movie_message()
    timer1.stop()
    print(f'一共找到{len(movie_messages)}个信息，耗时{timer1.elapsed():.4f}s')

    timer2 = MyTimer()
    timer2.start()
    # 生成唯一id
    movie_messages = generate_id(movie_messages, MovieType)
    # 存入数据库
    create_movie_message(movie_messages)
    timer2.stop()
    print(f'插入数据库耗时{timer2.elapsed():.4f}s')

if __name__ == "__main__":
    start()
    print('done')

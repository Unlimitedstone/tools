import dataclasses
import time
from dataclasses import field
from typing import List

import pymysql
from exceptiongroup import catch
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from setuptools.command.alias import alias

from tools.py.const import MovieType, DouBanSource, TVType
from tools.py.orm.model import MovieMessageModel, database, MovieTagsModel
from tools.py.utils import SnowflakeIDGenerator, MyTimer


@dataclasses.dataclass
class MovieDetail:
    introduce: str = field(init=False, default="")  # 简介
    alias: str = field(init=False, default="")  # 别名
    duration: int = field(init=False, default=0)  # 片长
    release_date: str = field(init=False, default="")  # 上映日期
    director: str = field(init=False, default="")  # 导演
    actor: str = field(init=False, default="")  # 主演
    writer: str = field(init=False, default="")  # 编剧
    country: str = field(init=False, default="")  # 制片国家
    imdb: str = field(init=False, default="")  # imdb链接


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
    detail: MovieDetail = field(init=False)


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
        # print('获取滚动条')
        slides = driver.find_elements(By.CLASS_NAME, "slider")
        if len(slides) == 0:
            print('no slides')
            return []
        # 热门电影栏目
        slide = slides[0]

        # print('获取图片位置')
        images = slide.find_elements(By.CSS_SELECTOR, "div.cover-wp img")
        print(f'get images len:{len(images)}')


        index = 0
        for image in images:
            index += 1

            # 鼠标悬停在图片上
            # print('鼠标悬停图片上')
            move_to_image(image, driver)
            time.sleep(3)

            print(f'提取第{index}个信息, {image.get_attribute("alt")}')
            movie_message = format_movie_message(driver, image.get_attribute('alt'), image.get_attribute('src'))
            movie_detail = get_movie_detail(image, driver)

            movie_message.detail = movie_detail

            # 提取信息
            hot_movie_message.append(
                movie_message)

    return hot_movie_message


def format_movie_message(driver, movie_name, image_url):
    try:
        # print('提取标题')
        pop_up_windows = driver.find_element(By.CSS_SELECTOR, 'div.detail-pop')
        # 提取标题
        title_element = pop_up_windows.find_element(By.CSS_SELECTOR, "h3 a")
        title = title_element.text.strip()
        if title == '':
            title = movie_name

        # 提取评分
        # print('提取评分')
        score_element = pop_up_windows.find_element(By.CSS_SELECTOR, "p.rank strong")
        score = score_element.text.strip()

        # 提取标签
        # print('提取标签')
        meta_element = pop_up_windows.find_element(By.CSS_SELECTOR, "p.meta")
        meta_info = meta_element.text.strip().split('\n')

        # 提取评论
        try:
            # print('提取评论')
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


def get_movie_detail(image, driver):
    # 点击事件
    driver.execute_script('''
    var event = new MouseEvent("click", {
        "bubbles": true,
        "cancelable": true,
        "view": window
    });
    arguments[0].dispatchEvent(event);
    ''', image)
    # 跳转到新窗口
    driver.switch_to.window(driver.window_handles[1])
    time.sleep(3)

    detail = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.ID, 'info')))
    if detail is None:
        print('no detail')
        return []

    movie_detail = MovieDetail()

    try:
        # 提取简介
        introduce = driver.find_elements(By.CLASS_NAME, "indent")
        introduce = introduce[1].text.strip()
        movie_detail.introduce = introduce

        # 提取导演
        director = detail.find_element(By.XPATH, './/span[span[text()="导演"]]/span[@class="attrs"]/a').text
        movie_detail.director = director

        # 提取编剧（多个） 两种提取方式
        try:
            screenwriters = [a.text for a in
                             detail.find_elements(By.XPATH, './/span[span[text()="编剧"]]/span[@class="attrs"]/a')]
            movie_detail.writer = ','.join(screenwriters)
        except Exception:
            screenwriters = [a.text for a in
                             detail.find_elements(By.XPATH, './/span[span[text()="编剧"]]/a')]
            movie_detail.writer = ','.join(screenwriters)

        # 提取主演（多个）
        actors = [a.text for a in
                  detail.find_elements(By.XPATH, './/span[span[text()="主演"]]/span[@class="attrs"]/span/a')]
        if len(actors) == 0:
            actors = [a.text for a in
                      detail.find_elements(By.XPATH, './/span[span[text()="主演"]]/span[@class="attrs"]/a')]
        movie_detail.actor = ','.join(actors)

        # 提取上映日期
        release_date = detail.find_element(By.XPATH, './/span[@property="v:initialReleaseDate"]')
        movie_detail.release_date = release_date.text.strip()

        # 提取片长
        duration = detail.find_element(By.XPATH, './/span[@property="v:runtime"]').text.strip()
        movie_detail.duration = int(duration.split('分钟')[0])

        # 提取又名
        try:
            other_names = detail.find_element(By.XPATH, './/span[contains(text(), "又名")]')
            movie_detail.alias = get_next_element_text(driver, other_names)
        except Exception:
            movie_detail.alias = ""

        # 提取 IMDb
        imdb = detail.find_element(By.XPATH, './/span[contains(text(), "IMDb")]')
        movie_detail.imdb = get_next_element_text(driver, imdb)

        # 提取制片国家/地区
        country = detail.find_element(By.XPATH, './/span[contains(text(), "制片国家")]')
        movie_detail.country = get_next_element_text(driver, country)

        # 提取类型
        genres = [genre.text for genre in
                  detail.find_elements(By.XPATH, './/span[contains(text(),"类型")]/span[@property="v:genre"]')]

        # 提取语言
        language = detail.find_element(By.XPATH, './/span[contains(text(),"语言")]')
        language = get_next_element_text(driver, language)

    except Exception as e:
        print(f'could not find detail:{e}')

    # 关闭标签页
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    time.sleep(3)
    return movie_detail

def get_next_element_text(driver, element):
    return driver.execute_script("""
    let node = arguments[0].nextSibling;
    return node && node.nodeValue.trim();
""", element)


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
                              type=m.type, introduce=m.detail.introduce, alias=m.detail.alias,
                              duration=m.detail.duration, release_date=m.detail.release_date,
                              director=m.detail.director,
                              actor=m.detail.actor, writer=m.detail.writer, country=m.detail.country,
                              imdb=m.detail.imdb))
    with database.atomic():
        MovieMessageModel.bulk_create(movie_message_model_list, batch_size=100)

    # 存入标签
    return create_tags(messages)


def create_tags(messages: List[MovieMessage]):
    tags_model_list = []
    for m in messages:
        for tag in m.tags:
            tags_model_list.append(MovieTagsModel(movie_id=m.uni_id, tag=tag, source=m.source))
    with database.atomic():
        MovieTagsModel.bulk_create(tags_model_list, batch_size=100)


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
    # TODO 不获取重复数据
    # MovieMessageModel.truncate_table()
    # MovieTagsModel.truncate_table()

    # TODO 电视剧，动漫获取

    start()
    print('done')

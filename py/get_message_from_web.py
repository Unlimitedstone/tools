import dataclasses
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


@dataclasses.dataclass
class MovieMessage:
    name: str
    tags: []
    score: []
    image_url: []
    common: str
    type: str


MovieType = 'Movie'
TVType = 'TV'

def get_movie_message():
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
            return
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
            hot_movie_message.append(format_movie_message(driver, image.get_attribute('alt'), image.get_attribute('src')))

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
            comment = "No comment available"

        return MovieMessage(name=title, tags=meta_info, score=score, image_url=image_url, common=comment, type=MovieType)
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


def get_message_from_web():
    pass


def start():
    # 连接数据库

    # 获取豆瓣信息
    get_movie_message()
    #


if __name__ == "__main__":
    start_time = time.time()
    print('start_time:', start_time)
    start()
    end_time = time.time()
    print('end_time:', end_time)
    print('done, took:', end_time - start_time)

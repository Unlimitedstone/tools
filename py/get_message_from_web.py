import os

from numpy.distutils.conv_template import header
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

import time

from selenium.webdriver.chrome.service import Service


class MovieMessage:
    def __init__(self,name=''):
        pass
    @property
    def name(self):
        return self.name
    @property
    def tags(self):
        return self.tags
    @property
    def score(self):
        return self.score
    @property
    def image_url(self):
        return self.image_url
    @property
    def common(self):
        return self.common
    @property
    def common_author(self):
        return self.common_author

def get_movie_message():
    # 配置webdriver,https://developer.chrome.com/docs/chromedriver/get-started?hl=zh-cn
    service = Service('D:\easy_code\chromedriver-win64\chromedriver.exe')
    service.start()

    hot_movie_message = [MovieMessage()]
    with webdriver.Chrome(service=service) as driver:
        web_url = 'https://movie.douban.com/'
        driver.get(web_url)
        time.sleep(3)
        # 图片的滚动条，下面需要用到
        slide_wrapper = driver.find_elements(By.CSS_SELECTOR,'slide-wrapper')[0]
        slide_width = 700
        max_width = int(driver.execute_script("return arguments[0].style.width;", slide_wrapper).strip("px"))

        actions = ActionChains(driver)
        current_left = 0
        while abs(current_left) < max_width:

            images = slide_wrapper.find_elements(By.CSS_SELECTOR, "div.cover-wp img")

            for image in images:
                # 鼠标悬停在图片上
                actions.move_to_element(image).perform()
                time.sleep(1)

                try:
                    pop_up_windows = driver.find_elements(By.CSS_SELECTOR,'div.detail-pop')
                    # 提取标题
                    title_element = pop_up_windows.find_element(By.CSS_SELECTOR, "h3 a")
                    title = title_element.text.strip()
                    link = title_element.get_attribute("href")

                    # 提取评分
                    score_element = pop_up_windows.find_element(By.CSS_SELECTOR, "p.rank strong")
                    score = score_element.text.strip()

                    # 提取额外信息
                    meta_element = pop_up_windows.find_element(By.CSS_SELECTOR, "p.meta")
                    meta_info = meta_element.text.strip()

                    # 提取评论
                    try:
                        comment_element = pop_up_windows.find_element(By.CSS_SELECTOR, "p.comment")
                        comment = comment_element.text.strip()
                    except Exception:
                        comment = "No comment available"

                except Exception as e:
                    print(f'could not find pop up windows:{e}')

                hot_movie_message.append({
                    "title": title,
                    "link": link,
                    "score": score,
                    "meta_info": meta_info,
                    "comment": comment
                })
            current_left -= slide_width
            driver.execute_script("arguments[0].style.left = arguments[1] + 'px';", slide_wrapper, current_left)
            time.sleep(2)  # 等待页面加载
    print(hot_movie_message)


def get_message_from_web():
    pass





def start():
    pass
    # 连接数据库

    # 获取豆瓣信息

    #




if __name__ == "__main__":
    get_movie_message()
    print('done')




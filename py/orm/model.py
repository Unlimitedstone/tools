# 根据数据库表一键生成orm代码：https://docs.peewee-orm.com/en/latest/peewee/playhouse.html#pwiz
# py -m pwiz -e mysql -u root -H 127.0.0.1 -p 4306 -P test

from peewee import *

database = MySQLDatabase('test',
                         **{'charset': 'utf8', 'sql_mode': 'PIPES_AS_CONCAT', 'use_unicode': True, 'host': '127.0.0.1',
                            'port': 4306, 'user': 'root', 'password': '123456'})


class BaseModel(Model):
    class Meta:
        database = database


class MovieMessageModel(BaseModel):
    actor = CharField(null=True)
    alias = CharField(null=True)
    common = CharField(null=True)
    country = CharField(null=True)
    director = CharField(null=True)
    duration = IntegerField(null=True)
    id = BigAutoField()
    image_url = CharField(null=True)
    imdb = CharField(null=True)
    introduce = CharField(null=True)
    name = CharField()
    release_date = CharField(null=True)
    score = CharField(null=True)
    source = CharField()
    type = CharField()
    uni_id = CharField(unique=True)
    writer = CharField(null=True)

    class Meta:
        table_name = 'movie_message'



class MovieTagsModel(BaseModel):
    id = BigAutoField(primary_key=True)
    movie_id = CharField(unique=True)
    source = IntegerField()
    tag = CharField(null=True)

    class Meta:
        table_name = 'movie_tags'

import uuid, time
from myorm import Model, StringField, BooleanField, FloatField, TextField


'''
uuid.uuid1()　　基于MAC地址，时间戳，随机数来生成唯一的uuid，可以保证全球范围内的唯一性。
uuid.uuid2()　　算法与uuid1相同，不同的是把时间戳的前4位置换为POSIX的UID。不过需要注意的是python中没有基于DCE的算法，所以python的uuid模块中没有uuid2这个方法。
uuid.uuid3(namespace,name)　　通过计算一个命名空间和名字的md5散列值来给出一个uuid，所以可以保证命名空间中的不同名字具有不同的uuid，但是相同的名字就是相同的uuid了
uuid.uuid4()　　通过伪随机数得到uuid，是有一定概率重复的
uuid.uuid5(namespace,name)　　和uuid3基本相同，只不过采用的散列算法是sha1
'''
def next_id():
    return '%015d%s000' % (int(time.time()*1000), uuid.uuid4().hex)


class User(Model):
    __table__ = 'table'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    email = StringField(ddl='varchar(50)')
    passwd = StringField(ddl='varchar(50)')
    admin = BooleanField()
    name = StringField(ddl='varchar(50)')
    image = StringField(ddl='varchar(500)')
    # 日期和时间用float类型存储在数据库中，而不是datetime类型，这么做的好处是不必关心数据库的时区以及时区转换问题，排序非常简单
    # 显示的时候，只需要做一个float到str的转换
    created_at = FloatField(default=time.time)

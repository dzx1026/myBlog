# -*- coding:utf-8 -*-
import asyncio, aiomysql
import logging

logging.basicConfig(level=logging.INFO)


async def create_pool(loop, **kw):
    global __pool
    __pool = await aiomysql.create_pool(
        host=kw.get('host', 'localhost'),  # localhost为默认值
        port=kw.get('port', 3306),
        user=kw['user'],  # 从kw中取得user
        password=kw['passwd'],
        db=kw['db'],
        charset=kw.get('charset', 'utf8'),
        autocommit=kw.get('autocommit', True),
        maxsize=kw.get('maxsize', 10),  # 连接池的最大数量是10个，默认10
        minsize=kw.get('minsize', 1),  # 最小值是0则不生产连接，最大值是0则连接池没有限制，默认1
        loop=loop
    )


async def select(sql, args, size=None):
    logging.info(sql)
    global __pool
    with (await __pool) as conn:  # await __pool 从__pool这个生成器中不断的去获取
        cur = await conn.cursor(aiomysql.DictCursor)
        await cur.execute(sql.replace('?', '%s'), args or ())
        if size:
            rs = await cur.fetchmany(size)  # 获取指定数量的记录
        else:
            rs = await cur.fetchall()  # 获取全部的记录
        await cur.close()
        logging.info('rows returned:%s' % len(rs))  # len()返回list元素的个数

        return rs


# 用于数据库delete、update、insert操作
async def execute(sql, args):
    logging.info(sql)
    logging.info(args)
    global __pool
    with (await __pool) as conn:
        try:  # 找不到数据的时候容易报错，进行错误捕捉
            cur = await conn.cursor()
            await cur.execute(sql.replace('?', '%s'), args or ())
            affected = cur.rowcount
            await cur.close()
        except BaseException as e:
            raise
        return affected


# 拼装sql语句中的？
def create_args_string(num):
    L = []
    for n in range(num):
        L.append('?')
    return ', '.join(L)


class Field(object):
    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    # 该方法用于把一个类的实例变成str
    def __str__(self):
        return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)


class StringField(Field):
    def __init__(self, name=None, primary_key=False, default=None, ddl='varchar(100)'):
        super().__init__(name, ddl, primary_key, default)


class IntegerField(Field):
    def __init__(self, name=None, primary_key=False, default=None, ddl='int(5)'):
        super().__init__(name, ddl, primary_key, default)


class BooleanField(Field):
    def __init__(self, name=None, primary_key=False, default=0, ddl='tinyint'):
        super().__init__(name, ddl, primary_key, default)


class FloatField(Field):
    def __init__(self, name=None, primary_key=False, default=None, ddl='float'):
        super().__init__(name, ddl, primary_key, default)


class TextField(Field):
    def __init__(self, name=None, primary_key=False, default=None, ddl='text'):
        super().__init__(name, ddl, primary_key, default)


# 创建model或者model子类的实例时，会自动赋值name、bases、attr
class ModelMetaClass(type):
    def __new__(cls, name, bases, attrs): # 类的方法属性合集，而不是方法的
        # 排除Model类本身
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)
        tablename = attrs.get('__tablename__', None) or name
        logging.info('find model: %s table: %s' % (name, tablename))
        mappings = dict()
        fields = []
        primarykey = None
        for k, v in attrs.items():
            if isinstance(v, Field):
                logging.info('  found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
                if v.primary_key:
                    # 找到主键
                    # 循环搜索主键，如果找到多的主键则报错
                    if primarykey:
                        raise RuntimeError('duplicate primary key for field: %s' % k)
                    primarykey = k
                else:
                    fields.append(k)
        if not primarykey:
            raise RuntimeError('Primary key not found.')
        # attrs中删除了所有的值为Field类型的key
        for k in mappings.keys():
            attrs.pop(k)
        # 记录了非主键的field
        escaped_field = list(map(lambda f: '%s ' % f, fields))
        attrs['__mappings__'] = mappings  # 保存属性和列的映射关系
        attrs['__table__'] = tablename
        attrs['__primary_key__'] = primarykey  # 主键属性名
        attrs['__fields__'] = fields  # 除主键外的属性名
        # 构造默认的select update insert delete语句,语句什么意思？打印出来看看
        attrs['__select__'] = 'select %s,%s from %s' % (primarykey, ','.join(escaped_field), tablename)
        attrs['__insert__'] = 'insert into %s (%s, %s) values(%s)' % (tablename, ','.join(escaped_field), primarykey,
                                                                     create_args_string(len(escaped_field) + 1))
        # map(lambda f: '%s=?' % (mappings.get(f).name or f), fields)
        # Fields类的name属性用于记录sql表的列名，没有的话默认为key值
        attrs['__update__'] = 'update %s set %s where %s=?' % (tablename, ','.join(map(lambda f: '%s=?' % (mappings.get(f).name or f), fields)), primarykey)
        attrs['__delete__'] = 'delete from %s where %s=?' % (tablename, primarykey)
        return type.__new__(cls, name, bases, attrs)


# 未定义子类的构造函数时，会默认调用父类的构造函数
# cls是type的实例，self是cls的实例
class Model(dict, metaclass=ModelMetaClass):
    def __init__(self, **kw):
        super().__init__(**kw)

    # 实现特殊方法__getattr__和__setattr__，可以像引用普通字段一样写name['dzx']
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError('Model 类型没有%s属性' % key)

    def __setattr__(self, key, value):
        self[key] = value

    def getvalue(self, key):
        return getattr(self, key, None)  # 这个getattr、getattr是python内置函数

    def getvalueordefault(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                # callable判断对象能否被调用
                value = field.default() if callable(field.default) else field.default  # if的用法
                logging.debug('using default value for %s: %s' % (key, str(value)))
                setattr(self, key, value)
        return value

    @classmethod
    async def find(cls, pk):
        'find object by primary key'
        rs = await select('%s where %s=?' % (cls.__select__, cls.__primary_key__), [pk], 1)   # 看一下rs的类型
        logging.info(rs[0])
        if len(rs) == 0:
            return None
        logging.info(cls(**rs[0]))
        return cls(**rs[0]) # 返回cls类的一个实例,初始化的参数是rs[0]

    @classmethod
    async def findall(cls, where=None, args=None, **kw):
        sql=[cls.__select__]
        if where:
            sql.append(' where ')
            sql.append(where)
        if args is None:
            args = []
        orderBy = kw.get('orderBy', None)
        if orderBy:
            sql.append(' order by')
            sql.append(orderBy)
        limit = kw.get('limit', None)
        if limit is not None:
            sql.append('limit')
            if isinstance(limit, int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append('?, ?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))
        rs = await select(' '.join(sql), args)
        logging.info(rs)
        if len(rs) == 0:
            return None
        return [cls(**r) for r in rs]

    async def save(self):
        args = list(map(self.getvalueordefault, self.__fields__))
        args.append(self.getvalueordefault(self.__primary_key__))
        rows = await execute(self.__insert__, args)
        if rows != 1:
            logging.warning('failed to insert record: affected rows: %s' % rows)


if __name__ == '__main__':
    pass

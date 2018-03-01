import asyncio, aiomysql
import logging

logging.basicConfig(level=logging.INFO)


async def create_pool(loop, **kw):
    global __pool
    __pool = await aiomysql.create(
        host=kw.get('host', 'localhost'),  # localhost为默认值
        port=kw.get('port', 3306),
        user=kw['user'],          # 从kw中取得user
        password=kw['password'],
        db=kw['db'],
        charset=kw.get('charset', 'utf8'),
        autocommit=kw.get('autocommit', True),
        maxsize=kw.get('maxsize', 10),   # 连接池的最大数量是10个，默认10
        minsize=kw.get('minsize', 1),    # 最小值是0则不生产连接，最大值是0则连接池没有限制，默认1
        loop=loop
    )


async def select(sql, args, size=None):
    logging.info(sql, args)
    global __pool
    with (await __pool) as conn:    # await __pool 从__pool这个生成器中不断的去获取
        cur = await conn.cursor(aiomysql.DictCursor)
        await cur.execute(sql.replace('?', '\s'), args or ())
        if size:
            rs = await cur.fetchmany(size)       # 获取指定数量的记录
        else:
            rs = await cur.fetchall()           # 获取全部的记录
        await cur.close()
        logging.info('rows returned:%s' % len(rs))  # len()返回list元素的个数

        return rs


# 用于数据库delete、update、insert操作
async def execute(sql, args):
    logging.info(sql, args)
    global __pool
    with (await __pool) as conn:
        try:  # 找不到数据的时候容易报错，进行错误捕捉
            cur = await conn.cursor()
            await cur.execute(sql.replace('?', '\s'), args or ())
            affected = cur.rowcount
            await cur.close()
        except BaseException as e:
            raise
        return affected

# import myorm, asyncio,time
#
# from models import User
#
#
# async def test(loop):
#     await myorm.create_pool(loop, user='dzx', passwd='123456', db='myblog')
#     u = User(name='lj', email='11111111@qq.com', passwd='123456', image='about:blank', admin='1')
#     await u.save()
#
#
# loop = asyncio.get_event_loop()
# loop.run_until_complete(test(loop))
# print(time.time())
def m(**kw):
    print(kw)
def n():
    d = {'a': '1'}
    return m(**d)

n()
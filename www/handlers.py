import coreweb
import models


@coreweb.get('/')   # 放上装饰器相当于执行了语句index=get('/')(index)，因此有__method__属性
async def index(request):
    user = await models.User.findall()
    return {
        '__template__': 'test.html',
        'users': user
    }
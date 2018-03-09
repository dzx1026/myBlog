import coreweb
import models


@coreweb.get('/')
def index(request):
    user = yield from models.User.findall()
    return {
        '__template__': 'test.html',
        'users': user
    }
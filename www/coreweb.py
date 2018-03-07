import functools, logging
import asyncio
import inspect


# 定义了一个装饰器
def get(path):
    def decorator(func):
        @functools.wraps(func)    # 保存方法原来的签名
        def wrapper(*args, **kw):
            return func(*args, **kw)

        wrapper.__method__ = 'GET'
        wrapper.__route__ = path
        return wrapper
    return decorator


def post(path):
    def decorator(func):
        @functools.wraps(func)    # 保存方法原来的签名
        def wrapper(*args, **kw):
            return func(*args, **kw)

        wrapper.__method__ = 'POST'
        wrapper.__route__ = path
        return wrapper
    return decorator


class RequestHandler(object):
    def __init__(self, app, fn):
        self._app = app
        self._fn = fn

    async def __call__(self, request):
        kw = '参数'
        r = await self._fn(**kw)   # 不加**编译器就理解为位置变量。
        return r


# 用来注册一个URL处理函数
def add_route(app, fn):
    method = getattr(fn, '__method__', None)
    path = getattr(fn, '__route__', None)
    if path is None or method is None:
        raise ValueError('@get or @post not defined in %s.' % str(fn))
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):  # 是否生成器函数
        fn = asyncio.coroutine(fn)
    # inspect.signature(fn).parameters.keys()返回方法的所有参数
    logging.info('add route %s %s => %s(%s)' % (method, path, fn.__name__, ', '.join(inspect.signature(fn).parameters.keys())))
    app.router.add_route(method, path, RequestHandler(app, fn))


# 自动把handler模块的所有符合条件的函数注册了
def add_routes(app, module_name):
    #  rfind() 返回字符串最后一次出现的位置(从右向左查询)，如果没有匹配项则返回-1
    n = module_name.rfind('.')
    if n == -1:
        mod = __import__(module_name, globals(), locals()) # __import__动态加载模块
    else:
        name = module_name[n+1:]
        mod = getattr(__import__(module_name[:n], globals(), locals(), [name]), name)
        for attr in dir(mod):
            if attr.startswith('_'):
                continue
            fn = getattr(mod, attr)
            if callable(fn):
                method = getattr(fn, '__method__', None)
                path = getattr(fn, '__route__', None)
                if method and path:
                    add_route(app, fn)
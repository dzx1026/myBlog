import inspect
def get_required_kw_args(fn): # 收集没有默认值的命名关键字参数
    args = []
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY and param.default == inspect.Parameter.empty:
            args.append(name)
    return tuple(args)

def fn(*,job,name=123,**kw):
    print(name)
fn(job=2)
r= get_required_kw_args(fn)
print(r)
'''POSITIONAL_ONLY、VAR_POSITIONAL、KEYWORD_ONLY、VAR_KEYWORD、POSITIONAL_OR_KEYWORD
分别对应位置参数、可变参数、命名关键字参数、关键字参数，最后一个是位置参数或命名关键字参数'''
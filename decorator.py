import inspect
from functools import wraps

from bottle import request
from pydantic.main import BaseModel


def validator(func):
    @wraps(func)
    def inner(*args, **kwargs):
        _obj: BaseModel
        _sign = inspect.signature(func)
        # request url args
        path_kwargs = request.url_args
        for k, v in path_kwargs.items():
            # type change
            v = _sign.parameters.get(k).annotation(v)
            request.url_args[k] = v
            kwargs[k] = v

        # request query parameters
        for v in _sign.parameters.values():
            if v.name not in request.url_args.keys():
                # exclude url args
                request.query[v.name] = v.default
                kwargs[v.name] = v.default

        if query_args := request.query_string:
            for arg in query_args.split("&"):
                k = arg.split("=")[0]
                v = _sign.parameters.get(k).annotation(arg.split("=")[1])
                request.query[k] = v
                kwargs[k] = v

        # request json need use pydantic schema
        for v in _sign.parameters.values():
            if issubclass(v.annotation, BaseModel):
                if body := request.json:
                    _obj = v.annotation(**body)
                else:
                    _obj = v.annotation()
                kwargs[v.name] = _obj
                request.json = _obj.json()

        callback = func(*args, **kwargs)
        # return type
        if issubclass(_sign.return_annotation, BaseModel):
            return callback.json()
        else:
            return callback

    return inner

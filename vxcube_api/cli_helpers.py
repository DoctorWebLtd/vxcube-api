# Copyright (c) 2019 Doctor Web, Ltd.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software
# and associated documentation files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom
# the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies
# or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
# BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE

import json
import os
from functools import wraps

import click

from vxcube_api.api import VxCubeApi


class ApiInfo(object):
    def __init__(self, api_key, base_url, version):
        self.api_key = api_key
        self.base_url = base_url
        self.version = version


pass_api_info = click.make_pass_decorator(ApiInfo)


def pass_api(func):
    return pass_api_info(api_from_repo(func))


class ClientConfig(object):
    __slots__ = ("path", "values")

    def __init__(self, path=None):
        self.path = path or os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.json")
        self.values = self._default_config
        self.load()

    @property
    def _default_config(self):
        return {
            "api_key": None,
            "base_url": "https://vxcube.drweb.com/",
            "version": 2.0
        }

    def __getattr__(self, item):
        """Hooks getting fields from values varible."""
        return self.values.get(item)

    __getitem__ = __getattr__

    def load(self):
        if os.path.exists(self.path):
            with open(self.path) as file:
                self.values.update(json.load(file))

    def save(self, **kwargs):
        with open(self.path, "w") as file:
            json.dump(kwargs, file)
        self.values.update(kwargs)

    def delete(self):
        self.values = self._default_config
        if os.path.exists(self.path):
            os.remove(self.path)
            return True
        return False


client_config = ClientConfig()


def api_from_repo(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        api_keys = {
            "api_key": "",
            "base_url": "",
            "version": ""
        }
        api_keys.update(vars(args[0]))
        api = VxCubeApi(**api_keys)

        args = (api, )
        return func(*args, **kwargs)

    return wrapper


class Mutex(click.Option):
    def __init__(self, *args, **kwargs):
        self.not_required_if = kwargs.pop("not_required_if")
        if not self.not_required_if:
            raise click.UsageError("'not_required_if' parameter is required")

        kwargs["help"] = ("{orig_help}Option is mutually exclusive with [{options}]".format(
            orig_help=kwargs.get("help", ""), options=", ".join(self.not_required_if)).strip())
        super(Mutex, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        current_opt = self.name in opts
        for mutex_opt in self.not_required_if:
            if mutex_opt in opts or mutex_opt in args:
                if current_opt:
                    raise click.UsageError("Illegal usage: '{name}' is mutually exclusive with {opts}".format(
                        name=str(self.name), opts=str(mutex_opt)))
                else:
                    self.prompt = None
        return super(Mutex, self).handle_parse_result(ctx, opts, args)

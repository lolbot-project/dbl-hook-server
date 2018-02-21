"""
The MIT License (MIT)

Copyright (c) 2018 tilda

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""
from sanic import Sanic
from sanic.response import text
import ruamel.yaml
import aiohttp
import asyncio

# log_level = '[%(levelname) - %(name)] %(host)
# - %(request) [%(status)] | %(message) '
app = Sanic()

conf_file = open('config.yaml')
conf = ruamel.yaml.load(conf_file.read())

session = aiohttp.ClientSession()

sign = {
    'X-Served-By': 'dbl-hook-server (https://github.com/tilda/dbl-hook-server)'
}

strings = {
    'UPVOTE': ':tada: <@{}> has **upvoted** <@{}>!',
    'UNVOTE': ':frowning: <@{}> has **unvoted** <@{}>.'
}


@app.route('/post', methods=['POST'])
async def post_hook(request):
    # Usually we should only get requests from DBL or dev clients.
    # So we'll just tell everyone else to fuck off
    if request.host not in ['discordbots.org', 'localhost:8000']:
        print('warning: {} tried to post'.format(request.host))
        return text('Unauthorized', status=401, headers=sign)

    if not request.json:
        return text('Bad Request', status=400, headers=sign)
    else:
        rj = request.json  # character save hack

    if request.json['type'] == 'upvote':
        req = await session.post(conf['webhook'], json={
            'content': strings['UPVOTE'].format(rj['user'], rj['bot'])
        })

        if req.status in [200, 204]:
            return text('OK', headers=sign)
        else:
            print('something happened')
            t = await req.text()
            print(t)
            return text('Server Error', status=500, headers=sign)
    elif request.json['type'] == 'none':
        req = await session.post(conf['webhook'], json={
            'content': strings['UNVOTE'].format(rj['user'], rj['bot'])
        })

        if req.status == 200:
            return text('OK', headers=sign)
        else:
            return text('Server Error', status=500, headers=sign)

    return text('OK', headers=sign)

if __name__ == "__main__":
    # Run server, port 8000, no logging.
    serv = app.create_server(host="0.0.0.0", port=8000, debug=False, access_log=False)
    loop = asyncio.get_event_loop()
    task = asyncio.ensure_future(serv)
    loop.run_forever()

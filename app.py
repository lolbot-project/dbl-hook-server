from sanic import Sanic
from sanic.response import text
import ruamel.yaml
import aiohttp

#log_level = '[%(levelname) - %(name)] %(host) - %(request) [%(status)] | %(message) '
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
    if request.host != 'discordbots.org' or 'localhost:8000':
        return text('Unauthorized', status=401, headers=sign)
    if not request.json:
        return text('Bad Request', status=400, headers=sign)
    else:
        rj = request.json  # character save hack
    if request.json['type'] == 'upvote':
        req = await session.post(conf['webhook'], json={
            'content': strings['UPVOTE'].format(rj['user'], rj['bot'])
        })
        if req.status == 200:
            return text('OK', headers=sign)
        else:
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
    app.run(host="0.0.0.0", port=8000, debug=False, access_log=False)

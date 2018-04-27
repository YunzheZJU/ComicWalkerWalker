# -*- coding: utf-8 -*-
import requests
import re
import json
import struct

bookId = 'KDCW_KS11000007010003_68'


def generate(key):
    result = []
    i = -1
    for k in key:
        i += 1
        code = ord(k)
        code = code - 87 if code >= 97 else code - 48
        if i % 2 == 0:
            result.append(code * 16)
        else:
            result[(i - 1) / 2] += code
    return result


def spider():
    session = requests.session()
    resp = session.get('https://ssl.seiga.nicovideo.jp/api/v1/comicwalker/episodes/' + bookId + '/frames')
    frame = json.loads(resp.text)[u'data'][u'result']
    for page in frame:
        pid = page[u'id']
        url = page[u'meta'][u'source_url']
        key = generate(page[u'meta'][u'drm_hash'][:16])
        resp = session.get(url, stream=True)
        with open(str(pid) + '.jpg', 'wb') as f:
            i = -1
            for c in resp.content:
                i += 1
                f.write(struct.pack('B', ord(c) ^ key[i % 8]))
        print 'Finished: %s.jpg' % pid


if __name__ == '__main__':
    spider()

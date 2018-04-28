# -*- coding: utf-8 -*-
import requests
import re
import json
import struct
import os


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


def spider(title, bid):
    if not os.path.exists(title):
        os.mkdir(title)
    else:
        print u'Folder %s already exists. Files with the same name may be covered. Make backups if needed!\n' \
              u'目录%s已存在，同名文件可能会被覆盖，请注意备份！'
        raw_input(u'Press ENTER to continue:\n' \
                  u'按回车以继续：')
    progress = 'Frame'
    resp = session.get('https://ssl.seiga.nicovideo.jp/api/v1/comicwalker/episodes/' + bid + '/frames')
    frame = json.loads(resp.text)[u'data'][u'result']
    progress = 'Decode'
    for page in frame:
        pid = page[u'id']
        url = page[u'meta'][u'source_url']
        key = generate(page[u'meta'][u'drm_hash'][:16])
        resp = session.get(url, stream=True)
        with open(os.path.join(title, str(pid) + '.jpg'), 'wb') as f:
            i = -1
            for c in resp.content:
                i += 1
                f.write(struct.pack('B', ord(c) ^ key[i % 8]))
        print '%s/%s.jpg' % (title, pid)


if __name__ == '__main__':
    error = {
        'Session': u'Fail to create session\n'
                   u'创建会话失败',
        'Address': u'Fail to open url\n'
                   u'打开链接失败',
        'List': u'Fail to find chapter list\n'
                u'未找到章节列表',
        'Chapter': u'Unrecognized chapter info exists\n'
                   u'出现了未能解析的章节信息',
        'Spider': u'Error occurred during fetching\n'
                  u'抓取过程中出现错误',
        'Frame': u'Fail to get frame\n'
                 u'未能获得漫画目录',
        'Decode': u'Error occurred during decoding files\n'
                  u'解码过程中出现错误'
    }
    progress = 'Session'
    try:
        session = requests.session()
        progress = 'Address'
        while 1:
            print u'Enter the address of detail page in Comic-Walker, for example: ' \
                  u'https://comic-walker.com/contents/detail/KDCW_KS11000007010000_68/ \n' \
                  u'输入漫画在Comic Walker中的详情地址, 如：' \
                  u'https://comic-walker.com/contents/detail/KDCW_KS11000007010000_68/ '
            address = raw_input(u'https://')
            # Filter the address
            r = r'^(?:https?://)?(comic-walker.com/contents/detail/(KDCW_[A-Z]{2}[0-9]{14}_[0-9]{2}))/?.*$'
            m = re.match(r, address)
            resp = session.get('https://' + m.group(1))
            progress = 'List'
            r = r'.*detail_backnumberList(.*?)</ul'
            ul = re.match(r, resp.text, re.S)
            r = r'a.*?title="(.*?)" href="(.*?)"'
            it = re.finditer(r, ul.group(1), re.S)
            progress = 'Chapter'
            for match in it:
                title = match.group(1)
                url = match.group(2)
                print u'title: %s, url: %s' % (title, url)
                r = r'.*cid=(KDCW_[A-Z]{2}[0-9]{14}_[0-9]{2})'
                bid = re.match(r, url).group(1)
                progress = 'Spider'
                spider(title, bid)
    except:
        print error[progress]

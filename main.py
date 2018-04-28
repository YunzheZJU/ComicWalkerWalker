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


def fetchEpisode(title, cid):
    if not os.path.exists(title):
        os.mkdir(title)
    else:
        print u'\n' \
              u'Folder %s already exists. Files with the same name may be covered. Make backups if needed!\n' \
              u'目录%s已存在，同名文件可能会被覆盖，请注意备份！' % (title, title)
        raw_input(u'Press ENTER to continue:\n' \
                  u'按回车以继续：')
        if not os.path.exists(title):
            os.mkdir(title)
    progress = 'Frame'
    resp = session.get('https://ssl.seiga.nicovideo.jp/api/v1/comicwalker/episodes/' + cid + '/frames', timeout=30)
    frame = json.loads(resp.text)[u'data'][u'result']
    progress = 'Decode'
    for page in frame:
        pid = page[u'id']
        url = page[u'meta'][u'source_url']
        key = generate(page[u'meta'][u'drm_hash'][:16])
        resp = session.get(url, stream=True, timeout=30)
        with open(os.path.join(title, str(pid) + '.jpg'), 'wb') as f:
            i = -1
            for c in resp.content:
                i += 1
                f.write(struct.pack('B', ord(c) ^ key[i % 8]))
        print '%s/%s.jpg' % (title, pid)


def fetchDetail(url):
    resp = session.get(url, timeout=30)
    progress = 'List'
    ul = reg['li'].split(reg['list'].match(resp.text).group(1))
    for item in ul:
        match = reg['episode'].match(item)
        if match is None: continue
        title = match.group(1)
        url = match.group(2)
        print u'Processing 《%s》...' % (title)
        cid = reg['cid'].match(url).group(1)
        progress = 'Spider'
        fetchEpisode(title, cid)


if __name__ == '__main__':
    error = {
        'Session': u'\n' \
                   u'Fail to create session\n'
                   u'创建会话失败',
        'Address': u'\n' \
                   u'Fail to open url\n'
                   u'打开链接失败',
        'List': u'\n' \
                u'Fail to find chapter list\n'
                u'未找到章节列表',
        'Chapter': u'\n' \
                   u'Unrecognized chapter info exists\n'
                   u'出现了未能解析的章节信息',
        'Spider': u'\n' \
                  u'Error occurred during fetching\n'
                  u'抓取过程中出现错误',
        'Frame': u'\n' \
                 u'Fail to get frame\n'
                 u'未能获得漫画目录',
        'Decode': u'\n' \
                  u'Error occurred during decoding files\n'
                  u'解码过程中出现错误',
        'Title': u'\n' \
                 u'Fail to find book/chapter title\n'
                 u'未找到书名/章节名',
        'Choose': u'\n' \
                  u'Please enter a valid number\n'
                  u'请输入一个合法的数字',
        'Search': u'\n' \
                  u'Error occurred during searching\n'
                  u'搜索过程中发生错误'
    }
    reg = {
        'detail': re.compile(
            r'^(?:https?://)?comic-walker.com(/contents/detail/(KDCW_[A-Z]{2}[0-9]{14}_[0-9]{2}))/?.*$'),
        'viewer': re.compile(
            r'^(?:https?://)?comic-walker.com(/viewer/.*cid=(KDCW_[A-Z]{2}[0-9]{14}_[0-9]{2})).*/?.*$'),
        'list': re.compile(r'^.*detail_backnumberList(.*?)</ul.*$', re.S),
        'episode': re.compile(r'^.*a.*?title="(.*?)" href="(.*?)".*', re.S),
        'cid': re.compile(r'^.*cid=(KDCW_[A-Z]{2}[0-9]{14}_[0-9]{2}).*$'),
        'ctitle': re.compile(r'^.*"content_title":"(.*?)".*$', re.S),
        'etitle': re.compile(r'^.*"episode_title":"(.*?)".*$', re.S),
        'searchResultNum': re.compile(r'^.*searchResultNum.*?>(\d+)</.*$', re.S),
        'searchResultList': re.compile(r'^.*tileList(?:\s|").*?>(.*?)</ul.*$', re.S),
        'searchResult': re.compile(r'^.*a.*href="(.*?)".*h2.*span>(.*?)</span.*', re.S),
        'li': re.compile(r'</li>'),
        's': re.compile(r'\s+')

    }
    progress = 'Session'
    try:
        session = requests.session()
        session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
        while 1:
            print u'\n\tEnter the address of detail page or vier page in Comic-Walker. ' \
                  u'Split multiple addresses with a space.' \
                  u'Unrecognized fragments will be set as keywords.' \
                  u'\n\t输入漫画在Comic Walker中的详情页或阅读页地址，多个地址以空格分隔，不能识别的字段将被认为是搜索关键字' \
                  u'\n\tExample: https://comic-walker.com/contents/detail/KDCW_KS11000007010000_68/ ' \
                  u'https://comic-walker.com/viewer/?tw=2&dlcl=ja&cid=KDCW_KS11000007010053_68 ' \
                  u'蜘蛛ですが、なにか？'
            addressList = reg['s'].split(raw_input(u'请：\n'))
            for address in addressList:
                if address == '': continue
                progress = 'Address'
                # Filter the address
                m = reg['detail'].match(address)
                if m is None:
                    m = reg['viewer'].match(address)
                    if m is None:
                        print '\n\tType: Keyword'
                        url = 'https://comic-walker.com/contents/search/?q=' + address
                        resp = session.get(url, timeout=30)
                        progress = 'Search'
                        resultNum = reg['searchResultNum'].match(resp.text).group(1)
                        if int(resultNum) == 0:
                            print u'\n\tThere is no searching result related to keyword "%s"' \
                                  u'\n\t没有符合关键词%s的搜索结果' % (address, address)
                        else:
                            print u'\n\tThere are %s result(s) found (The first 25 items will be shown)' \
                                  u'\n\t搜索结果共%s项 （仅显示前25项）' % (resultNum, resultNum)
                            resultNum = 25 if resultNum > 25 else resultNum
                            ul = reg['li'].split(reg['searchResultList'].match(resp.text).group(1))
                            i = 1
                            list = []
                            for item in ul:
                                match = reg['searchResult'].match(item)
                                if match is None: continue
                                list.append({'href': match.group(1), 'title': match.group(2)})
                                print u'{}: 《{}》'.format(i, list[i - 1]['title'])
                                i += 1
                            input = 0
                            while 1:
                                input = raw_input(
                                    u'\n\tWhich matches your target? Please enter the number before the title'
                                    u'\n\t以上哪一项是您要寻找的漫画？请输入序号\n')
                                progress = 'Choose'
                                input = int(input)
                                if 1 <= input <= len(list):
                                    print u'\n\tGet it：%s' \
                                          u'\n\t开始抓取：%s' % (list[input - 1]['title'], list[input - 1]['title'])
                                    break
                                elif input == -1:
                                    print u'\n\tStop searching' \
                                          u'\n\t搜索中止'
                                    break
                                else:
                                    print u'\n\tPlease enter a valid number between 1 and %s, ' \
                                          u'where -1 stands for stop searching' \
                                          u'\n\t请输入一个介于1和%s之间的数字，-1表示中止搜索' % (len(list), len(list))
                            fetchDetail('https://comic-walker.com' + list[input - 1]['href'])
                    else:
                        print '\n\tType: Viewer URL'
                        cid = m.group(2)
                        url = 'https://comic-walker.com' + m.group(1)
                        resp = session.get(url, timeout=30)
                        progress = 'Title'
                        ctitle = reg['ctitle'].match(resp.text)
                        etitle = reg['etitle'].match(resp.text)
                        fetchEpisode(ctitle.group(1) + ' ' + etitle.group(1), cid)
                else:
                    print '\n\tType: Detail URL'
                    fetchDetail('https://comic-walker.com' + m.group(1))
                print '\n\tDone for %s' % address
    except requests.exceptions.RequestException, e:
        print u'\n\tNetwork Error! Something went wrong with your network...' \
              u'\n\t网络连接不畅...'
    except BaseException, e:
        print error[progress]
        print 'Details: ', e

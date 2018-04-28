# -*- coding: utf-8 -*-
import requests
import re
import json
import struct
import os
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

ERROR = {
    'Session': u'\n\tFail to create session'
               u'\n\t创建会话失败',
    'Address': u'\n\tFail to open url'
               u'\n\t打开链接失败',
    'List': u'\n\tFail to find chapter list'
            u'\n\t未找到章节列表',
    'Chapter': u'\n\tUnrecognized chapter info exists'
               u'\n\t出现了未能解析的章节信息',
    'Spider': u'\n\tError occurred during fetching'
              u'\n\t抓取过程中出现错误',
    'Frame': u'\n\tFail to get frame'
             u'\n\t未能获得漫画目录',
    'Decode': u'\n\tError occurred during decoding files'
              u'\n\t解码过程中出现错误',
    'Title': u'\n\tFail to find book/chapter title'
             u'\n\t未找到书名/章节名',
    'Choose': u'\n\tPlease enter a valid number'
              u'\n\t请输入一个合法的数字',
    'Search': u'\n\tError occurred during searching'
              u'\n\t搜索过程中发生错误'
}
REG = {
    'detail': re.compile(
        r'^(?:https?://)?comic-walker.com(/contents/detail/(KDCW_[A-Z]{2}[0-9]{14}_[0-9]{2}))/?.*$'),
    'viewer': re.compile(
        r'^(?:https?://)?comic-walker.com(/viewer/.*?cid=(KDCW_[A-Z]{2}[0-9]{14}_[0-9]{2})).*/?.*$'),
    'list': re.compile(r'^.*detail_backnumberList(.*?)</ul.*$', re.S),
    'episode': re.compile(r'a.*?title="(.*?)" href="(.*?)"', re.S),
    'cid': re.compile(r'^.*cid=(KDCW_[A-Z]{2}[0-9]{14}_[0-9]{2}).*$'),
    'ctitle': re.compile(r'^.*"content_title":"(.*?)".*$', re.S),
    'etitle': re.compile(r'^.*"episode_title":"(.*?)".*$', re.S),
    'searchResultNum': re.compile(r'^.*searchResultNum.*?>(\d+)</.*$', re.S),
    'searchResultList': re.compile(r'^.*tileList(?:\s|").*?>(.*?)</ul.*$', re.S),
    'searchResult': re.compile(r'a.*?href="(.*?)".*?h2.*?span>(.*?)</span', re.S),
    'li': re.compile(r'</li>'),
    's': re.compile(r'\s+')
}
GLOBAL = {
    'progress': 'Session'
}


def set_progress(status):
    GLOBAL['progress'] = status
    return status


def get_progress():
    return GLOBAL['progress']


def try_except(func):
    def anonymous(*args, **kwargs):
        # try:
        return func(*args, **kwargs)
        # except requests.exceptions.RequestException:
        #     print u'\n\tNetwork Error! Something went wrong with your network...' \
        #           u'\n\t网络连接不畅...'
        # except BaseException, e:
        #     print ERROR[get_progress()]
        #     print u'Details: ', e

    return anonymous


def generate(key):
    result = []
    for i, k in enumerate(key):
        code = ord(k)
        code = code - 87 if code >= 97 else code - 48
        if i % 2 == 0:
            result.append(code * 16)
        else:
            result[(i - 1) / 2] += code
    return result


@try_except
def fetch_page(session, title, page):
    pid = page[u'id']
    print u'\t%s/%s.jpg...' % (title, pid),
    with open(os.path.join(title, str(pid) + '.jpg'), 'wb') as f:
        url = page[u'meta'][u'source_url']
        key = generate(page[u'meta'][u'drm_hash'][:16])
        resp = session.get(url, stream=True, timeout=30)
        for i, c in enumerate(resp.content):
            f.write(struct.pack('B', ord(c) ^ key[i % 8]))
    print u'OK'


@try_except
def fetch_episode(session, title, cid):
    if not os.path.exists(title):
        os.mkdir(title)
    else:
        print u'\n\tFolder %s already exists. Files with the same name may be covered. Make backups if needed!' \
              u'\n\t目录%s已存在，同名文件可能会被覆盖，请注意备份！' % ((title,) * 2)
        raw_input(u'\n\tPress ENTER to continue: '
                  u'\n\t按回车以继续：')
        if not os.path.exists(title):
            os.mkdir(title)
    set_progress('Frame')
    resp = session.get('https://ssl.seiga.nicovideo.jp/api/v1/comicwalker/episodes/' + cid + '/frames', timeout=30)
    frame = json.loads(resp.text)[u'data'][u'result']
    set_progress('Decode')
    for page in frame:
        fetch_page(session, title, page)


@try_except
def fetch_detail(session, url):
    resp = session.get(url, timeout=30)
    set_progress('List')
    it = REG['episode'].finditer(REG['list'].match(resp.text).group(1))
    for item in it:
        title = item.group(1)
        url = item.group(2)
        print u'Processing 《%s》...' % title
        cid = REG['cid'].match(url).group(1)
        set_progress('Spider')
        fetch_episode(session, title, cid)


@try_except
def spider():
    session = requests.session()
    session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
    while 1:
        print u'\n\tEnter the address of detail page or viewer page in Comic-Walker. ' \
              u'Split multiple addresses with a space.' \
              u'Unrecognized fragments will be set as keywords.' \
              u'\n\t输入漫画在Comic Walker中的详情页或阅读页地址，多个地址以空格分隔，不能识别的字段将被认为是搜索关键字' \
              u'\n\tExample: https://comic-walker.com/contents/detail/KDCW_KS11000007010000_68/ ' \
              u'https://comic-walker.com/viewer/?tw=2&dlcl=ja&cid=KDCW_KS11000007010053_68 ' \
              u'蜘蛛ですが、なにか？'
        address_list = REG['s'].split(raw_input(u'请：\n'))
        for address in address_list:
            if address == '':
                continue
            set_progress('Address')
            # Filter the address
            m = REG['detail'].match(address)
            if m is None:
                m = REG['viewer'].match(address)
                if m is None:
                    print u'\n\tType: Keyword'
                    url = 'https://comic-walker.com/contents/search/?q=' + address
                    resp = session.get(url, timeout=30)
                    set_progress('Search')
                    result_num = REG['searchResultNum'].match(resp.text).group(1)
                    if int(result_num) == 0:
                        print u'\n\tThere is no searching result related to keyword "%s"' \
                              u'\n\t没有符合关键词%s的搜索结果' % ((address,) * 2)
                    else:
                        print u'\n\tThere are %s result(s) found (The first 25 items will be shown)' \
                              u'\n\t搜索结果共%s项 （仅显示前25项）' % ((result_num,) * 2)
                        it = REG['searchResult'].finditer(REG['searchResultList'].match(resp.text).group(1))
                        result_list = []
                        for i, item in enumerate(it):
                            result_list.append({'href': item.group(1), 'title': item.group(2)})
                            print u'%s: 《%s》' % (i + 1, result_list[i]['title'])
                        while 1:
                            choice = raw_input(
                                u'\n\tWhich matches your target? Please enter the number before the title'
                                u'\n\t以上哪一项是您要寻找的漫画？请输入序号\n')
                            set_progress('Choose')
                            choice = int(choice)
                            if 1 <= choice <= len(result_list):
                                print u'\n\tGet it：%s\n\t开始抓取：%s' % ((result_list[choice - 1]['title'],) * 2)
                                break
                            elif choice == -1:
                                print u'\n\tStop searching' \
                                      u'\n\t搜索中止'
                                break
                            else:
                                print u'\n\tPlease enter a valid number larger than 0 while smaller than %s, ' \
                                      u'where -1 stands for stopping searching' \
                                      u'\n\t请输入一个大于0小于等于%s的数字，-1表示中止搜索' % ((len(result_list),) * 2)
                        fetch_detail(session, 'https://comic-walker.com' + result_list[choice - 1]['href'])
                else:
                    print u'\n\tType: Viewer URL'
                    cid = m.group(2)
                    url = 'https://comic-walker.com' + m.group(1)
                    resp = session.get(url, timeout=30)
                    set_progress('Title')
                    ctitle = REG['ctitle'].match(resp.text).group(1)
                    etitle = REG['etitle'].match(resp.text).group(1)
                    fetch_episode(session, ctitle + ' ' + etitle, cid)
            else:
                print u'\n\tType: Detail URL'
                fetch_detail(session, 'https://comic-walker.com' + m.group(1))
            print u'\n\tDone for %s' % address


if __name__ == '__main__':
    spider()

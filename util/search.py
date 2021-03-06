import time
import re
import os

import jieba

from public import log
from public.db.search_db import SearchDB
from public.settings import (SEARCH_PARTICIPLE_PATH, SEARCH_PARTICIPLE_FILE_NAME,
                             SEARCH_PARTICIPLE_SIZE)
from util import os_path

FILTER = re.compile(r"[\~\`\!\@\#\$%\^\&\*\(\)\_\-\+\=\{\[\}\]\|\\\:\;\"\'\<\,\>\.\?\/·！￥…（）【】、“”‘’：；，。？★◆]")


def chinese_to_number(chinese):
    '''
    把中文字符转换为如下格式：
        中国（20013， 22269）
    英文字符转化为小写返回：
        HELLO hello
    中英混合：
        先把英文转化为小写，在返回
        T恤（116,24676）
    :param chinese: 需要转化的字符
    :return:
    '''
    if isinstance(chinese, str):
        chinese = chinese.strip()
        chinese = chinese.replace('\\', '').replace('/', '')
        chinese = chinese.lower()
        codes = list()
        for c in chinese:
            codes.append(ord(c))
        if codes:
            return True, codes
        else:
            return False, codes
    else:
        return False,None

def splicing_path(file_codes):
    '''
    把ascii形式的关键字，拼装成路径
    :param file_codes: [38889,29256]
    :return: 文件夹路径，文件路径
    '''

    file_map = dict()
    if file_codes:
        shunt = str(int(file_codes[0]) // SEARCH_PARTICIPLE_SIZE)
        code_path = os.path.join(SEARCH_PARTICIPLE_PATH, shunt)
        folder_path = ""
        file_path = ''
        for file_code in file_codes:
            folder_path =str(file_code) if file_path == '' else folder_path + os.sep + str(file_code)
            file_path = str(file_code) if file_path == "" else file_path + '-' + str(file_code)

        # 拼装路径
        folder_path = os.path.join(code_path, folder_path)
        file_path = os.path.join(folder_path, SEARCH_PARTICIPLE_FILE_NAME)
        file_map['folder_path'] = folder_path
        file_map['file_path'] = file_path
        return file_map
    else:
        return False

def split_result(r, re_filter):
    '''
    拆分关键词
    :param r:
    :param re_filter:
    :return:
    '''
    title = r.get('title')
    dsc = r.get('goods_desc')
    title = re.sub(re_filter,' ', title)
    dsc = re.sub(re_filter,' ', dsc)

    titles1 = jieba.lcut_for_search(title)
    titles3 = jieba.lcut(title, cut_all=True)
    titles = titles1 + titles3

    dscs1 = jieba.lcut_for_search(dsc)
    dscs3 = jieba.lcut(dsc, cut_all=True)
    types = dscs1 + dscs3

    jbs = set(titles + types)
    search_map = dict()
    search_map['id'] = r.get('id')
    search_map['result'] = list()

    if '' in jbs:
        jbs.remove('')
    if ' ' in jbs:
        jbs.remove(' ')
    for jb in jbs:
        flag, result = chinese_to_number(jb)
        # 如果有数据
        if flag:
            search_map['result'].append(result)
    return search_map
def save_to_store(search_map):
    '''
    把每个商品的关键词保存到本地
    :param search_map:
    :return:
    '''
    id = search_map.get('id')
    result = search_map.get('result')
    for r in result:
        # 说明文件夹和文件路径已经生成
        file_map = splicing_path(r)
        if file_map:
            # 判断文件或者文件夹是否存在
            os_path.create_folder(file_map.get('folder_path'))
            os_path.write_file(file_map.get('file_path'), str(id) + '-')
        else:
            return False
class SearchParticiple(object):
    '''
    分词工具类
        1.从数据库获取一定量的数据
        2.拆分关键词
        3，保存关键词
    '''

    def __init__(self):
        self.search_db = SearchDB()
        log.logging.info('[INFO] Search init success')
        # 过滤垃圾字符
        self.filter = FILTER

    def db_split(self):
        '''
        拆分数据库字段：
            id,title,goods_brief
        :return:
        '''
        this_page = 0
        page_size = 500
        while True:
            results = self.search_db.find_commoditys(this_page, page_size)
            if results:
                this_page = this_page + page_size
                for r in results:
                    search_map = split_result(r, self.filter)
                    save_to_store(search_map)
                    log.logging.info('[INFO] save to store {0}'.format(search_map['id']))
            else:
                break

def start_participle():
    start_time = time.time()
    SearchParticiple().db_split()
    log.logging.info('[INFO] Search participle success')
    log.logging.info('[INFO] Ibantang Ok time cost: {0}'.format(time.time() - start_time))

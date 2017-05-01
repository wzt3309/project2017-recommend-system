# -*- coding: UTF-8 -*-
# ------------------------------------------------------
# Name:             load_movielines_data.py
# Purpose:          读取测试集和训练集，以字典格式存储在内存中
#
# Author:           ztwang
# ------------------------------------------------------

import sys
sys.path.append("../..")
import os
import config
import codecs
import random

U_DATA = os.path.join(config.DATA_100k_DIR, 'u.data')
U1_BASE = os.path.join(config.DATA_100k_DIR, 'u1.base')
U1_TEST = os.path.join(config.DATA_100k_DIR, 'u1.test')


def load_trains(file_name=U1_BASE):
    """ 加载指定的训练集文件；
        默认为/data/ml-100k/u1.base
    """
    if not validate_file(file_name):
        file_name = U1_BASE
    trains = {}
    with codecs.open(file_name, 'rb') as fi:
        fi.readline()
        for line in fi:
            (userid, movieid, rating, ts) = line.split('\t')
            trains.setdefault(userid, {})                     # trains字典格式为{'userid':{}}
            trains[userid][movieid] = float(rating)

    return trains                                             # trains字典结果为{'userid':{'movieid1':rating1, 'movieid2':rating2},...}


def load_tests(file_name=U1_TEST):
    """ 加载指定的测试集文件；
        默认为/data/ml-100k/u1.test
    """
    if not validate_file(file_name):
        file_name = U1_TEST
    tests = {}
    with codecs.open(file_name, 'rb') as fi:
        fi.readline()
        for line in fi:
            (userid, movieid, rating, ts) = line.split('\t')
            tests.setdefault(userid, {})
            tests[userid][movieid] = float(rating)

    return tests


def train_test_split(file_name, pviot=0.67):
    """从原始的movelines数据文件切分训练/测试集
    """
    if not validate_file(file_name):
        file_name = U_DATA
    trains = {}
    tests = {}
    with open(file_name, 'r') as fi:
        lines = fi.readlines()
        for line in lines:
            (userid, movieid, rating, ts) = line.split('::')    # 在文件"ratings.dat" 数据格式为UserID::MovieID::Rating::Timestamp
            if random.random() < pviot:
                trains.setdefault(userid, {})
                trains[userid][movieid] = float(rating)
            else:
                tests.setdefault(userid, {})
                tests[userid][movieid] = float(rating)

    return trains, tests


def save_records(file_name, records):
    """保存协同过滤模型测试记录
    """
    if not file_name or file_name.split() == '':
        file_name = 'temp_records'
    file_name = os.path.join(config.RECORDS_DIR, file_name)
    with open(file_name, 'w') as fo:
        for userid, movieid, pre_rating, act_rating in records:
            fo.write('%6s\t%6s\t%s\t%s\n' %
                     (userid, movieid, str(int(pre_rating)), str(int(act_rating))))


def validate_file(file_name):
    if not file_name or file_name.split() == '':
        print '文件名不能为空'
        return False
    if not os.path.exists(file_name):
        print '文件\'%s\'不存在' % file_name
        return False
    return True


if __name__ == "__main__":
    print(""" 这个部分可以进行上面2个函数测试 """)

    trains = load_trains()
    tests = load_tests()

    print(len(trains))
    print(len(tests))
    print(""" 测试通过 """)

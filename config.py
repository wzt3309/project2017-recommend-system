# -*- coding: UTF-8 -*-
# ----------------------------------------------------
# Name:             config.py
# Purpose:          定义各模块文件使用常量
#
# Author:           ztwang
# ----------------------------------------------------

import os

# 项目根目录
ROOT = os.path.split(os.path.realpath(__file__))[0]
# 项目数据根目录
DATA_BASE_DIR = os.path.join(ROOT, 'data')
# Movielines-1m数据目录
DATA_1M_DIR = os.path.join(DATA_BASE_DIR, 'ml-1m')
# Movielines-100k数据目录
DATA_100k_DIR = os.path.join(DATA_BASE_DIR, 'ml-100k')
# Movielines推荐系统推荐测试结果保存目录
RECORDS_DIR = os.path.join(ROOT, 'records')


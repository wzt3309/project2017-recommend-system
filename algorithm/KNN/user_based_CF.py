# -*- coding: UTF-8 -*-
# ------------------------------------------------------
# Name:             user_based_CF.py
# Purpose:          基于用户的协同过滤算法
#
# Author:           ztwang
# ------------------------------------------------------
from process_movielines_data import load_trains
from process_movielines_data import load_tests
from process_movielines_data import train_test_split
from process_movielines_data import save_records
from math import pow, sqrt
import operator
import datetime

SAVE_RECORDS_FILE_NAME = 'KNN_USERBASED_CF'


class UserBasedCF:
    def __init__(self, train=None, test=None):
        self.train_file = train
        self.test_file = test

    def read_data(self, train=None, test=None):
        """ 从指定'训练/测试'文件加载'训练/测试'集
        """
        self.train_file = train or self.train_file
        self.test_file = test or self.test_file
        # 加载训练集
        if self.train_file:
            self.trains = load_trains(self.train_file)
        else:
            self.trains = load_trains()
        # 加载测试集
        if self.test_file:
            self.tests = load_tests(self.test_file)
        else:
            self.tests = load_tests()

        print 'load trains/tests from %s/%s successful' % (self.train_file, self.test_file)
        print 'trains(%s), tests(%s)' % (repr(len(self.trains)), repr(len(self.tests)))

    def generate_dataset(self, file_name, pviot=0.67):
        """ 从原始的movelines数据文件切分训练/测试集
        """
        self.trains, self.tests = train_test_split(file_name, pviot=0.67)
        print 'generate trains/tests from %s successful' % file_name
        print 'trains(%s), tests(%s)' % (repr(len(self.trains)), repr(len(self.tests)))


def sim_user(dataset, user1, user2):
    """ 计算user1与user2的相似度

        @param  dataset     转化为字典的数据集

        @param  user1       user1的userid

        @param  user2       user2的userid

        @return similarity  -1,0,正数
    """
    sim = {}

    # 查找双方都评价过的项
    for movie in dataset[user1]:
        if movie in dataset[user2]:
            sim[movie] = 1
    # 相同项个数
    n = len(sim)
    # 不存在相同元素,user1与user2相似度为-1
    if n < 1:
        return -1

    # 偏好和
    sum1 = float(sum([dataset[user1][movie] for movie in sim]))
    sum2 = float(sum([dataset[user2][movie] for movie in sim]))

    # 偏好平方和
    sum1sq = float(sum([pow(dataset[user1][movie], 2) for movie in sim]))
    sum2sq = float(sum([pow(dataset[user2][movie], 2) for movie in sim]))

    # 求乘积之和
    summulti = float(
        sum([dataset[user1][movie] * dataset[user2][movie] for movie in sim]))

    num1 = summulti - (sum1 * sum2 / n)
    num2 = sqrt((sum1sq - pow(sum1, 2) / n) * (sum2sq - pow(sum2, 2) / n))
    if num2 == 0:
        return 0

    similarity = num1 / num2

    return similarity


def knn_matches_users(dataset, user, movie, k=20, similarity=sim_user):
    """ 从dataset中获取对movie有过评价的用户，并从中找出与user最相似的k个

        @param dataset          转化为字典的数据集

        @param user             userid

        @param movie            movieid

        @param k                取k个近邻

        @param similarity       比较用户相似度的函数

        @return 用户列表         不足k个返回全部,否则返回k个
    """

    user_set = []
    user_sim_dict = {}
    k_matches_users = []

    # 找出所有评价过movie的用户
    for user in dataset:
        if movie in dataset[user]:
            user_set.append(user)

    # 计算user_set中的用户与user的相似性
    user_sim_dict = {
        other: similarity(dataset, user, other)
        for other in user_set if other != user
    }
    user_sim_dict = sorted(user_sim_dict.iteritems(), key=operator.itemgetter(1), reverse=True)

    if len(user_sim_dict) < k:
        for user in user_sim_dict:
            k_matches_users.append(user[0])
    else:
        for user in user_sim_dict[0:k]:
            k_matches_users.append(user[0])

    return k_matches_users


def user_movies_avg(dataset, user):
    """ 计算用户user所评价电影的平均评分

        @param dataset 转化为字典的数据集

        @param user    userid

        @return avg    平均评分,新用户没对电影进行评价则返回0
    """
    n = 0
    score_sum = 0
    for movie in dataset[user]:
        score_sum = dataset[user][movie]
        n += 1
    if n == 0:
        avg = 0
    else:
        avg = float(score_sum) / n

    return avg


def predict_user_movie(dataset, user, movie, k=20, similarity=sim_user):
    """ 预测用户对电影的评分

        @param dataset      数据训练集

        @param user

        @param movie

        @param k

        @param similarity

        @return rating      不存在相似用户(该movie没有用户评分过)返回用户自身平均评分，
                            否则返回近邻用户对movie的加权评分
                            返回0: 该用户没有评价过任何电影，冷启动   
                            大于0：根据近邻用户推测或该用户平均评分
    """
    weight_avg = 0.0
    sim_sums = 0.0
    rating = 0.0

    # 获取user的k个近邻用户
    user_neighbors = knn_matches_users(dataset, user, movie, k, similarity)

    # 获取user对电影的评分平均值
    avg_user = user_movies_avg(dataset, user)

    # 计算user的近邻用户对电影的加权评分
    for other in user_neighbors:
        sim = similarity(dataset, user, other[0])
        # 相似度sim可能为负值，user与other没有看过相同的电影
        # TOCDO 此处暂时将other对该movie的评分对user的影响忽略
        if sim < 0:
            continue
        else:
            avg_other = user_movies_avg(dataset, other)
            sim_sums += sim
            weight_avg += (dataset[other][movie] - avg_other) * sim

    if sim_sums == 0:
        rating = avg_user
    else:
        rating = (avg_user + weight_avg / sim_sums)

    return rating


def eval_by_RMSE(records):
    """ 使用RMSE评价预测结果

        @param records  是一个矩阵，每行为[userid,movieid,pre_rating,act_rating]
    """
    sum = 0.0
    rmse = 0.0
    for record in records:
        pre_rating, act_rating = int(record[2]), int(record[3])
        sum += pow((act_rating - pre_rating), 2)
    rmse = sqrt(sum / float(len(records)))

    return rmse


def eval_by_MAE(records):
    """ 使用MAE评价预测结果

        @param records  是一个矩阵，每行为[userid,movieid,pre_rating,act_rating]
    """
    sum = 0.0
    mae = 0.0
    for record in records:
        pre_rating, act_rating = int(record[2]), int(record[3])
        sum += abs(act_rating - pre_rating)
    mae = sum / float(len(records))

    return mae


def recommend_movies(userBaseCF, user, movie_list, k=20, similarity=sim_user):
    """ 从电影列表中向某个用户推荐size长度的电影

        @param userBaseCF  UserBasedCF(train=None, test=None)

        @param user        userid,新来的用户要先注册，在数据库中留下自身的记录

        @param movie_list  待推荐电影的列表[moveid1,moveid2...]

        @param size        推荐列表的长度

        @param k           KNN聚类的大小

        @param similarity  相似度计算函数
    """
    ratings = []
    trainset = userBaseCF.trains

    for movie in movie_list:
        pre_rating = predict_user_movie(trainset, user, movie, k, sim_user)
        ratings.append((movie, pre_rating))
    return ratings


def recommend_top(ratings, top=10):
    ratings = sorted(ratings, key=operator.itemgetter(1), reverse=True)
    if len(ratings) < top:
        return ratings
    else:
        return ratings[0:top]


def recommend_eval(userBaseCF, user, recommend_list):
    records = []
    user_movie_list = {}
    trainset = userBaseCF.trains
    testset = userBaseCF.tests
    user_movie_list.setdefault(user, {})

    # 从训练集合和测试集合——完整dataset中取出user评价过的电影
    if user in trainset:
        for movie in trainset[user]:
            user_movie_list[user][movie] = trainset[user][movie]
    if user in testset:
        for movie in testset[user]:
            user_movie_list[user][movie] = testset[user][movie]
    if len(user_movie_list[user]) < 1:
        print "user(%s) doesn't in dataset"
        return

    # 计算从随机一组电影获取user推荐列表的评分误差
    # 方法：找出推荐列表中user已经评价过的电影，计算RMSE与MAE
    for movie in user_movie_list[user]:
        for pre_movie in recommend_list:
            if movie == pre_movie[0]:
                records.append([user, movie, pre_movie[1], user_movie_list[user][movie]])

    records = sorted(records, key=operator.itemgetter(2), reverse=True)
    save_records(SAVE_RECORDS_FILE_NAME + '_user_' + user, records)
    rmse = eval_by_RMSE(records)
    mae = eval_by_MAE(records)
    return rmse, mae


if __name__ == '__main__':

    """ 使用moveline数据对KNN模型的评价部分    
    print("\n--------------基于MovieLens的推荐系统 运行中... -----------\n")
    userBaseCF = UserBasedCF()

    print("\n--------------基于MovieLens的推荐系统 加载默认数据集 -----------\n")
    userBaseCF.read_data()
    records = []
    trainset = userBaseCF.trains
    testset = userBaseCF.tests

    print("\n--------------基于MovieLens的推荐系统 开始进行预测 -----------\n")
    starttime = datetime.datetime.now()

    # 选择其中一个用户进行预测
    user = testset.keys()[2]        # {'userid':{'movieid1':rating1, 'movieid2':rating2},...}
    print("\n--------------对测试集中的用户user(%s)进行预测 -----------\n" % user)
    for movie in testset[user]:
        pre_rating = predict_user_movie(trainset, user, movie)
        records.append([user, movie, pre_rating, testset[user][movie]])

    # 保存预测结果
    save_records(SAVE_RECORDS_FILE_NAME + '_user_' + user, records)
    rmse = eval_by_RMSE(records)
    mae = eval_by_MAE(records)

    # 预测结果评价
    print("RMSE:%6.3f%%, MAE:%6.3f%%, TIME:%6ss" % (rmse * 100, mae * 100, (datetime.datetime.now() - starttime).seconds))
    """

    """ 随机选取一组电影列表，对某个用户进行推荐
    """
    print("\n--------------基于MovieLens的推荐系统 运行中... -----------\n")
    userBaseCF = UserBasedCF()

    print("\n--------------基于MovieLens的推荐系统 加载默认数据集 -----------\n")
    userBaseCF.read_data()

    print("\n--------------基于MovieLens的推荐系统 随机选取一组电影 -----------\n")
    movie_list = [str(i) for i in range(1, 200)]
    user = '346'
    recommend_list = recommend_movies(userBaseCF, user, movie_list)
    starttime = datetime.datetime.now()
    print "对用户%s推荐的电影列表为:%s, 耗时:%5ss" % (user, recommend_top(recommend_list, 5), (datetime.datetime.now() - starttime))
    print "推荐误差 RMSE:%6.3f%%, MAE:%6.3f%%" % recommend_eval(userBaseCF, user, recommend_list)

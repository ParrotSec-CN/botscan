#!/usr/bin/env python3

from gevent import monkey
monkey.patch_all()

import json
import yaml
import api.qq_group_api as qq_group

from random import choice
from config import app
from flask import request, Response
from utils import callback_function as cf

bot_config = open('config/bot_config.yaml')
config_content = yaml.safe_load(bot_config)

headers = {'Content-Type': 'application/json'}
atMe, group = '[CQ:at,qq=212521306]', 160958474
random_time = [1800, 7200, 21600, 43200, 86400]


def new_topic(topic):
    content = topic
    topicName, topicSlug, topicId, userName = str(
        content['topic']['title']), str(
        content['topic']['slug']), str(
        content['topic']['id']), str(
        content['topic']['created_by']['username'])
    url = 'https://parrotsec-cn.org/t/' + topicSlug + '/' + topicId
    msg = '{} 发表了新主题: "{}" {} {}'.format(userName, topicName, "\n", url)
    return qq_group.send_msg(msg, 'group_id', group)


def new_post(post):
    content = post
    name, title, topicSlug, topicId, postNumber = str(
        content['post']['username']), str(
        content['post']['topic_title']), str(
        content['post']['topic_slug']), str(
        content['post']['topic_id']), str(
        content['post']['post_number'])

    url = "https://parrotsec-cn.org/t/{}{}{}{}{}".format(
        topicSlug, '/', topicId, '/', postNumber)

    if 'reply_to_user' in content['post']:
        msg = '{} 在主题 "{}" 中回复了 {} {} {}'.format(name, title, str(
            content['post']['reply_to_user']['username']), "\n", url)
        return qq_group.send_msg(msg, 'group_id', group)
    else:
        msg = '{} 在主题 "{}" 中发表了回复 {} {}'.format(name, title, "\n", url)
        return qq_group.send_msg(msg, 'group_id', group)


def handle(event, myjson):
    # 发表新文章
    if event == 'topic_created':
        if myjson['topic']['user_id'] != -1:
            print(1)
            return new_topic(myjson)
    # 发表回复
    elif event == 'post_created':
        if myjson['post']['post_number'] > 1:
            print(2)
            return new_post(myjson)
    # 修改文章
    elif event == 'post_edited':
        name, title = str(myjson['post']['username']), str(myjson['post']['topic_title'])
        url = "https://parrotsec-cn.org/t/{}/{}".format(myjson['post']['topic_slug'], myjson['post']['topic_id'])
        msg = '{} 修改了主题 "{}" {} {}'.format(name, title, "\n", url)
        return qq_group.send_msg(msg, 'group_id', group)


@app.route('/', methods=['GET'])
def hello_world():
    if request.method == "GET":
        return 'hello world'


@app.route('/json', methods=['POST'])
def my_json():
    headers = request.headers
    event = (headers['X-Discourse-Event'])
    instance = (headers['X-Discourse-Instance'])
    content = request.json
    # print(event, content, instance)
    if instance == 'https://parrotsec-cn.org':
        res = {'msg': handle(event, content)}
        return Response(json.dumps(res), mimetype='application/json')


@app.route('/msg', methods=['POST'])
def my_msg():
    print("------------------Print running log---------------------")

    fuckoff, usage_method, function_list, function_keyword = config_content['fuck_off'], \
                                           config_content['usage_method'], \
                                           config_content['function_list'], \
                                           config_content['function_keyword']
    content = request.json

    try:
        groupId = content['group_id']
    except BaseException:
        groupId = False
    userId = content['user_id']

    if groupId and groupId in [160958474]:
        if content['post_type'] == 'message':
            try:
                message = content['message']
                # 判断违禁词
                for ban_word in config_content['ban_word']:
                    if ban_word in "".join(message.lower().split()):
                        msg = {
                            'reply': ', big brother is watching you! 恭喜你小伙计中奖了！！！'}
                        qq_group.group_ban(groupId, userId, miu_num=choice(random_time))
                        return Response(
                            json.dumps(msg), mimetype='application/json')
                # 直接@我
                if atMe in message:
                    if "".join((message.split())) == atMe:
                        reply = config_content['fuck_reply']
                        msg = {'reply': choice(reply)}
                        return Response(
                            json.dumps(msg), mimetype='application/json')

                    # 判断骂机器人
                    for abuse_word in config_content['abuse_word']:
                        if abuse_word in "".join(message.lower().split()):
                            msg = {
                                'reply': ', 骂我? 小伙计你内心很浮躁嘛! 送你个大奖，不用谢！'}
                            qq_group.group_ban(groupId, userId, miu_num=choice(random_time))
                            return Response(
                                json.dumps(msg), mimetype='application/json')

                    keyword = message.split(' ')[1]

                    if keyword not in function_keyword:
                        msg = {'reply': choice(fuckoff)}
                        return Response(
                            json.dumps(msg), mimetype='application/json')

                    # search_info = QueryMsg(1001)(keyword=keyword)
                    function_result = cf.QueryMsg(keyword)(usage_method=usage_method,
                                         function_list=function_list,
                                         message=message,
                                         user_id=userId,
                                         group_id=groupId)
                    if function_result:
                        msg = {'reply': function_result}
                        return Response(
                            json.dumps(msg), mimetype='application/json')

            except Exception as e:
                print(e)

        elif content['post_type'] == 'notice':
            if content['notice_type'] == 'group_increase':
                msg = "欢迎大佬['{}']入群,请牢记渗透千万条,匿名第一条;搞事不规范,牢饭吃到早...!!!".format(str(content['user_id']))
                return qq_group.send_msg(msg, 'group_id', groupId)

    res = {'msg': 'ok'}
    return Response(json.dumps(res), mimetype='application/json')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9002)

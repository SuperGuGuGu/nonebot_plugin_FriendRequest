from asyncio import sleep
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, FriendRequestEvent, PrivateMessageEvent, RequestEvent, GroupRequestEvent
from nonebot import on_command, on_request, on_notice, require
from nonebot import get_driver, get_bot, on_request
import sqlite3
import random
# 添加请求命令
parseRequest = on_request(priority=1, block=True)

# Github网址：https://github.com/SuperGuGuGu/nonebot_plugin_FriendRequest


#  Config 配置选项 #
# 管理员qq号
adminqq = 12345678
# 自动处理：（同意，1）（审核，0）（拒绝，-1）
auto_approved_private = '0'
auto_approved_group = '0'
# 数据库文件位置
addrequestdb = './addrequest.db'
# 自动回复消息
apply_msg_private = ["阁下的好友请求已通过，请在群成员页面邀请bot加群（bot不会主动加群）待管理员审核后进群。",
                     "如需要帮助可使用<help>(不含括号)查看帮助"]
apply_msg_group = ["阁下群邀请已通过 "]
apply_msg_group_reject = ["管理员已拒绝该群邀请。如有疑问请联系管理员"]


@parseRequest.handle()
async def _(bot: Bot, requestevent: RequestEvent):
    botid = str(bot.self_id)
    added = 'off'

    import time
    date = str(time.strftime("%Y-%m-%d", time.localtime()))
    date_year = str(time.strftime("%Y", time.localtime()))
    date_month = str(time.strftime("%m", time.localtime()))
    date_day = str(time.strftime("%d", time.localtime()))
    dateshort = date_year + date_month + date_day
    timenow = str(time.strftime("%H:%M:%S", time.localtime()))
    time_h = str(time.strftime("%H", time.localtime()))
    time_m = str(time.strftime("%M", time.localtime()))
    time_s = str(time.strftime("%S", time.localtime()))
    timeshort = time_h + time_m + time_s

    msgid = 1
    num = 50
    while num >= 1:
        num -= 1
        if num <= 30:
            msgid = random.randint(100, 99999999)

        conn = sqlite3.connect(addrequestdb)
        cursor = conn.cursor()
        cursor.execute('select * from list where msgid = ' + str(msgid))
        data = cursor.fetchone()
        cursor.close()
        conn.close()
        if data == None:
            num = 0
        else:
            msgid += 1
    msgid = str(msgid)

    # 判断邀请类型，并获取部分数据
    if isinstance(requestevent, FriendRequestEvent):
        # 好友申请
        type = 'private'
        reqid = str(requestevent.user_id)  # 要添加好友的qq号
        requser = reqid  # 请求发起的人
        message = str(requestevent.comment)  # 验证消息
        flag = requestevent.flag
        sendmsg = reqid + '请求添加好友,\n申请编号：' + msgid + '\nbot："' + botid + '"\n验证消息为："' + message + '"\n时间:' + date + ',' + timenow  # 给管理员发送的消息
        apply_msg = "申请收到，等待管理员处理"  # 给请求发起人的消息（因为是好友申请，所以不发送

    elif isinstance(requestevent, GroupRequestEvent):
        # 群邀请
        if requestevent.sub_type != 'invite':  # 可能是排除不是群邀请的代码
            return
        type = 'group'
        reqid = str(requestevent.group_id)  # 要添加的QQ群
        requser = requestevent.get_user_id()  # 请求发起的人
        message = str(requestevent.comment)  # 验证消息（群邀请貌似为空
        flag = requestevent.flag
        sendmsg = '收到群邀请\n申请编号：' + msgid + '\nbot："' + botid + '"\n群号：' + reqid + '，\n邀请人：' + requser + '\n时间:' + date + ',' + timenow
        apply_msg = "申请收到，等待管理员处理"
        await bot.send_private_msg(user_id=requestevent.user_id, message=apply_msg)  # 给请求发起人发送消息
        # 检查是否自动添加
        await sleep(2)
        addinfo = await bot.get_group_info(group_id=int(reqid), no_cache=True)
        if addinfo["member_count"] != 0:
            sendmsg = sendmsg + '\n或因群人数少,已经添加成功'
            added = 'on'
            # 通知管理员
            await bot.send_private_msg(user_id=adminqq, message=sendmsg)
            return
    else:
        return

    # 通知管理员 审核消息
    await bot.send_private_msg(user_id=adminqq, message=sendmsg)

    # 处理自动通过
    if type == 'private':
        if auto_approved_private == '1':
            await requestevent.approve(bot)  # 同意申请
            added = 'on'
            await sleep(0.5)
            sendmsg = '已自动同意好友申请' + reqid
            await bot.send_private_msg(user_id=adminqq, message=sendmsg)  # 通知管理员
            await sleep(1.5)
            for apply_msg in apply_msg_private:
                await bot.send_private_msg(user_id=int(reqid), message=apply_msg)  # 发送欢迎消息
                await sleep(0.3)
        elif auto_approved_private == '-1':
            await requestevent.reject(bot)  # 拒绝申请
            sendmsg = '已自动拒绝好友申请' + reqid
            await bot.send_private_msg(user_id=adminqq, message=sendmsg)  # 通知管理员
            added = 'on'

    elif type == 'group':
        if auto_approved_group == '1':
            await requestevent.approve(bot)  # 同意申请
            added = 'on'
            sendmsg = '已自动同意群邀请' + reqid
            await bot.send_private_msg(user_id=adminqq, message=sendmsg)  # 通知管理员
            await sleep(0.5)
            apply_msg = '阁下群邀请已通过'
            await bot.send_private_msg(user_id=int(requser), message=apply_msg)
        elif auto_approved_private == '-1':
            await requestevent.reject(bot)  # 拒绝申请
            added = 'on'
            sendmsg = '已自动拒绝好友申请' + reqid
            await bot.send_private_msg(user_id=adminqq, message=sendmsg)  # 通知管理员
            await sleep(0.5)
            apply_msg = '群邀请已拒绝'
            await bot.send_private_msg(user_id=int(requser), message=apply_msg)

    conn = sqlite3.connect(addrequestdb)
    cursor = conn.cursor()
    cursor.execute('select * from list where flag = ' + str(flag))
    data = cursor.fetchone()
    cursor.close()
    conn.close()
    if data != None:
        added = 'on'
    # 保存数据
    if added == 'off':
        # 查看有无重复申请
        conn = sqlite3.connect(addrequestdb)
        cursor = conn.cursor()
        cursor.execute('select * from list where reqid = ' + reqid)
        data = cursor.fetchone()
        cursor.close()
        conn.close()
        # 判断有无已申请数据
        if data is not None:
            # 有申请，复用请求id
            msgid = data[0]

        conn = sqlite3.connect(addrequestdb)
        cursor = conn.cursor()
        cursor.execute('replace into list(msgid,botid,type,reqid,requser,message,flag,time) '
                       'values("' + msgid + '","' + botid + '","' + type + '","' + reqid + '","' + requser + '","' + message + '","' + flag + '","' + date + ',' + timenow + '")')
        cursor.close()
        conn.commit()
        conn.close()
    return


# 管理员使用，同意好友添加机器人请求
agree_qq_add = on_command("同意", aliases={'拒绝', '查看申请'}, block=False)

# github.com/SuperGuGuGu/nonebot_plugin_FriendRequest
@agree_qq_add.handle()
async def _(bot: Bot, messageevent: MessageEvent):
    qq = str(messageevent.get_user_id())
    if int(qq) == adminqq:
        botid = str(bot.self_id)
        errmsg = ''
        message = messageevent.get_message()
        message = str(message)
        commands = get_commands(message)
        command = str(commands[0])
        command = command.removeprefix("/")
        if len(commands) >= 2:
            command2 = commands[1]
        else:
            command2 = ''
        print(command)
        if '同意' == command:
            msgid = command2
            approve = True
        elif '拒绝' == command:
            msgid = command2
            approve = False
        else:
            approve = 'None'
            msgid = '0'

        if approve != 'None':
            # 配置列表
            conn = sqlite3.connect(addrequestdb)
            cursor = conn.cursor()
            cursor.execute('select * from list where msgid = ' + msgid)
            data = cursor.fetchone()
            cursor.close()
            conn.close()
            if data is not None:
                data_botid = data[1]
                data_type = data[2]
                data_reqid = data[3]
                data_requser = data[4]
                data_message = data[5]
                data_flag = data[6]
                if botid == data_botid:
                    if data_type == 'private':
                        friend_list = []
                        allinfolist = await bot.get_friend_list()
                        for info in allinfolist:
                            userid = str(info['user_id'])
                            friend_list.append(userid)
                        friend_list = []
                        if data_reqid in friend_list:
                            errmsg = '已添加，请勿重复添加'
                        else:
                            try:
                                await bot.set_friend_add_request(flag=data_flag, approve=approve)
                            except Exception as e:
                                print('error-:')
                                print(str(e))
                        conn = sqlite3.connect(addrequestdb)
                        cursor = conn.cursor()
                        cursor.execute('delete from list where msgid = ' + msgid)
                        conn.commit()
                        cursor.close()
                        conn.close()
                        await sleep(0.5)
                        sendmsg = '已同意好友申请' + data_reqid
                        await bot.send_private_msg(user_id=adminqq, message=sendmsg)  # 通知管理员
                        # 等待腾讯服务器更新
                        await sleep(1.5)
                        for apply_msg in apply_msg_private:
                            await bot.send_private_msg(user_id=int(data_reqid), message=apply_msg)  # 发送欢迎消息
                            await sleep(0.3)
                    elif data_type == 'group':
                        group_list = []
                        allinfolist = await bot.get_group_list()
                        for info in allinfolist:
                            groupcode = str(info['group_id'])
                            group_list.append(groupcode)
                        if data_reqid in group_list:
                            errmsg = '已添加，请勿重复添加'
                        else:
                            data_subtype = data_message
                            await bot.set_group_add_request(flag=data_flag, approve=approve, sub_type=data_subtype)
                            conn = sqlite3.connect(addrequestdb)
                            cursor = conn.cursor()
                            cursor.execute('delete from list where flag= ' + data_flag)
                            conn.commit()
                            cursor.close()
                            conn.close()
                            sendmsg = '已同意群邀请' + data_reqid
                            await bot.send_private_msg(user_id=adminqq, message=sendmsg)  # 通知管理员
                            for apply_msg in apply_msg_group:
                                await bot.send_private_msg(user_id=int(data_requser), message=apply_msg)  # 发送欢迎消息
                                await sleep(0.3)
            else:
                errmsg = '找不到该申请，请发送\n“/同意 [申请编号]”\n来同意申请'
            if errmsg != '':
                await bot.send_private_msg(user_id=int(qq), message=errmsg)  # 返回错误信息
        else:
            if '查看申请' == command:
                # 配置列表
                conn = sqlite3.connect(addrequestdb)
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM list")
                alldata = cursor.fetchall()
                cursor.close()
                conn.commit()
                conn.close()
                msg = ''
                if alldata is not None:
                    for data in alldata:
                        msgid = data[0]
                        botid = data[1]
                        type = data[2]
                        reqid = data[3]
                        requser = data[4]
                        message = data[5]
                        flag = data[6]
                        date = data[7]
                        print('data' + str(data))
                        if type == 'private':
                            sendmsg = '收到好友申请\n申请编号：' + msgid + '\nbot："' + botid + '"\nqq号："' + reqid + '"\n验证消息为："' + message + '"\n时间:' + date + '"\n申请id：:' + msgid
                        else:
                            sendmsg = '收到群邀请\n申请编号：' + msgid + '\nbot："' + botid + '"\n群号：' + reqid + '，\n邀请人：' + requser + '\n时间:' + date + '"\n申请id：:' + msgid
                        await bot.send_private_msg(user_id=int(qq), message=sendmsg)
                        await sleep(0.3)
                else:
                    sendmsg = '无好友申请/群邀请数据'
                    await bot.send_private_msg(user_id=int(qq), message=sendmsg)
            elif '删除所有申请' == command:
                print('删除所有申请')
            elif '帮助' == command:
                print('帮助')
                sendmsg = '指令列表\n/同意 [申请编号]\n/拒绝 [申请编号]\n例如“/同意 1”\n查看申请\n删除所有申请'
                await bot.send_private_msg(user_id=int(qq), message=sendmsg)

    else:
        print('权限不足')


def get_commands(message):
    # 获取发送的消息。使用第一个空格进行分段，无空格则不分段
    message = str(message)
    commands = []

    if ' ' in message:
        messages = message.split()
        if messages == []:
            message = ['']
        else:
            message = messages[0]
        commands.append(message)
        msglen = len(messages)

        num = 0
        message = ''
        while msglen >= 1:
            msglen -= 1
            addmessage = messages[num]
            if num == 1:
                message = message + addmessage
            elif num != 0:
                message = message + ' ' + addmessage
            num += 1
        commands.append(message)
    else:
        commands.append(message)
    # 去除cq码
    return commands

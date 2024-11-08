from telegram import Update
import config
from telegram.ext import  Application,CommandHandler,ContextTypes,filters,MessageHandler
import nest_asyncio
import requests
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import re

nest_asyncio.apply()

#触发的执行内容

# 配置请求的接口URL
API_URL = 'http://sp.billionprompt.com/api/chat/send'

AI_ID = '1242'

# 设置自定义请求头
headers = {
    'Authorization': config.ai_token,
    'Accept-Encoding': 'identity',
    'language': 'zh',
    'Content-Type': 'application/json; charset=UTF-8'
}

# 定义 AiUser 数据类
@dataclass
class AiUser:
    id: int
    card_id: int
    uid: int
    type: int
    name: str
    signature: str
    character: str
    character_setting: str
    greet_text: str
    share_num: int
    chat_num: int
    love_num: int
    img_path: str
    head_path: str
    sex: int
    topic_id: Optional[int]
    voice_url: str
    playtime: int
    card_num: int
    catena_num: int
    topic: List[str]


# 解析 JSON 数据中所有 ai 对象的方法
def parse_ai_data(data: Dict[str, Any]) -> List[AiUser]:
    ai_users = []

    for item in data.get('data', {}).get('data', []):
        if 'ai' in item:
            ai_data = item['ai']
            ai_user = AiUser(
                id=ai_data['id'],
                card_id=ai_data['card_id'],
                uid=ai_data['uid'],
                type=ai_data['type'],
                name=ai_data['name'],
                signature=ai_data['signature'],
                character=ai_data['character'],
                character_setting=ai_data['character_setting'],
                greet_text=ai_data['greet_text'],
                share_num=ai_data['share_num'],
                chat_num=ai_data['chat_num'],
                love_num=ai_data['love_num'],
                img_path=ai_data['img_path'],
                head_path=ai_data['head_path'],
                sex=ai_data['sex'],
                topic_id=ai_data.get('topic_id'),
                voice_url=ai_data['voice_url'],
                playtime=ai_data['playtime'],
                card_num=ai_data['card_num'],
                catena_num=ai_data['catena_num'],
                topic=ai_data.get('topic', [])
            )
            ai_users.append(ai_user)

    return ai_users
async  def echo(update: Update, context: ContextTypes.DEFAULT_TYPE)->None:
    user_message = update.message.text  # 获取用户消息
    print(f"收到消息: {user_message}")

    # 设置请求体，添加多个参数
    payload = {
        'msg': user_message,
        'to_id': AI_ID,
        'msg_type': 'txt',
        'file': 'null'
    }
    # 向接口发送请求
    response = requests.post(API_URL, json=payload, headers=headers)

    if response.status_code == 200:
        # 解析响应内容
        response_data = response.json()
        if response_data['code'] == 0 and 'data' in response_data:
            reply_text = response_data['data'].get('reply', '没有获取到回复')
        else:
            reply_text = "没有成功获取到有效的回复内容。"
        # 回复用户
        await update.message.reply_text(reply_text)
    else:
        await update.message.reply_text("请求接口失败，请稍后再试。")

# 提取所有 ai_users 的 name 字段，组成 msg 列表
def extract_names(ai_users: List[AiUser]) -> List[str]:
    msg = [user.name for user in ai_users]
    return msg

async def show_list(update: Update, context: ContextTypes.DEFAULT_TYPE)->None:
    user_message = update.message.text  # 获取用户消息
    print(f"收到消息: {user_message}")
    # 设置请求体，添加多个参数
    payload = {
        'page': '1',
        'page_sizi': '10'
    }
    # 向接口发送请求
    response = requests.post('http://sp.billionprompt.com/api/recommend', json=payload, headers=headers)

    if response.status_code == 200:
        # 解析响应内容
        response_data = response.json()
        # 解析 JSON 数据
        ai_users = parse_ai_data(response_data)
        if response_data['code'] == 0 and 'data' in response_data:
            # 提取所有 name 并组成 msg 列表
            msg = extract_names(ai_users)
            # reply_text = ' '.join(msg)
            for index, user in enumerate(ai_users, start=0):
                reply_text = 'id:'+ai_users[index].id.__str__()+'\n'+'https://d2hvnjr725nx7n.cloudfront.net/' + ai_users[index].head_path+ '\n' + ai_users[index].name+ '\n'+ai_users[index].character_setting
                await update.message.reply_text(reply_text)
        else:
            reply_text = "没有成功获取到有效的回复内容。"
            await update.message.reply_text(reply_text)
        # 回复用户
    else:
        await update.message.reply_text("请求接口失败，请稍后再试。")


async def switch_ai(update: Update, context: ContextTypes.DEFAULT_TYPE)->None:
    global AI_ID  # 声明使用全局变量
    user_message = update.message.text  # 获取用户消息
    print(f"收到消息: {user_message}")
    # 使用正则表达式提取 /switch 后的数字
    match = re.search(r'/switch (\d+)', user_message)
    if match:
        new_id = int(match.group(1))  # 获取匹配的数字并转换为整数
        AI_ID = new_id  # 存储在 user_data 中
        await update.message.reply_text(f"切换AI成功，新的 ID 是 {new_id}")
        print(f"当前用户的 ID 被设置为: {new_id}")
    else:
        await update.message.reply_text("请提供正确的命令格式，例如：/switch 1234")



#创建程序
application = Application.builder().token(config.telegram_token).build()
CommandHandler("start", echo)
application.add_handler(CommandHandler("list", show_list))
application.add_handler(CommandHandler("switch", switch_ai))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

application.run_polling()


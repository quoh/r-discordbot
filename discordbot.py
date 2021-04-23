# coding: UTF-8
# インストールした discord.py を読み込む
import discord
from datetime import datetime, timedelta, timezone
import random
import pandas as pd
import time
import numpy as np
# from discord.ext import commands

# コマンドを使えるようになる
# bot = commands.Bot(command_prefix='/')
# 自分のBotのアクセストークンに置き換えてください
TOKEN = 'XXXXXXXXXXXXXXXXXXXXX'

# 接続に必要なオブジェクトを生成
client = discord.Client()

# ヘルプにいれるテキスト
help = '```/ghelp :私の機能について紹介するわ！\n/dice [面数] [回す回数] :ダイスを振ってあげるわ！\n/dice [面数] [回す回数] sum :ダイスを振って合計値も出してあげるわ！\n/sdvxk [レベル] :現行収録されているボルテの曲を指定したレベルで3曲選んであげるわ！\n/sdvxk [レベル] [曲数] :現行収録されているボルテの曲を指定したレベルで指定された曲数選んであげるわ！\n※2020年07月16日の筐体側のアプデ分まで対応しているわ！\n\n version 1.0.0```'

#botstatusを表示するチャンネルIDを保存
channelID = 0000000000000000000 #for debug

reschID = 0000000000000000000

#タイムゾーンの生成
JST = timezone(timedelta(hours=+9), 'JST')

dfs = pd.read_csv('sdvxmusicdb-labeled.csv')

#絵文字リスト
emojiList = ["👏","👍","💪","🥺","🤗","😇"]

#voice channelのデータ
global voich

#VC接続記録をとってみる

nowConnect = [] #[[name, intime], [], ...]

# 起動時に動作する処理
@client.event
async def on_ready():
    # 起動したらターミナルにログイン通知が表示される
    print('ログインしました')
    now = datetime.now(JST).strftime("%Y/%m/%d %H:%M:%S")
    game = discord.Game("Xronièr [MXM]")
    await client.change_presence(status=discord.Status.online, activity=game)
    channel = client.get_channel(channelID)
    login = f'{now} :起動したわ！'
    await channel.send(login)

# @client.event
# async def on_disconnect():
#     # 起動したらターミナルにログイン通知が表示される
#     print('ログアウトしました')
#     now = datetime.now(JST).strftime("%Y/%m/%d %H:%M:%S")
#     channel = client.get_channel(channelID)
#     login = f'{now} :シャットダウンするわ！'
#     await channel.send(login)

@client.event
async def on_voice_state_update(member, before, after):
  global nowConnect
  df_vclog = pd.read_csv('vclog.csv')
  if member.guild.id == 0000000000000000000:
        # print("channel accepted!")
        now = datetime.now(JST).strftime("%Y/%m/%d %H:%M:%S")
        alert_channel = client.get_channel(0000000000000000000)
        if before.channel is None: 
            msg = f'{now} に {member.name} が {after.channel.name} に参加しました。'
            await alert_channel.send(msg)
            nowConnect.append([member.name,after.channel.name , datetime.now(JST)])
            print(nowConnect)
        elif after.channel is None: 
            msg = f'{now} に {member.name} が {before.channel.name} から退出しました。'
            await alert_channel.send(msg)
            arr = np.array(nowConnect)
            pos = str(tuple(nd[0] for nd in np.where(arr == member.name))) #posは(0,0)みたいに帰ってくるので、無理やり引っ張る　賢いやり方あるんだろうけど一時的に
            possess = int((pos.split(',')[0])[1:])
            #csvに時間を保存
            time = nowConnect[possess][2]
            times = datetime.now(JST) - time
            insert = {'name': member.name, 'channel': before.channel.name, 'time': times}
            df_vclog_ins = df_vclog.append(insert, ignore_index=True)
            df_vclog_ins.to_csv('vclog.csv', index=None)
            #配列の中からユーザ名を見つけてきて、それを消す処理
            print(df_vclog)
            nowConnect.pop(possess)
            print(nowConnect)

# メッセージ受信時に動作する処理
@client.event
async def on_message(message):
    # メッセージ送信者がBotだった場合は無視する
    global voich
    # global bot
    word = message.content
    now = datetime.now(JST).strftime("%Y/%m/%d %H:%M:%S")
    if message.author.bot:
        return
    if message.attachments:
        isReact = False
        print(message.channel)
        if str(message.channel) == "botstatus":
            for attachment in message.attachments:
                # Attachmentの拡張子がpng, jpg, jpegのどれかだった 場合
                if attachment.url.endswith(("png", "jpg", "jpeg")):
                    isReact = True
            if isReact == True:
                await message.add_reaction(random.choice(emojiList))
    # 「/neko」と発言したら「にゃーん」が返る処理
    if word == '$neko':
        await message.channel.send('にゃーん')
    # ヘルプの表示
    elif word == '$ghelp':
        await message.channel.send(help)
    #チャンネルの作成
    elif word.startswith('$mkch'):
      mkch = word.split(' ')
      new_channel = await create_channel(message, channel_name=mkch[1])
      channel = client.get_channel(channelID)
      # チャンネルのリンクと作成メッセージを送信
      text = f'{now} に {message.author.mention} が {new_channel.mention} を作成したわ！'
      await channel.send(text)
    elif word.startswith('$join'):
      voich = await discord.VoiceChannel.connect(message.author.voice.channel)
    elif word.startswith('$disconnect'):
      await voich.disconnect()
    elif word.startswith('$vchoice'):
      vchoi = word.split(' ')
      count = 1
      if len(vchoi) == 2:
        count = int(vchoi[1])
      name = [member.name for member in message.author.voice.channel.members]
      nameUser = [usr for usr in name if usr != 'rasis_bot']
      text = ''
      if len(nameUser) >= count:
        print(nameUser)
        choicedUser = random.sample(nameUser, count)
        text = '選ばれたのは、'
        member = []
        for i in choicedUser:
          member.append(discord.utils.get(message.guild.members, name=i))
          m = discord.utils.get(message.guild.members, name=i)
          text = f'{text} {m.mention}'
        text = f'{text}よ！'
      else:
        text = 'エラーよ！ちゃんと!ghelpみて確認しなさい！'
      await message.channel.send(text)
    # !dice n m 'sum'
    elif word.startswith('$dice'):
      roll = word.split(' ')
      sum = 0
      isSum = False
      if 'sum' in roll:
        isSum = True
      men = int(roll[1])
      count = int(roll[2])
      rtn = []
      for i in range(count):
        rollrnd = random.randint(1,men)
        rtn.append(rollrnd)
        if isSum == True:
          sum = sum + rollrnd
      text = f'{men}面ダイスを{count}回回したわ！\n結果は、\n{rtn}よ！'
      textSum = f'合計は、{sum}よ！'
      await message.channel.send(text)
      if isSum == True:
        await message.channel.send(textSum)
    # 課題曲を提示してくれる
    elif word.startswith('$sdvxk'):
      chl = client.get_channel(channelID)
      sdvx = word.split(' ')
      difficulty = sdvx[1]
      cnt = 3
      if len(sdvx) == 3:
        cnt = int(sdvx[2])
      df_query = dfs.query('difficulty == ' + difficulty)
      rtndf = df_query.sample(n=cnt,replace=True)
      rtntext = ''
      for item, rows in rtndf.iterrows():
        rtntext = rtntext + rows['title'] + '/' + rows['artist'] + '\n'
      # print(rtntext)
      text = f'Lv. {difficulty}の曲を{cnt}個選んだわ！\n\n{rtntext}\nちゃんとやりなさいよ！'
      await chl.send(text)
    #指定した範囲で課題曲を選択する
    elif word.startswith('$sdvxr'):
      chl = client.get_channel(channelID)
      sdvx = word.split(' ')
      difficulty_l = sdvx[1]
      difficulty_m = sdvx[2]
      cnt = 3
      if len(sdvx) == 4:
        cnt = int(sdvx[3])
    # 話かけられたとき
    if client.user in message.mentions: # 話しかけられたかの判定
        # オウム返し
        # await message.channel.send(word)
        await reply(message) # 返信する非同期関数を実行
        await message.add_reaction("💩")
# command test

#functions
async def reply(message):
    reply = f'{message.author.mention} 💩を投げとくわね' # 返信メッセージの作成
    await message.channel.send(reply) # 返信メッセージを送信

async def create_channel(message, channel_name):
    category_id = message.channel.category_id
    category = message.guild.get_channel(category_id)
    new_channel = await category.create_text_channel(name=channel_name)
    return new_channel

# Botの起動とDiscordサーバーへの接続
client.run(TOKEN)
#===== description =====#
"""
itoDiscord
Copyright (c) 2021 brave99
This software is released under the MIT License.
http://opensource.org/licenses/mit-license.php

This script is a discord bot that can be a GM of ito game.
Required libraly is only "discord.py"
Have fun with your BOT!!
"""

#===== modules =====#
import discord
from threading import Thread
from queue import Queue
import configparser
import random

#===== global =====#
### discord ###
config = configparser.ConfigParser()
config.read('option.ini', encoding = 'utf8')
client = discord.Client()
GAME = discord.Game(name = "ito")
CHANNEL = None#discord.channel(id=config["BOT"]["CHANNEL"])

### game ###
players = []
cards = 1
STARTED = False
PLAYING = 0 #0: not playing, 1: kumonoito, 2: akaiito
sendq = Queue() #need this when the game send message to discord

#===== script =====#
#===== bot =====#
@client.event
async def on_ready():
    global CHANNEL
    CHANNEL = client.get_channel(int(config["BOT"]["CHANNEL"]))
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print(CHANNEL)
    print('------')
    await CHANNEL.send('ブンブンハローDISCORD')
    await CHANNEL.send('"/start" でゲームを開始します。\n"/shutdown"で終了します。')

@client.event
async def on_message(message):
    global STARTED
    global PLAYING
    global CHANNEL
    global validate
    global players
    global cards

    if message.content.startswith("/shutdown"):
        if client.user != message.author:
            await message.channel.send("Bye!!")
            client.close()
            client.logout()
            exit(0)

    if not STARTED:
        if message.content.startswith("/start"):
            if client.user != message.author:
                await CHANNEL.send("クモノイトを始めます。")
                await client.change_presence(activity = GAME)
                await CHANNEL.send('参加したい人は"/join"と入力。\n全員の入力が終わったら"/go"と入力。')
                await CHANNEL.send('配られる数字の数は"/cards 2"のように変更できます。(初期値は1)')
                STARTED = True

    elif PLAYING == 0 and STARTED:
        if message.content.startswith("/join"):
            if client.user != message.author:
                p = []
                for player in players:
                    p.append(player.discord)
                if message.author in p:
                    await CHANNEL.send("{} はもう登録済みです。".format(message.author.name))
                else:
                    hoge = Player(message.author)
                    players.append(hoge)
                    await CHANNEL.send("{} を登録しました。".format(message.author.name))
        
        elif message.content.startswith("/cards"):
            try:
                cards = int(message.content.split(" ")[1])
                await CHANNEL.send(str(cards)+"枚ずつ配ります。")
            except:
                await CHANNEL.send("入力が正しくありません。")

        elif message.content.startswith("/go"):
            if len(players)<2:
                await CHANNEL.send("2人以上いないとプレイできません。再度/startからやりなおしてください。")
            else:
                PLAYING = 1
                num_player = len(players)

                ### deal number ###
                await CHANNEL.send("全員の準備が完了しました。DMでカードを配布します。")
                deal,ans = dealNumber(num_player, cards)
                for i, player in enumerate(players):
                    player.number = deal[i]
                    player.number_hard = player.number[:]

                for player in players: 
                    #player.notice()#this does not work
                    await player.discord.send('{0} さんの数字は【{1}】です。'.format(player.name, player.number))

                await CHANNEL.send('お題を決めて話し合いを始めてください。\n数字を公開する人は順番に"/open"と入力。')
                
                failed = False
                for num in ans:### TODO: make this area clear.
                    message = await client.wait_for('message', check=wait_for_open)
                    for player in players:
                        if message.author == player.discord:
                            challenge = player.number[0]
                            await CHANNEL.send(player.name+"の数字は【"+str(player.number.pop(0))+"】です。")
                            if challenge == num:
                                await CHANNEL.send("セーフ")
                            else:
                                await CHANNEL.send("アウトォォォ！！！")
                                failed = True
                                while True:
                                    failure = Thread(target = gameFailure, args = (players,), name = "failure")
                                    failure.start()
                                    state = sendq.get()
                                    if state =="end":
                                        break
                                    else:
                                        await CHANNEL.send(state)
                        if failed:
                            break
                    if failed:
                        break
                if not failed: # cleared
                    await CHANNEL.send("クリアおめでとう！\n各プレイヤーの数字は以下の通りです。")
                    content = "{0}:\t{1}"
                    for player in players:
                        await CHANNEL.send(content.format(player.name,player.number_hard))
                else:
                    await CHANNEL.send("残念だったね。")

                STARTED = False
                PLAYING = 0
                players = []
                cards = 1
                await CHANNEL.send('"/start" で次のゲームを開始します。\n"/shutdown"で終了します。')

#===== supporting functions =====#
def wait_for_open(message):
    return message.channel==CHANNEL and message.content=="/open"

def wait_for_player(message):
    return message.author==validate

#===== itoGame =====#
class Player():
    def __init__(self, discord):
        self.discord = discord
        self.name = self.discord.name
        self.number = []
        self.number_hard = []

    def notice(self):# this does not work
        self.discord.send(self.name+"さんの数字は【"+str(self.number)+"】です。")


def dealNumber(num_player, cards):
    rand_num = num_player * cards
    base = [i+1 for i in range(100)] # 1~100
    deal = []
    ans = random.sample(base,rand_num)
    for i in range(num_player):
        tmp = []
        for j in range(cards):
            tmp.append(ans[cards*i+j])
        tmp.sort()
        deal.append(tmp)
    ans.sort()
    return deal, ans


def gameFailure(players):
    global CHANNEL
    sendq.put("失敗です。\n各プレイヤーの数字は以下の通りです。")
    content = "{0}:\t{1}"
    for player in players:
        sendq.put(content.format(player.name,player.number_hard))
    sendq.put("end")


#===== main =====#
def main():
    client.run(config["BOT"]["TOKEN"])

if __name__ == "__main__":
    main()

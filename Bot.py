import discord
import time
import sys
import random
import asyncio
import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import style
style.use("fivethirtyeight")
client = discord.Client()

#establishing mysql connection
mydb = mysql.connector.connect(
    host = "localhost",
    user = "root",
    password = "#your password here",
    database = "userlevels"
)
print(mydb)

#status report
def report(guild):
    online = 0
    offline = 0

    for m in guild.members:
        if str(m.status) == "online":
            online += 1
        elif str(m.status) == "offline":
            offline += 1
    return online, offline

async def metrics_background_task():
    await client.wait_until_ready()
    global id
    while not client.is_closed(): # while client connected
        try: 
            online, offline = report(id)
            with open("usermetrics.csv", "a") as f:
                f.write(f"{int(time.time())},{online},{offline}\n")

            df = pd.read_csv("usermetrics.csv", names=['time', 'online', 'offline'])  # dataframe
            df['date'] = pd.to_datetime(df['time'], unit='s')  # converting unix time to date time
            df['total'] = df['online'] + df['offline']  # total online/offline
            df.drop("time", axis=1, inplace=True)  # getting rid of unix time
            df.set_index("date", inplace=True)

            #print(df.head())
            plt.clf() # clear figure every time to avoid mess

            df['online'].plot()
            plt.legend()
            plt.savefig("onlinediscord.png")
            await asyncio.sleep(10)

        except Exception as e:
            print(str(e))
            await asyncio.sleep(10)


@client.event  # what to do when event is about to occur #decorator
async def on_ready():  # when bot is fully connected to server
    global id
    id = client.get_guild(#client id here)  # client id for server
    print(f"Bot has logged in as {client.user}")  # evaluated at runtime

@client.event
async def on_member_join(member):
    for channel in member.guild.channels:
        if str(channel) == "general":
            await client.send_message(f"""Welcome {member.mention}""")

#generating XP randomly
def genXP():
    return random.randint(5,100)


@client.event
async def on_message(message):
    global id
    channels = ["commands", "general"]
    print(f"{message.channel}: {message.author}: {message.author.name}: {message.content}")

    if not message.author.bot:
        xp = genXP()
        print(message.author.name + " recieves " + str(xp) + "xp")
        cursor = mydb.cursor() 
        cursor.execute("SELECT user_xp, user_level FROM users WHERE client_id = " + str(message.author.id)) # return array of tuples
        result = cursor.fetchall()
        if (len(result) == 0):
            cursor.execute("INSERT INTO users VALUES(" + str(message.author.id)+ "," + str(xp) + ", 1)") #statements executed
            mydb.commit() # ends transaction in database and makes changes visible
            embed = discord.Embed()
            embed.set_author(name='Bot3000')
            embed.description = "Congrats you have entered the levelling system "

            await message.channel.send(embed=embed)

        else:
            newXP = result[0][0] + xp # referencing value of tuple
            currentlvl = result[0][1] # first position of tuple inside list
            lvlup = False

            if newXP < 100:
                currentlvl = 1
            elif newXP > 100 and newXP < 300:
                if currentlvl != 2:
                    lvlup = True
                currentlvl = 2
            elif newXP > 300 and newXP < 500:
                if currentlvl != 3:
                    lvlup = True
                currentlvl = 3
            elif newXP > 500 and newXP < 1000:
                if currentlvl != 4:
                    lvlup = True
                currentlvl = 4
            elif newXP > 1000 and newXP < 10000:
                if currentlvl != 5:
                    lvlup = True
                currentlvl = 5
            elif newXP > 10000:
                if currentlvl != 6:
                    lvlup = True
                currentlvl = 6

            cursor.execute("UPDATE users SET user_xp = " + str(newXP) + ", user_level = " + str(currentlvl) + " WHERE client_id = " + str(message.author.id))
            mydb.commit()

            embed = discord.Embed()
            embed.set_author(name ='Bot3000')
            embed.description = message.author.name + " Gained " + str(xp) + " XP!"
            await message.channel.send(embed=embed)

            if lvlup:
                embed = discord.Embed()
                embed.set_author(name = 'Bot3000')
                embed.description = message.author.name + " leveled up to " + str(currentlvl)
                await message.channel.send(embed=embed)



    if str(message.channel) in channels:
        if message.content.find("hey") != -1:
            await message.channel.send("HEY!")

        elif message.content.find("how are you, Bot3000?") != -1:
            await message.channel.send("Good, thanks.")

        elif message.content == "!users": # number of users
            await message.channel.send(f"""{id.member_count}""")

        elif message.content.find("leave bot") != -1:
            await client.close()
            sys.exit()

        elif "report" == message.content.lower():
            online, offline = report(id)
            await message.channel.send(f"```Online: {online} \nOffline: {offline}```")
            file = discord.File("onlinediscord.png", filename = "onlinediscord.png")
            await message.channel.send("onlinediscord.png", file=file)


client.loop.create_task(metrics_background_task())
client.run(#your token here)

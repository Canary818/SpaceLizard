import discord
import random
from discord.ext import commands
import requests
import sqlite3
import time
from datetime import datetime
 
# read API ket / token from file
with open("keys.txt") as file:
    TOKEN = file.readline()      # discord token
    API_KEY = file.readline()    # NASA API key

intents = discord.Intents.default()
intents.message_content = True

# create Discord client
client = commands.Bot(command_prefix="$", intents=intents)

# get current day
global date
date = datetime.now().strftime("%Y-%m-%d")

def str_time_prop(start, end, time_format, prop):
    '''
    Input params: start (str), end (str), format (str), prop (float from 0-1)
    Return type: str
    '''
    stime = time.mktime(time.strptime(start, time_format))
    etime = time.mktime(time.strptime(end, time_format))
    ptime = stime + prop * (etime - stime)
    return time.strftime(time_format, time.localtime(ptime))

def random_date(start, end, prop):
    '''
    Input params: start (str), end (str), prop (float from 0-1)
    Return type: str
    '''
    return str_time_prop(start, end, '%Y-%m-%d', prop)

def randQuestion():
    '''
    Input params: none
    Return type: tuple(int, str)
    Returns a random question number and question text from quiz database with all options attached
    '''
    # connect to quiz database and create cursor
    db = sqlite3.connect("quiz.db")
    cur = db.cursor()
    randQn = str(random.randint(1,10))
    question = cur.execute("SELECT QuestionText FROM Questions WHERE QuestionNumber = ?", randQn).fetchone()[0]
    question += "\n1. "
    question += cur.execute("SELECT OptionOne FROM Questions WHERE QuestionNumber = ?", randQn).fetchone()[0]
    question += "\n2. "
    question += cur.execute("SELECT OptionTwo FROM Questions WHERE QuestionNumber = ?", randQn).fetchone()[0]
    question += "\n3. "
    question += cur.execute("SELECT OptionThree FROM Questions WHERE QuestionNumber = ?", randQn).fetchone()[0]
    question += "\n4. "
    question += cur.execute("SELECT OptionFour FROM Questions WHERE QuestionNumber = ?", randQn).fetchone()[0]
    question += "\n"
    db.close()

    return randQn, question

def getCorrectAnswer(question, inputAns):
    '''
    Input params: question (int), inputAns (int)
    Return type: string
    '''
    # connect to quiz database and create cursor
    db = sqlite3.connect("quiz.db")
    cur = db.cursor()
    statement = "SELECT CorrectOption FROM Questions WHERE QuestionNumber = ?"
    answer = cur.execute(statement, question).fetchone()[0]
    db.close()

    if answer == inputAns:
        return "Correct!"

    return f"Wrong, the correct answer was option {answer}."

def fetchAsteroidNeowsFeed():
    '''
    Input params: none
    Return type: dict
    Gets json data from NASA API
    '''
    global date
    URL_NeoFeed = "https://api.nasa.gov/neo/rest/v1/feed"
    params = {
    'api_key':API_KEY,
    'start_date':date,
    'end_date':date
    }
    response = requests.get(URL_NeoFeed,params=params).json()

    return response

def asteroidData():
    '''
    Input params: none
    Return type: string
    Gets name, approach time, and url information from json response from API
    '''
    json_data = fetchAsteroidNeowsFeed()["near_earth_objects"][date]
    display = "Here are the asteroids passing by today!\n"

    for i in range(len(json_data)):
        display += json_data[i]['name']
        display += " : approaching at "
        display += json_data[i]['close_approach_data'][0]['close_approach_date_full'][-5:]
        display += "\n"
        display += json_data[i]['nasa_jpl_url']
        display += "\n\n"

    return display


# discord bot event & commands

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

client.remove_command('help')
@client.command()
async def help(ctx):
    embed=discord.Embed(
      title= "Commands",
      description= "All commands use the '$' prefix!\n\n**$help**: List commands\n**$asteroid**: A list of asteroids that will pass by Earth today\n**$image**: Show the Astronomy Picture of the Day, \n**$image rand**: Show a random Astronomy Picture of the Day\n**$image YYYY/MM/DD**: Show Astronomy Picture of the Day for the given day\n**$trivia** Small astronomy trivia question!\n",
      color= 2326507)
    await ctx.send(embed=embed)

@client.command()
async def asteroid(ctx):
    await ctx.send(asteroidData())

# View object with 4 buttons for trivia
class MyView(discord.ui.View):
    def __init__(self, qn):
        super().__init__()
        self.qn = qn
        
    @discord.ui.button(label="1", style=discord.ButtonStyle.primary)
    async def option1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(getCorrectAnswer(self.qn, 1))

    @discord.ui.button(label="2", style=discord.ButtonStyle.primary)
    async def option2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(getCorrectAnswer(self.qn, 2))

    @discord.ui.button(label="3", style=discord.ButtonStyle.primary)
    async def option3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(getCorrectAnswer(self.qn, 3))

    @discord.ui.button(label="4", style=discord.ButtonStyle.primary)
    async def option4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(getCorrectAnswer(self.qn, 4))

@client.command()
async def trivia(ctx):
    question = randQuestion()
    qnNum = question[0]
    qnText = question[1]
    await ctx.send(qnText, view=MyView(qnNum))

@client.command()
async def image(ctx, arg = None):
    day = date
    if arg == "random" or arg == "rand":
        day = random_date("1995-06-16", "2024-11-16", random.random())
    elif arg:
        day = arg
        day = day.replace('/', '-')
    params = {
        'api_key': API_KEY,
        'date': day,
        'hd':'True'
    }
    response = requests.get("https://api.nasa.gov/planetary/apod",params=params).json()
    url = response['hdurl']
    embed=discord.Embed(title= "Astronomy Picture of the Day for " + day, color= 2326507, url = url)
    embed.set_image(url = url)
    await ctx.send(embed = embed)
      
      
client.run(TOKEN)


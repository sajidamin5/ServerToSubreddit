import discord
import numpy
import os
import random
import asyncio
import time
from discord.ext import commands
from PIL import Image
from datetime import datetime
import json
import nltk
from nltk.corpus import wordnet
import random
import platform
import sqlite3
from collections import deque



import requests


# TODO: make global constants that are somehow protected or add to zhsrc file
token = 'NzcwOTU3MDU2NjE4MTM1NTUz.GhEOVg.Po-iJ21WZ9ZUqt6F3C6GfP7ZnoQV7y2n1Qu53U'


# run only the first time
nltk.download('wordnet')


intents = discord.Intents.all() 
client = discord.Client(intents=intents)

# Create bot instance and set command prefix
bot = commands.Bot(command_prefix="!", intents=intents)

# Set up the intents for your bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

# global structure to store balances
# wallets = {}
conn = sqlite3.connect("wallets.db")
tablePointer = conn.cursor()
tablePointer.execute("CREATE TABLE IF NOT EXISTS tblWallets (userID INTEGER PRIMARY KEY, balance INTEGER)")

# pokemon globals stuff
pokedex = None
reverse_pokedex = None
images_dir = '/Users/Sajid/Desktop/sprites/pokemon'
with open("pokedex.json", "r", encoding="utf-8") as f:
	pokedex = json.load(f)
	reverse_pokedex = {v.lower(): k for k, v in pokedex.items()}

# coup globals stuff
gameState = None

class GameState:
	def __init__(self, players):

		ids = [p.id for p in players]
		if len(ids) != len(set(ids)):
			raise ValueError("Duplicate players detected!")
		
		# coins/hands of each player
		self.players = {player.id: {"coins": 2, "hand" : []} for player in players}

		self.cards = {"Duke":3, "Assassin":3, "Contessa":3, "Ambassador":3, "Captain":3}
		
		# turn ordering via deque
		self.turn_order = deque(players)

		# list of player.ids to store players that can be accused
		self.accusable = ""

		# expand dictionary into a list of cards
		self.deck = []
		for card, count in self.cards.items():
			self.deck.extend([card] * count)

		# shuffle deck once
		random.shuffle(self.deck)

		# SET HANDS
		for player, pData in self.players.items():
			# two cards per player
			pData["hand"].append(self.deck.pop())
			pData["hand"].append(self.deck.pop())

	def set_accusable(self, player_id=""):
		self.accusable = player_id
	
	def get_accusable(self):
		return self.accusable

	def get_roles(self):
		return list(self.cards.keys())

	def get_players(self):
		return list(self.players.keys())

	def next_turn(self):
		self.turn_order.rotate(-1)  # move left
		return self.turn_order[0]

	def current_player(self):
		return self.turn_order[0]

	def get_coins(self):
		return {pid: pdata["coins"] for pid, pdata in self.players.items()}
	
	def add_coins(self, player_id, amount):
		if player_id in self.players:
			self.players[player_id]["coins"] += amount
	
	def remove_coins(self, player_id, amount):
		if player_id in self.players:
			self.players[player_id]["coins"] = max(0, self.players[player_id]["coins"] - amount)

	def remove_card(self, player_id, idx):
		if player_id in self.players:
			self.player[player_id]["hand"] = self.player[player_id]["hand"].remove(idx)

	def get_hand(self, player_id):
		if player_id in self.players:
			return self.players[player_id]["hand"]
		
	def get_hands(self):
		return {pid: pData["hand"] for pid, pData in self.players.items()}


	# when a player needs to replace card from hand with one in deck
	def draw_card(self, player_id, card):
		player = self.players[player_id]
		self.deck.add(player["hand"].remove(card))
		random.shuffle(self.deck)
		player["hand"].add(self.deck.pop())
		return
	
	def __str__(self):
        # readable string when you do str(game_state) or print(game_state)
		lines = []
		for pid, pdata in self.players.items():
			lines.append(f"Player {pid}: {pdata['coins']} coins, hand={pdata['hand']}")
		return "\n".join(lines)
	
@bot.command(help="Play a game of coup")
async def coup(ctx, *players: discord.Member):
	global gameState 

	if gameState is not None:
		return await ctx.send("A coup is already underway! End it first with !endgame.")
	
	# initialize players
	if not players or len(players) == 1:
		return await ctx.send("You need atleast two players to play coup!")

	for player in players:
		if not isinstance(player, discord.Member):
			return await ctx.send("please only supply the @s of members in the server")

	gameState = GameState(players)
	await ctx.send("A coup has begun to brew! Your roles have been sent to you, good luck rebels.")

	# notify player of handstate
	for player_id, hand in  gameState.get_hands().items():
		try:
			player = await bot.fetch_user(player_id)  # returns a discord.User
			await player.send(f"Your hand is the following: \n"
					 			f"Card 1: {hand[0]} \n"
								f"Card 2: {hand[1]} \n"
					 			"Good luck!" )
		except discord.Forbidden:
			await ctx.send(f"I couldn't DM {player.mention}. They might have DMs disabled.")

@bot.command(help="COUP COMMAND ONLY: Performs an action given a role")
async def action(ctx, role="", player:discord.Member = None, ):
	# ERROR HANDLING
	if gameState is None: return await ctx.send(f"No game currently in progress")
	if ctx.author is not gameState.current_player(): return await ctx.send(f"{ctx.author.mention}, It's not your turn!")
	if role=="" or role.lower() not in [w.lower() for w in gameState.get_roles()]: 
		return await ctx.send(f"{ctx.author.mention}, Specify a role who's action you'll perform!")

	gameState.set_accusable("")
	print(gameState.get_accusable())

	# TODO: case for when role -> COUP because this cannot be countered
	# TODO: increase counteraction window timer but incorporate a vote skip function if all players (excluding actioneer vote yes)
	await ctx.send(f"{ctx.author.display_name} is performing {role}! \n"
					"the rest of the players have 14 seconds to perform a counteraction - type **counter** in chat \n"
					"all players can type **skip** to move on")
	
	gameState.set_accusable(ctx.author.id)
	print(f"accusable: {gameState.get_accusable()}")

	# private function to pass into bot.wait_for()
	def check(message: discord.message):
		return message.channel == ctx.channel
	
	eligible = gameState.get_players()
	print(eligible)
	eligible.remove(ctx.author.id)
	print(eligible)
	skips = []
	try:
		guess = await bot.wait_for("message", 
							 				check=lambda m: m.author.id in eligible and m.content.lower() in ("counter", "skip"), 
											timeout=14.0)
		
		if guess.content.strip().lower() == "counter":
			gameState.set_accusable(guess.author.id)
			print(gameState.get_accusable())
			match role:
				case "duke":
					await ctx.send(f"foreign aid blocked by {guess.author.display_name}!")
				case "contessa":
					await ctx.send(f"assassin blocked by {guess.author.display_name}!")
				case "ambassador", "captain":
					await ctx.send(f"steal blocked by {guess.author.display_name}!")
		elif guess.content.strip().lower() == "skip":
			if guess.author.id not in skips: skips.append(guess.author.id)
			print(skips)
			if skips == eligible:
				return await ctx.send("counteraction phase skipped")
		else:
			await ctx.send(f"are you trying to counter? Maybe you mispelled: **counter**")

	except asyncio.TimeoutError:
		
		await ctx.channel.send(f":alarm_clock: Counter action period closed! {ctx.author.display_name}'s action was performed")
		match role:
			case "duke":
				await ctx.send(f"{ctx.author.mention} recieved foreign aid!")
			case "contessa":
				await ctx.send(f"nothing happpened...")
			case "assassin":
				await ctx.send(f"{ctx.author.mention} has killed {player}!")
			case "ambassador":
				await ctx.send(f"redraw!")
			case "captain":
				await ctx.send(f"steal!")

@bot.command(help="COUP COMMAND ONLY: Challenge a player of a given role")
async def challenge(ctx, player:discord.Member, role):
	# ERROR HANDLING
	if gameState is None: return await ctx.send(f"No game currently in progress")
	if player != gameState.get_accusable(): 
		return await ctx.send(f"{player.display_name} is not a valid player to challenge at this time. However, you may challenge {gameState.get_accusable()}")
	if role=="" or role.lower() not in [w.lower() for w in gameState.get_roles()]: 
		return await ctx.send(f"{ctx.author.mention}, Specify a valid role to accuse them of!")
	
	# check if challenged player has role
	if role.lower() in (card.lower() for card in gameState.get_hand(player.id)):
		await ctx.send(f"{ctx.author.display_name} has succesfully challenged {player.display_name} for having {role}! \n"
				 	   f"{player.display_name} now has 1 card left")
	else:
		await ctx.send(f"{ctx.author.display_name} has unsuccesfully challenged {player.display_name} for having {role}! \n"
				 	   f"{ctx.author.display_name} will now choose a card to discard back to the deck."
					   f"Please wait a moment while they choose which card to lose")
		
	def check(m: discord.Message):
		# ✅ Only accept if:
		# 1. Author is the target player
		# 2. Message is in a DM channel
		print(m.author)
		print(ctx.author)
		return m.author == ctx.author and isinstance(m.channel, discord.DMChannel)
	
	try:
		choice = await bot.wait_for("message", check=check, timeout=20.0)
		if not choice.content.isnumeric() and (choice.content == 1 or choice.content == 2):
			await ctx.player.send("type 1 or 2 for which card to lose")
		else:
			gameState.remove_card(player, choice - 1)
			await ctx.player.send(f"Your hand is now: {gameState.get_hand[0]} Good Luck.")
			await ctx.send(f"{ctx.author.display_name} is now down to one card.")
	except asyncio.TimeoutError:
		gameState.remove_card(player, random.randint(0, 1))
		await ctx.player.send("Times up! I chose for you"
							  f"Your hand is now: {gameState.get_hand[0]} Good Luck.")
		await ctx.send(f"{ctx.author.display_name} is now down to one card.")


@bot.command(help="End current game of coup")
async def endgame(ctx):
	global gameState

	if gameState is None:
		return await ctx.send("No game is currently running.")

	gameState = None
	await ctx.send("Game ended.")

# private balance func
def init_user_balance(userID):
	tablePointer.execute("SELECT balance FROM tblWallets WHERE userID = ?", (userID,))
	row = tablePointer.fetchone()
	if row is None:
		tablePointer.execute("INSERT INTO tblWallets (userID, balance) VALUES (?, ?)", (userID, 0))
		conn.commit()
		return 0
	return row[0]

@bot.command(help="You've  met with a terrible fate, haven't you?")
async def m8b(ctx, *, question=""):
	if question == "":
		await ctx.send(f"Ask me something")
		return

	magic_8_ball_responses = [
    # P	ositive
    "It is certain.",
    "It is decidedly so.",
    "Without a doubt.",
    "Yes – definitely.",
    "You may rely on it.",
    "As I see it, yes.",
    "Most likely.",
    "Outlook good.",
    "Yes.",
    "Signs point to yes.",

    # Neutral
    "Reply hazy, try again.",
    "Ask again later.",
    "Better not tell you now.",
    "Cannot predict now.",
    "Concentrate and ask again.",

    # Negative
    "Don't count on it.",
    "My reply is no.",
    "My sources say no.",
    "Outlook not so good.",
    "Very doubtful."
	]
	
	await ctx.send(f"To answer your question \"{question}\": \n{random.choice(magic_8_ball_responses)}")


@bot.command(help="I HAVE NOTHING")
async def wallet(ctx, amount=0):
	bal = init_user_balance(ctx.author.id)
	positive = [":money_mouth:", ":money_with_wings:", ":dollar:", ":moneybag:"]
	negative = [":roll_of_paper:", ":no_entry:", ":stuck_out_tongue_closed_eyes:", ":chart_with_downwards_trend:", ":pensive:"]
	
	if amount != 0:
		tablePointer.execute("UPDATE tblWallets SET balance = ? WHERE userID = ?", (amount + bal, ctx.author.id))
		conn.commit()
		bal = amount + bal
		await ctx.send(f"{abs(amount)} has been {'added to' if amount > 0 else 'deducted from'} your account {random.choice(positive) if amount > 0 else random.choice(negative)}")

	await ctx.send(f"{ctx.author.mention}, you have {bal} $ag coins! {random.choice(positive) if  bal > 0  else random.choice(negative)}")

@bot.command(help="Do not gamble, you will lose")
async def slot(ctx, amount: str="0", seed="default"):
	if not amount.isnumeric():
		await ctx.send(f"{ctx.author.mention} go home jit, you're drunk.")
		return

	amount = int(amount)
	if amount == 0:
		await ctx.send(f"{ctx.author.mention} put some money in to play, broke ass jit!")
		return
	

	userBal = init_user_balance(ctx.author.id)
	if userBal <= 0 or amount > userBal:
		await ctx.send(f"{ctx.author.mention} insufficient funds, get your money up jit")
		return
	
	reel = [":cherries:", ":cheese:", ":tangerine:", ":banana:", ":seven:", ":watermelon:", ":hearts:"]
	pulls = ["anita max wynn", "max win please", "unreal", "shameless", "don't get it twisted", "twisted", "unbelievable", "...", "we're so due", "cmon bitch", "let us in bitch", "bad seed", "please", "BRO", "heart heart heart", "HIT HIT HTI", "retrig man",  "just do it", "just get us in", "please bro", "fr", "wtf", "cmooon", "please", "no dude", "just lock in", "rolling", "pls", "next one"]
	sevenSevenSeven = ["BOOM JACKPOT", "BAAAAAAAAAAANG", "MAX WINNNNN"]
	threeOfAKind = ["not bad", "OKAYY", "nooot bad", "lfg"]
	reelOne = random.choice(reel)
	reelTwo = random.choice(reel)
	reelThree = random.choice(reel)
	msg = ""

	await ctx.channel.send(f"Rolling for {amount}!")

	if {reelOne, reelTwo, reelThree} == {":seven:"}:
		msg = random.choice(sevenSevenSeven)
		amount = amount * 100
	elif len({reelOne, reelTwo, reelThree}) == 1:
		msg = msg = random.choice(threeOfAKind)
		amount = amount * 10 
	elif seed.lower() == "win":
		msg = random.choice(sevenSevenSeven)
		reelOne = reelTwo = reelThree = ":seven:"
		amount = amount * 100
	elif seed.lower() != "win" and seed != "default":
		msg = "terrible seed"
		amount = amount * -1
	else:
		msg = random.choice(pulls)
		amount = amount * -1


	# SLOT ASCII
	divider = "+" + '-'*19 +" + " + "\n"
	margin = int((21 - len(msg)) / 2)
	await ctx.channel.send(divider + "|   SLOT MACHINE    |" + "\n" + 
							divider + "|       " + reelOne + "    " + reelTwo + "    "  + reelThree + "    |" + "\n" +
							divider + "|" + " "*margin + msg + " "*margin   + "     <-------------" + "\n"  +
							divider)	
	# update wallet
	await wallet(ctx, amount)

@client.event
async def on_ready():
    print("Bot is connected to Discord")

@bot.command(help="tell's you what you need to know about yourself")
async def gay(ctx):
	await ctx.channel.send(ctx.author.mention + " you are " + str(random.randint(0, 100)) + "% gay")
 
@bot.command(help="operating system I am currently running on")
async def system(ctx):
    this_os = platform.system()
    if this_os == "Darwin":
        this_os = "macOS"
        
    await ctx.channel.send(f"I am currently running on {this_os}!")

@bot.command(help="see how big you are!")      
async def penis(ctx):
	shaft = ""
	len = random.randint(1, 100)
	for x in range(len):
		shaft += "="
	await ctx.channel.send(ctx.author.mention + " your cock is  8" + shaft + "D long")
	
@bot.command(help="who's that pokemon?")   
async def pokemon(ctx, pokeName="none"):

	if pokeName != "none":
		pokeNum = reverse_pokedex.get(pokeName.lower())
		if pokeNum == None:
			await ctx.channel.send(f"{ctx.author.mention} Are you sure you spelled {pokeName} correctly?")
			return
		
		with open(os.path.join(images_dir, f"{pokeNum}.png"), 'rb') as f:
			encounter = [":scream_cat:", ":astonished:", ":exploding_head:"]
			await ctx.channel.send(ctx.author.mention, file=discord.File(f, "poke.png"))
			await ctx.channel.send(f"A wild {pokedex[pokeNum]} appeared! {random.choice(encounter)}")
		return
	
	if platform.system() == "Darwin":
		with open("/Users/sajidamin5/Documents/Python Stuff/ServerToSubreddit/ServerToSubreddit/pokelist.txt") as f:
			poke_list = f.read().split(",")
			pokemon = poke_list[random.randint(0, len(poke_list) - 1)]
			await ctx.channel.send(f"{ctx.author.mention} {pokemon}")
			return
		
	# Getting paths and names
	num = random.randint(1, 649)
	image_path = os.path.join(images_dir, f"{num}.png")
	pokeName = pokedex[str(num)]

	with open(image_path, 'rb') as f:
		await ctx.channel.send(ctx.author.mention, file=discord.File(f, "poke.png"))
		await ctx.channel.send("Who's that Pokémon?")
		# await ctx.channel.send(f"It's {pokeName}!")
		# print(num) DEBUG
	
	# private function to pass into bot.wait_for()
	def check(message: discord.message):
		# DEBUG
		# print("Heard:", message.content, "from", message.author)
		# print(f"guess: {message.content} pokemon: {pokeName}")
		return message.author == ctx.author and message.channel == ctx.channel

	try:
		guess = await bot.wait_for("message", check=check, timeout=10.0)
		correct = ["Baaang", "Correct", "Nice", "Yes"]
		incorrect = ["Nope", "Wrong", "Nah", "Incorrect"]
		if guess.content.strip().lower() == pokeName.lower():
			await ctx.channel.send(f":white_check_mark: {random.choice(correct)}! It's **{pokeName}**")
			await wallet(ctx, 100)
		else:
			await ctx.channel.send(f":x: {random.choice(incorrect)}. It's actually {pokeName}")
			await wallet(ctx, -10)
	except asyncio.TimeoutError:
		await ctx.channel.send(f":alarm_clock: Too slow! The Pokémon was **{pokeName}**.")

		
@bot.command(
    name="get_messages",
    help="""
Fetches messages from a channel.
Arguments:
  channel_id: ID of the channel to fetch messages from
  start_date: Start date in YYYY-MM-DD format
  end_date: End date in YYYY-MM-DD format
  author: (Optional) Filter by author username
"""
)
async def get_messages(ctx, channel_id, start_date, end_date, author="default"):
    
# Convert the date strings to datetime objects
	start_date = datetime.strptime(start_date, "%m-%d-%Y")
	end_date = datetime.strptime(end_date, "%m-%d-%Y")

	# Ensure end_date is after start_date
	if end_date <= start_date:
		await ctx.send("End date must be after start date.")
		return

	# Get the channel object by ID
	channel = bot.get_channel(channel_id)
	if not channel:
		await ctx.send("Channel not found!")
		return

	messages = []
	total_messages = 1
	start_time = time.time()  # Record start time

	# Retrieve message history in the specified date range
	current_message_count = 0
	async for message in channel.history(limit=None, after=start_date, before=end_date):
		# Check for author filter
		if author == "default" or message.author.name == author:
			msg_data = f"{message.author}: {message.content} (at {message.created_at})\n"
			messages.append(msg_data)
			total_messages += 1

	progress_message = await ctx.send("Starting to retrieve messages...")
	# Update the progress message every 10 messages to avoid too many edits
	if current_message_count % 10 == 0:
		progress = (current_message_count / total_messages) * 100
		await progress_message.edit(content=f"Retrieving messages... {progress:.2f}% complete")


	# Write messages to a text file
	# Define the file path in the "logs" folder
	os.makedirs("logs", exist_ok=True)
	date_format = "%Y-%m-%d"
	time_format = "%H_%M_%S"
	file_name = f"logs/{author}'s messages from {start_date.strftime('%m-%d-%Y')} to {end_date.strftime('%m-%d-%Y')} generated on {time.strftime(date_format)} at {time.strftime(time_format)}.txt"
	with open(file_name, "w", encoding="utf-8") as file:
		file.writelines(messages)

	end_time = time.time()  # Record end time
	total_time = end_time - start_time  # Calculate time taken
	
	# Edit progress message to show completion
	await progress_message.edit(content=f"Messages retrieved and written to file in {total_time:.2f} seconds.")

	# Send the file
	await ctx.send("Here is the messages file:", file=discord.File(file_name))

@bot.command(name='word', help="picks a random word")    
async def word(ctx, word=""):
	word_length = len(word)

	# Get all lemmas in WordNet
	all_lemmas = list(wordnet.all_lemma_names())


	# Pick a random word
	if word_length == 0:
		word = random.choice(all_lemmas)
	synsets = wordnet.synsets(word)

	await ctx.send(f"Your{' **random**' if word_length == 0 else ''} word is: **{word.replace('_', ' ')}**")

	if synsets:
		for s in synsets:
			definition_text = f"**Definition:** {s.definition()}"
			await ctx.send(definition_text)
	else:
		await ctx.send("No definitions found.")

@bot.command(name='shutdown', help="this kills the bot")
async def shutdown(ctx):
	await ctx.send("Shutting down...")
	await bot.close()  # Safely closes the bot connection

# Catch invalid commands
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        command_names = [command.name for command in bot.commands]
        help_text = f"{error} Here are my commands:\n" + "\n".join(command_names)
        await ctx.send(help_text + "\n" + "type !help to learn more about each one!")
    else:
        raise error  # re-raise other errors so you can see them


bot.run(token)
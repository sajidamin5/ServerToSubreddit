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
import random
import platform
import sqlite3
from collections import deque
from discord import Embed
from dotenv import load_dotenv
import requests
import math
import wn

# Grab token from system rather than hardcoding that boy into the file
load_dotenv()  # loads .env into environment for local dev
token = os.environ.get("DISCORD_TOKEN")
if not token:
    raise RuntimeError("DISCORD_TOKEN environment variable not set. Add to system vars or create .env with DISCORD_TOKEN=<token>")



hidden_gems = [":cucumber:", ":pretzel:", ":chipmunk:", ":llama:", ":hedgehog:", ":pickle:", ":peacock:", ":yo_yo:", ":jigsaw:", ":magic_wand:", ":jellyfish:", ":sewing_needle:", ":placard:", ":hook:", ":magnet:", ":test_tube:", ":petri_dish:", ":abacus:", ":teddy_bear:", ":crayon:", ":probing_cane:", ":mouse_trap:", ":puzzle_piece:", ":ringed_planet:", ":roll_of_paper:", ":seal:", ":wing:", ":worm:", ":zombie:", ":transgender_symbol:", ":ninja:", ":pirate_flag:", ":olive:", ":fondue:", ":waffle:", ":bagel:", ":teapot:", ":bubble_tea:", ":jar:", ":cockroach:", ":beetle:", ":beaver:", ":sloth:", ":otter:", ":skunk:", ":flamingo:", ":feather:", ":wing:", ":bone:", ":coral:", ":lotus:", ":potted_plant:", ":rock:", ":wood:", ":hut:", ":thread:", ":yarn:", ":knot:", ":safety_pin:"]
champion_names = []


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
if not platform.system() == "Darwin":
	with open("pokedex.json", "r", encoding="utf-8") as f:
		pokedex = json.load(f)
		reverse_pokedex = {v.lower(): k for k, v in pokedex.items()}

# coup globals stuff
gameState = None

@bot.command(name='word', help="picks a random word")    	
async def word(ctx, word=""):
	word_length = len(word)

	if wn.lexicons():
		print("Some lexicon(s) installed")
		print(f"lexicons: {wn.lexicons()}  num wordnets: {len(wn.words())}\n")
		lexicon = wn.Wordnet('omw-en:1.4')

	else:
		print("No lexicons installed — need to download.")
		# Download lexicons if they don't exist yet
		wn.download('omw-en')

	# Get synset
	synsets = list(wn.Wordnet().synsets())

	syn = random.choice(synsets)
	
	# pick one lemma from that synset
	lemma = random.choice(syn.lemmas())
	await ctx.send(f"Definitions for **{lemma}**:")
	for syn in lexicon.synsets(lemma):
		await ctx.send(f"- {syn.definition()}\n")







class GameState:
	def __init__(self, players):

		# channel game was instatiated in
		self.channel = ""
  
		ids = [p.id for p in players]
		if len(ids) != len(set(ids)):
			raise ValueError("Duplicate players detected!")
		
		self.phase = ""

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

	def set_channel(self, channel=""):
		self.channel = channel
	
	def get_channel(self):
		return self.channel

	def set_phase(self, phase=""):
		self.phase=phase
	
	def get_phase(self):
		return self.phase
 
	def get_roles(self):
		return list(self.cards.keys())

	def get_players(self):
		return list(self.players.keys())

	def next_turn(self):
		self.turn_order.rotate(-1)  # move left
		return self.turn_order[0]

	def current_player(self):
		return self.turn_order[0]

	def remove_player(self, player):
		return self.turn_order.remove(player)

	def players_alive(self):
		return len(self.turn_order)

	def get_coins(self):
		return {pid: pdata["coins"] for pid, pdata in self.players.items()}
	
	def add_coins(self, player_id, amount):
		if player_id in self.players:
			self.players[player_id]["coins"] += amount
	
	def remove_coins(self, player_id, amount):
		if player_id in self.players:
			self.players[player_id]["coins"] = max(0, self.players[player_id]["coins"] - amount)

	# returns the removed card as well if needed
	def remove_card(self, player_id, idx):
		if player_id in self.players:
			hand = self.players[player_id]["hand"]
   
			if isinstance(idx, int): # index case
				removed = hand.pop(idx)

			if isinstance(idx, str) and idx in hand: # role case
				removed = hand.remove(idx)
    
			self.deck.append(removed)
			random.shuffle(self.deck)
			self.players[player_id]["hand"] = hand
			return removed
	
	

	def get_hand(self, player_id, pretty=False):
		if player_id in self.players:
			hand = self.players[player_id]["hand"]
			if not pretty:
				return hand
			else:
				toString = f"Your hand is now the following: \n"
				for x, card in enumerate(hand):
					toString += f"Card {x+1}: {card} \n"
				toString = toString.rstrip("\n")
				return toString
		
		
	def get_hands(self):
		return {pid: pData["hand"] for pid, pData in self.players.items()}


	# when a player needs to replace card from hand with one in deck
	def draw_card(self, player_id, card):
		player = self.players[player_id]
		self.deck.append(player["hand"].remove(card))
		random.shuffle(self.deck)
		new = self.deck.pop()
		player["hand"].append(new)
		return new
	
	def __str__(self):
        # readable string when you do str(game_state) or print(game_state)
		lines = []
		for pid, pdata in self.players.items():
			lines.append(f"Player {pid}: {pdata['coins']} coins, hand={pdata['hand']}")
		return "\n".join(lines)

RANKS = "23456789TJQKA"
SUITS = "CDHS"  # clubs, diamonds, hearts, spades

def id_to_card(i: int) -> str:
    return RANKS[i % 13] + SUITS[i // 13]

def card_to_id(rank: str, suit: str) -> int:
    return RANKS.index(rank) + SUITS.index(suit) * 13

("Chat-GPT", "Raptor Mini")
class StandardDeck:
    """Efficient 52-card deck using ints 0..51."""
    def __init__(self, decks: int = 1, shuffle: bool = True):
        self._cards = [i for _ in range(decks) for i in range(52)]
        if shuffle:
            self.shuffle()

    def shuffle(self):
        random.shuffle(self._cards)

    def draw(self, n: int = 1):
        if n == 1:
            return self._cards.pop() if self._cards else None
        out = []
        for _ in range(min(n, len(self._cards))):
            out.append(self._cards.pop())
        return out

    def deal(self, num_hands: int, cards_per_hand: int):
        hands = [[] for _ in range(num_hands)]
        for _ in range(cards_per_hand):
            for h in hands:
                card = self.draw()
                if card is None:
                    return hands
                h.append(card)
        return hands

    def remaining(self):
        return len(self._cards)

    def reset(self, decks: int = 1):
        self.__init__(decks=decks, shuffle=True)

@bot.command(help="Poker Spot Generator: Gives you a preflop hand and position at the table")
async def preflop(ctx, stack=0, position="", amount="", bigBlind=3, smallBlind=1):
	deck = StandardDeck()

	positons = ["UTG", "UTG+1", "UTG+2", "MP1", "MP2", "Hijack", "Cutoff", "Button", "Small", "Big"]
	positonIndex = {p.lower(): i for i, p in enumerate(positons)}

	table = {}
	

	# TODO: label  

	mult = random.SystemRandom().uniform(1.0, 3.0)
	player = (random.choice(positons) if position == "" else position, 
										 math.floor(bigBlind * mult) if stack == 0 else stack, 
										 id_to_card(deck.draw()), id_to_card(deck.draw()))


	await ctx.send(player)

	if player[0] == "Small":
		smallBlind = player[1]

	if player[0] == "Big":
		bigBlind = player[1]

	await ctx.send(f"Your Blind Multiplier is: {mult}")

	return await ptable(ctx, player[0], f"{player[0]}={player[1]}", 
					 	f"Small={smallBlind}", f"Big={bigBlind}")



# ASCII poker table helpers

def _label_for(pos: str, stacks: dict | None, selected: bool) -> str:
    """Return a centered label text with optional stack and selection marker."""
    stack = ""
    if stacks is not None:
        # accept both pos and lower-case keys
        stack_val = stacks.get(pos) if pos in stacks else stacks.get(pos.lower())
        if stack_val is not None:
            stack = f"({stack_val})"
    label = f"{pos}{stack}"
    if selected:
        label = f"> {label} <"
    return label

def render_poker_table_ascii(selected_pos: str = "UTG", stacks: dict | None = None) -> str:
	"""
	Build a simple 9-seat ASCII table and highlight selected_pos.
	Returns a string (already wrapped as a code block) suitable for ctx.send(...).
	"""
	# Normalize
	sel = selected_pos.strip().lower() if selected_pos else ""
	labels = []
	POSITIONS = ["UTG+2", "MP-1", "MP-2", "UTG", "HiJack", "Big", "Small", "Button", "CO"]
	for pos in POSITIONS:
		labels.append(_label_for(pos, stacks, pos.lower() == sel))

	# choose column width to center-alig	everything
	width = max(len(lbl) for lbl in labels) + 2
	buffer = "      	            "
	def pad(txt): return txt.center(width)

	# layout rows: top(0,1,2) middle-left(3) middle-right(4) bottom(5,6,7,8)
	row1 = (buffer + "       ") + "   ".join(pad(labels[i]) for i in (0, 1, 2))
	row2 = pad(labels[3]) + buffer * 3 + "             " + str(labels[4])
	row3 = (buffer) + "   ".join(pad(labels[i]) for i in (5, 6, 7, 8))
	header = "```" + "\n"
	footer  = "\n" + "```"

	# build and return as a code block for Discord
	table = header + row1 + ("\n" * 4) + row2 + ("\n" * 4) + row3 + footer

	return table

@bot.command(help="Show an ASCII poker table and mark a given position")
async def ptable(ctx, position: str = "UTG", *stack_pairs):
	POSITIONS = ["UTG", "UTG+1", "UTG+2", "MP2", "Hijack", "Cutoff", "Button", "Small", "Big"]
	stacks = {}
	for p in stack_pairs:
		if "=" in p:
			key, val = p.split("=", 1)
			try:
				stacks[key.strip()] = int(val.strip())
			except ValueError:
				# ignore bad stack entry
				continue

	# validate position
	if position.strip().lower() not in (p.lower() for p in POSITIONS):
		return await ctx.send(f"Unknown position: {position}. Valid: {', '.join(POSITIONS)}")

	ascii_table = render_poker_table_ascii(position, stacks or None)
	await ctx.send(ascii_table)

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
	gameState.set_channel(ctx.channel)
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
   


@bot.command(help="Simple Chat Level Clear/Reset Command for when you need Mr.Clean to wipe shit down")
async def obfuscate(ctx):
	'''
    HUERISTICS:
    1) requires trusted/unstrusted parties (can use existing whitelist/blacklist/purgatory states)
    2) has to occur before observation of the obfuscated entity: i.e. observation ---> | ---> [screen]
    '''
	# await ctx.send(f"~"
    #  			    f"\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"
    #                f"\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"
    #                f"\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"
    #                f"\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"
    #                f"\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"
    #                f"\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"
    #                f"\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"
    #                f"\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"
    #                f"~")
    
	buffer = '~'
	for x in range(200):
			buffer += '\n'
	buffer += random.choice(hidden_gems)
	await ctx.send(buffer)
         
@bot.command(help="COUP COMMAND ONLY: Performs an action given a role")
async def action(ctx, role="", player:discord.Member = None, ):
	# ERROR HANDLING
	if gameState is None: return await ctx.send(f"No game currently in progress")
	if ctx.author is not gameState.current_player(): return await ctx.send(f"{ctx.author.mention}, It's not your turn!")
	if role=="" or role.lower() not in [w.lower() for w in gameState.get_roles()]: 
		return await ctx.send(f"{ctx.author.mention}, Specify a role who's action you'll perform!")
	if gameState.get_phase() == "action": return await ctx.send("Action currently in progress! Wait until it has resolved")

	# clearing accusable from previous action and resetting gamestate
	gameState.set_accusable("")
	gameState.set_phase("action")

	# TODO: case for when role -> COUP because this cannot be countered
	await ctx.send(f"{ctx.author.display_name} is performing {role}! \n"
					"the rest of the players have 10 seconds to perform a counteraction \n"
     				f"- type **counter** to perform a counteraction \n"
					f"- type **skip** to move to next turn (must be entered by all other players) \n"
     				f"- type (or copy) the following to challenge {ctx.author.display_name}'s {role}: ```!challenge @{ctx.author} {role.capitalize()}``` \n \n")

 
	gameState.set_accusable(ctx.author.id)
	# print(f"accusable: {gameState.get_accusable()}")
	
	eligible = gameState.get_players()
	# remove actioneer from eligble skipper pool
	eligible.remove(ctx.author.id)

	skips = []
	try:
		guess = await bot.wait_for("message", 
									check=lambda m: m.author.id in eligible 
									and m.content.lower() in ("counter", "skip") 
									and m.channel == gameState.get_channel(), 
									timeout=14.0)
  
		# exit if a player initiated a challenge
		if gameState.get_phase() == "challenge": return print("challenged")

		
		if guess.content.strip().lower() == "counter":
			gameState.set_accusable(guess.author.id)
			match role:
				case "duke":
					await ctx.send(f"{ctx.author.display_name}'s foreign aid blocked by {guess.author.display_name}!")
				case "contessa":
					await ctx.send(f"{ctx.author.display_name}'s assassin blocked by {guess.author.display_name}!")
				case "ambassador":
					await ctx.send(f"{ctx.author.display_name}'s steal blocked by {guess.author.display_name}!")
				case "captain":
					await ctx.send(f"{ctx.author.display_name}'s steal blocked by {guess.author.display_name}!")
     
		elif guess.content.strip().lower() == "skip":
			if guess.author.id not in skips: skips.append(guess.author.id)
			if skips == eligible:
				await ctx.send("counteraction phase skipped")
		else:
			await ctx.send(f"are you trying to counter? Maybe you mispelled: **counter**")

	except asyncio.TimeoutError:
		# exit if a player initiated a challenge
		if gameState.get_phase() == "challenge":
			gameState.next_turn()
			return 
  
		await ctx.channel.send(f":alarm_clock:  Counter action period closed!  :alarm_clock:  "
                         	   f"{ctx.author.display_name}'s action was performed")
		match role:
			case "duke":
				gameState.add_coins(ctx.author.id, 2)
				await ctx.send(f"{ctx.author.mention} recieved foreign aid! They now have {gameState.players[ctx.author.id]['coins']} tokens")
			case "contessa":
				await ctx.send(f"nothing happpened...")
			case "assassin":
				await ctx.send(f"{ctx.author.mention} has killed {player}!")
			case "ambassador":
				await ctx.send(f"redraw!")
			case "captain":
				await ctx.send(f"steal!")
    
    # increment turn counter forward
	gameState.set_phase("interim")
	gameState.next_turn()

# TODO: add logic so that player
@bot.command(help="COUP COMMAND ONLY: Challenge a player of a given role")
async def challenge(ctx, player:discord.Member, role):
	# ERROR HANDLING
	if gameState is None: return await ctx.send(f"No game currently in progress")
	if ctx.author.id == player.id: return await ctx.send("You can't challenge yourself, are you mad?")
	if player.id != gameState.get_accusable(): 
		return await ctx.send(f"{player.display_name} is not a valid player to challenge at this time." 
                        	  f"However, you may challenge {gameState.get_accusable()}")
	if role=="" or role.lower() not in [w.lower() for w in gameState.get_roles()]: 
		return await ctx.send(f"{ctx.author.mention}, Specify a valid role to accuse them of!")
	
	loser = None
	winner = None
 
	# check if challenged player has role
	if role.lower() not in (card.lower() for card in gameState.get_hand(player.id)):
		gameState.set_phase("challenge")
		await ctx.send(f"{ctx.author.display_name} has succesfully challenged {player.display_name} for having {role}! \n"
				 	   f"{player.mention} will now choose a card to discard back to the deck.")
		loser = player
	else:
		await ctx.send(f"{ctx.author.mention} has unsuccesfully challenged {player.display_name} for having {role}! \n"
				 	   f"{ctx.author.display_name} will now choose a card to discard and {player.display_name} will reshuffle their {role} and redraw.")
		loser = ctx.author
		winner = player
	await ctx.send(f"Please wait a moment while they choose which card to lose")

	# if winner is initialized, refresh their challenged role
	if winner is not None:
		newCard = gameState.draw_card(winner.id, role)
		await winner.send(f"\nYour {role} has been replaced with {newCard}. \n" 
                          f"{gameState.get_hand(winner.id, True)}")
	
	# only give choice if they have 2 cards, otherwise they lose their remaining
	if len(gameState.get_hand(loser.id)) == 2:
		await loser.send(f"Please reply 1 or 2 or which card you'd like to get rid of")
	else: 
		removed = gameState.remove_card(loser.id, 0)
		await loser.send(f"Your hand is gone since you only had {removed} left. You're out, GGs!")
		await ctx.send(f"{loser.display_name} has lost all their cards so they're out")
		gameState.remove_player(loser)

		# check for victory state:
		if gameState.players_alive() == 1:
			await ctx.send(f"Winner winner chicken dinner! {gameState.current_player().mention} is the last one standing")
			return endgame(ctx)

	def check(m: discord.Message):
		# ✅ Only accept if:
		# 1. Author is the target player
		# 2. Message is in a DM channel
		return m.author == loser and isinstance(m.channel, discord.DMChannel)

	try:
		choice = await bot.wait_for("message", check=check, timeout=10.0)
		if not choice.content.isnumeric():
			await loser.send("type 1 or 2 for which card to lose")
		else:
			removed = gameState.remove_card(loser.id, int(choice.content) - 1)
			await loser.send(f"{removed} has been returned back to the deck. \n" 
                    		 f"Your hand is now {gameState.get_hand(loser.id)[0]}, Good Luck.")
			await ctx.send(f"{loser.display_name} is now down to one card.")
	except asyncio.TimeoutError:
		removed = gameState.remove_card(loser.id, random.randint(0, len(gameState.get_hand(loser.id)) - 1))
		await loser.send("Times up! I chose for you. \n"
						f"{removed} has been returned back to the deck. \n" 
      					f"Your hand is now: {gameState.get_hand(loser.id)[0]}, Good Luck.")
		await ctx.send(f"{loser.display_name} is now down to one card.")

@bot.command(help="Displays token balances of given player, otherwise displays everyone's if none is given")
async def bank(ctx, player:discord.Member = None):
	global gameState

	if gameState is None:
		return await ctx.send("No game is currently running.")
	
	if player is None:
		lines = []
		for player_id, data in gameState.players.items():
			player = await ctx.guild.fetch_member(player_id)
			coins = data['coins']
			lines.append(f"{player.display_name:<12} : {coins}")
		result = "\n".join(lines)
		formatted = f"```\nToken Balances:\n{result}\n```"
	else:
		player = await ctx.guild.fetch_member(player.id)
		coins = gameState.players[player.id]["coins"]
		result = f"{player.display_name} : {coins}"
		formatted = f"```\nToken Balances:\n{result}\n```"
	await ctx.send(formatted)


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

@bot.event
async def on_message(message):    
    if message.author == bot.user:
        return
    
    if message.content.lower() == "nice":
        await message.channel.send("nice")
    
    await bot.process_commands(message)

@bot.command(help="see how big you are!")      
async def penis(ctx):
	shaft = ""
	len = random.randint(1, 100)
	for x in range(len):
		shaft += "="
	await ctx.channel.send(ctx.author.mention + " your cock is  8" + shaft + "D long")


@bot.command(help="CAMILLLLLLELEEEEE") 
async def champion(ctx):
	with open("/Users/Sajid/Desktop/ServerToSubreddit/champlist.txt") as f:
		champ_list = f.read().split(",")
		champ = champ_list[random.randint(0, len(champ_list) - 1)]
		# await ctx.channel.send(f"{ctx.author.mention} {champ}")

	image_path = "/Users/Sajid/Desktop/ServerToSubreddit/champions"

	with open(os.path.join(image_path, f"{champ}.png"), "rb") as f:
		await ctx.send(file=discord.File(f, filename=f"{champ}.png"))



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
import discord
import numpy
import os
import random
import asyncio
import time
from dotenv import load_dotenv
from discord.ext import commands
from PIL import Image
from datetime import datetime
from app import add_message
import json



load_dotenv()
token = 'NzcwOTU3MDU2NjE4MTM1NTUz.GhEOVg.Po-iJ21WZ9ZUqt6F3C6GfP7ZnoQV7y2n1Qu53U'

intents = discord.Intents.all() 
client = discord.Client(intents=intents)

# Set up the intents for your bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True


# Create bot instance and set command prefix
bot = commands.Bot(command_prefix="!", intents=intents)

@client.event
async def on_ready():
    print("Bot is connected to Discord")

@bot.command()
async def gay(ctx):
	await ctx.channel.send(ctx.author.mention + " you are " + str(random.randint(0, 100)) + "% gay")

@bot.command()      
async def penis(ctx):
	shaft = ""
	len = random.randint(1, 100)
	for x in range(len):
		shaft += "="
	await ctx.channel.send(ctx.author.mention + " your cock is  8" + shaft + "D long")
	
@bot.command()      
async def pokemon(ctx):
	images_dir = '/Users/Sajid/Desktop/img'
	images = os.listdir(images_dir)
	image_filename = random.choice(images)
	image_path = os.path.join(images_dir, image_filename)
	with open(image_path, 'rb') as f:
	    await ctx.channel.send(ctx.author.mention, file=discord.File(f, "poke.png"))
		
@bot.command(name='get_messages')
async def get_messages(ctx, channel_id: int, start_date: str, end_date: str, author="default"):
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
	
	# send messages to site
    # Load existing messages
	try:
		with open("messages.json", "r") as file:
			cur_messages = json.load(file)
	except FileNotFoundError:
		cur_messages = []
	
 
	for msg in messages:
		cur_messages.append(msg)
 
	with open("messages.json", "w") as file:
		json.dump(messages, file)

@bot.command(name='shutdown')
async def shutdown(ctx):
	await ctx.send("Shutting down...")
	await bot.close()  # Safely closes the bot connection

    
bot.run(token)
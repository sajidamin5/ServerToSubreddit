# ServerToSubreddit
Repository containing all the components necessary to create a subreddit (forum) from a given discord server

# bot.py
Server scraper bot (FOR PRIVATE AND APPROVED USE ONLY) - scrapes message data (given a channel ID, date range, and optionally an author) and writes it to file [\logs]

# app.py
Flask application that hosts messages from messages.json on a dynamic website which updates on each subsequent bot.py !get_messages call
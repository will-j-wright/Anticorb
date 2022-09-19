import discord
import discord.ext.commands
import discord.app_commands as app_commands
from tinydb import TinyDB, where
from emoji import is_emoji
import re

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

client = discord.ext.commands.Bot('/', intents=intents)
top = TinyDB("top.json")

@client.tree.command(description="Display your or another user's karma total")
async def karma(interaction: discord.Interaction, user: discord.Member=None):
    karma = TinyDB("karma.json")
    if user is None:
        user = interaction.user
    search = karma.search(where("user") == user.id)
    if len(search) == 0:
        await interaction.response.send_message(user.display_name + " has 0 karma.\n(0 upvotes, 0 downvotes)")
    else:
        upvotes = search[0]["upvotes"]
        downvotes = search[0]["downvotes"] 
        await interaction.response.send_message(user.display_name + " has " \
            + str(upvotes - downvotes) + " karma.\n(" + str(upvotes) + " upvotes, " \
            + str(downvotes) + " downvotes)")

@client.tree.command(description="Display the most upvoted messages from this server")
async def top(interaction: discord.Interaction):
    await interaction.response.send_message("This command is under construction!")

@client.tree.command(description="Display the global karma leaders")
async def leaderboard(interaction: discord.Interaction):
    await interaction.response.send_message("This command is under construction!")

@client.tree.command(description="Change the upvote emoji for this server")
async def upvote_emoji(interaction: discord.Interaction, emoji: str):
    e = emoji.split(':')
    if len(e) < 3 and not is_emoji(emoji):
        await interaction.response.send_message("You must enter an emoji!", ephemeral=True)
    emojis = TinyDB("emojis.json")
    search = emojis.search(where("server") == interaction.guild_id)
    if is_emoji(emoji):
        await interaction.response.send_message("Upvote emoji changed to " + emoji + "!")
        if len(search) == 0:
            emojis.insert({"server": interaction.guild_id, "upvote": emoji, "downvote": 1010686493674721330})
        else:
            emojis.update({"upvote": emoji}, where("server") == interaction.guild_id)
    else:
        emoji_id = e[2][:-1] 
        e = client.get_emoji(int(emoji_id))
        if e and e.guild_id == interaction.guild_id:
            if len(search) == 0:
                emojis.insert({"server": interaction.guild_id, "upvote": int(emoji_id), "downvote": 1010686493674721330})
            else:
                emojis.update({"upvote": int(emoji_id)}, where("server") == interaction.guild_id)
            await interaction.response.send_message("Upvote emoji changed to " + emoji + "!")
        else:
            await interaction.response.send_message("Please choose a default emoji or an emoji from this server.", ephemeral=True)

@client.tree.command(description="Change the downvote emoji for this server")
async def downvote_emoji(interaction: discord.Interaction, emoji: str):
    e = emoji.split(':')
    if len(e) < 3 and not is_emoji(emoji):
        await interaction.response.send_message("You must enter an emoji!", ephemeral=True)
        return
    emojis = TinyDB("emojis.json")
    search = emojis.search(where("server") == interaction.guild_id)
    if is_emoji(emoji):
        await interaction.response.send_message("Downvote emoji changed to " + emoji + "!")
        if len(search) == 0:
            emojis.insert({"server": interaction.guild_id, "upvote": 1010686477459529778, "downvote": emoji})
        else:
            emojis.update({"downvote": emoji}, where("server") == interaction.guild_id)
    else:
        emoji_id = e[2][:-1] 
        e = client.get_emoji(int(emoji_id))
        if e and e.guild_id == interaction.guild_id:
            if len(search) == 0:
                emojis.insert({"server": interaction.guild_id, "upvote": 1010686477459529778, "downvote": int(emoji_id)})
            else:
                emojis.update({"downvote": int(emoji_id)}, where("server") == interaction.guild_id)
            await interaction.response.send_message("Downvote emoji changed to " + emoji + "!")
        else:
            await interaction.response.send_message("Please choose a default emoji or an emoji from this server.", ephemeral=True)

def get_guild_upvote(guild_id):
    emojis = TinyDB("emojis.json")
    s = emojis.search(where("server") == guild_id)
    if len(s) == 0:
        return 1010686477459529778
    else:
        return s[0]["upvote"]

def get_guild_downvote(guild_id):
    emojis = TinyDB("emojis.json")
    s = emojis.search(where("server") == guild_id)
    if len(s) == 0:
        return 1010686493674721330
    else:
        return s[0]["downvote"]

@client.event
async def on_message(message):
    if len(message.attachments) != 0 or len(message.embeds) != 0 \
            or re.search(r"http.*\/\/.+\..+", message.clean_content):
        upvote = get_guild_upvote(message.guild.id)
        downvote = get_guild_downvote(message.guild.id)
        if is_emoji(upvote):
            await message.add_reaction(upvote)
        else:
            await message.add_reaction(client.get_emoji(get_guild_upvote(message.guild.id)))
        if is_emoji(downvote):
            await message.add_reaction(downvote)
        else:
            await message.add_reaction(client.get_emoji(get_guild_downvote(message.guild.id)))

def adjust_downvote(user_id, amount):
    karma = TinyDB("karma.json")
    s = karma.search(where("user") == user_id)
    if len(s) == 0:
        karma.insert({"user": user_id, "upvotes": 0, "downvotes": 1})
    else:
        karma.update({"downvotes": s[0]["downvotes"] + amount}, where("user") == user_id)

def adjust_upvote(user_id, amount):
    karma = TinyDB("karma.json")
    s = karma.search(where("user") == user_id)
    if len(s) == 0:
        karma.insert({"user": user_id, "upvotes": 1, "downvotes": 0})
    else:
        karma.update({"upvotes": s[0]["upvotes"] + amount}, where("user") == user_id)

@client.event
async def on_raw_reaction_add(payload):
    message = await client.get_channel(payload.channel_id).fetch_message(payload.message_id)
    if(payload.user_id != client.user.id and payload.user_id != message.author.id):
        if is_emoji(payload.emoji.name):
            if(payload.emoji.name == get_guild_upvote(payload.guild_id)):
                adjust_upvote(message.author.id, 1)
            elif(payload.emoji.name == get_guild_downvote(payload.guild_id)):
                adjust_downvote(message.author.id, 1)
        else:
            if(payload.emoji.id == get_guild_upvote(payload.guild_id)):
                adjust_upvote(message.author.id, 1)
            elif(payload.emoji.id == get_guild_downvote(payload.guild_id)):
                adjust_downvote(message.author.id, 1)

@client.event
async def on_raw_reaction_remove(payload):
    message = await client.get_channel(payload.channel_id).fetch_message(payload.message_id)
    if(payload.user_id != client.user.id and payload.user_id != message.author.id):
        if is_emoji(payload.emoji.is_unicode_emoji):
            if(payload.emoji.name == get_guild_upvote(payload.guild_id)):
                adjust_upvote(message.author.id, -1)
            elif(payload.emoji.name == get_guild_downvote(payload.guild_id)):
                adjust_downvote(message.author.id, -1)
        else:
            if(payload.emoji.id == get_guild_upvote(payload.guild_id)):
                adjust_upvote(message.author.id, -1)
            elif(payload.emoji.id == get_guild_downvote(payload.guild_id)):
                adjust_downvote(message.author.id, -1)

@client.event
async def on_ready():
    await client.tree.sync()
with open("token.txt") as f:
    client.run(f.read()) # Token is stored as plaintext in token.txt

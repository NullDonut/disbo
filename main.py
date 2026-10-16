import discord
import random
import os
from dotenv import load_dotenv

from discord import app_commands, channel

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    await tree.sync()
    print(f"We have logged in as {client.user}")

@tree.command(name="ping",description="Check if bot is online")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

## Kick command implementation
#@tree.command(name="kick",description="Kicks a user")
#@app_commands.guild_only()

#@app_commands.describe(member ="Who to kick",reason = "why")
#async def kick(interaction:discord.Interaction,member:discord.Member,reason:str = "No reason"):
#    author = interaction.user
#    if not isinstance(author,discord.Member):
#       return
#    if(member.top_role < author.top_role):
#        await member.kick(reason=reason)
#        await interaction.response.send_message(f"Kicked: {member.mention}")
#   else:
#       await interaction.response.send_message(f"You don't have permission to run this command")

@tree.command(name="roll",description="Roll the dice")
async def roll(interaction: discord.Interaction):
    n = random.randrange(1,7)
    await interaction.response.send_message(f"You rolled a {n}!")

@tree.command(name="purge",description="Delete recent messages")
@app_commands.guild_only()
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.checks.cooldown(1,5.0)
@app_commands.describe(amount = "How many recent messages to bulk delete (1-100)")
@app_commands.checks.bot_has_permissions(manage_messages=True)
async def purge(interaction: discord.Interaction,amount:app_commands.Range[int ,1,100]):
    channel = interaction.channel
    if not isinstance(channel, (discord.TextChannel , discord.Thread , discord.VoiceChannel)):
        await interaction.response.send_message("Can't purge here.",ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"Deleted {len(deleted)} messages.",ephemeral=True)




@tree.error
async def on_app_command_error(interaction :discord.Interaction,error:app_commands.AppCommandError):
    if isinstance(error,app_commands.MissingPermissions):
        msg = "You don't have permission to use this command."
    elif isinstance(error,app_commands.CommandOnCooldown):
        msg = f"Slow down! Try again in {error.retry_after:.1f}s."
    elif isinstance(error,app_commands.NoPrivateMessage):
        msg = "This command only works in the server."
    elif isinstance(error,app_commands.BotMissingPermissions):
        msg = "I'm missing permissions to do that"
    else:
        msg = "Something went wrong."
        print(f"Unhandled error in /{interaction.command.name if interaction.command else '?'} : {error!r}")
    
    if interaction.response.is_done():
        await interaction.followup.send(msg,ephemeral=True)
    else:
        await interaction.response.send_message(msg,ephemeral=True)


load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
print("Bot token used is:",BOT_TOKEN)
if BOT_TOKEN == None:
    print("error occured")
    exit(1)
client.run(BOT_TOKEN)


from warnings import resetwarnings

from aiosqlite.context import Result
import discord
import random
import os
from api import init_db, remove_anime, search_anime, add_anime,get_list
from dotenv import load_dotenv

from discord import app_commands, channel

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

def make_embed(a):
    name = a["title"]["english"] or a["title"]["romaji"]
    desc  = (a["description"] or "No synopsis.").replace("<br>","").replace("<i>","").replace("</i>","")
    if len(desc) > 300:
        desc = desc[:300].rsplit(" ",1)[0] + "..."
    desc  = desc.split("(Source")[0].strip()
    score = f"{a['averageScore']/ 10:.1f}/10" if a["averageScore"] else "N/A"
    embed = discord.Embed(title=name,url=a["siteUrl"],description=desc,color=0x3DB4F2)
    embed.set_thumbnail(url=a["coverImage"]["large"])
    embed.add_field(name="Score",value=score)
    embed.add_field(name="Episodes",value=a["episodes"] or "N/A")
    embed.add_field(name="Status",value=a["status"].replace("_"," ").title()) 
    return embed

class ResultPicker(discord.ui.View):
    def __init__(self,results,author_id):
        super().__init__(timeout=120)
        self.results = results
        self.author_id = author_id
        self.message = None

        options = [
                discord.SelectOption(
                    label=(a["title"]["english"] or a["title"]["romaji"])[:100],
                    value=str(i),
                    )
                for i, a in enumerate(results)
                ]
        select = discord.ui.Select(placeholder="Pick a result",options=options)
        select.callback = self.on_select
        self.add_item(select)
    async def on_select(self,interaction:discord.Interaction):
        i = int(interaction.data["values"][0])
        await interaction.response.edit_message(embed=make_embed(self.results[i]))
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                    "This isn't your search.Run /search yourself.",ephemeral = True
                    )
            return False
        return True
    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        if self.message:
            await self.message.edit(view=self)

@client.event
async def on_ready():
    await init_db()
    await tree.sync()
    print(f"We have logged in as {client.user}")

@tree.command(name="ping",description="Check if bot is online")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

@tree.command(name="roll",description="Roll the dice")
async def roll(interaction: discord.Interaction):
    n = random.randrange(1,7)
    await interaction.response.send_message(f"You rolled a {n}!")


@tree.command(name="search",description="Search anime")
@app_commands.checks.cooldown(1,5.0)
@app_commands.describe(name="Title name")
async def search(interaction:discord.Interaction,name:str="Naruto"):
    await interaction.response.defer()
    results = await search_anime(name)
    if not results:
        await interaction.followup.send("No results found or anime service down")
        return
    view = ResultPicker(results,interaction.user.id)
    view.message = await interaction.followup.send(embed=make_embed(results[0]),view=view)

@tree.command(name="add",description="Add a anime to list")
@app_commands.describe(name="Title name",status="Current status")
@app_commands.choices(status=[
    app_commands.Choice(name="Plan to watch",value="planning"),
    app_commands.Choice(name="Completed",value="completed"),
    app_commands.Choice(name="Watching",value="watching")
    ])
async def add_to_list(interaction:discord.Interaction,name:str,status:app_commands.Choice[str]):
    await interaction.response.defer()
    results = await search_anime(name)
    if not results:
        await interaction.followup.send("No results found.")
        return
    a = results[0]
    title = a["title"]["english"] or a["title"]["romaji"]

    await add_anime(interaction.user.id,a["id"],title,status.value)
    await interaction.followup.send(f"Added **{title}** as *{status.name}*.")


STATUS_LABELS = {"planning":"Plan to watch","watching":"Watching","completed":"Completed"}
@tree.command(name="list",description="Show your anime list")
async def show_list(interaction:discord.Interaction):
    rows = await get_list(interaction.user.id)
    if not rows:
        await interaction.response.send_message("Your list is empty. Use /add to add Something.",ephemeral=True)
        return
    lines = [f"• **{title}** — {STATUS_LABELS.get(status, status)}" for title, status in rows[:20]]
    if len(rows) > 20:
        lines.append(f"...and {len(rows) - 20} more")

    embed = discord.Embed(
        title=f"{interaction.user.display_name}'s list",
        description="\n".join(lines),
        color=0x3DB4F2,
    )
    await interaction.response.send_message(embed=embed)

@tree.command(name="remove",description="Remove an anime from your list")
@app_commands.describe(title="Exact title as shown in /list")
async def remove(interaction:discord.Interaction,title:str):
    count = await remove_anime(interaction.user.id,title)
    if count:
        await interaction.response.send_message(f"Removed **{title}**.")
    else:
        await interaction.response.send_message('That title isn\'t on your list.')

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
if BOT_TOKEN == None:
    print("error occured")
    exit(1)
client.run(BOT_TOKEN)


import discord
import json
from discord.ext import commands

class MyHelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mappings):
        help_msg = ""
        for cmd in mappings[None]:
            help_msg += "\n\n**{0}**".format(cmd.name)
            help_msg += "\nUsage: `{0}`".format("-msb " + cmd.name + " " + cmd.signature)
            help_msg += "\nPurpose: {0}".format(cmd.help)
        embed = discord.Embed(title="Multi-Starboard Help",
            type="rich",
            description=help_msg,
            color=discord.Color.dark_purple())
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, cmd):
        help_msg = "\n\n**{0}**".format(cmd.name)
        help_msg += "\nUsage: `{0}`".format("-msb " + cmd.name + " " + cmd.signature)
        help_msg += "\nPurpose: {0}".format(cmd.help)
        embed = discord.Embed(title="Multi-Starboard Help",
            type="rich",
            description=help_msg,
            color=discord.Color.dark_purple())
        await self.get_destination().send(embed=embed)

bot = commands.Bot(command_prefix="-msb ", help_command = MyHelpCommand())

starboards = {}

async def is_guild_channel(ctx):
    return ctx.guild is not None

async def is_admin(ctx):
    return ctx.author.guild_permissions.administrator

@bot.event
async def on_ready():
    global starboards
    print(f'{bot.user} has connected to Discord!')
    with open("./starboards.json", "r") as f:
        starboards = json.loads(f.read())

@bot.command(brief="Registers a new starboard", 
                help="Registers a new starboard. Messages starred in" + \
                    " channel `<source>` will be recorded in" + \
                    " channel `<target>` when they reach the" + \
                    " star `<threshold>`")
@commands.check(is_guild_channel)
@commands.check(is_admin)
async def add(ctx, target: discord.TextChannel, source: discord.TextChannel, threshold: int=3):
    if str(ctx.guild.id) not in starboards:
        starboards[str(ctx.guild.id)] = {}
    if str(source.id) in starboards[str(ctx.guild.id)]:
        await ctx.send("Channel {0} already has a registed starboard ({1})".format(source.name, starboards[str(ctx.guild.id)][str(source.id)]["target_id"]))
        return

    starboards[str(ctx.guild.id)][str(source.id)] = { "target_id": target.id, "threshold": threshold, "messages": [] }
    with open("./starboards.json", "w") as f:
        f.write(json.dumps(starboards))
    await ctx.send("Registed starboard for channel {0} ({1})".format(source.name,target.name))
@add.error
async def add_error(ctx, error):
    print(error)
    await ctx.send("An error occured... which isn't handled yet.")

@bot.command(brief="Registers multiple new starboards", 
                help="Registers a new starboard. Messages starred in" + \
                    " channels `<sources>` will be recorded in" + \
                    " channel `<target>` when they reach the" + \
                    " star `<threshold>`")
@commands.check(is_guild_channel)
@commands.check(is_admin)
async def addMultiple(ctx, target: discord.TextChannel, threshold: int, *sources: discord.TextChannel):
    for source in sources:
        await add(ctx,target,source,threshold)
@addMultiple.error
async def addMultiple_error(ctx, error):
    print(error)
    await ctx.send("An error occured... which isn't handled yet.")

@bot.command(brief="Registers multiple new starboards", 
                help="Registers a new starboard. Messages starred in" + \
                    " all channels except `<omitSources>` will be recorded in" + \
                    " channel `<target>` when they reach the" + \
                    " star threshold")
@commands.check(is_guild_channel)
@commands.check(is_admin)
async def addExcept(ctx, target: discord.TextChannel, threshold: int, *omitSources: discord.TextChannel):
    for source in ctx.guild.text_channels:
        if source not in omitSources:
            await add(ctx,target,source,threshold)
@addExcept.error
async def addExcept_error(ctx, error):
    print(error)
    await ctx.send("An error occured... which isn't handled yet.")

@bot.command(brief="Unregisters a starboard", 
                help="Unregisters the starboard assigned to channel `<source>`")
@commands.check(is_guild_channel)
@commands.check(is_admin)
async def remove(ctx, source: discord.TextChannel):   
    if str(ctx.guild.id) not in starboards:
        starboards[str(ctx.guild.id)] = {}
    if str(source.id) not in starboards[str(ctx.guild.id)]:
        await ctx.send("Channel {0} has no registered starboard".format(source.name))
        return

    del starboards[str(ctx.guild.id)][str(source.id)]
    with open("./starboards.json", "w") as f:
        f.write(json.dumps(starboards))
    await ctx.send("Starboard for channel {0} unregistered".format(source.name))
@remove.error
async def remove_error(ctx, error):
    print(error)
    await ctx.send("An error occured... which isn't handled yet.")

@bot.command(brief="Configures a starboard threshold",
                help="Sets the star threshold required to record" + \
                    " a message to the starboard assigned to" + \
                    " channel `<source>`")
@commands.check(is_guild_channel)
@commands.check(is_admin)
async def threshold(ctx, source: discord.TextChannel, threshold: int):
    if str(ctx.guild.id) not in starboards:
        starboards[str(ctx.guild.id)] = {}
    if str(source.id) not in starboards[str(ctx.guild.id)]:
        await ctx.send("Channel {0} has no registered starboard".format(source.name))
        return

    starboards[str(ctx.guild.id)][str(source.id)]["threshold"] = threshold
    with open("./starboards.json", "w") as f:
        f.write(json.dumps(starboards))
    await ctx.send("Starboard threshold for channel {0} set to {1}".format(source.name,threshold))
@threshold.error
async def threshold_error(ctx, error):
    print(error)
    await ctx.send("An error occured... which isn't handled yet.")

@bot.command(brief="Stops Multi-Starboard",
                help="Stops Multi-Starboard")
@commands.check(is_guild_channel)
@commands.check(is_admin)
async def stop(ctx):
    await bot.close()
@stop.error
async def stop_error(ctx, error):
    print(error)
    await ctx.send("An error occured... which isn't handled yet.")

@bot.event
async def on_raw_reaction_add(payload):
    if isinstance(bot.get_channel(payload.channel_id), discord.TextChannel):
        if str(payload.guild_id) not in starboards:
            starboards[str(payload.guild_id)] = {}
        if str(payload.channel_id) in starboards[str(payload.guild_id)]:
            if payload.message_id not in starboards[str(payload.guild_id)][str(payload.channel_id)]["messages"]:
                message = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
                stars = 0
                for reaction in message.reactions:
                    if reaction.emoji == '⭐':
                        stars += reaction.count
                if stars >= starboards[str(message.channel.guild.id)][str(payload.channel_id)]["threshold"]:
                    embed = discord.Embed(title="Multi-Starboard",
                        type="rich",
                        description=message.content,
                        color=message.author.color)
                    embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
                    embed.add_field(name="Link", value="[Click to go to message]({0})".format(message.jump_url))
                    embed.set_footer(text="Message ID: {0} ({1})".format(message.id,message.created_at))
                    await bot.get_channel(starboards[str(message.channel.guild.id)][str(payload.channel_id)]["target_id"]).send(embed=embed)
                    starboards[str(message.channel.guild.id)][str(payload.channel_id)]["messages"].append(message.id)
                    with open("./starboards.json", "w") as f:
                        f.write(json.dumps(starboards))


TOKEN = "TOKEN"
bot.run(TOKEN)
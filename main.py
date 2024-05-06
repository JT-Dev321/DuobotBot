import discord
from discord import app_commands, ui
from discord.utils import get
import datetime
from discord.app_commands import Group
from ids import *
from dotenv import load_dotenv
import os
import asyncio
import re
import math
import aiosqlite
import ast

load_dotenv()


defaultticketperm = discord.PermissionOverwrite()
defaultticketperm.send_messages = True
defaultticketperm.create_private_threads = False
defaultticketperm.create_private_threads = False
defaultticketperm.view_channel = True

tickethandlerperm = discord.PermissionOverwrite()
tickethandlerperm.send_messages = True
tickethandlerperm.create_private_threads = True
tickethandlerperm.create_private_threads = True
tickethandlerperm.view_channel = True
tickethandlerperm.manage_messages = True

everyoneticketperm = discord.PermissionOverwrite()
everyoneticketperm.view_channel = False
everyoneticketperm.use_application_commands = False

guild_id = 434449451055185943
guild_id_l = [434449451055185943]

maincolour = 0x38b6ff


def hasRole(member : discord.Member, roleID : int):
    roles = [r.id for r in member.roles]
    for r in roles:
        if r == roleID:
            return True
    return False


class client(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        
        self.synced = False

    async def setup_hook(self) -> None:
        self.add_view(AutoErrorSupportENGView())
        self.add_view(AutoQuestionSupportENGView())
        self.add_view(ticketpromptview())
        self.add_view(ticketclosedview())
        self.add_view(ticketmenuview())

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync(guild = discord.Object(id=guild_id))
            self.synced = True
        print(f"We have logged in as {self.user}.")
        
aclient = client()
tree = app_commands.CommandTree(aclient)

    
class AutoErrorSupportENG(discord.ui.Select):
    def __init__(self):
        options = []
        for key in autoSupportDictionary.keys():
            options.append(discord.SelectOption(label=key))
        super().__init__(placeholder='Select the error you are experiencing', min_values=1, max_values=1, options=options, custom_id="Auto_Support_ENG_ID")
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"{autoSupportDictionary[self.values[0]]}", ephemeral=True)
    
class AutoErrorSupportENGView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(AutoErrorSupportENG())



class AutoQuestionSupportENG(discord.ui.Select):
    def __init__(self):
        options = []
        for key in autoQuestionSupportDictionary.keys():
            options.append(discord.SelectOption(label=key))
        super().__init__(placeholder='Select the question you have', min_values=1, max_values=1, options=options, custom_id="Auto_QuestionSupport_ENG_ID")
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"{autoQuestionSupportDictionary[self.values[0]]}", ephemeral=True)
    
class AutoQuestionSupportENGView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(AutoQuestionSupportENG())


class AutoQandRSupportENG(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(AutoQuestionSupportENG())
        self.add_item(AutoErrorSupportENG())

@tree.command(guild = discord.Object(id=guild_id), name = 'send_autosupp', description='Send the autosupport message')
@app_commands.checks.has_permissions(administrator=True)
async def send_autosupp(interaction: discord.Interaction):
    await interaction.channel.send("**Please use the menus below for automatic support**", view=AutoQandRSupportENG())



ticketgroup = Group(name = 'ticket', description='Manage tickets', guild_ids=guild_id_l)

class ticketpromptview(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
    async def ticketopen(self,interaction:discord.Interaction,button:discord.ui.Button):
        for c in get(interaction.guild.categories, id=ticketcategory).channels:
            if interaction.user.name[:17] in c.name:
                await interaction.response.send_message("You already have a ticket open.", ephemeral=True)
                break
        else:
            category = get(interaction.guild.categories, id=ticketcategory)
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                get(interaction.guild.roles, id=tickethandler) : discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            channel = await category.create_text_channel(
                name = f"ticket-{interaction.user.name[:17]}",
                overwrites = overwrites,
            )
            
            logchannel = get(interaction.guild.channels, id=ticketlogchannelid)
            logembed = discord.Embed(
            title = 'Ticket opened',
            timestamp=datetime.datetime.now(),
            colour=maincolour
            )
            logembed.add_field(name = 'Opener', value = f'**{interaction.user.mention}** ({interaction.user.id})', inline = True)
            logembed.add_field(name = 'Ticket', value = f'**{channel.mention}** ({channel.id})', inline = False)
            await logchannel.send(embed = logembed)
            
            inticketembed = discord.Embed(
                title = "Welcome to your ticket",
                description = f"{interaction.user.mention} Welcome to your ticket - Please describe your issue below.\n\nCopy and pasting error messages & showing screenshots of your chat with the bot is really useful!\n\nPlease also provide your **steam profile link**, as in most cases it is useful to us.",
                timestamp=datetime.datetime.now(),
                colour = maincolour
            )
            await channel.send(embed=inticketembed, content=f"{interaction.user.mention}", view=ticketmenuview())
            await channel.send(embed=discord.Embed(description="**Use the select menus below for automatic solutions to common errors and questions.**", colour=maincolour), view=AutoQandRSupportENG())
            await interaction.response.send_message(f"Success! {channel.mention}", ephemeral=True)
            
    @discord.ui.button(label="⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀Support Ticket⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",style=discord.ButtonStyle.blurple, row=1, custom_id="Ticket_Open_BTN")
    async def ticketopenbutton(self,interaction:discord.Interaction,button:discord.ui.Button):
        await ticketpromptview.ticketopen(self, interaction, button)

class ticketclosedview(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label="Reopen",style=discord.ButtonStyle.blurple, custom_id="Ticket_Reopen_BTN")
    async def ticketreopen(self,interaction:discord.Interaction,button:discord.ui.Button):
        await interaction.channel.edit(category=get(interaction.guild.categories, id=ticketcategory))
        await interaction.message.delete()
        logchannel = get(interaction.guild.channels, id=ticketlogchannelid)
        logembed = discord.Embed(
        title = 'Ticket Reopened',
        timestamp=datetime.datetime.now(),
        colour=maincolour
        )
        logembed.add_field(name = 'Reopener', value = f'**{interaction.user}** ({interaction.user.id})', inline = True)
        logembed.add_field(name = 'Ticket', value = f'**{interaction.channel.mention}** ({interaction.channel.name})', inline = False)
        await logchannel.send(embed = logembed)
        await interaction.response.defer()
        
class ticketmenuview(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    """
    @discord.ui.button(label="Close & Archive",style=discord.ButtonStyle.red)
    async def ticketclosearc(self,interaction:discord.Interaction,button:discord.ui.Button):
        for r in interaction.user.roles:
            if r.id == tickethandler:
                await interaction.response.defer()
                logchannel = get(interaction.guild.channels, id=ticketlogchannelid)
                logembed = discord.Embed(
                title = 'Ticket Closed & Archived',
                timestamp=datetime.datetime.now(),
                colour=redcolour
                )
                logembed.add_field(name = 'Closer', value = f'**{interaction.user}** ({interaction.user.id})', inline = True)
                logembed.add_field(name = 'Ticket', value = f'**{interaction.channel.name}** ({interaction.channel.id})', inline = False)
                await logchannel.send(embed = logembed)
                await interaction.channel.edit(category=get(interaction.guild.categories, id=ticketarchivecategory))
                await interaction.channel.send("Use to reopen", view=ticketclosedview())
                break
    """
    @discord.ui.button(label="Close & Delete",style=discord.ButtonStyle.red, custom_id="Ticket_CloseDel_BTN")
    async def ticketclosedel(self,interaction:discord.Interaction,button:discord.ui.Button):
        for r in interaction.user.roles:
            if r.id == tickethandler:
                await interaction.response.defer()
                logchannel = get(interaction.guild.channels, id=ticketlogchannelid)
                logembed = discord.Embed(
                title = 'Ticket Closed & Deleted',
                timestamp=datetime.datetime.now(),
                colour=redcolour
                )
                logembed.add_field(name = 'Closer', value = f'**{interaction.user}** ({interaction.user.id})', inline = True)
                logembed.add_field(name = 'Ticket', value = f'**{interaction.channel.name}** ({interaction.channel.id})', inline = False)
                await logchannel.send(embed = logembed)
                await interaction.channel.delete()
                break
                
@ticketgroup.command(name = 'send_prompt', description='Send the ticket prompt to this channel')
@app_commands.checks.has_permissions(administrator=True)
async def sendticketprompt(interaction: discord.Interaction):
    
    embed = discord.Embed(
        title = 'Create a Ticket',
        description = 
        f"""
        Please create a ticket with the button below if you have any questions regarding the discord server, or our level up bots on steam.
        
        Please avoid opening tickets for support with external/unrelated sites to Duobot, as we are not sponsored or associated with any of these in any way.
        
        Before creating a ticket, please read <#863918636778651688>, it will answer the vast majority of questions we get asked. It saves everyone's time.
        """,
        colour=0x38b6ff,
    )
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/729112154925432913/1099686907912388678/duobott.png")
    
    await interaction.channel.send(embed=embed, view=ticketpromptview())
    await interaction.response.send_message("Done", ephemeral=True)

@ticketgroup.command(name = 'add', description='Adds a user to a ticket')
@app_commands.checks.has_role(tickethandler)
async def ticketadd(interaction: discord.Interaction, member : discord.Member):
    logchannel = get(interaction.guild.channels, id=ticketlogchannelid)
    if interaction.channel.category_id == ticketcategory:
        await interaction.channel.set_permissions(member, read_messages = True, send_messages = True)
        await interaction.response.send_message("Success!", ephemeral=True)
        logembed = discord.Embed(
        title = 'Ticket Member Added',
        timestamp=datetime.datetime.now(),
        colour=greencolour
        )
        logembed.add_field(name = 'Staff', value = f'**{interaction.user}** ({interaction.user.id})', inline = True)
        logembed.add_field(name = 'Member', value = f'**{member}** ({member.id})', inline = True)
        logembed.add_field(name = 'Ticket', value = f'**{interaction.channel.mention}** (#{interaction.channel.name})', inline = False)
        await logchannel.send(embed = logembed)
    else:
        await interaction.response.send_message("This command may only be used within a ticket!", ephemeral=True)

@ticketgroup.command(name = 'remove', description='Removes a user from a ticket')
@app_commands.checks.has_role(tickethandler)
async def ticketremove(interaction: discord.Interaction, member : discord.Member):
    logchannel = get(interaction.guild.channels, id=ticketlogchannelid)
    if interaction.channel.category_id == ticketcategory:
        await interaction.channel.set_permissions(member, read_messages = False, send_messages = False)
        await interaction.response.send_message("Success!", ephemeral=True)
        logembed = discord.Embed(
        title = 'Ticket Member Removed',
        timestamp=datetime.datetime.now(),
        colour=redcolour
        )
        logembed.add_field(name = 'Staff', value = f'**{interaction.user}** ({interaction.user.id})', inline = True)
        logembed.add_field(name = 'Member', value = f'**{member}** ({member.id})', inline = True)
        logembed.add_field(name = 'Ticket', value = f'**{interaction.channel.mention}** (#{interaction.channel.name})', inline = False)
        await logchannel.send(embed = logembed)
    else:
        await interaction.response.send_message("This command may only be used within a ticket!", ephemeral=True)

tree.add_command(ticketgroup)

@ticketgroup.error
async def onerror(interaction : discord.Interaction, error : app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("You're not a support team member!", ephemeral=True)
    elif isinstance(error, app_commands.MissingRole):
        await interaction.response.send_message("You're not a support team member!", ephemeral=True)



class announce_embed(ui.Modal, title = 'Announcement embed'):

    def __init__(self, mention : bool, server_notice : bool):
            self.mention = mention
            self.server_notice = server_notice
            super().__init__()

    heading = ui.TextInput(label = 'Title', style = discord.TextStyle.short, required = True, placeholder = "", min_length=1, max_length=256)
    body = ui.TextInput(label = 'Main Body', style = discord.TextStyle.paragraph, required = True, placeholder = "", min_length=1, max_length=4000)
    image = ui.TextInput(label = 'Main Image', style = discord.TextStyle.short, required = False, placeholder = "Large image at bottom")
    thumbnail = ui.TextInput(label = 'Thumbnail', style = discord.TextStyle.short, required = False, placeholder = "Small image in TR corner")
    # colour = ui.TextInput(label = 'Colour Hex', style = discord.TextStyle.short, required = True, default="38b6ff")

    async def on_submit(self, interaction: discord.Interaction) -> None:
        
        desc = self.body.value
        
        if self.server_notice:
            embed = discord.Embed(title=self.heading.value, description=desc, url="https://duobot.com/p/deepforce", colour=maincolour, timestamp=datetime.datetime.now())
            embed.set_footer(text = "Visit our website at https://duobot.com", icon_url=interaction.user.avatar.url)
        else:
            embed = discord.Embed(title=self.heading.value, description=desc, colour=maincolour)
            # embed.set_footer(text = "Visit our website at https://duobot.com")
        try:
            embed.set_image(url=self.image.value)
            embed.set_thumbnail(url=self.thumbnail.value)
            if self.mention:
                await interaction.channel.send(content="@everyone", embed=embed)
            else:
                await interaction.channel.send(embed=embed)

        except:
            await interaction.response.send_message("An error has occurred.", ephemeral=True)

@tree.command(guild = discord.Object(id=guild_id), name = 'announce', description='Send an announcement')
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(server_notice="Adds extras to the embed, meant for server wide announcements.")
async def announce(interaction: discord.Interaction, mention_everyone : bool = False, server_notice : bool = False):
    await interaction.response.send_modal(announce_embed(mention_everyone, server_notice))
    





















@aclient.event
async def on_message(message : discord.Message):
    cont = message.content.lower()
    if "discord.gg/" in cont and not hasRole(message.author, staffroleid):
        await message.delete()
    if message.author.id != aclient.user.id and len(message.content) > 1 and not message.author.bot and message.channel.category.id in auto_response_cats:
            
        # autoresponses
        """ 
        if message.channel.category.id == 570721296183197697 or message.channel.category.id == 657238193896423424:
            for error in autoSupportDictionary.keys():
                if error.replace(".", "").lower() in cont:
                    await message.reply(f"{autoSupportDictionary[error]}")
        """

        rep = None
        if cont[0] == '!':
            rep = await message.reply("You should use these commands in DMs with the bot's on steam, not in the discord server.")
        elif ("bot" in cont and "add" in cont and "me" in cont) or ("friend request" in cont):
            rep = await message.reply(f"Please open a {ticketchannelmention} for us to manually add you on one of the bots, within the ticket provide:\n\n**1.** Your profile link\n**2.** The bot's profile link")
        elif "specific" in cont and "set" in cont:
            rep = await message.reply(f"We cannot sell you specific sets from our bots.")
        elif "tradable" in cont or "tradeable" in cont:
            rep = await message.reply(
            f"""
            Keys may not be tradeable for these reasons:

            CS:GO:
            - They were purchased in-game (Never expires)
            - They were bought from the steam marketplace (7 day wait)
            - They were recently traded (7 day wait)

            TF2:
            - They were bought from the steam marketplace (7 day wait)

            Therefore, in order to minimise wait times. Buy TF2 keys from an external marketplace (which trades them to you). Such as:
            **- https://marketplace.tf/items/tf2/5021;6**
            **- https://cs.deals/market/tf2/Tool/?name=mann%20co.%20supply%20crate%20key&sort=price**
            """)
        elif "an error occurred" in cont:
            rep = await message.reply(
            f"""
            EN: This is a Steam related issue, and there is nothing we can do in order to attempt to solve this issue. We encourage you to stop trying to use the bot for 15-20 minutes and try again after that.

            PT: 
            Este é um problema relacionado ao Steam e não há nada que possamos fazer para tentar resolvê-lo. Recomendamos que você pare de tentar usar o bot por 15 a 20 minutos e tente novamente depois disso.
            """)
        elif "there was an error loading your profile as it is private" in cont:
            rep = await message.reply(
            f"""
            This is a case of the steam servers being slow to communicate with the bot, meaning it cannot operate. Please try again in around 10 minutes. - We cannot fix this.
            """)
        elif "crypto" in cont or "paypal" in cont or "bitcoin" in cont or "ethereum" in cont:
            rep = await message.reply(
            f"""
            In order to pay via cash, rather than using keys, you must use [**our website**](https://duobot.com/p/deepforce) & deposit into your balance via your desired payment method. 
            """)
            
        
        
        # first time function
        if message.channel.category.id == 570721296183197697 and not hasRole(message.author, staffroleid):
            with open('supids.txt', 'r+') as f:
                filecontent = f.read()
                found = False
                splitlist = filecontent.split(',')
                for authorid in splitlist:
                    if authorid == str(message.author.id):
                        found = True
                if not found:
                    f.write(f"{message.author.id},")
                    await message.reply(f"""## Looks like it's your first time here {message.author.mention}, welcome!
                                        
                                        Be sure to check out {faqchannelmention} and {autosupchannelmention} for immediate support.
                                        Please feel free to open a ticket in {ticketchannelmention} with any further questions you have!""",
                                        delete_after=120)

def insert_returns(body):
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])

    if isinstance(body[-1], ast.If):
        insert_returns(body[-1].body)
        insert_returns(body[-1].orelse)

    if isinstance(body[-1], ast.With):
        insert_returns(body[-1].body)

@tree.command(guild = discord.Object(id=guild_id), name="eval", description="Eval something")
async def eval_py(interaction : discord.Interaction, cmd : str, ephemeral : bool = True):
    if interaction.user.id == 378963670589505557:
        fn_name = "_eval_expr"

        # wrap in async def body
        body = f"async def {fn_name}():\n\t{cmd}"

        parsed = ast.parse(body)
        body = parsed.body[0].body

        insert_returns(body)

        env = {
            'bot': aclient,
            'discord': discord,
            'interaction': interaction,
            '__import__': __import__
        }
        exec(compile(parsed, filename="<ast>", mode="exec"), env)

        result = (await eval(f"{fn_name}()", env))
        if len(result) == 0:
            result = "No return value"
        await interaction.response.send_message(result, ephemeral=True)
    else:
        await interaction.response.send_message("YOU ARENT ME!!!", ephemeral=ephemeral)
  
@tree.error
async def on_app_command_error(interaction : discord.Interaction, error : app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingRole) or isinstance(error, app_commands.MissingAnyRole):
        await interaction.response.send_message("You're missing a role!", ephemeral=True)
    elif isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(f"You're on cooldown for another `{int(error.retry_after)}` seconds!", ephemeral=True)
    elif isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("You're missing a permission!", ephemeral=True)
    else:
        await interaction.response.send_message(f"```{str(error)}```", ephemeral=True)





aclient.run(f"{os.getenv('token')}")
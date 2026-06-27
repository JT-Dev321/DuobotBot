from __future__ import annotations

import ast
import datetime
import os
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

import aiohttp
import aiosqlite
import discord
from discord import app_commands, ui
from discord.app_commands import Group
from discord.ext import commands, tasks
from discord.utils import get
from dotenv import load_dotenv

from auto_responses import find_auto_response
from ids import *

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "db" / "db.sqlite"

load_dotenv(BASE_DIR / ".env")


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

STEAM_LEVEL_OAUTH_URL = f"https://discord.com/api/oauth2/authorize?client_id={os.getenv('DISCORD_CLIENT_ID')}&redirect_uri=" + "https://jt-dev.xyz/callback" + "&response_type=code&scope=identify%20connections"

maincolour = 0x38b6ff

STEAM_STATUS_REFRESH_SECONDS = 60
STEAM_API_BATCH_SIZE = 100


def split_steam_identifiers(raw_ids: str) -> list[str]:
    identifiers = [identifier.strip("<>") for identifier in re.split(r"[\s,;]+", raw_ids.strip()) if identifier]

    if not identifiers:
        raise ValueError("Please provide at least one SteamID64, Steam profile URL, or vanity name.")

    return identifiers


def steam_identifier_to_id_or_vanity(identifier: str) -> tuple[str, str]:
    normalized = identifier.strip().strip("/")

    if normalized.isdigit() and 15 <= len(normalized) <= 20:
        return "steamid", normalized

    url_candidate = normalized
    if normalized.lower().startswith("steamcommunity.com/"):
        url_candidate = f"https://{normalized}"

    parsed_url = urlparse(url_candidate)
    if parsed_url.netloc.lower().endswith("steamcommunity.com"):
        path_parts = [unquote(part) for part in parsed_url.path.split("/") if part]

        if len(path_parts) >= 2 and path_parts[0].lower() == "profiles":
            steam_id = path_parts[1]
            if steam_id.isdigit() and 15 <= len(steam_id) <= 20:
                return "steamid", steam_id

            raise ValueError(f"`{identifier}` does not contain a valid SteamID64.")

        if len(path_parts) >= 2 and path_parts[0].lower() == "id":
            return "vanity", path_parts[1]

        raise ValueError(f"`{identifier}` is not a supported Steam profile URL.")

    if re.fullmatch(r"[A-Za-z0-9_-]{2,64}", normalized):
        return "vanity", normalized

    raise ValueError(f"`{identifier}` is not a valid SteamID64, Steam profile URL, or vanity name.")


async def resolve_steam_ids(raw_ids: str) -> list[str]:
    api_key = os.getenv("STEAM_API_KEY")
    if not api_key:
        raise RuntimeError("Missing `STEAM_API_KEY` environment variable.")

    steam_ids = []
    seen = set()
    vanity_names = []

    for identifier in split_steam_identifiers(raw_ids):
        identifier_type, value = steam_identifier_to_id_or_vanity(identifier)

        if identifier_type == "steamid":
            if value not in seen:
                steam_ids.append(value)
                seen.add(value)
        else:
            vanity_names.append(value)

    if vanity_names:
        timeout = aiohttp.ClientTimeout(total=15)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            for vanity_name in vanity_names:
                params = {
                    "key": api_key,
                    "vanityurl": vanity_name,
                }

                async with session.get("https://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/", params=params) as response:
                    response.raise_for_status()
                    data = await response.json()

                vanity_response = data.get("response", {})
                if vanity_response.get("success") != 1:
                    raise ValueError(f"Could not resolve Steam vanity name `{vanity_name}`.")

                steam_id = vanity_response.get("steamid")
                if steam_id and steam_id not in seen:
                    steam_ids.append(steam_id)
                    seen.add(steam_id)

    if not steam_ids:
        raise ValueError("No Steam accounts could be resolved from that input.")

    return steam_ids


def chunk_list(items: list[str], size: int):
    for index in range(0, len(items), size):
        yield items[index:index + size]


def format_steam_display_name(name: str) -> str:
    if name.startswith("! "):
        name = name[2:]

    if name.endswith(" Level Up"):
        name = name[:-len(" Level Up")]

    return name.strip()


async def fetch_steam_players(steam_ids: list[str]) -> dict[str, dict]:
    api_key = os.getenv("STEAM_API_KEY")
    if not api_key:
        raise RuntimeError("Missing `STEAM_API_KEY` environment variable.")

    players = {}
    timeout = aiohttp.ClientTimeout(total=15)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        for batch in chunk_list(steam_ids, STEAM_API_BATCH_SIZE):
            params = {
                "key": api_key,
                "steamids": ",".join(batch),
            }

            async with session.get("https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/", params=params) as response:
                response.raise_for_status()
                data = await response.json()

            for player in data.get("response", {}).get("players", []):
                players[player["steamid"]] = player

    return players


def build_steam_status_embed(steam_ids: list[str], players: dict[str, dict] | None = None, error: str | None = None) -> discord.Embed:
    embed = discord.Embed(
        title="Steam Account Status",
        colour=maincolour,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )

    embed.set_footer(text=f"Refreshes every {STEAM_STATUS_REFRESH_SECONDS} seconds")

    if error:
        embed.description = f"Unable to refresh Steam status.\n\n{error}"
        return embed

    players = players or {}
    counts = {"Online": 0, "Offline": 0, "Unknown": 0}
    status_rows = []

    for steam_id in steam_ids:
        player = players.get(steam_id)

        if player:
            if player.get("personastate", 0) == 0:
                state_name = "Offline"
                marker = "🔴"
            else:
                state_name = "Online"
                marker = "🟢"

            name = format_steam_display_name(player.get("personaname", steam_id))
            name = discord.utils.escape_markdown(name)
            profile_url = player.get("profileurl", f"https://steamcommunity.com/profiles/{steam_id}")
            line = f"{marker} [{name}]({profile_url}) `{steam_id}`"
        else:
            state_name = "Unknown"
            line = f"`UNK` `{steam_id}` - Unknown"

        counts[state_name] = counts.get(state_name, 0) + 1
        status_rows.append((state_name == "Offline", state_name == "Unknown", line))

    embed.description = (
        f"Tracking `{len(steam_ids)}` Steam account{'s' if len(steam_ids) != 1 else ''}.\n"
        f"Online: `{counts.get('Online', 0)}` | Offline: `{counts.get('Offline', 0)}`"
    )

    current_field = []
    current_length = 0
    shown_lines = 0

    for _, _, line in sorted(status_rows):
        if len(line) > 900:
            line = line[:897] + "..."

        if current_field and current_length + len(line) + 1 > 950:
            embed.add_field(name="Accounts", value="\n".join(current_field), inline=False)
            current_field = []
            current_length = 0

        if len(embed.fields) >= 24:
            break

        current_field.append(line)
        current_length += len(line) + 1
        shown_lines += 1

    if current_field and len(embed.fields) < 25:
        embed.add_field(name="Accounts", value="\n".join(current_field), inline=False)

    hidden_count = len(status_rows) - shown_lines
    if hidden_count > 0 and len(embed.fields) < 25:
        embed.add_field(name="More", value=f"`{hidden_count}` more account statuses are tracked but not shown in this embed.", inline=False)

    return embed

class LevelRoles:
    roles = {}
    
    @classmethod
    def get_highest_role(cls, level : int):
        for key in sorted(cls.roles.keys(), reverse=True):
            if level >= key:
                return cls.roles[key]

def hasRole(member : discord.Member, roleID : int):
    roles = [r.id for r in member.roles]
    for r in roles:
        if r == roleID:
            return True
    return False

class bot(commands.Bot):
    def __init__(self):
        super().__init__(intents=discord.Intents.all(), help_command=None, command_prefix="!!")
        self.synced = False
        self.steam_status_messages = {}

    async def setup_hook(self) -> None:
        self.add_view(AutoErrorSupportENGView())
        self.add_view(AutoQuestionSupportENGView())
        self.add_view(ticketpromptview())
        self.add_view(ticketclosedview())
        self.add_view(ticketmenuview())

        if not self.distribute_steam_level_role.is_running():
            self.distribute_steam_level_role.start()

        if not self.update_steam_status_embeds.is_running():
            self.update_steam_status_embeds.start()

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync(guild = discord.Object(id=guild_id))
            self.synced = True
            
        for role in self.get_guild(guild_id).roles:
            if role.name.startswith("Level"):
                LevelRoles.roles[int(role.name.split(" ")[1])] = role.id
        
        print(f"We have logged in as {self.user}.")
    
    @tasks.loop(seconds=15)
    async def distribute_steam_level_role(self):
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT discord_id, steam_level FROM users") as cursor:
                async for row in cursor:
                    discord_id, steam_level = row
                    guild = await self.fetch_guild(guild_id)
                    member = await guild.fetch_member(int(discord_id))
                    if member:
                        role = get(guild.roles, id=LevelRoles.get_highest_role(steam_level))
                        if role and not hasRole(member, role):
                            await member.add_roles(role)

    @tasks.loop(seconds=STEAM_STATUS_REFRESH_SECONDS)
    async def update_steam_status_embeds(self):
        if not self.steam_status_messages:
            return

        tracked_messages = list(self.steam_status_messages.items())

        for message_id, status_message in tracked_messages:
            channel = self.get_channel(status_message["channel_id"])

            if not channel:
                try:
                    channel = await self.fetch_channel(status_message["channel_id"])
                except discord.DiscordException:
                    self.steam_status_messages.pop(message_id, None)
                    continue

            message = None
            try:
                message = await channel.fetch_message(message_id)
                steam_ids = status_message["steam_ids"]
                players = await fetch_steam_players(steam_ids)
                embed = build_steam_status_embed(steam_ids, players)
                await message.edit(embed=embed)
            except discord.NotFound:
                self.steam_status_messages.pop(message_id, None)
            except Exception as error:
                if not message:
                    continue

                embed = build_steam_status_embed(status_message["steam_ids"], error=str(error))
                try:
                    await message.edit(embed=embed)
                except Exception:
                    pass

    @update_steam_status_embeds.before_loop
    async def before_update_steam_status_embeds(self):
        await self.wait_until_ready()
        
myBot = bot()
tree = myBot.tree


class LinkSteamView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Link your steam account", style=discord.ButtonStyle.link, url=STEAM_LEVEL_OAUTH_URL))

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

@tree.command(guild = discord.Object(id=guild_id), name = 'website', description='Get a link to our website')
@app_commands.checks.has_permissions(administrator=True)
async def get_website(interaction: discord.Interaction, ephemeral : bool = False):
    await interaction.response.send_message("[Click here to visit our website](https://duobot.com/p/deepforce)", ephemeral=ephemeral)


@tree.command(guild = discord.Object(id=guild_id), name = 'link_steam', description='Link your steam account')
@app_commands.checks.has_permissions(administrator=True)
async def link_steam(interaction: discord.Interaction):
    await interaction.response.send_message(f"Please follow the link below to link your steam account and get your role!\n## {STEAM_LEVEL_OAUTH_URL}", view=LinkSteamView(), ephemeral=True)


@tree.command(guild=discord.Object(id=guild_id), name='steam_status', description='Send a live Steam account status embed')
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(steam_ids="SteamID64s, Steam profile URLs, or vanity names separated by commas, spaces, or new lines.")
async def steam_status(interaction: discord.Interaction, steam_ids: str):
    await interaction.response.defer(ephemeral=True)

    try:
        parsed_ids = await resolve_steam_ids(steam_ids)
    except (ValueError, RuntimeError, aiohttp.ClientError) as error:
        await interaction.followup.send(str(error), ephemeral=True)
        return

    try:
        players = await fetch_steam_players(parsed_ids)
        embed = build_steam_status_embed(parsed_ids, players)
    except Exception as error:
        embed = build_steam_status_embed(parsed_ids, error=str(error))

    message = await interaction.channel.send(embed=embed)
    myBot.steam_status_messages[message.id] = {
        "channel_id": interaction.channel.id,
        "steam_ids": parsed_ids,
    }

    await interaction.followup.send(f"Created live Steam status embed `{message.id}`.", ephemeral=True)


@tree.command(guild=discord.Object(id=guild_id), name='steam_status_update', description='Update the SteamID list for a live Steam status embed')
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    message_id="The message ID of the live Steam status embed.",
    steam_ids="Replacement SteamID64s, Steam profile URLs, or vanity names separated by commas, spaces, or new lines.",
)
async def steam_status_update(interaction: discord.Interaction, message_id: str, steam_ids: str):
    await interaction.response.defer(ephemeral=True)

    try:
        parsed_message_id = int(message_id)
    except ValueError as error:
        await interaction.followup.send("Please provide a valid Discord message ID.", ephemeral=True)
        return

    try:
        parsed_ids = await resolve_steam_ids(steam_ids)
    except ValueError as error:
        await interaction.followup.send(str(error), ephemeral=True)
        return
    except (RuntimeError, aiohttp.ClientError) as error:
        await interaction.followup.send(str(error), ephemeral=True)
        return

    try:
        message = await interaction.channel.fetch_message(parsed_message_id)
    except discord.NotFound:
        await interaction.followup.send("I could not find that message in this channel.", ephemeral=True)
        return

    myBot.steam_status_messages[parsed_message_id] = {
        "channel_id": interaction.channel.id,
        "steam_ids": parsed_ids,
    }

    try:
        players = await fetch_steam_players(parsed_ids)
        embed = build_steam_status_embed(parsed_ids, players)
    except Exception as error:
        embed = build_steam_status_embed(parsed_ids, error=str(error))

    try:
        await message.edit(embed=embed)
    except discord.Forbidden:
        myBot.steam_status_messages.pop(parsed_message_id, None)
        await interaction.followup.send("I do not have permission to edit that message.", ephemeral=True)
        return
    except discord.HTTPException as error:
        myBot.steam_status_messages.pop(parsed_message_id, None)
        await interaction.followup.send(f"Discord rejected the embed update: `{error}`", ephemeral=True)
        return

    await interaction.followup.send(f"Updated live Steam status embed `{parsed_message_id}`.", ephemeral=True)


@tree.command(guild=discord.Object(id=guild_id), name='steam_status_stop', description='Stop refreshing a live Steam status embed')
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(message_id="The message ID of the live Steam status embed.")
async def steam_status_stop(interaction: discord.Interaction, message_id: str):
    try:
        parsed_message_id = int(message_id)
    except ValueError:
        await interaction.response.send_message("Please provide a valid Discord message ID.", ephemeral=True)
        return

    removed = myBot.steam_status_messages.pop(parsed_message_id, None)

    if removed:
        await interaction.response.send_message(f"Stopped refreshing Steam status embed `{parsed_message_id}`.", ephemeral=True)
    else:
        await interaction.response.send_message("That message is not currently being refreshed by this bot process.", ephemeral=True)


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

    def __init__(self, mention : bool, hyperlink_title : bool):
            self.mention = mention
            self.hyperlink_title = hyperlink_title
            super().__init__()

    heading = ui.TextInput(label = 'Title', style = discord.TextStyle.short, required = True, placeholder = "", min_length=1, max_length=256)
    body = ui.TextInput(label = 'Main Body', style = discord.TextStyle.paragraph, required = True, placeholder = "", min_length=1, max_length=4000)
    footer = ui.TextInput(label = 'Footer', style = discord.TextStyle.short, required = False, default="Visit our website at duobot.com", min_length=0, max_length=256)
    image = ui.TextInput(label = 'Main Image', style = discord.TextStyle.short, required = False, placeholder = "Large image at bottom")
    thumbnail = ui.TextInput(label = 'Thumbnail', style = discord.TextStyle.short, required = False, placeholder = "Small image in TR corner")
    # colour = ui.TextInput(label = 'Colour Hex', style = discord.TextStyle.short, required = True, default="38b6ff")

    async def on_submit(self, interaction: discord.Interaction) -> None:
        
        desc = self.body.value
        
        if self.hyperlink_title:
            embed = discord.Embed(title=self.heading.value, description=desc, url="https://duobot.com/p/deepforce", colour=maincolour)
            embed.set_footer(text = self.footer.value)
        else:
            embed = discord.Embed(title=self.heading.value, description=desc, colour=maincolour)
            embed.set_footer(text = self.footer.value)
            
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
@app_commands.describe(hyperlink_title="Adds extras to the embed, meant for server wide announcements.")
async def announce(interaction: discord.Interaction, mention_everyone : bool = False, hyperlink_title : bool = False):
    await interaction.response.send_modal(announce_embed(mention_everyone, hyperlink_title))
    

_auto_reply_cooldowns: dict[int, datetime.datetime] = {}
AUTO_REPLY_COOLDOWN_SECONDS = 60


@myBot.event
async def on_message(message: discord.Message):
    cont = message.content.lower()

    if "discord.gg/" in cont and not hasRole(message.author, staffroleid):
        await message.delete()

    if (
        message.author.id != myBot.user.id
        and len(message.content) > 1
        and not message.author.bot
        and message.channel.category is not None
        and message.channel.category.id in auto_response_cats
        and not hasRole(message.author, staffroleid)
    ):
        last_reply = _auto_reply_cooldowns.get(message.author.id)
        on_cooldown = (
            last_reply is not None
            and (datetime.datetime.now() - last_reply).total_seconds() < AUTO_REPLY_COOLDOWN_SECONDS
        )

        if not on_cooldown:
            match = find_auto_response(cont)
            if match:
                _auto_reply_cooldowns[message.author.id] = datetime.datetime.now()
                await message.reply(match["response"])

@myBot.event
async def on_guild_role_update(guild : discord.Guild, before : discord.Role, after : discord.Role):
    if after.name.startswith("Level"):
        LevelRoles.roles.clear()
        for role in guild.roles:
            if role.name.startswith("Level"):
                LevelRoles.roles[int(role.name.split(" ")[1])] = role.id

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
            'bot': myBot,
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





myBot.run(f"{os.getenv('token')}")

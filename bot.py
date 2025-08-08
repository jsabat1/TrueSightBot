import json
import os

import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
RIOT_API_KEY = os.getenv("RIOT_API_KEY")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "registered_accounts.json"


def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")


@bot.command(name="register")
async def register_account(ctx, *, summoner_name: str):
    data = load_data()
    guild_id = str(ctx.guild.id)
    user_id = str(ctx.author.id)

    if guild_id not in data:
        data[guild_id] = {}

    for user_accounts in data[guild_id].values():
        if summoner_name in user_accounts:
            await ctx.send(
                f"The account `{summoner_name}` is already registered by someone else."
            )
            return

    if user_id not in data[guild_id]:
        data[guild_id][user_id] = []

    data[guild_id][user_id].append(summoner_name)
    save_data(data)

    await ctx.send(
        f"Account `{summoner_name}` added for user {ctx.author.display_name} on this server."
    )


@bot.command(name="list")
async def list_accounts(ctx):
    data = load_data()
    guild_id = str(ctx.guild.id)

    if guild_id not in data or not data[guild_id]:
        await ctx.send("No registered accounts on this server.")
        return

    accounts = data[guild_id]
    message_lines = []
    for user_id, summoner_names in accounts.items():
        member = ctx.guild.get_member(int(user_id))
        username = member.display_name if member else f"User ID {user_id}"
        names = ", ".join(summoner_names)
        message_lines.append(f"**{username}**: {names}")

    message = "\n".join(message_lines)
    await ctx.send(f"Registered summoner names on this server:\n{message}")


@bot.command(name="remove")
async def remove_account(ctx, *, summoner_name: str):
    data = load_data()
    guild_id = str(ctx.guild.id)
    user_id = str(ctx.author.id)

    if guild_id not in data or user_id not in data[guild_id]:
        await ctx.send("You don't have any registered accounts.")
        return

    if summoner_name not in data[guild_id][user_id]:
        await ctx.send(
            f"The account `{summoner_name}` is not registered under your user."
        )
        return

    data[guild_id][user_id].remove(summoner_name)

    if not data[guild_id][user_id]:
        del data[guild_id][user_id]

    if not data[guild_id]:
        del data[guild_id]

    save_data(data)
    await ctx.send(f"Removed account `{summoner_name}` from your registrations.")


@bot.command(name="update")
async def update_account(ctx, old_summoner_name: str, *, new_summoner_name: str):
    data = load_data()
    guild_id = str(ctx.guild.id)
    user_id = str(ctx.author.id)

    if guild_id not in data or user_id not in data[guild_id]:
        await ctx.send("You have no accounts to update.")
        return

    if old_summoner_name not in data[guild_id][user_id]:
        await ctx.send(
            f"No registered account found with the name `{old_summoner_name}`."
        )
        return

    for user_accounts in data[guild_id].values():
        if new_summoner_name in user_accounts:
            await ctx.send(
                f"The new account name `{new_summoner_name}` is already taken."
            )
            return

    idx = data[guild_id][user_id].index(old_summoner_name)
    data[guild_id][user_id][idx] = new_summoner_name
    save_data(data)
    await ctx.send(
        f"Updated account from `{old_summoner_name}` to `{new_summoner_name}`."
    )


async def get_account_info(game_name: str, tag_line: str):
    url = f"https://api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"[DEBUG] Account info for {game_name}#{tag_line}: {data}")
                return data
            else:
                print(f"[ERROR] get_account_info failed with status {resp.status}")
                return None


async def get_summoner_by_puuid(puuid: str):
    url = f"https://eun1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"[DEBUG] Summoner info for PUUID {puuid}: {data}")
                return data
            else:
                print(f"[ERROR] get_summoner_by_puuid failed: {resp.status}")
                return None


@bot.command(name="info")
async def summoner_info(ctx):
    data = load_data()
    guild_id = str(ctx.guild.id)
    user_id = str(ctx.author.id)

    if guild_id not in data or user_id not in data[guild_id]:
        await ctx.send("You have no registered accounts.")
        return

    accounts = data[guild_id][user_id]
    messages = []

    for summoner_name in accounts:
        if "#" not in summoner_name:
            messages.append(
                f"Invalid Riot ID format: `{summoner_name}` (expected format: GameName#TagLine)"
            )
            continue
        game_name, tag_line = summoner_name.split("#", 1)
        account_info = await get_account_info(game_name, tag_line)
        if not account_info:
            messages.append(f"No summoner ID found for: `{summoner_name}`.")
            continue
        puuid = account_info.get("puuid")
        if not puuid:
            messages.append(f"No PUUID found for: `{summoner_name}`.")
            continue
        summoner_data = await get_summoner_by_puuid(puuid)
        if not summoner_data:
            messages.append(f"No summoner data found for: `{summoner_name}`.")
            continue
        encrypted_id = summoner_data.get("id")
        if not encrypted_id:
            messages.append(f"No summoner ID found for: `{summoner_name}`.")
            continue
        messages.append(
            f"Encrypted Summoner ID for `{summoner_name}` on EUNE: `{encrypted_id}`"
        )

    await ctx.send("\n".join(messages))


bot.run(TOKEN)

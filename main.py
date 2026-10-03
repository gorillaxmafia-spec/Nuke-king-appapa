import discord
from discord.ext import commands
import asyncio

# ---------- CONFIG ----------
USE_TRIGGER = True                  # If True, requires TRIGGER to run. If False, runs automatically
TRIGGER = ""                        # Command to trigger listing servers (if USE_TRIGGER=True)
DM = True                            # If True, DM the user; if False, reply in channel
PREVIEW = True                       # Print servers info in console
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"   # Your bot token
SHOW_MEMBER_COUNT = True             # Include number of members in each server
SELECT_USER_IDS = []                 # List of user IDs to DM. If empty, uses message author or channel

# Bot info toggles
SHOW_ROLES = False
SHOW_PERMISSIONS = False
SHOW_VISIBLE_CHANNELS = False
SHOW_SERVER_INFO = False
SHOW_SERVER_INVITE = False
MAX_MESSAGE_LENGTH = 1900

# New: Optional server invite search keywords (comma-separated string, e.g., "test,fun")
INVITE_KEYWORDS = ""  
# ----------------------------

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


async def get_bot_info(guild: discord.Guild):
    bot_member = guild.get_member(bot.user.id)
    if not bot_member:
        return "Bot is not a member of this guild."

    info = []

    if SHOW_SERVER_INFO:
        owner = guild.owner.name if guild.owner else "Unknown"
        info.append(f"Server Name: {guild.name}")
        info.append(f"Server ID: {guild.id}")
        info.append(f"Server Owner: {owner}")
        info.append(f"Boost Level: {guild.premium_tier}")
        info.append(f"Members: {guild.member_count}")
        info.append(f"Categories: {len(guild.categories)}")
        info.append(f"Text Channels: {len(guild.text_channels)}")
        info.append(f"Voice Channels: {len(guild.voice_channels)}")
        info.append(f"Roles: {len(guild.roles)}")
        info.append(f"Bot Join Date: {bot_member.joined_at}")

    if SHOW_ROLES:
        roles = [r.name for r in bot_member.roles if r.name != "@everyone"]
        info.append(f"Bot Roles: {', '.join(roles) if roles else 'No roles'}")

    if SHOW_PERMISSIONS:
        permissions = [perm[0] for perm in bot_member.guild_permissions if perm[1]]
        info.append(f"Bot Permissions: {', '.join(permissions) if permissions else 'No permissions'}")
        info.append(f"Bot Admin: {'Yes' if bot_member.guild_permissions.administrator else 'No'}")

    if SHOW_VISIBLE_CHANNELS:
        visible_channels = []
        total_channels = len(guild.channels)
        for ch in guild.channels:
            if ch.permissions_for(bot_member).read_messages:
                visible_channels.append(f"**{ch.name}**")
            else:
                visible_channels.append(ch.name)
        visible_count = sum(1 for ch in guild.channels if ch.permissions_for(bot_member).read_messages)
        info.append(f"Channels: {', '.join(visible_channels)} ({visible_count}/{total_channels} visible)")

    if SHOW_SERVER_INVITE:
        invite_link = "No permission to create invite"
        for ch in guild.text_channels:
            # Skip servers that don't match keywords if specified
            if INVITE_KEYWORDS:
                keywords = [k.strip().lower() for k in INVITE_KEYWORDS.split(",")]
                if not any(kw in guild.name.lower() for kw in keywords):
                    continue

            if ch.permissions_for(bot_member).create_instant_invite:
                try:
                    invite = await ch.create_invite(max_age=3600, max_uses=1, unique=True)
                    invite_link = invite.url
                    break
                except Exception:
                    continue
        info.append(f"Server Invite Link: {invite_link}")

    return "\n".join(info)


async def send_server_list(target_user=None, channel=None):
    for guild in bot.guilds:
        full_message = await get_bot_info(guild)

        if PREVIEW:
            print(f"Server info for {guild.name}:\n{full_message}\n{'-'*50}")

        # Split message if too long
        chunks = [full_message[i:i+MAX_MESSAGE_LENGTH] for i in range(0, len(full_message), MAX_MESSAGE_LENGTH)]
        for chunk in chunks:
            try:
                if DM and target_user:
                    await target_user.send(chunk)
                elif channel:
                    await channel.send(chunk)
            except discord.Forbidden:
                print(f"Cannot send message to {target_user or channel}. Permission denied.")
            except discord.HTTPException as e:
                print(f"Failed to send message: {e}")
            await asyncio.sleep(1)  # small delay to avoid rate limits


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    # Automatic run if not using trigger
    if not USE_TRIGGER and SELECT_USER_IDS:
        for user_id in SELECT_USER_IDS:
            user = bot.get_user(user_id)
            if user:
                await send_server_list(target_user=user)


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if USE_TRIGGER and message.content.lower().strip() == TRIGGER.lower():
        # Determine target users
        targets = []
        if SELECT_USER_IDS:
            for user_id in SELECT_USER_IDS:
                user = bot.get_user(user_id)
                if user:
                    targets.append(user)
        else:
            targets.append(message.author)

        for target in targets:
            await send_server_list(target_user=target, channel=message.channel if not DM else None)


bot.run(BOT_TOKEN)

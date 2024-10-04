__author__ = "Felix, Olly, Zoose, Smiley, and Chairwoman Abbi"

import asyncio
import json
import os
import re
from datetime import datetime, timedelta
from difflib import SequenceMatcher

import aiohttp
import core
import discord
from discord.ext import commands, tasks

BYPASS_LIST = [

    323473569008975872, 381170131721781248, 346382745817055242,
    601095665061199882, 211368856839520257,
    767824073186869279, 697444795785674783,
    249568050951487499
]

UNITS = {
    's': 'seconds',
    'm': 'minutes',
    'h': 'hours',
    'd': 'days',
    'w': 'weeks'
}

BLOXLINK_API_KEY = os.environ.get('BLOXLINK_KEY')
SERVER_ID = "788228600079843338"
HEADERS = {'Authorization': BLOXLINK_API_KEY}

EMOJI_VALUES = {True: "✅", False: "⛔"}

def unix_converter(seconds: int) -> int:
    now = datetime.now()
    then = now + timedelta(seconds=seconds)

    return int(then.timestamp())

def convert_to_seconds(text: str) -> int:
    return int(
        timedelta(
            **{
                UNITS.get(m.group('unit').lower(), 'seconds'):
                float(m.group('val'))
                for m in re.finditer(r'(?P<val>\d+(\.\d+)?)(?P<unit>[smhdw]?)',
                                     text.replace(' ', ''),
                                     flags=re.I)
            }).total_seconds())


channel_options = {
    'Main': '1221162035513917480',
    'Prize Claims': '1213885924581048380',
    'Affiliate': '1196076391242944693',
    'Development': '1196076499137200149',
    'Appeals': '1196076578938036255',
    'Moderator Reports': '1246863733355970612'
}

# channel_options = {
#     'Mu': '1249441110829301911',
#     'Phi': '1249441160762494997',
#     'Lambaaaa': '1249441131524132894',
# }


class DropDownChannels(discord.ui.Select):

    def __init__(self):
        options = [
            discord.SelectOption(label=i[0]) for i in channel_options.items()
        ]

        super().__init__(
            placeholder="Select a channel...",
            options=options,
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction):
        category_id = channel_options[self.values[0]]
        category = interaction.guild.get_channel(int(category_id))

        await interaction.channel.edit(category=category, sync_permissions=True)

        await interaction.response.edit_message(
            content="Moved channel successfully", view=None)


class DropDownView(discord.ui.View):

    def __init__(self, dropdown):
        super().__init__()
        self.add_item(dropdown)


THUMBNAIL = "https://cdn.discordapp.com/attachments/1208495821868245012/1223677006894596146/Propaganda3.png?ex=661ab905&is=66084405&hm=f66c28d77dc53ad7c31228a367ae9cfea2f6489514b59c63497f186863d0b691&"
FOOTER = "Sponsored by the Guides Committee"

gamepasses = {
    "Rainbow Name": 20855496,
    "Ground Crew": 20976711,
    "Cabin Crew": 20976738,
    "Captain": 20976820,
    "Senior Staff": 20976845,
    "Staff Manager": 20976883,
    "Airport Manager": 20976943,
    "Board of Directors": 21002253,
    "Co Owner": 21002275,
    "First Class": 21006608,
    "Segway Board": 22042259
}


def find_most_similar(name):
    return max(gamepasses.items(),
               key=lambda x: SequenceMatcher(None, x[0], name).ratio())


def EmbedMaker(ctx, **kwargs):
    e = discord.Embed(**kwargs, colour=0x8e00ff)
    e.set_image(url=THUMBNAIL)
    e.set_footer(text=FOOTER if ctx.author.id != 767824073186869279 else
                 "Thank you Chairwoman Abbi for gracing us with your presence")
    return e
#

MODS = {
    "amod": "1165941639144034334",
}

ROLE_HIERARCHY = [
    '1248340570275971125', '1248340594686820403', '1248340609727729795',
    '1248340626773381240', '1248340641117765683'
]

# ROLE_HIERARCHY = ['1223001309217820702','1223001302397616188','1223001292100866289', '1223001271867412670']


def is_bypass():

    async def predicate(ctx):
        return (ctx.author.id in BYPASS_LIST) or (set(
            [i.id
             for i in ctx.author.roles]).intersection(set(ROLE_HIERARCHY[:2])))

    return commands.check(predicate)


async def check(ctx):
    if ctx.author.id in BYPASS_LIST or set(
        [i.id
         for i in ctx.author.roles]).intersection(set(ROLE_HIERARCHY[:2])):
        return True

    coll = ctx.bot.plugin_db.get_partition(ctx.bot.get_cog('GuidesCommittee'))
    thread = await coll.find_one({'thread_id': str(ctx.thread.channel.id)})
    if thread is not None:
        can_r = ctx.author.bot or str(ctx.author.id) == thread['claimer']
        if not can_r:
            if "⛔" not in [i.emoji for i in ctx.message.reactions
                           ]:  # Weird bug where check runs twice?????
                await ctx.message.add_reaction("⛔")
        return can_r
    # cba to do this properly so repetition it is
    if "⛔" not in [i.emoji for i in ctx.message.reactions
                   ]:  # Weird bug where check runs twice?????
        await ctx.message.add_reaction("⛔")
    return False


class GuidesCommittee(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.api.get_plugin_partition(self)
        self.bot.get_command("reply").add_check(check)
        self.bot.get_command("areply").add_check(check)
        self.bot.get_command("fareply").add_check(check)
        self.bot.get_command("freply").add_check(check)
        self.bot.get_command("close").add_check(check)

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            embed = EmbedMaker(ctx, title="On Cooldown", description=f"You can use this command again <t:{unix_converter(error.retry_after)}:R>")

            await ctx.send(embed=embed)
        else:
            super().cog_command_error(ctx, error)

    @core.checks.thread_only()
    @core.checks.has_permissions(core.models.PermissionLevel.SUPPORTER)
    @commands.cooldown(1, 900, commands.BucketType.user)
    @commands.command()
    async def claim(self, ctx):
        thread = await self.db.find_one(
            {'thread_id': str(ctx.thread.channel.id)})
        if thread is None:
            await self.db.insert_one({
                'thread_id': str(ctx.thread.channel.id),
                'claimer': str(ctx.author.id),
                'original_name': ctx.channel.name
            })

            try:
                nickname = ctx.author.display_name

                await ctx.channel.edit(name=f"claimed-{nickname}")

                embed = EmbedMaker(
                    ctx,
                    title="Claimed",
                    description=f"Claimed by {ctx.author.mention}")

                m = await ctx.message.channel.send(embed=embed)

                # await asyncio.sleep(10)  # Should be longer ngl

                # await m.delete()

            except discord.errors.Forbidden:
                await ctx.message.reply("I don't have permission to do that")
        else:
            claimer = thread['claimer']
            embed = EmbedMaker(
                ctx,
                title="Already Claimed",
                description=
                f"Already claimed by {(f'<@{claimer}>') if claimer != ctx.author.id else 'you dumbass'}"
            )
            await ctx.send(embed=embed)

    @core.checks.thread_only()
    @core.checks.has_permissions(core.models.PermissionLevel.SUPPORTER)
    @commands.command()
    async def unclaim(self, ctx):
        thread = await self.db.find_one(
            {'thread_id': str(ctx.thread.channel.id)})
        if thread is None:
            embed = EmbedMaker(
                ctx,
                title="Already Unclaimed",
                description="This thread is not claimed, you can claim it!")
            return await ctx.message.reply(embed=embed)

        if thread['claimer'] == str(ctx.author.id):
            await self.db.find_one_and_delete(
                {'thread_id': str(ctx.thread.channel.id)})

            try:
                embed = EmbedMaker(
                    ctx,
                    title="Unclaimed",
                    description=f"Unclaimed by {ctx.author.mention}")

                await ctx.channel.edit(name=thread['original_name'])

                await ctx.message.reply(embed=embed)

            except discord.errors.Forbidden:
                await ctx.message.reply("I don't have permission to do that")
        else:
            e = discord.Embed(
                title="Unclaim Denied",
                description=
                f"You're not the claimer of this thread, don't anger chairwoman abbi"
            )
            await ctx.message.reply(embed=e)

    @core.checks.thread_only()
    @core.checks.has_permissions(core.models.PermissionLevel.SUPPORTER)
    @commands.command()
    async def takeover(self, ctx):
        roles_taker = [str(i.id) for i in ctx.author.roles]
        roles_to_take_t = []
        for i in range(len(roles_taker)):
            if roles_taker[i] not in ROLE_HIERARCHY:
                roles_to_take_t.append(roles_taker[i])

        for i in roles_to_take_t:
            roles_taker.remove(i)

        # await asyncio.sleep(1)
        thread = await self.db.find_one(
            {'thread_id': str(ctx.thread.channel.id)})

        if thread['claimer'] == str(ctx.author.id):
            embed = EmbedMaker(
                ctx,
                title="Takeover Denied",
                description=
                f"You have literally claimed this yourself tf u doing")
            await ctx.channel.send(embed=embed)
            return

        mem = await ctx.guild.fetch_member(thread['claimer'])

        roles_claimed = [str(i.id) for i in mem.roles]

        roles_to_take_c = []
        for i in range(len(roles_claimed)):
            if roles_claimed[i] not in ROLE_HIERARCHY:
                roles_to_take_c.append(roles_claimed[i])

        for i in roles_to_take_c:
            roles_claimed.remove(i)

        if (ROLE_HIERARCHY.index(roles_taker[-1])
                < ROLE_HIERARCHY.index(roles_claimed[-1])):
            await self.db.find_one_and_update(
                {'thread_id': str(ctx.thread.channel.id)},
                {'$set': {
                    'claimer': str(ctx.author.id)
                }})
            e = EmbedMaker(
                ctx,
                title="Takeover",
                description=f"Takeover by <@{ctx.author.id}> succesful")
            await ctx.channel.send(embed=e)
            try:
                nickname = ctx.author.display_name

                await ctx.channel.edit(name=f"claimed-{nickname}")

                m = await ctx.message.channel.send(
                    f"Successfully renamed, this rename was sponsored by the **guides committee**"
                )

                await asyncio.sleep(10)

                await m.delete()

            except discord.errors.Forbidden:
                await ctx.message.reply("I don't have permission to do that")
        else:
            e = EmbedMaker(
                ctx,
                title="Takeover Denied",
                description=
                f"Takeover denied by as claimer is your superior, this angers chairwoman abbi"
            )
            await ctx.reply(embed=e)

    async def cog_unload(self):
        cmds = [
            self.bot.get_command("reply"),
            self.bot.get_command("freply"),
            self.bot.get_command("areply"),
            self.bot.get_command("fareply"),
            self.bot.get_command("close")
        ]
        for i in cmds:
            if check in i.checks:
                print(f'REMOVING CHECK IN {i.name}')  # Some logging yh
                i.remove_check(check)

    @commands.command()
    @core.checks.has_permissions(core.models.PermissionLevel.SUPPORTER)
    async def owns(self, ctx, username, *, gamepass):
        conversion_gamepass = False
        conversion_username = False

        try:
            gamepass = int(gamepass)
        except Exception:
            gamepass = gamepass
            conversion_gamepass = True

        try:
            username_id = int(username)
        except Exception:
            username = username
            conversion_username = True

        async with aiohttp.ClientSession() as session:
            if conversion_username is True:
                async with session.post(
                        'https://users.roblox.com/v1/usernames/users',
                        data=json.dumps({
                            'usernames': [username],
                            'excludeBannedUsers': True
                        })) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if bool(data['data']) is False:
                            e = EmbedMaker(
                                ctx,
                                title="Wrong username",
                                description=
                                "Error Checking, please try putting the right username"
                            )
                            return await ctx.message.reply(embed=e)
                        if data['data'][0]['requestedUsername'] != username:
                            e = EmbedMaker(
                                ctx,
                                title="Failed checks",
                                description=
                                "Error Checking, please try manually checking")
                            return await ctx.message.reply(embed=e)
                        print(data['data'][0]['id'])
                        username_id = data['data'][0]['id']

            if conversion_gamepass is True:
                gamepass_id = find_most_similar(gamepass)
                print(gamepass_id)

            async with session.get(
                    f'https://inventory.roblox.com/v1/users/{username_id}/items/1/{gamepass_id[1]}/is-owned'
            ) as resp:
                if resp.status == 200:
                    owns = await resp.json()

                    if not isinstance(owns, bool):
                        if "errors" in owns.keys():
                            owns = False

                    if owns is True:
                        e = EmbedMaker(
                            ctx,
                            title="Gamepass Owned",
                            description=
                            f"{gamepass_id[0]} owned by {username}, [link](https://inventory.roblox.com/v1/users/{username_id}/items/1/{gamepass_id[1]}/is-owned)"
                        )
                        return await ctx.message.reply(embed=e)
                    else:
                        e = EmbedMaker(
                            ctx,
                            title="Gamepass NOT Owned ⛔⛔⛔",
                            description=
                            f"{gamepass_id[0]} not owned by {username}, [link](https://inventory.roblox.com/v1/users/{username_id}/items/1/{gamepass_id[1]}/is-owned)"
                        )
                        return await ctx.message.reply(embed=e)

    @commands.command()
    @core.checks.thread_only()
    async def getinfo(self, ctx):
        await ctx.message.add_reaction("<a:loading_f:1249799401958936576>")
        m_id = ctx.thread.recipient.id
        gamepasses_owned = {key: "IDK" for key in gamepasses.keys()}

        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"https://api.blox.link/v4/public/guilds/788228600079843338/discord-to-roblox/{m_id}",
                    headers=HEADERS) as res:
                roblox_data = await res.json()
                roblox_id = roblox_data["robloxID"]

                avatar_url_get = roblox_data["resolved"]["roblox"]["avatar"][
                    "bustThumbnail"]
            async with session.get(avatar_url_get) as res:
                avatar_url_ = await res.json()
                avatar_url = avatar_url_["data"][0]["imageUrl"]

            for i in gamepasses_owned.keys():
                id = gamepasses[i]

                async with session.get(
                        f'https://inventory.roblox.com/v1/users/{roblox_id}/items/1/{id}/is-owned'
                ) as res:
                    owns = await res.json()

                    if not isinstance(owns, bool):
                        if "errors" in owns.keys():
                            owns = False

                    if owns is True:
                        gamepasses_owned[i] = True
                    else:
                        gamepasses_owned[i] = False

        roblox_name = roblox_data["resolved"]["roblox"]["name"]
        roblox_display_name = roblox_data["resolved"]["roblox"]["displayName"]
        roblox_profile_link = roblox_data["resolved"]["roblox"]["profileLink"]
        roblox_rank_name = roblox_data["resolved"]["roblox"]["groupsv2"][
            "8619634"]["role"]["name"]
        roblox_rank_id = roblox_data["resolved"]["roblox"]["groupsv2"][
            "8619634"]["role"]["rank"]

        embed = discord.Embed(title=roblox_name,
                              url=roblox_profile_link,
                              colour=0x8e00ff,
                              timestamp=datetime.now())

        msg = ""
        for i, j in gamepasses_owned.items():
            msg += f"**{i}**: {EMOJI_VALUES[j]}\n"

        msg.strip()

        embed.add_field(
            name="Discord",
            value=
            f"**ID**: {m_id}\n**Username**: {ctx.thread.recipient.name}\n**Display Name**: {ctx.thread.recipient.display_name}",
            inline=False)
        embed.add_field(
            name="ROBLOX",
            value=
            f"**ID**: {roblox_id}\n**Username**: {roblox_name}\n**Display Name**: {roblox_display_name}\n**Rank In Group**: {roblox_rank_name} ({roblox_rank_id})",
            inline=False)

        embed.add_field(name="Gamepasses", value=msg, inline=False)

        embed.set_thumbnail(url=avatar_url)

        embed.set_footer(
            text=FOOTER,
            icon_url=
            "https://cdn.discordapp.com/attachments/1208495821868245012/1249743898075463863/Logo.png?ex=66686a34&is=666718b4&hm=f13b57e1fbd96c14bc8123d0a57980791e0f0db267da9ae39911fe50211406e1&"
        )

        await ctx.message.clear_reactions()

        await ctx.reply(embed=embed)

    @commands.command()
    @core.checks.thread_only()
    @core.checks.has_permissions(core.models.PermissionLevel.SUPPORTER)
    async def mover(self, ctx):
        view = DropDownView(DropDownChannels())

        await ctx.send("Choose a channel to move this ticket to", view=view)

    @commands.command()
    @core.checks.thread_only()
    @core.checks.has_permissions(core.models.PermissionLevel.SUPPORTER)
    async def remindme(self, ctx, time: str, *, message: str):
        embed = EmbedMaker(
            ctx,
            title="Remind Me",
            description=f"I will remind you about {message} in {time}")
        m = await ctx.message.reply(embed=embed)

        await asyncio.sleep(convert_to_seconds(time))

        await ctx.channel.send(f"<@{ctx.author.id}>, {message}")

        try:
            await m.delete()
            await ctx.author.send(message)
        except discord.errors.Forbidden:
            pass

    @commands.command()
    @core.checks.thread_only()
    @is_bypass()
    async def transfer(self, ctx, user: discord.Member):
        thread = await self.db.find_one(
            {'thread_id': str(ctx.thread.channel.id)})

        if thread['claimer'] == str(user.id):
            embed = EmbedMaker(
                ctx,
                title="Takeover Denied",
                description=f"<@{user.id}> is the thread claimer")
            await ctx.channel.send(embed=embed)
            return

        await self.db.find_one_and_update(
            {'thread_id': str(ctx.thread.channel.id)},
            {'$set': {
                'claimer': str(user.id)
            }})
        e = EmbedMaker(ctx,
                       title="Takeover",
                       description=f"Takeover by <@{user.id}> succesful")
        await ctx.channel.send(embed=e)
        try:
            nickname = user.display_name

            await ctx.channel.edit(name=f"claimed-{nickname}")

            m = await ctx.message.channel.send(
                f"Successfully renamed, this rename was sponsored by the **guides committee**"
            )

            await asyncio.sleep(10)

            await m.delete()
        except Exception as e:
            return await ctx.message.channel.send(str(e))

    @commands.command()
    @core.checks.has_permissions(core.models.PermissionLevel.SUPPORTER)
    async def credits(self, ctx):
        embed = EmbedMaker(
            ctx,
            title="Credits",
            description=
            "- Designer: **Chairwoman Abbi**\n- Developer: **Chairwoman Abbi**\n- "
            "Supporter: **Chairwoman Abbi**\n- Animator: **Chairwoman Abbi**\n- "
            "Moderator: **Chairwoman Abbi**\n- Admin: **Chairwoman Abbi**\n- "
            "Technical Support: **Chairwoman Abbi**\n- Server Infrastructure "
            "Lead: **Chairwoman Abbi**\n- UI Designer: **Chairwoman Abbi**\n- UI "
            "Developer: **Chairwoman Abbi**\n- UI Supporter: **Chairwoman "
            "Abbi**\n- UI Animator: **Chairwoman Abbi**\n- UI Moderator: "
            "**Chairwoman Abbi**\n- Chief Engineer: **Chairwoman "
            "Abbi**\n- Engineer: **Chairwoman Abbi**\n- Chief Technology Officer:"
            "**Chairwoman Abbi**\n- Technology Officer: **Chairwoman "
            "Abbi**\n- Senior Leader for Community Engagement and Conflict "
            "Resolution Oversight: **Chairwoman Abbi**\n- Chief Community "
            "Manager: **Chairwoman Abbi**\n- Lead Content Moderator and "
            "Compliance Officer for Online Community Standards "
            "Enforcement: **Chairwoman Abbi**\n- Chief Governance and Policy "
            "Enforcement Administrator for Moderation Team Operations: "
            "**Chairwoman Abbi**\n- Chief Community Manager: **Chairwoman "
            "Abbi**\n- Principal Regulatory Compliance Manager for User "
            "Conduct and Content Moderation: **Chairwoman Abbi**")
        await ctx.message.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(GuidesCommittee(bot))

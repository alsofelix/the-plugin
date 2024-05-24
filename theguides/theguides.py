__author__ = "Felix, Olly, Zoose, Smiley, and Chairwoman Abbi"

import asyncio
import json
from difflib import SequenceMatcher

import aiohttp
import core
import discord
from discord.ext import commands

# THUMBNAIL = "https://cdn.discordapp.com/attachments/1208495821868245012/1223677006894596146/Propaganda3.png?ex=661ab905&is=66084405&hm=f66c28d77dc53ad7c31228a367ae9cfea2f6489514b59c63497f186863d0b691&"
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


def EmbedMaker(**kwargs):
    e = discord.Embed(**kwargs, colour=0x8e00ff)
    #    e.set_image(url=THUMBNAIL)
    e.set_footer(text=FOOTER)
    return e


MODS = {
    "amod": "1165941639144034334",
}

ROLE_HIERARCHY = [
    '1165941140499988560', '1165946875728371772', '1165941871332302900',
    '1165941639144034334', '1165941640196784158', '1165941641106952222'
]


# ROLE_HIERARCHY = ['1223001309217820702','1223001302397616188','1223001292100866289', '1223001271867412670']
async def check(ctx):
    #has = await ctx.author.get_role('1165946875728371772')
    #if has is not None:
    #    return True

    coll = ctx.bot.plugin_db.get_partition(ctx.bot.get_cog('GuidesCommittee'))
    thread = await coll.find_one({'thread_id': str(ctx.thread.channel.id)})
    if thread is not None:
        can_r = ctx.author.bot or str(ctx.author.id) == thread['claimer']
        if not can_r:
            if "⛔" not in [i.emoji for i in ctx.message.reactions
                           ]:  # Weird bug where check runs twice?????
                await ctx.message.add_reaction("⛔")
        return can_r
    return True


class GuidesCommittee(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.api.get_plugin_partition(self)
        self.bot.get_command("reply").add_check(check)
        self.bot.get_command("areply").add_check(check)
        self.bot.get_command("fareply").add_check(check)
        self.bot.get_command("freply").add_check(check)
        self.bot.get_command("close").add_check(check)

    @core.checks.thread_only()
    @core.checks.has_permissions(core.models.PermissionLevel.SUPPORTER)
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
                title="Already Unclaimed",
                description="This thread is not claimed, you can claim it!")
            return await ctx.message.reply(embed=embed)

        if thread['claimer'] == str(ctx.author.id):
            await self.db.find_one_and_delete(
                {'thread_id': str(ctx.thread.channel.id)})

            try:
                embed = EmbedMaker(
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
        for i, item in enumerate(roles_taker):
            if item not in ROLE_HIERARCHY:
                roles_to_take_t.append(item)

        for i in roles_to_take_t:
            roles_taker.remove(i)

        # await asyncio.sleep(1)
        thread = await self.db.find_one(
            {'thread_id': str(ctx.thread.channel.id)})

        if thread['claimer'] == str(ctx.author.id):
            embed = EmbedMaker(
                title="Takeover Denied",
                description=
                f"You have literally claimed this yourself tf u doing")
            await ctx.channel.send(embed=embed)
            return

        mem = await ctx.guild.fetch_member(thread['claimer'])

        roles_claimed = [str(i.id) for i in mem.roles]

        roles_to_take_c = []
        for i, item in enumerate(roles_claimed):
            if item not in ROLE_HIERARCHY:
                roles_to_take_c.append(item)

        for i in roles_to_take_c:
            roles_claimed.remove(i)

        if (ROLE_HIERARCHY.index(roles_taker[len(roles_taker) - 1])
                < ROLE_HIERARCHY.index(roles_claimed[len(roles_claimed) - 1])):
            await self.db.find_one_and_update(
                {'thread_id': str(ctx.thread.channel.id)},
                {'$set': {
                    'claimer': str(ctx.author.id)
                }})
            e = EmbedMaker(
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
                                title="Wrong username",
                                description=
                                "Error Checking, please try putting the right username"
                            )
                            return await ctx.message.reply(embed=e)
                        if data['data'][0]['requestedUsername'] != username:
                            e = EmbedMaker(
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
                            title="Gamepass Owned",
                            description=
                            f"{gamepass_id[0]} owned by {username}, [link](https://inventory.roblox.com/v1/users/{username_id}/items/1/{gamepass_id[1]}/is-owned)"
                        )
                        return await ctx.message.reply(embed=e)
                    else:
                        e = EmbedMaker(
                            title="Gamepass NOT Owned ⛔⛔⛔",
                            description=
                            f"{gamepass_id[0]} not owned by {username}, [link](https://inventory.roblox.com/v1/users/{username_id}/items/1/{gamepass_id[1]}/is-owned)"
                        )
                        return await ctx.message.reply(embed=e)


#    @commands.command()
#    async def credits(self, ctx):
#        print("HI")
#        embed = EmbedMaker(title="Credits", description="- Designer: **Chairwoman Abbi**\n- Developer: **Chairwoman Abbi**\n- "
#                                                        "Supporter: **Chairwoman Abbi**\n- Animator: **Chairwoman Abbi**\n- "
#                                                        "Moderator: **Chairwoman Abbi**\n- Admin: **Chairwoman Abbi**\n- "
#                                                        "Technical Support: **Chairwoman Abbi**\n- Server Infrastructure "
#                                                        "Lead: **Chairwoman Abbi**\n- UI Designer: **Chairwoman Abbi**\n- UI "
#                                                        "Developer: **Chairwoman Abbi**\n- UI Supporter: **Chairwoman "
#                                                        "Abbi**\n- UI Animator: **Chairwoman Abbi**\n- UI Moderator: "
#                                                        "**Chairwoman Abbi**\n- Chief Engineer: **Chairwoman "
#                                                        "Abbi**\n- Engineer: **Chairwoman Abbi**\n- Chief Technology Officer:"
#                                                        "**Chairwoman Abbi**\n- Technology Officer: **Chairwoman "
#                                                        "Abbi**\n- Senior Leader for Community Engagement and Conflict "
#                                                        "Resolution Oversight: **Chairwoman Abbi**\n- Chief Community "
#                                                        "Manager: **Chairwoman Abbi**\n- Lead Content Moderator and "
#                                                        "Compliance Officer for Online Community Standards "
#                                                        "Enforcement: **Chairwoman Abbi**\n- Chief Governance and Policy "
#                                                        "Enforcement Administrator for Moderation Team Operations: "
#                                                        "**Chairwoman Abbi**\n- Chief Community Manager: **Chairwoman "
#                                                        "Abbi**\n- Principal Regulatory Compliance Manager for User "
#                                                        "Conduct and Content Moderation: **Chairwoman Abbi**")
#        await ctx.message.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(GuidesCommittee(bot))

import discord
from redbot.core import commands, Config, checks
from redbot.core.bot import Red
import re
from datetime import datetime
import asyncio

class Partner(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.data = Config.get_conf(self, identifier=3467369396939, force_registration=True)
        default_member = {
            "weekly_points": 0,
            "points": 0
        }
        default_guild = {
            "channel": None
        }
        self.data.register_member(**default_member)
        self.data.register_guild(**default_guild)
        self.loop = bot.loop.create_task(self.weekly_reset())

    def cog_unload(self):
        self.loop.cancel()
       
    def days_before_reset(self):
        now = datetime.utcnow().weekday()
        _next = 6
        _next = str(_next - now)
        return _next

    async def weekly_reset(self):
        while True:
            await asyncio.sleep(5)
            now = datetime.utcnow()
            if now.isoweekday() == 7 and now.hour == 0 and now.minute == 0:
                for guild_id in (data:= await self.data.all_guilds()):
                    guild = self.bot.get_guild(int(guild_id))

                    if not guild:
                        continue
 
                    all_members = await self.data.all_members(guild)

                    if all_members:
                        for member_id in all_members:
                            member = guild.get_member(int(member_id))
                            if not member:
                                continue

                            await self.data.member(member).weekly_points.set(0)
                           
    @commands.guild_only()
    @commands.group()
    async def partner(self, ctx):
        """Partnership System"""
        if ctx.invoked_subcommand is None:
            pass

    @checks.admin()
    @partner.command(name="reset")
    async def _reset(self, ctx):
        """Reset alltime or weekly leaderboard."""
        data = await self.data.all_members(ctx.guild)
        n=0
        if data:
            for member_id in data:
                member = ctx.guild.get_member(int(member_id))
                if not member:
                    continue
                
                await self.data.clear_all_members(ctx.guild)
                n+=1
            return await ctx.send(f"Successfully reset the points for **{n}** members.")
        await ctx.send("There is no data to reset!")

    @checks.admin()
    @partner.command(name="channel")
    async def _channel(self, ctx, channel: discord.TextChannel=None):
        """Specify a channel for partnerships."""
        channel = None if not channel else channel
        if channel:
            await self.data.guild(ctx.guild).channel.set(channel.id)
            await ctx.send(f"The partner channel has been set to {channel.mention}.")
        else:
            await self.data.guild(ctx.guild).channel.set(None)
            await ctx.send(f"Reset the partner channel!")


    @partner.command(name="weekly")    
    async def _weekly(self, ctx):
        """ View weekly leaderboard for partnerships."""
        data = await self.data.all_members(ctx.guild)
        if not data:
            return await ctx.send("There is nothing to see here.")
        sorted_data = sorted(data, key=lambda x: data[x]["weekly_points"], reverse=True)
        author_rank = 0
        message = ""
        n = 1
        for rank in sorted_data:
            member = ctx.guild.get_member(rank)
            if member:
                message += f"{n}. ``{member}`` - **{data[member.id]['weekly_points']}** points\n"
                n+=1 

            if n == 11:
                break
        embed=discord.Embed(title="Weekly Partner Leaderboard", description=message, color=discord.Colour(await ctx.bot._config.color()))
        embed.set_author(name=ctx.guild, icon_url=ctx.guild.icon_url)
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.set_footer(text=f"Next weekly reset in: {self.days_before_reset()} days")
        await ctx.send(embed=embed)

    @partner.command(name="alltime", aliases=["all"])    
    async def _all(self, ctx):
        """ View All time leaderboard for partnerships."""
        data = await self.data.all_members(ctx.guild)
        if not data:
            return await ctx.send("There is nothing to see here.")
        sorted_data = sorted(data, key=lambda x: data[x]["points"], reverse=True)
        author_rank = 0
        message = ""
        n = 1
        for rank in sorted_data:
            member = ctx.guild.get_member(rank)
            if member:
                message += f"{n}. ``{member}`` - **{data[member.id]['points']}** points\n"
                n+=1 

            if n == 11:
                break
        embed=discord.Embed(title="Alltime Partner Leaderboard", description=message, color=discord.Colour(await ctx.bot._config.color()))
        embed.set_author(name=ctx.guild, icon_url=ctx.guild.icon_url)
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.set_footer(text="Top 10 alltime partners")
        await ctx.send(embed=embed)

    @partner.command(name="stats")
    async def _stats(self, ctx, member: discord.Member = None):
        """View a member stats or your owns"""
        if member is None:
            member = ctx.author
        
        if member.bot:
            em = discord.Embed(description="Bots can't be tracked.")
            return await ctx.send(embed=em)

        data = await self.data.all_members(ctx.guild)
        em = discord.Embed(colour=discord.Colour(await ctx.bot._config.color()))
        try:
            em.set_author(name=member.name, icon_url=member.avatar_url)
            em.set_thumbnail(url=member.avatar_url)
            em.set_footer(text=f"Next weekly reset in: {self.days_before_reset()} days")
            em.add_field(name="Weekly :", value=f"{data[member.id]['weekly_points']}")
            em.add_field(name="All-Time :", value=f"{data[member.id]['points']}")
        except KeyError:
            em = discord.Embed(description="No stats available for you or the user provided.")
            return await ctx.send(embed=em)
        return await ctx.send(embed=em)

    @commands.Cog.listener()
    async def on_message(self, message):
        guild = message.guild
        if message.author.bot:
            return 

        if not guild:
            return

        partner_channel = await self.data.guild(guild).channel()
        if not partner_channel:
            return

        if partner_channel != message.channel.id:
            return 
        
        reinvite = r"(?:[\/s \/S]|)*(?:https?:\/\/)?(?:www.)?(?:discord.gg|(?:canary.)?discordapp.com\/invite)\/((?:[a-zA-Z0-9]){2,32})(?:[\/s \/S]|)*"
        if not re.search(reinvite, message.content, re.IGNORECASE):
            return
        
        data = await self.data.member(message.author).weekly_points()
        await self.data.member(message.author).weekly_points.set(data+1)
        data = await self.data.member(message.author).points()
        await self.data.member(message.author).points.set(data+1)

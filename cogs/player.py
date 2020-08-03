import discord
from discord.ext import commands
from utils.util import get_uuid_profileid
from utils.skypy import skypy, exceptions
from utils.skypy.constants import skill_icons
from utils.embed import Embed
from EZPaginator import Paginator
from datetime import datetime



class Player(commands.Cog):
    def __init__(self, bot):
        self.bot : commands.Bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        pass
    
    def format_name(self, name):
        return name + "'s" if name[-1] is not "s" else name


    async def shortcut_error(self, ctx):
        embed = await Embed(self.bot, ctx.author, title="Error", description="You can only use this shortcut if you link a username to your Discord account.").set_requested_by_footer()
        await ctx.send(embed=embed)
        await ctx.invoke(self.bot.get_command("help show_command"), arg=self.skills)

    async def profile_not_found_error(self, ctx : commands.Context, player):
        embed = await Embed(self.bot, ctx.author, title="Error", description="Couldn't find the provided profile in your Skyblock account. Your profiles: " + ", ".join(player.profiles.keys())).set_requested_by_footer()
        await ctx.send(embed=embed)


    async def get_uname(self, ctx, uname):
        if not uname:
            uname, profile = await get_uuid_profileid(self.bot, ctx.author)
            if uname is None:
                return await self.shortcut_error(ctx)
        return uname
        
    async def make_player(self, ctx, uname, profile):
        if uname and uname.lower() == "me":
            uname, rest = await get_uuid_profileid(self.bot, ctx.author)
            
        if not uname and not profile:
            uname, profile = await get_uuid_profileid(self.bot, ctx.author)
            if uname is None:
                await self.shortcut_error(ctx)
                return None
            
        player = await skypy.Player(keys=self.bot.api_keys, uname=uname)
        
        if not profile:
            await player.set_profile_automatically()
        elif profile and profile.capitalize() in player.profiles.keys():
            await player.set_profile(player.profiles[profile.capitalize()])
        else:
            try:
                await player.set_profile(profile)
            except exceptions.DataError:
                await self.profile_not_found_error(ctx, player)
                return None
        return player


    async def get_skills_embed(self, ctx, player):
        player.load_skills_slayers(False)
        
        if not player.enabled_api["skills"]:
            return await Embed(self.bot, ctx.author, title="Error", description="Your skills API is disabled. Please enable it and try again.").set_requested_by_footer()

        name = self.format_name(player.uname)

        embed = Embed(self.bot, ctx.author, title=f"{name} Skills on {player.profile_name}", description=f"Average skill level: {player.skill_average}")
        await embed.set_requested_by_footer()
        for name, level in player.skills.items():
            embed.add_field(name=f"{skill_icons[name]} {name.capitalize()} Level", value=f"**LEVEL {level}**\n{player.skill_xp[name]:,}XP total\n{player.skills_needed_xp[name]:,}XP to next level")
        return embed


    async def get_stats_embed(self, ctx, player : skypy.Player):
        player.load_banking(False)
        player.load_misc(False)
        
        name = self.format_name(player.uname)

        percentages = ["crit_chance", "speed", "crit_damage", "bonus_attack_speed", "sea_creature_chance"]
        icons = {
                'health': "❤️", 'defense': "🛡️", 'effective_health': "💕", 'strength': "⚔️", 
                'speed': "🏃‍♂️", 'crit_chance': "🎲", 'crit_damage': "☠️", 'bonus_attack_speed': "🗯️", 
                'intelligence': "🧠", 'sea_creature_chance': "🎣", 'magic_find': "⭐", 'pet_luck': "🦜"}

        embed = Embed(self.bot, ctx.author, title=f"{name} Stats on {player.profile_name}")
        await embed.set_patron_footer()
        embed.set_thumbnail(url=player.avatar())

        for name, stat in player.stats.items():
            if name == "damage" or name == "damage_increase": continue
            if name in percentages:
                stat = str(stat) + "%"
            else:
                stat = f"{stat:,}"
            embed.add_field(name=icons[name] + name.replace("_", " ").capitalize(), value=stat)

        embed.add_field(name="🌈Fairy souls", value=player.fairy_souls_collected)
        if player.enabled_api["banking"]:
            embed.add_field(name="🏦Bank Balance", value=f"{round(player.bank_balance):,}")
            embed.add_field(name="💰Purse", value=f"{round(player.purse):,}")
        online = await player.is_online()
        embed.add_field(name="🟢Currently online" if online else "🔴Currently online", value="Yes" if online else "No")
        embed.add_field(name="🚪Join date", value=str(player.join_date.strftime("%Y-%m-%d")))
        embed.add_field(name="⏰Last update", value=str(player.last_save.strftime("%Y-%m-%d")))
        
        return embed
        

    
    
    async def get_slayer_embed(self, ctx, player : skypy.Player):
        player.load_skills_slayers(False)
        slayerNames = {"zombie": "Revenent Horror", "spider": "Tarantula Broodfather", "wolf": "Sven Packmaster"}
        embed = await Embed(self.bot, ctx.author, title=f"{self.format_name(player.uname)} slayer stats on {player.profile_name}").set_requested_by_footer()
        for slayer in player.slayers:
            embed.add_field(name=f"{slayerNames[slayer]}\nLEVEL {player.slayers[slayer]}", value=f"{player.slayers_needed[slayer]:,} XP\nto next level")
        for slayer in player.slayers:
            string = ''
            for i, bossLevel in enumerate(player.slayer_boss_kills[slayer]):
                string += f"\n**Tier {i + 1}** Kills: {player.slayer_boss_kills[slayer][bossLevel]}"
            embed.add_field(name="\u200b", value=string)
        embed.add_field(name="Total Slayer XP", value=f"{player.total_slayer_xp:,} XP")
        embed.add_field(name="Total Boss Kills",  value=f"{player.total_boss_kills} kills")
        embed.add_field(name="Total Spend", value=f"{player.slayer_total_spend:,} coins")
        return embed
        if not player.enabled_api["skills"]:
            return await Embed(self.bot, ctx.author, title="Error", description="Your skills API is disabled. Please enable it and try again.").set_requested_by_footer()

    
    
    async def get_profiles_embed(self, ctx, uname):
        player = await skypy.Player(keys=self.bot.api_keys, uname=uname)
        
        name = self.format_name(player.uname)
        
        embed = Embed(self.bot, ctx.author, title=f"{name} profiles")
        await embed.set_requested_by_footer()
        
        for number, profile in enumerate(player.profiles.items()):
            await player.set_profile(profile[1])
            uuids = list(player._api_data["members"].keys())
            unames = []
            for uuid in uuids:
                name, uuid = await skypy.fetch_uuid_uname(uuid)
                unames.append(name)
            embed.add_field(name=f"{number + 1}. {profile[0]}", value="- " + "\n- ".join(unames), inline=False)
            player._profile_set = False
        return embed

    async def get_auctions_embeds(self, ctx, player):
        auctions = await player.auctions()

        embeds = []
        for auction in auctions:
            
            item : skypy.Item = auction[1]
            auction = auction[0]
            
            embed = Embed(self.bot, ctx.author, title=self.format_name(player.uname) + " Auctions", description=f"Item: {auction['item']}")
            await embed.set_made_with_love_footer()
            async def get_uname(uuid):
                uname, uuid = await skypy.fetch_uuid_uname(uuid)
                return uname

            bids = [str(await get_uname(bid["bidder"])) + ", " + "Amount: " + f"{bid['amount']:,}" for bid in auction["bids"]] if auction["bids"] else ["None"]
            bids.reverse()
            bids = '\n'.join(bids[:5])

            started = datetime.utcfromtimestamp(auction["start"] / 1000)
            started = str(started)[:-7] if started.microsecond else started
            ending = datetime.utcfromtimestamp(auction["end"] / 1000)
            ending = str(ending)[:-7] if ending.microsecond else ending

            description = '\n'.join(item.description_clean)


            value = f"**Name:** {item.name}\nAmount: {item.stack_size}\n**Description:** {description}"
            if len(value) > 1000:
                value = f"**Name:** {item.name}\nAmount: {item.stack_size}"

            embed.add_field(name="Starting-Ending", value=f"**Started:** {started}\n**Ending:** {ending}")
            embed.add_field(name="Item", value=value)
            embed.add_field(name="Bids", value=f"**Starting Bid:** {auction['starting_bid']:,}\n**Highest bid:** {auction['highest_bid']:,}\n**Bids:**\n{bids}")

            
            embeds.append(embed)

        return embeds
    
    
    @commands.command(name="skills", description="Shows you Skyblock skill levels and xp.", usage="[username] ([profile])", aliases=["skill", "sk"])
    async def skills(self, ctx, uname=None, profile=None): 
        player = await self.make_player(ctx, uname, profile)
        if not player: return
        async with ctx.typing():
            embed = await self.get_skills_embed(ctx, player)
            await ctx.send(embed=embed)


    @commands.command(name="stats", description="Shows you Skyblock profile stats like health, strength and more.", usage="[username] ([profile])", aliases=["stat"])
    async def stats(self, ctx, uname=None, profile=None):
        player : skypy.Player = await self.make_player(ctx, uname, profile)
        if not player: return
        await player.skylea_stats()
        async with ctx.typing():
            embed = await self.get_stats_embed(ctx, player)
            await ctx.send(embed=embed)
        
    
    @commands.command(name="slayer", description="Shows you Slayer stats.", usage="[username] ([profile])", aliases = ["slay"])
    async def slayer(self, ctx, uname=None, profile=None):
        player = await self.make_player(ctx, uname, profile)
        if not player: return
        async with ctx.typing():
            embed = await self.get_slayer_embed(ctx, player)
            await ctx.send(embed=embed)
         
            
    @commands.command(name="Profiles", description="Shows you all your available profiles on Skyblock.", usage="[Minecraft Username]")
    async def profiles(self, ctx, uname=None):
        uname = await self.get_uname(ctx, uname)
        async with ctx.typing():
            embed = await self.get_profiles_embed(ctx, uname)
            await ctx.send(embed=embed)

    @commands.command(name="auctions", description="Shows you SKyblock auctions and information about them.", usage="[username]", aliases=["ah", "auction"])
    async def auctions(self, ctx, uname=None):
        uname = await self.get_uname(ctx, uname)
        player : skypy.Player = await skypy.Player(keys=self.bot.api_keys, uname=uname)
        await player.set_profile_automatically()
        async with ctx.typing():
            embeds = await self.get_auctions_embeds(ctx, player)
            if not embeds:
                return await ctx.send(f"{player.uname} has no auctions running.")
            msg = await ctx.send(embed=embeds[0])
        if len(embeds) > 1:
            pages = Paginator(self.bot, msg, embeds=embeds, only=ctx.author, use_more=True)
            await pages.start()
        

    

def setup(bot):
    bot.add_cog(Player(bot))
from .advertiser import Advertiser

def setup(bot):
    cog = Advertiser(bot)
    bot.add_cog(cog)

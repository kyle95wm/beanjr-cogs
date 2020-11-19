from .partner import Partner

def setup(bot):
    cog = Partner(bot)
    bot.add_cog(cog)

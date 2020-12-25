import discord
from discord.ext import commands
from dade import DaDe
from vantu import VanTu


class TTBot(commands.Bot):
    async def on_ready(self):
        game = discord.Activity(name="Trí tuệ Discord",type=1)
        await bot.change_presence(status=discord.Status.online, activity=game)
        print('[DEBUG] We have logged in as {0.user}'.format(bot))
        await bot.get_channel(788388679743438868).send("ttbot is online")


if __name__ == "__main__":
    bot = TTBot(command_prefix="tt!", self_bot=False)
    
    bot.add_cog(VanTu(bot))
    bot.add_cog(DaDe(bot))
    
    bot.run("token")


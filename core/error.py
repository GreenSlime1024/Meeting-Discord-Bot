import discord

class error():
    async def error_message(error, interaction):
        embed=discord.Embed(title="Error!", description=f"```{error}```", color=0xff0000)
        await interaction.response.send_message(embed=embed)
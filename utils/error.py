import discord

class error():
    async def error_message(interaction, error, description = None, ephemeral=True):
        embed=discord.Embed(title="Error!", description=f"```{error}```", color=0xff0000)
        embed.add_field(name="description", value=description, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=ephemeral)
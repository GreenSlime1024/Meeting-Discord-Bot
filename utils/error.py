import discord

class error():
    async def error_message(interaction, error, description:str="no info", mode:str="respond",ephemeral:bool=True):
        embed=discord.Embed(title="Error!", description=f"```{error}```", color=0xff0000)
        embed.add_field(name="description", value=description, inline=False)
        if mode == "respond":
            await interaction.response.send_message(embed=embed, ephemeral=ephemeral)
        elif mode == "edit":
            await interaction.response.edit_message(embed=embed)
        elif mode == "follow":
            await interaction.followup.send(embed=embed, ephemeral=ephemeral)
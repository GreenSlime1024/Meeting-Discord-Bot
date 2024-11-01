import discord
from discord.app_commands.errors import BotMissingPermissions

def interaction_check(interaction: discord.Interaction):
    perms = {perm: value for perm, value in discord.Permissions(395405618192) if value}
    permissions = interaction.app_permissions
    missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

    if not missing:
        return True

    raise BotMissingPermissions(missing)
import disnake

# Sophisticated, clean UI design colors
COLOR_SUCCESS = disnake.Color.from_rgb(46, 204, 113) # Clean Green
COLOR_ERROR = disnake.Color.from_rgb(231, 76, 60) # Clean Red
COLOR_INFO = disnake.Color.from_rgb(52, 152, 219) # Clean Blue
COLOR_NEUTRAL = disnake.Color.from_rgb(149, 165, 166)

def success_embed(title: str, description: str) -> disnake.Embed:
    embed = disnake.Embed(
        title=title,
        description=description,
        color=COLOR_SUCCESS
    )
    return embed

def error_embed(title: str, description: str) -> disnake.Embed:
    embed = disnake.Embed(
        title=title,
        description=description,
        color=COLOR_ERROR
    )
    return embed

def info_embed(title: str, description: str) -> disnake.Embed:
    embed = disnake.Embed(
        title=title,
        description=description,
        color=COLOR_INFO
    )
    return embed

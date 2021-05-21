# In this example you will see how embeds works on discord.py.
# This doesn not require any privileged intent.

import discord
from discord.ext import commands

"""Def the bot."""
description = '''An example for how embeds works in discord.py.'''

intents = discord.Intents.default()

bot = commands.Bot(command_prefix='?', description=description, intents=intents)
"""Finished def bot."""

  # Example
  
  # let's start create a basic embed
  embed = discord.Embed(title="the title of the embed", color = "here you can use discorc colors, or HEXA colors.")
                          ^                               ^
                      #embed title                 #embed side color
    
  # now let's add a description (that's like a tiny text after the title)
  embed = discord.Embed(title="the title of the embed", description="place the embed description here", color = "here you can use discorc colors, or HEXA colors.")
                                                             ^
                                                   #that's like a subtitle
      
  # you can add also a thumbnail or image in the embed
  embed = discord.Embed(title="the title of the embed", description="place the embed description here", color = "here you can use discorc colors, or HEXA colors.")
  
  embed.set_thumbnail(url="this can be a web url (which redirect directly to the image), or an internal file, like 'thumbnail.png').")
  embed.set_image(url="same thing as thumbnail).")
  #what's the difference? thumbnail is a tiny image which will be placed on top right in the embed, image is a big image placed after all the text (title, description exc..)
  
  #now let's add a field into the embed
    embed = discord.Embed(title="the title of the embed", description="place the embed description here", color = "here you can use discorc colors, or HEXA colors.")
  
    embed.set_thumbnail(url="this can be a web url (which redirect directly to the image), or an internal file, like 'thumbnail.png').")
    embed.set_image(url="same thing as thumbnail).")
    
    embed.add_field(name="the title of the field goes here", value="the value of the field goes here")
    #how fields works? they works exactly same as title and description, just with different names. Fields are tiny boxes into embed where you can add informations if needed, they can me max 3 x row.
    
    #well, there's also a footer, which is a tiny text after all the stuff in the embed.
    embed = discord.Embed(title="the title of the embed", description="place the embed description here", color = "here you can use discorc colors, or HEXA colors.")
  
    embed.set_thumbnail(url="this can be a web url (which redirect directly to the image), or an internal file, like 'thumbnail.png').")
    embed.set_image(url="same thing as thumbnail).")
    
    embed.add_field(name="the title of the field goes here", value="the value of the field goes here")
    
    embed.set_footer(text="your footer text goes here", icon_url="footer takes also urls to place a tiny image before the footer text.")
    #you can't use hyperlinks in foooter.
    
    #you can also add an author on the embed
    embed = discord.Embed(title="the title of the embed", description="place the embed description here", color = "here you can use discorc colors, or HEXA colors.")
  
    embed.set_thumbnail(url="this can be a web url (which redirect directly to the image), or an internal file, like 'thumbnail.png').")
    embed.set_image(url="same thing as thumbnail).")
    
    embed.add_field(name="the title of the field goes here", value="the value of the field goes here")
    
    embed.set_footer(text="your footer text goes here", icon_url="footer takes also urls to place a tiny image before the footer text.")
    
    embed.set_author(name="the name of the author you want, can be like the {ctx.author.name}", icon_url="the icon which needs to be displayed before the author text")
    
    
    # FINAL RESULT
    @bot.command()
    async def embed(ctx):
      #base embed
      embed = discord.Embed(title="the title of the embed", description="place the embed description here", color = "here you can use discorc colors, or HEXA colors.")
      
      #thumbnail
      embed.set_thumbnail(url="this can be a web url (which redirect directly to the image), or an internal file, like 'thumbnail.png').")
      
      #image
      embed.set_image(url="same thing as thumbnail).")
      
      #fields (yes you can set multiple fields into a single embed)
      embed.add_field(name="the title of the field goes here", value="the value of the field goes here")
      
      #footer
      embed.set_footer(text="your footer text goes here", icon_url="footer takes also urls to place a tiny image before the footer text.")
      
      #author
      embed.set_author(name="the name of the author you want, can be like the {ctx.author.name}", icon_url="the icon which needs to be displayed before the author text")
      
      #how can you send the embed? look here
      await ctx.send(embed=embed) #the second 'embed' is the name of the var where we started creating our embed with 'discord.Embed'.
    
  

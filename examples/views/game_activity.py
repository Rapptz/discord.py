import discord
from discord.ext import commands

# A basic Bot (Nothing Special)
class Bot(commands.Bot):
	def __init__(self):
		super().__init__(command_prefix=commands.when_mentioned_or('$'))

	async def on_ready(self):
		print(f'Logged in as {self.user} (ID: {self.user.id})')
		print('------')

# The only view used
class GameActivity(discord.ui.View):
	def __init__(self, timeout: float):
		super().__init__(timeout=timeout)
		self.activity_id = None
		self.channel_id = None

	# A select with default options to choose from
	@discord.ui.select(
		placeholder="Select Your Activity",
		options = [
				discord.SelectOption(label="Youtube", value="755600276941176913",description="Watch Youtube Together"),
				discord.SelectOption(label="Poker", value="755827207812677713",description="Play Poker Night"),
				discord.SelectOption(label="Chess", value="832012774040141894",description="Play Chess In The Park")
			]
		)
	async def activity(self, select: discord.ui.Select, interaction: discord.Interaction):
		# Storing the choice and activity label and description
		self.activity_id = int(select.values[0])
		self.activity_name = None
		for option in select.options:
			if option.value == str(self.activity_id):
				self.activity_name = option.label
				break

	# A select to change the options (Options to be change depending on guilds)
	@discord.ui.select(
		placeholder="Select Your Channel",
		)
	async def vc(self, select: discord.ui.Select, interaction: discord.Interaction):
		# Storing the choice
		self.channel_id = int(select.values[0])

	# A button to confirm the creation of activity
	@discord.ui.button(style=discord.ButtonStyle.green, label="Confirm")
	async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
		# if channel and activity is not selected then tell the user to select it.
		if self.activity_id==None or self.channel_id==None:
			await interaction.response.send_message(f"Choose a {'activity' if self.activity_id==None else 'channel'} to proceed.", ephemeral=True)
			return

		voice_channel = discord.utils.get(self.guild.channels, id=self.channel_id)

		try:
			# creating invite
			invite = await voice_channel.create_invite(
				max_age=86400,
				target_type=discord.InviteTarget.embedded_application,
				target_application_id=self.activity_id
			)
		except discord.errors.Forbidden:
			# discord.errors.Forbidden is raised if the bot is missing the required permission
			await interaction.response.send_message("Bot is missing required `Create Instant Invite` permission to run this command", ephemeral=True)
			return
		else:
			# Clearing out buttons and select menu
			self.children=[]
			# adding a linked button for joining the activity
			self.add_item(discord.ui.Button(label=self.activity_description, url=invite.url))
			await interaction.response.edit_message(content=f"Starting Your Game as...\n**Activity:** {self.activity_name}\n**Channel:** {voice_channel.name}",view=self)
			self.stop()

	# A button to just delete the message. In case someone doesn't want to continue
	@discord.ui.button(style=discord.ButtonStyle.red, label="Cancel")
	async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
		# discord.py is not handling the interaction if we do only do interaction.message.delete()
		# Also if the response is not deferred we cannot delete the message 
		# So we deferred the response before deleting the message
		await interaction.response.defer()
		await interaction.message.delete()
		self.stop()


bot = Bot()

@bot.command()
async def play(ctx):
	options = []
	pos=0
	# Getting all the voice channels of a guild (Considering there isn't more than 26)
	for channel in ctx.guild.channels:
		if isinstance(channel, discord.VoiceChannel):
			pos+=1
			options.append(discord.SelectOption(label=f"Voice Channel #{pos}", value=f"{channel.id}", description=channel.name))
	
	# If there isn't a voice channel then ask to create a voice channel
	if len(options)==0:
		await ctx.send("Please create a voice channel to start an activity")
		return
	
	view = GameActivity(timeout=60)
	view.guild = ctx.guild

	# Changing the options of 2nd view item (SelectMenu) without a subclass
	view.children[1].options=options

	await ctx.send("Choose your desired game to play", view=view)

bot.run('token')
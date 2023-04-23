from discord.app_commands import App

app = App(
    application_id = 1000000000000,
    public_key = 'PUBLIC_KEY',
    token = 'TOKEN'
)

@app.tree.command()
async def hello(interaction):
    await interaction.response.send_message('hello')  

# 1. Copy this code to your "main.py" file
# 2. Run "uvicorn main:app" to start the webserver
# 3. Update Interactions Endpoint URL in discord dev page to "<URL>/interactions"
# 4. Go to "<URL>/sync" to sync commands
# 5. F5 Discord and run /hello to make the bot say hello
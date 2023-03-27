import discord 
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)


class FeederBack(discord.ui.Modal , title = "Ok mate"):
    fb_title = discord.ui.TextInput (
        style=discord.TextStyle.short,
        label="Title",
        required=False, 
        placeholder="Sup"
    )

    message = discord.ui.TextInput(
        style=discord.TextStyle.long,
        label= "Confused Unga Bunga",
        required = True, 
        max_length=2000,
        placeholder="I Will show them my true power"
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(1042349269560078356)

        embed = discord.Embed(title="New Feedback", 
                              description=self.message.value, 
                              color= 0x7289da)
        embed.set_author(name=self.user.nick)

        await channel.send(embed=embed)
        await interaction.response.send_message(f"Thank you, {self.user.nick}", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error):
        await interaction.guild.get_channel(1042349269560078356).send("Damn")
    

@client.event
async def on_ready():
    tree.copy_global_to(guild = discord.Object(id = 1033376502177337386))
    await tree.sync(guild = discord.Object(id = 1033376502177337386))
    print("Bot is up and running as {0.user}".format(client))

@client.event
async def on_message(msg):
    if msg.author == client.user:
        return
    if msg.content.lower().startswith("hello"):
        await msg.channel.send("Hello there {0.author.mention}!!".format(msg))
        
@tree.command(name = "feedback" , description = "Give us your feedback" ,
              guild = discord.Object(id = 1033376502177337386))
async def feedback(interaction: discord.Interaction , name: str):
    feedback_modal = FeederBack()
    feedback_modal.user = interaction.user
    await interaction.response.send_modal(feedback_modal)
    await interaction.channel.send("{0.mention} has initiated feedback...".format(interaction.user))
    
@tree.command(name = "echobed" , description = "Embeds a message" , guild = discord.Object(id = 1033376502177337386))
async def self(interaction: discord.Interaction , title: str , description: str):
    embed = discord.Embed(title = title , description = description , color = 0x7289da)
    await interaction.response.send_message(embed = embed)
    
client.run(os.getenv("TOKEN"))
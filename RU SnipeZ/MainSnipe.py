import discord
from discord.ext import commands, tasks
import requests
from discord import app_commands, Interaction
from dataStorage import load_user_data, saving_user_data, user_data
import datetime
from manipulatingdata import data_dict
from discord.ui import Button
import aiohttp
import asyncio
import time
#discord user data stuff
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)
unopen_sections = set()
registration_link = 'https://sims.rutgers.edu/webreg/editSchedule.htm?login=cas&semesterSelection=12024&indexList='
cooldowns = {}





@bot.event
async def on_ready():
    user_data = load_user_data()
    print('Bot is online and connected to Discord!')
    check_open_classes.start()
    synced = await bot.tree.sync()
    print(len(synced))

@bot.event
async def on_member_join(member):
    # Customize your welcome message and embed here
    welcome_channel = bot.get_channel("Channel ID")  # Replace with your actual welcome channel ID

    embed = discord.Embed(
        title=f'Welcome to the server, {member.name}!',
        description=f'We are glad to have you here. Enjoy your stay!',
        color=discord.Color.green()
    )

    embed.set_thumbnail(url=member.avatar_url)

    await welcome_channel.send(embed=embed)



@tasks.loop(seconds=1)
async def check_open_classes():
    # Create a list to store tasks for parallel processing
    response = requests.get("https://sis.rutgers.edu/soc/api/openSections.json?year=2024&term=1&campus=NB")
    open_sections = set(response.json())
    tasks = []

    # Create a copy of the user_data keys
    user_ids = list(user_data.keys())

    for user_id in user_ids:
        sniped_classes = user_data[user_id]['sniped_classes']
        sniped_classes_set = set(sniped_classes)

        # Use set intersection to find common elements between sniped_classes and open_sections
        common_classes = sniped_classes_set & open_sections

        if common_classes:
            user = await bot.fetch_user(user_id)
            if user:
                # Check cooldown for each class and user
                for index in common_classes:
                    if not is_on_cooldown(user_id, index):
                        task = process_user(user, index)
                        tasks.append(task)
                        set_cooldown(user_id, index)

    # Execute tasks concurrently
    await asyncio.gather(*tasks)


def is_on_cooldown(user_id, index):
    cooldown_key = f"{user_id}_{index}"
    return cooldowns.get(cooldown_key, 0) > time.time()

def set_cooldown(user_id, index, cooldown_duration=60):
    cooldown_key = f"{user_id}_{index}"
    cooldowns[cooldown_key] = time.time() + cooldown_duration

async def process_user(user, index):
    embed = discord.Embed()
    notified_classes = set()
    title = data_dict.get(index, {}).get('Title', 'Class Title Not Found')
    section = data_dict.get(index, {}).get('Section', 'Class Section Not Found')
    embed.title = f"{title} {section} is now open!"
    embed.description = f"{index}"
    button_register = discord.ui.Button(style=discord.ButtonStyle.url, label="Register", url=registration_link + index)
    embed.color = discord.Color.green()
    file = discord.File("RU_snipeZ_logo.png", filename='logo.png')
    embed.set_thumbnail(url="attachment://logo.png")  
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    embed.set_footer(text=timestamp)
    message = f"Hey {user.mention}, a class in your snipe list has opened!"
    user_id = user.id
    # Create a dummy Context object to use its send() method
    dm_channel = user.dm_channel
    if dm_channel is None:
        dm_channel = await user.create_dm()
    
    try:
        await dm_channel.send(content=message, embed=embed, file=file, view=discord.ui.View().add_item(button_register))
    except discord.Forbidden:
        print(f"Failed to send message to {user} due to permissions.")
    
    notified_classes.add(index)
    if index in notified_classes:
        notified_classes.remove(index)
    




@bot.tree.command(name='snipe', description='Snipe a Class')
async def snipe(interaction: discord.Interaction, index: str):
    user_id = str(interaction.user.id)

    if user_id not in user_data:
        user_data[user_id] = {
            'sniped_classes': set(),
        }
      # Print the entire data_dict for debugging
    if index not in data_dict:
        await interaction.response.send_message("Invalid index. Please enter a valid index and try again.", ephemeral=True)
        return
    print(f"Received /snipe command with index {index}")
    response = requests.get("https://sis.rutgers.edu/soc/api/openSections.json?year=2024&term=1&campus=NB")
    open_sections = response.json()
    title = data_dict.get(index, {}).get('Title', 'Title not found')
    section = data_dict.get(index, {}).get('Section', 'Section not found')
    # Assuming data_dict is a dictionary containing course information
    
    
    if index in open_sections:
        embed = discord.Embed(
            title=f"{title} {section} is now open!",
            description=f"Course Index: {index}",
            color=discord.Color.green()
        )

        embed.set_thumbnail(url="attachment://logo.png")
        button = Button(style=discord.ButtonStyle.url, label="Register", url=registration_link + index)

        file = discord.File("RU_snipeZ_logo.png", filename='logo.png')
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        embed.set_footer(text=timestamp)

        avatar_url = interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url
        embed.set_author(name=interaction.user.display_name, icon_url=avatar_url)

        await interaction.response.send_message(embed=embed, file=file, view=discord.ui.View().add_item(button), ephemeral=True)
        print(f"Class {index} is currently open!")
    else:
        if len(index) != 5 or not index.isdigit():  # Corrected the condition
            await interaction.response.send_message("Please enter a valid index and try again.", ephemeral=True)
        elif index in user_data[user_id]['sniped_classes']:
            await interaction.response.send_message(f"You already have an existing snipe for {index}.", ephemeral=True)
        else:
            user_data[user_id]['sniped_classes'].append(index)
            embed = discord.Embed(
                title=f"Snipe set for {title} Section {section}",
                description=f"Course Index: {index}",
                color=discord.Color.blue()
            )

            embed.set_thumbnail(url="attachment://logo.png")
            timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
            embed.set_footer(text=timestamp)

            avatar_url = interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url
            embed.set_author(name=interaction.user.display_name, icon_url=avatar_url)

            file = discord.File("RU_snipeZ_logo.png", filename='logo.png')

            await interaction.response.send_message(embed=embed, file=file, ephemeral=True)
            print(f"Snipe set for Class {index}")

    saving_user_data(user_data)

@bot.tree.command(name='remove', description='removes all current snipes')
async def remove(interaction: discord.Interaction, index: str):
    user_id = str(interaction.user.id)
    embed = discord.Embed() 
    title = data_dict.get(index, {}).get('Title', 'Title not found')
    section = data_dict.get(index, {}).get('Section', 'Section not found')
    if index not in data_dict:
        await interaction.response.send_message("Invalid index. Please enter a valid index and try again.", ephemeral=True)
        return
    if user_id in user_data:
        if index in user_data[user_id]['sniped_classes']:
            user_data[user_id]['sniped_classes'].remove(index)
            embed.title = f"{title} {section} at INDEX {index} is now removed!"
            embed.color = discord.Color.green()
            avatar_url = interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url
            embed.set_author(name=interaction.user.display_name, icon_url=avatar_url)

            # Add timestamp to the description
            timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
            embed.description = f"Timestamp: {timestamp}"
            file = discord.File("RU_snipeZ_logo.png", filename='logo.png')
            embed.set_thumbnail(url="attachment://logo.png") 
            await interaction.response.send_message(embed=embed, file=file,  ephemeral=True)
            print(f'Recieved /remove with index {index}')
        else:
            await interaction.response.send_message(f"{index} is not found in snipe list",  ephemeral=True)
    else:
        await interaction.response.send_message("You are currently not sniping any classes",  ephemeral=True)
    saving_user_data(user_data)




@bot.tree.command(name='clear', description='clears all snipes')
async def clear(interaction: Interaction):
    user_id = str(interaction.user.id)
    embed = discord.Embed() 

    if user_id in user_data:
        currently_sniping = user_data[user_id]['sniped_classes']
        currently_sniping.clear()
        print('Sniped clear run success')
        
        embed.title = f"All snipes are removed!"
        embed.color = discord.Color.green()
        avatar_url = interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url
        embed.set_author(name=interaction.user.display_name, icon_url=avatar_url)
        file = discord.File("RU_snipeZ_logo.png", filename='logo.png')
        embed.set_thumbnail(url="attachment://logo.png") 
        
        

        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        embed.set_footer(text=timestamp)

            
        
        await interaction.response.send_message(embed=embed, file=file,  ephemeral=True)
    else:
        
        await interaction.response.send_message("You are currently not sniping any classes.",  ephemeral=True)

    saving_user_data(user_data)


@bot.tree.command(name='check', description='check all current snipes')
async def check(interaction: Interaction):
    user_id = str(interaction.user.id)
    embed = discord.Embed()
    # Check if the user is in the user_data dictionary
    if user_id in user_data:
        sniped_classes = user_data[user_id]['sniped_classes']
        print(f'Recieved /check command')
        embed.title = f"All current sniped classes!"
        embed.color = discord.Color.green()
        avatar_url = interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url
        embed.set_author(name=interaction.user.display_name, icon_url=avatar_url)
        file = discord.File("RU_snipeZ_logo.png", filename='logo.png')
        embed.set_thumbnail(url="attachment://logo.png")  
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        embed.set_footer(text=timestamp)

        if sniped_classes:
            description = ''
            list_of_sniped_classes = list(sniped_classes)
            for item in list_of_sniped_classes:
                index = item
                title = data_dict.get(index, {}).get('Title', '--')
                section = data_dict.get(index, {}).get('Section', '--')
                description += f'{title} at SECTION {section} on INDEX {index}\n'
            embed.description = description
        else:
            embed.description = 'You are currently not sniping any classes.'

       
        await interaction.response.send_message(embed=embed, file=file,  ephemeral=True)
    else:
        
        await interaction.response.send_message("You are currently not sniping any classes.",  ephemeral=True)

    saving_user_data(user_data)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    await bot.process_commands(message) 

    user_id = str(message.author.id)
    if user_id not in user_data:
        user_data[user_id] = {
            'sniped_classes' : set(),
        }

    if message.content.startswith('hello'):
        await message.channel.send('Hello!')



bot.run('Bot Token Here')

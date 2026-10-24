import discord, os, random
from game import check_winner, is_board_full
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Tells discord what the bot is allowed to see
intents = discord.Intents.default()

# Lets the bot read the text message
intents.message_content = True

class MyView(discord.ui.View):
    # Runs when someone clicks on the button
    @discord.ui.button(label="Click me", style=discord.ButtonStyle.primary)
    async def my_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Reply to when you click the button
        button.label = 'Clicked!'
        button.style = discord.ButtonStyle.success # shows green button for success
        button.disabled = True # Greys the button to make it unclickable
        # Using the View that I'm inside of 
        await interaction.response.edit_message(view=self)
    

# Button Class
class CellButton(discord.ui.Button):
    def __init__(self, row, col):
        super().__init__(style=discord.ButtonStyle.secondary, label='\u200b', row=row)
        self.r = row
        self.c = col
    
    async def callback(self, interaction: discord.Interaction):
        # Responds to user privately and tells them to stop playing the game 
        if interaction.user != self.view.player:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        # The button goes to the Board it belongs to, finds the Board's list, and puts an X
        # at its own row and column
        self.view.board[self.r][self.c] = 'X'
        self.label = 'X'
        self.style = discord.ButtonStyle.primary
        self.disabled = True

        winner = check_winner(self.view.board)
        tie = is_board_full(self.view.board)

        if winner:
            # Someone won, show the win message
            self.view.lock()
            await interaction.response.edit_message(content='You won!', view=self.view)
        elif tie:
            self.view.lock()
            await interaction.response.edit_message(content='It\'s a tie!', view=self.view)
        else:
            # No winner yet
            empty_spaces = []
            for r in range(3):
                for c in range(3):
                    if self.view.board[r][c] == '---':
                        empty_spaces.append((r, c))
            row, col = random.choice(empty_spaces)

            # Puts 'O' in the list at the spot the bot picks on the board
            self.view.board[row][col] = 'O'

            for item in self.view.children:
                if item.r == row and item.c == col:
                    item.label = 'O'
                    item.style = discord.ButtonStyle.red
                    item.disabled = True

            winner = check_winner(self.view.board)
            tie = is_board_full(self.view.board)

            # Checks if bot won
            if winner:
                self.view.lock()
                await interaction.response.edit_message(content='TicTacToe Bot Won!', view=self.view)
            # Checks if its a tie
            elif tie:
                self.view.lock()
                await interaction.response.edit_message(content='It\'s a tie!', view=self.view)
            # Check if no one has won or tied 
            else:
                await interaction.response.edit_message(content='It\'s your turn!', view=self.view) 

# Game Board
class Board(discord.ui.View):
    def __init__(self, player):
        super().__init__() # run discord.ui.View's setup first
        self.player = player
        self.board = [
        ["---", "---", "---"],
        ["---", "---", "---"],
        ["---", "---", "---"],
        ]

        for r in range(3):
            for c in range(3):
                btn = CellButton(r, c) # Creates the button object 
                self.add_item(btn)     # Adds the button to the View

    def lock(self):
        for item in self.children:
            item.disabled = True

# Tic Tac Toe Bot 
class MyClient(discord.Client):
    # Runs when the bot connects to the channel
    async def on_ready(self):
        print('Logged on as {0}'.format(self.user))

    # Gets called if there is a new message in a channel 
    async def on_message(self, message):
        # Ignore messsages sent by the bot
        if message.author == self.user:
            return
        # if user types !ping respond back with pong
        if message.content.startswith('!ping'):
            await message.channel.send('pong')
        # if user types !button show a button
        if message.content.startswith('!button'):
            # Make a new View object
            await message.channel.send('Here\'s a button', view=MyView())
        if message.content.startswith('!ttt'):
            # Replies to the message received with a message and sends a 3x3 button grid
            # Board(message.author) creates a Board object which builds the 3x3 buttons
            # message.author is the person who typed the command and saves it 
            await message.channel.send('Tic Tac toe!', view=Board(message.author)) 

client = MyClient(intents=intents)
client.run(TOKEN)
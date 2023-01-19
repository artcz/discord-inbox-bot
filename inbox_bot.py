import os
from datetime import datetime

import discord
from discord.ext import commands
from peewee import *

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

db = SqliteDatabase("database.db")


class Todo(Model):
    # message on discord that we want to track
    message_id = TextField()
    channel_id = TextField()
    channel_name = TextField()
    server_id = TextField()
    author = TextField()

    # This is ID of the user that's tracking the message.
    # Using CharFields instead of ints just to avoid overflows and other issues
    user_id = TextField()
    content = TextField()

    created_at = DateTimeField()

    class Meta:
        database = db

    def url(self):
        return f"https://discord.com/channels/{self.server_id}/{self.channel_id}/{self.message_id}"

    def summary(self):
        return (
            f"`{self.timestamp}` | from **{self.author}** @ **{self.channel_name}**: "
            f"[{self.content[:30]}...]({self.url()})"
        )

    @property
    def timestamp(self):
        return self.created_at.strftime("%Y-%m-%d %H:%M")


def create_tables():
    with db:
        db.create_tables([Todo])


create_table = 1

if create_table:
    create_tables()
    print("Created tables!")


run_bot = 1
inbox_emoji = "📥"


if run_bot:
    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_raw_reaction_add(payload):
        if payload.emoji.name == inbox_emoji:
            channel = bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            Todo.create(
                content=message.content,
                message_id=message.id,
                user_id=str(payload.user_id),
                channel_id=str(payload.channel_id),
                channel_name=f"#{channel.name}",
                server_id=str(payload.guild_id),
                author=str(message.author.name),
                created_at=datetime.now(),
            )

    @bot.event
    async def on_raw_reaction_remove(payload):
        if payload.emoji.name == inbox_emoji:
            todo = Todo.get(
                Todo.id == payload.message_id,
                Todo.user_id == payload.user_id,
            )
            todo.delete_instance()

    @bot.command()
    async def inbox(ctx):
        user_id = ctx.message.author.id
        todos = Todo.select().where(Todo.user_id == user_id).execute()
        msg = "Currently tracking following mesages: \n"

        for todo in todos:
            msg += "* " + todo.summary() + "\n"

        embed = discord.Embed()
        embed.description = msg
        await ctx.send(embed=embed)

    inbox_bot_token = os.environ["inbox_bot_token"]
    bot.run(inbox_bot_token)

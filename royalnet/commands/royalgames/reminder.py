import typing
import dateparser
import datetime
import pickle
import telegram
import discord
from sqlalchemy import and_
from ..command import Command
from ..commandargs import CommandArgs
from ..commandinterface import CommandInterface
from ..commanddata import CommandData
from ...utils import sleep_until, asyncify, telegram_escape, discord_escape
from ...database.tables import Reminder
from ...error import *


class ReminderCommand(Command):
    name: str = "reminder"

    description: str = "Ti ricorda di fare qualcosa dopo un po' di tempo."

    syntax: str = "[ (data) ] (messaggio)"

    require_alchemy_tables = {Reminder}

    def __init__(self, interface: CommandInterface):
        super().__init__(interface)
        reminders = (
            interface.session
                     .query(interface.alchemy.Reminder)
                     .filter(and_(
                         interface.alchemy.Reminder.datetime >= datetime.datetime.now(),
                         interface.alchemy.Reminder.interface_name == interface.name))
                     .all()
        )
        for reminder in reminders:
            interface.loop.create_task(self._remind(reminder))

    async def _remind(self, reminder):
        await sleep_until(reminder.datetime)
        if self.interface.name == "telegram":
            chat_id: int = pickle.loads(reminder.interface_data)
            bot: telegram.Bot = self.interface.bot.client
            await asyncify(bot.send_message,
                           chat_id=chat_id,
                           text=telegram_escape(f"❗️ {reminder.message}"),
                           parse_mode="HTML",
                           disable_web_page_preview=True)
        elif self.interface.name == "discord":
            channel_id: int = pickle.loads(reminder.interface_data)
            bot: discord.Client = self.interface.bot.client
            channel = bot.get_channel(channel_id)
            await channel.send(discord_escape(f"❗️ {reminder.message}"))

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        try:
            date_str, reminder_text = args.match(r"\[\s*([^]]+)\s*]\s*([^\n]+)\s*")
        except InvalidInputError:
            date_str, reminder_text = args.match(r"\s*(.+?)\s*\n\s*([^\n]+)\s*")

        try:
            date: typing.Optional[datetime.datetime] = dateparser.parse(date_str)
        except OverflowError:
            date = None
        if date is None:
            await data.reply("⚠️ La data che hai inserito non è valida.")
            return
        if date <= datetime.datetime.now():
            await data.reply("⚠️ La data che hai specificato è nel passato.")
            return
        await data.reply(f"✅ Promemoria impostato per [b]{date.strftime('%Y-%m-%d %H:%M:%S')}[/b]")
        if self.interface.name == "telegram":
            interface_data = pickle.dumps(data.update.effective_chat.id)
        elif self.interface.name == "discord":
            interface_data = pickle.dumps(data.message.channel.id)
        else:
            raise UnsupportedError("Interface not supported")
        creator = await data.get_author()
        reminder = self.interface.alchemy.Reminder(creator=creator,
                                                   interface_name=self.interface.name,
                                                   interface_data=interface_data,
                                                   datetime=date,
                                                   message=reminder_text)
        self.interface.loop.create_task(self._remind(reminder))
        self.interface.session.add(reminder)
        await asyncify(self.interface.session.commit)
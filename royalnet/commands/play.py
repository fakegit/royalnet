import typing
import asyncio
import youtube_dl
import ffmpeg
from ..utils import Command, Call, NetworkHandler, asyncify
from ..network import Message, RequestSuccessful, RequestError
from ..error import TooManyFoundError, NoneFoundError
from ..audio import RoyalPCMAudio, YtdlInfo
if typing.TYPE_CHECKING:
    from ..bots import DiscordBot


loop = asyncio.get_event_loop()


class PlayMessage(Message):
    def __init__(self, url: str, guild_name: typing.Optional[str] = None):
        self.url: str = url
        self.guild_name: typing.Optional[str] = guild_name


class PlaySuccessful(RequestSuccessful):
    def __init__(self, info_list: typing.List[YtdlInfo]):
        self.info_list: typing.List[YtdlInfo] = info_list


class PlayNH(NetworkHandler):
    message_type = PlayMessage

    @classmethod
    async def discord(cls, bot: "DiscordBot", message: PlayMessage):
        """Handle a play Royalnet request. That is, add audio to a PlayMode."""
        # Find the matching guild
        if message.guild_name:
            guild = bot.client.find_guild(message.guild_name)
        else:
            if len(bot.music_data) == 0:
                raise NoneFoundError("No voice clients active")
            if len(bot.music_data) > 1:
                raise TooManyFoundError("Multiple guilds found")
            guild = list(bot.music_data)[0]
        # Ensure the guild has a PlayMode before adding the file to it
        if not bot.music_data.get(guild):
            # TODO: change Exception
            raise Exception("No music_data for this guild")
        # Start downloading
        try:
            audio_sources: typing.List[RoyalPCMAudio] = await asyncify(RoyalPCMAudio.create_from_url, message.url)
        except youtube_dl.utils.DownloadError:
            audio_sources = await asyncify(RoyalPCMAudio.create_from_ytsearch, message.url)
        await bot.add_to_music_data(audio_sources, guild)
        return PlaySuccessful(info_list=[source.rpf.info for source in audio_sources])


class PlayCommand(Command):
    command_name = "play"
    command_description = "Riproduce una canzone in chat vocale."
    command_syntax = "[ [guild] ] (url)"

    network_handlers = [PlayNH]

    @classmethod
    async def common(cls, call: Call):
        guild, url = call.args.match(r"(?:\[(.+)])?\s*(.+)")
        response: typing.Union[RequestError, PlaySuccessful] = await call.net_request(PlayMessage(url, guild), "discord")
        if isinstance(response, RequestError):
            # RoyalPCMFile errors
            if isinstance(response.exc, FileExistsError):
                await call.reply(f"❌ Scaricare [c]{url}[/c] significherebbe sovrascrivere un file già esistente.\nQuesto è un bug, e non dovrebbe mai succedere. Se è appena successo, segnalate il problema a https://github.com/Steffo99/royalnet/issues.\n[p]{response.exc}[/p]")
                return
            # ffmpeg errors
            if isinstance(response.exc, ffmpeg.Error):
                await call.reply(f"⚠️ Errore durante la conversione a PCM di [c]{url}[/c]:\n[p]{response.exc}[/p]")
                return
            # youtube_dl errors
            if isinstance(response.exc, youtube_dl.utils.ContentTooShortError):
                await call.reply(f"⚠️ Mentre era in corso il download di [c]{url}[/c], la connessione è stata interrotta, quindi la riproduzione è stata annullata.\n[p]{response.exc}[/p]")
                return
            if isinstance(response.exc, youtube_dl.utils.UnavailableVideoError):
                await call.reply(f"⚠️ Non è disponibile nessun audio su [c]{url}[/c].\n[p]{response.exc}[/p]")
                return
            if isinstance(response.exc, youtube_dl.utils.SameFileError):
                await call.reply(f"❌ Scaricare [c]{url}[/c] significherebbe scaricare due file diversi sullo stesso nome.\nQuesto è un bug, e non dovrebbe mai succedere. Se è appena successo, segnalate il problema a https://github.com/Steffo99/royalnet/issues.\n[p]{response.exc}[/p]")
                return
            if isinstance(response.exc, youtube_dl.utils.GeoRestrictedError):
                await call.reply(f"⚠️ [c]{url}[/c] non può essere visualizzato nel paese in cui si trova il bot e non può essere scaricato.\n[p]{response.exc}[/p]")
                return
            if isinstance(response.exc, youtube_dl.utils.UnsupportedError):
                await call.reply(f"⚠️ [c]{url}[/c] non è supportato da YoutubeDL e non può essere scaricato.\n[p]{response.exc}[/p]")
                return
            if isinstance(response.exc, youtube_dl.utils.ExtractorError):
                await call.reply(f"⚠️ Errore nella ricerca di info per [c]{url}[/c]:\n[p]{response.exc}[/p]")
                return
            if isinstance(response.exc, youtube_dl.utils.DownloadError):
                await call.reply(f"⚠️ Errore nel download di [c]{url}[/c]:\n[p]{response.exc}[/p]")
                return
            if isinstance(response.exc, youtube_dl.utils.YoutubeDLError):
                await call.reply(f"⚠️ Errore di youtube_dl per [c]{url}[/c]:\n[p]{response.exc}[/p]")
                return
        for info in response.info_list:
            await call.reply(f"⬇️ Download di [i]{info.title}[/i] completato.")

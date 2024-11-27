from __future__ import annotations
import os
import tempfile
import validators
from asyncio import TimeoutError, sleep
from discord import (
    ClientException,
    FFmpegPCMAudio,
    utils,
    VoiceState,
)
from dotenv import load_dotenv
from typing import TYPE_CHECKING, Union
from yt_dlp import YoutubeDL
from milo.globals import voice_client_tts_max_chars
from milo.helpers.action_decorators import no_response, simple_response

if TYPE_CHECKING:
    from discord import Message, VoiceClient
    from milo.handler.discord import DiscordHandler
    from milo.handler.llm import LLMHandler


class DiscordAudio:
    """
    Class to handle the bot interacting in Discord voice channels.

    Attributes:
        dc_handler: DiscordHandler
        llm_handler: LLMHandler
        message: Message
        voice_state_user: VoiceState
        args: dict
    """

    def __init__(
        self,
        dc_handler: DiscordHandler,
        message: Message,
        args: dict,
        llm_handler: LLMHandler = None,
    ) -> None:
        self.dc_handler = dc_handler
        self.llm_handler = llm_handler
        self.message = message
        self.voice_state_user: VoiceState = message.author.voice
        self.args = args

    @property
    def ydl_opts(self) -> dict:
        """
        Options to be used with yt-dlp.

        Returns:
            dict
        """
        load_dotenv()
        proxy = os.getenv("PROXY")

        return {
            "verbose": False,
            "geo-bypass": True,
            "format": "bestaudio/best",
            "quiet": True,
            "noplaylist": True,
            "playlist_items": "1",
            "extractaudio": True,
            "audio-format": "mp3",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "nocheckcertificate": True,
            "proxy": proxy,
            "cookiefile": "./data/system/youtube_cookies.txt",
            "skip_download": True,
            "ignore-errors": True,
        }

    async def get_voice_client(self) -> Union[VoiceClient, None]:
        """
        Get voice client if it exists or connect to voice channel and
        create voice client. The voice client will always be associated
        with the user.

        Raises:
            ClientException: Exception
            TimeoutError: Exception

        Returns:
            Union[VoiceClient, None]
        """
        if self.voice_state_user is None:
            raise ClientException("User must be connected to voice channel.")

        voice_client = utils.get(
            self.dc_handler.client.voice_clients, guild=self.message.guild
        )

        if voice_client is not None:
            # return voice_client if exists already. if user is in a different
            # voice channel, disconnect and don't exit function
            if voice_client.channel == self.voice_state_user.channel:
                return voice_client
            else:
                await voice_client.disconnect()

        voice_channel = self.voice_state_user.channel

        try:
            voice_client = await voice_channel.connect()
            return voice_client
        except TimeoutError as e:
            raise TimeoutError(e)
        except ClientException as e:
            raise ClientException(e)

    async def play_from_file(self, filepath: str) -> None:
        """
        Play audio file in Discord voice channel.

        Args:
            filepath (): str
        """
        try:
            voice_client = await self.get_voice_client()
        except Exception as e:
            raise Exception(e)

        if voice_client.is_playing():
            voice_client.stop()

        ffmpeg_options = {"options": "-vn"}

        source = FFmpegPCMAudio(source=filepath, **ffmpeg_options)
        voice_client.play(source)
        while voice_client.is_playing():
            await sleep(1)

    @no_response
    async def say_text(self) -> Union[str, None]:
        """
        Creates audio file from text as a temp file and play it.

        Returns:
            Union[str, None]
        """

        # summarize if text is too long
        if len(self.args["text"]) > voice_client_tts_max_chars:
            text = self.llm_handler.summarize_text(
                self.args["text"], voice_client_tts_max_chars
            )
            text = f"Summarizing because that message was way too long: {text}"
        else:
            text = self.args["text"]

        temp_file = tempfile.NamedTemporaryFile(suffix=".opus")
        self.llm_handler.text_to_speech(temp_file.name, text)

        try:
            await self.play_from_file(temp_file.name)
        except Exception as e:
            return f"{e}"

    @simple_response
    async def stream_audio(self) -> str:
        """
        Stream audio from URL or search YouTube and stream result.

        Returns:
            str
        """

        try:
            voice_client = await self.get_voice_client()
        except Exception as e:
            return f"{e}"

        try:
            query = self.args["query"]

            yt_domains = ["youtube.com", "youtu.be"]
            is_youtube = any(i in query for i in yt_domains)

            if validators.url(query) and not is_youtube:
                # play directly from URL if the source is not YouTube
                with YoutubeDL(self.ydl_opts) as ydl:
                    info_searched = ydl.extract_info(query, download=False)
                    audio_url = info_searched["url"]
                    title = info_searched["title"]
            else:
                # don't use proxy if using YouTube
                ydl_opts = self.ydl_opts
                ydl_opts.pop("proxy")

                if not validators.url(query):
                    query = f"{query} audio"  # search specifically for audio

                with YoutubeDL(ydl_opts) as ydl:
                    info_searched = ydl.extract_info(
                        f"ytsearch1:{query}", download=False
                    )
                    audio_url = info_searched["entries"][0]["url"]
                    title = info_searched["entries"][0]["title"]

        except Exception as e:
            return f"An error occured: {e}"

        else:

            ffmpeg_options = {
                "options": "-vn",
                "before_options": """-reconnect 1 -reconnect_streamed 1
                -reconnect_delay_max 5""",
            }

            source = FFmpegPCMAudio(audio_url, **ffmpeg_options)

            if voice_client.is_playing():
                voice_client.stop()
            voice_client.play(source)

            return title

    @simple_response
    async def pause(self) -> Union[str, None]:
        """
        Pause whatever is playing in voice client.

        Returns:
            Union[str, None]
        """
        try:
            voice_client = await self.get_voice_client()
        except Exception as e:
            return f"{e}"

        if voice_client.is_paused():
            return "already paused"
        elif voice_client.is_playing():
            voice_client.pause()
        else:
            return "nothing playing"

    @simple_response
    async def resume(self) -> Union[str, None]:
        """
        Resumes whatever is playing in voice client.

        Returns:
            Union[str, None]
        """
        try:
            voice_client = await self.get_voice_client()
        except Exception as e:
            return f"{e}"

        if voice_client.is_paused():
            voice_client.resume()
        elif voice_client.is_playing():
            return "already playing"
        else:
            return "nothing playing"

    @simple_response
    async def stop(self) -> Union[str, None]:
        """
        Stops whatever is playing in voice client.

        Returns:
            Union[str, None]
        """
        try:
            voice_client = await self.get_voice_client()
        except Exception as e:
            return f"{e}"

        if voice_client.is_playing():
            voice_client.stop()
        else:
            return "nothing playing"

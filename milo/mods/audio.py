from __future__ import annotations
import logging
import os
import tempfile
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
from milo.handler.action_decorators import no_response, simple_response

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
        }

    async def get_voice_client(self) -> VoiceClient:
        """
        Get voice client if it exists or connect to voice channel and
        create voice client with that.

        Raises:
            ClientException: Exception

        Returns:
            VoiceClient
        """
        voice_client = utils.get(
            self.dc_handler.client.voice_clients, guild=self.message.guild
        )

        if voice_client is None:
            if self.voice_state_user is None:
                raise ClientException(
                    "User must be connected to voice channel."
                )

            voice_channel = self.voice_state_user.channel

            try:
                voice_client = await voice_channel.connect()
                return voice_client
            except TimeoutError as timeout:
                logging.error(timeout)
            except ClientException as already_connected:
                logging.info(already_connected)
        else:
            return voice_client

    async def play_from_file(self, filepath: str) -> None:
        """
        Play audio file in Discord voice channel.

        Args:
            filepath (): str
        """
        try:
            voice_client = await self.get_voice_client()
        except Exception as e:
            return f"{e}"

        if voice_client.is_playing():
            voice_client.stop()

        ffmpeg_options = {"options": "-vn"}

        source = FFmpegPCMAudio(source=filepath, **ffmpeg_options)
        voice_client.play(source)
        while voice_client.is_playing():
            await sleep(1)

    @no_response
    async def say_text(self) -> None:
        """Creates audio file from text as a temp file and play it."""
        # exit if the text is longer than 500 characters
        if len(self.args["text"]) > 200:
            return

        temp_file = tempfile.NamedTemporaryFile(suffix=".opus")

        self.llm_handler.text_to_speech(temp_file.name, self.args["text"])
        await self.play_from_file(temp_file.name)

    @simple_response
    async def stream_audio(self) -> None:
        """Stream audio from URL or search YouTube and stream result."""

        try:
            voice_client = await self.get_voice_client()
        except Exception as e:
            return f"{e}"

        try:
            with YoutubeDL(self.ydl_opts) as ydl:
                title = self.args["query"]
                info_searched = ydl.extract_info(
                    f"ytsearch1:{title}", download=False
                )
                audio_url = info_searched["entries"][0]["url"]

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

            return info_searched["title"]

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

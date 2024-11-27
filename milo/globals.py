from milo.handler.log import Logger

app_logger = Logger("milo").get_logger()

bot_name = "milo"
bot_name_len = len(bot_name)
bot_server_id = 0

parent_mod = "milo.mods"
timeout_wait_for_reply = 10
timeout_wait_for_button_interaction = 5
voice_client_disconnect_time = 60
voice_client_tts_max_chars = 250

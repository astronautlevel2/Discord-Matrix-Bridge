"""
    Copyright 2018 Alex Taber ("astronautlevel")

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

from matrix_client.client import MatrixClient
import requests
import json
import discord
import re
from config import *

matrix_client = MatrixClient(matrix_homeserver)
token = matrix_client.login(matrix_username, matrix_password)
discord_client = discord.Client()

matrix_room = matrix_client.join_room(matrix_room_id)

matrix_file_types = ('m.file', 'm.image', 'm.video', 'm.audio')

def prepare_matrix_content(message):
	attachments = "\n".join([x.url for x in message.attachments])
	content = message.clean_content + ("\n" + attachments if attachments != "" else "")
	return content

guild = None
emojis = {}

@discord_client.event
async def on_ready():
	global guild
	global emojis
	guild = discord_client.get_channel(discord_channel).guild
	emojis = {":{}:".format(emoji.name): "<:{}:{}>".format(emoji.name, emoji.id) for emoji in guild.emojis}

@discord_client.event
async def on_message(message):
	if message.author.discriminator == "0000" or message.channel.id != discord_channel: return
	username = message.author.name[:1] + "\u200B" + message.author.name[1:] + "#" + message.author.discriminator
	content = prepare_matrix_content(message)
	matrix_room.send_text("<{}> {}".format(username, content))

def send_webhook(username, avatar_url, content):
	data = {'username': username, 'content': content}
	if avatar_url: data['avatar_url'] = avatar_url
	headers = {'Content-type': 'application/json'}
	r = requests.post(webhook_url, data = json.dumps(data), headers=headers)

def prepare_discord_content(content):
	content = content.replace("@everyone", "@\u200Beveryone")
	content = content.replace("@here", "@\u200Bhere")
	content = re.sub("</?del>", "~~", content)
	mentions = re.findall("(^|\s)(@(\w*))", content)
	for mention in mentions:
		member = guild.get_member_named(mention[2])
		if not member: continue
		content = content.replace(mention[1], member.mention)
	for emoji_name, emoji_id in emojis.items():
		if emoji_name in content:
			content = content.replace(emoji_name, emoji_id)
	return content

def on_matrix_message(room, event):
	user = matrix_client.get_user(event['sender'])
	if event['type'] == "m.room.message" and not user.user_id == matrix_user_id:
		if event['content']['msgtype'] == "m.text":
			username = "{}{}".format(discord_prefix, user.get_display_name())
			avatar = user.get_avatar_url()
			content = prepare_discord_content(event['content']['body'])
			send_webhook(username, avatar, content)
		if event['content']['msgtype'] in matrix_file_types:
			username = "{}{}".format(discord_prefix, user.get_display_name())
			avatar = user.get_avatar_url()
			content = matrix_homeserver + "/_matrix/media/v1/download/" + event['content']['url'][6:]
			send_webhook(username, avatar, content)

matrix_room.add_listener(on_matrix_message)
matrix_client.start_listener_thread()
discord_client.run(discord_token)

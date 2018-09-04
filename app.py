from matrix_client.client import MatrixClient
import requests
import json
import discord
import re
from config import *

matrix_client = MatrixClient(matrix_homeserver, token=matrix_token,  user_id=matrix_user_id)
discord_client = discord.Client()

matrix_room = matrix_client.join_room(matrix_room_id)

@discord_client.event
async def on_message(message):
	if message.author.discriminator == "0000": return
	username = message.author.display_name[:1] + "\u200B" + message.author.display_name[1:]
	matrix_room.send_text("<{}> {}".format(username, message.clean_content))

def send_webhook(username, avatar_url, content):
	data = {'username': username, 'content': content}
	if avatar_url: data['avatar_url'] = avatar_url
	headers = {'Content-type': 'application/json'}
	r = requests.post(webhook_url, data = json.dumps(data), headers=headers)

def prepare_discord_content(content):
	content = content.replace("@everyone", "@\u200Beveryone")
	content = content.replace("@here", "@\u200Bhere")
	mentions = re.findall("(^|\s)(@(\w*))", content)
	guild = discord_client.get_channel(discord_channel).guild
	for mention in mentions:
		member = guild.get_member_named(mention[2])
		if not member: continue
		content = content.replace(mention[1], member.mention)
	return content

def on_matrix_message(room, event):
	if event['type'] == "m.room.message":
		user = matrix_client.get_user(event['sender'])
		if event['content']['msgtype'] == "m.text" and not user.user_id == matrix_user_id:
			username = "[Matrix] {}".format(user.get_display_name())
			avatar = user.get_avatar_url()
			content = prepare_discord_content(event['content']['body'])
			send_webhook(username, avatar, content)

matrix_room.add_listener(on_matrix_message)
matrix_client.start_listener_thread()
discord_client.run(discord_token)

#!/usr/bin/env python3

import json
import getpass
import requests
import os
import time
import binascii
import pickle
import html
from datetime import datetime

backup_dir = os.path.expanduser(os.path.join(
    "~", "Downloads", "RocketChat_Backup"))


def main():
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    global base_url
    if os.environ.get('ROCKETCHAT_URL') is None:
        base_url = input("Base URL: ")
    else:
        base_url = os.environ.get('ROCKETCHAT_URL')

    global auth_headers
    token, uid = get_token()
    auth_headers = {'X-User-Id': uid, 'X-Auth-Token': token}

    rooms = get_rooms()
    selected_rooms = filter_rooms(rooms)
    for r in selected_rooms:
        backup_file_base = os.path.join(backup_dir, name_of(r))
        print(f'Dumping {backup_file_base} ...')
        backup(r, backup_file_base)


def get_token():
    global user
    if os.environ.get('ROCKETCHAT_USER') is None:
        user = input("Username: ")
    else:
        user = os.environ.get('ROCKETCHAT_USER')
    if os.environ.get('ROCKETCHAT_PASSWORD') is None:
        passwd = getpass.getpass(prompt="Password: ")
    else:
        passwd = os.environ.get('ROCKETCHAT_PASSWORD')
    payload = {'user': user, 'password': passwd}
    resp = requests.post(f'{base_url}/api/v1/login', data=payload)
    return resp.json()['data']['authToken'], resp.json()['data']['me']['_id']


def get_rooms():
    resp = requests.get(f'{base_url}/api/v1/rooms.get', headers=auth_headers)
    return resp.json()['update']


def name_of(room):
    if room['t'] != 'd':
        return html.escape(room['name'])
    usernames = room['usernames'].copy()
    usernames.remove(user)
    return html.escape(usernames[0]) if len(usernames) > 0 else "unknown room"


def filter_rooms(rooms):
    print('Found rooms:')
    i = 1
    for r in rooms:
        print(f'- {i: >2} {name_of(r)}')
        i += 1
    selection = input(
        "Room number(s) to dump (a for all; separate multiple numbers with spaces): ")
    if selection == 'a':
        return rooms
    return [rooms[int(s)-1] for s in selection.split()]


def backup(room, backup_file_base):
    if room['t'] == 'd':
        backup_dms(room, backup_file_base)
    elif room['t'] == 'c' or room['t'] == 'p':
        backup_channel_or_group(room, backup_file_base)
    else:
        print(
            f'Could not dump {room["_id"]}, because it has the unknown type "{room["t"]}".')


def backup_dms(room, backup_file_base):
    msgs = []
    offset = 0
    while True:
        while True:
            resp = requests.get(
                f'{base_url}/api/v1/im.messages?roomId={room["_id"]}&count=100&offset={offset}', headers=auth_headers)
            if resp.status_code == 429:
                print('Received 429 response. Retrying in 60 seconds...')
                time.sleep(60)
                continue
            elif resp.status_code != 200:
                print(resp.json())
                resp.raise_for_status()
            else:
                break
        j = resp.json()
        msgs += j['messages']
        offset = j['offset'] + j['count']
        print(f'Retrieved {offset} of {j["total"]} messages...')
        if j['count'] == 0 or j['total'] <= j['offset'] + j['count']:
            break
    sort_thread_and_dump(room, msgs, backup_file_base)


def backup_channel_or_group(room, backup_file_base):
    msgs = []
    offset = 0
    while True:
        while True:
            if room['t'] == 'c':
                path = f'{base_url}/api/v1/channels.history'
            else:
                path = f'{base_url}/api/v1/groups.history'
            resp = requests.get(
                f'{path}?roomId={room["_id"]}&count=100&offset={offset}', headers=auth_headers)
            if resp.status_code == 429:
                print('Received 429 response. Retrying in 60 seconds...')
                time.sleep(60)
                continue
            elif resp.status_code != 200:
                print(resp.json())
                resp.raise_for_status()
            else:
                break
        j = resp.json()
        msgs += j['messages']
        offset += 100  # Offset 100 seems to be allowed.
        print(f'Retrieved {offset} messages (total amount unkown)...')
        if len(j['messages']) == 0:
            break
        sort_thread_and_dump(room, msgs, backup_file_base)


def sort_thread_and_dump(room, msgs, backup_file_base):
    msgs = sorted(msgs, key=lambda x: x['ts'], reverse=True)
    threaded_msgs = []
    msgs.reverse()
    for msg in msgs:
        if 't' in msg:
            # This seems to mean that this is a special message like "user joined".
            continue
        if 'tmid' not in msg:
            threaded_msgs.append(msg)
            threaded_msgs += [x for x in msgs if x.get(
                'tmid', '_') == msg['_id']]
    dump(room, threaded_msgs, backup_file_base)


def dump(room, threaded_msgs, backup_file_base):
    dump_pickle(room, threaded_msgs, backup_file_base)
    dump_html(room, threaded_msgs, backup_file_base)


def dump_pickle(room, threaded_msgs, backup_file_base):
    filename = backup_file_base + '.pkl'
    print(f"Writing {filename}...")
    with open(filename, 'wb') as f:
        pickle.dump({'room': room, 'threaded_msgs': threaded_msgs}, f)


def dump_html(room, threaded_msgs, backup_file_base):
    filename = backup_file_base + '.html'
    print(f"Writing {filename}...")
    with open(filename, 'w') as f:
        f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <style>
        body {{
            background: ghostwhite;
        }}
        h1 {{
            text-align: center;
        }}
        .content {{
            max-width: 52em;
            margin: 0 auto;
        }}
        .card {{
            box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
            margin: 12px;
            padding: 8px;
            background: white;
        }}
        .card.response {{
            margin-left: 4em;
        }}
        .card h2 {{
            font-size: large;
            margin: 0.3em;
        }}
    </style>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>{name_of(room)} RocketChat Backup</title>
</head>
<body>
<div class="content">
    <h1>{name_of(room)} RocketChat Backup</h1>
""")
        for msg in threaded_msgs:
            content = msg["msg"]
            for attachment in msg.get('attachments', []):
                if content:
                    content += '\n'
                content += f'Attachment "{attachment.get("title", "without title")}"'
                if 'description' in attachment:
                    content += f': {attachment["description"]}'
            name = msg.get('u', {}).get('name', 'unknown name')
            ts = datetime.strptime(
                msg["ts"], '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%d %H:%M:%S UTC')
            colorval = 10 * (binascii.crc32(name.encode('utf8')) % 36)
            classes = "card"
            if 'tmid' in msg:
                classes += ' response'
            f.write(f'<div class="{classes}" style="border-left: 4px solid hsl({colorval}, 100%, 50%)">'
                    + f'<h2>{name} ({ts})</h2>'
                    + html.escape(content).replace("\n", "<br>\n")
                    + '</div>\n')
        f.write(f'</div>\n'
                f'</body>\n'
                f'</html>\n')
    print('=== Done ===')


if __name__ == '__main__':
    main()

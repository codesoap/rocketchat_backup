#!/usr/bin/env python3

from rocketchat_backup import dump_html

room = {'t': 'c', 'name': 'biketalk'}
threaded_msgs = [
    {
        'u': {'name': 'Bob'},
        'ts': '2023-10-13T08:32:16.81Z',
        'msg': 'Hi all!'
    },
    {
        'u': {'name': 'Alice'},
        'ts': '2023-10-13T08:32:21.14Z',
        'msg': 'Hi Bob!',
        'tmid': 'smth'
    },
    {
        'u': {'name': 'Eugene'},
        'ts': '2023-10-13T08:32:24.31Z',
        'msg': 'Greetings',
        'tmid': 'smth'
    },
    {
        'u': {'name': 'Bob'},
        'ts': '2023-10-13T08:33:52.87Z',
        'msg': '',
        'attachments': [
            {
                'title': 'my_new_bike.jpg',
                'description': "That's my new beauty. What do you think?"
            }
        ]
    },
    {
        'u': {'name': 'Alice'},
        'ts': '2023-10-13T08:33:59.71Z',
        'msg': 'Nice.',
        'tmid': 'smth'
    },
    {
        'u': {'name': 'Eugene'},
        'ts': '2023-10-13T08:34:22.76Z',
        'msg': 'Real nice.',
        'tmid': 'smth'
    },
    {
        'u': {'name': 'Alice'},
        'ts': '2023-10-13T08:34:02.95Z',
        'msg': "Let's see Paul's bike.",
    },
]

dump_html(room, threaded_msgs, 'demo')

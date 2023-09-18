#!/usr/bin/env python3

import discord, code
import os
from pprint import pprint as pp
from pprint import pformat as pf

import datetime

from consensus_date_parsing import parse_date

import sys, inspect
def dbg(message):
    sys.stderr.write(f"[Line {inspect.currentframe().f_back.f_lineno}] {message}\n")

import load_env
load_env.load()

import asyncio
save_lock = asyncio.Lock()

# Things that need to be saved for persistence
parties = {}               # party name : party
waiting_message_refs = {}  # ref : party name
thumbs_message_refs = {}   # ref : party name

import json
import tempfile
async def save_state():
    async with save_lock:
        serialized_parties = {k: {**v, 'attendant_ids': list(v['attendant_ids'])} for k, v in parties.items()}
        serialized_waiting_refs = {f"{ref.message_id}-{ref.channel_id}-{ref.guild_id}": v for ref, v in waiting_message_refs.items()}
        serialized_thumbs_refs = {f"{ref.message_id}-{ref.channel_id}-{ref.guild_id}": v for ref, v in thumbs_message_refs.items()}
        
        data = {
            "parties": serialized_parties,
            "waiting_message_refs": serialized_waiting_refs,
            "thumbs_message_refs": serialized_thumbs_refs,
            "timestamp": int(datetime.datetime.now().timestamp())
        }
        
        with tempfile.NamedTemporaryFile('w', dir='.', delete=False) as f:
            json.dump(data, f)
        
        os.rename(f.name, 'saved-state.json')

async def load_state():
    try:
        with open('saved-state.json', 'r') as f:
            data = json.load(f)
        
        deserialized_parties = {k: {**v, 'attendant_ids': set(v['attendant_ids'])} for k, v in data['parties'].items()}
        deserialized_waiting_refs = {discord.MessageReference(message_id=int(mid), channel_id=int(cid), guild_id=int(gid)): v 
                                     for k, v in data['waiting_message_refs'].items() 
                                     for mid, cid, gid in [k.split('-')]}
        deserialized_thumbs_refs = {discord.MessageReference(message_id=int(mid), channel_id=int(cid), guild_id=int(gid)): v 
                                    for k, v in data['thumbs_message_refs'].items() 
                                    for mid, cid, gid in [k.split('-')]}
        
        dbg(f"Loaded state from epoch {data['timestamp']}. Parties: {len(deserialized_parties)}, Waiting refs: {len(deserialized_waiting_refs)}, Thumbs refs: {len(deserialized_thumbs_refs)}")
        
        return deserialized_parties, deserialized_waiting_refs, deserialized_thumbs_refs
    except FileNotFoundError:
        dbg("No save state file - starting fresh")
        return {}, {}, {}

intents = discord.Intents.default()
intents.message_content = True
#intents.reactions = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    global parties, waiting_message_refs, thumbs_message_refs
    parties, waiting_message_refs, thumbs_message_refs = await load_state()
    dbg(f'Logged in as {client.user}')

def message_references_equal(l: list):
    #dbg(l)
    if len(l) == 0: return None
    mid = l[0].message_id;
    cid = l[0].channel_id;
    gid = l[0].guild_id;
    for i in range(len(l)-1):
        if mid != l[i+1].message_id: return False
        if cid != l[i+1].channel_id: return False
        if gid != l[i+1].guild_id: return False
    return True

def bot_is_mentioned_in(message):
    fake_index = 99999999
    ret = {'string': '', 'index': fake_index}
    if client.user.mentioned_in(message):
        s = f'<@{str(client.user.id)}>'
        # For some reason `... in message.content` triggers Python
        #   complains about Message not being an iterable, even
        #   if you put `message.content` in parentheses... IDKWTF
        dereferenced_content = str(message.content)
        if s not in dereferenced_content and message.type == discord.MessageType.reply:
            #return {'string': 'reply', 'index': message.reference.message_id}
            # Actually the full ref is better, includes guild & channel
            #   but sadly not an int
            return {'string': 'reply', 'index': message.reference}
        i = message.content.index(s)
        if i < ret['index']:
            ret = {'string': s, 'index': i}
        if i == 0:
            return ret
    for r in message.role_mentions:
        if client.user in r.members:
            s = f'<@&{str(r.id)}>'
            i = fake_index
            if s in message.content:
                i = message.content.index(s)
            if i < ret['index']:
                ret = {'string': s, 'index': i}
            if i == 0:
                return ret
    if ret['index'] == fake_index:
        return False
    return ret

def valid_party_creation(message, mention):
    """Make sure the message is in a valid format - @bot[:] invite @a[,][ and]
    @... to event name is the rest of the message"""

    remaining = message.content
    #dbg(remaining)

    def strip_mandatory(man_str, in_str):
        #dbg(in_str.startswith(man_str), in_str[len(man_str):])
        if not in_str.startswith(man_str):
            return False
        else:
            return in_str[len(man_str):]

    #dbg(pf([mention['string'], strip_mandatory(mention['string'], remaining)]))
    #dbg(pf([mention['string'], strip_mandatory('asd', remaining)]))
    if False == (remaining := strip_mandatory(mention['string'], remaining)):
        return False
    #dbg(remaining)
    
    def strip_optional(opt_str, in_str):
        if in_str.startswith(opt_str):
            return in_str[len(opt_str):]
        return in_str

    remaining = strip_optional(':', remaining)
    #dbg(remaining)
    
    if False == (remaining := strip_mandatory(' invite', remaining)):
        return False
    #dbg(remaining)

    attendant_ids = []

    while remaining.startswith(' <@'):
        if '>' not in remaining[3:]:
            return False
        userstr = remaining[3:remaining.index('>')]
        if not userstr.isdigit():
            return False
        attendant_ids.append(int(userstr))
        if False == (remaining := strip_mandatory(f' <@{userstr}>', remaining)):
            return False
        remaining = strip_optional(',', remaining)
        remaining = strip_optional(' and', remaining)

    if attendant_ids == []:
        return False

    if False == (remaining := strip_mandatory(' to ', remaining)):
        return False

    if len(remaining) == 0:
        return False

    return {
            'organizer_id': message.author.id,
            'attendant_ids': set(attendant_ids),
            'proposed_time': None,
            'channel_id': message.channel.id,
            'name': remaining
            }

def ask_party_time_message(pName):
    return '<@' + str(parties[pName]['asshole_id']) + '>, reply to this message with a datetime when you want this to happen:\n' + pName

def poll_message_content(party):
    # TODO
    return 'placeholder text for poll_message_content' + pf(party)

@client.event
async def on_message(message):
    if message.author == client.user: return
    # if message.content.startswith('eval() this: '):
    #     evalstring = message.content[len('eval() this: '):]
    #     await message.channel.send(
    #             '```\n' + 
    #             str(eval(evalstring)) +
    #             '\n```'
    #             )
    if not (mention := bot_is_mentioned_in(message)):
        # dbg(f'Not mentioned in: {message.content}')
        return
    if mention['string'] == 'reply':
        # Assume this is a reply to 'when' message until I figure out how to get the id
        #replied_to_message = await message.channel.fetch_message(mention['index'])
        #dbg( mention['index'] in waiting_message_refs, mention['index'], waiting_message_refs)
        ## REEEE ^^^ this doesn't work even if they have identical mId cId and gId ... sad
        for k in list(waiting_message_refs.keys()):
            if message_references_equal([message.reference, k]):
                party = parties[waiting_message_refs[k]]
                channel = await client.fetch_channel(party['channel_id'])
                consensus, detail, text = parse_date(message.content)
                
                if consensus is True:
                    party['proposed_time'] = list(detail['success'].values())[0]
                    sent_message = await channel.send(
                        content=poll_message_content(party),
                        reference=message
                    )
                    thumbs_message_refs[discord.MessageReference(
                        message_id = sent_message.id,
                        channel_id = sent_message.channel.id,
                        guild_id   = sent_message.guild.id
                    )] = party['name']
                    await sent_message.add_reaction('👍')
                    await sent_message.add_reaction('👎')
                    party['state_annotation'] = 'waiting for thumbs' # Don't worry, we're about to save
                    party['asshole_id'] = None

                    # Remove wait refs
                    keys_to_remove = [k for k, v in waiting_message_refs.items() if v == party['name']]
                    for key in keys_to_remove:
                        del waiting_message_refs[key]
                else:
                    sent_message = await channel.send(
                        content=text,
                        reference=message
                    )
                    waiting_message_refs[discord.MessageReference(
                        message_id = sent_message.id,
                        channel_id = sent_message.channel.id,
                        guild_id   = sent_message.guild.id
                    )] = party['name']
                await save_state()
                return
    if not (party := valid_party_creation(message, mention)):
        #dbg('ignoring ' + str(message) + ' because not valid party creation')
        return
    if party['name'] in parties:
        await message.reply(f'"{party["name"]}" is the name of an exising party')
        return
    party['asshole_id'] = party['organizer_id']
    party['state_annotation'] = 'asshole detected' # This is a very temporary state, hence no save
    parties[party['name']] = party
    channel = await client.fetch_channel(party['channel_id'])
    sent_message = await channel.send(
            content=ask_party_time_message(party['name']), 
            reference=message
            )
    waiting_message_refs[discord.MessageReference(
        message_id = sent_message.id, 
        channel_id = sent_message.channel.id, 
        guild_id   = sent_message.guild.id
        )] = party['name']
    #dbg(sent_message.reference.message_id)
    party['state_annotation'] = f'waiting on asshole {party["asshole_id"]}'
    await save_state()
    return

@client.event
async def on_raw_reaction_add(reactionEvent):
    if reactionEvent.emoji.name in "👍👎" and reactionEvent.user_id != client.user.id:
        # dbg('it was a thumbs and not self')
        reactedMessageRef = discord.MessageReference(
            message_id=reactionEvent.message_id,
            channel_id=reactionEvent.channel_id,
            guild_id=reactionEvent.guild_id
        )
        # dbg(f'{str(reactionEvent.message_id)} vs {reactedMessageRef} vs {pf(thumbs_message_refs)}')
        for k in list(thumbs_message_refs.keys()):
            if message_references_equal([reactedMessageRef, k]):
                party = parties[thumbs_message_refs[k]]
                channel = await client.fetch_channel(party['channel_id'])
                if reactionEvent.emoji.name == "👎":
                    party['asshole_id'] = reactionEvent.member.id
                    party['state_annotation'] = 'asshole detected'
                    channel = await client.fetch_channel(party['channel_id'])
                    sent_message = await channel.send(
                            content=ask_party_time_message(party['name'])
                            )
                    waiting_message_refs[discord.MessageReference(
                        message_id = sent_message.id, 
                        channel_id = sent_message.channel.id, 
                        guild_id   = sent_message.guild.id
                        )] = party['name']
                    #dbg(sent_message.reference.message_id)
                    party['state_annotation'] = f'waiting on asshole {party["asshole_id"]}'
                    await save_state()
                    return
                dbg('was not a thumbs down')

                # dbg('and in refs')
                await client.get_partial_messageable(reactionEvent.channel_id).send(
                    '<@' + str(reactionEvent.user_id) + '> just opined on my poll'
                    )


client.run(os.environ.get('DISCORD_AUTH_TOKEN'))

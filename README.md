# schedules-and-schonflicts

## Is this ready to go?

Janky but it works

## What's it supposed to do?

The best implimentation of the worst scheduling consensus system:  
When someone says they can't make it, the onus is on them to propose a later time.  
Repeat until all parties can make it ... possibly never!

## Setup

- Find instructions on how to make a discord bot, get to the point where you have a token.
- ```bash
  K=DISCORD_AUTH_TOKEN; read -p "$K=" && echo "$K=$REPLY" > $K.env`\
  virtualenv venv
  source ./venv/bin/activate
  pip install -r requirements.txt
  ```
- I like making it reload on save when developing:  
  ```bash
  while true; do ./s-n-s-bot.py & inotifywait -e modify s-n-s-bot.py; kill $(jobs -p); done
  ```
- Alternatuvely make it a service:
  ```bash
  sudo ./systemd-service-generator.sh ${PWD##*/} "$PWD/venv/bin/python $PWD/s-n-s-bot.py"
  ```

## How do I ivoke the bot?

**Alice:** `@🤖`, invite `@Alice`, `@Bob`, and `@Charlie` to Hangout after work  
The bot will guide you through the rest - starting with asking the organizer `@Alice` to propose a time, 

## Progress

- Waits for messages similar to:  
  "`@bot-user`, invite `@user1`, `@user2`, [...], and `@userN` to Arbitrary text name of an event
- Makes the person who said ^^^ that the organizer and current party asshole
- Asks the asshole when is a good time for the party
- Wait for replies to the "when" message
- Parse the reply as a date 5 different ways and hope for consensus
- If no date consensus, ask the asshole again (and wait for replies on both messages)
- If date consensus, send a confirmation message and add thumbs reactions
- Wait for thumbs to be added on
- On a thumbs down, that user is the new asshole and must propose a new time
- On final thumbs up it pings everyone and destroys the party

## TODO

- [ ] Save and load to `saved-*.json`
  - [ ] TODO: On load go over watched messages and sync state to reality in case activity was missed
- [ ] Edit old messsages to reflect that they're no longer actively watched
- [ ] gCal API
  - [ ] associate a calendar with each user
  - [ ] TODO: 1 user can have many calendars mapped to specific ... events matching regex?
- [ ] Edit thumbs messages to say "Still waiting on [@user, ...]" when thumbs are modified
- [ ] Some incantation that can be used to destroy the party... maybe reply to the "when" message with "never"
- [ ] Complain if a new date is not later than the old date, but succumb if it's repeated twice in a row
# schedules-and-schonflicts

## Is this ready to go?

Nope, WIP.


## What's it supposed to do?

Here's a user story:

FYI trying to implement the best worst scheduling system in the world, e.g.:  
A: /event "poopoo party" with @A @B @C  
Bot: Okay, when?  
A: Monday  
Bot: A invites you to "poopoo party" at 00:00:00 Eastern Time on Monday July 31st 2023 - @A @B @C  
Bot: {reacts 👍 👎  to self}  
A: No, wait, that's not what I meant {reacts 👎 }  
Bot: @A you piece of shit, if you can't make it to "poopoo party" at 00:00:00 Eastern Time on Monday July 31st 2023 then what time is good for you?  
A: 18:00 Monday  
Bot: A invites you to "poopoo party" at 18:00:00 Eastern Time on Monday July 31st 2023 - @A @B @C  
Bot: {reacts 👍 👎  to self}  
[...]  
B: {reacts 👎 }  
Bot: @B you piece of shit, if you can't make it to "poopoo party" at 18:00:00 Eastern Time on Monday July 31st 2023 then what time is good for you?  
... and so on until everyone 👍


## Progress so far

- Waits for messages similar to:  
  "@bot-user, invite @user1, @user2, [...], and @userN to Arbitrary text name of an event
- Makes the person who said ^^^ that the party asshole
- Asks the asshole when is a good time for the party
- Wait for replies to the ask message
- Parse the reply as a date 5 different ways and hope for consensus
- If no date consensus, ask the asshole again (and wait for replies on both messages)
- If date consensus, send a confirmation message and add thumbs reactions
- Wait for thumbs to be added on
- On a thumbs down, that user is the new asshole
- NEXT: thumbs up logic


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


## TODO

- Save and load to `saved-*.json`
  - TODO: On load go over watched messages and sync state to reality in case activity was missed
- Edit old messsages to reflect that they're no longer actively watched
- gCal API
  - associate a calendar with each user
  - TODO: 1 user can have many calendars mapped to specific ... events matching regex?
- Edit thumbs messages to say "Still waiting on [@user, ...]" when thumbs are modified

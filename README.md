# True Sight Discord Bot

## Current status
    - The bot registers summoner names and tries to fetch Riot Api data
    - **Sadly the bot currently fails to resolve `api.riotgames.com` because of DNS issues on my local network**
    - This results in massive connection errors and the bot cannot get summoner info or any game data at the moment

## The known issue
    - DNS queries are routed to an ipv6 dns server which doesnt resolve riots api domain properly
    - Because of this all http requests to riots api fail with dns lookup errors

## Planned steps

    - Investigate and fix the dns issue (arealy spent a good few hours working on that with no solution)
    - Once it works, fully test the bots riot api integration
    - Add proper error handling
    - Improve bot commands and choice between polish and english
    - Publish a working version, for now its work in progress

---

** If you come by any problems trying to make your own similar discord bot or encounter any problems while trying to use mine (once its actually works), feel free to message me with any question and ill try to help you :33

---

Thanks for your patience and support guys
import discord, json, requests, os, httpx, base64, time, subprocess
from discord.ext import commands, tasks
from colorama import Fore, init
from discord.utils import get
import datetime
from datetime import datetime
from cgitb import text
init(convert=True)

from builtins import *

bot = discord.Bot(intents=discord.Intents.all())
settings = json.load(open("settings.json", encoding="utf-8"))
products = json.load(open("products.json", encoding="utf-8"))
redeemer = open("apps/redeemer.txt" , 'r').read()
boostool = open("apps/boostool.txt" , 'r').read()
sms = open("apps/sms.txt" , 'r').read().splitlines
onliner = open("apps/onliner.txt" , 'r').read().splitlines


guild = settings["guildId"]
sellixchannel = settings["sellixchannel"]
sellappchannel = settings["sellappchannel"]
owner = settings["owner"]
invitefield = "invite:"


@bot.event
async def on_message(message):  # sellix API.
    names = []
    values = []

    invite = ""

    if str(message.channel.id) == str(sellixchannel):

        for emb in message.embeds:
            for field in emb.fields:
                names.append(field.name)
                values.append(field.value)

                if field.name == invitefield:
                    invite = field.value

            for i in range(len(names)):
                name = names[i]

                if name.lower() == "product" and invite:

                    INVITE = invite.replace("//", "")

                    if "/invite/" in INVITE:
                        INVITE = INVITE.split("/invite/")[1]

                    elif "/" in INVITE:
                        INVITE = INVITE.split("/")[1]

                    if products[values[i]]:

                        jsondict = products[values[i]]

                        boosts = int(jsondict["boosts"])
                        months = int(jsondict["months"])

                        embed = discord.Embed(
                            title="**Sell.App**", description=f"Sell.App order received; boosting https://discord.gg/{INVITE} {boosts} times", timestamp=datetime.now(), color=0x0000FF)

                        msg = await message.channel.send(embed=embed)

                        autoboost(owner, INVITE, boosts)

                        embed2 = discord.Embed(
                            title="**Finished**", description=f"Finished Boosting https://discord.gg/{INVITE} x{boosts} times", timestamp=datetime.now(), color=discord.Colour.blue())
                            
                        await msg.reply(embed=embed2)

    ### Sell.App AutoBoosting
    # Checking if channel matches 
    if str(message.channel.id) == str(sellappchannel):

        # Iterating through embeds
        for embed in message.embeds:

            # Verifying that it is a boosting product
            if "Order Completed" in embed.title:

                # Checking all products
                for product in products:
                    if embed.fields[0] == product:

                        # Getting invite
                        invite = None
                        for field in embed.fields:
                            if field.name == "invitecode:":
                                invite = field.value
                        
                        # Boosting
                        if invite:

                            # Formatting invite
                            INVITE = invite.replace("//", "")
                            if "/invite/" in INVITE:
                                INVITE = INVITE.split("/invite/")[1]
                            elif "/" in INVITE:
                                INVITE = INVITE.split("/")[1]

                            # Getting variables
                            jsondict = products[embed.fields[0]]
                            boosts = int(jsondict["boosts"])
                            months = int(jsondict["months"])

                            # Sending first embed
                            embed = discord.Embed(
                                title="**Sell App**", 
                                description=f"SellApp order received; boosting https://discord.gg/{INVITE} {boosts} times", 
                                timestamp=datetime.now(), 
                                color=0x80000FF
                            )
                            msg = await message.channel.send(embed=embed)

                            # Boosting
                            autoboost(owner, INVITE, boosts)

                            # Sending final embed
                            embed2 = discord.Embed(
                                title="**Finished**", 
                                description=f"Finished Boosting https://discord.gg/{INVITE} x{boosts} times", 
                                timestamp=datetime.now(), 
                                color=discord.Colour.blue()
                            )    
                            await msg.reply(embed=embed2)


if not os.path.isfile("used.json"):
    used = {}
    json.dump(used, open("used.json", "w", encoding="utf-8"), indent=4)

used = json.load(open("used.json"))

@bot.event
async def on_ready():
    print("")

def is_licensed(target):
    try:
        open(f"{target}.txt", "r")
        return True
    except FileNotFoundError:
        return False


def isAdmin(ctx):
    return str(ctx.author.id) in settings["botAdminId"]


def isWhitelisted(ctx):
    return str(ctx.author.id) in settings["botWhitelistedId"]

def makeUsed(token: str):
    data = json.load(open('used.json', 'r'))
    with open('used.json', "w") as f:
        if data.get(token): return
        data[token] = {
            "boostedAt": str(time.time()),
            "boostFinishAt": str(time.time() + 30 * 86400)
        }
        json.dump(data, f, indent=4)


def removeToken(user, token: str):
    with open(f'{user}.txt', "r") as f:
        Tokens = f.read().split("\n")
        for t in Tokens:
            if len(t) < 5 or t == token:
                Tokens.remove(t)
        open(f'{user}.txt', "w").write("\n".join(Tokens))

def runBoostshit(user: int, invite: str, amount: int, EXP: bool, bio: str, nick: str):
    if amount % 2 != 0:
        amount += 1
    tokens = get_all_tokens(f'{user}.txt')
    all_data = []
    tokens_checked = 0
    actually_valid = 0
    boosts_done = 0
    nesto = 0
    for token in tokens:
        s, headers = get_headers(token)
        profile = validate_token(s, headers)
        tokens_checked += 1

        if profile != False:
            actually_valid += 1
            data_piece = [s, token, headers, profile]
            all_data.append(data_piece)
            print(f"{Fore.GREEN} > {Fore.WHITE}{profile}")
        else:
            pass
    for data in all_data:
        if boosts_done >= amount:
            return
        s, token, headers, profile = get_items(data)
        boost_data = s.get(f"https://discord.com/api/v9/users/@me/guilds/premium/subscription-slots", headers=headers)
        if boost_data.status_code == 200:
            if len(boost_data.json()) != 0:
                join_outcome, server_id = do_join_server(s, token, headers, profile, invite, bio, nick)
                if join_outcome:
                    for boost in boost_data.json():

                        if boosts_done >= amount:
                            removeToken(user, token)
                            if EXP:
                                makeUsed(token)
                            return
                        boost_id = boost["id"]
                        bosted = do_boost(s, token, headers, profile, server_id, boost_id)
                        if bosted:
                            print(f"{Fore.GREEN} > {Fore.WHITE}{profile} {Fore.MAGENTA}BOOSTED {Fore.WHITE}{invite}")
                            boosts_done += 1
                        else:
                            print(f"{Fore.GREEN} > {Fore.WHITE}{profile} {Fore.RED}ERROR BOOSTING {Fore.WHITE}{invite}")
                    removeToken(user, token)
                    if EXP:
                        makeUsed(token)
                else:
                    print(f"{Fore.RED} > {Fore.WHITE}{profile} {Fore.RED}Error joining {invite}")

            else:
                removeToken(user, token)
                print(f"{Fore.GREEN} > {Fore.WHITE}{profile} {Fore.RED}BROKE ASS DONT GOT NITRO")



    
    
no_perms = discord.Embed(title="**???? | Access Denied**", description="You dont have permissions to do this", timestamp=datetime.now(), color=discord.Colour.red())





    
@bot.slash_command(name="activity", description="") 
async def activity(ctx, activity=discord.Option(str, "activity", required=True)):
    if not is_licensed(ctx.author.id):
        await ctx.respond(embed=no_perms, ephemeral=True)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=activity))
    await ctx.respond(f"Changed Activity to {activity}")




@bot.slash_command(name="stock", description="")
async def stock(ctx: discord.ApplicationContext):
    if not is_licensed(ctx.author.id):
        await ctx.respond(embed=no_perms, ephemeral=True)
    if is_licensed(ctx.author.id):
        return await ctx.respond(f"{len(open(f'{ctx.author.id}.txt', encoding='utf-8').read().splitlines()) * 2} boost in stock lol")
   

@bot.slash_command(name="key", description="Generates a Key for Any Application given")
async def key(ctx: discord.ApplicationContext,
                application: discord.Option(str, "EX: Redeemer | Boost Tool | Onliner | SMS-Verifyer ", required=True),
                expire: discord.Option(str, "EX: Lifetime | 1d | 1w | 1m | 1y", required=True),
                amount: discord.Option(int, "EX: 1 | 2 | 3 | 4 | 5 | ETC", required=False)):
    if not is_licensed(ctx.author.id):
       await ctx.respond(embed=no_perms, ephemeral=True)
    if application == "Redeemer" or "redeemer":
       embed=discord.Embed(title=f"Key-Gen", description=f">>>   Application: `{application}` \n Ex: `{expire}` \n Amount: `{amount}` \n key: `Check Dms`", color=0x00000)
    await ctx.send(embed=embed)
    StopIteration
    if application == "Boost Tool" and "boostool":
       embed=discord.Embed(title=f"Key-Gen", description=f">>>   Application: `{application}` \n Ex: `{expire}` \n Amount: `{amount}` \n key: `Check Dms`", color=0x00000)
    await ctx.send(embed=embed)
    StopIteration
    if application == "Onliner" and "onliner":
       embed=discord.Embed(title=f"Key-Gen", description=f">>>   Application: `{application}` \n Ex: `{expire}` \n Amount: `{amount}` \n key: `Check Dms`", color=0x00000)
    await ctx.send(embed=embed)
    StopIteration
    if application == "SMS-Verifyer" and "sms":
       embed=discord.Embed(title=f"Key-Gen", description=f">>>   Application: `{application}` \n Ex: `{expire}` \n Amount: `{amount}` \n key: `Check Dms`", color=0x00000)
    await ctx.send(embed=embed)
    StopIteration
    





@bot.slash_command(name="restock", description="")
async def restock(ctx: discord.ApplicationContext,
                  code: discord.Option(str, "..", required=True)):
    if not is_licensed(ctx.author.id):
        await ctx.respond(embed=no_perms, ephemeral=True)

    code = code.replace("https://paste.ee/p/", "")

    temp_stock = requests.get(f"https://paste.ee/d/{code}", headers={
        "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.61 Safari/537.36"}).text

    f = open(f"{ctx.author.id}.txt", "a", encoding="utf-8")
    f.write(f"{temp_stock}\n")
    f.close()

    embed = discord.Embed(title=f"Restocked",
                          description=f" have a total of {len(open(f'{ctx.author.id}.txt', encoding='utf-8').read().splitlines())} Tokens ",
                          color=0x60a561)
    await ctx.respond(embed=embed, ephemeral=True)

@bot.slash_command(name="boost",
                   description="..")
async def boost(ctx: discord.ApplicationContext,
                invitecode: discord.Option(str, "..", required=True),
                amount: discord.Option(int, "..", required=True),
                days: discord.Option(int, "...", required=True),
                bio: discord.Option(str, "bio", required=True),
                nick: discord.Option(str, "nicknames", required=True)):
    if not is_licensed(ctx.author.id):
        return await ctx.respond(".")

    if days != 30 and days != 90:
        return await ctx.respond("*The number of days can only be 30 or 90.*")
    emoji = discord.utils.get(bot.emojis, name='pbj1')
    await ctx.respond(f"Started boosting {amount}/{amount}'s")
    

    
    


    INVITE = invitecode.replace("//", "")
    if "/invite/" in INVITE:
        INVITE = INVITE.split("/invite/")[1]

    elif "/" in INVITE:
        INVITE = INVITE.split("/")[1]

    dataabotinvite = httpx.get(f"https://discord.com/api/v9/invites/{INVITE}").text

    if '{"message": "Unknown Invite", "code": 10006}' in dataabotinvite:
        print(f"{Fore.RED}discord.gg/{INVITE} is invalid")
        return await ctx.edit("The invite link you provided is invalid!")
    else:
        print(f"{Fore.GREEN}discord.gg/{INVITE} appears to be a valid server")

    EXP = True
    if days == 90:
        EXP = False
    kk = ctx.author.id
    runBoostshit(kk, INVITE, amount, EXP, bio, nick)
    await ctx.respond(f"Finsihed boosting {amount}/{amount}'s")

@bot.slash_command(name="license",
                   description="..")
async def add_license(ctx: discord.ApplicationContext, targetid: discord.Option(str, "...", required=True)):
    if isAdmin(ctx):
        if not is_licensed(targetid):
            open(f"{targetid}.txt", "w")
            await ctx.respond(f"<@!{targetid}> Licensed ")
        else:
            await ctx.respond(f"<@!{targetid}> is already Licensed")
                                 
           


@bot.slash_command(name="remove",
                   description="")
async def remove_license(ctx: discord.ApplicationContext, targetid: discord.Option(str, "Target ID.", required=True)):
    if isAdmin(ctx):
        if is_licensed(ctx.author.id):
            os.remove(f"{targetid}.txt")
            await ctx.respond(f"<@!{targetid}> Removed license")
            print(f"Attempting to License ({targetid}) in ({guild})")
        else:
            await ctx.respond(f"<@!{targetid}> is not licensed")



def get_super_properties():
    properties = '''{"os":"Windows","browser":"Chrome","device":"","system_locale":"en-GB","browser_user_agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36","browser_version":"95.0.4638.54","os_version":"10","referrer":"","referring_domain":"","referrer_current":"","referring_domain_current":"","release_channel":"stable","client_build_number":102113,"client_event_source":null}'''
    properties = base64.b64encode(properties.encode()).decode()
    return properties


def get_fingerprint(s):
    try:
        fingerprint = s.get(f"https://discord.com/api/v9/experiments", timeout=5).json()["fingerprint"]
        return fingerprint
    except Exception as e:
         # print(e)
        return "Error"


def get_cookies(s, url):
    try:
        cookieinfo = s.get(url, timeout=5).cookies
        dcf = str(cookieinfo).split('__dcfduid=')[1].split(' ')[0]
        sdc = str(cookieinfo).split('__sdcfduid=')[1].split(' ')[0]
        return dcf, sdc
    except:
        return "", ""


def get_proxy():
    return None  # can change if problems occur


def get_headers(token):
    while True:
        s = httpx.Client(proxies=get_proxy())
        dcf, sdc = get_cookies(s, "https://discord.com/")
        fingerprint = get_fingerprint(s)
        if fingerprint != "Error":  # Making sure i get both headers
            break

    super_properties = get_super_properties()
    headers = {
        'authority': 'discord.com',
        'method': 'POST',
        'path': '/api/v9/users/@me/channels',
        'scheme': 'https',
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate',
        'accept-language': 'en-US',
        'authorization': token,
        'cookie': f'__dcfduid={dcf}; __sdcfduid={sdc}',
        'origin': 'https://discord.com',
        'sec-ch-ua': '"Google Chrome";v="95", "Chromium";v="95", ";Not A Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36',

        'x-debug-options': 'bugReporterEnabled',
        'x-fingerprint': fingerprint,
        'x-super-properties': super_properties,
    }

    return s, headers


def find_token(token):
    if ':' in token:
        token_chosen = None
        tokensplit = token.split(":")
        for thing in tokensplit:
            if '@' not in thing and '.' in thing and len(
                    thing) > 30:  # trying to detect where the token is if a user pastes email:pass:token (and we dont know the order)
                token_chosen = thing
                break
        if token_chosen == None:
            print(f"Error finding token", Fore.RED)
            return None
        else:
            return token_chosen


    else:
        return token


def get_all_tokens(filename):
    all_tokens = []
    with open(filename, 'r') as f:
        for line in f.readlines():
            token = line.strip()
            token = find_token(token)
            if token != None:
                all_tokens.append(token)

    return all_tokens


def validate_token(s, headers):
    check = s.get(f"https://discord.com/api/v9/users/@me", headers=headers)

    if check.status_code == 200:
        profile_name = check.json()["username"]
        profile_discrim = check.json()["discriminator"]
        profile_of_user = f"{profile_name}#{profile_discrim}"
        return profile_of_user
    else:
        return False




def do_member_gate(s, token, headers, profile, invite, server_id):
    outcome = False
    try:
        member_gate = s.get(
            f"https://discord.com/api/v9/guilds/{server_id}/member-verification?with_guild=false&invite_code={invite}",
            headers=headers)
        if member_gate.status_code != 200:
            return outcome
        accept_rules_data = member_gate.json()
        accept_rules_data["response"] = "true"

        # del headers["content-length"] #= str(len(str(accept_rules_data))) #Had too many problems
        # del headers["content-type"] # = 'application/json'  ^^^^

        accept_member_gate = s.put(f"https://discord.com/api/v9/guilds/{server_id}/requests/@me", headers=headers,
                                   json=accept_rules_data)
        if accept_member_gate.status_code == 201:
            outcome = True

    except:
        pass

    return outcome
    
    
def do_join_server(s, token, headers, profile, invite, bio,nick):
    join_outcome = False;
    server_id = None
    try:
        # headers["content-length"] = str(len(str(server_join_data)))
        headers["content-type"] = 'application/json'

        for i in range(15):
            try:
                createTask = httpx.post("https://api.capmonster.cloud/createTask", json={
                    "clientKey": settings["capmonsterKey"],
                    "task": {
                        "type": "HCaptchaTaskProxyless",
                        "websiteURL": "https://discord.com/channels/@me",
                        "websiteKey": "76edd89a-a91d-4140-9591-ff311e104059"
                    }
                }).json()["taskId"]

                print(f"Captcha Task: {createTask}")

                getResults = {}
                getResults["status"] = "processing"
                while getResults["status"] == "processing":
                    getResults = httpx.post("https://api.capmonster.cloud/getTaskResult", json={
                        "clientKey": settings["capmonsterKey"],
                        "taskId": createTask
                    }).json()

                    time.sleep(1)

                solution = getResults["solution"]["gRecaptchaResponse"]

                print(f"Captcha Solved")

                join_server = s.post(f"https://discord.com/api/v9/invites/{invite}", headers=headers, json={
                    "captcha_key": solution
                })
                server_id = join_server.json()["guild"]["id"]
                requests.patch(url="https://discord.com/api/v9/users/@me", headers= {"authorization": token}, json = {"bio": bio} )
                requests.patch(url=f"https://discord.com/api/v9/guilds/{server_id}/members/@me",headers= {"authorization": token}, json = {"nick": nick})

                break
            except:
                pass

        server_invite = invite
        if join_server.status_code == 200:
            join_outcome = True
            server_name = join_server.json()["guild"]["name"]
            server_id = join_server.json()["guild"]["id"]
            print(f"{Fore.GREEN} > {Fore.WHITE}{profile} {Fore.GREEN}> {Fore.WHITE}{server_invite}")
        else:
            print(join_server.text)
    except:
        pass

    return join_outcome, server_id
  

def do_boost(s, token, headers, profile, server_id, boost_id):
    boost_data = {"user_premium_guild_subscription_slot_ids": [f"{boost_id}"]}
    headers["content-length"] = str(len(str(boost_data)))
    headers["content-type"] = 'application/json'

    boosted = s.put(f"https://discord.com/api/v9/guilds/{server_id}/premium/subscriptions", json=boost_data,
                    headers=headers)
    if boosted.status_code == 201:
        return True
    else:
        return False


def get_invite():
    while True:
        print(f"{Fore.CYAN}Server invite?", end="")
        invite = input(" > ").replace("//", "")

        if "/invite/" in invite:
            invite = invite.split("/invite/")[1]

        elif "/" in invite:
            invite = invite.split("/")[1]

        dataabotinvite = httpx.get(f"https://discord.com/api/v9/invites/{invite}").text

        if '{"message": "Unknown Invite", "code": 10006}' in dataabotinvite:
            print(f"{Fore.RED}discord.gg/{invite} is invalid")
        else:
            print(f"{Fore.GREEN}discord.gg/{invite} appears to be a valid server")
            break

    return invite


def get_items(item):
    s = item[0]
    token = item[1]
    headers = item[2]
    profile = item[3]
    return s, token, headers, profile


def autojoin(s, token, headers, profile, invite):
    join_outcome = False
    server_id = None
    try:
        # headers["content-length"] = str(len(str(server_join_data)))
        headers["content-type"] = 'application/json'

        for i in range(15):
            try:
                createTask = httpx.post("https://api.capmonster.cloud/createTask", json={
                    "clientKey": settings["capmonsterKey"],
                    "task": {
                        "type": "HCaptchaTaskProxyless",
                        "websiteURL": "https://discord.com/channels/@me",
                        "websiteKey": "76edd89a-a91d-4140-9591-ff311e104059"
                    }
                }).json()["taskId"]

                print(f"[-] Captcha Detected, Solving")

                getResults = {}
                getResults["status"] = "processing"
                while getResults["status"] == "processing":
                    getResults = httpx.post("https://api.capmonster.cloud/getTaskResult", json={
                        "clientKey": settings["capmonsterKey"],
                        "taskId": createTask
                    }).json()

                    time.sleep(1)

                solution = getResults["solution"]["gRecaptchaResponse"]

                print(f"[+] Captcha Solved")

                join_server = s.post(f"https://discord.com/api/v9/invites/{invite}", headers=headers, json={
                    "captcha_key": solution
                })

                break
            except:
                pass

        server_invite = invite
        if join_server.status_code == 200:
            join_outcome = True
            server_name = join_server.json()["guild"]["name"]
            server_id = join_server.json()["guild"]["id"]
            print(f"[!] Joined Server - {token[20:]}************")
        else:
            print(join_server.text)
    except:
        pass

    return join_outcome, server_id



def autoboost(user, invite: str, amount: int):
    print("[!] Starting up")
    if amount % 2 != 0:
        amount += 1

    tokens = get_all_tokens(f'{user}.txt')
    all_data = []
    tokens_checked = 0
    actually_valid = 0
    boosts_done = 0
    for token in tokens:
        s, headers = get_headers(token)
        profile = validate_token(s, headers)
        tokens_checked += 1

        if profile != False:
            actually_valid += 1
            data_piece = [s, token, headers, profile]
            all_data.append(data_piece)
        else:
            pass
    for data in all_data:
        if boosts_done >= amount:
            return
        s, token, headers, profile = get_items(data)
        boost_data = s.get(
            f"https://discord.com/api/v9/users/@me/guilds/premium/subscription-slots", headers=headers)
        if boost_data.status_code == 200:
            if len(boost_data.json()) != 0:
                join_outcome, server_id = autojoin(
                    s, token, headers, profile, invite)
                if join_outcome:
                    for boost in boost_data.json():

                        if boosts_done >= amount:
                            removeToken(user, token)
                            return
                        boost_id = boost["id"]
                        bosted = do_boost(s, token, headers,
                                          profile, server_id, boost_id)
                        if bosted:
                            print(
                                f"{Fore.GREEN}[+]Boosted - {token[20:]}******")
                            boosts_done += 1
                        else:
                            print(
                                f"{Fore.RED}[!] Already Boosting another server - {token[20:]}******")
                    removeToken(user, token)
                else:
                    print(
                        f"{Fore.RED}{token}[!] Error joining - {token[20:]}******")

            else:
                removeToken(user, token)
                print(
                    f"{Fore.RED}[!] No Nitro Found On Token - {token[20:]}******")







bot.run(settings["botToken"])
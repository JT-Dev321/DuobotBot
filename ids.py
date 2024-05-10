logchannelid = 954793965696221224

ticketlogchannelid = 599640893552852992
ticketcategory = 657238193896423424
tickethandler = 599640682482892880
ticketarchivecategory = 760517017823346728

auto_response_cats = [657238193896423424, 570721296183197697, 570718686990827530]

staffroleid = 1173264473134477353

ticketchannelmention = "<#1173302179310874784>"
faqchannelmention = "<#863918636778651688>"
autosupchannelmention = "<#1105157686057779300>"
botguidemention = "<#1165717673322221649>"

redcolour = 0xFF0000
darkredcolour = 0x8b0000
orangecolour = 0xFFA500
greencolour = 0x00FF00
darkorangecolour = 0xDC582A
maincolour = 0x3A739C



autoSupportDictionary = {
    "I don't find any tradable TF2 key(s) in your inventory to complete this request." : """
1. Ensure you're using !buytf and no other command
2. Ensure you did not purchase the keys from the steam market within the last 7 days.
""",
    "I don't find any tradable CSGO key(s) in your inventory to complete this request." : """
1. Ensure you're using !buy and no other command
2. Ensure you did not purchase the keys from the steam market within the last 7 days.
3. Ensure you did not trade the keys within the last 7 days.
""",
    "I don't find any tradable HYDRA key(s) in your inventory to complete this request." : """
1. Ensure you're using !buyhydra and no other command
2. Ensure you did not purchase the keys from the steam market within the last 7 days.
3. Ensure you did not trade the keys within the last 7 days.
""",

    'An error occurred while...' : """
Any error beginning like this is an issue with the delay between steam servers and our bots.

**We cannot do anything on our end to solve this issue**, you must wait and try again later. Expect issues like this to clear up within <10 minutes. 
If after that amount of time you are still experiencing the error, check: https://steamstat.us/""",
    
    'There was an error loading your profile as it is private.' : """
Please ensure your privacy page looks like this when trading with the bot to avoid issues: https://i.imgur.com/mpO7Z09.png    

If you are certain your profile is public and are still getting this error, then the error is caused by an issue with the delay between steam servers and our bots.

**We cannot do anything on our end to solve this issue**, you must wait and try again later. Expect issues like this to clear up within <10 minutes. 
If after that amount of time you are still experiencing the error, check: https://steamstat.us/""",
    
    'Processing your request, please hold...' : """
If you are sitting on this message from the bot, and nothing seems to be happening. There is an issue with steam communicating to our bot.

**We cannot do anything on our end to solve this issue**, you must wait and try again later. Expect issues like this to clear up within <10 minutes. 
If after that amount of time you are still experiencing the error, check: https://steamstat.us/"""
}

autoQuestionSupportDictionary = {

"""Which bot do I use for my steam level? / What does the "High" and "Low" in the bot's name mean?""":
    
f"""
Please see {botguidemention}
""",

"What keys does the bot accept?" :
    
"""
List of keys: https://pastebin.com/5cxyRMTb
""",

"Where can I buy the best value keys?":
"""
There are many ways of purchasing keys across a range of payment methods/gateways. The two sites we personally recommend are:
https://marketplace.tf/items/tf2/5021;6
https://cs.deals/market/tf2/Tool/?name=mann%20co&sort=price

*Duobot is not affiliated with these sites in any way*
""",

"Can I have a refund?":
"""
Duobot does not uniformly hand out refunds, instead, each request is reviewed on a case-by-case basis **in one of our support tickets**.

Please do not expect a refund if there has not been a technical fault with one of our bots, we will not refund you if you simply regret a purchase.
""",

"I got less sets/a lower level than expected":
f"""
There are multiples reasons that this may occur:
    - There was a large gap in time between you checking prices and running the buy command (The prices changed in that time)
- You purchased cards while having craftable sets in your inventory
- Other reasons
    
If you would like to request a refund, please open a {ticketchannelmention}
"""
}



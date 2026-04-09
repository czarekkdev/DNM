

#"
# TO DO:
# -----------------------
# proxies
# proxies validating
# webhook sending loop
# threading
# replace base64 encoding with AES cryptography
# -----------------------
# "


# API URLs and configurations
url_discord_gifts = "https://discord.com/api/v9/entitlements/gift-codes/"
url_syskrnl_version = "localhost/version/"
length = 16  # Length of the gift code
gen_cooldown = 0.01  # Cooldown time between code generations
default_settings = """{"launched": false, "version": "1.0dev", "settings": {"auto_save_working_codes": true, "dev_mode": false, "ping_when_found_working_code": false, "user_id_to_ping": "your_discord_id", "log_everything_to_webhook": false, "webhook_link": "your_webhook", "use_proxies": false, "disable_gen_cooldown": true}}"""

import requests
import string
from colorama import Fore, init
from time import sleep
import os
import random
import platform
import json
import ctypes
from datetime import datetime
from blessed import Terminal
from threading import Thread, Event
import base64

terminal = Terminal()

init(autoreset=True)

# Get the operating system name
_os = platform.system()
_os_release = platform.release()
_os_version = platform.version()

global _error
global _wait_for_input
global _clear
global _set_title
global _display_license

match _os:
    case "Windows":
        User32Dll = ctypes.windll.LoadLibrary("User32.dll")

        class MB_RETURN_VALUES:
            # Define return values for message box
            def __init__(self):
                self.IDABORT = 3
                self.IDCANCEL = 2
                self.IDCONTINUE = 11
                self.IDIGNORE = 5
                self.IDNO = 7
                self.IDOK = 1
                self.IDRETRY = 4
                self.IDTRYAGAIN = 10
                self.IDYES = 6

        def _error(content, on_retry):
            # Show error message box and handle user response
            response = User32Dll.MessageBoxW(None, content, "Critical Error", 0x00000010 | 0x00000002)

            _MB_RETURN_VALUES = MB_RETURN_VALUES()
            
            match response:
                case _MB_RETURN_VALUES.IDABORT:
                    exit(1)  # Exit the program on abort
                case _MB_RETURN_VALUES.IDIGNORE:
                    pass  # Ignore the error
                case _MB_RETURN_VALUES.IDRETRY:
                    on_retry()  # Retry the operation
        
        def _wait_for_input():
            os.system("pause")

        def _clear():
            os.system("cls")

        def _set_title(title):
            os.system(f"title {title}")
        
        def _display_license():
            os.system("notepad resources\\LICENSE")

    case "Linux":
        def _error(content, on_retry):
            print(f"{Fore.RED}Critical Error: {content}\n\n[1]: Retry\n[2]: Ignore\n[3]: Abort\n{Fore.RESET}")
            _input = input("choose option: ")
            
            match _input:
                case "1":
                    on_retry()
                case "2":
                    pass
                case "3":
                    exit(1)
        
        def _wait_for_input():
            input("Press enter key to continue...\n")
        
        def _clear():
            os.system("clear")
        
        def _set_title(title):
            pass

        def _display_license():
            _clear()
            hFile = open("resources/LICENSE", "r")
            fRead = hFile.read()
            hFile.close()
            print(f"{Fore.RESET}{fRead}\n{Fore.BLUE}")
            _wait_for_input()


class log_options:
    def __init__(self):
        # Log levels
        self.log = 0
        self.success = 3
        self.warn = 2
        self.error = 1

LogOptions = log_options()

# Logo for the application
logo = (f"""{Fore.YELLOW}
  )   ((   (   (  
 (()  ))\  )\: )\ 
()(_)((_)))(_)((_){Fore.RED}
|   \| \| |  \/  |
| |) | .  | |\/| |
|___/|_|\_|_|  |_|
\n""")

close_event = Event()

def check_for_files():
    global _data

    #check if license file exists
    try:
        hFile = open("resources/LICENSE", "r")
        hFile.close()
    except:
        _error("license file not found", check_for_files)
    
    hFile.close()

    # Load data from resources/data.dat
    try:
        hFile = open("resources/data.dat", "r")  # Open data file
        _data = json.loads(base64.standard_b64decode(hFile.read()))  # Read and parse JSON data
    except Exception as err:
        _data = json.loads(default_settings)  # Load default settings if file is not found
        hfile = open("resources/data.dat", "wb")  # Create data file
        hfile.write(base64.standard_b64encode(json.dumps(_data).encode()))  # Write default settings to the file
        hfile.close()
    
    hFile.close()  # Close the file

def setup_checking():
    global gifts_checked
    global status_checking

    status_checking = ""
    gifts_checked = []

def end_checking():
    global gifts_checked
    global status_checking

    gifts_checked = None
    status_checking = None

def sort_gifts() -> dict:
    correct = []
    wrong = []
    redeemed = []

    for gift in gifts_checked:
        if gift["status"] == "reedemed":
            redeemed.append(gift)
        elif gift["status"] == "valid":
            correct.append(gift)
        elif gift["status"] == "invalid":
            wrong.append(gift)
    return {"valid": correct, "invalid": wrong, "redeemed": redeemed}

class status_bar:

    def kill_bar(self):
        sleep(0.6)
        self.is_alive = False

    def __init__(self):
        self.is_alive = True

        def do_it():
            while not close_event.is_set():
                if self.is_alive == False:
                    break

                sorted_gifts = sort_gifts()
                with terminal.location(0, terminal.height - 1):
                    print(f"{Fore.CYAN}Checked gifts --> {Fore.RESET}{len(gifts_checked)} | {Fore.GREEN}Valid gifts --> {Fore.RESET}{len(sorted_gifts['valid'])} | {Fore.RED}Invalid --> {Fore.RESET}{len(sorted_gifts['invalid'])} | {Fore.YELLOW}Redeemed --> {Fore.RESET}{len(sorted_gifts['redeemed'])}", end='\r')
                sleep(0.5)
        bar_thread = Thread(target=do_it, name="status_bar")
        bar_thread.start()
    

def main():
    
    check_internet()
    check_for_files()
    
    # Check if the license agreement has been accepted
    if not _data["launched"]:
        license_agreement()  # Prompt for license agreement

    if _data["settings"]["log_everything_to_webhook"] == True or _data["settings"]["ping_when_found_working_code"] == True:
        check_webhook()

    # Set console title and clear screen for a fresh start
    _set_title("DNM ~ sys.krnl")
    _clear()

    print(logo)  # Print the application logo

    # Display welcome message and options
    print(f"""
{Fore.MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{Fore.LIGHTMAGENTA_EX}     Welcome to Discord Nitro Miner       
{Fore.MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{Fore.RED}©sys.krnl 2024. All rights reserved.

{Fore.MAGENTA}→ {Fore.LIGHTMAGENTA_EX}[Detected OS]: {Fore.LIGHTYELLOW_EX}{_os} {_os_release}
{Fore.MAGENTA}→ {Fore.LIGHTMAGENTA_EX}[OS version]: {Fore.LIGHTYELLOW_EX}{_os_version}
{Fore.MAGENTA}→ {Fore.LIGHTMAGENTA_EX}[Version]: {Fore.LIGHTYELLOW_EX}{_data["version"]}

{Fore.LIGHTCYAN_EX}Options:
{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{Fore.LIGHTCYAN_EX}[mine]  {Fore.LIGHTYELLOW_EX}→  Generate and check gifts
{Fore.LIGHTCYAN_EX}[gene]  {Fore.LIGHTYELLOW_EX}→  Generate gifts
{Fore.LIGHTCYAN_EX}[chec]  {Fore.LIGHTYELLOW_EX}→  Check gifts
{Fore.LIGHTCYAN_EX}[sett]  {Fore.LIGHTYELLOW_EX}→  Settings
{Fore.LIGHTCYAN_EX}[lice]  {Fore.LIGHTYELLOW_EX}→  License
{Fore.LIGHTCYAN_EX}[exit]  {Fore.LIGHTYELLOW_EX}→  Exit
{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)
    user_input = input(f"{Fore.LIGHTBLUE_EX}Choose option: {Fore.LIGHTYELLOW_EX}")  # Get user option
    print("\n")

    match user_input.lower():
        case "chec":
            log(LogOptions.log, "trying to open resources/gifts.txt")  # Log attempt to open gifts file
            try:
                hFile = open("resources/gifts.txt", 'r')  # Open gifts file for reading
                log(LogOptions.success, "successfully opened resources/gifts.txt")  # Log success
            except:
                log(LogOptions.warn, "failed to open resources/gifts.txt, maybe try to generate gifts")  # Log warning
                main()  # Restart main menu
            
            log(LogOptions.log, "try to read lines from file handler")  # Log attempt to read lines
            try:
                read_buffer = hFile.readlines()  # Read all lines from the file
                log(LogOptions.success, "successfully read lines from file handler")  # Log success
            except:
                log(LogOptions.warn, "failed to read lines from file handler")  # Log warning
                _wait_for_input()  # Pause for user input
                main()  # Restart main menu
            
            hFile.close()  # Close the file
            setup_checking()
            check_codes(read_buffer)  # Check the gift codes
            print(f"{Fore.GREEN}\nChecked all gifts")  # Print success message
            end_checking()
            _wait_for_input()  # Pause for user input
            main()  # Restart main menu
        
        case "gene":
            gen_codes()
            main()  # Restart main menu

        case "exit":
            _exit()  # Exit the program

        case "mine":
            both ()  # Generate and check gift codes

        case "sett":
            settings()  # Open settings menu
        
        case "lice":
            _clear()
            _display_license()
            main()
        
        case "dev":
            dev_options()

        case _:
            main()  # Restart main menu on invalid input

def check_code(code):
    code = str.replace(code, " ", "")  # Remove whitespace
    code = str.replace(code, "\n", "")  # Remove newline character
    code = str.replace(code, "https://discord.com/gifts/", "")  # Remove carriage return character

    log(LogOptions.log, "Checking code size")  # Log attempt to check code size

    if len(code) > length or len(code) < length:

        log(LogOptions.error, "Wrong gift size")  # Log error on invalid code size

    log(LogOptions.success, "Correct code size")  # Log success on valid code size
    
    log(LogOptions.log, "Trying to send request to Discord API")  # Log attempt to send request
    try:
        request = requests.get(url=(url_discord_gifts + code + "?with_subscription_plan=true"))  # Send GET request to Discord API
        log(LogOptions.success, "Request successfully sent to Discord API")  # Log success on sending request
    except Exception as err:
        log(LogOptions.warn, f"Failed to send request to Discord API, try to connect to the internet")  # Log warning on request failure
        _wait_for_input()  # Pause for user input
        main()  # Restart main menu
    
    log(LogOptions.log, "Checking if gift link exists")

    log(LogOptions.log, "Trying to fetch JSON data from Discord API")  # Log attempt to fetch JSON data
    try:
        params = json.loads(request.text)
        log(LogOptions.success, "Succesfully fetched JSON data from Discord API")  # Log success on valid json data
    except:
        log(LogOptions.error, "Failed to parse JSON from response")  # Log error on JSON parsing failure

    match request.status_code:
        case 200:
            log(LogOptions.success, "Gift link exist")  # Log success on valid code

            log(LogOptions.log, "Trying to fetch json data from response")  # Log attempt to fetch json data

            log(LogOptions.log, "Checking if gift is valid")
            try:
                if params["uses"] == 0:
                    log(LogOptions.success, "Gift is valid")  # Log success on valid gift
                    gifts_checked.append({"status": "valid", "expires_at": params["expires_at"], "type": params["subscription_plan"]["name"]})
                elif  params["uses"] == 1:
                    log(LogOptions.warn, "Gift was already redeemed")  # Log error on invalid gift
                    gifts_checked.append({"status": "redeemed"})
                else:
                    log(LogOptions.error, "Unknown value")  # Log error on invalid gift
            except:
                log(LogOptions.warn, "Failed to check if gift is redeemed (i assume it works)")  # Log error
                gifts_checked.append({"status": "valid", "expires_at": params["expires_at"], "type": params["subscription_plan"]["name"]})
            
        case 404:
            log(LogOptions.warn, "Gift link doesn't exist")  # Log error on invalid code
            gifts_checked.append({"status": "invalid"})
        
        case 429:
            log(LogOptions.warn, f"Rate limit exceeded! Retrying in {params['retry_after']} seconds...")  # Log error on rate limit exceeded
            sleep(params["retry_after"])
            check_code(code)
            
        case _:
            log(LogOptions.error, "unknown status code")  # Log error on invalid code

def check_codes(codes):
    _clear()
    print(logo)
    print(f"{Fore.GREEN}Welcome to discord gifts checker!\n\n")
    stat = status_bar()
    for code in codes:
        check_code(code)
    stat.kill_bar()

def gen_code() -> str:
    log(LogOptions.log, "generating code")
    alphabet = string.ascii_letters
    numbers = string.digits

    chars = []
    chars.extend(alphabet)
    chars.extend(numbers)

    final_code = []

    for num in range(length):
        final_code.append(random.choice(chars))
    
    log(LogOptions.success, f"code {''.join(final_code)} generated")
    return ''.join(final_code)  # Return the generated code

def gen_codes():
    _clear()

    print(logo)
    print(f"{Fore.GREEN}Welcome to the gift code generator!\n")

    with terminal.location(0, terminal.height - 1):
        quantity = int(input(f"{Fore.LIGHTBLUE_EX}Quantity: "))  # Get quantity from user

    final_codes = []

    for num in range(quantity):
        code = gen_code()  # Generate a gift code
        with terminal.location(0, terminal.height - 2):
            print(f"{Fore.MAGENTA}> Generating --> {Fore.RESET}{code}", end="\r")
        with terminal.location(0, terminal.height - 1):
            print(f"{Fore.CYAN}Generated gifts --> {Fore.RESET}{num + 1}", end="\r")
        final_codes.append(code)
        if _data["settings"]["disable_gen_cooldown"] == False:
            sleep(gen_cooldown)  # Wait before generating the next code

    with terminal.location(0, terminal.height - 2):
        print("                                               ", end="\r")
    with terminal.location(0, terminal.height - 1):
        print("                                               ", end="\r")
    log(LogOptions.log, "trying to open handle for resources/gifts.txt file")  # Log attempt to open gifts file
    try:
        hFile = open("resources/gifts.txt", "w+")  # Open gifts file for writing
        log(LogOptions.success, "successfully opened handle for resources/gifts.txt file")  # Log success
    except:
        log(LogOptions.error, "failed to open handle for resources/gifts.txt file")  # Log error
        main()  # Restart main menu
    
    log(LogOptions.log, "trying to write gifts to file handle")  # Log attempt to write gifts
    try:
        for code in final_codes:
            hFile.write(f"https://discord.com/gifts/{code}\n")  # Write each gift code to the file
        log(LogOptions.success, "successfully written gifts to file handle")  # Log success
    except:
        log(LogOptions.warn, "failed to write gifts to file handle")  # Log warning

    hFile.close()  # Close the file
    print(f"{Fore.YELLOW}\n> Done! Gifts are saved to resources/gifts.txt")  # Print success message

    _wait_for_input()  # Pause for user input

def both():
    _clear()
    print(logo)
    print(f"{Fore.GREEN}Welcome to nitro miner!\n")
    setup_checking()
    status_bar()
    while True:
        code = gen_code()  # Generate a gift code
        check_code(code)
        

def license_agreement():
    _clear()
    print(f"""
{logo}
{Fore.MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{Fore.LIGHTMAGENTA_EX}           License agreement       
{Fore.MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{Fore.RED}©sys.krnl 2024. All rights reserved.

{Fore.LIGHTCYAN_EX}Options:
{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{Fore.LIGHTCYAN_EX}[agree]  {Fore.LIGHTYELLOW_EX}→  Agree to our license and continue
{Fore.LIGHTCYAN_EX}[openl]  {Fore.LIGHTYELLOW_EX}→  Open license agreement
{Fore.LIGHTCYAN_EX}[exitt]  {Fore.LIGHTYELLOW_EX}→  Exit program
{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
    uInput = input(f"{Fore.CYAN}Choose option: {Fore.LIGHTYELLOW_EX}")

    if uInput == "openl":
        _display_license()
        main()  # Restart main menu
    elif uInput == "agree":
        _data["launched"] = True
        save_data()
        main()  # Restart main menu
    elif uInput == "exitt":
        exit(0)  # Exit the program
    else:
        main()  # Restart main menu on invalid input

def settings():
    _clear()

    print(f"{logo}")  # Print the application logo

    items = []

    for setting in _data["settings"]:
        items.append(setting)
    
    print(f"{Fore.LIGHTCYAN_EX}Settings:")
    print(f"{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    for index in range(len(items)):
        setting_name = items[index]
        setting_value = _data["settings"][items[index]]
        print(f"{Fore.LIGHTCYAN_EX}[{index + 1}]  {Fore.CYAN}→  {setting_name}: {Fore.LIGHTYELLOW_EX}{setting_value}")
    print(f"{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"\n{Fore.LIGHTCYAN_EX}Options:")
    print(f"{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"{Fore.LIGHTCYAN_EX}[{len(items) + 1}]  {Fore.CYAN}→  Return to main menu")
    print(f"{Fore.LIGHTCYAN_EX}[{len(items) + 2}]  {Fore.CYAN}→  Set default settings")
    print(f"{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    print("\n")
    
    user_input = input(f"{Fore.CYAN}Select setting that you want to change or any option: {Fore.LIGHTYELLOW_EX}")

    try:
        user_input = int(user_input) - 1
    except:
        settings()

    if int(user_input) == (len(items) + 1):
        set_default_settings()
    elif int(user_input) > len(items):
        settings()
    elif int(user_input) == len(items):
        main()
    elif int(user_input) <= 0:
        settings()
    
    data_type = type(_data["settings"][items[int(user_input)]]).__name__

    match data_type:
        case str.__name__:
            new_value = input(f"{Fore.BLUE}Enter new value: ")

            new_value = new_value.replace("\n", "")
            new_value = new_value.replace(" ", "_")
            
            _data["settings"][items[int(user_input)]] = new_value
        
        case int.__name__:
            new_value = input(f"{Fore.CYAN}Enter new value: ")

            try:
                int(new_value)
            except:
                log(LogOptions.error, "Data type doesnt match")

            _data["settings"][items[user_input]] = new_value
        
        case bool.__name__:
            if _data["settings"][items[user_input]] == True:
                _data["settings"][items[user_input]] = False
            elif _data["settings"][items[user_input]] == False:
                _data["settings"][items[user_input]] = True

        case _:
            log(LogOptions.error, "Unsupported data type")
    
    save_data()
    check_for_files()
    settings()

def dev_options():
    global _data

    _clear()
    print(f"""
{logo}
{Fore.MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{Fore.LIGHTMAGENTA_EX}           Developer options       
{Fore.MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{Fore.RED}©sys.krnl 2024. All rights reserved.

{Fore.LIGHTCYAN_EX}Options:
{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{Fore.LIGHTCYAN_EX}[clr_ch]  {Fore.LIGHTYELLOW_EX}→  Clear cache
{Fore.LIGHTCYAN_EX}[rst_dt]  {Fore.LIGHTYELLOW_EX}→  Reset application data
{Fore.LIGHTCYAN_EX}[ext_dv]  {Fore.LIGHTYELLOW_EX}→  Exit developer options (main menu)
{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
    user_input = input(f"{Fore.CYAN}Enter option: {Fore.LIGHTYELLOW_EX}")

    match user_input:
        case "clr_ch":
            _data = None
            dev_options()
        
        case "rst_dt":
            _default_data = json.loads(default_settings)
            _data = _default_data
            save_data()
            dev_options()
        
        case "ext_dv":
            main()
        
        case _:
            dev_options()
            
def save_data():
    try:
        hFile = open("resources/data.dat", "wb")
        data = base64.standard_b64encode(json.dumps(_data).encode())
        hFile.write(data)
        hFile.close()
    except Exception as err:
        log(LogOptions.error, f"Failed to save data to file")

def set_default_settings():
    _default_settings = json.loads(default_settings)
    _data["settings"] = _default_settings["settings"]
    save_data()
    check_for_files()
    settings()

def log(log_option, text):

    match log_option:
        case LogOptions.log:
            if not _data["settings"]["dev_mode"]:
                return
            print(f"{Fore.RESET}> {Fore.CYAN}[LOG]: {Fore.WHITE}{text}")  # Print log message
        case LogOptions.warn:
            if not _data["settings"]["dev_mode"]:
                return
            print(f"{Fore.RESET}> {Fore.YELLOW}[WARNING]: {Fore.WHITE}{text}")  # Print warning message
        case LogOptions.error:
            print(f"{Fore.RESET}> {Fore.RED}[ERROR]: {Fore.WHITE}{text}")  # Print error message
            _error(text, main)  # Handle error
        case LogOptions.success:
            if not _data["settings"]["dev_mode"]:
                return
            print(f"{Fore.RESET}> {Fore.GREEN}[SUCCESS]: {Fore.WHITE}{text}")  # Print success message

def check_webhook():

    if _data["settings"]["ping_when_found_working_code"] == False and _data["settings"]["log_everything_to_webhook"] == False:
        return

    log(LogOptions.log, "Trying to check webhook...")

    webhook = _data["settings"]["webhook_link"]

    if str.rfind(webhook, "https://discord.com/api/webhooks/", 0, len(webhook)):
        log(LogOptions.error, "Webhook link is invalid")

    try:
        request = requests.get(webhook)
    except Exception as err:
        log(LogOptions.error, f"Failed to send webhook request (Probably invalid webhook link) (will try to automatically fix that by disabling webhook functions) error: {err}")
        _data["settings"]["ping_when_found_working_code"] = False
        _data["settings"]["log_everything_to_webhook"] = False
        save_data()

    if request.status_code == 404:
        log(LogOptions.error, "Webhook link is invalid")
    elif  request.status_code == 200:
        log(LogOptions.success, "Webhook link is valid")
    elif request.status_code == 429:
        log(LogOptions.warn, f"Webhook link is rate limited. Waiting {json.loads(request.text)['retry_after']} seconds")
        sleep(int(json.loads(request.text)["retry_after"]) + 1)
        check_webhook()
    elif request.status_code == 401:
        log(LogOptions.error, "You dont have permission to use this webhook")
    else:
        log(LogOptions.error, f"Webhook link returned unknown status code: {request.status_code}")

def send_webhook_msg(embed: dict):
    log(LogOptions.log, "Trying to send webhook message...")

    webhook = _data["settings"]["webhook_link"]

    try:
        requests.post(webhook, json={"embeds":[embed]})
        log(LogOptions.success, "Successfully sent webhook message")

    except Exception as err:
        log(LogOptions.error, f"Failed to send webhook request ({err})")

def ping():
    log(LogOptions.log, "Trying to ping...")

    webhook = _data["settings"]["webhook_link"]

    try:
        requests.post(webhook, json={"content": f"<@{_data['settings']['user_id_to_ping']}>"})
        log(LogOptions.success, "Successfully sent webhook message")

    except Exception as err:
        log(LogOptions.error, f"Failed to send webhook request ({err})")

# not implemented yet
async def wb_send(status):
    send_webhook_msg({
        "title": "DNM - Webhook",
        "description": "",
        "color": "65280",
        "image": {"url": "https://cdn.discordapp.com/attachments/1297845408839499797/1298021463391207455/logo.gif?ex=67180c30&is=6716bab0&hm=549d4e15b3e580df4e7e42742989e673966146468fd043249c31165e6b3a8da9&"},
        "fields": [
            {
                "name": "Working gifts",
                "value": f"> {(checked + 1) - wrongs}"
            },
            {
                "name": "Wrong gifts",
                "value": f"> {wrongs}"
            },
            {
                "name": "Checked gifts",
                "value": f"> {checked + 1}"
            },
            {
                "name": "Status",
                "value": status
            }
        ],
        "author": {
            "name": "Made by sys.krnl",
            "icon_url": "https://cdn.discordapp.com/attachments/1297845408839499797/1298021463391207455/logo.gif?ex=67180c30&is=6716bab0&hm=549d4e15b3e580df4e7e42742989e673966146468fd043249c31165e6b3a8da9&"
        },
        "footer": {
            "text": "©sys.krnl 2024. All rights reserved."
        }
    })

def check_internet():
    try:
        requests.get("https://google.com/")
    except requests.ConnectionError:
        _error("Please connect to the internet and try again.", check_internet)
        exit(1)

def _exit():
    log(LogOptions.warn, "Exiting...")
    try:
        close_event.set()
        exit(0)
    except Exception as err:
        _error(f"Failed to exit (Please show this to the developer): {err}", _exit)

_clear()
print("Loading...")
main()  # Start the main menu
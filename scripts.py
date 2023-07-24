import requests
import json
from datetime import date
import time
import logging as log


# integer checking function
def is_integer(n):
    try:
        float(n)
    except ValueError:
        return False
    else:
        return float(n).is_integer()


# Returns value of key 'govee_api_key' from a json file. 
# Reminder usage: get_govee_credentials(file_name)[json_name_of_credential]
# Ex. Default: get_govee_credentials()["govee_api_key"]
def get_govee_credentials(file_name = "default"):
    if file_name == "default":
        file = open('govee_credentials.json')
    else:
        file = open(file_name)
    data = json.load(file)
    if data["govee_api_key"] =="Enter your key here":
        print("Your script will error! Remember to set your api key in govee credentials or whatever source you're using for key storage!")
    return data


# iterate through govee devices to grab MAC, model, and device name using your API Key
def get_govee_devices(api_key = get_govee_credentials()["govee_api_key"]):
    url = "https://developer-api.govee.com/v1/devices"
    headers = {
        "accept": "application/json",
        "Govee-API-Key": api_key
    }
    response = requests.get(url, headers=headers)
    return response.json()["data"]["devices"]


# allows user to select devices from the previous function, and along with the server function will send a payload to light function
def choose_govee_device():
    devices = get_govee_devices()
    counter = 0
    print("Please choose between the follow devices by typing the device number. Type 'Cancel' to cancel your request")
    for i in devices:
        counter +=1
        print(f"{counter} -- Device Name: {i['deviceName']} -- MAC: {i['device']}")
    device_input = input("Type valid device numbers (Ex. '123' for devices 1, 2, and 3): ")
    done = False
    payloads = []
    while done == False:
        if device_input == 'Cancel':
            payloads = [
                {
                "model": get_govee_credentials()["default_device_model"],
                "device": get_govee_credentials()["default_device_mac"],
                "cmd": {
                    "name": "turn",
                    "value": "on"
                    }
                },
            ]
            break
        for i in device_input:
            if int(i) <= counter and int(i) > 0 and is_integer(i): 
                i = int(i) - 1
                payload = {
                    "model": devices[i]['model'],
                    "device": devices[i]['device'],
                    "cmd": {
                        "name": "turn",
                        "value": "on"
                    }
                }
                payloads.append(payload)
                done = True
                print(f"Device {devices[i]['deviceName']} is now default!")
            else:
                print("INVALID INPUT!")
                device_input = input("Please enter a valid device number: ")
    return payloads

# State is equal "on" or "off" // Controls lights. Can accept payloads to change models on the current network.
def lights(state, payloads = "default"):
    url = "https://developer-api.govee.com/v1/devices/control"
    print(payloads)
    if payloads == "default":
        payloads = [
            {
                "model": get_govee_credentials()["default_device_model"],
                "device": get_govee_credentials()["default_device_mac"],
                "cmd": {
                    "name": "turn",
                    "value": "on"
                    }
            },
        ]
    else:
        print("Custom payload accepted!")
    if state == "off":
        for payload in payloads:
            payload["cmd"]["value"] = "off"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Govee-API-Key": get_govee_credentials()["govee_api_key"]
    }
    try:
        # Update to Valid Request
        for payload in payloads:
            response = requests.put(url, json=payload, headers=headers)
            if response.status_code == 429:
                # Suspend Sending Additional Requests until the Retry-After period has elapsed
                time.sleep(int(response.headers["Retry-After"])+5)
            log.info(response.content)
    except requests.exceptions.RequestException as e:
        log.error(e)


def basic_server():

    print("\nWelcome to the Govee Lights Program! Type /help for more info.\n")
    # variables
    status = True # What keeps the server on
    user_input = "" # User input value
    payload_set = False # Whether a current payload is set for the given session
    initialization = True # For the first run through so theres no invalid input warning

    # user inputs
    while status == True:
        if user_input == "/help":
            print("\nServer Commands:\n/help: Help Menu\n/set: Changes target light from default.\n/log: Print server log\n/lights: Turns lights on for 30 seconds\n/payloads: Prints current set payload\n/stop: Ends session\n")
        elif user_input == "/set":
            payload = choose_govee_device()
            payload_set = True
        elif user_input  == "/payload":
            print("Current active devices will be displayed below: ")
            if payload_set == True:
                print(payload)
            else:
                print([
                {
                "model": get_govee_credentials()["default_device_model"],
                "device": get_govee_credentials()["default_device_mac"],
                "cmd": {
                    "name": "turn",
                    "value": "on"
                    }
                },
                ])
        elif user_input == "/lights":
            print(f"Turning lights on for 30 seconds.")
            if payload_set == True:
                lights("on",payload)
                time.sleep(30)
                lights("off",payload)
            else:
                lights("on")
                time.sleep(30)
                lights("off")
            print("Light is off!")
        elif user_input == "/log":
            log_file = open(f"log_{str(date.today())}.log","r")
            print(log_file.read())
        elif user_input == "/stop":
            status = False
        else:
            if initialization == False:
                print("Invalid input, please try again.")
            else:
                initialization = False
        if status == True:
            user_input = input("Server> ")

if __name__ == "__main__":
    basic_server()
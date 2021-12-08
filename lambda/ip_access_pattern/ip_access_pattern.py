import os
import json
import logging
import subprocess
import re
import requests
import boto3
soracom_auth_key_id = os.getenv('SORACOM_AUTH_KEY_ID')
soracom_auth_key = os.getenv('SORACOM_AUTH_KEY')
soracom_imsi = os.getenv('IMSI')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# SORACOM API
soracom_common_arg = ' --auth-key-id ' + \
    soracom_auth_key_id + ' --auth-key ' + soracom_auth_key


# Lambda Response
ok_response = {
    "isBase64Encoded": False,
    "statusCode": 200,
    "headers": {},
    "body": ""
}
error_response = {
    "isBase64Encoded": False,
    "statusCode": 401,
    "headers": {},
    "body": ""
}


def create_url():
    soracom_cli_create_port_mapping = "soracom port-mappings create --body '{\"destination\": {\"imsi\": \"" + \
        soracom_imsi + "\", \"port\": 5000}, \"duration\": 30, \"tlsRequired\": true}'" + \
        soracom_common_arg
    port_mapping_info = json.loads((subprocess.run(
        soracom_cli_create_port_mapping, shell=True, stdout=subprocess.PIPE)).stdout.decode())
    url = "https://" + \
        port_mapping_info["hostname"] + ":" + \
        str(port_mapping_info["port"]) + "/"
    logger.info("Created port mapping.")
    return url


def delete_port_mapping(url):
    # url = https://xx-xx-xx-xx.napter.soracom.io:xxxxx/
    ip_address = re.split(r'[/\.]', url)[2].replace('-', '.')
    port = re.split(r'[:/]', url)[4]

    soracom_cli_delete_port_mapping = "soracom port-mappings delete --ip-address " + \
        ip_address + " --port " + port + soracom_common_arg
    subprocess.run(
        soracom_cli_delete_port_mapping, shell=True, stdout=subprocess.PIPE)
    logger.info("Deleted port mapping.")
    return


def get_led_check_message(url):
    try:
        res = requests.get(url)
        res.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(e)
        raise e
    led_state = res.text  # 1 or 0
    led_state_message = 'ついてるよ' if (int(led_state)) else '消えてるよ'
    return led_state_message


def set_led(led_state, url):
    url = url + "led"
    headers = {'Content-type': 'application/json'}
    payload = json.dumps({"led": led_state})
    try:
        res = requests.put(url,
                           headers=headers, data=payload)
        res.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(e)
        raise e
    return


def lambda_handler(event, context):
    message_text = event.get("message")
    logger.info("message is " + message_text)

    try:
        url = create_url()

        if (message_text == "電気ついてる？"):
            return_message_text = get_led_check_message(url)
        elif (message_text == "電気つけて"):
            set_led("1", url)
            return_message_text = "つけたよ"
        elif (message_text == "電気消して"):
            set_led("0", url)
            return_message_text = "消したよ"
        else:
            logger.warn("Invalid input")
            return_message_text = "メッセージが変だよ"

        delete_port_mapping(url)
    except:
        return_message_text = "エラーだよ"

    return return_message_text

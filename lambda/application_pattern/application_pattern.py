import os
import json
import logging
import boto3
import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# AWS IoT
endpoint_url = os.getenv('AWS_IOT_ENDPOINT_URL')
thing_name = os.getenv('AWS_IOT_THING_NAME')

client = boto3.client(
    'iot-data', endpoint_url=endpoint_url)

response = client.get_thing_shadow(
    thingName=thing_name,
    shadowName='led'
)


def get_led_check_message():
    response = client.get_thing_shadow(
        thingName=thing_name,
        shadowName='led'
    )

    payload = json.loads(response["payload"].read().decode())

    led_state = payload["state"].get("reported", {}).get("led")
    timestamp_jst = payload["timestamp"] + 32400
    last_updated = str(datetime.datetime.fromtimestamp(timestamp_jst))

    led_state_message = 'ついてるよ' if (int(led_state)) else '消えてるよ'
    ret_message = led_state_message + "\n最終更新 [JST]: " + last_updated
    return ret_message


def set_led(led_state):
    shadowDoc = {'state': {'desired': {'led': led_state}}}
    new_payload = bytes(json.dumps(shadowDoc), "utf-8")

    res = client.update_thing_shadow(
        thingName=thing_name, shadowName='led', payload=new_payload)

    return


def lambda_handler(event, context):
    message_text = event.get("message")
    logger.info("message is " + message_text)

    try:
        if (message_text == "電気ついてる？"):
            return_message_text = get_led_check_message()
        elif (message_text == "電気つけて"):
            set_led("1")
            return_message_text = "つけるね"
        elif (message_text == "電気消して"):
            set_led("0")
            return_message_text = "消すね"
        else:
            logger.warn("Invalid input")
            return_message_text = "メッセージが変だよ"

    except:
        return_message_text = "エラーだよ"

    return return_message_text

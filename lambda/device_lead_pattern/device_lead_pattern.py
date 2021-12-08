import os
import json
import logging
import subprocess
soracom_auth_key_id = os.getenv('SORACOM_AUTH_KEY_ID')
soracom_auth_key = os.getenv('SORACOM_AUTH_KEY')
soracom_imsi = os.getenv('IMSI')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# SORACOM API
soracom_common_arg = ' --auth-key-id ' + \
    soracom_auth_key_id + ' --auth-key ' + soracom_auth_key


def get_sim_tags():
    soracom_cli_get_sim = "soracom subscribers get --imsi " + \
        soracom_imsi + soracom_common_arg
    sim_info = json.loads((subprocess.run(
        soracom_cli_get_sim, shell=True, stdout=subprocess.PIPE)).stdout.decode())
    # tags = {"LED":"1","lastUpdated":"[JST] 2021-11-20T23:43","name":"RasPi-vSIM"}
    return sim_info['tags']


def get_led_check_message(tags):
    led_state = int(tags['LED'])
    last_updated = tags['lastUpdated']
    led_state_message = 'ついてるよ' if (led_state) else '消えてるよ'
    ret_message = led_state_message + "\n最終更新: " + last_updated
    return ret_message


def set_led(led_state):
    soracom_cli_put_sim_tags = "soracom subscribers put-tags --imsi " + \
        soracom_imsi + \
        ' --body \'[{"tagName":"LED","tagValue":"' + \
        led_state + '"}]\'' + soracom_common_arg
    subprocess.run(soracom_cli_put_sim_tags,
                   shell=True, stdout=subprocess.PIPE)
    return


def lambda_handler(event, context):
    message_text = event.get("message")
    logger.info("message is " + message_text)

    try:
        if (message_text == "電気ついてる？"):
            return_message_text = get_led_check_message(get_sim_tags())
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

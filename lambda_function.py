"""
This file receive incoming event and first process event from Application
"""

import json
import urllib.parse
from aws import slackstash
from aws import constants


def process_schedule_set_option(options):
    """
    Process schedule options
    """
    options_size = len(options)
    # Support only schedule for turnon/turnoff
    if 3 < options_size < 8:
        schedule = {
            "commands": [],
            "requester": None
        }
        i = 2
        while i < options_size - 1:
            if options[i] == "turnon" or options[i] == "turnoff":
                cmd = {
                    "cmd": "aws",
                    "cmd_text": options[i],
                    "instance_tag": options[options_size - 1],
                    "time": urllib.parse.unquote(options[i+1]).replace("-", " "),
                    "is_loop": False
                }
                date_time = cmd["time"]
                if date_time is None:
                    return constants.MESSAGE_WRONG_COMMAND
                schedule["commands"].append(cmd)
                i = i + 2
            else:
                return constants.MESSAGE_WRONG_COMMAND
        return schedule
    else:
        return constants.MESSAGE_WRONG_COMMAND


def process_event(event):
    """
    Process incoming event
    """
    text = ""
    att_text = ""
    response = {
        "response_type": "in_channel",
        "mrkdwn": "true",
        "text": None,
        "attachments": []
    }
    body = event.get('body').replace("&", "\",\"").replace("=", "\":\"")
    data = json.loads("{\"" + body + "\"}")

    command = data["command"].strip("%2F")

    data["text"] = " ".join(data["text"].replace("+", " ").split())
    options = data["text"].split(" ")

    if slackstash.check_authorization(data):
        text = "User <@{0}> has run `{1} {2}` command".format(
            data["user_name"], command, urllib.parse.unquote(data["text"]))
    else:
        text = "User <@{0}> are not have authorization access to this function!".format(
            data["user_name"])
    attach = ""
    cmd = slackstash.Command()
    # Delete schedule if event is auto triggered and schedule is executed once
    try:
        if data["auto_trigger_event"] == "True" and data["is_loop"] == "False":
            cmd.call("aws_delete_schedule", data["rule_name"])
    except KeyError:
        print ("Not auto trigger event!")
        pass

    if options[0] == "turnon":
        att_text = cmd.call(command + "_turnon", options[1])
    elif options[0] == "turnoff":
        att_text = cmd.call(command + "_turnoff", options[1])
    elif options[0] == "status":
        attach = cmd.call(command + "_status", options[1])
    elif options[0] == "tags":
        att_text = cmd.call(command + "_tags", options[1])
    elif options[0] == "schedule" and options[1] == "set":
        schedule = process_schedule_set_option(options)
        if schedule == constants.MESSAGE_WRONG_COMMAND:
            att_text = "Command `{0} {1}` wrong".format(
                command, data["text"].replace("+", " "))
        else:
            schedule["requester"] = data["user_name"]
            att_text = cmd.call(command + "_set_schedule", schedule)
    elif options[0] == "schedule" and options[1] == "delete":
        att_text = cmd.call(command + "_delete_schedule", options[2])
    elif options[0] == "schedule" and options[1] == "list-all":
        att_text = cmd.call(command + "_list_schedule", None)
    else:
        att_text = "Command `{0} {1}` wrong".format(
            command, data["text"].replace("+", " "))

    att_text = {"text": att_text, "color": "#3AA3E3"}

    response["text"] = text
    response["attachments"].append(att_text)
    response["attachments"].append(attach)
    return response


def lambda_handler(event, context):
    """
    Handler incoming request
    """
    response = process_event(event)
    return {
        "isBase64Encoded": True,
        'statusCode': 200,
        'body': json.dumps(response)
    }

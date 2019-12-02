"""
This file receive incoming event and first process event from Application
"""

import json
import urllib.parse
from aws import slackstash
from aws import constants
import botocore.vendored.requests as requests


def verify_command(options):
    """
    Verify command
    """
    options_size = len(options)

    if options_size >= 2:
        return True

    return False


def process_schedule_set_option(options):
    """
    Process schedule options
    """
    options_size = len(options)
    # Support only schedule for turnon/turnoff
    if 3 < options_size < 7:
        schedule = {
            "commands": [],
            "requester": None
        }
        i = 1
        while i < options_size - 1:
            if options[i] == "turnon" or options[i] == "turnoff":
                date_time = urllib.parse.unquote(options[i+1]).replace("-", " ")
                if date_time is None:
                    return constants.MESSAGE_WRONG_COMMAND
                cron_express = slackstash.convert_datetime_to_cron(date_time)
                # Check if input date_time is match format
                if cron_express is None:
                    return constants.MESSAGE_DATE_TIME_INCORRECT
                cmd = {
                    "cmd": "aws",
                    "cmd_text": options[i],
                    "instance_tag": options[options_size - 1],
                    "cron_express": cron_express,
                    "is_loop": False
                }
                schedule["commands"].append(cmd)
                i = i + 2
            else:
                return constants.MESSAGE_WRONG_COMMAND
        return schedule
    else:
        return constants.MESSAGE_WRONG_COMMAND


def process_approval_request(payload):
    """
    Process event when user click 'approve' or 'reject'
    """
    actions = payload["actions"]
    original_request_message = payload["original_message"]["text"].replace('+', ' ')
    response_text = ""
    value = actions[0]["value"].replace('+', ' ').replace("'", "\"")
    action_value = json.loads(value)
    data = {
        "token": payload["token"],
        "team_id": payload["team"]["id"],
        "channel_id": payload["channel"]["id"],
        "user_id": action_value["user_id"],
        "user_name": action_value["user_name"],
        "command": action_value["command"],
        "text": action_value["text"],
        "response_url": action_value["response_url"],
        "attachments": [],
        "approval_user_id": payload["user"]["id"],
        "approval_action": None
    }

    if actions[0]["name"] == "approve":
        response_text = "<@{0}> approved this request".format(payload["user"]["name"])
        process_command_response = process_slash_command_request(data)
        data["approval_action"] = "approved"
        data["attachments"] = process_command_response["attachments"]
    elif actions[0]["name"] == "reject":
        response_text = "<@{0}> rejected this request".format(payload["user"]["name"])
        data["approval_action"] = "rejected"

    # This send response to original request channel
    send_result_message_after_approval(data)

    # This response to approval channel
    return {
        "replace_original": "true",
        "text": original_request_message,
        "attachments": [
            {
                "text": response_text,
                "color": "#3AA3E3",
                "attachment_type": "default",
            }
        ]
    }


def process_slash_command_request(data):
    """
    Process slash command
    """
    text = ""
    att_text = ""
    response = {
        "response_type": "in_channel",
        "mrkdwn": "true",
        "text": None,
        "attachments": []
    }

    command = data["command"].strip("/")

    data["text"] = " ".join(data["text"].replace("+", " ").split())
    options = data["text"].split(" ")
    command_text = urllib.parse.unquote(data["text"])

    if slackstash.check_authorization(data):
        text = "User <@{0}> has run `{1} {2}` command".format(
            data["user_name"], command, command_text)
    else:
        text = "User <@{0}> are not have authorization access to this function!".format(
            data["user_name"])

    if verify_command(options):
        action = options[0]
        options.pop(0)
        value = options

    cmd = slackstash.Command()
    # Delete schedule if event is auto triggered and schedule is executed once
    try:
        if data["auto_trigger_event"] == "True" and data["is_loop"] == "False":
            cmd.call("aws_delete_schedule", data["rule_name"])
    except KeyError:
        print("Not auto trigger event!")
        pass

    if action == "turnon":
        if slackstash.check_need_approval(data):
            send_approval_message("User <@{0}> request to `{1}`".format(
                data["user_name"], command_text), data)
            att_text = constants.MESSAGE_APPROVAL_USER
        else:
            att_text = cmd.call(command + "_turnon", value)
    elif action == "turnoff":
        if slackstash.check_need_approval(data):
            send_approval_message("User <@{0}> request to `{1}`".format(
                data["user_name"], command_text), data)
            att_text = constants.MESSAGE_APPROVAL_USER
        else:
            att_text = cmd.call(command + "_turnoff", value)
    elif action == "status":
        response["attachments"] = cmd.call(command + "_status", value)
        return response
    elif action == "tags":
        response["attachments"] = cmd.call(command + "_tags", value)
        return response
    elif action == "schedule" and value[0] == "set":
        schedule = process_schedule_set_option(value)
        if schedule == constants.MESSAGE_WRONG_COMMAND:
            att_text = "Command `{0} {1}` wrong".format(
                command, data["text"].replace("+", " "))
        else:
            schedule["requester"] = data["user_name"]
            att_text = cmd.call(command + "_set_schedule", schedule)
    elif action == "schedule" and value[0] == "delete":
        att_text = cmd.call(command + "_delete_schedule", value[1])
    elif action == "schedule" and value[0] == "list-all":
        att_text = cmd.call(command + "_list_schedule", None)
    else:
        att_text = "Command `{0} {1}` wrong".format(
            command, data["text"].replace("+", " "))

    att_text = {"text": att_text, "color": "#3AA3E3"}

    response["text"] = text
    response["attachments"].append(att_text)

    return response


def process_event(event):
    """
    Process incoming event
    """
    body = event.get('body').replace("=", "\":\"").replace("&", "\",\"")
    body = "{\"" + body + "\"}"
    unquote_body = urllib.parse.unquote(body)
    unquote_body = unquote_body.replace(':"{"', ':{"').replace('"}"', '"}')
    data = json.loads(unquote_body)
    # Check if this is a approval request
    if 'payload' in data:
        payload = data["payload"]
        if payload["type"] == "interactive_message":
            return process_approval_request(payload)
    else:
        # This request is not a approval request
        return process_slash_command_request(data)


def send_approval_message(approval_message, data):
    """
    Send a message to approval channel, request to approve command
    """
    uri = constants.SLACK_APPROVAL_ROOM_WEEBHOOK
    headers = {
        'content-type': 'application/json'
    }
    value_object = {
        "command": data["command"],
        "text": data["text"],
        "user_id": data["user_id"],
        "user_name": data["user_name"],
        "response_url": data["response_url"],
        "attachments": []
    }
    data = {
        "response_type": "in_channel",
        "text": approval_message,
        "attachments": [
            {
                "text": "Would you approve this request?",
                "fallback": "Would you approve this request?",
                "callback_id": "confirm_request",
                "color": "#3AA3E3",
                "attachment_type": "default",
                "actions": [
                    {
                        "name": "approve",
                        "text": "Approve",
                        "type": "button",
                        "style": "primary",
                        "value": str(value_object)
                    },
                    {
                        "name": "reject",
                        "text": "Reject",
                        "type": "button",
                        "style": "danger",
                        "value": str(value_object)
                    }
                ]
            }
        ]
    }
    requests.post(uri, data=json.dumps(data), headers=headers)


def send_result_message_after_approval(data):
    uri = data["response_url"]
    headers = {
        'content-type': 'application/json'
    }
    data = {
        "response_type": "in_channel",
        "text": '<@{0}> {1} request: `{2}` of user <@{3}>'.format(
            data["approval_user_id"], data["approval_action"], data["text"], data["user_id"]),
        "attachments": data["attachments"]
    }
    requests.post(uri, data=json.dumps(data), headers=headers)


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

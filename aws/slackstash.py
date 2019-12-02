"""
Define all command when call from Slack
"""

from datetime import datetime
from aws import ec2
from aws import rds
from aws import cw_events
from aws import constants


def find_channel(channel_id, channel_ids):
    """
    Find channel is exist
    """
    for _id in channel_ids:
        if channel_id == _id:
            return True
    return False


def find_user(user_id, user_ids):
    """
    Find user is exist
    """
    for _id in user_ids:
        if user_id == _id:
            return True
    return False


def find_command(command, commands):
    """
    Find command is exist
    """
    for item in commands:
        if command == item:
            return True
    return False


def check_authorization(data):
    """
    Check user authorization with change
    """
    if data["token"] == constants.TOKEN and data[
            "team_id"] == constants.TEAM_ID:
        return True
    return False


def check_need_approval(data):
    """
    Check if request need approval or not (depend on user_id and channel_id)
    """
    if data["channel_id"] == constants.SLACK_APPROVAL_CHANNEL_ID:
        return False
    return True


def get_instance_id(_instances, instance_list, regex):
    """
    Get all install match with tag name
    """
    instances = []
    if regex:
        for item in instance_list:
            if _instances[0] in item["TagName"].lower():
                instances.append(item)
    else:
        for instance in _instances:
            for item in instance_list:
                if instance.lower() == item["TagName"].lower():
                    instances.append(item)

    return instances


def print_instance_info(_instance):
    """
    Format attachment for EC2 instance
    """
    attachment = {"text": "", "fields": [], "color": "#F35A00"}
    attachment["text"] = "The instance `" + _instance[
        "TagName"] + "` has current status as below:"
    field_service_type = {
        "title": "Service Type:",
        "value": _instance["ServiceType"].upper(),
        "short": "true"
    }
    field_status = {
        "title": "Status:",
        "value": _instance["State"],
        "short": "true"
    }
    field_instance_type = {
        "title": "Instance Type:",
        "value": _instance["InstanceType"],
        "short": "true"
    }

    attachment["fields"].append(field_service_type)
    attachment["fields"].append(field_instance_type)
    attachment["fields"].append(field_status)

    if _instance["ServiceType"] == "ec2":
        field_local_ip = {
            "title": "Local IP:",
            "value": _instance["PrivateIpAddresses"],
            "short": "true"
        }
        attachment["fields"].append(field_local_ip)
        if _instance["PublicIpAddress"] is not None:
            field_public_ip = {
                "title": "Public IP:",
                "value": _instance["PublicIpAddress"],
                "short": "true"
            }
            attachment["fields"].append(field_public_ip)
    elif _instance["ServiceType"] == "rds":
        field_endpoint = {
            "title": "Endpoint:",
            "value": _instance["Endpoint"],
            "short": "true"
        }
        field_engine = {
            "title": "Engine:",
            "value": _instance["Engine"],
            "short": "true"
        }
        field_engine_version = {
            "title": "Engine Version:",
            "value": _instance["EngineVersion"],
            "short": "true"
        }
        attachment["fields"].append(field_endpoint)
        attachment["fields"].append(field_engine)
        attachment["fields"].append(field_engine_version)

    return attachment


def print_instance_tag(_instance):
    """
    Format attachment for tag information
    """
    attachment = {"text": "", "fields": [], "color": "#119367"}
    field_service_type = {
        "title": "Service Type:",
        "value": _instance["ServiceType"].upper(),
        "short": "true"
    }
    field_tag = {
        "title": "Tag Name:",
        "value": _instance["TagName"],
        "short": "true"
    }

    attachment["fields"].append(field_tag)
    attachment["fields"].append(field_service_type)

    return attachment


def create_schedule(aws_cmd, cmd_text, instance, cron_express, is_loop, requester):
    schedule = {
        "commands": [],
        "requester": requester
    }
    cmd = {
        "cmd": aws_cmd,
        "cmd_text": cmd_text,
        "instance_tag": instance,
        "cron_express": cron_express,
        "is_loop": is_loop
    }
    schedule["commands"].append(cmd)
    return schedule

def get_schedule_rule_name(rule_name_regex) :
    list_schedule_rule = []
    rules = cw_events.list_rules()["Rules"]
    for rule in rules:
        if rule_name_regex in rule["Name"] :
            list_schedule_rule.append(rule["Name"])
    return list_schedule_rule

def print_schedule_list_info(list_rules):
    """
    Format attachment for schedule info
    """
    text = ""
    array_schedules = list_rules["Rules"]
    if len(array_schedules) > 0:
        text = "List of schedule as below:\n"
        for schedule in array_schedules:
            text = "{0} - *Schedule:* `{1}`     *State:* `{2}`\n".format(
                text, schedule["Name"], schedule["State"])
    else:
        text = "There are no schedules!"

    return text


def convert_datetime_to_cron(date_time):
    """
    Convert date time to cron expression
    """
    # Not handle timezone logic. Default timezone of ICT+7
    offset = constants.LOCAL_TIMEZONE
    parse_time = None
    try:
        parse_time = datetime.strptime(date_time, "%Y/%m/%d %H:%M")
    except ValueError:
        # date time not match format
        return None
    parse_time = datetime.fromtimestamp(datetime.timestamp(parse_time) - offset*60*60)
    cron_express = "cron({0} {1} {2} {3} ? {4})".format(
        parse_time.minute, parse_time.hour, parse_time.day, parse_time.month,
        parse_time.year)
    return cron_express


class Command(object):
    """
    All command list here
    """

    def call(self, command, options):
        """
        Call functions
        """
        method_name = command
        method = getattr(self, method_name, lambda: 'Invalid command!')

        return method(options)

    @classmethod
    def aws_turnon(cls, _instances):
        """
        Turn on command
        """
        ec2_instances = ec2.get_list_instances()
        rds_instances = rds.get_list_instances()
        list_instance = ec2_instances + rds_instances
        instances = get_instance_id(_instances, list_instance, False)
        number_instance = len(instances)
        if number_instance == 0:
            return constants.MESSAGE_INSTANCE_NOT_FOUND
        else:
            input_ec2_instances = []
            input_rds_instances = []
            for _instance in instances:
                if _instance["ServiceType"] == "ec2":
                    input_ec2_instances.append(_instance)
                elif _instance["ServiceType"] == "rds":
                    input_rds_instances.append(_instance)

            value = ""
            if len(input_rds_instances) > 0:
                result = rds.start_all_instance(input_rds_instances)
                value = "{0}{1}\n".format(value, result)

            if len(input_ec2_instances) > 0:
                # Need to check and turnon rds before ec2
                for ec2_instance in input_ec2_instances:
                    rds_instance_can_be = ["{0}db".format(
                        ec2_instance["TagName"].lower()), "{0}-db".format(ec2_instance["TagName"].lower())]
                    check_rds_can_be = get_instance_id(rds_instance_can_be, rds_instances, False)
                    if len(check_rds_can_be) == 0 or (check_rds_can_be[0]["State"] == "available"):
                        # Check turnon schedule. If exist, remove it
                        rule_name_prefix = "auto_schedule_turnon_{0}".format(ec2_instance["TagName"])
                        list_rule = get_schedule_rule_name(rule_name_prefix)
                        for rule_name in list_rule:
                            cw_events.delete_rule(rule_name)
                        # Can turn on ec2
                        result = ec2.start_instance(ec2_instance)
                        value = "{0}{1}\n".format(value, result)
                    elif check_rds_can_be[0]["State"] == "stopped":
                        # Need to turn-on rds first
                        rds.start_instance(check_rds_can_be[0])
                        schedule = create_schedule(
                            "aws", "turnon", ec2_instance["TagName"], "cron(0/2 * * * ? *)", True, "auto_schedule")
                        Command.aws_set_schedule(schedule)
                        result = "The RDS instance `{0}` is starting\n".format(check_rds_can_be[0]["TagName"])
                        result = "{0}`Turnon {1}` need to wait until RDS instance `{2}` is started. Please wait!".format(
                            result, ec2_instance["TagName"], check_rds_can_be[0]["TagName"])
                        value = "{0}{1}\n".format(value, result)
                    elif check_rds_can_be[0]["State"] == "starting" or ("configuring" in check_rds_can_be[0]["State"]):
                        # Waiting until rds is turned-on
                        result = "`Turnon {0}` need to wait until RDS instance `{1}` is started. Please wait!".format(
                            ec2_instance["TagName"], check_rds_can_be[0]["TagName"])
                        value = "{0}{1}\n".format(value, result)
                    else:
                        result = "Cannot `turn-on` instance EC2 `{0}` because of RDS instance `{1}` is `{2}`".format(
                            ec2_instance["TagName"], check_rds_can_be[0]["TagName"], check_rds_can_be[0]["State"])
                        value = "{0}{1}\n".format(value, result)

            return value

    @classmethod
    def aws_turnoff(cls, _instances):
        """
        Turnoff command
        """
        ec2_instances = ec2.get_list_instances()
        rds_instances = rds.get_list_instances()
        list_instance = ec2_instances + rds_instances
        instances = get_instance_id(_instances, list_instance, False)
        number_instance = len(instances)
        if number_instance == 0:
            return constants.MESSAGE_INSTANCE_NOT_FOUND
        else:
            input_ec2_instances = []
            input_rds_instances = []
            for _instance in instances:
                if _instance["ServiceType"] == "ec2":
                    input_ec2_instances.append(_instance)
                elif _instance["ServiceType"] == "rds":
                    input_rds_instances.append(_instance)

            value = ""
            if len(input_ec2_instances) > 0:
                for ec2_instance in input_ec2_instances:
                    result = ec2.stop_instance(ec2_instance)
                    value = "{0}{1}\n".format(value, result)
                    rds_instance_can_be = ["{0}db".format(
                        ec2_instance["TagName"].lower()), "{0}-db".format(ec2_instance["TagName"].lower())]
                    check_rds_can_be = get_instance_id(rds_instance_can_be, rds_instances, False)
                    if len(check_rds_can_be) > 0:
                        result = rds.stop_instance(check_rds_can_be[0])
                        value = "{0}{1}\n".format(value, result)

            if len(input_rds_instances) > 0:
                result = rds.stop_all_instance(input_rds_instances)
                value = "{0}{1}\n".format(value, result)

        return value

    @classmethod
    def aws_status(cls, _instances):
        """
        aws status command using for get status of instances
        """
        attachments = []
        ec2_instances = ec2.get_list_instances()
        rds_instances = rds.get_list_instances()
        list_instance = ec2_instances + rds_instances
        instances = get_instance_id(_instances, list_instance, False)
        if instances:
            for _instance in instances:
                attachments.append(print_instance_info(_instance))
        else:
            for _instance in _instances:
                attachments.append({
                    "text": "Instance `{0}` is not exist!".format(_instance),
                    "color": "#119300"
                })
            return attachments

        return attachments

    @classmethod
    def aws_tags(cls, _instance):
        """
        aws tag command using for get all instance tags
        """
        attachments = []
        ec2_instances = ec2.get_list_instances()
        rds_instances = rds.get_list_instances()
        list_instance = ec2_instances + rds_instances
        if _instance == "all":
            instances = list_instance
        else:
            instances = get_instance_id(_instance, list_instance, True)

        if instances:
            for _instance in instances:
                attachments.append(print_instance_tag(_instance))
        else:
            attachments.append({
                "text": constants.MESSAGE_INSTANCE_NOT_FOUND,
                "color": "#119300"
            })
            return attachments

        return attachments

    @classmethod
    def aws_set_schedule(cls, schedule):
        """
        aws schedule command using for set schedule turn-on and turn-off instance
        """
        # Check instance
        timestamp = datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')
        response_text = "Set schedule successfully:\n"
        for command in schedule["commands"]:
            if command["cmd_text"] == "turnon" or command["cmd_text"] == "turnoff":
                # Check if input instance exist
                list_instance = ec2.get_list_instances() + rds.get_list_instances()
                instances = get_instance_id([command["instance_tag"]], list_instance, False)
                if len(instances) == 0:
                    return constants.MESSAGE_INSTANCE_NOT_FOUND
                rule_name = '{0}_{1}_{2}_{3}'.format(
                    schedule["requester"], command["cmd_text"], command["instance_tag"], timestamp)
                rule_description = '{0} `{1}` with cron expression {2}'.format(
                    command["cmd_text"], command["instance_tag"], command["cron_express"]).capitalize()
                # Create rule
                cmd_text = '{0}+{1}'.format(command["cmd_text"], command["instance_tag"])
                target_input = '{"body":"' + constants.AUTO_TRIGGER_EVENT_BODY.format(
                    schedule["requester"], rule_name, command["is_loop"], command["cmd"], cmd_text) + '"}'
                cw_events.create_rule(rule_name, rule_description,
                                      command["cron_express"], constants.LAMBDA_FUNCTION_NAME, target_input)
                response_text = '{0}*- Rule `{1}`:*\n      {2}\n'.format(
                    response_text, rule_name, rule_description)

        return response_text

    @classmethod
    def aws_delete_schedule(cls, rule_name):
        """
        aws delete a schedule by rule name
        """
        rules = cw_events.list_rules()["Rules"]
        for rule in rules:
            if rule["Name"] == rule_name:
                cw_events.delete_rule(rule_name)
                return "Deleted schedule `{0}`".format(rule_name)

        return "Rule `{0}` not exists!".format(rule_name)

    @classmethod
    def aws_list_schedule(cls, schedule):
        """
        aws list all rules
        """
        list_rules = cw_events.list_rules()
        attachment = print_schedule_list_info(list_rules)

        return attachment

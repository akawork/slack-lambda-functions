"""
Define all function using for AWS EC2
"""

import json
import boto3
from aws import constants

INSTANCES = boto3.resource('ec2', region_name=constants.REGION)
CLIENT = boto3.client('ec2', region_name=constants.REGION)


def get_list_instances():
    """
    Get all instances
    """
    instances = []
    response = CLIENT.describe_instances()
    reservations = response.get('Reservations')
    if reservations:
        for reservation in reservations:
            instance = json.loads('{"InstanceId": " ", ' + '"TagName":" ", ' +
                                  '"PrivateIpAddresses":" ", ' +
                                  '"PublicIpAddress":" ", ' +
                                  '"InstanceType":" ", ' + '"State":" ", ' +
                                  '"ServiceType":" "}')
            instance_value = reservation.get("Instances")[0]
            instance["ServiceType"] = "ec2"
            instance["InstanceId"] = instance_value.get("InstanceId")
            instance["PrivateIpAddresses"] = instance_value.get(
                "PrivateIpAddress")
            instance["InstanceType"] = instance_value.get("InstanceType")
            instance["PublicIpAddress"] = instance_value.get("PublicIpAddress")

            state = instance_value.get("State")
            instance["State"] = state.get("Name")

            if instance_value.get("Tags"):
                for tag in instance_value.get("Tags"):
                    if tag.get("Key") == "Name":
                        instance["TagName"] = tag.get("Value")

            instances.append(instance)
        return instances
    return None


def start_all_instance(instances):
    """
    Start all instances
    """
    if instances:
        instance_ids = []
        text = ""

        for instance in instances:
            if instance["State"] == "stopped":
                instance_ids.append(instance["InstanceId"])
                text = text + 'The instance `' + str(
                    instance["TagName"]) + '` starting!\n'
            else:
                text = "{0}Can not `turn-on` instance `{1}` because of Instance in `{2}`!\n".format(
                    text, str(instance["TagName"]), str(instance["State"]))

        if instance_ids:
            CLIENT.start_instances(InstanceIds=instance_ids)

        return text
    return constants.MESSAGE_INSTANCE_NOT_FOUND


def stop_all_instance(instances):
    """
    Stop all instances
    """
    if instances:
        instance_ids = []
        text = ""

        for instance in instances:
            if instance["State"] == "running":
                instance_ids.append(instance["InstanceId"])
                text = text + 'The instance `' + str(
                    instance["TagName"]) + '` stopping!\n'
            else:
                text = "{0}Can not `turn-off` instance `{1}` because of Instance in `{2}`!\n".format(
                    text, str(instance["TagName"]), str(instance["State"]))

        if instance_ids:
            CLIENT.stop_instances(InstanceIds=instance_ids)

        return text
    return constants.MESSAGE_INSTANCE_NOT_FOUND


def start_instance(instance):
    """
    Start an instance
    """
    instance_ids = []
    text = ""
    if instance["State"] == "stopped":
        instance_ids.append(instance["InstanceId"])
        CLIENT.start_instances(InstanceIds=instance_ids)
        text = text + 'The EC2 instance `' + str(
            instance["TagName"]) + '` is starting!\n'
    else:
        text = "{0}Can not `turn-on` instance `{1}` because of Instance in `{2}`!\n".format(
            text, str(instance["TagName"]), str(instance["State"]))

    return text


def stop_instance(instance):
    """
    Stop an instance
    """
    instance_ids = []
    text = ""
    if instance["State"] == "running":
        instance_ids.append(instance["InstanceId"])
        CLIENT.stop_instances(InstanceIds=instance_ids)
        text = text + 'The EC2 instance `' + str(
            instance["TagName"]) + '` is stopping!\n'
    else:
        text = "{0}Can not `turn-off` instance `{1}` because of Instance in `{2}`!\n".format(
            text, str(instance["TagName"]), str(instance["State"]))

    return text

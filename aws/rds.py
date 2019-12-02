"""
Define all function using for AWS RDS
"""

import json
import boto3
from aws import constants

RDS = boto3.client('rds', region_name=constants.REGION)


def get_list_instances():
    """
    Get all instance
    """
    instances = []
    response = RDS.describe_db_instances()
    db_instances = response.get("DBInstances")

    if db_instances:
        for item in db_instances:
            instance = json.loads('{"InstanceId":" ", ' + '"TagName":" ", ' +
                                  '"Endpoint":" ", ' +
                                  '"EngineVersion":" ", ' +
                                  '"InstanceType":" ", ' + '"State":" ", ' +
                                  '"Engine":" ", ' + '"ServiceType":" "}')
            instance["ServiceType"] = "rds"
            instance["InstanceId"] = item.get("DBInstanceIdentifier")
            instance["InstanceType"] = item.get("DBInstanceClass")
            instance["Engine"] = item.get("Engine")
            instance["TagName"] = item.get("DBInstanceIdentifier")
            instance["State"] = item.get("DBInstanceStatus")
            instance["Endpoint"] = item.get("Endpoint")["Address"]
            instance["EngineVersion"] = item.get("EngineVersion")
            instances.append(instance)
        return instances
    return None


def start_all_instance(instances):
    """
    Start all instances
    """
    text = ""
    if instances:
        for instance in instances:
            if instance["State"] == "stopped":
                RDS.start_db_instance(
                    DBInstanceIdentifier=str(instance["InstanceId"]))
                text = "{0}The instance `{1}` starting!\n".format(
                    text, instance["TagName"])
            else:
                text = "{0}Can not `turn-on` instance `{1}` because of Instance in `{2}`!\n".format(
                    text, instance["TagName"], instance["State"])

        return text
    return constants.MESSAGE_INSTANCE_NOT_FOUND


def stop_all_instance(instances):
    """
    Stop all instances
    """
    text = ""
    if instances:
        for instance in instances:
            if instance["State"] == "available":
                RDS.stop_db_instance(
                    DBInstanceIdentifier=str(instance["InstanceId"]))
                text = "{0}The instance `{1}` stopping!\n".format(
                    text, str(instance["TagName"]))
            else:
                text = "{0}Can not `turn-off` instance `{1}` because of Instance in `{2}`!\n".format(
                    text, str(instance["TagName"]), str(instance["State"]))

        return text
    return constants.MESSAGE_INSTANCE_NOT_FOUND


def start_instance(instance):
    """
    Start an instance
    """
    text = ""
    if instance["State"] == "stopped":
        RDS.start_db_instance(
            DBInstanceIdentifier=str(instance["InstanceId"]))
        text = "{0}The RDS instance `{1}` is starting!\n".format(
            text, str(instance["TagName"]))
    else:
        text = "{0}Can not `turn-on` instance `{1}` because of Instance in `{2}`!\n".format(
            text, str(instance["TagName"]), str(instance["State"]))

    return text


def stop_instance(instance):
    """
    Stop an instance
    """
    text = ""
    if instance["State"] == "available":
        RDS.stop_db_instance(
            DBInstanceIdentifier=str(instance["InstanceId"]))
        text = "{0}The RDS instance `{1}` is stopping!\n".format(
            text, str(instance["TagName"]))
    else:
        text = "{0}Can not `turn-off` instance `{1}` because of Instance in `{2}`!\n".format(
            text, str(instance["TagName"]), str(instance["State"]))

    return text

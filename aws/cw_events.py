"""
Define all function using for AWS CloudWatch Event
"""

import boto3
from aws import constants
from aws import aws_lambda

# Create CloudWatchEvents client
CW_EVENTS = boto3.client('events', region_name=constants.REGION)


def create_rule(rule_name, rule_description, cron_expression, function_name, target_input):
    """
    Create an event and push to AWS
    """
    funct = aws_lambda.find_function(function_name)
    # Put an event rule
    CW_EVENTS.put_rule(Name=rule_name,
                       Description=rule_description,
                       ScheduleExpression=cron_expression,
                       State='ENABLED')
    CW_EVENTS.put_targets(Rule=rule_name,
                          Targets=[{
                              'Arn': funct["FunctionArn"].replace(':' + funct["Version"], ''),
                              'Id': funct["FunctionName"],
                              'Input': str(target_input)
                          }])


def list_rules():
    """
    List all rules
    """
    response = CW_EVENTS.list_rules()
    return response


def delete_rule(rule_name):
    """
    Delete an event and push to AWS
    """
    # Delete all targets of rule first
    targets = CW_EVENTS.list_targets_by_rule(Rule=rule_name)["Targets"]
    if len(targets) > 0:
        target_ids = []
        for target in targets:
            target_ids.append(target["Id"])
        CW_EVENTS.remove_targets(Rule=rule_name, Ids=target_ids)
    CW_EVENTS.delete_rule(Name=rule_name)

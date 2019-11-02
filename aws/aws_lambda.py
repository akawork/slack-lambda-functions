"""
Define all function using for AWS Lambda Functions
"""

import boto3
from aws import constants

LAMBDA = boto3.client('lambda', region_name=constants.REGION)


def find_function(function_name):
    """
    Find an Lambda Function
    """
    response = LAMBDA.list_functions(FunctionVersion='ALL')
    for funct in response["Functions"]:
        if funct["FunctionName"] == function_name:
            return funct
    return "Lambda Function not found!"


def add_invoke_function_permission(statement_id, function_name):
    # Make source_arn as statement id
    LAMBDA.add_permission(StatementId=statement_id, FunctionName=function_name, Principal='events.amazonaws.com',
                          Action='lambda:InvokeFunction')


def remove_permission(statement_id, function_name):
    # Remove permission with statement_id
    LAMBDA.remove_permission(FunctionName=function_name, StatementId=statement_id)

"""
Slack Information Values
"""
TOKEN = ""
TEAM_ID = ""
CHANNEL_IDS = [""]
USER_IDS = [""]
COMMANDS = ["turnon", "turnoff"]
REGION = 'us-east-1'
RESPONSE = {"response_type": "in_channel", "text": None, "attachments": []}
SLACK_APPROVAL_CHANNEL_ID = ''
ADMIN_USER_IDS = [""]
SLACK_APPROVAL_ROOM_WEEBHOOK = ''

"""
Messages response
"""
MESSAGE_WRONG_COMMAND = 'Command wrong format!'
MESSAGE_INSTANCE_NOT_FOUND = 'Instance not found!'
MESSAGE_APPROVAL_USER = "Your request need approval. Please wait!"
MESSAGE_DATE_TIME_INCORRECT = 'The input time parameter is incorrect! The format should be same as `2016/4/15-08:27`'

"""
Lambda Function Information
"""
LAMBDA_FUNCTION_NAME = 'slackbot'
LAMBDA_INVOKE_FUNCTION_ID = 'lambda-invoke-function-id'

"""
Date Time
"""
LOCAL_TIMEZONE = +7

import boto3
import os
from botocore.config import Config

aws_region = os.environ.get('AWS_REGION')

my_config = Config(
    region_name = aws_region
)

client = boto3.client('ec2', config=my_config)

def on_event(event, context):
  print(event)
  request_type = event['RequestType']
  if request_type == 'Create': return on_create()
  if request_type == 'Update': return on_update()
  if request_type == 'Delete': return on_delete()
  raise Exception("Invalid request type: %s" % request_type)


def on_create():
  prefix_lists = client.describe_managed_prefix_lists(
    Filters=[
        {
            'Name': 'prefix-list-name',
            'Values': [
                'com.amazonaws.global.cloudfront.origin-facing',
            ]
        },
    ]
)
  data = {
    "prefix_lists": prefix_lists["PrefixLists"][0]["PrefixListId"]
  }
  return { 'Data': data }

def on_update():
    return on_create()

def on_delete():
    print("Just delete the ENV variable")
    return

def handler(event, context):
    return on_event(event, context)
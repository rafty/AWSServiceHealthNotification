# -*- coding: utf-8 -*-
import os
import urllib.request
import xml.etree.ElementTree as et
from datetime import datetime, timezone
import logging
import boto3


logger = logging.getLogger()
logger.setLevel(logging.INFO)

sns = boto3.client('sns')

services = {
    "ap-northeast-1": {
        "Transfer for SFTP": 'https://status.aws.amazon.com/rss/transfer-ap-northeast-1.rss',
        "EC2": "https://status.aws.amazon.com/rss/ec2-ap-northeast-1.rss",
    },
    "us-east-1": {
        "EC2": 'https://status.aws.amazon.com/rss/ec2-us-east-1.rss'
    },
    "global": {
        "Console": "https://status.aws.amazon.com/rss/management-console.rss",
        "Route53": "https://status.aws.amazon.com/rss/route53.rss"
    }
}


# AWS Lambda environment variables
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']


def pub_date_to_utc(pub_date):
    # e.g. pub_date: Thu, 22 Aug 2019 23:40:01 PDT
    logger.info('pub_date: {}'.format(pub_date))
    elements = pub_date.split(' ')

    if elements[-1] == 'PDT':
        _date = elements[1:-1]
        _date.append('-0700')
        _pub_date = ' '.join(_date)
        utc_time = datetime.strptime(_pub_date, '%d %b %Y %H:%M:%S %z').\
            astimezone(timezone.utc)
        return utc_time
    elif elements[-1] == 'PCT':
        _date = elements[1:-1]
        _date.append('-0800')
        _pub_date = ' '.join(_date)
        utc_time = datetime.strptime(_pub_date, '%d %b %Y %H:%M:%S %z').\
            astimezone(timezone.utc)
        return utc_time
    else:
        raise ValueError('datetime format error: {}'.format(pub_date))


def rss_read(url):
    """
    return: item(dict) list
    item: {
       'pub_date':
          datetime.datetime(2019,8,23,11,18,35,tzinfo=datetime.timezone.utc),
       'description':
          'The majority of impaired EC2 instances and EBS...'
    }
    """
    root = et.fromstring(urllib.request.urlopen(url).read())

    items = list()
    for item in root.iter('item'):
        pub_date = pub_date_to_utc(item[2].text)
        description = item[4].text
        items.append(dict(pub_date=pub_date, description=description))

    logger.info('item list: {}'.format(items))
    return items


def message_format(item, aws_service, region):
    message = 'AWS Service Error!!\n'\
              '{} in {}\n'\
              'UTC:{}\n\nMESSAGE:\n{}'\
        .format(
            aws_service,
            region,
            item['pub_date'].strftime('%Y/%m/%d %H:%M:%S'),
            item['description'])

    logger.info(message)
    return message


def alert_service_status(items, aws_service, region):
    """
    - Send to CloudWatch Logs
    - CloudWatch Scheduled Events every 5 minutes
    - 5 minutes x 2 minutes = 600 seconds
    - Notify Items within the last 10 minutes
    """

    logger.info('xml: {}'.format(items))

    for item in items:
        delta = datetime.now(timezone.utc) - item['pub_date']

        # if delta.total_seconds() <= 60 * 5 * 2 * 10000000:  # for test
        if delta.total_seconds() <= 60 * 5 * 2:
            message = message_format(item, aws_service, region)
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Message=message,
                Subject='Alert! AWS Service Error. {} in {}'.format(
                    aws_service, region))
            logger.info('Message published: {} in {}'.format(
                aws_service, region))


def lambda_handler(event, context):
    logger.info('event: {}'.format(event))
    try:
        region = 'ap-northeast-1'
        aws_service = 'Transfer for SFTP'
        items = rss_read(services.get(region).get(aws_service))
        if len(items):
            alert_service_status(items, aws_service, region)
        else:
            logger.info('Normal Operation: AWS Service {} in {}'.format(
                aws_service, region))

    except Exception as e:
        logger.error('Error: {}'.format(str(e)))

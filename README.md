# AWSServiceHealthNotification

AWS Transfer for SFTPはAWS Personal Health Dashboardでサポートされてない。
そのサービスのステータスをAWS Service Health Dashboardから取得しメール通知する。

動作仕様
1. AWS CloudWatch Schedule Eventで起動されたAWS Lambda functionがAWS Personal Health Dashboardから情報(xml)を取得する。

2｡ AWS Lambda functionは取得した情報(xml)から通知すべき情報があれば、AWS SNSを使ってmail通知する。


Notify the health status of "AWS Transfer for SFTP"

AWS Transfer for SFTP is not supported by the AWS Personal Health Dashboard.
Get the status of the service from the AWS Service Health Dashboard and send an email notification.

Operating specifications
1. AWS Lambda function started by AWS CloudWatch Schedule Event gets information (xml) from AWS Personal Health Dashboard.

2. AWS Lambda function sends mail notification using AWS SNS if there is information to be notified from the acquired information (xml).


## Deploying
### Requirements

- AWS Account
- Python 3.7 or greater
- AWS CLI latest

### Instructions

These are the deployment steps until the full implementation is complete.:
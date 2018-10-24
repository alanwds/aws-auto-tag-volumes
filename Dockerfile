FROM python:2.7

ADD aws-auto-tag-volumes.py /

RUN pip install boto3 

CMD [ "python", "./aws-auto-tag-volumes.py" ]

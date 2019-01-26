FROM amazonlinux

RUN yum update -y
RUN yum install python3 -y

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

RUN mkdir -p /home/app/
WORKDIR /home/app/
COPY . ./
CMD ["python3", "update_links.py"]

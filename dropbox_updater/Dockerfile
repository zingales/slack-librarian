FROM amazonlinux:latest

RUN yum install python3 -y && yum -y clean all

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

RUN mkdir -p /home/app/
WORKDIR /home/app/
COPY . ./
CMD ["python3", "update_links.py"]

#!/usr/bin/env python3
# Launch the LLM inference observatory on a g4dn.xlarge (1x T4). Self contained:
# packages ./stack, embeds it in user-data, and boots the compose stack on a
# Deep Learning GPU AMI (drivers + docker + nvidia runtime preinstalled).
import base64, io, os, sys, tarfile, time, boto3

REGION = sys.argv[1] if len(sys.argv) > 1 else "us-east-1"
PROFILE = "llm"
ITYPE = "g4dn.xlarge"
HERE = os.path.dirname(os.path.abspath(__file__))

sess = boto3.Session(profile_name=PROFILE, region_name=REGION)
ec2 = sess.client("ec2")
ssm = sess.client("ssm")

# 1. Deep Learning Base GPU AMI (Ubuntu 22.04), latest, via public SSM param
ami = ssm.get_parameter(Name="/aws/service/deeplearning/ami/x86_64/base-oss-nvidia-driver-gpu-ubuntu-22.04/latest/ami-id")["Parameter"]["Value"]
print("AMI:", ami)

# 2. package ./stack into a tarball -> base64
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w:gz") as tar:
    tar.add(os.path.join(HERE, "stack"), arcname="stack")
blob = base64.b64encode(buf.getvalue()).decode()

user_data = f"""#!/bin/bash
set -x
mkdir -p /opt/obs && cd /opt/obs
echo {blob} | base64 -d | tar xz
cd /opt/obs/stack
for i in $(seq 1 30); do docker info && break; sleep 5; done
docker compose up -d
"""

# 3. security group (open the UI + ssh)
try:
    sg = ec2.create_security_group(GroupName="llm-obs-sg", Description="llm observatory")["GroupId"]
    for port in (22, 3000, 8000, 9090):
        ec2.authorize_security_group_ingress(GroupId=sg, IpProtocol="tcp", FromPort=port, ToPort=port, CidrIp="0.0.0.0/0")
except ec2.exceptions.ClientError:
    sg = ec2.describe_security_groups(GroupNames=["llm-obs-sg"])["SecurityGroups"][0]["GroupId"]
print("SG:", sg)

# 4. launch
r = ec2.run_instances(
    ImageId=ami, InstanceType=ITYPE, MinCount=1, MaxCount=1,
    SecurityGroupIds=[sg],
    BlockDeviceMappings=[{"DeviceName": "/dev/sda1", "Ebs": {"VolumeSize": 100, "VolumeType": "gp3"}}],
    UserData=user_data,
    TagSpecifications=[{"ResourceType": "instance", "Tags": [{"Key": "Name", "Value": "llm-observatory"}]}],
)
iid = r["Instances"][0]["InstanceId"]
print("instance:", iid)
ec2.get_waiter("instance_running").wait(InstanceIds=[iid])
ip = ec2.describe_instances(InstanceIds=[iid])["Reservations"][0]["Instances"][0].get("PublicIpAddress")
print("public ip:", ip)
print(f"Grafana: http://{ip}:3000  (admin/llmobs)  vLLM: http://{ip}:8000/v1")

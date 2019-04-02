#!/usr/bin/python3
import collections
import json
import subprocess

instances = json.loads(subprocess.check_output(["aws", "ec2", "describe-instances"]).decode("utf-8"))

########### ELBs ##########################
elb_prod_arn = 'arn:aws:elasticloadbalancing:eu-west-1:930821752279:targetgroup/dpnk/67c4d6e00abf2f57'
elb_test_arn = 'arn:aws:elasticloadbalancing:eu-west-1:930821752279:targetgroup/dpnk-test/4a530ccfaf7ade97'
def get_targets(elb):
    return json.loads(subprocess.check_output(['aws', 'elbv2', 'describe-target-health', '--target-group-arn', elb,  '--query', 'TargetHealthDescriptions[*].Target.Id']).decode("utf-8"))
elb_prod = get_targets(elb_prod_arn)
elb_test = get_targets(elb_test_arn)
instance_elbs = {}
for instance in elb_prod:
    instance_elbs[instance] = "elb_prod"

for instance in elb_test:
    instance_elbs[instance] = "elb_test"
##########################

states = collections.OrderedDict([
    ('terminated', []),
    ('stopped', []),
    ('pending', []),
    ('initializing', []),
    ('running', []),
])


def get_container_listing(ip):
    container_listing = ""
    print("Getting container listing and versions for ip:", ip)
    try:
        container_listing_raw = subprocess.check_output(["ssh", "-oStrictHostKeyChecking=no", "ubuntu@" + ip, "--", "sudo", "docker", "ps", "--format", "{{.Names}}"]).decode("utf-8") # noqa
        for container in container_listing_raw.splitlines():
            try:
                container_listing += '\n\t\t%s %s' % (container, ' '.join(subprocess.check_output(["ssh", "-oStrictHostKeyChecking=no", "ubuntu@" + ip, "--", "sudo", "docker", "exec", container, "cat", "static/version.txt"]).decode("utf-8").splitlines())) # noqa
            except subprocess.CalledProcessError:
                container_listing += '\n\t\t' + container
    except subprocess.CalledProcessError:
        container_listing = ""
    return container_listing


for instance in instances["Reservations"]:
    i = instance["Instances"][0]
    groupName = ""
    try:
        for tag in i["Tags"]:
            if tag["Key"] == "aws:autoscaling:groupName":
                groupName = tag["Value"]
    except KeyError:
        groupName = "no_tags_set"
    state = i["State"]["Name"]
    if state == "terminated":
        states[state].append("%s %s" % (groupName, state))
        continue
    try:
        ip = i["PublicIpAddress"]
        container_listing = get_container_listing(ip)
    except KeyError:
        ip = "no_ip"
        container_listing = "\n"
    states[state].append(
        "%s %s %s %s %s%s" % (
            groupName,
            state,
            ip,
            i["InstanceId"],
            instance_elbs.get(i['InstanceId'], 'unregistered'),
            container_listing,
        ),
    )

for state, instances in states.items():
    print(state)
    for instance in instances:
        print("\t", instance)

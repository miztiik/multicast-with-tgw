#!/usr/bin/env python3
from stacks.back_end.vpc_stack import VpcStack
from stacks.back_end.tgw_stack import TransitGatewayStack
from stacks.back_end.multicast_on_ec2_stack.multicast_producer_on_ec2_stack import MulticastProducerOnEC2Stack
from stacks.back_end.multicast_on_ec2_stack.multicast_consumer_on_ec2_stack import MulticastConsumerOnEC2Stack
import os

import aws_cdk as cdk


app = cdk.App()

# VPC Stack for hosting Secure workloads & Other resources
vpc_stack = VpcStack(
    app,
    # f"{app.node.try_get_context('project')}-vpc-stack",
    f"multicast-vpc-stack",
    stack_log_level="INFO",
    description="Miztiik Automation: Custom Multi-AZ VPC"
)

# Transit Gateway Stack
tgw_stack = TransitGatewayStack(
    app,
    # f"{app.node.try_get_context('project')}-vpc-stack",
    f"multicast-tgw-stack",
    tgw_asn=64512,
    vpc=vpc_stack.vpc,
    stack_log_level="INFO",
    description="Miztiik Automation: Transit Gateway Stack"
)

# Deploy Multicast Producer On EC2 instance
multicast_producer_stack = MulticastProducerOnEC2Stack(
    app,
    f"multicast-producer-stack",
    stack_log_level="INFO",
    vpc=vpc_stack.vpc,
    ec2_instance_type="t2.micro",
    description="Miztiik Automation: Deploy Multicast Producer On EC2 instance"
)
# Deploy Multicast Consumer On EC2 instance
multicast_consumer_stack = MulticastConsumerOnEC2Stack(
    app,
    f"multicast-consumer-stack",
    stack_log_level="INFO",
    vpc=vpc_stack.vpc,
    ec2_instance_type="t2.micro",
    description="Miztiik Automation: Deploy Multicast Consumer On EC2 instance"
)

# Stack Level Tagging
_tags_lst = app.node.try_get_context("tags")

if _tags_lst:
    for _t in _tags_lst:
        for k, v in _t.items():
            cdk.Tags.of(app).add(
                k, v, apply_to_launched_instances=True, priority=300)

app.synth()

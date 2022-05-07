import aws_cdk as cdk
from aws_cdk import Stack
from constructs import Construct

from stacks.miztiik_global_args import GlobalArgs
from aws_cdk import aws_ec2 as _ec2
from aws_cdk import aws_iam as _iam


class GlobalArgs:
    """
    Helper to define global statics
    """

    OWNER = "MystiqueAutomation"
    ENVIRONMENT = "production"
    REPO_NAME = "multicast-with-tgw"
    SOURCE_INFO = f"https://github.com/miztiik/{REPO_NAME}"
    VERSION = "2022-04-13"
    MIZTIIK_SUPPORT_EMAIL = ["mystique@example.com", ]


class MulticastConsumerOnEC2Stack(cdk.Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        stack_log_level: str,
        vpc,
        ec2_instance_type: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Read BootStrap Script):
        try:
            with open("stacks/back_end/multicast_on_ec2_stack/bootstrap_scripts/deploy_app.sh",
                      encoding="utf-8",
                      mode="r"
                      ) as f:
                user_data = f.read()
        except OSError as e:
            print("Unable to read UserData script")
            raise e

        # Get the latest AMI from AWS SSM
        linux_ami = _ec2.AmazonLinuxImage(
            generation=_ec2.AmazonLinuxGeneration.AMAZON_LINUX_2)

        # Get the latest ami
        amzn_linux_ami = _ec2.MachineImage.latest_amazon_linux(
            generation=_ec2.AmazonLinuxGeneration.AMAZON_LINUX_2
        )
        # ec2 Instance Role
        self._instance_role = _iam.Role(
            self, "webAppClientRole",
            assumed_by=_iam.ServicePrincipal(
                "ec2.amazonaws.com"),
            managed_policies=[
                _iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSSMManagedInstanceCore"
                )
            ]
        )

        # Allow CW Agent to create Logs
        self._instance_role.add_to_policy(_iam.PolicyStatement(
            actions=[
                "logs:Create*",
                "logs:PutLogEvents"
            ],
            resources=["arn:aws:logs:*:*:*"]
        ))

        # app_server Instance
        app_server = _ec2.Instance(
            self,
            "appServer",
            instance_type=_ec2.InstanceType(
                instance_type_identifier=f"{ec2_instance_type}"),
            instance_name="multicast_consumer_01",
            machine_image=amzn_linux_ami,
            vpc=vpc,
            vpc_subnets=_ec2.SubnetSelection(
                subnet_type=_ec2.SubnetType.PRIVATE_WITH_NAT
            ),
            role=self._instance_role,
            user_data=_ec2.UserData.custom(
                user_data)
        )

        # Allow Web Traffic to WebServer
        app_server.connections.allow_from_any_ipv4(
            _ec2.Port.tcp(80),
            description="Allow Incoming HTTP Traffic"
        )

        # app_server.connections.allow_internally(
        #     port_range=_ec2.Port.tcp(3306),
        #     description="Allow Incoming MySQL Traffic"
        # )

        app_server.connections.allow_from(
            other=_ec2.Peer.ipv4(vpc.vpc_cidr_block),
            port_range=_ec2.Port.tcp(80),
            description="Allow Incoming Web Traffic"
        )

        # Allow Multicast UDP
        multicast_consumer_sg = _ec2.CfnSecurityGroup(
            self, "multicastConsumerSG",
            group_description="Allow Multicast Traffic",
            group_name="multicastConsumerSG",
            security_group_ingress=[
                _ec2.CfnSecurityGroup.IngressProperty(
                    ip_protocol="2",
                    cidr_ip=vpc.vpc_cidr_block,
                    description="IGMP Receivers",
                    from_port=0,
                    to_port=65535
                ),
                _ec2.CfnSecurityGroup.IngressProperty(
                    ip_protocol="udp",
                    cidr_ip=vpc.vpc_cidr_block,
                    description="Allow Multicast UDP Ingress",
                    from_port=0,
                    to_port=65535
                ),
                _ec2.CfnSecurityGroup.IngressProperty(
                    ip_protocol="2",
                    cidr_ip="0.0.0.0/32",
                    description="IGMP Querier",
                    from_port=0,
                    to_port=65535
                )
            ],
            security_group_egress=[_ec2.CfnSecurityGroup.EgressProperty(
                ip_protocol="-1",
                cidr_ip="224.0.0.0/4",
                description="Egress multicast traffic (UDP)",
                from_port=0,
                to_port=65535
            )],
            vpc_id=vpc.vpc_id
        )

        # Add Multicast SG to instance
        app_server.add_security_group(_ec2.SecurityGroup.from_security_group_id(
            self, "multicast_consumer_sg1", security_group_id=multicast_consumer_sg.attr_group_id))

        # Allow CW Agent to create Logs
        self._instance_role.add_to_policy(_iam.PolicyStatement(
            actions=[
                "logs:Create*",
                "logs:PutLogEvents"
            ],
            resources=["arn:aws:logs:*:*:*"]
        ))

        ###########################################
        ################# OUTPUTS #################
        ###########################################
        output_0 = cdk.CfnOutput(
            self,
            "AutomationFrom",
            value=f"{GlobalArgs.SOURCE_INFO}",
            description="To know more about this automation stack, check out our github page."
        )
        output_1 = cdk.CfnOutput(
            self,
            "ConsumerPrivateIp",
            value=f"http://{app_server.instance_private_ip}",
            description=f"Private IP of App on EC2"
        )
        output_2 = cdk.CfnOutput(
            self,
            "Ec2ConsumerInstance",
            value=(
                f"https://console.aws.amazon.com/ec2/v2/home?region="
                f"{cdk.Aws.REGION}"
                f"#Instances:search="
                f"{app_server.instance_id}"
                f";sort=instanceId"
            ),
            description=f"Login to the instance using Systems Manager and use curl to access Urls"
        )

import aws_cdk as cdk
from aws_cdk import Stack
from constructs import Construct

from stacks.miztiik_global_args import GlobalArgs
from aws_cdk import aws_ec2 as _ec2


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


class TransitGatewayStack(cdk.Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        tgw_asn: int,
        vpc,
        stack_log_level: str,
        ** kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Transit Gateway
        self.tgw = _ec2.CfnTransitGateway(
            self,
            "tgwForMulticast1",
            amazon_side_asn=tgw_asn,
            auto_accept_shared_attachments="enable",
            default_route_table_association="enable",
            default_route_table_propagation="enable",
            dns_support="enable",
            multicast_support="enable",
            description="Transit Gateway for Multicast",
            tags=[cdk.CfnTag(
                key="Name", value=f"tgwForMulticast1")]

        )

        # Transit Gateway attachment to the VPC
        self.tgw_attachment_1 = _ec2.CfnTransitGatewayAttachment(
            self,
            "tgwForMulticastAttach1",
            transit_gateway_id=self.tgw.ref,
            vpc_id=vpc.vpc_id,
            # subnet_ids=[subnet.subnet_id for subnet in vpc.isolated_subnets],
            subnet_ids=[subnet.subnet_id for subnet in vpc.private_subnets],
            tags=[cdk.CfnTag(
                key="Name", value=f"tgwForMulticastAttach1")]
        )

        # Create MultiCast Domain
        tgw_multicast_domain = _ec2.CfnTransitGatewayMulticastDomain(
            self,
            "tgwMulticastDomain1",
            transit_gateway_id=f"{self.tgw.attr_id}",
            # the properties below are optional
            options={"Igmpv2Support": "enable"},
            tags=[cdk.CfnTag(
                key="Name",
                value=f"tgwMulticastDomain1"
            )]
        )

        priv_subnet_ids = [subnet.subnet_id for subnet in vpc.private_subnets]
        priv_subnet_id_1 = priv_subnet_ids[0]
        priv_subnet_id_2 = priv_subnet_ids[1]

        # MultiCast Domain Association
        tgw_multicast_domain_assn_1 = _ec2.CfnTransitGatewayMulticastDomainAssociation(
            self,
            "tgwMulticastDomainAssn1",
            subnet_id=priv_subnet_id_1,
            transit_gateway_attachment_id=self.tgw_attachment_1.ref,
            transit_gateway_multicast_domain_id=tgw_multicast_domain.ref
        )
        tgw_multicast_domain_assn_2 = _ec2.CfnTransitGatewayMulticastDomainAssociation(
            self,
            "tgwMulticastDomainAssn2",
            subnet_id=priv_subnet_id_2,
            transit_gateway_attachment_id=self.tgw_attachment_1.ref,
            transit_gateway_multicast_domain_id=tgw_multicast_domain.ref
        )

        # Network ACLs for TGW Multicast
        # https://docs.aws.amazon.com/vpc/latest/tgw/how-multicast-works.html

        for subnets in vpc.private_subnets:
            priv_subnets = subnets

        multicast_nacl = _ec2.NetworkAcl(
            self,
            "multicastNacl",
            vpc=vpc,
            subnet_selection=priv_subnets,
            network_acl_name=f"multicastNacl",
        )

        # INBound Rules
        multicast_nacl.add_entry(
            "multicastNaclIngress100",
            rule_number=100,
            cidr=_ec2.AclCidr.any_ipv4(),
            traffic=_ec2.AclTraffic.all_traffic(),
            rule_action=_ec2.Action.ALLOW,
            direction=_ec2.TrafficDirection.INGRESS
        )

        multicast_nacl.add_entry(
            "multicastNaclIngress200",
            rule_number=200,
            cidr=_ec2.AclCidr.ipv4("224.0.0.1/32"),
            traffic=_ec2.AclTraffic.icmp(code=-1, type=-1),
            rule_action=_ec2.Action.ALLOW,
            direction=_ec2.TrafficDirection.INGRESS,
        )
        multicast_nacl.add_entry(
            "multicastNaclIngress300",
            rule_number=300,
            cidr=_ec2.AclCidr.ipv4(vpc.vpc_cidr_block),
            traffic=_ec2.AclTraffic.udp_port_range(0, 65535),
            rule_action=_ec2.Action.ALLOW,
            direction=_ec2.TrafficDirection.INGRESS
        )
        # Outbound Rules
        multicast_nacl.add_entry(
            "multicastNaclEgress100",
            rule_number=100,
            cidr=_ec2.AclCidr.any_ipv4(),
            traffic=_ec2.AclTraffic.all_traffic(),
            rule_action=_ec2.Action.ALLOW,
            direction=_ec2.TrafficDirection.EGRESS
        )
        multicast_nacl.add_entry(
            "multicastNaclEgress200",
            rule_number=200,
            cidr=_ec2.AclCidr.ipv4(vpc.vpc_cidr_block),
            traffic=_ec2.AclTraffic.udp_port_range(0, 65535),
            rule_action=_ec2.Action.ALLOW,
            direction=_ec2.TrafficDirection.EGRESS
        )
        multicast_nacl.add_entry(
            "multicastNaclEgress300",
            rule_number=300,
            cidr=_ec2.AclCidr.ipv4("224.0.0.2/32"),
            traffic=_ec2.AclTraffic.icmp(code=-1, type=-1),
            rule_action=_ec2.Action.ALLOW,
            direction=_ec2.TrafficDirection.EGRESS
        )
        multicast_nacl.add_entry(
            "multicastNaclEgress400",
            rule_number=400,
            cidr=_ec2.AclCidr.ipv4(vpc.vpc_cidr_block),
            traffic=_ec2.AclTraffic.icmp(code=-1, type=-1),
            rule_action=_ec2.Action.ALLOW,
            direction=_ec2.TrafficDirection.EGRESS
        )

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
            "TransitGatewayId",
            value=f"{self.tgw.attr_id}",
            description="Transit Gateway Id."
        )

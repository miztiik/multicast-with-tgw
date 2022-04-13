import aws_cdk as core
import aws_cdk.assertions as assertions

from multicast_with_tgw.multicast_with_tgw_stack import MulticastWithTgwStack

# example tests. To run these tests, uncomment this file along with the example
# resource in multicast_with_tgw/multicast_with_tgw_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = MulticastWithTgwStack(app, "multicast-with-tgw")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })

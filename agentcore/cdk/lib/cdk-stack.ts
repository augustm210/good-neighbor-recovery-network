import { AgentCoreApplication, type AgentCoreProjectSpec } from '@aws/agentcore-cdk';
import { CfnOutput, Stack, type StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';

export interface AgentCoreStackProps extends StackProps {
  spec: AgentCoreProjectSpec;
}

export class AgentCoreStack extends Stack {
  constructor(scope: Construct, id: string, props: AgentCoreStackProps) {
    super(scope, id, props);

    new AgentCoreApplication(this, 'Application', { spec: props.spec });
    new CfnOutput(this, 'StackNameOutput', {
      description: 'Name of the CloudFormation stack',
      value: this.stackName,
    });
  }
}

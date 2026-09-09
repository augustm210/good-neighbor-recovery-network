#!/usr/bin/env node
import { ConfigIO, type AwsDeploymentTarget } from '@aws/agentcore-cdk';
import { App, type Environment } from 'aws-cdk-lib';
import * as path from 'path';
import { AgentCoreStack } from '../lib/cdk-stack';

function environment(target: AwsDeploymentTarget): Environment {
  return { account: target.account, region: target.region };
}

function stackName(projectName: string, targetName: string): string {
  return `AgentCore-${projectName.replace(/_/g, '-')}-${targetName.replace(/_/g, '-')}`;
}

async function main(): Promise<void> {
  const configRoot = path.resolve(process.cwd(), '..');
  const configIO = new ConfigIO({ baseDir: configRoot });
  const spec = await configIO.readProjectSpec();
  const targets = await configIO.readAWSDeploymentTargets();
  if (targets.length === 0) {
    throw new Error('No deployment targets configured in agentcore/aws-targets.json');
  }

  const app = new App();
  for (const target of targets) {
    new AgentCoreStack(app, stackName(spec.name, target.name), {
      spec,
      env: environment(target),
      description: `Good Neighbor AgentCore runtime for ${target.name}`,
      tags: {
        'agentcore:project-name': spec.name,
        'agentcore:target-name': target.name,
      },
    });
  }
  app.synth();
}

main().catch((error: unknown) => {
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
});

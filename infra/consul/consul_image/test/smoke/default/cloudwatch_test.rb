
describe file('/opt/cwlogs/awslogs-agent-setup.py') do
  it { should exist }
end

describe file('/opt/cwlogs/cwlogs.conf') do
  it { should exist }
  its('content') { should match(%r{\[consul_agent\]}) }
end

# do not run the setup script b/c final configuration is deferred to runtime
describe service('awslogs') do
  it { should_not be_installed }
end

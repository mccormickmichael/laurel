describe file('/usr/local/bin/consul') do
  it { should exist }
  it { should be_executable }
end

describe command('/usr/local/bin/consul --version') do
  its('stdout') { should match /v0.8.3/ }
end

describe file('/etc/consul/consul.json') do
  it { should exist }
  its('content') { should_not match(%r{bind_addr}) }
  its('content') { should_not match(%r{retry_join}) }
end

# TODO: config file contents

describe service('consul') do
  it { should be_installed }
end

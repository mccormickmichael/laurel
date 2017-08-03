describe file('/usr/local/bin/consul') do
  it { should exist }
  it { should be_executable }
end

describe command('/usr/local/bin/consul --version') do
  its('stdout') { should match /v0.8.3/ }
end

describe service('consul') do
  it { should be_installed }
end

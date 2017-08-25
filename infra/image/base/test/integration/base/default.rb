['/etc/chef', '/var/lib/chef', '/var/log/chef'].each do |dir|
  describe directory(dir) do
    it { should exist }
  end
end

describe file('/etc/chef/first-boot.json') do
  it { should exist }
end

describe file('/etc/chef/infra-validator.pem') do
  it { should exist }
end

describe file('/etc/chef/first-boot.json') do
  it { should exist }
end

describe file('/etc/chef/client.rb') do
  it { should exist }
  its('content') { should match %r{validation_client_name "infra-validator"} }
  its('content') { should match %r{validation_key "/etc/chef/infra-validator.pem"} }end

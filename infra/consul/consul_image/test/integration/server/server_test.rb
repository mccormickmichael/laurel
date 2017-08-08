describe json('/opt/consul/config/config.json') do
  let(:node) { json('/tmp/kitchen/chef_node.json').params }

  its('bind_addr')  { should eq "#{node['automatic']['ipaddress']}" }
end

describe service('consul') do
  it { should be_installed }
  it { should be_enabled }
  it { should be_running }
end

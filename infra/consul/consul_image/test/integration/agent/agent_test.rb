describe directory('/opt/consul') do
  it { should exist }
  its('group') { should eq 'root' }
  its('owner') { should eq 'root' }
  its('mode') { should cmp '0755' }
end

describe file('/opt/consul/consul') do
  it { should exist }
  it { should be_executable }
  its('group') { should eq 'root' }
  its('owner') { should eq 'root' }
  its('mode') { should cmp '0755' }
end

describe command('/opt/consul/consul --version') do
  let(:node) { json('/tmp/kitchen/chef_node.json').params }  # it would be nice to do this once and have it available everywhere
  let(:version) { node['default']['consul']['agent']['version'] }
  
  its('stdout') { should match /v#{version}/ }

end

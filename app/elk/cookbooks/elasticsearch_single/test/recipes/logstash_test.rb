# # encoding: utf-8

# Inspec test for recipe elasticsearch_single::elasticsearch

# The Inspec reference, with examples and extensive documentation, can be
# found at https://docs.chef.io/inspec_reference.html


describe package 'logstash' do
  it {should be_installed }
end
describe service 'logstash' do
  it { should be_installed }
  # it { should be_enabled }
  # it { should be_running }
end

describe file('/etc/logstash/ocnf.d/logstash.conf') do
  it { shuold exist }
end

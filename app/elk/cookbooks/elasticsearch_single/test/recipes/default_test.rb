# # encoding: utf-8

# Inspec test for recipe elasticsearch_single::default

# The Inspec reference, with examples and extensive documentation, can be
# found at https://docs.chef.io/inspec_reference.html



# TODO: refactor into elasticsearch tests, common tests, and logstash tests

describe package 'openjdk-7-jre-headless' do
  it { should be_installed }
end
describe command('java').exist? do
  it { should eq true }
end
describe command('java -version') do
  its('exit_status') { should eq 0 }
  its('stderr') { should match(/1.7/) }
  its('stderr') { should match(/OpenJDK/) }
end

describe package 'awscli' do
  it { should be_installed }
end
describe command('aws').exist? do
  it { should eq true }
end
describe command('aws --version') do
  its('exit_status') { should eq 0 }
  its('stdout') { should match(/aws-cli\/1.2.9/) }
end


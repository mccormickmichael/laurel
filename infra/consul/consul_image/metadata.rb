name 'consul_image'
maintainer 'ThousandLeaves'
maintainer_email 'michael@thousandleaves.org'
description 'Configures a Consul server AMI'
version '0.1.0'
chef_version '>= 12.1' if respond_to?(:chef_version)

depends 'consul'

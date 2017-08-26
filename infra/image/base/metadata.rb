name 'base'
maintainer 'Thousandleaves'
maintainer_email 'michael@thousandleaves.org'
license 'All Rights Reserved'
description 'Configures base image (e.g. with chef-client bootstrap scripts)'
long_description 'Installs/Configures base image (with chef-client for AWS Chef Automate bootstrap scripts)'
version '0.1.0'
chef_version '>= 12.1' if respond_to?(:chef_version)

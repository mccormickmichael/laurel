#!/bin/sh

# register elasticsearch in apt

wget -qO - https://packages.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -

echo "deb https://packages.elastic.co/elasticsearch/2.x/debian stable main" | sudo tee -a /etc/apt/sources.list.d/elasticsearch-2.x.list


# Whoops, we don't have apt, we have yum

# make sure there's a JVM installed
sudo add-apt-repository ppa:webupd8team/java
sudo apt-get update
sudo apt-get install oracle-java8-installer
java -version

# add the ES key 

rpm --import https://packages.elastic.co/GPG-KEY-elasticsearch

# add this as a file in /etc/yum.repos.d: e.g. slasticsearch.repo

[elasticsearch-2.x]
name=Elasticsearch repository for 2.x packages
baseurl=https://packages.elastic.co/elasticsearch/2.x/centos
gpgcheck=1
gpgkey=https://packages.elastic.co/GPG-KEY-elasticsearch
enabled=1

yum install elasticsearch

# start as a daemon:
# presumably will just work b/c installed as a package

chkconfig --add elasticsearch
service elasticsearch start

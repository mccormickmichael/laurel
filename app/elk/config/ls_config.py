from string import Template

with open('ls_conf.conf', 'r') as f:
    ls_config = f.read()

# this magic file is written out by our userdata script
with open('/tmp/es_network_host', 'r') as f:
    es_network_host = f.read().strip().strip('"')

mapping = {
    'ES_HOST': es_network_host
}
ls_config = Template(ls_config).substitute(mapping)

with open('conf.d/logstash.conf', 'w') as f:
    f.write(ls_config)

# TODO: Does the old ls-tiny need to be deleted?

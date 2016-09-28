from string import Template

with open('kibana_conf', 'r') as f:
    kib_config = f.read()

# this magic file is written out by our userdata script
with open('/tmp/es_network_host', 'r') as f:
    es_network_host = f.read().strip().strip('"')

mapping = {
    'ES_HOST': es_network_host
}
ls_config = Template(kib_config).substitute(mapping)

with open('kibana.yml', 'w') as f:
    f.write(kib_config)

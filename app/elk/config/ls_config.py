import sys
from string import Template

source_file = sys.argv[1]

with open(source_file, 'r') as f:
    ls_config = f.read()

# this magic file is written out by our userdata script
with open('/tmp/es_host', 'r') as f:
    es_host = f.read().strip()

mapping = {
    'ES_HOST': es_host
}
ls_config = Template(ls_config).substitute(mapping)

with open('conf.d/logstash.conf', 'w') as f:
    f.write(ls_config)

# TODO: Does the old ls-tiny need to be deleted?

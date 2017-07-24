# ./enrol.py 10.225.2.96 node_clean
import os
import time
import sys
import commands
import conf

MAX_PARALLELISM_DEGREE = 4

VALID_SCHEDULE_MODES = ['ipmi', 'class', 'random']


def call(cmd):
    print('CMD: %s' % cmd)
    status, output = commands.getstatusoutput(cmd)
    print('STATUS: %s' % status)
    print('OUTPUT: %s' % output)
    return status, output


def find_nodes(node_id):
    nodes = []

    switch_infos = {}
    for line in open('switchs.info'):
        if line.startswith('#'):
            continue
        if len(line.split(",")) == 4:
            ipmi_ip, switch_vendor, switch_version = line.split(",")[0:3]
            switch_infos[ipmi_ip] = (switch_vendor, switch_version)

    for line in open('nodes.info'):
        if line.startswith('#'):
            continue
        print "node info: %s" % line.split(",")

        if len(line.split(",")) == 8:
            ipmi, ipmi_username, ipmi_password, switch_ip_1, switch_port_1, port_mac_1, vendor, server_type_class = line.split(",")
            server_type_class = server_type_class.replace("\n", "")
            port_num = 1
            switch_ip_2, switch_port_2, port_mac_2 = None, None, None
        elif len(line.split(",")) == 11:
            (ipmi, ipmi_username, ipmi_password, switch_ip_1, switch_port_1, port_mac_1,
             switch_ip_2, switch_port_2, port_mac_2, vendor, server_type_class) = line.split(",")
            server_type_class = server_type_class.replace("\n", "")
            port_num = 2
        else:
            continue
        vendor = vendor.replace("\n", "")
        if node_id == 'all' or node_id == ipmi:
            node = {
                'ipmi': ipmi,
                'ipmi_username': ipmi_username,
                'ipmi_password': ipmi_password,
                'switch_ip_1': switch_ip_1,
                'switch_port_1': switch_port_1,
                'switch_vendor_1': switch_infos[ipmi][0].strip(),
                'switch_version_1': switch_infos[ipmi][1].strip(),
                'port_mac_1': port_mac_1,
                'switch_ip_2': switch_ip_2,
                'switch_port_2': switch_port_2,
                'switch_vendor_2': switch_infos[ipmi][0].strip(),
                'switch_version_2': switch_infos[ipmi][1].strip(),
                'port_mac_2': port_mac_2,
                'port_num': port_num,
                'vendor': vendor,
                'repr_mac_1': port_mac_1.replace(':', '-'),
                'repr_mac_2': port_mac_2.replace(':', '-') if port_mac_2 is not None else "",
                'server_type_class': server_type_class
            }
            node['uuid'] = ('00000000-0000-0000-0000-%3s%3s%3s%3s' % tuple(node['ipmi'].split('.'))).replace(' ', '0')
            if vendor == 'HP':
                node['deploy_kernel'] = conf.deploy_kernel_hp
                node['deploy_ramdisk'] = conf.deploy_ramdisk_hp
            if vendor == 'DELL_DIRECTC': # DELL, with direct controller
                node['deploy_kernel'] = conf.deploy_kernel_dell_directc
                node['deploy_ramdisk'] = conf.deploy_ramdisk_dell_directc
            else: # all other vendor, with only raidc
                node['deploy_kernel'] = conf.deploy_kernel_dell
                node['deploy_ramdisk'] = conf.deploy_ramdisk_dell
            nodes.append(node)  
    return nodes


def server_boot(node):
    node['image_id'] = conf.image_id
    node['network_id'] = conf.network_id
    node['hypervisor_name'] = conf.hypervisor_name
    node['admin_pass'] = conf.admin_pass
    schedule_mode = conf.schedule_mode
    is_do_raid = conf.is_do_raid

    cmd = 'nova boot --image %(image_id)s --nic net-id=%(network_id)s --admin-pass %(admin_pass)s' % node

    # check conf
    if schedule_mode not in VALID_SCHEDULE_MODES:
        print('ERROR: conf schedule_mode %s is invalid ! valid are: %s'
              % (schedule_mode, VALID_SCHEDULE_MODES))
        exit(1)
    if not isinstance(is_do_raid, bool):
        print('ERROR: conf is_do_raid %s is invalid ! value type must be bool !')
        exit(1)

    # parse schedule_mode
    if schedule_mode == 'ipmi':
        node['flavor_name'] = conf.flavor_class_name_map['random']
        cmd += ' --flavor %(flavor_name)s' % node
        cmd += ' --availability-zone nova:%(hypervisor_name)s:%(uuid)s' % node
    elif schedule_mode == 'random':
        node['flavor_name'] = conf.flavor_class_name_map['random']
        cmd += ' --flavor %(flavor_name)s' % node
    else:
        node['flavor_name'] = conf.flavor_class_name_map[node['server_type_class']]
        cmd += ' --flavor %(flavor_name)s' % node

    # parse is_do_raid
    if is_do_raid:
        cmd += ' --meta raid_config=\'{"logical_disks": [{"size_gb": "MAX", "disk_type": "hdd", "raid_level": "1", "is_root_volume": true, "volume_name": "root_volume"}, {"size_gb": "MAX", "disk_type": "hdd", "number_of_physical_disks": 4, "raid_level": "5", "volume_name": "data_volume"}]}\''

    # run cmd
    cmd += ' node-%(uuid)s' % node
    call(cmd)


def server_delete(node):
    call('nova delete node-%(uuid)s' % node)


def node_clean(node):
    call('ironic --ironic-api-version latest node-set-provision-state %(uuid)s manage' % node)
    call('ironic --ironic-api-version latest node-set-provision-state %(uuid)s provide' % node)


def node_power_off(node):
    call('ipmitool -I lanplus -H %(ipmi)s -U %(ipmi_username)s -P %(ipmi_password)s chassis power off' % node)


def node_power_on(node):
    call('ipmitool -I lanplus -H %(ipmi)s -U %(ipmi_username)s -P %(ipmi_password)s chassis power on' % node)


def node_delete(node):
    call('ironic --ironic-api-version latest node-set-provision-state %(uuid)s abort' % node)
    call('ironic node-set-maintenance %(uuid)s true' % node)
    call('ironic node-delete %(uuid)s' % node)
    call('ipmitool -I lanplus -H %(ipmi)s -U %(ipmi_username)s -P %(ipmi_password)s chassis power off' % node)


def node_create(node):
    call('ironic node-create -d pxe_ipmitool -u %(uuid)s' % node)
    call('ironic node-update %(uuid)s add driver_info/ipmi_address=%(ipmi)s' % node)
    call('ironic node-update %(uuid)s add driver_info/ipmi_port=623' % node)
    call('ironic node-update %(uuid)s add driver_info/ipmi_username=%(ipmi_username)s' % node)
    call('ironic node-update %(uuid)s add driver_info/ipmi_password=%(ipmi_password)s' % node)
    call('ironic node-update %(uuid)s add driver_info/deploy_kernel=%(deploy_kernel)s' % node)
    call('ironic node-update %(uuid)s add driver_info/deploy_ramdisk=%(deploy_ramdisk)s' % node)
    call('ironic node-update %(uuid)s add properties/cpus=1000' % node)
    call('ironic node-update %(uuid)s add properties/memory_mb=1024000' % node)
    call('ironic node-update %(uuid)s add properties/local_gb=1024000' % node)
    call('ironic node-update %(uuid)s add properties/cpu_arch=x86_64' % node)
    call('ironic node-update %(uuid)s add instance_info/root_gb=1024000' % node)
    call('ironic node-update %(uuid)s add instance_info/capabilities=\'{"boot_option":"local"}\'' % node)
    call('ironic node-update %(uuid)s add properties/capabilities=type:%(server_type_class)s' % node)
    call('ironic node-set-power-state %(uuid)s off' % node)

    if node['port_num'] == 1:
        call('ironic --ironic-api-version latest port-create -n %(uuid)s -a %(port_mac_1)s -l '
             'switch_id=00:00:00:00:00:00 -l switch_info=manage_ip:%(switch_ip_1)s,'
             'switch_vendor:%(switch_vendor_1)s,switch_version:%(switch_version_1)s,'
             'port_mac:%(repr_mac_1)s -l port_id="%(switch_port_1)s"'
             ' --pxe-enabled true' % node)
    else:
        status, output = call('ironic --ironic-api-version latest portgroup-create '
                              '-n %(uuid)s --mode "802.3ad" --standalone-ports-supported true|grep \' uuid\'|awk \'{print $4}\'' % node)
        node['portgroup_uuid'] = output
        call('ironic --ironic-api-version latest port-create -n %(uuid)s --portgroup %(portgroup_uuid)s '
             '-a %(port_mac_1)s -l switch_id=00:00:00:00:00:00 -l switch_info=manage_ip:%(switch_ip_1)s,'
             'switch_vendor:%(switch_vendor_1)s,'
             'switch_version:%(switch_version_1)s,port_mac:%(repr_mac_1)s/%(repr_mac_2)s '
             '-l port_id="%(switch_port_1)s" --pxe-enabled true' % node)
        call('ironic --ironic-api-version latest port-create -n %(uuid)s --portgroup %(portgroup_uuid)s '
             '-a %(port_mac_2)s -l switch_id=00:00:00:00:00:00 -l switch_info=manage_ip:%(switch_ip_2)s,'
             'switch_vendor:%(switch_vendor_2)s,switch_version:%(switch_version_2)s,'
             'port_mac:%(repr_mac_1)s/%(repr_mac_2)s -l port_id="%(switch_port_2)s" --pxe-enabled false' % node)


def update_server_type(node):
    call('ironic node-update %(uuid)s add properties/capabilities=type:%(server_type_class)s' % node)


def network_create():
    call('neutron quota-update --subnet -1 --network -1 --floatingip -1 --port -1 --router -1 --subnetpool -1')
    for i in range(1, 101):
        call('neutron net-create private_%s --provider:segmentation_id %s --provider:network_type vlan --provider:physical_network physnet1 --shared' % (i, 3000+i))
        call('neutron subnet-create private_%s 192.168.%s.0/24 --ip-version=4 --gateway=192.168.%s.1 --disable-dhcp' % (i, i, i))


def network_delete():
    for i in range(1, 101):
        call('neutron net-delete private_%s' % i)


def flavor_create():
    for server_type_class, flavor_name in conf.flavor_class_name_map.items():
        call('nova flavor-create %s %s 102400 100 32' % (flavor_name, flavor_name))
        call('nova flavor-key %s set capabilities:hypervisor_type=ironic' % flavor_name)
        if server_type_class != 'random':
            call('nova flavor-key %s set capabilities:type=%s' % (flavor_name, server_type_class))

def flavor_delete():
    for server_type_class, flavor_name in conf.flavor_class_name_map.items():
        call('nova flavor-delete %s' % flavor_name)
    

def flavor_show():
    for server_type_class, flavor_name in conf.flavor_class_name_map.items():
        call('nova flavor-show %s' % flavor_name)
    

def dryrun(node):
    call('date')


def do_action_with_node(action, nodes):
    # check config
    if conf.parallelism_degree > MAX_PARALLELISM_DEGREE:
        print('ERROR: conf parallelism_degree must <= %s !!!'
              % MAX_PARALLELISM_DEGREE)
        exit(1)
    
    # desice parallelism outside & inside interval 
    if action == 'server_boot':
        parallelism_outside_interval = conf.server_boot_interval
    elif action == 'server_delete':
        parallelism_outside_interval = conf.server_delete_interval
    elif action == 'node_clean':
        parallelism_outside_interval = conf.node_clean_interval
    else:
        parallelism_outside_interval = conf.action_default_interval
    parallelism_inside_interval = conf.parallelism_interval

    # concurrency control
    for i, node in enumerate(nodes):
        # decide interval
        interval = 0
        node_num = i + 1
        if action in conf.parallelism_actions: 
            if node_num != len(nodes):
                if node_num % conf.parallelism_degree != 0:
                    interval = parallelism_inside_interval
                else:
                    interval = parallelism_outside_interval

        # do action
        print('\n%s) %s => %s (next action interval %ss)' %
              (node_num, node['ipmi'], action, interval))
        SUPPORTED_ACTIONS_WITH_NODE[action](node)
        time.sleep(interval)


def do_action_with_no_node(action):
    SUPPORTED_ACTIONS_WITH_NO_NODE[action]()


def usage():
    print 'usage: python enrol.py ACTION [IPMI|all]'
    print 'supported ACTION:'
    print '\tnode_list'
    print '\tnode_list_detail'
    print '\tnetwork_create'
    print '\tnetwork_delete'
    print '\tflavor_create'
    print '\tflavor_delete'
    print '\tflavor_show'
    print '\tnode_create [IPMI|all]'
    print '\tnode_delete [IPMI|all]'
    print '\tnode_power_off [IPMI|all]'
    print '\tnode_power_on [IPMI|all]'
    print '\tnode_clean [IPMI|all]'
    print '\tserver_boot [IPMI|all]'
    print '\tserver_delete [IPMI|all]'
    print '\tdryrun [IPMI|all]'
    print '\tupdate_server_type [IPMI|all]'


def node_list():
    nodes = find_nodes('all')
    for i, node in enumerate(nodes):
        print node['ipmi']


def node_list_detail():
    nodes = find_nodes('all')
    for i, node in enumerate(nodes):
        print('ipmi: %s, detail: %s' % (node['ipmi'], node))


SUPPORTED_ACTIONS_WITH_NODE = {
    'node_create': node_create,
    'node_delete': node_delete,
    'node_power_off': node_power_off,
    'node_power_on': node_power_on,
    'node_clean': node_clean,
    'server_boot': server_boot,
    'server_delete': server_delete,
    'dryrun': dryrun,
    'update_server_type': update_server_type,
}

SUPPORTED_ACTIONS_WITH_NO_NODE = {
    'node_list': node_list,
    'node_list_detail': node_list_detail,
    'network_create': network_create,
    'network_delete': network_delete,
    'flavor_create': flavor_create,
    'flavor_delete': flavor_delete,
    'flavor_show': flavor_show,
    'help': usage,
    '-h': usage,
    '--help': usage,
}

SUPPORTED_ACTIONS = dict(SUPPORTED_ACTIONS_WITH_NODE.items() +
                         SUPPORTED_ACTIONS_WITH_NO_NODE.items())


if __name__ == '__main__':
    if len(sys.argv) == 1:
        usage()
        exit(0)

    # check action
    action = sys.argv[1]
    if action not in SUPPORTED_ACTIONS:
        print('ERROR: ACTION %s not support !\n' % action)
        usage()
        exit(1)

    # do action
    if len(sys.argv) == 2:
        if action not in SUPPORTED_ACTIONS_WITH_NO_NODE:
            print('ERROR: ACTION %s must specified [IPMI|all] !\n' % action)
            usage()
            exit(1)
        do_action_with_no_node(action)
    else:
        if action in SUPPORTED_ACTIONS_WITH_NO_NODE:
            do_action_with_no_node(action)
        else:
            node = sys.argv[2]
            nodes = find_nodes(node)
            do_action_with_node(action, nodes)

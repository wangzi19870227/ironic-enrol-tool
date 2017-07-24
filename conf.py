import commands


cmd = 'hostname'
net = 'neutron net-list |grep \'public\' |awk -F \'|\' \'{print $2}\''
(status1, output1) = commands.getstatusoutput(cmd)
if status1 != 0:
    raise IOError("hostname get faild")
(status2, output2) = commands.getstatusoutput(net)
if status2 != 0:
    raise IOError("neutron get net_id faild")


# for node deploy / clean
deploy_kernel_hp = '00000000-0000-0000-0000-000010000001'
deploy_ramdisk_hp = '00000000-0000-0000-0000-000010000002'
deploy_kernel_dell = '00000000-0000-0000-0000-000020000001'
deploy_ramdisk_dell = '00000000-0000-0000-0000-000020000002'
deploy_kernel_dell_directc = '00000000-0000-0000-0000-000030000001'
deploy_ramdisk_dell_directc = '00000000-0000-0000-0000-000030000002'

# for server boot
image_id = '00000000-0000-0000-0000-216040000002'
network_id = output2.split()[0]
hypervisor_name = output1
admin_pass = 'qiugaoqs'
flavor_class_name_map = {'random': 'plato-stp-enrol-random',
                         'comm1': 'plato-stp-enrol-comm1',
                         'comm2': 'plato-stp-enrol-comm2',
                         'calc1': 'plato-stp-enrol-calc1',
                         'calc2': 'plato-stp-enrol-calc2',
                         'stor1': 'plato-stp-enrol-stor1',
                         'stor2': 'plato-stp-enrol-stor2',
                         'stor3': 'plato-stp-enrol-stor3',
                         'hio1': 'plato-stp-enrol-hio1'}

# Schedule mode for server boot. Now support: ipmi, class, random.
# Default is ipmi.
#     ipmi mode: force schedule server on specified ipmi node, 
#                no mater what baremetal class is;
#     random mode: schedule server on a random node,
#                  no mater what baremetal class is;
#     class mode: schedule server on a node witch belong to this
#                 specified server type class;
schedule_mode = 'ipmi'

# Raid control
# Default is True.
# if True, this will make root_volume raid 1, and data_volume raid 5
is_do_raid = True


# action intervals
# unit: sec
# NOTICE:
#    Do not modify these configurations,
#    unless you know what you're doing
server_boot_interval = 30 * 60
server_delete_interval = 5 * 60
node_clean_interval = 5 * 60
action_default_interval = 1

# concurrency control
# NOTICE:
#    parallelism_degree must <= 4 !!!
#    Do not modify these configurations,
#    unless you know what you're doing
parallelism_degree = 1
parallelism_interval = 60
parallelism_actions = ['server_boot',
                       'server_delete',
                       'node_clean']

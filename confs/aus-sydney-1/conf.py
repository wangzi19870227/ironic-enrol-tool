# for node deploy / clean
deploy_kernel = 'c9b01d5c-e03b-42a2-b4b1-587fe446a2d6'
deploy_ramdisk = '38061b31-5d0f-41ab-8539-fd89bbd64584'

# for server boot
image_id = '00000000-0000-0000-0000-216040000002'
flavor_name = 'baremetal-flavor'
network_id = 'b397c38a-4fc4-4997-aa8a-187b7d00e928'
hypervisor_name = 'controller-10-200.aus-sydney-1.lcs.i-lecloud.com'
admin_pass = 'qiugaoqs'

# action intervals
# unit: sec
server_boot_interval = 30 * 60
server_delete_interval = 5 * 60
node_delete_interval = 5 * 60
action_default_interval = 1

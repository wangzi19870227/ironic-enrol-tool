## NOTICE about conf.py
> **conf about node deploy / clean**
>
> - deploy_kernel_hp, download from http://yum-production.plato.lecloud.com/images/ironic-deploy-proliant-latest.vmlinuz;
> - deploy_ramdisk_hp, download from http://yum-production.plato.lecloud.com/images/ironic-deploy-proliant-latest.initramfs;
> - deploy_kernel_dell, download from http://yum-production.plato.lecloud.com/images/ironic-deploy-mega-latest.vmlinuz;
> - deploy_ramdisk_dell, download from http://yum-production.plato.lecloud.com/images/ironic-deploy-mega-latest.initramfs;
> - deploy_kernel_dell_directc, download from http://yum-production.plato.lecloud.com/images/ironic-deploy-mega-directc-latest.vmlinuz;
> - deploy_ramdisk_dell_directc, download from http://yum-production.plato.lecloud.com/images/ironic-deploy-mega-directc-latest.initramfs;

> **concurrency control**
>
> - parallelism_degree, must <= 4

> **schedule control**
>
> - schedule_mode = 'ipmi'
> - Schedule mode for server boot. Now support: ipmi, class, random. Default is ipmi.
> - ipmi mode: force schedule server on specified ipmi node, no mater what baremetal class is;
> - random mode: schedule server on a random node, no mater what baremetal class is;
> - class mode: schedule server on a node witch belong to this specified server type class;

> **raid control**
>
> - is_do_raid = True
> - Default is True. if True, this will make root_volume raid 1, and data_volume raid 5.

## NOTIC ablout nodes.info

**read nodes.info.sample for reference !**

> **support following format:**
>
> - ipmi, ipmi_username, ipmi_password, switch_ip_1, switch_port_1, port_mac_1, vendor, class
> - ipmi, ipmi_username, ipmi_password, switch_ip_1, switch_port_1, port_mac_1, switch_ip_2, switch_port_2, port_mac_2, vendor, class

>**vendor support:**
>
> - HP
> - DELL
> - SHUGUANG
> - LANGCHAO
> - DELL_DIRECTC

> **class support:**
>
> - comm1
> - comm2
> - calc1
> - calc2
> - stor1
> - stor2
> - stor3
> - hio1

Reference: http://wiki.letv.cn/pages/viewpage.action?pageId=68860310


## Get Started
**step 0: read usage**
- run `python enrol`
- or run `python enrol -h`
- or run `python enrol --help`

**step 1: config enrol**
- prepare conf.py on-demand.
- prepare nodes.info on-demand. Notice: before this, you need read nodes.info.sample first !
- prepare switchs.info on-demand

**step 2: init env**
- init networks, run cmd `python enrol network_create`
- init flavors, run cmd `python enrol flavor_create`

**step 3: register**
`python enrol.py node_create [IPMI|all]`

**step 4: deploy**
`python enrol.py server_boot [IPMI|all]`

**step 5: clean**
`python enrol.py server_delete [IPMI|all]`

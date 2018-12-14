#!/usr/bin/env python

from .InventoryFilter import InventoryFilter
from .InventoryProviders import get_all_drivers
from .InventoryProviders import get_inv_formatter


class GenericInventory(InventoryFilter):

    def __init__(self, inv_format="cfg"):
        InventoryFilter.__init__(self)
        self.filter_classes = get_all_drivers()
        self.inv_formatter = get_inv_formatter(inv_format)()

    def get_host_data(self, res_output, config):
        """
        """
        host_data = {}
        for inv_filter in self.filter_classes:
            data = self.filter_classes[inv_filter]()\
                .get_host_data(res_output, config)
            host_data[inv_filter] = data
        return host_data

    def get_host_ips(self, host_data):
        """
        Returns a list of hostnames from each provider's hosts

        :param host_data
            map of host data for each provider
        """

        hosts = []
        for inv_filter in self.filter_classes:
            data = self.filter_classes[inv_filter]()\
                .get_host_ips(host_data[inv_filter])
            hosts.extend(data)
        return hosts


    def get_hosts_by_count(self, host_dict, count, sort_order):
        """
        currently this function gets all the ips/hostname according to the
        order in which inventories are specified. later can be modified
        to work with user input
        """

        all_hosts = []
        for provider in sort_order:
            all_hosts.extend(host_dict[provider].keys())
        return all_hosts[:count]

    def populate_config(self, host_dict, res_output, config):
        """
        """
        populated_config = {}
        for provider in host_dict.keys():
            for host in host_dict[provider].keys():
                populated_config[host] = {}
                for var in config[provider]:
                    value = self.filter_classes[provider]().\
                        get_field_values(res_output, var)
                    populated_config[host][var] = value
        return populated_config

    def get_inventory(self, res_output, layout, topology, config):
        # get the provisioning order
        sort_order = []
        for resource_group in topology["resource_groups"]:
            if not (resource_group.get("resource_group_type") in sort_order):
                sort_order.append(resource_group.get("resource_group_type"))
        # get all the topology host_ips
        host_data = self.get_host_data(res_output, config)
        # sort it based on topology
        # get the count of all layout hosts needed
        layout_host_count = self.get_layout_hosts(layout)
        # generate hosts list based on the layout host count
        inven_hosts = self.get_hosts_by_count(host_data,
                                              layout_host_count,
                                              sort_order)
        # adding sections to respective host groups
        host_groups = self.get_layout_host_groups(layout)

        self.inv_formatter.add_sections(host_groups)
        # set children for each host group
        self.inv_formatter.set_children(layout)
        # set vars for each host group
        self.inv_formatter.set_vars(layout)
        # add ip addresses to each host
        self.inv_formatter.add_ips_to_groups(inven_hosts, layout)
        # add common vars to host_groups
        self.inv_formatter.add_common_vars(host_groups, layout, host_data)
        return self.inv_formatter.generate_inventory()
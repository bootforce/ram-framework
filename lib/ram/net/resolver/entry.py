#!/usr/bin/python

import ram.context
import ram.widgets


with ram.context(__name__):
    from net.utils import ValidateDomainList, ValidateEmptyOrIpV4

from ram.widgets import *


def SwitchPeerDnsDevice(config, delta):
    ifaces = config['ifaces'].split()
    current = config['peerdns'] if config['peerdns'] else "no"
    options = ["no"] + ifaces[:]

    ifname = options[(options.index(current) + delta) % len(options)]

    config['peerdns'] = ifname if ifname in ifaces else ""


def SelectPeerDnsDevice(config, ensure=False):
    ifaces = config['ifaces'].split()
    current = config['peerdns'] if config['peerdns'] else "no"
    options = ["no"] + ifaces[:]

    if current not in options:
        if not ram.widgets.AskViaButtons(
            "Incorrect DNS over DHCP",
            "Current DHCP interface for obtaining DNS `%s`\n"
            "is not available or configured at the moment.\n\n"
            "What would you like to do with DNS over DHCP?\n" % current,
            "Select device ...", "Keep `%s`" % current
        ):
            return
    elif ensure:
        return

    ifname = ram.widgets.SingleChoice("Obtain DNS addresses over DHCP?", "", options, current=current)
    if ifname == current:
        return

    config['peerdns'] = ifname if ifname in ifaces else ""


def EditIfaceDnsServers(config):
    current = config['peerdns']

    if current and not ram.widgets.AskViaButtons(
        "Use static configuration?",
        "Current DNS configuration set to obtain DNS addresses via DHCP protocol using interface:\n\n\t%s\n\n"
        "Would you like to use static configuration?\n" % current
    ):
        return

    domains, pri_dns, sec_dns = ram.widgets.RunEntry(
        "Interface DNS configuration",
        "Specify domain search list, primary and secondary DNS addresses.",
        [
            ("Search list", config['domains'], ValidateDomainList),
            ("Primary", config['pri_dns'], ValidateEmptyOrIpV4),
            ("Secondary", config['sec_dns'], ValidateEmptyOrIpV4),
        ]
    )

    if not pri_dns and sec_dns:
        pri_dns, sec_dns = sec_dns, pri_dns

    config['peerdns'] = ""
    config['domains'] = domains
    config['pri_dns'] = pri_dns
    config['sec_dns'] = sec_dns


def RunDnsConfigurationMenu(config, wizard):
    def __SelectPeerDnsDevice(action):
        if action == ram.widgets.ACTION_SET:
            SelectPeerDnsDevice(config)
        elif action == ram.widgets.ACTION_INC:
            SwitchPeerDnsDevice(config, +1)
        elif action == ram.widgets.ACTION_DEC:
            SwitchPeerDnsDevice(config, -1)

    def __EditPrimaryDnsServer(action):
        EditIfaceDnsServers(config)

    def __EditSecondaryDnsServer(action):
        EditIfaceDnsServers(config)

    def __EditDomainSearchList(action):
        EditIfaceDnsServers(config)

    if not config['pri_dns'] and config['sec_dns']:
        config['pri_dns'], config['sec_dns'] = config['sec_dns'], config['pri_dns']

    def __MkDnsConfigurationMenu():
        domains = "dhcp" if config['peerdns'] else config['domains']
        pri_dns = "dhcp" if config['peerdns'] else config['pri_dns']
        sec_dns = "dhcp" if config['peerdns'] else config['sec_dns']
        peerdns = config['peerdns'] if config['peerdns'] else "no"

        return [
            ("%-16s < %6s >" % ("Use DHCP:", peerdns.center(6)), __SelectPeerDnsDevice),
            ("", 1),
            ("%-16s %s" % ("Search list:", domains), __EditDomainSearchList),
            ("%-16s %-15s" % ("Primary DNS:", pri_dns), __EditPrimaryDnsServer),
            ("%-16s %-15s" % ("Secondary DNS:", sec_dns), __EditSecondaryDnsServer),
        ]

    SelectPeerDnsDevice(config, ensure=True)

    ram.widgets.RunMenu(
        "Select Action - Resolver",
        __MkDnsConfigurationMenu,
        itemExit=wizard,
        doAction=True
    )


def ModifyPeerDnsDevice(config, ifname):
    ifaces = config['ifaces'].split()
    current = config['peerdns']

    if not ifname in ifaces:
        return ram.widgets.ShowError(
            ifname,
            "No suitable device found on the machine.",
        )

    if current == ifname:
        return

    if not current and not ram.widgets.AskViaButtons(
        "Use dynamic configuration?",
        "Current DNS configuration set to use static DNS addresses:\n\n\t%s\n\t%s\n\n"
        "Would you like to obtain DNS addresses via DHCP protocol using interface:\n\n\t%s\n\n?" % (
            config['pri_dns'], config['sec_dns'], ifname,
        )
    ):
        return

    if current in ifaces and not ram.widgets.AskViaButtons(
        "Change device to obtain DNS addresses?",
        "Current DNS configuration set to obtain DNS addresses via DHCP protocol using interface:\n\n\t%s\n\n"
        "Would you like to obtain DNS addresses via DHCP protocol using interface:\n\n\t%s\n\n?" % (
            current, ifname
        )
    ):
        return

    config['peerdns'] = params.device

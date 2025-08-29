#!/usr/bin/env python3

# IPv4/v6 Calculator
# Converted from the original Perl script by Krischan Jodies
# Original Copyright (C) Krischan Jodies 2000 - 2021
# Python conversion by Gemini
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS for A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

import argparse
import ipaddress
import sys
import math

VERSION = '0.51 (Python Conversion)'

# --- Color Definitions ---
class Colors:
    """ANSI color codes for terminal output."""
    BLUE = "\033[34m"
    NORMAL = "\033[m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    MAGENTA = "\033[35m"
    GREEN = "\033[32m"
    ERROR = "\033[31m"
    
    @staticmethod
    def disable():
        """Disables all color output."""
        for attr in dir(Colors):
            if isinstance(getattr(Colors, attr), str) and getattr(Colors, attr).startswith("\033"):
                setattr(Colors, attr, "")

# --- HTML Definitions ---
class Html:
    """HTML tags for colorized output."""
    BLUE = '<font color="#0000ff">'
    NORMAL = '<font color="#000000">'
    YELLOW = '<font color="#909090">' # Binary
    RED = '<font color="#ff0000">'    # Netmask
    MAGENTA = '<font color="#009900">'# Class
    GREEN = '<font color="#663366">'  # Subnet bits
    FONT_END = '</font>'
    BREAK = "<br>"
    
    @staticmethod
    def disable():
        """Disables HTML output by emptying tags."""
        for attr in dir(Html):
            if isinstance(getattr(Html, attr), str) and getattr(Html, attr).startswith("<"):
                setattr(Html, attr, "")

# --- Global State (for formatting) ---
_COLOR_MODE = 'text' # 'text', 'color', 'html'
_CURRENT_COLOR = ''

def set_color(new_color_code):
    """
    Sets the current output color, avoiding redundant ANSI/HTML tags.
    This mimics the behavior of the original Perl script's set_color sub.
    """
    global _CURRENT_COLOR
    if new_color_code == _CURRENT_COLOR:
        return ""
    
    output = ""
    # In HTML mode, we need to close the previous font tag
    if _COLOR_MODE == 'html' and _CURRENT_COLOR != "":
        output += Html.FONT_END

    _CURRENT_COLOR = new_color_code
    output += new_color_code
    return output

def get_class(address: ipaddress.IPv4Address):
    """Determines the class (A, B, C, D, E) of an IPv4 address."""
    first_octet = address.packed[0]
    if first_octet & 0b10000000 == 0:
        return 'A'
    if first_octet & 0b11000000 == 0b10000000:
        return 'B'
    if first_octet & 0b11100000 == 0b11000000:
        return 'C'
    if first_octet & 0b11110000 == 0b11100000:
        return 'D'
    return 'E'

def get_netblock_description(network: ipaddress.IPv4Network):
    """Returns a description for well-known netblocks (e.g., private ranges)."""
    descriptions = {
        "10.0.0.0/8": ("Private Internet", "http://www.ietf.org/rfc/rfc1918.txt"),
        "172.16.0.0/12": ("Private Internet", "http://www.ietf.org/rfc/rfc1918.txt"),
        "192.168.0.0/16": ("Private Internet", "http://www.ietf.org/rfc/rfc1918.txt"),
        "127.0.0.0/8": ("Loopback", "http://www.ietf.org/rfc/rfc1700.txt"),
        "169.254.0.0/16": ("APIPA", "http://www.ietf.org/rfc/rfc3330.txt"),
        "224.0.0.0/4": ("Multicast", "http://www.ietf.org/rfc/rfc3171.txt"),
    }
    for block_str, (desc, url) in descriptions.items():
        block = ipaddress.ip_network(block_str)
        if network.overlaps(block):
            if network.subnet_of(block):
                return (desc, url)
            return (f"Partially overlaps with {desc}", url)
    return (None, None)

def print_line(label, addr, network, old_network=None, show_class_bits=False, show_binary=True):
    """Prints a formatted line of IP information."""
    
    is_netmask = label.lower() == 'netmask'
    
    addr_str = str(addr)
    if is_netmask and isinstance(addr, ipaddress.IPv4Address):
        addr_str += f" = {network.prefixlen}"
    if label.lower() == 'network':
        addr_str += f"/{network.prefixlen}"

    if _COLOR_MODE == 'html':
        print('<tr>')
        print(f'  <td><tt>{set_color(Html.NORMAL)}{label+":":<11s}{Html.FONT_END}</tt></td>')
        print(f'  <td><tt>{set_color(Html.BLUE)}{addr_str:<21s}{Html.FONT_END}</tt></td>')
    else:
        print(f"{set_color(Colors.NORMAL)}{label+':':<11s} {set_color(Colors.BLUE)}{addr_str:<21s}", end="")

    if show_binary:
        binary_str = f"{int(addr):032b}"
        
        # Colorize binary output
        bits_out = []
        if _COLOR_MODE in ['color', 'html']:
            color_map = {
                'text': Colors,
                'color': Colors,
                'html': Html
            }[_COLOR_MODE]

            c_normal = color_map.NORMAL
            c_binary = color_map.YELLOW
            c_mask = color_map.RED
            c_class = color_map.MAGENTA
            c_subnet = color_map.GREEN
            
            # Default color
            current_color = c_mask if is_netmask else c_binary
            if show_class_bits:
                current_color = c_class
            
            bits_out.append(set_color(current_color))

            for i, bit in enumerate(binary_str):
                # Class bit coloring (for network address)
                if show_class_bits and i > 0 and binary_str[i-1] == '1' and bit == '0':
                    show_class_bits = False
                    bits_out.append(set_color(c_binary))

                # Delineate netmask sections
                if i == network.prefixlen or (old_network and i == old_network.prefixlen):
                     bits_out.append(" ")
                     if not is_netmask:
                         if i == network.prefixlen and old_network and network.prefixlen > old_network.prefixlen:
                             bits_out.append(set_color(c_subnet))
                         elif old_network and i == old_network.prefixlen:
                             bits_out.append(set_color(c_binary))
                
                bits_out.append(bit)
                
                if (i + 1) % 8 == 0 and i < 31:
                    bits_out.append(f"{set_color(c_normal)}.{set_color(current_color)}")

            bits_out.append(set_color(c_normal))
        else:
            bits_out.append(binary_str[:network.prefixlen])
            bits_out.append(" ")
            bits_out.append(binary_str[network.prefixlen:])

        if _COLOR_MODE == 'html':
             print(f'  <td><tt>{"".join(bits_out)}</tt></td>')
        else:
             print(f' {"".join(bits_out)}')
    
    if _COLOR_MODE == 'html':
        print('</tr>')
    else:
        # if not showing binary, we still need a newline
        if not show_binary:
            print()

def print_network_info(network: ipaddress.IPv4Network, old_network=None, show_binary=True):
    """Prints the full details for a given network."""
    if _COLOR_MODE == 'html':
        print('<table border="0" cellspacing="0" cellpadding="0">')

    print_line("Network", network.network_address, network, old_network, show_class_bits=True, show_binary=show_binary)
    if network.prefixlen < 31:
        print_line("HostMin", network.network_address + 1, network, old_network, show_binary=show_binary)
        print_line("HostMax", network.broadcast_address - 1, network, old_network, show_binary=show_binary)
        print_line("Broadcast", network.broadcast_address, network, old_network, show_binary=show_binary)
    elif network.prefixlen == 31: # Point-to-Point
        print_line("HostMin", network.network_address, network, old_network, show_binary=show_binary)
        print_line("HostMax", network.broadcast_address, network, old_network, show_binary=show_binary)
    
    hosts_count = network.num_addresses
    if network.prefixlen < 31:
        hosts_count -= 2
    if hosts_count < 0:
        hosts_count = 0

    if _COLOR_MODE == 'html':
        print('<tr>')
        print(f'  <td><tt>{set_color(Html.NORMAL)}Hosts/Net:{Html.FONT_END}</tt></td>')
        print(f'  <td colspan="2"><tt>{set_color(Html.BLUE)}{hosts_count}{Html.FONT_END}</tt></td>')
        print('</tr>')
    else:
        print(f"{set_color(Colors.NORMAL)}Hosts/Net:  {set_color(Colors.BLUE)}{hosts_count}")

    # Class and Netblock Info
    desc, url = get_netblock_description(network)
    class_info = get_class(network.network_address)
    info_parts = []
    
    if _COLOR_MODE in ['color', 'html']:
        color_map = {'color': Colors, 'html': Html}[_COLOR_MODE]
        info_parts.append(f"{set_color(color_map.MAGENTA)}Class {class_info}{set_color(color_map.NORMAL)}")
        if network.prefixlen == 31:
            info_parts.append("PtP Link RFC 3021")
        if desc:
            if _COLOR_MODE == 'html':
                 info_parts.append(f'<a href="{url}">{desc}</a>')
            else:
                 info_parts.append(desc)
    else:
        info_parts.append(f"Class {class_info}")
        if network.prefixlen == 31:
            info_parts.append("PtP Link RFC 3021")
        if desc:
            info_parts.append(desc)

    info_str = ", ".join(info_parts)
    if _COLOR_MODE == 'html':
        print('<tr>')
        print(f'<td colspan="3">{set_color(Html.NORMAL)}{info_str}{Html.FONT_END}</td>')
        print('</tr></table>')
        print('<br>')
    else:
        print(info_str)
        print(set_color(Colors.NORMAL))


def format_ipv6_binary(address: ipaddress.IPv6Address):
    """Formats an IPv6 address into its binary representation with colons."""
    binary_str = f"{int(address):0128b}"
    parts = [binary_str[i:i+16] for i in range(0, 128, 16)]
    return ":".join(parts)

def handle_ipv6_calculation(network: ipaddress.IPv6Network, address: ipaddress.IPv6Address, show_binary=True):
    """Prints the details for a given IPv6 network, mimicking the original Perl script."""
    # Select the correct color palette based on the mode
    if _COLOR_MODE == 'html':
        C = Html
    else:
        C = Colors

    # Address line
    line = (f"{set_color(C.NORMAL)}{'Address:':<9s}"
          f"{set_color(C.BLUE)}{str(address):<40s}")
    if show_binary:
          line += f"{set_color(C.YELLOW)}{format_ipv6_binary(address)}"
    print(line)
    
    # Netmask line
    line = (f"{set_color(C.NORMAL)}{'Netmask:':<9s}"
            f"{set_color(C.BLUE)}{network.prefixlen:<40d}")
    if show_binary:
        netmask_binary = f"{int(network.netmask):0128b}"
        netmask_bin_formatted = ":".join([netmask_binary[i:i+16] for i in range(0, 128, 16)])
        line += f"{set_color(C.RED)}{netmask_bin_formatted}" # Using RED for consistency
    print(line)

    # Prefix line
    line = (f"{set_color(C.NORMAL)}{'Prefix:':<9s}"
            f"{set_color(C.BLUE)}{str(network):<40s}")
    if show_binary:
        line += f"{set_color(C.YELLOW)}{format_ipv6_binary(network.network_address)}"
    print(line)
    
    # Reset color at the end
    print(set_color(C.NORMAL))


def handle_split_network(network: ipaddress.IPv4Network, sizes: list):
    """Handles network splitting (VLSM)."""
    
    # Calculate required block size for each host count
    # Size must be a power of 2, and accommodate network/broadcast addresses
    needed_blocks = []
    for i, size in enumerate(sizes):
        # We need size + 2 addresses (network + broadcast)
        actual_size = size + 2
        # Find the next power of 2
        power = math.ceil(math.log2(actual_size))
        block_size = 2**power
        needed_blocks.append({'original_size': size, 'block_size': block_size, 'original_index': i})

    # Sort by largest block size first to allocate contiguously
    needed_blocks.sort(key=lambda x: x['block_size'], reverse=True)

    total_needed = sum(b['block_size'] for b in needed_blocks)
    if total_needed > network.num_addresses:
        print(f"{set_color(Colors.ERROR)}Error: The requested subnet sizes ({total_needed} addresses) "
              f"exceed the capacity of the provided network ({network.num_addresses} addresses).{set_color(Colors.NORMAL)}", file=sys.stderr)
        return

    current_address = network.network_address
    allocated_subnets = [None] * len(sizes)
    
    for block in needed_blocks:
        prefix = 32 - int(math.log2(block['block_size']))
        subnet = ipaddress.ip_network((current_address, prefix))
        allocated_subnets[block['original_index']] = subnet
        current_address += block['block_size']
        
    print(f"Splitting {network} into subnets for hosts: {', '.join(map(str, sizes))}\n")
    for i, subnet in enumerate(allocated_subnets):
        print(f"{i+1}. Requested size: {sizes[i]} hosts (requires block of {subnet.num_addresses})")
        print_line("Netmask", subnet.netmask, subnet, network)
        print_network_info(subnet, network)

def main():
    """Main function to parse arguments and perform calculations."""
    parser = argparse.ArgumentParser(
        description='An IP subnet calculator, converted from the original Perl script.',
        epilog='Examples:\n'
               '  ipcalc.py 192.168.0.1/24\n'
               '  ipcalc.py 192.168.0.0/24 26\n'
               '  ipcalc.py 192.168.0.0/24 -s 50 20 10\n'
               '  ipcalc.py 10.0.0.5 - 10.0.0.18\n',
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument('params', nargs='*', help='ADDRESS[/MASK] [MASK] [MASK2]')

    # Options matching the original script
    parser.add_argument('-k', '--color', action='store_true', help='Display ANSI color codes (default on tty).')
    parser.add_argument('-n', '--nocolor', action='store_true', help="Don't display ANSI color codes.")
    parser.add_argument('-b', '--nobinary', action='store_true', help='Suppress the bitwise output.')
    parser.add_argument('--class', dest='print_class', action='store_true', help='Just print the class of the given address.')
    parser.add_argument('-H', '--html', action='store_true', help='Display results as HTML.')
    parser.add_argument('-v', '--version', action='store_true', help='Print version information and exit.')
    parser.add_argument('-s', '--split', nargs='+', type=int, help='Split network into subnets of given sizes (hosts).')
    
    args = parser.parse_args()

    if args.version:
        print(VERSION)
        sys.exit(0)

    if not args.params and not args.version:
        parser.print_help()
        sys.exit(1)
    
    # --- Setup output mode ---
    global _COLOR_MODE
    if args.html:
        _COLOR_MODE = 'html'
        print("<!DOCTYPE HTML><html><head><title>ipcalc</title></head><body><pre>")
    elif args.color or (sys.stdout.isatty() and not args.nocolor):
        _COLOR_MODE = 'color'
    else:
        _COLOR_MODE = 'text'
        Colors.disable()

    # --- Deaggregation / Range Mode ---
    if len(args.params) > 1 and args.params[1] == '-':
        try:
            start_ip = ipaddress.ip_address(args.params[0])
            end_ip = ipaddress.ip_address(args.params[2])
            print(f"Deaggregating range: {start_ip} - {end_ip}\n")
            for network in ipaddress.summarize_address_range(start_ip, end_ip):
                print(network)
            sys.exit(0)
        except (ValueError, IndexError) as e:
            print(f"{set_color(Colors.ERROR)}Invalid range specified. Use: <IP1> - <IP2>. Error: {e}{set_color(Colors.NORMAL)}", file=sys.stderr)
            sys.exit(1)

    # --- Standard Calculation Mode ---
    try:
        # First, try to parse just the address to detect version
        test_addr = ipaddress.ip_address(args.params[0].split('/')[0])

        if isinstance(test_addr, ipaddress.IPv6Address):
            # --- IPv6 Path ---
            address_part = args.params[0]
            network_str = address_part
            if '/' not in network_str:
                if len(args.params) > 1:
                    network_str += f"/{args.params[1]}"
                else:
                    # Default prefix for IPv6, mimicking original script's behavior
                    network_str += "/64"
            
            initial_network = ipaddress.ip_network(network_str, strict=False)
            initial_address = ipaddress.ip_address(address_part.split('/')[0])
            handle_ipv6_calculation(initial_network, initial_address, show_binary=not args.nobinary)
            sys.exit(0)

        # --- IPv4 Path ---
        address_part = args.params[0]
        netmask2_arg = None

        # Determine network string and second netmask based on provided parameters
        if '/' in address_part:
            # Format: ADDRESS/MASK [MASK2]
            network_str = address_part
            if len(args.params) > 1:
                netmask2_arg = args.params[1]
        else:
            # Format: ADDRESS [MASK1] [MASK2]
            network_str = address_part
            if len(args.params) > 1:
                # MASK1 is present
                network_str += f"/{args.params[1]}"
                if len(args.params) > 2:
                    netmask2_arg = args.params[2]
            else:
                # No MASK1, use classful default
                temp_addr = ipaddress.ip_address(network_str)
                addr_class = get_class(temp_addr)
                if addr_class == 'A':
                    network_str += '/8'
                elif addr_class == 'B':
                    network_str += '/16'
                else: # C, D, E
                    network_str += '/24'
            
        initial_network = ipaddress.ip_network(network_str, strict=False)
        initial_address = ipaddress.ip_address(address_part.split('/')[0])
        
    except (ValueError, IndexError) as e:
        print(f"{set_color(Colors.ERROR)}Invalid address or netmask provided. Error: {e}{set_color(Colors.NORMAL)}", file=sys.stderr)
        sys.exit(1)

    if args.print_class:
        print(f"Class: {get_class(initial_address)}")
        sys.exit(0)
    
    # --- Split mode ---
    if args.split:
        handle_split_network(initial_network, args.split)
        sys.exit(0)

    # --- Default/Subnet/Supernet mode ---
    if _COLOR_MODE == 'html':
        print('<table border="0" cellspacing="0" cellpadding="0">')
    
    print_line("Address", initial_address, initial_network, show_binary=not args.nobinary)
    print_line("Netmask", initial_network.netmask, initial_network, show_binary=not args.nobinary)
    print_line("Wildcard", initial_network.hostmask, initial_network, show_binary=not args.nobinary)
    
    if _COLOR_MODE == 'html':
        print('<tr><td colspan="3"><hr></td></tr>')
    else:
        print("=>")

    if _COLOR_MODE == 'html':
        print('</table>')

    print_network_info(initial_network, show_binary=not args.nobinary)

    # Handle second netmask for subnetting/supernetting
    if netmask2_arg:
        try:
            new_prefix = int(netmask2_arg)
            if not (0 <= new_prefix <= 32):
                 raise ValueError("Prefix must be between 0 and 32.")
                 
            if new_prefix > initial_network.prefixlen:
                print(f"--- Subnets for {initial_network} transitioning to /{new_prefix} ---\n")
                subnets = list(initial_network.subnets(new_prefix=new_prefix))
                for i, subnet in enumerate(subnets):
                    if i >= 1000: # Safety break like in original script
                        print("... stopped at 1000 subnets ...")
                        break
                    print(f"{i+1}.")
                    print_network_info(subnet, initial_network, show_binary=not args.nobinary)
            
            elif new_prefix < initial_network.prefixlen:
                print(f"--- Supernet of {initial_network} transitioning to /{new_prefix} ---\n")
                supernet = initial_network.supernet(new_prefix=new_prefix)
                print_network_info(supernet, show_binary=not args.nobinary)

        except ValueError as e:
            print(f"{set_color(Colors.ERROR)}Invalid second netmask: {e}{set_color(Colors.NORMAL)}", file=sys.stderr)
            sys.exit(1)

    if _COLOR_MODE == 'html':
        print("</pre></body></html>")

if __name__ == '__main__':
    main()






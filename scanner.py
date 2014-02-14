import nmap
scanner = nmap.PortScanner()

scanner.scan('127.0.0.1', '22-443')

for host in scanner.all_hosts
    if scanner[host]['status']['state'] == up
# Make sure this is only "OPEN" ports
ports = scanner['127.0.0.1']['tcp'].keys()

for port in ports:
    scanner

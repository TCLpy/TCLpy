# rules.tcl - Live Tcl DSL ruleset running over tclpy

proc on_packet {} {
    set proto [packet protocol]
    set dport [packet dst_port]
    set src   [packet src]

    # Flag potential cleartext management/remote access
    if {$dport == 23} {
        alert "Insecure Telnet traffic identified from $src"
    } elseif {$dport == 22} {
        log "SSH session activity observed: $src"
    }

    # Example filter query rule
    if {$proto eq "DNS"} {
        log "DNS Query processed for destination [packet dst]"
    }
}

# rules.tcl - Hot-reloadable security signature ruleset

rule telnet_detect {
    set severity high
    if {[packet dst_port] == 23} {
        alert "Legacy Telnet remote management session identified" $severity
    }
}

rule ssh_monitor {
    set severity low
    if {[packet dst_port] == 22} {
        log "SSH handshake activity observed from [packet src]"
    }
}

rule dns_anomaly_check {
    set severity medium
    if {[packet has DNS] && [packet contains "admin"]} {
        alert "Suspicious keyword 'admin' found in DNS traffic payload!" $severity
    }
}
rule web_traffic_monitor {
    if {[packet dst_port] == 80 || [packet dst_port] == 443} {
        log "Web traffic detected to [packet dst]"
    }
}

rule dns_tunnel_detector {
    if {[packet protocol] eq "DNS"} {
        set q [packet dns_query]
        if {[string length $q] > 30} {
            alert "Suspicious long DNS query observed: $q" HIGH
        }
    }
}
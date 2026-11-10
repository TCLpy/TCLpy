# scripts/network.tcl - Request Interceptor & Network Rules

proc on_before_navigate {url} {
    # Example interceptor logic
    log "Preparing to fetch URL: $url"
    return 1
}

# Define a custom reconnaissance or inspection payload template
proc build_custom_request {target_url user_agent} {
    set headers [dict create \
        "User-Agent" $user_agent \
        "X-Security-Probe" "TCLpy-Security-Analyst-v1" \
        "Accept" "text/html,application/json" \
    ]
    return [list url $target_url headers $headers method "GET"]
}

find temp/* | xargs -I{} sh -c 'printf "%-50s" "{}"; python rl_replay_parser.py {} 2>/dev/null | head -n 1'

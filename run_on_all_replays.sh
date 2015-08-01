find temp/* | xargs -I{} sh -c 'printf "%-50s" "{}"; python rl_replay_parser.py {} 2>&1 | tail -n 1'

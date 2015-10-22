import sys
import pprint

from rl_replay_parser import ReplayParser

if __name__ == '__main__':
    filename = sys.argv[1]
    if not filename.endswith('.replay'):
        sys.exit('Filename {} does not appear to be a valid replay file'.format(filename))

    with open(filename, 'rb') as replay_file:
        results = ReplayParser().parse(replay_file)
        #pprint.pprint(results)

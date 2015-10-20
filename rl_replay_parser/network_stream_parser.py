import pprint
from .reverse_bit_reader import ReverseBitReader

class NetworkStreamParser(object):
    def __init__(self, class_name_lookup, property_name_lookup):
        self.class_name_lookup = class_name_lookup
        self.property_name_lookup = property_name_lookup
        self.actors = {}
        self.property_read_strategies = {
            'unknown' : lambda reader: self._read_bits(reader, 100),
            'Engine.GameReplicationInfo:GameClass': lambda reader: self._read_bits(reader, 230),
            'TAGame.GameEvent_TA:ReplicatedStateIndex': lambda reader: self._read_bits(reader, 85),
            'TAGame.Team_TA:GameEvent': lambda reader: self._read_bits(reader, 33),
            'Engine.PlayerReplicationInfo:PlayerName': lambda reader: self._read_string(reader),
            'Engine.PlayerReplicationInfo:Team': lambda reader: self._read_bits(reader, 33),
            'Engine.PlayerReplicationInfo:bReadyToPlay': lambda reader: self._read_bits(reader, 1),
            'Engine.PlayerReplicationInfo:UniqueId': lambda reader: self._read_bits(reader, 739),
            'TAGame.RBActor_TA:ReplicatedRBState': lambda reader: self._read_variable_vector(reader),
        }

    def parse(self, replay_file):
        reverse_reader = ReverseBitReader(replay_file)
        #self._find_candidate_frame_starts(replay_file)
        #print(reverse_reader.read(4953).bin)
        #reverse_reader.read(19845)
        #print("Data: {}".format(reverse_reader.read(241).bin))

        self._read_network_frame(reverse_reader)
        self._read_network_frame(reverse_reader)

    def _read_network_frame(self, reverse_reader):
        current_time = reverse_reader.read(32, reverse=True).floatbe
        delta_time = reverse_reader.read(32, reverse=True).floatbe
        print("Current time: {}".format(current_time))
        print("Delta time: {}".format(delta_time))

        actors = []

        while True:
            another_actor = reverse_reader.read(1).bool
            print("Another actor?: {}".format(another_actor))

            if not another_actor:
                break

            self._read_network_frame_actor(reverse_reader)
            print("")

    def _read_network_frame_actor(self, reverse_reader):
        actor_id = reverse_reader.read(10, reverse=True).uint
        print("Actor ID: {}".format(actor_id))

        channel_open = reverse_reader.read(1).bool
        print("Channel Open: {}".format(channel_open))
        new_actor = reverse_reader.read(1).bool
        print("New Actor: {}".format(new_actor))

        if new_actor:
            self._read_network_frame_actor_new(actor_id, reverse_reader)
        else:
            self._read_network_frame_actor_existing(actor_id, reverse_reader)

    def _read_network_frame_actor_new(self, actor_id, reverse_reader):
        unknown = reverse_reader.read(1).bool
        print("Unknown Bit: {}".format(unknown))

        type_id = reverse_reader.read(8, reverse=True).uint
        class_name = self.class_name_lookup[type_id]
        self.actors[actor_id] = class_name
        print("Type ID: {} ({})".format(type_id, class_name))

        zeros = reverse_reader.read(24)
        print("Zeros bits ({}): {}".format(zeros.length, zeros.bin))

        vector = self._read_variable_vector(reverse_reader)
        print("Vector: {}".format(vector))
        #if type_id in [44, 70, 79, 80, 180]:
        #    vector = self._read_vector(reverse_reader, 5)
        #    print("Vector: {}".format(vector))
        #elif type_id in [124, 189, 201, 203, 205, 208, 212]:
        #    vector = self._read_vector(reverse_reader, 4)
        #    print("Vector: {}".format(vector))

        if class_name in ['Archetypes.Ball.Ball_Default', 'Archetypes.Car.Car_Default']:
            rotator = self._read_rotator(reverse_reader)
            print("Rotator: {}".format(rotator))

    def _read_serialized_int(self, reverse_reader, max_value=20):
        value = 0
        bits_read = 0

        while True:
            if reverse_reader.read(1).bool:
                value += (1 << bits_read)
            bits_read += 1
            possible_value = value + (1 << bits_read) 
            if possible_value > max_value:
                return value

    def _read_variable_vector(self, reverse_reader):
        length = self._read_serialized_int(reverse_reader) + 2
        x = reverse_reader.read(length, reverse=True).uint
        y = reverse_reader.read(length, reverse=True).uint
        z = reverse_reader.read(length, reverse=True).uint
        return (x, y, z)

    def _read_vector(self, reverse_reader, size):
        length = reverse_reader.read(size, reverse=True).uint + 2
        x = reverse_reader.read(length, reverse=True).uint
        y = reverse_reader.read(length, reverse=True).uint
        z = reverse_reader.read(length, reverse=True).uint
        return (x, y, z)

    def _read_rotator(self, reverse_reader):
        x = self._read_rotator_component(reverse_reader)
        y = self._read_rotator_component(reverse_reader)
        z = self._read_rotator_component(reverse_reader)
        return (x, y, z)

    def _read_rotator_component(self, reverse_reader):
        has_component = reverse_reader.read(1).bool
        if has_component:
            return reverse_reader.read(8, reverse=True).uint
        else:
            return 0

    def _read_network_frame_actor_existing(self, actor_id, reverse_reader):
        actor_class_name = self.actors[actor_id]
        print("Reading properties for {}".format(actor_class_name))

        pprint.pprint(self.property_name_lookup[actor_class_name])
        max_property = max(self.property_name_lookup[actor_class_name].keys())
        while True:
            another_property = reverse_reader.read(1).bool
            print("Another property?: {}".format(another_property))

            if not another_property:
                break

            net_property_id = self._read_serialized_int(reverse_reader, max_value=max_property)
            print("Network Property ID: {}".format(net_property_id))
            property_name = self.property_name_lookup[actor_class_name][net_property_id]
            print("Network Property Name: {}".format(property_name))

            value = self.property_read_strategies[property_name](reverse_reader)
            print("Value: {}".format(value))

    def _read_bits(self, reverse_reader, bits):
        results = reverse_reader.read(bits)
        return results.bin

    def _read_string(self, reverse_reader):
        length = reverse_reader.read(32, reverse=True).uint
        print("Length: {}".format(length))
        return ''.join([reverse_reader.read(8, reverse=True).bytes for x in range(length)][:-1])

    def _read_rigid_body_state(self, reverse_reader):
        self._read_variable_vector(reverse_reader)
        self._read_variable_vector(reverse_reader)
        reverse_reader.read(24)
        self._read_variable_vector(reverse_reader)
        self._read_variable_vector(reverse_reader)

    def _find_candidate_frame_starts(self, replay_file):
        last_time = 0
        last_bit = 0
        last_found = 0
        start_pos = replay_file.pos
        for x in range(0, 100000):
            if x % 1000 == 0:
                print("Trying {}".format(x))

            replay_file.pos = start_pos + ((x / 8) * 8)
            reverse_reader = ReverseBitReader(replay_file)
            reverse_reader.read(x % 8)
            current = reverse_reader.read(32, reverse=True).floatbe
            delta = reverse_reader.read(32, reverse=True).floatbe
            if 0.001 <= current <= 20 and 0.01 <= delta <= 0.4:
                print("***************************")
                print("Frame {} at Bit {}. Size: {}".format(last_time, last_bit, x - last_bit))
                last_time = current
                last_bit = x



from . import ReverseBitReader

class NetworkFrameParser(object):
    def __init__(self, replay_file, property_names_lookup):
        self.reverse_reader = ReverseBitReader(replay_file)
        self.property_names_lookup = {
            # (type_name, network_property_id) => property_name
        }
        self.parsers = {}

    def parse(self, replay_file):
        stream_byte_length = replay_file.read(UINT32)
        start_byte_pos = replay_file.bytepos
        start_pos = replay_file.pos
        print("Network stream start (bytes): {}".format(start_byte_pos))
        print("Network stream start (bits): {}".format(start_pos))

        #self._find_candidate_frame_starts(replay_file)
        reverse_reader.read(19845)
        print("Data: {}".format(reverse_reader.read(241).bin))
        self._read_network_frame(reverse_reader)

        # TODO: Figure this out at a later time

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
            print("Finished reading. next data: {}".format(reverse_reader.read(32, reverse=True).floatbe))
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
        print("Type ID: {}".format(type_id))

        zeros = reverse_reader.read(24)
        print("Zeros bits ({}): {}".format(zeros.length, zeros.bin))

        if type_id in [44, 68, 79, 80, 180]:
            vector = self._read_vector(reverse_reader, 5)
            print("Vector: {}".format(vector))
        elif type_id in [124, 189, 201, 203, 205, 208, 212]:
            vector = self._read_vector(reverse_reader, 4)
            print("Vector: {}".format(vector))

        if type_id in [124, 189]:
            rotator = self._read_rotator(reverse_reader)
            print("Rotator: {}".format(rotator))

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
        while True:
            another_property = reverse_reader.read(1).bool
            print("Another property?: {}".format(another_property))

            if not another_property:
                break

            property_id = reverse_reader.read(6, reverse=True).uint
            print("Property ID: {}".format(property_id))

            def read_rigid_body():
                print("Rotator: {}".format(self._read_rotator(reverse_reader)))
                print("Vector: {}".format(self._read_vector(reverse_reader, 4)))
                print("Vector: {}".format(self._read_vector(reverse_reader, 4)))
                print("Vector: {}".format(self._read_vector(reverse_reader, 4)))
                print("Rotator: {}".format(self._read_vector(reverse_reader, 4)))
                print("Vector: {}".format(self._read_vector(reverse_reader, 4)))
                print("Vector: {}".format(self._read_vector(reverse_reader, 4)))
                print("Vector: {}".format(self._read_vector(reverse_reader, 4)))
                #print("Vector: {}".format(self._read_vector(reverse_reader, 5)))
                #print("Raw Bits: {}".format(reverse_reader.read(24).bin))
                return "A bunch of values..."

            reader_plans = {
                (1, 37): lambda: reverse_reader.read(32, reverse=True).uint,
                (6, 50): read_rigid_body
            }
            try:
                value = reader_plans[(actor_id, property_id)]()
            except KeyError:
                value = reverse_reader.read(200).bin

            print("Value: {}".format(value))

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



import pprint
import sys
import struct
import math

import bitstring

BOOL = 'bool'
UINT32 = 'uintle:32'
UINT64 = 'uintle:64'
FLOAT32 = 'floatle:32'

class ReverseBitReader(object):
    def __init__(self, stream):
        self.stream = stream
        self.latest_chunk = bitstring.BitArray('')

    def read(self, size, reverse=False):
        missing_bits = max(0, size - self.latest_chunk.length)
        missing_bytes = int(math.ceil(missing_bits / 8.0))

        for x in range(missing_bytes):
            next_byte = bitstring.BitArray(self.stream.read(8))
            next_byte.reverse()
            self.latest_chunk.append(next_byte)

        chunk = self.latest_chunk[0:size]
        del self.latest_chunk[0:size]

        if reverse:
            chunk.reverse()

        return chunk

class ReplayParser:
    def parse(self, replay_file):
        data = {}
        # TODO: CRC, version info, other stuff
        crc = replay_file.read('bytes:20')
        header_start = replay_file.read('bytes:24')

        data['header'] = self._read_properties(replay_file)
        unknown = replay_file.read('bytes:8')
        data['level_info'] = self._read_level_info(replay_file)
        data['key_frames'] = self._read_key_frames(replay_file)
        data['network_frames'] = self._read_network_frames(replay_file)
        data['debug_logs'] = self._read_debug_logs(replay_file)
        data['goal_frame_info'] = self._read_goal_frame_infos(replay_file)
        data['packages'] = self._read_packages(replay_file)
        data['objects'] = self._read_objects(replay_file)
        data['names'] = self._read_names(replay_file)
        data['class_index'] = self._read_class_index(replay_file)
        data['class_net_cache'] = self._read_class_net_cache(replay_file)

        return data

    def _read_properties(self, replay_file):
        results = {}

        while True:
            property_info = self._read_property(replay_file)
            if property_info:
                results[property_info['name']] = property_info['value']
            else:
                return results

    def _read_property(self, replay_file):
        name_length = replay_file.read(UINT32)
        property_name = self._read_string(replay_file, name_length)

        if property_name == 'None':
            return None

        type_length = replay_file.read(UINT32)
        type_name = self._read_string(replay_file, type_length)
        length_of_data = replay_file.read(UINT64)

        if type_name == 'IntProperty':
            value = replay_file.read(UINT32)
        elif type_name == 'StrProperty':
            length = replay_file.read(UINT32)
            value = self._read_string(replay_file, length)
        elif type_name == 'FloatProperty':
            value = replay_file.read(FLOAT32)
        elif type_name == 'NameProperty':
            length = replay_file.read(UINT32)
            value = self._read_string(replay_file, length)
        elif type_name == 'ArrayProperty':
            array_length = replay_file.read(UINT32)
            value = [
                self._read_properties(replay_file)
                for x in range(array_length)
            ]

        print('{}: {}'.format(property_name, value))
        return { 'name' : property_name, 'value': value}

    def _read_level_info(self, replay_file):
        map_names = []
        number_of_maps = replay_file.read(UINT32)
        for x in range(number_of_maps):
            map_name_length = replay_file.read(UINT32)
            map_name = self._read_string(replay_file, map_name_length)
            map_names.append(map_name)

        return map_names

    def _read_key_frames(self, replay_file):
        number_of_key_frames = replay_file.read(UINT32)
        key_frames = [
            self._read_key_frame(replay_file)
            for x in range(number_of_key_frames)
        ]
        return key_frames

    def _read_key_frame(self, replay_file):
        time = replay_file.read(FLOAT32)
        frame = replay_file.read(UINT32)
        file_position = replay_file.read(UINT32)
        return {
            'time' : time,
            'frame' : frame,
            'file_position' : file_position
        }

    def _read_network_frames(self, replay_file):
        start_byte_pos = replay_file.bytepos
        start_pos = replay_file.pos
        print("Network stream start (bytes): {}".format(start_byte_pos))
        print("Network stream start (bits): {}".format(start_pos))
        stream_byte_length = replay_file.read(UINT32)
        start_byte_pos = replay_file.bytepos

        self._read_network_frame(replay_file)
        #self._read_network_frame(replay_file)
        #start_pos = replay_file.pos
        #print("Network stream start (bytes): {}".format(start_byte_pos))
        #print("Network stream start (bits): {}".format(start_pos))
        #print("Network stream length (bytes): {}".format(stream_byte_length))
        #self._find_candidate_frame_starts(replay_file)

        #replay_file.pos += 175479
        #self._find_candidate_value(replay_file, 'uint:6', [32, 36])
        #self._find_candidate_vectors(replay_file)

        #replay_file.pos += 4480
        #self._read_network_frame(replay_file)
        #for x in range(100):
        #    self._read_network_frame(replay_file)
        #self._read_network_frame(replay_file)

        # TODO: Figure this out at a later time
        replay_file.bytepos = start_byte_pos + stream_byte_length

    def _read_network_frame(self, replay_file):
        current_time = replay_file.read(FLOAT32)
        delta_time = replay_file.read(FLOAT32)
        print("Current time: {}".format(current_time))
        print("Delta time: {}".format(delta_time))

        reverse_reader = ReverseBitReader(replay_file)

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
            #print(reverse_reader.read(1000).bin)
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
        print("Unknown bits: {}".format(reverse_reader.read(300).bin))

    def _parse_vector(self, replay_file):
        bits_per_component = replay_file.read('uint:4')
        x, y, z = replay_file.readlist(['uint:{}'.format(bits_per_component)] * 3)
        return (x, y, z)


    def _find_candidate_frame_starts(self, replay_file):
        start_pos = replay_file.pos
        for x in range(0, 200000):
            replay_file.pos = start_pos + x
            current = replay_file.read(FLOAT32)
            delta = replay_file.read(FLOAT32)
            if 0.001 <= current <= 50 and 0.01 <= delta <= 0.4:
                print("************** Candidate Frame *****************")
                print("Found at {}: {} with delta {}".format(x, current, delta))
                next_bits = replay_file.read(64).bin
                print("Next Bits: {}".format(next_bits))

        #pprint.pprint([x for x in sorted(found)])

    def _find_candidate_vectors(self, replay_file):
        start_pos = replay_file.pos

        for offset in range(0, 10000):
            replay_file.pos = start_pos + offset
            bits_per_component = replay_file.read('uint:4')
            if 0 < bits_per_component <= 10:
                x, y, z = replay_file.readlist(['uint:{}'.format(bits_per_component)]* 3)
                print("Found at {}: ({}, {}, {}) w/ {} bits each".format(offset, x, y, z, bits_per_component))

    def _find_candidate_value(self, replay_file, value_type, values):
        start_pos = replay_file.pos
        for x in range(0, 10000):
            replay_file.pos = start_pos + x
            actual = replay_file.read(value_type)
            if actual in values:
                print("Found {} at offset {}".format(actual, x))

    def _read_debug_logs(self, replay_file):
        log_size = replay_file.read(UINT32)
        return [
            self._read_debug_log(replay_file)
            for x in range(log_size)
        ]

    def _read_debug_log(self, replay_file):
        frame = replay_file.read(UINT32)
        name_length = replay_file.read(UINT32)
        name = self._read_string(replay_file, name_length)
        msg_length = replay_file.read(UINT32)
        msg = self._read_string(replay_file, msg_length)
        return {
            'frame': frame,
            'name' : name,
            'message' : msg
        }

    def _read_goal_frame_infos(self, replay_file):
        number_goal_frame_infos = replay_file.read(UINT32)
        return [
            self._read_goal_frame_info(replay_file)
            for x in range(number_goal_frame_infos)
        ]

    def _read_goal_frame_info(self, replay_file):
        type_length = replay_file.read(UINT32)
        type_name = self._read_string(replay_file, type_length)
        frame_number = replay_file.read(UINT32)
        return {
            'type' : type_name,
            'frame_number': frame_number,
        }

    def _read_packages(self, replay_file):
        number_of_packages = replay_file.read(UINT32)
        return [
            self._read_package(replay_file)
            for x in range(number_of_packages)
        ]

    def _read_package(self, replay_file):
        package_length = replay_file.read(UINT32)
        return self._read_string(replay_file, package_length)

    def _read_objects(self, replay_file):
        number_of_objects = replay_file.read(UINT32)
        return [
            self._read_object(replay_file)
            for x in range(number_of_objects)
        ]

    def _read_object(self, replay_file):
        object_length = replay_file.read(UINT32)
        return self._read_string(replay_file, object_length)

    def _read_names(self, replay_file):
        number_of_names = replay_file.read(UINT32)
        return [
            self._read_name(replay_file)
            for x in range(number_of_names)
        ]

    def _read_name(self, replay_file):
        name_length = replay_file.read(UINT32)
        return self._read_string(replay_file, name_length)

    def _read_class_index(self, replay_file):
        number_of_classes = replay_file.read(UINT32)
        return dict(
            self._read_class_index_item(replay_file)
            for x in range(number_of_classes)
        )

    def _read_class_index_item(self, replay_file):
        class_name_size = replay_file.read(UINT32)
        class_name = self._read_string(replay_file, class_name_size)
        class_id = replay_file.read(UINT32)
        return (class_id, class_name)

    def _read_class_net_cache(self, replay_file):
        array_length = replay_file.read(UINT32)
        return dict(
            self._read_class_net_cache_item(replay_file)
            for x in range(array_length)
        )

    def _read_class_net_cache_item(self, replay_file):
        # Corresponds to the 'id' value in the class index.
        class_id = replay_file.read(UINT32)
        # start/end represent range of the corresponding property elements in the
        # 'objects' array.
        class_index_start = replay_file.read(UINT32)
        class_index_end = replay_file.read(UINT32)
        length = replay_file.read(UINT32)
        data = {
            'class_index_start': class_index_start,
            'class_index_end': class_index_end,
            'properties' : dict(
                self._read_class_net_cache_item_property_map(replay_file)
                for x in range(length)
            )
        }
        return (class_id, data)

    def _read_class_net_cache_item_property_map(self, replay_file):
        property_index = replay_file.read(UINT32)
        property_mapped_id = replay_file.read(UINT32)
        return (property_mapped_id, property_index)

    def _pretty_byte_string(self, bytes_read):
        return ':'.join(format(ord(x), '#04x') for x in bytes_read)

    def _print_bytes(self, bytes_read):
        print('Hex read: {}'.format(self._pretty_byte_string(bytes_read)))

    def _read_string(self, replay_file, length):
        # NOTE(mhildreth): Strip off the final byte, since it will be a zero (null terminator)
        return replay_file.read(8 * length).bytes[:-1]

    def _sniff_bits(self, replay_file, size):
        print('****** Sniff Results *******')
        b = replay_file.read(size)
        print("Binary: {}".format(b.bin))
        if size % 4 == 0:
            print("Hex: {}".format(b.hex))
        if size % 8 == 0:
            print("Int: {}".format(b.intle))
            print("Uint: {}".format(b.uintle))
        if size in [32, 64]:
            print("Float: {}".format(b.floatle))

if __name__ == '__main__':
    filename = sys.argv[1]
    if not filename.endswith('.replay'):
        sys.exit('Filename {} does not appear to be a valid replay file'.format(filename))

    with open(filename, 'rb') as replay_file:
        replay_bit_stream = bitstring.ConstBitStream(replay_file)
        results = ReplayParser().parse(replay_bit_stream)
        try:
            pprint.pprint(results)
            pprint.pprint([x for x in enumerate(results['objects'])])
            for cache_key, cache_value in results['class_net_cache'].items():
                print("Type {} ({})".format(cache_key, results['objects'][cache_key]))
                properties = cache_value.get('properties', {})
                for prop_net_id, object_id in properties.items():
                    print("\t{} -> {} ({})".format(prop_net_id, object_id, results['objects'][object_id]))
        except IOError as e:
            pass

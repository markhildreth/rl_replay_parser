import math
import pprint

import bitstring

from .utils import build_class_name_lookup, build_property_name_lookup
from .network_stream_parser import NetworkStreamParser

BOOL = 'bool'
UINT32 = 'uintle:32'
UINT64 = 'uintle:64'
FLOAT32 = 'floatle:32'


class ReplayParser:
    def parse(self, replay_file):
        replay_file = bitstring.ConstBitStream(replay_file)
        data = {}
        # TODO: CRC, version info, other stuff
        crc = replay_file.read('bytes:20')
        header_start = replay_file.read('bytes:24')

        data['header'] = self._read_properties(replay_file)
        unknown = replay_file.read('bytes:8')
        data['level_info'] = self._read_level_info(replay_file)
        data['key_frames'] = self._read_key_frames(replay_file)

        # Skip over the network stream for now. We'll parse this later
        # after reading necessary lookup info from later in the file
        network_stream_byte_length = replay_file.read(UINT32)
        network_stream_location = replay_file.bytepos
        replay_file.bytepos += network_stream_byte_length

        data['debug_logs'] = self._read_debug_logs(replay_file)
        data['goal_frame_info'] = self._read_goal_frame_infos(replay_file)
        data['packages'] = self._read_packages(replay_file)
        data['objects'] = self._read_objects(replay_file)
        data['names'] = self._read_names(replay_file)
        data['class_index'] = self._read_class_index(replay_file)
        data['class_net_cache'] = self._read_class_net_cache(replay_file)

        class_name_lookup = build_class_name_lookup(data['objects'])
        property_name_lookup = build_property_name_lookup(data['objects'], data['class_net_cache'])

        number_of_frames = data['header']['NumFrames']
        replay_file.bytepos = network_stream_location
        network_stream_parser = NetworkStreamParser(class_name_lookup, property_name_lookup)
        network_stream_parser.parse(replay_file, number_of_frames)

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
        elif type_name == 'ByteProperty':
            key_length = replay_file.read(UINT32)
            key_text = self._read_string(replay_file, key_length)
            value_length = replay_file.read(UINT32)
            value_text = self._read_string(replay_file, value_length)
            value = {key_text: value_text}
        elif type_name == 'QWordProperty':
            value = replay_file.read(64).uint
        elif type_name == 'BoolProperty':
            value = replay_file.read(8).uint == 1
        else:
            print("Unknown property type '{}' for {}".format(type_name, property_name))

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


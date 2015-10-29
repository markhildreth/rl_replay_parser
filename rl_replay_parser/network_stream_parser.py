import pprint
from .reverse_bit_reader import ReverseBitReader

class UnknownObjectError(Exception): pass

class NetworkStreamParser(object):
    def __init__(self, object_name_lookup, property_name_lookup):
        self.object_name_lookup = object_name_lookup
        pprint.pprint(object_name_lookup)
        pprint.pprint(property_name_lookup)
        self.property_name_lookup = property_name_lookup
        self.actors = {}
        self.property_read_strategies = {
            'unknown' : lambda reader: self._read_bits(reader, 100),
            'Engine.GameReplicationInfo:GameClass': lambda reader: self._read_bits(reader, 33),
            'Engine.GameReplicationInfo:ServerName': lambda reader: self._read_string(reader),
            'TAGame.GameEvent_TA:ReplicatedStateIndex': lambda reader: self._read_replicated_state_index(reader),
            'TAGame.Team_TA:GameEvent': lambda reader: self._read_bits(reader, 33),
            'Engine.PlayerReplicationInfo:PlayerName': lambda reader: self._read_string(reader),
            'Engine.PlayerReplicationInfo:Team': lambda reader: self._read_team(reader),
            'Engine.PlayerReplicationInfo:bReadyToPlay': lambda reader: self._read_bits(reader, 1),
            'Engine.PlayerReplicationInfo:UniqueId': lambda reader: self._read_unique_id(reader),
            'Engine.PlayerReplicationInfo:PlayerID': lambda reader: self._read_bits(reader, 71),
            'TAGame.PRI_TA:PartyLeader': lambda reader: self._read_unique_id(reader),
            'TAGame.RBActor_TA:ReplicatedRBState': lambda reader: self._read_rigid_body_state(reader),
            'Engine.Pawn:PlayerReplicationInfo': lambda reader: self._read_nullable_int(reader),
            'TAGame.Ball_TA:GameEvent': lambda reader: self._read_bits(reader, 33),
            'TAGame.Car_TA:TeamPaint': lambda reader: self._read_bits(reader, 88),
            'TAGame.CarComponent_TA:Vehicle': lambda reader: self._read_bits(reader, 33),
            'TAGame.GameEvent_TA:ReplicatedGameStateTimeRemaining': lambda reader: self._read_bits(reader, 32),
            'ProjectX.GRI_X:bGameStarted': lambda reader: reader.read(1).bool,
            'ProjectX.GRI_X:ReplicatedGamePlaylist': lambda reader: self._read_bits(reader, 32),
            'TAGame.Vehicle_TA:ReplicatedThrottle': lambda reader: self._read_bits(reader, 8),
            'TAGame.VehiclePickup_TA:ReplicatedPickupData': lambda reader: self._read_bits(reader, 34),
            'TAGame.Vehicle_TA:bDriving': lambda reader: self._read_bits(reader, 1),
            'TAGame.GameEvent_Soccar_TA:SecondsRemaining': lambda reader: self._read_bits(reader, 32),
            'TAGame.CarComponent_TA:ReplicatedActive': lambda reader: self._read_bits(reader, 8),
            'TAGame.PRI_TA:MatchScore': lambda reader: self._read_bits(reader, 32),
            'TAGame.PRI_TA:MatchShots': lambda reader: self._read_bits(reader, 32),
            'TAGame.Ball_TA:HitTeamNum': lambda reader: self._read_bits(reader, 8),
            'Engine.Actor:bCollideActors': lambda reader: reader.read(1).bool,
            'Engine.Actor:bBlockActors': lambda reader: reader.read(1).bool,
            'Engine.PlayerReplicationInfo:Score': lambda reader: reader.read(32, reverse=True).uint,
            'TAGame.PRI_TA:MatchGoals': lambda reader: reader.read(32, reverse=True).uint,
            'TAGame.PRI_TA:MatchAssists': lambda reader: reader.read(32, reverse=True).uint,
            'TAGame.PRI_TA:MatchSaves': lambda reader: reader.read(32, reverse=True).uint,
            'TAGame.Ball_TA:ReplicatedExplosionData': lambda reader: self._read_bits(reader, 79),
            'TAGame.GameEvent_Team_TA:MaxTeamSize': lambda reader: reader.read(32, reverse=True).uint,
            'TAGame.GameEvent_Soccar_TA:RoundNum': lambda reader: reader.read(32, reverse=True).uint,
            'TAGame.GameEvent_Soccar_TA:ReplicatedScoredOnTeam': lambda reader: reader.read(8, reverse=True).uint,
            'Engine.TeamInfo:Score': lambda reader: reader.read(32, reverse=True).uint,
            'TAGame.PRI_TA:CameraSettings': lambda reader: reader.read(431).bin,
            'TAGame.PRI_TA:ReplicatedGameEvent': lambda reader: reader.read(33).bin,
            'TAGame.PRI_TA:bUsingSecondaryCamera': lambda reader: reader.read(1).bool,
            'TAGame.PRI_TA:bIsInSplitScreen': lambda reader: reader.read(1).bool,
            'TAGame.PRI_TA:ClientLoadout': lambda reader: self._read_client_loadout(reader),
            'TAGame.Vehicle_TA:ReplicatedSteer': lambda reader: reader.read(8, reverse=True).int,
            'TAGame.CarComponent_Dodge_TA:DodgeTorque': lambda reader: self._read_variable_vector(reader),
            'Engine.PlayerReplicationInfo:Ping': lambda reader: reader.read(8, reverse=True).uint,
            'ProjectX.GRI_X:GameServerID': lambda reader: reader.read(64).bin,
            'ProjectX.GRI_X:Reservations': lambda reader: self._read_reservations(reader),
            'Engine.Actor:DrawScale': lambda reader: reader.read(32).bin,
            'TAGame.CrowdActor_TA:ReplicatedOneShotSound': lambda reader: reader.read(33).bin,
            'TAGame.CrowdActor_TA:ModifiedNoise': lambda reader: reader.read(32).bin,
            'TAGame.CrowdActor_TA:GameEvent': lambda reader: reader.read(33).bin,
            'TAGame.CrowdManager_TA:GameEvent': lambda reader: reader.read(33).bin,
            'TAGame.CrowdActor_TA:ReplicatedCountDownNumber': lambda reader: reader.read(32).bin,
            'TAGame.PRI_TA:CameraYaw': lambda reader: reader.read(8).bin,
            'TAGame.PRI_TA:CameraPitch': lambda reader: reader.read(8).bin,
            'Engine.PlayerReplicationInfo:bBot': lambda reader: reader.read(1).bool,
            'TAGame.Vehicle_TA:bReplicatedHandbrake': lambda reader: reader.read(1).bool,
            'Engine.Actor:bHidden': lambda reader: reader.read(1).bool,
            'TAGame.Car_TA:ReplicatedDemolish': lambda reader: self._read_replicated_demolish(reader),
            'TAGame.PRI_TA:bUsingBehindView': lambda reader: reader.read(1).bool,
            'Engine.PlayerReplicationInfo:bWaitingPlayer': lambda reader: reader.read(1).bool,
            'TAGame.RBActor_TA:bReplayActor': lambda reader: reader.read(1).bool,
            'TAGame.CarComponent_FlipCar_TA:bFlipRight': lambda reader: reader.read(1).bool,
            'TAGame.CarComponent_FlipCar_TA:FlipCarTime': lambda reader: reader.read(32).uint,
            'TAGame.GameEvent_Soccar_TA:bOverTime': lambda reader: reader.read(1).bool,
            'TAGame.GameEvent_Soccar_TA:ReplicatedMusicStinger': lambda reader: reader.read(41).bin,
        }

    def parse(self, replay_file, number_of_frames):
        reverse_reader = ReverseBitReader(replay_file)
        #self._find_candidate_frame_starts(replay_file)
        #print(reverse_reader.read(4953).bin)
        #reverse_reader.read(19845)
        #print("Data: {}".format(reverse_reader.read(241).bin))

        for x in range(number_of_frames):
            print("************************************")
            print("Reading network frame {}".format(x))
            print("************************************")
            self._read_network_frame(reverse_reader)

        #self._find_candidate_frame_starts(replay_file, min=30, max=31)
        #print(reverse_reader.read(6789).bin)
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

    def _read_nullable_int(self, reverse_reader):
        has_value = reverse_reader.read(1).bool
        value = reverse_reader.read(32, reverse=True).uint

        if not has_value:
            value = None

        return value

    def _read_network_frame_actor(self, reverse_reader):
        actor_id = reverse_reader.read(10, reverse=True).uint
        print("Actor ID: {}".format(actor_id))

        channel_open = reverse_reader.read(1).bool
        print("Channel Open: {}".format(channel_open))

        if not channel_open:
            del self.actors[actor_id]
            return

        new_actor = reverse_reader.read(1).bool
        print("New Actor: {}".format(new_actor))

        if new_actor:
            self._read_network_frame_actor_new(actor_id, reverse_reader)
        else:
            self._read_network_frame_actor_existing(actor_id, reverse_reader)

    def _read_network_frame_actor_new(self, actor_id, reverse_reader):
        unknown = reverse_reader.read(1).bool
        print("Unknown Bit: {}".format(unknown))

        type_id = reverse_reader.read(32, reverse=True).uint
        class_name = self.object_name_lookup[type_id]

        self.actors[actor_id] = class_name
        print("Type ID: {} ({})".format(type_id, class_name))

        if 'TheWorld' in class_name:
            return

        vector = self._read_variable_vector(reverse_reader)
        print("Vector: {}".format(vector))

        if class_name in ['Archetypes.Ball.Ball_Default', 'Archetypes.Car.Car_Default']:
            rotator = self._read_rotator(reverse_reader)
            print("Rotator: {}".format(rotator))

    def _read_serialized_int(self, reverse_reader, max_value=19):
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
        print("Reading properties for '{}'".format(actor_class_name))

        try:
            property_lookup = self.property_name_lookup[actor_class_name]
        except KeyError:
            raise UnknownObjectError('Parser does not know about archetype "{}"'.format(actor_class_name))

        max_property = max(property_lookup.keys())
        while True:
            another_property = reverse_reader.read(1).bool
            print("Another property?: {}".format(another_property))

            if not another_property:
                break

            net_property_id = self._read_serialized_int(reverse_reader, max_value=max_property)
            print("Network Property ID: {}".format(net_property_id))
            property_name = property_lookup[net_property_id]
            print("Property Name: {}".format(property_name))

            try:
                read_strategy = self.property_read_strategies[property_name]
            except KeyError:
                raise UnknownObjectError('Parser does not know how to parse property "{}"'.format(property_name))
            value = read_strategy(reverse_reader)
            print("Value: {}".format(value))

    def _read_bits(self, reverse_reader, bits):
        results = reverse_reader.read(bits)
        return results.bin

    def _read_unique_id(self, reverse_reader):
        # I'm guessing here that this differentiates PCs and PS4s
        system_id = reverse_reader.read(8, reverse=True).uint
        STEAM = 1
        PS4 = 2

        if system_id == STEAM:
            return (system_id, reverse_reader.read(72).bin)
        elif system_id == PS4:
            return (system_id, reverse_reader.read(264).bin)

    def _read_reservations(self, reverse_reader):
        unknown_bits = reverse_reader.read(3).bin
        values = []

        at_end = False

        while not at_end:
            unique_id = self._read_unique_id(reverse_reader)
            name = self._read_string(reverse_reader)
            unknown = reverse_reader.read(3).bin
            at_end = reverse_reader.read(1).bool
            even_more_unknown = reverse_reader.read(8).bin

            values.append( (unique_id, name) )

        yet_more_unknown_stuff = reverse_reader.read(29).bin

        return values

    def _read_team(self, reverse_reader):
        unknown = reverse_reader.read(1)
        team_actor_id = reverse_reader.read(32, reverse=True).uint
        return team_actor_id

    def _read_replicated_state_index(self, reverse_reader):
        return reverse_reader.read(8, reverse=True).uint

    def _read_replicated_demolish(self, reverse_reader):
        return (
            reverse_reader.read(66).bin,
            self._read_variable_vector(reverse_reader),
            reverse_reader.read(1).bin,
            self._read_variable_vector(reverse_reader),
            reverse_reader.read(5).bin,
            #reverse_reader.read(20).bin,
        )

    def _read_string(self, reverse_reader):
        length = reverse_reader.read(32, reverse=True).uint
        print("Length: {}".format(length))
        return ''.join([reverse_reader.read(8, reverse=True).bytes for x in range(length)][:-1])

    def _read_rigid_body_state(self, reverse_reader):
        rb_state_type = reverse_reader.read(1).bool
        if rb_state_type:
            return (
                self._read_variable_vector(reverse_reader),
                self._read_bits(reverse_reader, 48),
            )
        else:
            return (
                self._read_variable_vector(reverse_reader),
                self._read_bits(reverse_reader, 48),
                self._read_variable_vector(reverse_reader),
                self._read_variable_vector(reverse_reader),
            )

    def _read_client_loadout(self, reverse_reader):
        unknown = reverse_reader.read(8, reverse=True).uint
        return (
            reverse_reader.read(32, reverse=True).uint,
            reverse_reader.read(32, reverse=True).uint,
            reverse_reader.read(32, reverse=True).uint,
            reverse_reader.read(32, reverse=True).uint,
            reverse_reader.read(32, reverse=True).uint,
            reverse_reader.read(32, reverse=True).uint,
            reverse_reader.read(32, reverse=True).uint,
        )

    def _find_candidate_frame_starts(self, replay_file, min=20, max=30):
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
            if min + 0.001 <= current <= max and 0.01 <= delta <= 0.4:
                print("***************************")
                print("Frame {} at Bit {}. Size: {}".format(last_time, last_bit, x - last_bit))
                last_time = current
                last_bit = x



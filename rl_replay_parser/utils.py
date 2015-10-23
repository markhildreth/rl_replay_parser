KNOWN_ARCHETYPES = {
    'GameInfo_Soccar.GameInfo.GameInfo_Soccar:GameReplicationInfoArchetype': [
        'Engine.Actor',
        'Engine.GameReplicationInfo',
        'ProjectX.GRI_X',
        'TAGame.GRI_TA',
    ],

    'Archetypes.GameEvent.GameEvent_SoccarSplitscreen': [
        'Engine.Actor',
        'TAGame.GameEvent_TA',
        'TAGame.GameEvent_Team_TA',
        'TAGame.GameEvent_Soccar_TA',
        'TAGame.GameEvent_SoccarPrivate_TA',
        'TAGame.GameEvent_SoccarSplitscreen_TA',
    ],
    'Archetypes.Teams.Team0': [
        'Engine.Actor',
        'Engine.TeamInfo',
        'TAGame.Team_TA',
        'TAGame.Team_Soccar_TA',
    ],
    'Archetypes.Teams.Team1': [
        'Engine.Actor',
        'Engine.TeamInfo',
        'TAGame.Team_TA',
        'TAGame.Team_Soccar_TA',
    ],
    'TAGame.Default__PRI_TA': [
        'Engine.Actor',
        'Engine.PlayerReplicationInfo',
        'ProjectX.PRI_X',
        'TAGame.PRI_TA',
    ],
    'Archetypes.Ball.Ball_Default': [
        'Engine.Actor',
        'Engine.Pawn',
        'TAGame.RBActor_TA',
        'TAGame.Ball_TA',
    ],
    'Archetypes.Car.Car_Default': [
        'Engine.Actor',
        'Engine.Pawn',
        'TAGame.RBActor_TA',
        'TAGame.Vehicle_TA',
        'TAGame.Car_TA',
    ],
    'Archetypes.CarComponents.CarComponent_Boost': [
        'Engine.Actor',
        'TAGame.CarComponent_TA',
        'TAGame.CarComponent_Boost_TA',
    ],
    'Archetypes.CarComponents.CarComponent_Jump': [
        'Engine.Actor',
        'TAGame.CarComponent_TA',
        'TAGame.CarComponent_Jump_TA',
    ],
    'Archetypes.CarComponents.CarComponent_DoubleJump': [
        'Engine.Actor',
        'TAGame.CarComponent_TA',
        'TAGame.CarComponent_DoubleJump_TA',
    ],
    'Archetypes.CarComponents.CarComponent_Dodge': [
        'Engine.Actor',
        'TAGame.CarComponent_TA',
        'TAGame.CarComponent_Dodge_TA',
    ],
    'Archetypes.CarComponents.CarComponent_FlipCar': [
        'Engine.Actor',
        'TAGame.CarComponent_TA',
        'TAGame.CarComponent_FlipCar_TA',
    ],
}

boosts = [
    'trainstation_p.TheWorld:PersistentLevel.VehiclePickup_Boost_TA_62',
    'trainstation_p.TheWorld:PersistentLevel.VehiclePickup_Boost_TA_24',
    'trainstation_p.TheWorld:PersistentLevel.VehiclePickup_Boost_TA_60',
    'trainstation_p.TheWorld:PersistentLevel.VehiclePickup_Boost_TA_46',
    'trainstation_p.TheWorld:PersistentLevel.VehiclePickup_Boost_TA_58',
]

for boost in boosts:
    KNOWN_ARCHETYPES[boost] = [
        'Engine.Actor',
        'TAGame.VehiclePickup_Boost_TA',
        'TAGame.VehiclePickup_TA',
    ]

def build_class_name_lookup(objects):
    object_name_lookup = {name: name_id for name_id, name in enumerate(objects)}

    results = {}
    for class_name in KNOWN_ARCHETYPES.keys():
        object_id = object_name_lookup[class_name]
        results[object_id] = class_name

    return results

def build_property_name_lookup(objects, class_net_cache):
    object_name_lookup = dict(enumerate(objects))
    object_id_lookup = _build_reverse_lookup(object_name_lookup)
    
    results = {}
    for archetype_name, known_class_types in KNOWN_ARCHETYPES.items():
        results[archetype_name] = {}
        for known_class_type in known_class_types:
            class_id = object_id_lookup[known_class_type]
            properties = class_net_cache[class_id]['properties']
            for property_net_id, property_id in properties.items():
                results[archetype_name][property_net_id] = object_name_lookup[property_id]

    return results

def _build_reverse_lookup(d):
    reverse_lookup = {}
    for key, value in d.items():
        reverse_lookup[value] = key

    return reverse_lookup


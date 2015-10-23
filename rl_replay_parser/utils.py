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

    'Archetypes.GameEvent.GameEvent_Soccar': [
        'Engine.Actor',
        'TAGame.GameEvent_TA',
        'TAGame.GameEvent_Team_TA',
        'TAGame.GameEvent_Soccar_TA',
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
    'eurostad_oob_audio_map.TheWorld:PersistentLevel.CrowdActor_TA_0': [
        'Engine.Actor',
        'TAGame.CrowdActor_TA',
    ],
    'eurostad_oob_audio_map.TheWorld:PersistentLevel.CrowdManager_TA_0': [
        'Engine.Actor',
        'TAGame.CrowdManager_TA',
    ],
}

# TODO: Perhaps we should be more explicit here.
boosts = [
    'trainstation_p.TheWorld:PersistentLevel.VehiclePickup_Boost_TA_{}'.format(x)
    for x in range(100)
]
boosts.extend([
    'eurostadium_p.TheWorld:PersistentLevel.VehiclePickup_Boost_TA_{}'.format(x)
    for x in range(100)
])

for boost in boosts:
    KNOWN_ARCHETYPES[boost] = [
        'Engine.Actor',
        'TAGame.VehiclePickup_Boost_TA',
        'TAGame.VehiclePickup_TA',
    ]

def build_property_name_lookup(object_name_lookup, class_net_cache):
    object_id_lookup = _build_reverse_lookup(object_name_lookup)
    
    results = {}
    for archetype_name, known_class_types in KNOWN_ARCHETYPES.items():
        results[archetype_name] = {}
        for known_class_type in known_class_types:
            try:
                class_id = object_id_lookup[known_class_type]
            except KeyError:
                continue

            properties = class_net_cache[class_id]['properties']
            for property_net_id, property_id in properties.items():
                results[archetype_name][property_net_id] = object_name_lookup[property_id]

    return results

def _build_reverse_lookup(d):
    reverse_lookup = {}
    for key, value in d.items():
        reverse_lookup[value] = key

    return reverse_lookup


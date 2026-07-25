"""Curated ElevenLabs Sound Effects prompt catalog for vector casting."""

from __future__ import annotations

from datetime import datetime, timezone

SFX_ENTRIES: list[dict] = [
    {
        "slug": "rain_abandoned_house_night",
        "name": "Abandoned house rain night bed",
        "use_case": "ambience",
        "tags": "rain,house,night,horror,loop,bed",
        "prompt": (
            "Soft continuous rain on a tin roof and window glass, distant thunder rumble, "
            "wind through broken shutters, abandoned house at night ambience bed, "
            "loopable under dialogue, cinematic horror, no music"
        ),
        "when": "Exterior/interior abandoned house scenes at night with rain.",
    },
    {
        "slug": "floorboard_creak",
        "name": "Floorboard creak",
        "use_case": "foley",
        "tags": "creak,wood,footstep,horror,spot",
        "prompt": (
            "Old wooden floorboard creaking slowly under a careful footstep, "
            "close perspective, dry interior, suspenseful horror foley, single spot effect"
        ),
        "when": "Character sneaking or weight shifting inside old house.",
    },
    {
        "slug": "distant_train",
        "name": "Distant train",
        "use_case": "ambience",
        "tags": "train,distant,night,city,spot",
        "prompt": (
            "Distant train horn and low rumble at night, far away, urban outskirts, "
            "melancholy thriller atmosphere, no dialogue"
        ),
        "when": "Station, tracks, or night city-edge scenes.",
    },
    {
        "slug": "platform_loudspeaker",
        "name": "Platform loudspeaker crackle",
        "use_case": "spot",
        "tags": "station,loudspeaker,crackle,train",
        "prompt": (
            "Railway platform PA loudspeaker crackle and muffled announcement tone, "
            "busy station ambience underneath, brief spot effect"
        ),
        "when": "Train platform scenes with announcements.",
    },
    {
        "slug": "wind_through_trees",
        "name": "Wind through trees",
        "use_case": "ambience",
        "tags": "wind,trees,night,forest,bed",
        "prompt": (
            "Night wind whistling through trees and dry leaves rustling, "
            "lonely outdoor ambience bed, loopable, horror-thriller, no animals screaming"
        ),
        "when": "Outdoor forest / roadside night scenes.",
    },
    {
        "slug": "heavy_door_creak",
        "name": "Heavy wooden door creak",
        "use_case": "foley",
        "tags": "door,creak,wood,horror,spot",
        "prompt": (
            "Heavy wooden door creaking open slowly on rusty hinges, "
            "interior echo, cinematic horror spot effect"
        ),
        "when": "Entering rooms, reveals, threshold crossings.",
    },
    {
        "slug": "crowd_murmur_low",
        "name": "Low crowd murmur",
        "use_case": "ambience",
        "tags": "crowd,murmur,market,city,bed",
        "prompt": (
            "Low distant crowd murmur and soft footsteps, indoor hall or market, "
            "ducked under dialogue, loopable bed, no intelligible speech"
        ),
        "when": "Public spaces where VO must stay clear.",
    },
    {
        "slug": "heartbeat_tense",
        "name": "Tense heartbeat",
        "use_case": "design",
        "tags": "heartbeat,tension,horror,spot",
        "prompt": (
            "Muffled tense heartbeat pulse in a quiet room, low and slow then slightly faster, "
            "psychological horror design element, no music melody"
        ),
        "when": "POV fear beats and cliffhangers.",
    },
    {
        "slug": "phone_vibrate",
        "name": "Phone vibrate",
        "use_case": "spot",
        "tags": "phone,vibrate,modern,spot",
        "prompt": (
            "Smartphone vibrating on a wooden table, short buzz pattern, "
            "close mic, realistic modern thriller spot"
        ),
        "when": "Call / message interrupts.",
    },
    {
        "slug": "rain_interior_window",
        "name": "Interior rain on window",
        "use_case": "ambience",
        "tags": "rain,window,interior,soft,bed",
        "prompt": (
            "Gentle rain against a window heard from inside a quiet room, "
            "soft roomtone, intimate thriller ambience, loopable"
        ),
        "when": "Indoor night conversations during rain.",
    },
    {
        "slug": "thunder_distant",
        "name": "Distant thunder",
        "use_case": "spot",
        "tags": "thunder,distant,storm,horror",
        "prompt": (
            "Distant thunder roll across the sky, low frequency rumble, "
            "storm night, cinematic but not overpowering"
        ),
        "when": "Punctuate dread without masking VO.",
    },
    {
        "slug": "clock_tick_empty_room",
        "name": "Clock tick empty room",
        "use_case": "ambience",
        "tags": "clock,tick,empty,suspense,bed",
        "prompt": (
            "Single analog clock ticking in an otherwise empty quiet room, "
            "soft roomtone, suspenseful minimal ambience, loopable"
        ),
        "when": "Waiting / silence tension scenes.",
    },
    {
        "slug": "footsteps_gravel",
        "name": "Footsteps on gravel",
        "use_case": "foley",
        "tags": "footsteps,gravel,outdoor,spot",
        "prompt": (
            "Footsteps walking on wet gravel path at night, medium pace, "
            "then stopping suddenly, thriller foley"
        ),
        "when": "Approach / pursuit outdoors.",
    },
    {
        "slug": "metal_gate_rattle",
        "name": "Metal gate rattle",
        "use_case": "foley",
        "tags": "gate,metal,rattle,horror",
        "prompt": (
            "Old metal gate rattling in the wind then a sharp clang, "
            "outdoor night, horror thriller spot"
        ),
        "when": "Compound / courtyard entries.",
    },
    {
        "slug": "whisper_roomtone",
        "name": "Uneasy roomtone",
        "use_case": "ambience",
        "tags": "roomtone,uneasy,interior,bed",
        "prompt": (
            "Uneasy quiet roomtone with faint air hiss and barely-there distant city hum, "
            "psychological thriller bed, loopable, no music"
        ),
        "when": "Dialogue-forward interiors needing subtle tension.",
    },
    {
        "slug": "car_passby_wet",
        "name": "Wet street car pass-by",
        "use_case": "spot",
        "tags": "car,street,rain,city",
        "prompt": (
            "Car pass-by on a wet street at night, tire splash, whoosh, "
            "urban thriller transition spot"
        ),
        "when": "City night transitions.",
    },
    {
        "slug": "temple_bell_distant",
        "name": "Distant temple bell",
        "use_case": "spot",
        "tags": "temple,bell,india,distant,cultural",
        "prompt": (
            "Single distant temple bell ringing faintly across a quiet Indian neighborhood evening, "
            "atmospheric, not loud, cultural regional thriller color"
        ),
        "when": "Pune/Patna/regional setting flavor.",
    },
    {
        "slug": "ceiling_fan_hum",
        "name": "Ceiling fan hum",
        "use_case": "ambience",
        "tags": "fan,interior,india,roomtone,bed",
        "prompt": (
            "Soft ceiling fan hum and light blade whoosh in a warm Indian room, "
            "loopable roomtone bed under dialogue"
        ),
        "when": "Domestic Indian interiors.",
    },
    {
        "slug": "auto_rickshaw_pass",
        "name": "Auto rickshaw pass",
        "use_case": "spot",
        "tags": "rickshaw,street,india,city",
        "prompt": (
            "Auto rickshaw engine pass-by on a narrow Indian street, brief horn chirp, "
            "day or night street color, short spot"
        ),
        "when": "City street exteriors.",
    },
    {
        "slug": "power_cut_buzz",
        "name": "Power cut buzz then silence",
        "use_case": "design",
        "tags": "power,electric,silence,horror",
        "prompt": (
            "Electric light buzz cutting out suddenly into thick silence with faint outdoor insects, "
            "power-cut horror beat, short design effect"
        ),
        "when": "Blackout cliff moments.",
    },
    {
        "slug": "radio_static_whisper",
        "name": "Radio static whisper",
        "use_case": "design",
        "tags": "radio,static,whisper,horror",
        "prompt": (
            "Old radio static with almost-unintelligible whispered fragments fading in and out, "
            "supernatural thriller design, keep quiet under VO"
        ),
        "when": "Haunting / The Voice motifs.",
    },
    {
        "slug": "kitchen_night_quiet",
        "name": "Quiet kitchen night",
        "use_case": "ambience",
        "tags": "kitchen,interior,night,bed",
        "prompt": (
            "Quiet kitchen at night: soft fridge hum, occasional drip, distant street, "
            "loopable domestic ambience"
        ),
        "when": "Home night dialogue.",
    },
    {
        "slug": "stairs_wood_climb",
        "name": "Wooden stairs climb",
        "use_case": "foley",
        "tags": "stairs,wood,footsteps,horror",
        "prompt": (
            "Footsteps climbing old wooden stairs, slow and careful, "
            "creaks escalating, suspense horror foley"
        ),
        "when": "Ascending to attic / upper floor reveals.",
    },
    {
        "slug": "attic_wind_howl",
        "name": "Attic wind howl",
        "use_case": "ambience",
        "tags": "attic,wind,howl,horror,bed",
        "prompt": (
            "Wind howling through attic gaps and loose tiles, dusty wood resonance, "
            "abandoned house upper floor ambience"
        ),
        "when": "Attic / rooftop interior scenes.",
    },
    {
        "slug": "glass_shatter_distant",
        "name": "Distant glass shatter",
        "use_case": "spot",
        "tags": "glass,shatter,distant,shock",
        "prompt": (
            "Distant glass shattering then brief silence, outdoor night, "
            "startle moment for thriller"
        ),
        "when": "Off-screen shocks.",
    },
    {
        "slug": "market_evening_india",
        "name": "Indian evening market bed",
        "use_case": "ambience",
        "tags": "market,india,evening,crowd,bed",
        "prompt": (
            "Indian evening market ambience: soft vendor calls blurred, scooter hums, "
            "crowd murmur, spices-and-street energy, loopable bed ducked for VO"
        ),
        "when": "Bazaar / market scenes.",
    },
    {
        "slug": "hospital_corridor",
        "name": "Hospital corridor hum",
        "use_case": "ambience",
        "tags": "hospital,corridor,hum,tense,bed",
        "prompt": (
            "Quiet hospital corridor: fluorescent hum, distant trolley wheels, "
            "soft PA chime far away, tense clean ambience"
        ),
        "when": "Hospital / clinic scenes.",
    },
    {
        "slug": "police_siren_distant",
        "name": "Distant police siren",
        "use_case": "spot",
        "tags": "siren,police,city,distant",
        "prompt": (
            "Distant police siren doppler across a city night, then fading, "
            "thriller punctuation, not piercing"
        ),
        "when": "Crime / chase aftermath beats.",
    },
    {
        "slug": "river_night_flow",
        "name": "Night river flow",
        "use_case": "ambience",
        "tags": "river,water,night,bed",
        "prompt": (
            "Gentle river flow at night with soft insects and breeze, "
            "peaceful but lonely outdoor bed, loopable"
        ),
        "when": "Riverside / ghats scenes.",
    },
    {
        "slug": "bus_interior_rattle",
        "name": "Bus interior rattle",
        "use_case": "ambience",
        "tags": "bus,interior,rattle,travel,bed",
        "prompt": (
            "Moving bus interior: engine drone, seat rattles, muffled outside traffic, "
            "commute thriller ambience, loopable"
        ),
        "when": "Travel / commute scenes.",
    },
    {
        "slug": "keys_in_lock",
        "name": "Keys in lock",
        "use_case": "foley",
        "tags": "keys,lock,door,spot",
        "prompt": (
            "Metal keys fumbling then turning in a door lock, click of latch, "
            "close mic domestic thriller spot"
        ),
        "when": "Arriving home / entering locked spaces.",
    },
    {
        "slug": "whisper_corridor_echo",
        "name": "Corridor whisper echo",
        "use_case": "design",
        "tags": "whisper,echo,corridor,horror",
        "prompt": (
            "Barely audible whisper echoing down a long empty corridor, "
            "reverb heavy, supernatural hint, keep low for ducking under VO"
        ),
        "when": "Supernatural presence cues.",
    },
    {
        "slug": "monsoon_heavy_rain",
        "name": "Heavy monsoon rain",
        "use_case": "ambience",
        "tags": "monsoon,rain,india,heavy,bed",
        "prompt": (
            "Heavy Indian monsoon rain on concrete and foliage, dense but filtered for dialogue bed, "
            "loopable, cinematic"
        ),
        "when": "Intense monsoon exteriors/interiors.",
    },
    {
        "slug": "scooter_idle_street",
        "name": "Scooter idle street",
        "use_case": "spot",
        "tags": "scooter,street,india,idle",
        "prompt": (
            "Two-wheeler scooter idling then pulling away on an Indian street, "
            "short realistic spot"
        ),
        "when": "Street arrivals/departures.",
    },
    {
        "slug": "temple_crowd_soft",
        "name": "Soft temple courtyard",
        "use_case": "ambience",
        "tags": "temple,courtyard,india,soft,bed",
        "prompt": (
            "Soft temple courtyard ambience: distant bells, quiet footsteps, birds, "
            "respectful low bed under narration"
        ),
        "when": "Temple / spiritual setting scenes.",
    },
    {
        "slug": "office_ac_hum",
        "name": "Office AC hum",
        "use_case": "ambience",
        "tags": "office,ac,hum,interior,bed",
        "prompt": (
            "Office air-conditioner hum with faint keyboard clicks far away, "
            "corporate thriller roomtone, loopable"
        ),
        "when": "Office / workplace scenes.",
    },
    {
        "slug": "elevator_ding",
        "name": "Elevator ding",
        "use_case": "spot",
        "tags": "elevator,ding,building,spot",
        "prompt": (
            "Elevator arrival ding and soft door open whoosh in a quiet building lobby, "
            "short transition spot"
        ),
        "when": "Building transitions.",
    },
    {
        "slug": "night_insects_rural",
        "name": "Rural night insects",
        "use_case": "ambience",
        "tags": "insects,rural,night,india,bed",
        "prompt": (
            "Rural Indian night insects and frogs at a moderate distance, "
            "warm air, lonely countryside bed, loopable"
        ),
        "when": "Village / outskirts night.",
    },
    {
        "slug": "metal_bucket_drop",
        "name": "Metal bucket drop",
        "use_case": "spot",
        "tags": "metal,drop,shock,spot",
        "prompt": (
            "Metal bucket dropped on concrete floor with short ringing decay, "
            "startle foley for horror"
        ),
        "when": "Jump-scare practical sounds.",
    },
    {
        "slug": "fan_stop_silence",
        "name": "Fan slowing to stop",
        "use_case": "design",
        "tags": "fan,stop,silence,power",
        "prompt": (
            "Ceiling fan slowing down and stopping into sudden quiet, "
            "power-failure transition design"
        ),
        "when": "Power cut transitions.",
    },
    # Expanded ambience / spot bank (ElevenLabs SFX has no list API — prompts are the catalog)
    {"slug": "owl_night", "name": "Owl hoot night", "use_case": "spot", "tags": "owl,night,rural", "prompt": "Single distant owl hoot at night in rural quiet, sparse and eerie", "when": "Rural night tension."},
    {"slug": "dog_bark_distant", "name": "Distant dog bark", "use_case": "spot", "tags": "dog,bark,distant,night", "prompt": "Distant dog barking once then fading in a quiet neighborhood night", "when": "Neighborhood night color."},
    {"slug": "motorcycle_pass", "name": "Motorcycle pass-by", "use_case": "spot", "tags": "motorcycle,street,pass", "prompt": "Motorcycle accelerating past on asphalt then fading, urban night", "when": "Street chase flavor."},
    {"slug": "rain_on_umbrella", "name": "Rain on umbrella", "use_case": "foley", "tags": "rain,umbrella,close", "prompt": "Rain hitting fabric umbrella close mic, walking pace, intimate thriller", "when": "Walking in rain POV."},
    {"slug": "keys_jingle_pocket", "name": "Keys jingle", "use_case": "foley", "tags": "keys,jingle,pocket", "prompt": "Metal keys jingling in a pocket then pulled out, close foley", "when": "Character fidget / arrival."},
    {"slug": "zipper_jacket", "name": "Jacket zipper", "use_case": "foley", "tags": "zipper,jacket,foley", "prompt": "Jacket zipper pulled up quickly, cloth rustle, realistic foley", "when": "Getting ready beats."},
    {"slug": "match_strike", "name": "Match strike", "use_case": "spot", "tags": "match,fire,strike", "prompt": "Match strike and brief flame whoosh in a quiet dark room", "when": "Candle / dark reveal."},
    {"slug": "candle_blow_out", "name": "Candle blow out", "use_case": "spot", "tags": "candle,blow,dark", "prompt": "Soft breath blowing out a candle into darkness, quiet room", "when": "Lights out moment."},
    {"slug": "clock_chime_hour", "name": "Clock chime", "use_case": "spot", "tags": "clock,chime,hour", "prompt": "Old wall clock chiming the hour faintly in a large house", "when": "Time jump / dread."},
    {"slug": "water_drip_cave", "name": "Cave water drip", "use_case": "ambience", "tags": "drip,cave,echo,bed", "prompt": "Water dripping in a reverberant cave or basement, slow irregular drips, loopable bed", "when": "Basement / underground."},
    {"slug": "basement_hum", "name": "Basement electrical hum", "use_case": "ambience", "tags": "basement,hum,electric,bed", "prompt": "Low electrical transformer hum in a damp basement, uneasy loopable bed", "when": "Basement interiors."},
    {"slug": "fridge_night_hum", "name": "Fridge night hum", "use_case": "ambience", "tags": "fridge,kitchen,night,bed", "prompt": "Refrigerator compressor cycling in a dark kitchen at night, domestic bed", "when": "Kitchen night."},
    {"slug": "typing_keyboard_fast", "name": "Fast keyboard typing", "use_case": "foley", "tags": "keyboard,typing,office", "prompt": "Fast laptop keyboard typing in a quiet office, close mic", "when": "Office / hacking beats."},
    {"slug": "mouse_click", "name": "Mouse click", "use_case": "spot", "tags": "mouse,click,computer", "prompt": "Single computer mouse click on a desk, short and clean", "when": "UI / computer interaction."},
    {"slug": "notification_chime_soft", "name": "Soft notification chime", "use_case": "spot", "tags": "notification,chime,phone", "prompt": "Soft modern phone notification chime, not shrill, short", "when": "Message arrives."},
    {"slug": "voicemail_beep", "name": "Voicemail beep", "use_case": "spot", "tags": "voicemail,beep,phone", "prompt": "Telephone voicemail beep tone then brief silence", "when": "Phone message scenes."},
    {"slug": "busy_signal", "name": "Phone busy signal", "use_case": "spot", "tags": "phone,busy,signal", "prompt": "Classic telephone busy signal repeating twice then stop", "when": "Failed call."},
    {"slug": "elevator_mechanics", "name": "Elevator cables rumble", "use_case": "ambience", "tags": "elevator,mechanics,building", "prompt": "Elevator shaft cable rumble and soft mechanical movement while ascending", "when": "Elevator travel."},
    {"slug": "subway_approach", "name": "Subway train approach", "use_case": "spot", "tags": "subway,train,underground", "prompt": "Underground subway train approaching then braking with screech, station reverb", "when": "Metro scenes."},
    {"slug": "airport_pa_muffle", "name": "Airport PA muffled", "use_case": "ambience", "tags": "airport,pa,muffled,bed", "prompt": "Muffled airport PA announcements and rolling suitcase ambience, loopable bed under VO", "when": "Airport."},
    {"slug": "school_bell", "name": "School bell", "use_case": "spot", "tags": "school,bell", "prompt": "School bell ringing in a corridor with light echo", "when": "School setting."},
    {"slug": "crowd_cheer_stadium", "name": "Stadium crowd cheer", "use_case": "ambience", "tags": "crowd,cheer,stadium", "prompt": "Distant stadium crowd cheer swell then settle, large space reverb", "when": "Public event."},
    {"slug": "market_birds_morning", "name": "Morning birds courtyard", "use_case": "ambience", "tags": "birds,morning,courtyard,india,bed", "prompt": "Morning birds in an Indian courtyard with soft distant traffic, peaceful bed", "when": "Morning exteriors."},
    {"slug": "temple_aarti_soft", "name": "Soft aarti bells", "use_case": "ambience", "tags": "aarti,bells,temple,india", "prompt": "Soft temple aarti bells and quiet devotee murmur at a distance, respectful low bed", "when": "Temple ritual color."},
    {"slug": "train_compartment_rattle", "name": "Train compartment rattle", "use_case": "ambience", "tags": "train,compartment,rattle,india,bed", "prompt": "Indian train sleeper compartment: track clack, bunk rattle, muffled chatter far away, loopable", "when": "Train travel."},
    {"slug": "whistle_guard_train", "name": "Train guard whistle", "use_case": "spot", "tags": "train,whistle,guard", "prompt": "Short train guard whistle on a platform before departure", "when": "Train departure."},
    {"slug": "pressure_cooker_hiss", "name": "Pressure cooker hiss", "use_case": "spot", "tags": "kitchen,cooker,india", "prompt": "Pressure cooker hissing and soft steam release in a home kitchen", "when": "Domestic Indian kitchen."},
    {"slug": "mixer_grinder_burst", "name": "Mixer grinder burst", "use_case": "spot", "tags": "kitchen,mixer,india", "prompt": "Short mixer-grinder motor burst then stop, Indian kitchen", "when": "Kitchen activity."},
    {"slug": "ceiling_crack_plaster", "name": "Plaster crack fall", "use_case": "spot", "tags": "plaster,crack,horror", "prompt": "Small plaster crumbs falling from a cracked ceiling, dusty horror detail", "when": "House settling dread."},
    {"slug": "pipe_clang_wall", "name": "Pipe clang in wall", "use_case": "spot", "tags": "pipe,clang,wall,horror", "prompt": "Metal pipe clang inside a wall then brief resonance, unsettling", "when": "Haunted house plumbing."},
    {"slug": "scratch_door_slow", "name": "Slow scratch on door", "use_case": "spot", "tags": "scratch,door,horror", "prompt": "Slow fingernail-like scratch across a wooden door from the other side", "when": "Entity outside door."},
    {"slug": "breath_close_mic", "name": "Close mic breath", "use_case": "design", "tags": "breath,close,horror", "prompt": "Close-mic human breath inhale exhale, tense and quiet, no words", "when": "POV fear."},
    {"slug": "heartbeat_fast", "name": "Fast heartbeat", "use_case": "design", "tags": "heartbeat,fast,panic", "prompt": "Fast muffled heartbeat rising in panic then steadying, design element", "when": "Panic beats."},
    {"slug": "wind_chimes_eerie", "name": "Eerie wind chimes", "use_case": "ambience", "tags": "chimes,wind,eerie", "prompt": "Sparse eerie wind chimes on a porch at night, irregular and lonely", "when": "Porch / courtyard night."},
    {"slug": "leaves_crunch_walk", "name": "Leaves crunch walk", "use_case": "foley", "tags": "leaves,footsteps,forest", "prompt": "Footsteps crunching dry leaves on a forest path at night, medium pace", "when": "Forest walk."},
    {"slug": "mud_footsteps", "name": "Mud footsteps", "use_case": "foley", "tags": "mud,footsteps,rain", "prompt": "Footsteps in wet mud after rain, squelch detail, outdoor", "when": "Monsoon paths."},
    {"slug": "gate_chain_rattle", "name": "Chain on gate", "use_case": "foley", "tags": "chain,gate,metal", "prompt": "Heavy chain rattling on a metal gate then settling", "when": "Locked compound."},
    {"slug": "lock_padlock_click", "name": "Padlock click", "use_case": "spot", "tags": "padlock,click,metal", "prompt": "Padlock snapping shut with a sharp metal click", "when": "Locking / trapping."},
    {"slug": "camera_shutter", "name": "Camera shutter", "use_case": "spot", "tags": "camera,shutter", "prompt": "Single DSLR camera shutter click", "when": "Photo / evidence beats."},
    {"slug": "tape_recorder_click", "name": "Tape recorder click", "use_case": "spot", "tags": "tape,recorder,click", "prompt": "Old cassette recorder play button click then soft tape hiss start", "when": "Found footage / evidence."},
    {"slug": "vhs_tracking_noise", "name": "VHS tracking noise", "use_case": "design", "tags": "vhs,static,horror", "prompt": "Brief VHS tracking static burst then settle, retro horror design", "when": "Glitch / memory."},
    {"slug": "fluorescent_flicker_buzz", "name": "Fluorescent flicker buzz", "use_case": "design", "tags": "fluorescent,flicker,buzz", "prompt": "Fluorescent light buzzing and flickering electrically in a corridor", "when": "Unstable lighting."},
    {"slug": "generator_fail", "name": "Generator failing", "use_case": "spot", "tags": "generator,fail,power", "prompt": "Small generator sputtering then dying into silence", "when": "Power loss rural."},
    {"slug": "mosquito_close", "name": "Mosquito buzz close", "use_case": "spot", "tags": "mosquito,buzz,night,india", "prompt": "Single mosquito buzz near the ear then fade, night interior India", "when": "Night domestic realism."},
    {"slug": "ceiling_gecko_chirp", "name": "Gecko chirp", "use_case": "spot", "tags": "gecko,chirp,night,india", "prompt": "House gecko chirp on a ceiling at night, brief and natural", "when": "Indian night interior."},
    {"slug": "temple_conch", "name": "Temple conch", "use_case": "spot", "tags": "conch,temple,india", "prompt": "Single temple conch shell blow, resonant and distant", "when": "Ritual punctuation."},
    {"slug": "rain_drain_gutter", "name": "Rain in gutter", "use_case": "ambience", "tags": "rain,gutter,drain,bed", "prompt": "Rainwater rushing through a rooftop gutter and drainpipe, continuous bed", "when": "Heavy rain exteriors."},
    {"slug": "thunder_close_crack", "name": "Close thunder crack", "use_case": "spot", "tags": "thunder,close,crack", "prompt": "Sharp close thunder crack then rumble decay, dramatic but short", "when": "Storm shock."},
    {"slug": "hail_on_tin", "name": "Hail on tin roof", "use_case": "ambience", "tags": "hail,tin,roof,storm", "prompt": "Hail hitting a tin roof rapidly, dense storm texture, duckable bed", "when": "Severe storm."},
    {"slug": "crowd_temple_festival", "name": "Temple festival crowd", "use_case": "ambience", "tags": "festival,crowd,temple,india,bed", "prompt": "Busy temple festival crowd: drums distant, chatter, bells, energetic but filtered for VO bed", "when": "Festival scenes."},
    {"slug": "fireworks_distant", "name": "Distant fireworks", "use_case": "spot", "tags": "fireworks,distant,festival", "prompt": "Distant fireworks pops and crackles across a city night sky", "when": "Festival night."},
    {"slug": "auto_stand_idle", "name": "Auto stand idle", "use_case": "ambience", "tags": "auto,rickshaw,idle,india,bed", "prompt": "Several auto-rickshaws idling at a stand with soft horn chirps, street bed", "when": "Transport hub."},
    {"slug": "bus_horn_india", "name": "Indian bus horn", "use_case": "spot", "tags": "bus,horn,india", "prompt": "Loud Indian bus air horn short blast then traffic wash", "when": "Road chaos."},
    {"slug": "crossing_bell_railway", "name": "Railway crossing bell", "use_case": "spot", "tags": "railway,crossing,bell", "prompt": "Railway level-crossing warning bell ringing continuously for a few seconds", "when": "Tracks / crossing."},
    {"slug": "signal_cabin_clack", "name": "Signal cabin clack", "use_case": "spot", "tags": "railway,signal,clack", "prompt": "Mechanical railway signal lever clack in a cabin", "when": "Railway ops color."},
    {"slug": "hospital_monitor_beep", "name": "Hospital monitor beep", "use_case": "ambience", "tags": "hospital,monitor,beep,bed", "prompt": "Steady hospital heart monitor beeps in a quiet ward, tense clean bed", "when": "Hospital bedside."},
    {"slug": "hospital_curtain_pull", "name": "Hospital curtain pull", "use_case": "foley", "tags": "hospital,curtain,foley", "prompt": "Hospital privacy curtain rings sliding on a metal rail", "when": "Ward scenes."},
    {"slug": "syringe_prep", "name": "Syringe prep", "use_case": "foley", "tags": "syringe,medical,foley", "prompt": "Syringe plastic unwrap and plunger click, clinical close foley", "when": "Medical procedure."},
    {"slug": "courtroom_gavel", "name": "Court gavel", "use_case": "spot", "tags": "court,gavel", "prompt": "Wooden gavel striking once in a courtroom with light room reverb", "when": "Legal beats."},
    {"slug": "crowd_gasp", "name": "Crowd gasp", "use_case": "spot", "tags": "crowd,gasp", "prompt": "Small crowd sharp gasp then murmur, indoor hall", "when": "Public reveal."},
    {"slug": "paper_rustle_stack", "name": "Paper stack rustle", "use_case": "foley", "tags": "paper,rustle,office", "prompt": "Stack of papers being shuffled on a desk, investigative foley", "when": "Evidence review."},
    {"slug": "stamp_ink_thud", "name": "Rubber stamp thud", "use_case": "spot", "tags": "stamp,office,thud", "prompt": "Rubber office stamp thud on paper, bureaucratic punctuation", "when": "Official documents."},
    {"slug": "safe_dial_click", "name": "Safe dial clicks", "use_case": "foley", "tags": "safe,dial,click", "prompt": "Combination safe dial clicking slowly then a bolt open clunk", "when": "Heist / secret."},
    {"slug": "drawer_wood_open", "name": "Wooden drawer open", "use_case": "foley", "tags": "drawer,wood,open", "prompt": "Wooden desk drawer sliding open with a soft scrape", "when": "Searching rooms."},
    {"slug": "wardrobe_door_creak", "name": "Wardrobe door creak", "use_case": "foley", "tags": "wardrobe,creak,horror", "prompt": "Tall wardrobe door creaking open in a dark bedroom", "when": "Closet dread."},
    {"slug": "bed_springs_shift", "name": "Bed springs shift", "use_case": "foley", "tags": "bed,springs,night", "prompt": "Person shifting on old bed springs at night, quiet house", "when": "Insomnia / presence."},
    {"slug": "window_rattle_storm", "name": "Window rattle storm", "use_case": "ambience", "tags": "window,rattle,storm,bed", "prompt": "Window panes rattling in a strong wind storm, loopable tense bed", "when": "Storm interiors."},
    {"slug": "shutter_slam", "name": "Shutter slam", "use_case": "spot", "tags": "shutter,slam,wind", "prompt": "Wooden window shutter slamming in the wind then bouncing once", "when": "Wind shock."},
    {"slug": "glass_bottle_roll", "name": "Bottle roll on floor", "use_case": "spot", "tags": "bottle,roll,floor", "prompt": "Glass bottle rolling slowly across a wooden floor then stopping", "when": "Empty house detail."},
    {"slug": "coin_drop_tile", "name": "Coin drop on tile", "use_case": "spot", "tags": "coin,drop,tile", "prompt": "Single coin dropping and spinning on a tile floor", "when": "Small detail accent."},
    {"slug": "market_goat_bleat", "name": "Goat bleat market", "use_case": "spot", "tags": "goat,market,india", "prompt": "Single goat bleat in a busy Indian market background", "when": "Rural market color."},
    {"slug": "cowbell_distant", "name": "Distant cowbell", "use_case": "spot", "tags": "cowbell,rural,india", "prompt": "Distant cowbell irregular clanks on a rural path at dusk", "when": "Village dusk."},
    {"slug": "well_bucket_splash", "name": "Well bucket splash", "use_case": "spot", "tags": "well,bucket,water,rural", "prompt": "Metal bucket hitting water in a deep well with echo splash", "when": "Village well."},
    {"slug": "handpump_water", "name": "Handpump water", "use_case": "foley", "tags": "handpump,water,india", "prompt": "Handpump handle strokes and water gushing into a metal pot", "when": "Village water scene."},
    {"slug": "night_watchman_stick", "name": "Night watchman stick", "use_case": "spot", "tags": "watchman,stick,night,india", "prompt": "Night watchman tapping a stick on pavement while walking, distant", "when": "Neighborhood night India."},
    {"slug": "temple_dogs_night", "name": "Temple dogs night", "use_case": "spot", "tags": "dogs,temple,night", "prompt": "Street dogs barking near a temple at night then quieting", "when": "Temple night exterior."},
    {"slug": "ac_window_rattle", "name": "Window AC rattle", "use_case": "ambience", "tags": "ac,window,rattle,india,bed", "prompt": "Old window AC unit rattling and humming in an Indian apartment, loopable bed", "when": "Apartment interiors."},
    {"slug": "inverter_beep_powercut", "name": "Inverter beep powercut", "use_case": "spot", "tags": "inverter,beep,powercut,india", "prompt": "Home inverter warning beeps during power cut then switch to battery hum", "when": "Indian power cut."},
    {"slug": "diesel_genset_start", "name": "Diesel genset start", "use_case": "spot", "tags": "genset,diesel,start", "prompt": "Diesel generator starting up outside a building, rough idle", "when": "Backup power."},
    {"slug": "sea_waves_soft", "name": "Soft sea waves", "use_case": "ambience", "tags": "sea,waves,beach,bed", "prompt": "Soft sea waves on a quiet beach at night, loopable calm bed", "when": "Coastal scenes."},
    {"slug": "foghorn_distant", "name": "Distant foghorn", "use_case": "spot", "tags": "foghorn,harbor,distant", "prompt": "Distant harbor foghorn single low blast across water", "when": "Harbor night."},
    {"slug": "boat_wood_creak", "name": "Wooden boat creak", "use_case": "ambience", "tags": "boat,wood,creak,water", "prompt": "Wooden boat creaking gently on water with soft lap of waves", "when": "Boat interiors."},
    {"slug": "bridge_traffic_hum", "name": "Bridge traffic hum", "use_case": "ambience", "tags": "bridge,traffic,hum,bed", "prompt": "Traffic humming across a steel bridge with wind, distant city bed", "when": "City bridge."},
    {"slug": "construction_distant", "name": "Distant construction", "use_case": "ambience", "tags": "construction,distant,city,bed", "prompt": "Distant daytime construction clanks and drill, city bed under dialogue", "when": "Urban day."},
    {"slug": "market_pressure_cooker_street", "name": "Street food sizzle", "use_case": "ambience", "tags": "streetfood,sizzle,india,bed", "prompt": "Street food oil sizzle and spatula scrapes at an Indian stall, lively bed", "when": "Street food scenes."},
    {"slug": "chai_stall_clink", "name": "Chai cups clink", "use_case": "spot", "tags": "chai,cups,clink,india", "prompt": "Glass chai cups clinking on a metal tray at a stall", "when": "Chai stall."},
    {"slug": "newspaper_fold", "name": "Newspaper fold", "use_case": "foley", "tags": "newspaper,fold,foley", "prompt": "Newspaper being folded and slapped on a table", "when": "Morning routine / news."},
    {"slug": "radio_tuning_sweep", "name": "Radio tuning sweep", "use_case": "design", "tags": "radio,tuning,static", "prompt": "AM radio tuning sweep through static then settling on a weak station", "when": "Old radio motifs."},
    {"slug": "tv_static_burst", "name": "TV static burst", "use_case": "design", "tags": "tv,static,horror", "prompt": "CRT television static burst then abrupt silence", "when": "Supernatural glitch."},
    {"slug": "whisper_multilayer", "name": "Layered whispers", "use_case": "design", "tags": "whisper,layered,horror", "prompt": "Multiple overlapping unintelligible whispers in a reverberant space, keep low for VO", "when": "Haunting swarm."},
    {"slug": "door_knock_three", "name": "Three knocks on door", "use_case": "spot", "tags": "knock,door,horror", "prompt": "Three deliberate knocks on a heavy wooden door, pause, silence", "when": "Arrival / dread."},
    {"slug": "doorbell_old", "name": "Old doorbell", "use_case": "spot", "tags": "doorbell,old", "prompt": "Old electric doorbell buzz-ring once in a hallway", "when": "Visitor arrival."},
    {"slug": "latch_chain_door", "name": "Door chain latch", "use_case": "foley", "tags": "chain,latch,door", "prompt": "Door security chain sliding into latch then door opening a crack", "when": "Cautious open."},
    {"slug": "stairs_concrete_echo", "name": "Concrete stair echo", "use_case": "foley", "tags": "stairs,concrete,echo", "prompt": "Footsteps descending concrete stairs with parking-garage echo", "when": "Apartment stairwell."},
    {"slug": "parking_car_alarm_chirp", "name": "Car lock chirp", "use_case": "spot", "tags": "car,lock,chirp", "prompt": "Car remote lock double chirp in a quiet parking lot", "when": "Parking scenes."},
    {"slug": "trunk_close_car", "name": "Car trunk close", "use_case": "spot", "tags": "car,trunk,close", "prompt": "Car trunk lid slamming shut in a parking lot", "when": "Loading / hiding."},
    {"slug": "seatbelt_click", "name": "Seatbelt click", "use_case": "foley", "tags": "seatbelt,click,car", "prompt": "Seatbelt buckle click inside a quiet car cabin", "when": "Car interior."},
    {"slug": "wipers_rain", "name": "Wipers on wet glass", "use_case": "ambience", "tags": "wipers,rain,car,bed", "prompt": "Car windshield wipers on wet glass with rain, interior cabin bed", "when": "Driving in rain."},
    {"slug": "horn_traffic_jam", "name": "Traffic jam horns", "use_case": "ambience", "tags": "traffic,horns,jam,india,bed", "prompt": "Indian traffic jam layered horns and engines, dense but filterable bed", "when": "City gridlock."},
    {"slug": "metro_door_chime", "name": "Metro door chime", "use_case": "spot", "tags": "metro,door,chime", "prompt": "Metro train door closing chime then pneumatic door shut", "when": "Metro boarding."},
    {"slug": "escalator_hum", "name": "Escalator hum", "use_case": "ambience", "tags": "escalator,hum,mall,bed", "prompt": "Shopping-mall escalator mechanical hum and soft footsteps, loopable", "when": "Mall / station."},
    {"slug": "atm_beeps", "name": "ATM beeps", "use_case": "spot", "tags": "atm,beeps,bank", "prompt": "ATM keypad beeps and cash dispenser whir short sequence", "when": "ATM scene."},
    {"slug": "vault_door_heavy", "name": "Heavy vault door", "use_case": "spot", "tags": "vault,door,metal", "prompt": "Heavy bank vault door swinging and sealing with a deep clunk", "when": "Vault / secure room."},

    # ── Pocket FM / Indian serial / movie drama pack ─────────────────
    {"slug": "dandi_march_crowd", "name": "March crowd chanting", "use_case": "ambience", "tags": "march,crowd,chant,india,protest,bed", "prompt": "Large peaceful protest march on a dirt road, hundreds of footsteps, distant patriotic chanting, no individual clear words, cinematic historical India, loopable bed under narration, no music", "when": "Salt march / freedom struggle scenes."},
    {"slug": "conch_shell_ritual", "name": "Conch shell blow", "use_case": "spot", "tags": "conch,shankh,ritual,india,temple", "prompt": "Single Indian conch shell (shankh) blowing clearly then fading, temple courtyard reverb, ceremonial, no music", "when": "Ritual start, temple, historic call."},
    {"slug": "temple_bells_morning", "name": "Temple bells morning", "use_case": "ambience", "tags": "temple,bells,morning,india,bed", "prompt": "Multiple temple bells ringing at different distances at dawn, soft birds, calm Indian temple ambience bed, loopable, no music no chant", "when": "Temple morning / spiritual open."},
    {"slug": "aarti_thali_clink", "name": "Aarti thali clink", "use_case": "spot", "tags": "aarti,thali,puja,india", "prompt": "Brass aarti thali and small bells clinking briefly during puja, close warm foley", "when": "Puja / aarti moments."},
    {"slug": "village_morning_ambience", "name": "Village morning bed", "use_case": "ambience", "tags": "village,morning,india,birds,bed", "prompt": "Indian village morning: rooster, distant cows, soft birds, handpump drip far away, peaceful rural bed under dialogue, loopable, no music", "when": "Village dawn establishing."},
    {"slug": "village_evening_chulha", "name": "Chulha fire crackle", "use_case": "ambience", "tags": "chulha,fire,village,evening,india,bed", "prompt": "Village evening chulha wood fire crackling, soft pot simmer, distant dogs, warm rural bed, loopable", "when": "Village kitchen / evening home."},
    {"slug": "fields_wind_crops", "name": "Wind through crops", "use_case": "ambience", "tags": "fields,wind,crops,rural,bed", "prompt": "Wind moving through tall crops in open fields, soft insect hush, wide rural ambience bed, loopable", "when": "Farm / open countryside."},
    {"slug": "oxcart_wood_rattle", "name": "Ox cart rattle", "use_case": "spot", "tags": "oxcart,wood,rattle,rural,india", "prompt": "Wooden ox cart rolling on dirt path with creaks and wheel rattle, brief pass-by", "when": "Rural travel."},
    {"slug": "bullock_bells", "name": "Bullock bells", "use_case": "spot", "tags": "bullock,bells,rural,india", "prompt": "Bullock neck bells jingling irregularly as animals walk on a village road", "when": "Rural procession / farm."},
    {"slug": "monsoon_heavy_rain_street", "name": "Heavy monsoon rain on street", "use_case": "ambience", "tags": "monsoon,rain,india,street,bed", "prompt": "Heavy Indian monsoon rain on tin roof and wet street, continuous dense bed, loopable under dialogue, no thunder spikes, no music", "when": "Monsoon drama scenes."},
    {"slug": "monsoon_thunder_close", "name": "Close thunder clap", "use_case": "spot", "tags": "thunder,monsoon,storm", "prompt": "Close cinematic thunder clap with short rumble tail, dramatic punctuation, no rain bed included", "when": "Storm climax beats."},
    {"slug": "umbrella_open_rain", "name": "Umbrella open in rain", "use_case": "foley", "tags": "umbrella,rain,foley", "prompt": "Umbrella snapping open then rain hitting fabric, close foley", "when": "Character steps into rain."},
    {"slug": "flooded_street_splash", "name": "Flooded street splash", "use_case": "foley", "tags": "flood,splash,street,monsoon", "prompt": "Feet splashing through flooded street water, monsoon India, short sequence", "when": "Walking flood water."},
    {"slug": "bazaar_dense_india", "name": "Dense Indian bazaar", "use_case": "ambience", "tags": "bazaar,market,india,crowd,bed", "prompt": "Dense Indian bazaar: overlapping vendor calls (unintelligible), crowd murmur, scooter horns far, metal scales clink, lively bed under VO, loopable, no music", "when": "Market establishing."},
    {"slug": "sabzi_mandi_morning", "name": "Sabzi mandi morning", "use_case": "ambience", "tags": "sabzi,mandi,market,morning,india,bed", "prompt": "Morning vegetable mandi: baskets thuds, vendors calling, carts, busy but not chaotic, loopable bed", "when": "Morning market."},
    {"slug": "gold_shop_bell", "name": "Jewellery shop door bell", "use_case": "spot", "tags": "shop,bell,jewellery,india", "prompt": "Small brass shop door bell ringing once as customer enters a jewellery store", "when": "Shop entrance."},
    {"slug": "weighing_scale_clink", "name": "Shop scale clink", "use_case": "foley", "tags": "scale,clink,shop,india", "prompt": "Metal weighing scale pans clinking and weights placed, shop foley", "when": "Buying / selling."},
    {"slug": "wedding_shehnai_distant", "name": "Distant shehnai bed", "use_case": "ambience", "tags": "shehnai,wedding,india,distant,bed", "prompt": "Distant outdoor wedding shehnai melody very soft under crowd murmur, keep low for dialogue, festive India bed, short loopable texture (treat as ambience not full song)", "when": "Wedding nearby establishing (keep under VO)."},
    {"slug": "wedding_crowd_cheer", "name": "Wedding crowd cheer", "use_case": "spot", "tags": "wedding,crowd,cheer,india", "prompt": "Wedding guests cheering and clapping once, outdoor shamiana, joyful spot", "when": "Wedding celebration beat."},
    {"slug": "dhol_rhythm_distant", "name": "Distant dhol rhythm", "use_case": "ambience", "tags": "dhol,drums,festival,india,distant", "prompt": "Distant dhol drums at a street celebration, rhythmic but not overpowering, festive bed under dialogue", "when": "Festival / baraat approach."},
    {"slug": "baraat_horns_cheer", "name": "Baraat horns and cheer", "use_case": "spot", "tags": "baraat,horns,cheer,wedding,india", "prompt": "Baraat procession short burst: band horns, cheers, fireworks pop far, festive spot effect", "when": "Baraat arrival."},
    {"slug": "courtroom_murmur", "name": "Courtroom murmur bed", "use_case": "ambience", "tags": "court,murmur,legal,bed", "prompt": "Quiet courtroom audience murmur and paper rustle, tense formal bed under dialogue, loopable, no gavel", "when": "Court scenes under VO."},
    {"slug": "police_station_ambience", "name": "Police station bed", "use_case": "ambience", "tags": "police,station,india,office,bed", "prompt": "Indian police station: typewriter/keyboard, distant phones, ceiling fan, low voices, bureaucratic bed, loopable, no music", "when": "Thana / interrogation outer."},
    {"slug": "handcuff_click", "name": "Handcuff click", "use_case": "spot", "tags": "handcuff,police,metal", "prompt": "Metal handcuffs clicking shut once, close cinematic foley", "when": "Arrest beat."},
    {"slug": "jail_cell_door_clang", "name": "Jail cell door clang", "use_case": "spot", "tags": "jail,cell,door,metal", "prompt": "Heavy iron jail cell door slamming and locking with echo in a corridor", "when": "Prison lock-in."},
    {"slug": "jail_corridor_echo", "name": "Jail corridor echo bed", "use_case": "ambience", "tags": "jail,corridor,echo,bed", "prompt": "Distant jail corridor footsteps and metal clinks with long echo, sparse tense bed, loopable", "when": "Prison interiors."},
    {"slug": "interrogation_room_clock", "name": "Interrogation room clock", "use_case": "ambience", "tags": "clock,interrogation,tense,bed", "prompt": "Loud wall clock ticking in a quiet interrogation room, tense minimal bed, loopable", "when": "Interrogation silence."},
    {"slug": "newsroom_typewriters", "name": "Newsroom typewriters", "use_case": "ambience", "tags": "newsroom,typewriter,office,bed", "prompt": "Busy newsroom with overlapping typewriters and phones, period or modern mix, energetic bed under VO", "when": "News / press scenes."},
    {"slug": "camera_flash_bulbs", "name": "Press camera flashes", "use_case": "spot", "tags": "camera,flash,press,paparazzi", "prompt": "Multiple press camera flash bulbs popping rapidly with shutter clicks, short burst", "when": "Media scrum."},
    {"slug": "radio_news_jingle_static", "name": "Radio news sting", "use_case": "spot", "tags": "radio,news,static,period", "prompt": "Short vintage radio news sting with brief static then announcer tone (no clear words), period India flavor", "when": "Historical radio cutaway."},
    {"slug": "tv_news_room_tone", "name": "TV news bed", "use_case": "ambience", "tags": "tv,news,studio,bed", "prompt": "Soft TV news studio hum and distant control-room chatter, modern bed under dialogue", "when": "News studio."},
    {"slug": "hospital_corridor_busy", "name": "Busy hospital corridor", "use_case": "ambience", "tags": "hospital,corridor,busy,bed", "prompt": "Busy hospital corridor: trolley wheels, soft PA, footsteps, tense medical bed, loopable, no clear announcements", "when": "Hospital drama."},
    {"slug": "ot_machine_beeps", "name": "OT machine beeps", "use_case": "ambience", "tags": "ot,hospital,beeps,surgery,bed", "prompt": "Operating theatre machine beeps and oxygen hiss, sterile tense bed, loopable under dialogue", "when": "Surgery / OT."},
    {"slug": "ambulance_siren_pass", "name": "Ambulance siren pass-by", "use_case": "spot", "tags": "ambulance,siren,passby,india", "prompt": "Indian ambulance siren Doppler pass-by on a city street, short cinematic spot", "when": "Emergency arrival."},
    {"slug": "school_bell_india", "name": "School bell ring", "use_case": "spot", "tags": "school,bell,india", "prompt": "School handbell or electric bell ringing in a courtyard with distant children, brief", "when": "School scenes."},
    {"slug": "classroom_chalk_squeak", "name": "Chalk on blackboard", "use_case": "foley", "tags": "chalk,blackboard,school", "prompt": "Chalk writing and squeaking on a blackboard, classroom foley", "when": "Classroom."},
    {"slug": "college_canteen_buzz", "name": "College canteen buzz", "use_case": "ambience", "tags": "college,canteen,crowd,youth,bed", "prompt": "College canteen crowd chatter and steel plates, youthful energy bed, loopable, unintelligible voices", "when": "College youth scenes."},
    {"slug": "hostel_corridor_night", "name": "Hostel corridor night", "use_case": "ambience", "tags": "hostel,corridor,night,bed", "prompt": "Quiet hostel corridor at night: distant fan, door close far, sparse footsteps, loopable bed", "when": "Hostel night."},
    {"slug": "office_open_plan_india", "name": "Open office India bed", "use_case": "ambience", "tags": "office,corporate,india,bed", "prompt": "Indian open-plan office: keyboards, soft phones, AC hum, muted chatter, corporate bed under dialogue", "when": "Office drama."},
    {"slug": "boardroom_chair_scrape", "name": "Boardroom chair scrape", "use_case": "foley", "tags": "chair,boardroom,office", "prompt": "Office chair scraping on floor as someone stands in a quiet boardroom", "when": "Meeting tension."},
    {"slug": "elevator_ding_doors", "name": "Elevator ding and doors", "use_case": "spot", "tags": "elevator,ding,doors", "prompt": "Elevator arrival ding then doors opening in a lobby", "when": "Corporate / apartment arrival."},
    {"slug": "penthouse_city_night", "name": "Penthouse city night bed", "use_case": "ambience", "tags": "city,night,penthouse,bed", "prompt": "High-rise window city night ambience: distant traffic wash, soft wind, luxurious quiet bed, loopable", "when": "Rich apartment night."},
    {"slug": "slum_night_ambience", "name": "Basti night bed", "use_case": "ambience", "tags": "slum,basti,night,india,bed", "prompt": "Dense basti night: distant TVs, dogs, soft crowd, generator far, authentic urban poor India bed, loopable, no music", "when": "Basti / chawl night."},
    {"slug": "chawl_corridor_voices", "name": "Chawl corridor voices", "use_case": "ambience", "tags": "chawl,corridor,voices,mumbai,bed", "prompt": "Mumbai chawl corridor: distant cooking, neighbours' muffled voices, shared bathroom drip, intimate bed", "when": "Chawl interiors."},
    {"slug": "train_general_compartment", "name": "Train general compartment", "use_case": "ambience", "tags": "train,compartment,india,bed", "prompt": "Indian train general compartment: track rhythm, vendors far, soft chatter, window rattle, travel bed under dialogue, loopable", "when": "Train journey."},
    {"slug": "train_whistle_long", "name": "Train whistle long", "use_case": "spot", "tags": "train,whistle,india", "prompt": "Long Indian locomotive whistle across open countryside, cinematic spot", "when": "Train travel punctuation."},
    {"slug": "platform_chai_vendor", "name": "Platform chai vendor call", "use_case": "spot", "tags": "chai,vendor,platform,train,india", "prompt": "Distant chai vendor calling on a railway platform with train idle underneath, brief color spot (unintelligible)", "when": "Station color."},
    {"slug": "bus_stand_india", "name": "Bus stand India bed", "use_case": "ambience", "tags": "bus,stand,india,crowd,bed", "prompt": "Indian bus stand: diesel buses, horns, crowd, conductor whistles far, dusty travel bed, loopable", "when": "Intercity bus travel."},
    {"slug": "auto_rickshaw_ride", "name": "Auto rickshaw ride bed", "use_case": "ambience", "tags": "auto,rickshaw,ride,india,bed", "prompt": "Inside auto-rickshaw ride: engine putter, street wash, occasional horn, bumpy cabin bed, loopable under dialogue", "when": "Auto travel scenes."},
    {"slug": "scooter_start_india", "name": "Scooter kick start", "use_case": "spot", "tags": "scooter,start,india", "prompt": "Old Indian scooter kick-start attempts then engine catching, short spot", "when": "Departure beats."},
    {"slug": "highway_night_drive", "name": "Highway night drive bed", "use_case": "ambience", "tags": "highway,night,car,bed", "prompt": "Car interior highway night: engine drone, soft tyre roar, occasional pass-by, tense travel bed, loopable", "when": "Night drive thriller."},
    {"slug": "car_chase_passby", "name": "Car chase pass-by", "use_case": "spot", "tags": "car,chase,passby,action", "prompt": "Fast car Doppler pass-by with tyre screech hint, action spot, no music", "when": "Chase punctuation."},
    {"slug": "tyre_screech_hard", "name": "Hard tyre screech", "use_case": "spot", "tags": "tyre,screech,action", "prompt": "Hard tyre screech on asphalt then short skid, action punctuation", "when": "Sudden stop / chase."},
    {"slug": "gunshot_distant_echo", "name": "Distant gunshot echo", "use_case": "spot", "tags": "gunshot,distant,echo,thriller", "prompt": "Single distant gunshot with outdoor echo, thriller punctuation, not overly loud for dialogue mix", "when": "Thriller violence beat (use sparingly)."},
    {"slug": "punch_body_impact", "name": "Punch body impact", "use_case": "spot", "tags": "punch,fight,impact", "prompt": "Single fist body impact thud with short cloth rustle, fight foley spot", "when": "Fight scene."},
    {"slug": "glass_shatter_window", "name": "Window glass shatter", "use_case": "spot", "tags": "glass,shatter,window", "prompt": "Window glass shattering with shards falling, dramatic spot", "when": "Break-in / accident."},
    {"slug": "explosion_distant_boom", "name": "Distant explosion boom", "use_case": "spot", "tags": "explosion,distant,boom,action", "prompt": "Distant low explosion boom with debris rumble, cinematic but not ear-splitting", "when": "Action climax far."},
    {"slug": "romantic_park_evening", "name": "Park evening romance bed", "use_case": "ambience", "tags": "park,evening,romance,birds,bed", "prompt": "Quiet park at evening: soft birds, distant kids, gentle breeze, romantic calm bed under dialogue, loopable, no music", "when": "Romantic park scenes."},
    {"slug": "cafe_soft_chatter", "name": "Cafe soft chatter bed", "use_case": "ambience", "tags": "cafe,chatter,cups,bed", "prompt": "Soft cafe chatter, cup clinks, espresso machine far, intimate conversation bed, loopable, unintelligible voices", "when": "Cafe / coffee dates."},
    {"slug": "rain_on_umbrella_close", "name": "Rain on umbrella close", "use_case": "ambience", "tags": "rain,umbrella,close,romance,bed", "prompt": "Close rain hitting umbrella fabric while two people stand still, intimate monsoon bed, loopable", "when": "Romantic rain beat."},
    {"slug": "heartbeat_tense_bed", "name": "Tense heartbeat bed", "use_case": "design", "tags": "heartbeat,tense,thriller,design", "prompt": "Low muffled heartbeat pulse for thriller tension under VO, subtle design bed, loopable, no music", "when": "Fear / panic POV."},
    {"slug": "horror_drone_low", "name": "Low horror drone", "use_case": "design", "tags": "horror,drone,tension,design", "prompt": "Very low subtle horror drone texture without melody, keep under dialogue, atmospheric design bed", "when": "Horror dread under VO."},
    {"slug": "jump_scare_stinger", "name": "Jump scare stinger", "use_case": "spot", "tags": "jumpscare,stinger,horror", "prompt": "Short sharp horror jump-scare stinger hit (non-musical impact), brief punctuation", "when": "Horror reveal."},
    {"slug": "whispers_behind_wall", "name": "Whispers behind wall", "use_case": "design", "tags": "whisper,wall,horror,design", "prompt": "Muffled unintelligible whispers seeming to come from behind a wall, eerie sparse design", "when": "Haunting presence."},
    {"slug": "old_haveli_ambience", "name": "Old haveli bed", "use_case": "ambience", "tags": "haveli,old,house,india,bed", "prompt": "Old Indian haveli: wood creaks, courtyard birds, distant pigeons, soft wind in corridors, period mansion bed, loopable", "when": "Haveli / ancestral home."},
    {"slug": "palace_corridor_echo", "name": "Palace corridor echo", "use_case": "ambience", "tags": "palace,corridor,echo,period,bed", "prompt": "Large palace stone corridor with soft echo footsteps far and airy reverb, regal sparse bed", "when": "Palace / period drama."},
    {"slug": "sword_draw_metal", "name": "Sword draw", "use_case": "spot", "tags": "sword,metal,period,action", "prompt": "Sword drawing from scabbard with metallic ring, period action spot", "when": "Period fight ready."},
    {"slug": "cavalry_horses_pass", "name": "Cavalry horses pass", "use_case": "spot", "tags": "horses,cavalry,period,passby", "prompt": "Group of horses galloping past on dirt, period battle flavor, short pass-by", "when": "Period war / chase."},
    {"slug": "battlefield_distant", "name": "Distant battlefield bed", "use_case": "ambience", "tags": "battle,distant,period,war,bed", "prompt": "Distant battlefield: muffled shouts, metal clashes far, drums hint, keep under narration, historical war bed", "when": "War establishing (historical)."},
    {"slug": "crowd_booing_angry", "name": "Angry crowd booing", "use_case": "spot", "tags": "crowd,boo,angry,protest", "prompt": "Angry crowd booing and shouting (unintelligible), outdoor, short intense spot", "when": "Public backlash."},
    {"slug": "crowd_applause_big", "name": "Big crowd applause", "use_case": "spot", "tags": "crowd,applause,cheer", "prompt": "Large crowd sustained applause and cheers, outdoor rally, triumphant spot", "when": "Speech success / rally."},
    {"slug": "stadium_cheer_wave", "name": "Stadium cheer wave", "use_case": "spot", "tags": "stadium,cheer,sports", "prompt": "Stadium crowd rising cheer wave, sports or concert energy, short spot", "when": "Big public moment."},
    {"slug": "cinema_hall_india", "name": "Cinema hall bed", "use_case": "ambience", "tags": "cinema,hall,india,bed", "prompt": "Indian single-screen cinema hall: soft audience, projector hum, AC, muted film audio far, nostalgic bed under dialogue", "when": "Cinema scenes."},
    {"slug": "theatre_stage_ambience", "name": "Theatre stage wings bed", "use_case": "ambience", "tags": "theatre,stage,wings,bed", "prompt": "Theatre wings: soft rope creaks, distant audience hush, stage light buzz, performance bed", "when": "Stage / natak."},
    {"slug": "mehfil_soft_claps", "name": "Mehfil soft claps", "use_case": "spot", "tags": "mehfil,claps,ghazal,india", "prompt": "Small intimate mehfil audience soft claps and wah-wah murmurs (unintelligible), cultured spot", "when": "Cultural gathering."},
    {"slug": "kitchen_pressure_cooker", "name": "Pressure cooker whistle", "use_case": "spot", "tags": "pressure,cooker,kitchen,india", "prompt": "Indian pressure cooker whistle blast then steam hiss, domestic spot", "when": "Home kitchen."},
    {"slug": "kitchen_morning_india", "name": "Indian kitchen morning bed", "use_case": "ambience", "tags": "kitchen,morning,india,bed", "prompt": "Indian home kitchen morning: tadka sizzle soft, utensils, fridge hum, domestic bed under dialogue, loopable", "when": "Family morning."},
    {"slug": "doorbell_flat_india", "name": "Flat doorbell India", "use_case": "spot", "tags": "doorbell,flat,apartment,india", "prompt": "Indian apartment doorbell ding-dong once in a hallway", "when": "Visitor at flat."},
    {"slug": "neighbour_tv_through_wall", "name": "Neighbour TV through wall", "use_case": "ambience", "tags": "tv,neighbour,wall,apartment,bed", "prompt": "Muffled neighbour television through apartment wall, soft soap-opera wash, urban intimacy bed", "when": "Apartment thin walls."},
    {"slug": "rooftop_city_evening", "name": "Rooftop city evening bed", "use_case": "ambience", "tags": "rooftop,city,evening,india,bed", "prompt": "City rooftop evening: distant traffic, kite strings soft wind, sparrows, contemplative India bed, loopable", "when": "Rooftop conversations."},
    {"slug": "ghat_river_bells", "name": "River ghat bells bed", "use_case": "ambience", "tags": "ghat,river,bells,india,spiritual,bed", "prompt": "River ghat: soft water, distant temple bells, sparse footsteps on stone, spiritual India bed, loopable, no music", "when": "Ghat / spiritual river."},
    {"slug": "boat_oar_water", "name": "Boat oar in water", "use_case": "foley", "tags": "boat,oar,water,river", "prompt": "Wooden oar dipping and pulling through river water, calm foley sequence", "when": "Boat crossing."},
    {"slug": "forest_night_india", "name": "Indian forest night bed", "use_case": "ambience", "tags": "forest,night,insects,india,bed", "prompt": "Indian forest night: dense insects, distant owl, soft leaves, thriller-ready bed under dialogue, loopable, no scream animals", "when": "Jungle / forest night."},
    {"slug": "snake_hiss_short", "name": "Snake hiss short", "use_case": "spot", "tags": "snake,hiss,danger", "prompt": "Short snake hiss close perspective, danger punctuation, brief", "when": "Snake threat beat."},
    {"slug": "leopard_distant_call", "name": "Distant wild call", "use_case": "spot", "tags": "wildlife,distant,forest,thriller", "prompt": "Distant wild feline call in forest night, eerie sparse spot", "when": "Wildlife threat far."},
    {"slug": "factory_machinery_bed", "name": "Factory machinery bed", "use_case": "ambience", "tags": "factory,machinery,industrial,bed", "prompt": "Factory floor machinery hum and rhythmic clanks, industrial bed under dialogue, loopable", "when": "Mill / factory drama."},
    {"slug": "construction_site_india", "name": "Construction site India", "use_case": "ambience", "tags": "construction,site,india,bed", "prompt": "Indian construction site: hammering, rebar clinks, distant mixer, dusty work bed, loopable", "when": "Labour / site scenes."},
    {"slug": "mine_tunnel_drip", "name": "Mine tunnel drip bed", "use_case": "ambience", "tags": "mine,tunnel,drip,echo,bed", "prompt": "Dark mine tunnel water drips with long echo and distant rumble, claustrophobic bed", "when": "Mine / tunnel thriller."},
    {"slug": "clock_tower_chime", "name": "Clock tower chime", "use_case": "spot", "tags": "clock,tower,chime,city", "prompt": "Distant clock tower chiming the hour across a city, period or colonial flavor", "when": "Time jump / city establish."},
    {"slug": "church_bells_distant", "name": "Distant church bells", "use_case": "spot", "tags": "church,bells,distant", "prompt": "Distant church bells pealing across a town, brief establishing spot", "when": "Town morning / funeral far."},
    {"slug": "mosque_azan_distant", "name": "Distant azan texture", "use_case": "ambience", "tags": "azan,mosque,distant,india,bed", "prompt": "Very distant soft azan call texture mixed with city evening hush, respectful low bed under dialogue (keep unintelligible/soft), no music bed competing", "when": "Evening city spiritual color (use carefully)."},
    {"slug": "election_rally_crowd", "name": "Election rally crowd bed", "use_case": "ambience", "tags": "election,rally,crowd,india,bed", "prompt": "Political rally crowd roar and megaphone wash (unintelligible), energetic India bed under narration", "when": "Political drama."},
    {"slug": "megaphone_feedback", "name": "Megaphone feedback", "use_case": "spot", "tags": "megaphone,feedback,rally", "prompt": "Megaphone brief feedback squeal then voice tone (no clear words), rally spot", "when": "Rally technical beat."},
    {"slug": "breaking_news_stinger", "name": "Breaking news stinger", "use_case": "spot", "tags": "news,stinger,tv,drama", "prompt": "Short modern breaking-news style stinger hit (non-song), media punctuation", "when": "News cutaway."},
    {"slug": "phone_vibrate_table", "name": "Phone vibrate on table", "use_case": "spot", "tags": "phone,vibrate,table,modern", "prompt": "Smartphone vibrating on a wooden table, modern urgency spot", "when": "Incoming call/message."},
    {"slug": "whatsapp_notify_soft", "name": "Message notify soft", "use_case": "spot", "tags": "message,notify,phone,modern", "prompt": "Soft generic mobile message notification chime once (not branded), modern spot", "when": "Chat message beat."},
    {"slug": "video_call_connect", "name": "Video call connect", "use_case": "spot", "tags": "videocall,connect,modern", "prompt": "Video call connecting tones then soft open, modern communication spot", "when": "Remote conversation start."},
]


def curated_sfx_rows() -> list[dict]:
    """Background / ambience / foley prompt catalog for ElevenLabs text-to-SFX.

    There is no ElevenLabs API that lists a stock SFX library — effects are generated
    from text prompts. These rows are the searchable background beds + spot effects
    for cast recommend (asset_type=sfx).
    """
    now = datetime.now(timezone.utc).isoformat()
    rows: list[dict] = []
    for e in SFX_ENTRIES:
        use = e["use_case"]
        kind = {
            "ambience": "background ambience bed (loopable under dialogue)",
            "foley": "foley / movement spot effect",
            "spot": "short spot sound effect",
            "design": "designed tension / horror texture",
        }.get(use, "sound effect")
        description = (
            f"Background / scene audio: {e['name']}. Kind: {kind}. "
            f"ElevenLabs sound effect prompt: {e['prompt']} "
            f"When to use: {e['when']} "
            f"Use case: {use}. Tags: {e['tags']}. "
            "Suitable for Pocket FM serial audio drama beds, Indian film/TV drama, "
            "historical protest marches, romance, thriller, horror atmosphere, "
            "village/city/train/hospital/court ambience, and layered background under character voices. "
            "Generate via ElevenLabs text-to-sound-effects API using the prompt above. "
            "No music bed unless the prompt explicitly asks for a soft distant texture."
        )
        rows.append(
            {
                "id": f"sfx_{e['slug']}",
                "asset_type": "sfx",
                "provider": "elevenlabs",
                "provider_id": e["slug"],
                "name": e["name"],
                "language": "any",
                "gender": None,
                "age": None,
                "accent": None,
                "use_case": use,
                "free_users_allowed": True,
                "preview_url": None,
                "tags": f"{e['tags']},background,sfx,{use}|prompt:{e['prompt']}",
                "description": description,
                "updated_at": now,
            }
        )
    return rows

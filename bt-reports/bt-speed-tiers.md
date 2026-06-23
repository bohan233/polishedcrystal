# BT Speed Tier Table (Lv50)
Source: data/battle_tower/parties.asm + data/battle_tower/dvs.asm
Formula: Spe = BaseSpe + SpeDV + 5, then ×nature (floor ×1.1 SPE_UP / ×0.9 SPE_DOWN), 0 stat exp
Note: regenerate with `python3 generate_bt_speed_tiers.py` when parties.asm is updated

Sorted by **effective threat speed** (post-Scarf, post-setup, or post-self-weather when applicable).
One row per unique species/form threat. Fastest variant kept when multiple sets exist.

| Rank | Pokemon | Base Spe | Spe DV | Nature | Spe stat | +Scarf | +1 Speed | +2 Speed | Threat | Ability | Item | Moves |
|------|---------|----------|--------|--------|----------|--------|----------|----------|--------|---------|------|-------|
| 1 | Weavile | 125 | 15 | neutral | 145 | — | — | 290 | Agility | Technician | Life Orb | Icicle Crash, Knock Off, Low Kick, Agility |
| 2 | Smeargle | 100 | 15 | SPE_UP | 132 | — | — | 264 | Shell Smash | Moody | Focus Sash | Spore, Substitute, Baton Pass, Shell Smash |
| 3 | Jumpluff | 110 | 15 | neutral | 130 | — | — | 260 | Chlorophyll Sun | Chlorophyll | Life Orb | Solar Beam, Dazzling Gleam, Hidden Power(Ground), Sunny Day |
| 4 | Girafarig | 95 | 15 | SPE_UP | 126 | — | — | 252 | Agility | Sap Sipper | Eviolite | Dark Pulse, Baton Pass, Substitute, Agility |
| 5 | Leafeon | 95 | 15 | neutral | 115 | — | — | 230 | Chlorophyll Sun | Chlorophyll | Life Orb | Seed Bomb, Knock Off, Strength, Sunny Day |
| 6 | Ledian | 85 | 15 | SPE_UP | 115 | — | — | 230 | Agility | Early Bird | Leftovers | Knock Off, Baton Pass, Roost, Agility |
| 7 | Seadra | 85 | 15 | SPE_UP | 115 | — | — | 230 | Agility | Poison Point | Eviolite | Surf, Ice Beam, Flamethrower, Agility |
| 8 | Moltres | 90 | 15 | neutral | 110 | — | — | 220 | Agility | Berserk | Chesto Berry | Dark Pulse, Air Slash, Rest, Agility |
| 9 | Porygon-Z | 90 | 14 | neutral | 109 | — | — | 218 | Agility | Adaptability | Life Orb | Tri Attack, Dark Pulse, Hidden Power(Fighting), Agility |
| 10 | Feraligatr | 88 | 15 | neutral | 108 | — | — | 216 | Agility | Sheer Force | Life Orb | Waterfall, Crunch, Ice Punch, Agility |
| 11 | Golduck | 85 | 15 | neutral | 105 | — | — | 210 | Swift Swim Rain | Swift Swim | Life Orb | Hydro Pump, Ice Beam, Hidden Power(Grass), Rain Dance |
| 12 | Kingdra | 85 | 15 | neutral | 105 | — | — | 210 | Swift Swim Rain | Swift Swim | Life Orb | Hydro Pump, Dragon Pulse, Ice Beam, Rain Dance |
| 13 | Kleavor | 85 | 15 | neutral | 105 | — | — | 210 | Agility | Sheer Force | Life Orb | Rock Slide, Bug Bite, Close Combat, Agility |
| 14 | Overqwil | 85 | 15 | neutral | 105 | — | — | 210 | Swift Swim Rain | Swift Swim | Life Orb | Waterfall, Poison Jab, Explosion, Rain Dance |
| 15 | Qwilfish | 85 | 15 | neutral | 105 | — | — | 210 | Swift Swim Rain | Swift Swim | Life Orb | Waterfall, Poison Jab, Explosion, Rain Dance |
| 16 | Seaking | 83 | 15 | neutral | 103 | — | — | 206 | Swift Swim Rain | Swift Swim | Life Orb | Hydro Pump, Ice Beam, Hidden Power(Electric), Rain Dance |
| 17 | Kabutops | 80 | 15 | neutral | 100 | — | — | 200 | Swift Swim Rain | Swift Swim | Leftovers | Stone Edge, Waterfall, Knock Off, Rain Dance |
| 18 | Charizard | 100 | 15 | SPE_UP | 132 | — | 198 | — | Dragon Dance | Tough Claws | Leftovers | Fire Punch, Dragon Claw, Roost, Dragon Dance |
| 19 | Cloyster | 70 | 15 | SPE_UP | 99 | — | — | 198 | Shell Smash | Overcoat | Life Orb | Hydro Pump, Ice Beam, Explosion, Shell Smash |
| 20 | Venusaur | 80 | 14 | neutral | 99 | — | — | 198 | Chlorophyll Sun | Chlorophyll | Life Orb | Solar Beam, Sludge Bomb, Hidden Power(Fire), Sunny Day |
| 21 | Blastoise | 78 | 15 | neutral | 98 | — | — | 196 | Shell Smash | Torrent | White Herb | Waterfall, Iron Head, Close Combat, Shell Smash |
| 22 | Tauros | 110 | 15 | neutral | 130 | 195 | — | — | Scarf | Intimidate | Choice Scarf | Double-Edge, Earthquake, Zen Headbutt, Stone Edge |
| 23 | Arcanine | 95 | 15 | SPE_UP | 126 | — | 189 | — | Dragon Dance | Intimidate | Life Orb | Flare Blitz, Wild Charge, Close Combat, Dragon Dance |
| 24 | Jynx | 96 | 14 | SPE_UP | 126 | 189 | — | — | Scarf | Filter | Choice Scarf | Ice Beam, Psychic, Focus Blast, Hidden Power(Fire) |
| 25 | Mr. Mime | 95 | 15 | SPE_UP | 126 | 189 | — | — | Scarf | Soundproof | Choice Scarf | Psychic, Dazzling Gleam, Thunderbolt, Focus Blast |
| 26 | Furret | 105 | 15 | neutral | 125 | 187 | — | — | Scarf | Keen Eye | Choice Scarf | Double-Edge, Strength, Knock Off, U-turn |
| 27 | Sandslash-A | 65 | 15 | SPE_UP | 93 | — | — | 186 | Slush Rush Hail | Slush Rush | Life Orb | Icicle Crash, Iron Head, Earthquake, Hail |
| 28 | Butterfree | 90 | 15 | SPE_UP | 121 | 181 | — | — | Scarf | Levitate | Choice Scarf | Bug Buzz, Psychic, Giga Drain, Hidden Power(Ground) |
| 29 | Zapdos | 100 | 15 | neutral | 120 | 180 | — | — | Scarf | Defiant | Choice Scarf | Close Combat, Brave Bird, U-turn, Knock Off |
| 30 | Mantine | 70 | 15 | neutral | 90 | — | — | 180 | Swift Swim Rain | Swift Swim | Damp Rock | Surf, Hurricane, Roost, Rain Dance |
| 31 | Heracross | 85 | 15 | SPE_UP | 115 | 172 | — | — | Scarf | Moxie | Choice Scarf | Megahorn, Close Combat, Stone Edge, Knock Off |
| 32 | Primeape | 95 | 15 | neutral | 115 | 172 | — | — | Scarf | Gorilla Tactics | Choice Scarf | Close Combat, Stone Edge, Gunk Shot, Ice Punch |
| 33 | Electrode | 150 | 15 | neutral | 170 | — | — | — | Fast | Aftermath | Focus Sash | Thunderbolt, Hidden Power(Grass), Bug Buzz, Explosion |
| 34 | Ampharos | 65 | 15 | neutral | 85 | — | — | 170 | Agility | Static | Life Orb | Thunderbolt, Dragon Pulse, Focus Blast, Agility |
| 35 | Gyarados (Red) | 81 | 15 | SPE_UP | 111 | — | 166 | — | Dragon Dance | Moxie | Life Orb | Waterfall, Fly, Strength, Dragon Dance |
| 36 | Aerodactyl | 130 | 15 | SPE_UP | 165 | — | — | — | Fast | Rock Head | Life Orb | Stone Edge, Brave Bird, Earthquake, Hone Claws |
| 37 | Crobat | 130 | 15 | SPE_UP | 165 | — | — | — | Fast | Inner Focus | Red Card | Brave Bird, Super Fang, Roost, Toxic |
| 38 | Annihilape | 90 | 15 | neutral | 110 | 165 | — | — | Scarf | Gorilla Tactics | Choice Scarf | Close Combat, Shadow Claw, Ice Punch, U-turn |
| 39 | Dragonite | 80 | 15 | SPE_UP | 110 | — | 165 | — | Dragon Dance | Multiscale | Weak Policy | Dragon Claw, Iron Head, Fire Punch, Dragon Dance |
| 40 | Togekiss | 80 | 15 | SPE_UP | 110 | 165 | — | — | Scarf | Serene Grace | Choice Scarf | Moonblast, Aeroblast, Fire Blast, Aura Sphere |
| 41 | Jolteon | 130 | 14 | SPE_UP | 163 | — | — | — | Fast | Volt Absorb | Life Orb | Thunderbolt, Shadow Ball, Hidden Power(Ice), Toxic |
| 42 | Lapras | 60 | 15 | neutral | 80 | — | — | 160 | Shell Smash | Water Absorb | Leftovers | Surf, Ice Beam, Thunderbolt, Shell Smash |
| 43 | Sunflora | 60 | 15 | neutral | 80 | — | — | 160 | Chlorophyll Sun | Chlorophyll | Heat Rock | Solar Beam, Flamethrower, Healinglight, Sunny Day |
| 44 | Pinsir | 85 | 15 | neutral | 105 | 157 | — | — | Scarf | Moxie | Choice Scarf | Megahorn, Stone Edge, Earthquake, Knock Off |
| 45 | Alakazam | 120 | 15 | SPE_UP | 154 | — | — | — | Fast | Trace | Focus Sash | Psychic, Shadow Ball, Calm Mind, Recover |
| 46 | Dugtrio | 120 | 15 | SPE_UP | 154 | — | — | — | Fast | Arena Trap | Choice Band | Earthquake, Stone Edge, Sucker Punch, Toxic |
| 47 | Raichu | 120 | 15 | SPE_UP | 154 | — | — | — | Fast | Static | Choice Band | Wild Charge, Strength, Knock Off, Extremespeed |
| 48 | Raichu-A | 120 | 15 | SPE_UP | 154 | — | — | — | Fast | Static | Choice Specs | Volt Switch, Psychic, Surf, Focus Blast |
| 49 | Sneasler | 120 | 15 | SPE_UP | 154 | — | — | — | Fast | Poison Touch | Life Orb | Close Combat, Knock Off, Ice Punch, Swords Dance |
| 50 | Ditto | 108 | 0 | SPE_DOWN | 101 | 151 | — | — | Scarf | Imposter | Choice Scarf | Transform, No Move, No Move, No Move |
| 51 | Gyarados | 81 | 15 | neutral | 101 | — | 151 | — | Dragon Dance | Intimidate | Leftovers | Waterfall, Dragon Dance, Rest, Sleep Talk |
| 52 | Omastar | 55 | 15 | neutral | 75 | — | — | 150 | Shell Smash | Weak Armor | White Herb | Power Gem, Hydro Pump, Ice Beam, Shell Smash |
| 53 | Ambipom | 115 | 15 | SPE_UP | 148 | — | — | — | Fast | Technician | Choice Band | Return, Low Kick, Aerial Ace, Knock Off |
| 54 | Persian | 115 | 15 | SPE_UP | 148 | — | — | — | Fast | Technician | Red Card | Thief, Aerial Ace, Hypnosis, Hone Claws |
| 55 | Persian-A | 115 | 15 | SPE_UP | 148 | — | — | — | Fast | Fur Coat | Leftovers | Dark Pulse, Attract, Rest, Toxic |
| 56 | Sneasel | 115 | 15 | SPE_UP | 148 | — | — | — | Fast | Inner Focus | Focus Sash | Icicle Crash, Knock Off, Strength, Swords Dance |
| 57 | Sneasel-H | 115 | 15 | SPE_UP | 148 | — | — | — | Fast | Inner Focus | Focus Sash | Poison Jab, Close Combat, Knock Off, Swords Dance |
| 58 | Starmie | 115 | 15 | SPE_UP | 148 | — | — | — | Fast | Natural Cure | Light Clay | Scald, Reflect, Light Screen, Thunder Wave |
| 59 | Mr. Rime | 70 | 15 | SPE_UP | 99 | 148 | — | — | Scarf | Screen Cleaner | Choice Scarf | Ice Beam, Psychic, Thunderbolt, Dazzling Gleam |
| 60 | Exeggutor | 55 | 14 | neutral | 74 | — | — | 148 | Chlorophyll Sun | Chlorophyll | Life Orb | Solar Beam, Psychic, Hidden Power(Fire), Sunny Day |
| 61 | Raikou | 115 | 14 | SPE_UP | 147 | — | — | — | Fast | Volt Absorb | Light Clay | Volt Switch, Hidden Power(Ice), Reflect, Light Screen |
| 62 | Dodrio | 110 | 15 | SPE_UP | 143 | — | — | — | Fast | Early Bird | Life Orb | Brave Bird, Hi Jump Kick, Knock Off, Swords Dance |
| 63 | Dugtrio-A | 110 | 15 | SPE_UP | 143 | — | — | — | Fast | Sand Force | Focus Sash | Earthquake, Iron Head, Stone Edge, Sandstorm |
| 64 | Espeon | 110 | 15 | SPE_UP | 143 | — | — | — | Fast | Magic Bounce | Light Clay | Psychic, Reflect, Light Screen, Toxic |
| 65 | Gengar | 110 | 15 | SPE_UP | 143 | — | — | — | Fast | Shadow Tag | Black Sludge | Hex, Sludge Bomb, Destiny Bond, Will-O-Wisp |
| 66 | Mismagius | 110 | 15 | SPE_UP | 143 | — | — | — | Fast | Levitate | Leftovers | Hex, Dazzling Gleam, Destiny Bond, Will-O-Wisp |
| 67 | Ninetales | 109 | 15 | SPE_UP | 141 | — | — | — | Fast | Drought | Leftovers | Fire Blast, Shadow Ball, Solar Beam, Nasty Plot |
| 68 | Ninetales-A | 109 | 15 | SPE_UP | 141 | — | — | — | Fast | Snow Warning | Leftovers | Blizzard, Moonblast, Hex, Will-O-Wisp |
| 69 | Raticate | 108 | 15 | SPE_UP | 140 | — | — | — | Fast | Guts | Flame Orb | Facade, Super Fang, Sucker Punch, U-turn |
| 70 | Bellossom | 50 | 14 | neutral | 69 | — | — | 138 | Chlorophyll Sun | Chlorophyll | Life Orb | Solar Beam, Hidden Power(Fire), Earth Power, Sunny Day |
| 71 | Rapidash | 105 | 15 | SPE_UP | 137 | — | — | — | Fast | Flash Fire | Life Orb | Flare Blitz, Play Rough, Wild Charge, Swords Dance |
| 72 | Rapidash-G | 105 | 15 | SPE_UP | 137 | — | — | — | Fast | Pastel Veil | Life Orb | Play Rough, Strength, Extremespeed, Swords Dance |
| 73 | Scyther | 105 | 15 | SPE_UP | 137 | — | — | — | Fast | Technician | Choice Band | U-turn, Aerial Ace, Knock Off, Rock Smash |
| 74 | Electabuzz | 105 | 14 | SPE_UP | 136 | — | — | — | Fast | Vital Spirit | Eviolite | Volt Switch, Focus Blast, Hidden Power(Ice), Psychic |
| 75 | Pidgeot | 101 | 15 | SPE_UP | 133 | — | — | — | Fast | No Guard | Life Orb | Hurricane, Focus Blast, Roost, U-turn |
| 76 | Tyranitar | 61 | 15 | SPE_UP | 89 | 133 | — | — | Scarf | Sand Stream | Choice Scarf | Rock Slide, Crunch, Iron Head, Fire Punch |
| 77 | Entei | 100 | 15 | SPE_UP | 132 | — | — | — | Fast | Pressure | Leftovers | Sacred Fire, Protect, Substitute, Toxic |
| 78 | Fearow | 100 | 15 | SPE_UP | 132 | — | — | — | Fast | Sniper | Scope Lens | Double-Edge, Drill Peck, U-turn, Pursuit |
| 79 | Miltank | 100 | 15 | SPE_UP | 132 | — | — | — | Fast | Sap Sipper | Life Orb | Double-Edge, Earthquake, Rollout, Fresh Snack |
| 80 | Mr. Mime-G | 100 | 15 | SPE_UP | 132 | — | — | — | Fast | Screen Cleaner | Eviolite | Ice Beam, Encore, Substitute, Baton Pass |
| 81 | Tauros-P-Fire | 100 | 15 | SPE_UP | 132 | — | — | — | Fast | Intimidate | Life Orb | Close Combat, Flare Blitz, Wild Charge, Bulk Up |
| 82 | Tauros-P-Water | 100 | 15 | SPE_UP | 132 | — | — | — | Fast | Intimidate | Life Orb | Close Combat, Aqua Tail, Earthquake, Bulk Up |
| 83 | Tentacruel | 100 | 15 | SPE_UP | 132 | — | — | — | Fast | Clear Body | Life Orb | Waterfall, Poison Jab, Knock Off, Swords Dance |
| 84 | Typhlosion | 100 | 15 | SPE_UP | 132 | — | — | — | Fast | Flash Fire | Choice Specs | Flamethrower, Earth Power, Hidden Power(Grass), Focus Blast |
| 85 | Magnezone | 60 | 14 | SPE_UP | 86 | 129 | — | — | Scarf | Magnet Pull | Choice Scarf | Thunderbolt, Flash Cannon, Hidden Power(Fire), Thunder Wave |
| 86 | Gliscor | 95 | 15 | SPE_UP | 126 | — | — | — | Fast | Poison Heal | Toxic Orb | Earthquake, Facade, Knock Off, Swords Dance |
| 87 | Houndoom | 95 | 15 | SPE_UP | 126 | — | — | — | Fast | Flash Fire | Life Orb | Dark Pulse, Flamethrower, Sludge Bomb, Nasty Plot |
| 88 | Typhlosion-H | 95 | 15 | SPE_UP | 126 | — | — | — | Fast | Blaze | Life Orb | Flamethrower, Shadow Ball, Solar Beam, Sunny Day |
| 89 | Xatu | 95 | 15 | SPE_UP | 126 | — | — | — | Fast | Magic Bounce | Light Clay | U-turn, Reflect, Light Screen, Thunder Wave |
| 90 | Yanmega | 95 | 15 | SPE_UP | 126 | — | — | — | Fast | Tinted Lens | Choice Specs | Bug Buzz, Dragon Pulse, Giga Drain, Hidden Power(Ground) |
| 91 | Electivire | 105 | 15 | neutral | 125 | — | — | — | Fast | Motor Drive | Life Orb | Thunderbolt, Cross Chop, Flamethrower, Earthquake |
| 92 | Arcanine-H | 90 | 15 | SPE_UP | 121 | — | — | — | Fast | Intimidate | Choice Band | Flare Blitz, Wild Charge, Close Combat, Extremespeed |
| 93 | Ariados | 90 | 15 | SPE_UP | 121 | — | — | — | Fast | Swarm | Focus Sash | Megahorn, Poison Jab, Hone Claws, Glare |
| 94 | Golbat | 90 | 15 | SPE_UP | 121 | — | — | — | Fast | Infiltrator | Eviolite | Sludge Bomb, Air Slash, Roost, Nasty Plot |
| 95 | Kangaskhan | 90 | 15 | SPE_UP | 121 | — | — | — | Fast | Parental Bond | Assault Vest | Seismic Toss, Drain Punch, Ice Punch, Crunch |
| 96 | Venomoth | 90 | 15 | SPE_UP | 121 | — | — | — | Fast | Tinted Lens | Life Orb | Bug Buzz, Sludge Bomb, Roost, Sleep Powder |
| 97 | Tauros-P | 100 | 15 | neutral | 120 | — | — | — | Fast | Cud Chew | Sitrus Berry | Close Combat, Earthquake, Wild Charge, Iron Head |
| 98 | Raticate-A | 88 | 15 | SPE_UP | 118 | — | — | — | Fast | Hustle | Life Orb | Sucker Punch, Double-Edge, U-turn, Swords Dance |
| 99 | Hitmonlee | 87 | 15 | SPE_UP | 117 | — | — | — | Fast | Reckless | Life Orb | Mach Punch, Hi Jump Kick, Knock Off, Poison Jab |
| 100 | Articuno | 85 | 15 | SPE_UP | 115 | — | — | — | Fast | Competitive | Life Orb | Aeroblast, Shadow Ball, Recover, Calm Mind |
| 101 | Beedrill | 85 | 15 | SPE_UP | 115 | — | — | — | Fast | Adaptability | Choice Band | U-turn, Poison Jab, Knock Off, Toxic |
| 102 | Delibird | 85 | 15 | SPE_UP | 115 | — | — | — | Fast | Insomnia | Focus Sash | Icy Wind, Spikes, Destiny Bond, Toxic |
| 103 | Flareon | 95 | 15 | neutral | 115 | — | — | — | Fast | Drought | Life Orb | Flamethrower, Earth Power, Shadow Ball, Smokescreen |
| 104 | Nidoking | 85 | 15 | SPE_UP | 115 | — | — | — | Fast | Sheer Force | Life Orb | Sludge Bomb, Earth Power, Ice Beam, Flamethrower |
| 105 | Qwilfish-H | 85 | 15 | SPE_UP | 115 | — | — | — | Fast | Intimidate | Eviolite | Waterfall, Poison Jab, Destiny Bond, Thunder Wave |
| 106 | Stantler | 85 | 15 | SPE_UP | 115 | — | — | — | Fast | Intimidate | Life Orb | Return, Psychic, Shadow Ball, Hi Jump Kick |
| 107 | Yanma | 95 | 15 | neutral | 115 | — | — | — | Fast | Speed Boost | Focus Sash | Bug Buzz, Air Slash, Hidden Power(Ground), Protect |
| 108 | Glaceon | 95 | 14 | neutral | 114 | — | — | — | Fast | Snow Warning | Choice Specs | Blizzard, Shadow Ball, Earth Power, Hidden Power(Flying) |
| 109 | Magmar | 93 | 15 | neutral | 113 | — | — | — | Fast | Vital Spirit | Eviolite | Flare Blitz, Cross Chop, ThunderPunch, Will-O-Wisp |
| 110 | Magmortar | 93 | 15 | neutral | 113 | — | — | — | Fast | Vital Spirit | Choice Band | Flare Blitz, Cross Chop, Earthquake, ThunderPunch |
| 111 | Dudunsparce | 55 | 15 | neutral | 75 | — | 112 | — | Dragon Dance | Sand Stream | Life Orb | Outrage, Earthquake, Poison Jab, Dragon Dance |
| 112 | Murkrow | 91 | 15 | neutral | 111 | — | — | — | Fast | Prankster | Eviolite | Roost, Substitute, Mean Look, Perish Song |
| 113 | Mamoswine | 80 | 15 | SPE_UP | 110 | — | — | — | Fast | Thick Fat | Choice Band | Ice Shard, Icicle Crash, Earthquake, Knock Off |
| 114 | Gligar | 85 | 15 | neutral | 105 | — | — | — | Fast | Immunity | Eviolite | Earthquake, Knock Off, Roost, Toxic |
| 115 | Misdreavus | 85 | 15 | neutral | 105 | — | — | — | Fast | Levitate | Eviolite | Pain Split, Protect, Mean Look, Perish Song |
| 116 | Suicune | 85 | 15 | neutral | 105 | — | — | — | Fast | Water Absorb | Leftovers | Scald, Sleep Talk, Rest, Calm Mind |
| 117 | Arbok (Koga) | 80 | 15 | neutral | 100 | — | — | — | Fast | Intimidate | Black Sludge | Gunk Shot, Earthquake, Crunch, Glare |
| 118 | Meganium | 80 | 15 | neutral | 100 | — | — | — | Fast | Natural Cure | Big Root | Giga Drain, Protect, Leech Seed, Toxic |
| 119 | Cursola | 30 | 15 | neutral | 50 | 75 | — | — | Scarf | Weak Armor | Choice Scarf | Shadow Ball, Ice Beam, Surf, Earth Power |

---

## Trick Room Users
These mons either run `BTDVS_TRICK_ROOM` or explicitly carry `Trick Room`.

| Pokemon | Raw Spe | Nature | Ability | Item | Moves |
|---------|---------|--------|---------|------|-------|
| Slowbro-G | 31 | SPE_DOWN | Regenerator | Life Orb | Sludge Bomb, Psychic, Earthquake, Trick Room |
| Slowking | 31 | SPE_DOWN | Regenerator | Life Orb | Surf, Psychic, Flamethrower, Trick Room |
| Slowking-G | 31 | SPE_DOWN | Regenerator | Life Orb | Sludge Bomb, Psychic, Flamethrower, Trick Room |
| Steelix | 31 | SPE_DOWN | Sturdy | Leftovers | Gyro Ball, Earthquake, Stone Edge, Curse |
| Forretress | 40 | SPE_DOWN | Overcoat | Assault Vest | Gyro Ball, Earthquake, Volt Switch, Explosion |
| Exeggutor-A | 45 | SPE_DOWN | Harvest | Lum Berry | Giga Drain, Dragon Pulse, Rest, Trick Room |
| Exeggutor | 54 | SPE_DOWN | Harvest | Life Orb | Giga Drain, Psychic, Hidden Power, Trick Room |
| Perrserker | 58 | SPE_DOWN | Steely Spirit | Leftovers | Gyro Ball, Crunch, Seed Bomb, Curse |
| Porygon2 | 58 | SPE_DOWN | Download | Eviolite | Return, Shadow Ball, Recover, Trick Room |
| Porygon2 | 58 | SPE_DOWN | Download | Eviolite | Thunderbolt, Ice Beam, Recover, Trick Room |
| Ditto | 101 | SPE_DOWN | Imposter | Choice Scarf | Transform, No Move, No Move, No Move |

---

## Key Notes

- `Threat` reflects the fastest realistic speed mode from that exact BT set: raw, Choice Scarf, setup, or self-enabled weather ability.
- Weather ability boosts are included only when that same set can self-enable the weather with `Rain Dance`, `Sunny Day`, `Sandstorm`, or `Hail`.
- `+1 Speed` covers moves like `Dragon Dance` and `Quiver Dance`; `+2 Speed` covers `Agility`, `Rock Polish`, `Shell Smash`, and self-weather x2 ability lines.
- The detailed `Ability`, `Item`, and `Moves` columns show exactly what to watch out for on the fastest kept variant for each threat.

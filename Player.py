import random
import matplotlib.pyplot as plt
import numpy as np
import pickle
import pandas as pd
from IPython.display import display, clear_output, HTML
import re
import streamlit as st
from scipy.interpolate import PchipInterpolator
import altair as alt
import json, io

# Define available genetic markers.
# Arcanum (A) -- Nexus, Durabilis (D) -- Fortis Crags, Equilibrio (E) -- Percepio, Sapien (I) -- Celeste, Symbiosis (B) -- Synvios, Metamorphosis (M) -- Variare
MARKERS = ['A', 'D', 'E', 'I', 'B', 'M']

# ---- Base Abilities ----
BASE_ABILITIES = [
    "Portaling", "Strategy", "Fishing", "Technique", "Willpower",
    "Resilience", "Recovery", "Strength", "Smithing", "Intimidation",
    "Medicine", "Perception", "Diplomacy", "Construction", "Agility",
    "Navigation", "Foraging", "Tracking", "Persuasion", "Reflexes",
    "Brewing", "Taming", "Farming", "Hunting", "Trade",
    "Stealth", "Crafting", "Deception", "Thieving", "Speed"
]

# ---- Essence-Based Abilities ----
ESSENCE_ABILITIES = ['Arcanum', 'Symbiosis', 'Durabilis', 'Equilibrio', 'Sapien', 'Metamorphosis']

# ---- Gameplay Sliders ----
SLIDER_VALUES = [
    'Thinking Speed', # How quickly the player can process information (how much time is slowed down in decision making and combat)
    'Learning Rate', # How quickly the player can learn new skills or abilities
    'Inverse Metabolic Rate', # How often the player needs to eat, higher is less often
    'Inverse Sleep Cycle', # How often the player needs to sleep, higher is less often
    'Memory' # How quickly the player loses abilities if not used, higher is slower loss
]

ABILITY_CATEGORIES = { 
    "Essence-Based": ESSENCE_ABILITIES,
    "Physical": ["Strength", "Speed", "Agility", "Reflexes", "Resilience", "Recovery", "Technique"],
    "Mental": ["Willpower", "Perception", "Stealth", "Strategy"],
    "Social": ["Persuasion", "Diplomacy", "Deception", "Intimidation"],
    "Livelihood": ["Medicine", "Brewing", "Crafting", "Smithing", "Construction", "Foraging", "Farming", "Hunting", "Fishing", "Tracking", "Thieving", "Trade"],
    "Travel": ["Navigation", "Taming", "Portaling"]
}

# Define the skill progression data
SKILL_PROGRESSION = [
    {"Level": 0, "Title": "Unawakened", "Optimal Training Game Hours": 0, "XP Required": 0, "Active Real-Time Minutes (Optimal)": 0},
    {"Level": 1, "Title": "Novice", "Optimal Training Game Hours": 5, "XP Required": 500, "Active Real-Time Minutes (Optimal)": 5},
    {"Level": 2, "Title": "Novice", "Optimal Training Game Hours": 10, "XP Required": 1000, "Active Real-Time Minutes (Optimal)": 10},
    {"Level": 3, "Title": "Novice", "Optimal Training Game Hours": 25, "XP Required": 2500, "Active Real-Time Minutes (Optimal)": 25},
    {"Level": 4, "Title": "Intermediate", "Optimal Training Game Hours": 50, "XP Required": 5000, "Active Real-Time Minutes (Optimal)": 50},
    {"Level": 5, "Title": "Intermediate", "Optimal Training Game Hours": 125, "XP Required": 12500, "Active Real-Time Minutes (Optimal)": 125},
    {"Level": 6, "Title": "Advanced", "Optimal Training Game Hours": 250, "XP Required": 25000, "Active Real-Time Minutes (Optimal)": 250},
    {"Level": 7, "Title": "Advanced", "Optimal Training Game Hours": 500, "XP Required": 50000, "Active Real-Time Minutes (Optimal)": 500},
    {"Level": 8, "Title": "Expert", "Optimal Training Game Hours": 1250, "XP Required": 125000, "Active Real-Time Minutes (Optimal)": 1250},
    {"Level": 9, "Title": "Expert", "Optimal Training Game Hours": 2500, "XP Required": 250000, "Active Real-Time Minutes (Optimal)": 2500},
    {"Level": 10, "Title": "Master", "Optimal Training Game Hours": 5000, "XP Required": 500000, "Active Real-Time Minutes (Optimal)": 5000},
]

# 1.  MASTER TABLE
# ----------------------------------------------------------------
# For brevity floors & ceilings are all 0 / 1 now.  If you’d ever
# like a curve to *never* quite reach 0 or 1, re-insert f and C and
# the normalisation step will still work.
# ----------------------------------------------------------------
ABILITY_AGE_CURVES = {
    #  kind      centre/peak   width/steep
    # ---------- Physical ----------
    "Strength"     : ("bell",    35 , 35),
    "Speed"        : ("bell",    25 ,  25 ),
    "Agility"      : ("bell",    20 ,  30 ),
    "Reflexes"     : ("bell",    28 ,  30 ),
    "Resilience"   : ("bell",    25,   35),
    "Recovery"     : ("bell", 17,  25 ),
    "Technique"    : ("bell",   70 ,  35 ),

    # ---------- Mental ----------
    "Willpower"    : ("bell",   68 ,  40 ),
    "Perception"   : ("bell",   83 ,  35 ),
    "Strategy"     : ("bell",   119 ,  25 ),
    "Stealth"      : ("bell",    50 ,  30 ),

    # ---------- Social ----------
    "Persuasion"   : ("bell",    111 ,  40 ),
    "Diplomacy"    : ("bell",    118 ,  60 ),
    "Deception"    : ("bell",    63 ,  40 ),
    "Intimidation" : ("bell",    75 ,  60 ),

    # ---------- Livelihood ----------
    "Medicine"     : ("bell",   83 ,  43 ),
    "Brewing"      : ("bell",   78 ,  38 ),
    "Crafting"     : ("bell",   69 ,  34 ),
    "Smithing"     : ("bell",   59 ,  33 ),
    "Construction" : ("bell",   77 ,  37 ),
    "Foraging"     : ("bell",   87 ,  34 ),
    "Farming"      : ("bell",   81 ,  42 ),
    "Hunting"      : ("bell",    48 ,  36 ),
    "Fishing"      : ("bell",    93 ,  41 ),
    "Tracking"     : ("bell",    46 ,  28 ),
    "Thieving"     : ("bell",    28 ,  20 ),
    "Trade"        : ("bell",    86 ,  30 ),

    # ---------- Travel ----------
    "Navigation"   : ("bell",    77 ,  45 ),
    "Portaling"    : ("bell",    99 ,  40 ),
    "Taming"       : ("bell",    53 ,  35 ),

    # ---------- Essence ----------
    "Arcanum"      : ("bell", 110, 70),
    "Symbiosis"    : ("bell", 90, 60),
    "Durabilis"    : ("bell", 60, 50),
    "Equilibrio"   : ("bell", 110, 65),
    "Sapien"       : ("bell", 75, 55),
    "Metamorphosis": ("bell", 50, 45),
}

# ——— 1) Set up your control points ———

# Learning Rate: steep drop 0→21, gentle 21→120, then sharp to 0 at 145
_lr_ages  = np.array([  0,  21, 120, 145], dtype=float)
_lr_vals  = np.array([  1, 0.7, 0.3,   0], dtype=float)
_lr_interp = PchipInterpolator(_lr_ages, _lr_vals)

# Inverse Metabolic Rate: at age 0→0.5, down to 0 at 21, up to 1 at 145
_imr_ages  = np.array([  0,  21, 100, 145], dtype=float)
_imr_vals  = np.array([0.5,   0,  .6, 1], dtype=float)
_imr_interp = PchipInterpolator(_imr_ages, _imr_vals)

# Memory: 0→0.5 @0, →0.8 @17, →1 @45, →0.7 @120, →0 @145
_mem_ages  = np.array([  0,  17,  45, 120, 145], dtype=float)
_mem_vals  = np.array([0.5, 0.8, 1.0, 0.7,   0], dtype=float)
_mem_interp = PchipInterpolator(_mem_ages, _mem_vals)

# Create a DataFrame
SKILL_PROGRESSION_DF = pd.DataFrame(SKILL_PROGRESSION)

# Load the genetic modifiers from the file
with open('genetic_modifiers.pkl', 'rb') as f:
    GENETIC_MODIFIERS = pickle.load(f)

# ---- Trait Categories ----
# Physical Traits (Choose 1)
PHYSICAL_TRAITS = {
    "Survivalist": "Boosts Resilience and Willpower, a defensive grinder in combat and able to withstand to harsh conditions (e.g., extreme heat, cold, poison, sleep, hunger).",
    "Duelist": "Enhances Reflexes & Precision, excelling in one-on-one combat but with slightly lower brute force.",
    "Juggernaut": "Maximizes Raw Strength & Durability.",
    "Tactician": "Increases Combat Awareness & Strategic Movement, allowing for superior positioning in battle.",
    "Swiftfoot": "Enhances Speed & Agility, making the character excel in movement-based challenges.",
    "Sharpshooter": "Increases Technique & Perception, concentrated on ranged combat.",
    "Mystic Blade": "Increases Essence Manipulation & Arcane Knowledge, allowing for the use of magical abilities and enchanted items."
}

# Mental Traits (Choose 1)
MENTAL_TRAITS = {
    "Strategist": "Boosts Intelligence & Perception, giving an edge in analyzing situations and planning ahead.",
    "Manipulator": "Enhances Psychological Insight & Mental Tactics, allowing for deception and persuasion to be more effective.",
    "Inventor": "Improves creativity & engineering, excelling in problem-solving through crafting or mechanical expertise.",
    "Realmwise": "Gains superior language acquisition and deep cultural literacy, enabling mastery of foreign tongues, traditions, and diplomatic customs.",
    "Observer": "Heightens Perception & Intuition, making it easier to notice small details and patterns others miss."
}

# Social Traits (Choose 1)
SOCIAL_TRAITS = {
    "Diplomat": "Increases Persuasion & Negotiation, making it easier to influence others and resolve conflicts peacefully.",
    "Lone Wolf": "Improves Independence & Self-Reliance, reducing reliance on allies but making teamwork less effective.",
    "Charlatan": "Enhances Deception & Trickery, excelling in misleading others and maintaining disguises."
}

# Livelihood Traits (Choose 1)
LIVELIHOOD_TRAITS = {
    "Mercantile": "Enhances Commerce & Wealth Accumulation, making business ventures and trade routes more profitable.",
    "Black Market Broker": "Enhances Underworld Trade & Smuggling, excelling in illicit dealings and secret networks.",
    "Artisan": "Boosts production & material Mastery, excelling in Smithing, Crafting, and Construction.",
    "Harvester": "Specializes in Farming, Fishing & Herbalism, excelling in sustainable food and medicinal production.",
    "Shadowbound": "Improves Hunting, scouting, and resource discovery through superior environmental awareness.", 
    "Medic": "Enhances healing & Medical Knowledge, excelling in treating injuries and diseases.",
    "Brewer": "Skilled at alchemical concoctions and herbal remedies, excelling in potion-making and restorative brews.",
    "Thief": "Improves Stealth & Thievery, excelling in infiltration and larceny.",
    #"Jack-of-All-Master-of-None": "Provides balanced improvements across livelihood domains.", would be all above and 1/12 on abilities, memory boost too perhaps
    "Warrior (Survivalist)": "Boosts Resilience and Willpower, a defensive grinder in combat and able to withstand to harsh conditions (e.g., extreme heat, cold, poison, sleep, hunger).",
    "Warrior (Duelist)": "Enhances Reflexes & Precision, excelling in one-on-one combat but with slightly lower brute force.",
    "Warrior (Juggernaut)": "Maximizes Raw Strength & Durability.",
    "Warrior (Tactician)": "Increases Combat Awareness & Strategic Movement, allowing for superior positioning in battle.",
    "Warrior (Swiftfoot)": "Enhances Speed & Agility, making the character excel in movement-based challenges.",
    "Warrior (Sharpshooter)": "Increases Technique & Perception, concentrated on ranged combat.",
    "Warrior (Mystic Blade)": "Increases Essence Manipulation & Arcane Knowledge, allowing for the use of magical abilities and enchanted items."
}
# Travel Traits (Choose 1)
TRAVEL_TRAITS = {
    "Wayfinder": "Boosts Navigation & Route Planning, makes long-distance travel and exploration safer and more efficient.",
    "Beast Rider": "Enhances travel using mounts, improving Taming and endurance for long journeys. Unlocks mastery of rare and powerful creatures.",
    "Gatewalker": "Improves Portaling, taking less time to form and energy to form, while allowing for larger transport loads, reduces disorientation and improves range."
}
# Essence-Based Traits (Choose 4)
ESSENCE_TRAITS = {
    "E": {  # Equilibrio (Balance, Perception, Harmony, Awareness)
        "Seer's Insight": "Heightens intuition & foresight, improving the ability to anticipate threats and sense disturbances.",
        "Flowstate Mastery": "Enables the user to enter a heightened state of focus and precision, where movement, thought, and task become seamlessly synchronized.",
        "Homeostatic Healing [Requires: Medic]": "Enhances natural healing & recovery, stabilizing vital functions and reducing the impact of injuries."
    },
    "D": {  # Durabilis (Resilience, Fortitude, Endurance, Strength)
        "Ironclad Will": "Maximizes physical & mental endurance, making it harder to be exhausted or intimidated.",
        "Phoenix's Flight": "Improves natural healing & regeneration, increasing recovery speed and longevity.",
        "Pangolin's Plaitmancer [Requires: Artisan]": "A master smith who has learned to become one with armor, gaining increased protection and mobility."
    },
    "A": {  # Arcanum (Magic, Portals, Cosmic Understanding, Mysticism)
        "Portalmaster [Requires: Gatewalker]": "Greatly expands Portaling capabilities.",
        "Runic Aegis": "Able to build essence-based armor and defend against essence attacks.",
        "Bladebound Runes": "Able to build essence-based weapons and work with Arcanum Crystals and Celestial Bindstones."
    },
    "B": {  # Symbiosis (Nature, Adaptation, Connection, Growth)
        "Beastkin": "Enhances affinity with animals & wildlife for deeper communication and control.",
        "Vitalist": "Strengthens life-force energy, promoting rapid plant growth, sustainable harvesting, and biological reinforcement.",
        "Brewmaster [Requires: Brewer]": "Mastery over organic alchemy and natural fermentation, excelling in medicinal, restorative, and transformational brews."
    },
    "M": {  # Metamorphosis (Change, Evolution, Transformation, Fluidity)
        "Chimera's Gift": "Allows for temporary biological modifications such as enhanced speed or durability.",
        "Essence Weaver": "Improves internal transfer of different essence types, enabling masterful hybridization and creative energy use.", # Uses both arcanum and metamorphosis
        "Folkwise": "Grants instinctive cultural adaptation, allowing seamless integration into new societies through subtle shifts in speech, mannerisms, and demeanor."
    },
    "I": {  # Sapien (Knowledge, Intelligence, Rationality, Learning)
        "Memory Palace": "Enhances memory retention & recall, allowing for vast knowledge storage and rapid information retrieval.",
        "Prodigal Polymath": "Accelerates learning new abilities and knowledge, reducing time to master complex subjects.",
        "Quickened Mind": "Allows accelerated processing of information for rapid deduction and decision-making under pressure."
    }
}

TRAIT_MODIFIERS = {
    # Physicality Traits (Choose 1)
    "Survivalist": {
        "Abilities": {
            "Resilience": 0.4,   # Enduring harsh conditions
            "Recovery":   0.35,  # Elevated to emphasize physical recuperation
            "Willpower":  0.25   # Slightly lower effect
        },
        "Sliders": {
            "Inverse Metabolic Rate": 0.5,  # Slight improvement: less food needed
            "Inverse Sleep Cycle":   0.5,  # Slight improvement: less sleep required
        },
        "Skillsets": {
            "Adrenaline Surge": "Triggers when cornered or low in health, boosting combat prowess temporarily.",
            "Wilderness Fortitude": "Mitigates environmental and other sustained damage while increasing skills outside of combat when affected by sustained damage (e.g., improved alchemy when poisoned, improved resource gathering when hungry, reduced physical deficits when fatigued).",
            "Brace": "A strong defensive posture or block reducing incoming damage.",
            "Survivalist's Bond": "Able to channel Essence with Ambrosia Sap weaponry and armor (excluding bows)."
        }
    },
    "Duelist": {
        "Abilities": {
            "Reflexes":  0.50,
            "Strength": 0.05,
            "Resilience": 0.05,
            "Technique": 0.30,
            "Agility":   0.05,
            "Willpower": 0.05,
        },
        "Sliders": {
            "Thinking Speed":        0.10,  # Boosted for quick decision-making
            "Inverse Sleep Cycle":   -0.10,  # Tradeoff: more sleep needed to keep reflexes sharp
        },
        "Skillsets": {
            "Precision Parry": "Allows a perfectly timed block or deflection, leaving the attacker momentarily vulnerable to a powerful counterattack.",    
            "Flash Stab": "Executes an extremely quick, precise attack designed to bypass enemy defenses or interrupt enemy actions.",
            "Riposte": "Responds to an enemy attack with a quick counterstrike, exploiting the opening created by the opponent's move.",
            "Duelist's Perception": "Able to channel Essence with Libranium weaponry and armor (excluding bows)."
        }
    },
    "Juggernaut": {
        "Abilities": {
            "Strength": 0.70,
            "Resilience": 0.20,
            "Willpower": 0.10
        },
        "Sliders": {},
        "Skillsets": {
            "Unstoppable Charge": "Rush forward with immense force, knocking enemies aside, breaking defensive stances, and clearing a direct path through obstacles or foes.",
            "Ironhide": "Briefly hardens your physical form, drastically reducing incoming damage and preventing knockback or disruption, allowing you to endure even powerful enemy assaults head-on.",
            "Crushing Blow": "Delivers a massive strike capable of shattering armor and defensive buffs, dealing heavy damage and significantly reducing enemy resistances.",
            "Juggernaut's Might": "Able to channel Essence with Durabilis weaponry and armor."
        }
    },
    "Tactician": {
        "Abilities": {
            "Technique":  0.50,
            "Perception": 0.05,
            "Strategy":   0.20,
            "Reflexes":   0.15,
            "Willpower":  0.05,
            "Resilience": 0.05,
        },
        "Sliders": {
            "Inverse Metabolic Rate": -.01,
            "Inverse Sleep Cycle":   -.01,
            "Memory":                .02
        },
        "Skillsets": {
            "Strategic Insight": "Analyzes the battlefield and enemy movements, allowing for precise positioning and tactical advantage.",
            "Combat Momentum": "A fluid sequence of rapid hits and parries builds momentum, temporarily increasing attack abilities as the combo progresses.",
            "Feint": "Executes a deceptive move to mislead the enemy, creating an opening for a powerful follow-up attack.",
            "Tactician's Insight": "Able to channel Essence with Celestial Bindstones weaponry and armor."
        }
    },
    "Swiftfoot": {
        "Abilities": {
            "Speed":   0.50,
            "Agility": 0.45,
            "Reflexes": 0.05,
        },
        "Sliders": {
            "Thinking Speed":        0.01,
            "Inverse Metabolic Rate": -0.01
        },
        "Skillsets": {
            "Blinding Speed": "Temporarily accelerates movement and attack speed, allowing for rapid strikes and quick escapes.",
            "Acrobatic": "Executes complex maneuvers and dodges, allowing for evasion of even the most precise attacks.",
            "Swift Slash": "Delivers a smooth slash attack, combining speed and precision to strike vulnerable points and bypass defenses.",
            "Swiftfoot's Agility": "Able to channel Essence with Kinestal weaponry and armor."
        }
    },
    "Sharpshooter": {
        "Abilities": {
            "Technique": 0.40,
            "Perception": 0.30,
            "Strength": 0.10,
            "Reflexes":  0.10,
            "Stealth":   0.10,
        },
        "Sliders": {
            "Thinking Speed":        0.02,
            "Inverse Sleep Cycle": -0.02,
        },
        "Skillsets": {
            "Deadeye Mark": "Executes a high-precision shot that targets a vulnerable point even in motion, increasing critical hit chance and granting bonus damage against moving or evasive enemies.",
            "Armor-Split Shot": "Fires a heavy, penetrating shot designed to pierce armor and cover, temporarily reducing the target's physical resistance and exposing them to follow-up attacks.",
            "Rain of Arrows": "Allows for either rapid consecutive shots at a single target (speed shooting) or a sweeping arc of arrows across multiple foes. Especially effective for crowd control and maintaining offensive pressure.",
            "Sharpshooter's Focus": "Able to channel Essence with Essence-infused ranged weapons (e.g., Ambrosia Tree bows and arrows, Libranium cross-bows, Durabilis bolts and arrows tips, Kinestal impulse fanblade, Libranium harmonized chakram if combined with Primordial Instinct)."
        }
    },
    "Mystic Blade": {
        "Abilities": {
            "Arcanum": 0.70,
            "Technique": 0.30
        },
        "Sliders": {},
        "Skillsets": {
            "Infuse Essence": "Able to flow essence into entities.",
            "Siphon Essence": "Able to flow essence out of entities.",
            "Aetheric Grasp": "Able to detect essence or grab such that you can then apply crystallize, amorphize, or transmute--note: this is not necessary for siphon which just pulls without knowing if something is there--grasp can however strengthen siphon at a later skill level.",
            "Mystic Blade's Arcana": "Able to channel Essence with Arcanum Crystals weaponry and armor.",
        }
    },

    # Mentality Traits (Choose 1)
    "Strategist": {
        "Abilities": {
            "Strategy":  0.50,
            "Perception": 0.30,
            "Willpower": 0.20
        },
        "Sliders": {
            "Thinking Speed":        0.05,
            "Inverse Metabolic Rate": -0.05,
            "Inverse Sleep Cycle":   -0.05,
            "Memory":                0.05
        },
        "Skillsets": {
            "Master Planner": "Develops intricate strategies and plans, maximizing efficiency and success in various endeavors.",
            "Commander's Presence": "Inspires allies to fight harder and more effectively, boosting their combat prowess and morale.",
            "Analytical Mind": "Breaks down complex problems and situations, identifying key elements and potential solutions."
        }
    },
    "Manipulator": {
        "Abilities": {
            "Persuasion": 0.40,
            "Deception":  0.40,
            "Diplomacy":  0.10,
            "Perception": 0.10
        },
        "Sliders": {
            "Thinking Speed":        0.03,
            "Inverse Metabolic Rate": -0.02,
            "Inverse Sleep Cycle":   -0.01
        },
        "Skillsets": {
            "Master of Deception": "Creates false impressions, allowing for effective misdirection and disguise.",
            "Psychological Insight": "Reads and manipulates the emotions and thoughts of others, better understanding how to influence their behavior and decisions.",
            "Mind Games": "Plays psychological games with opponents, exploiting their fears and desires to gain an advantage."
        }
    },
    "Inventor": {
        "Abilities": {
            "Crafting":     0.35,
            "Smithing":     0.30,
            "Construction": 0.35
        },
        "Sliders": {},
        "Skillsets": {
            "Creative Genius": "Invents new devices, tools, and solutions to problems, using a combination of knowledge and imagination.",
            "Mechanical Mastery": "Understands the inner workings of machines and devices, allowing for efficient repairs and modifications.",
            "Large-Scale Engineering": "Designs and constructs large-scale projects, from defensive fortresses to massive sea vessles.",
        }
    },
    "Realmwise": {
        "Abilities": {
            "Diplomacy": 0.40,
            "Persuasion": 0.20,
            "Stealth":    0.40
        },
        "Sliders": {
            "Inverse Metabolic Rate": -0.05,
            "Inverse Sleep Cycle":   -0.05,
            "Memory":                0.10
        },
        "Skillsets": {
            "Polyglot": "Enhances knowledge of languages and dialects, allowing for effective communication with a wide range of cultures and peoples.",
            "Cultural Literacy": "Understands the customs, traditions, and social norms of different societies, enabling smooth interactions and negotiations.",
            "Lorekeeper": "Has deep historical knowledge of various regions, factions, and significant events, enabling strategic use of information in social interactions and quests."
        }
    },
    "Observer": {
        "Abilities": {
            "Perception": 1.0
        },
        "Sliders": {
            "Thinking Speed":        0.05,
            "Learning Rate":         0.02,
            "Inverse Metabolic Rate": -0.05,
            "Inverse Sleep Cycle":   -0.02
        },
        "Skillsets": {
            "Mind's Eye": "Environmental observation—heightened perception of surroundings, structures, terrain, potential hazards, and hidden resources, improving exploration, detection, and situational awareness.",
            "Intuitive Awareness": "Social observation—keen sensitivity to subtle changes in body language, expressions, and demeanor, allowing early detection of deception, aggression, or hidden intentions.",
            "Pattern Recognition": "Quickly identifies and leverages recurring clues, puzzle mechanics, architectural layouts, and behavioral patterns, explicitly reducing the time and effort needed to solve mysteries, decipher puzzles, and navigate complex environments."
        }
    },

    # Social Traits (Choose 1)
    "Diplomat": {
        "Abilities": {
            "Persuasion": 0.30,
            "Diplomacy":  0.70
        },
        "Sliders": {},
        "Skillsets": {
            "Negotiation": "Resolves conflicts and disputes through dialogue and compromise, finding mutually beneficial solutions.",
            "Friends in High Places": "Cultivates relationships with influential figures and factions, gaining access to valuable resources, information, and support.",
            "Charisma": "Inspires trust and confidence in others, making it easier to influence and persuade them."
        }
    },
    "Lone Wolf": {
        "Abilities": {
            "Stealth":      0.35,
            "Intimidation": 0.25,
            "Willpower":    0.40
        },
        "Sliders": {},
        "Skillsets": {
            "Menacing Presence": "Projects an aura of threat and confidence, dramatically increasing the effectiveness of intimidation tactics and reducing the likelihood of enemy aggression or challenge.",
            "Solitary Focus": "When alone, gains improved mental clarity, heightened senses, and faster skill progression, making solitary exploration and investigation more effective.",
            "Shadow Operative": "Significantly improves stealth capabilities, increasing movement silence, reducing detection radius, and granting bonuses to infiltration, sabotage, and covert missions as well as hunting and scouting."
        }
    },
    "Charlatan": {
        "Abilities": {
            "Deception":  0.70,
            "Persuasion": 0.30
        },
        "Sliders": {},
        "Skillsets": {
            "Master of Disguise": "Assumes different identities and personas with ease, blending seamlessly into various social circles and environments.",
            "Con Artist": "Deceives others through elaborate schemes and manipulative tactics, exploiting their weaknesses and desires for personal gain.",
            "Counterfeit Expertise": "Skilled at crafting convincing forgeries and fake documents, as well as appraising and identifying fake or altered items and goods."
        }
    },

    # Livelihood Traits (Choose 1)
    "Mercantile": {
        "Abilities": {
            "Trade":     1.0
        },
        "Sliders": {},
        "Skillsets": {
            "Haggler's Instinct": "Naturally secures better prices in trade and negotiations, reducing buying costs and increasing selling profits when bartering with merchants and traders.",
            "Market Opportunist": "Identifies lucrative trade routes, trends, and shortages, allowing for strategic buying, selling, and investment before market fluctuations occur.",
            "Appraisal Expert": "Quickly and accurately determines the true value of items, spotting hidden flaws or rare qualities that others might overlook."
        }
    },
    "Black Market Broker": {
        "Abilities": {
            "Trade":    0.40,
            "Thieving": 0.30,
            "Stealth":  0.30,
        },
        "Sliders": {},
        "Skillsets": {
            "Underworld Connections": "Cultivates relationships with a network of informants, smugglers, and criminals, providing valuable information, contraband, and illicit services.",
            "Display of Power": "Projects an aura of authority and danger, deterring potential threats and encouraging cooperation from less reputable individuals.",
            "Shadow Broker": "Specializes in discreet transactions and secret dealings, maintaining anonymity and security in all black market operations."
        }
    },
    "Artisan": {
        "Abilities": {
            "Smithing":     0.33,
            "Crafting":     0.34,
            "Construction": 0.33
        },
        "Sliders": {},
        "Skillsets": {
            "Basic Metalworking": "Ability to smith with basic metals.",
            "Basic Woodworking": "Ability to craft with basic woods.",
            "Weaponcraft": "Ability to build weapons.",
            "Armorcraft": "Ability to build armor.",
            "Structural Engineering": "Ability to design and construct buildings and other structures.",
            "Precision Designing": "Enables fine-detail work, allowing for the integration of complex engravings, moving parts, and enhancements in built items, unlocking properties and unique synergies.",
            "Textile & Leatherworking": "Ability to craft with flexible materials such as cloth, leather, and hide, allowing for the creation of garments, light armor, tents, and specialized gear."
        }
    },
    "Harvester": {
        "Abilities": {
            "Farming":  0.35,
            "Fishing":  0.35,
            "Foraging": 0.30
        },
        "Sliders": {},
        "Skillsets": {
            "Green Thumb": "Enhances plant growth and health, increasing crop yields and medicinal potency.",
            "Fisherman's Luck": "Improves fishing success and efficiency, increasing the likelihood of catching rare or valuable fish.",
            "Nature's Bounty": "Identifies and harvests food and valuable resources from the environment, including rare herbs, minerals, and other natural treasures."
        }
    },
    "Shadowbound": {
        "Abilities": {
            "Hunting":  0.40,
            "Tracking": 0.40,
            "Foraging": 0.20
        },
        "Sliders": {},
        "Skillsets": {
            "Small Game Hunter": "Tracks and hunts small creatures.",
            "Big Game Hunter": "Tracks and hunts large creatures.",
            "Scavenger": "Finds and collects useful items and resources from the environment, including hidden caches, discarded goods, and overlooked valuables.",
            "Shadow Operative": "Significantly improves stealth capabilities, increasing movement silence, reducing detection radius, and granting bonuses to infiltration, sabotage, and covert missions as well as hunting and scouting."
        }
    },
    "Medic": {
        "Abilities": {
            "Medicine": 1.00
        },
        "Sliders": {
            "Thinking Speed":        0.02,
            "Inverse Metabolic Rate": -0.06,
            "Inverse Sleep Cycle":   -0.06,
            "Memory":                0.1
        },
        "Skillsets": {
            "Field Medic": "Provides emergency medical care and first aid, stabilizing injuries and preventing further harm.",
            "Long-Term Care": "Provides recovery support, accelerating healing and reducing the impact of injuries.",
            "Medical Knowledge": "Enhances understanding of anatomy, physiology, and medical treatments, improving diagnosis and treatment of diseases and injuries."
        }
    },
    "Thief": {
        "Abilities": {
            "Thieving": .70,
            "Stealth":  .30
        },
        "Sliders": {},
        "Skillsets": {
            "Pickpocket": "Expertly lifts items from unsuspecting targets, increasing success rate and reducing the chance of detection when stealing valuables.",
            "Lockpicking": "Effortlessly bypasses locks, safes, and secured containers, increasing success rate and speed when attempting break-ins.",
            "Shadow Operative": "Significantly improves stealth capabilities, increasing movement silence, reducing detection radius, and granting bonuses to infiltration, sabotage, and covert missions as well as hunting and scouting."
        }
    },
    "Brewer": {
        "Abilities": {
            "Brewing": 1.00
        },
        "Sliders": {},
        "Skillsets": {
            "Medicinal Brewing": "Creates potions and tonics that heal wounds, cure ailments, enhance recovery, and bolster the body's resistance to disease and poisons.",
            "Mental Enhancement Brewing": "Crafts brews that temporarily boost mental clarity, providing strategic advantages in combat or skill-based tasks.",
            "Physical Enhancement Brewing": "Crafts brews that temporarily boost physical capabilities, providing strategic advantages in combat or skill-based tasks."
        }
    },
    "Warrior (Survivalist)": {
        "Abilities": {
            "Resilience": 0.4,   # Enduring harsh conditions
            "Recovery":   0.35,  # Elevated to emphasize physical recuperation
            "Willpower":  0.25   # Slightly lower effect
        },
        "Sliders": {
            "Inverse Metabolic Rate": 0.5,  # Slight improvement: less food needed
            "Inverse Sleep Cycle":   0.5,  # Slight improvement: less sleep required
        },
        "Skillsets": {
            "Adrenaline Surge": "Triggers when cornered or low in health, boosting combat prowess temporarily.",
            "Wilderness Fortitude": "Mitigates environmental and other sustained damage while increasing skills outside of combat when affected by sustained damage (e.g., improved alchemy when poisoned, improved resource gathering when hungry, reduced physical deficits when fatigued).",
            "Brace": "A strong defensive posture or block reducing incoming damage.",
            "Survivalist's Bond": "Able to wield Ambrosia Sap weaponry and armor."
        }
    },
    "Warrior (Duelist)": {
        "Abilities": {
            "Reflexes":  0.50,
            "Strength": 0.05,
            "Resilience": 0.05,
            "Technique": 0.30,
            "Agility":   0.05,
            "Willpower": 0.05,
        },
        "Sliders": {
            "Thinking Speed":        0.10,  # Boosted for quick decision-making
            "Inverse Sleep Cycle":   -0.10,  # Tradeoff: more sleep needed to keep reflexes sharp
        },
        "Skillsets": {
            "Precision Parry": "Allows a perfectly timed block or deflection, leaving the attacker momentarily vulnerable to a powerful counterattack.",    
            "Flash Stab": "Executes an extremely quick, precise attack designed to bypass enemy defenses or interrupt enemy actions.",
            "Riposte": "Responds to an enemy attack with a quick counterstrike, exploiting the opening created by the opponent's move.",
            "Duelist's Perception": "Able to wield Libranium weaponry and armor."
        }
    },
    "Warrior (Juggernaut)": {
        "Abilities": {
            "Strength": 0.70,
            "Resilience": 0.20,
            "Willpower": 0.10
        },
        "Sliders": {},
        "Skillsets": {
            "Unstoppable Charge": "Rush forward with immense force, knocking enemies aside, breaking defensive stances, and clearing a direct path through obstacles or foes.",
            "Ironhide": "Briefly hardens your physical form, drastically reducing incoming damage and preventing knockback or disruption, allowing you to endure even powerful enemy assaults head-on.",
            "Crushing Blow": "Delivers a massive strike capable of shattering armor and defensive buffs, dealing heavy damage and significantly reducing enemy resistances.",
            "Juggernaut's Might": "Able to wield Durabilis weaponry and armor."
        }
    },
    "Warrior (Tactician)": {
        "Abilities": {
            "Technique":  0.50,
            "Perception": 0.05,
            "Strategy":   0.20,
            "Reflexes":   0.15,
            "Willpower":  0.05,
            "Resilience": 0.05,
        },
        "Sliders": {
            "Inverse Metabolic Rate": -.01,
            "Inverse Sleep Cycle":   -.01,
            "Memory":                .02
        },
        "Skillsets": {
            "Strategic Insight": "Analyzes the battlefield and enemy movements, allowing for precise positioning and tactical advantage.",
            "Combat Momentum": "A fluid sequence of rapid hits and parries builds momentum, temporarily increasing attack abilities as the combo progresses.",
            "Feint": "Executes a deceptive move to mislead the enemy, creating an opening for a powerful follow-up attack.",
            "Tactician's Insight": "Able to wield Celestial Bindstones weaponry and armor."
        }
    },
    "Warrior (Swiftfoot)": {
        "Abilities": {
            "Speed":   0.50,
            "Agility": 0.45,
            "Reflexes": 0.05,
        },
        "Sliders": {
            "Thinking Speed":        0.01,
            "Inverse Metabolic Rate": -0.01
        },
        "Skillsets": {
            "Blinding Speed": "Temporarily accelerates movement and attack speed, allowing for rapid strikes and quick escapes.",
            "Acrobatic": "Executes complex maneuvers and dodges, allowing for evasion of even the most precise attacks.",
            "Swift Slash": "Delivers a smooth slash attack, combining speed and precision to strike vulnerable points and bypass defenses.",
            "Swiftfoot's Agility": "Able to wield Kinestal weaponry and armor."
        }
    },
    "Warrior (Sharpshooter)": {
        "Abilities": {
            "Technique": 0.40,
            "Perception": 0.30,
            "Strength": 0.10,
            "Reflexes":  0.10,
            "Stealth":   0.10,
        },
        "Sliders": {
            "Thinking Speed":        0.02,
            "Inverse Sleep Cycle": -0.02,
        },
        "Skillsets": {
            "Deadeye Mark": "Executes a high-precision shot that targets a vulnerable point even in motion, increasing critical hit chance and granting bonus damage against moving or evasive enemies.",
            "Armor-Split Shot": "Fires a heavy, penetrating shot designed to pierce armor and cover, temporarily reducing the target's physical resistance and exposing them to follow-up attacks.",
            "Rain of Arrows": "Allows for either rapid consecutive shots at a single target (speed shooting) or a sweeping arc of arrows across multiple foes. Especially effective for crowd control and maintaining offensive pressure.",
            "Sharpshooter's Focus": "Able to channel Essence with Essence-infused ranged weapons (e.g., Ambrosia Tree bows and arrows, Libranium cross-bows, Durabilis bolts and arrows tips, Kinestal impulse fanblade, Libranium harmonized chakram if combined with Primordial Instinct)."
        }
    },
    "Warrior (Mystic Blade)": {
        "Abilities": {
            "Arcanum": 0.70,
            "Technique": 0.30
        },
        "Sliders": {},
        "Skillsets": {
            "Infuse Essence": "Able to flow essence into entities.",
            "Siphon Essence": "Able to flow essence out of entities.",
            "Aetheric Grasp": "Able to detect essence or grab such that you can then apply crystallize, amorphize, or transmute--note: this is not necessary for siphon which just pulls without knowing if something is there--grasp can however strengthen siphon at a later skill level.",
            "Mystic Blade's Arcana": "Able to wield Arcanum Crystals weaponry and armor.",
        }
    },

    # Travel Traits (Choose 1)
    "Wayfinder": {
        "Abilities": {
            "Navigation": 1.00
        },
        "Sliders": {},
        "Skillsets": {
            "Celestial Clues": "Uses the positions of stars, moons, and other celestial markers to determine direction, time, and optimal routes, even in unfamiliar lands.",
            "Seafaring": "Ocean, river, and sea navigation and captaining capabilities, reading currents, tides, and wind patterns to optimize maritime travel and avoid dangers.",
            "Pathfinder's Instinct": "A keen sense of direction in unexplored terrain, allowing the identification of natural paths, hidden routes, and safe passages in unfamiliar landscapes."
        }
    },
    "Beast Rider": {
        "Abilities": {
            "Taming":    1.00
        },
        "Sliders": {},
        "Skillsets": {
            "Flowing Stride": "Maintains precise control while riding, improving speed, maneuverability, and stability during difficult terrain, high-speed chases, or combat.",
            "Endurance Synergy": "Enhances stamina and resilience for both rider and mount, allowing for longer travel, faster recovery, and resistance to harsh environmental conditions.",
            "Saddleborn": "Allows the bonding and taming of rare and powerful mounts, deepening trust and improving control over even the most untamable creatures."
        }
    },
    "Gatewalker": {
        "Abilities": {
            "Portaling": 1.00
        },
        "Sliders": {},
        "Skillsets": {
            "Waypoint Expansion": "Increases the Range of portals, allowing for longer-distance travel.",
            "Tethered Entanglement": "Enhances the Capacity of portals, enabling the transport of larger and more complex loads (e.g., objects, animals, multiple people).",
            "Aetherstreaming": "Reduces the Efficiency (i.e., Time and Essence) required to form portals, making travel faster and more efficient."
        }
    },

    # Essence-Based Traits (Choose 4)

    # Equilibrio (E)
    "Seer's Insight": {
        "Abilities": {
            "Equilibrio": 0.7,   # Enhances overall balance and intuition
            "Perception": 0.3    # Improves threat anticipation and disturbance sensing
        },
        "Sliders": {
            "Thinking Speed":        0.05,
            "Inverse Sleep Cycle":   -0.05,
        },
        "Skillsets": {
            "Radiant Equilibrium": "Able to adjust vision to different light conditions, including low-light and bright-light environments, enhancing visual perception in various situations.",
            "Echowise": "Includes both the sensitivity to detect subtle sounds and the capability to isolate and focus on specific noises when needed.",
            "Palate Perception": "Includes both the sensitivity to detect subtle tastes and the capability to isolate and focus on specific flavors when needed.",
            "Haptic Sensitivity": "Includes both the sensitivity to detect subtle vibrations and the capability to isolate and focus on specific textures when needed.",
            "Primordial Instict": "Ability to detect the presence of essence, including the ability to identify the type of essence and its source."
        }
    },
    
    "Flowstate Mastery": {
        "Abilities": {
            "Equilibrio": 0.5,  # Boosts focus and synchrony
            "Reflexes":   0.1,   # Enhances precision in movement
            "Speed":      0.1,  # Provides temporary physical enhancements
            "Strength":   0.1,    # Provides temporary physical enhancements
            "Agility":    0.1,    # Improves movement and coordination
            "Technique":  0.1,    # Enhances skill execution
        },
        "Sliders": {},
        "Skillsets": {
            "Flowstate Mastery": "Increases the ability to enter a flow state after repeated successful skill actions, where the character can perform tasks with heightened focus and precision.",
            "Effortless Repetition": "Tasks that require repetition (crafting, training, refining) become smoother, reducing fatigue buildup and increasing efficiency over extended periods."
        }
    },
    "Homeostatic Healing [Requires: Medic]": {
        "Abilities": {
            "Equilibrio": 0.5,   # Baseline balance for stable vital functions
            "Medicine":   0.3,   # Advanced healing and recovery techniques
            "Recovery":   0.2    # Strong healing and injury mitigation
        },
        "Sliders": {},
        "Skillsets": {
            "Equilibrium Surge": "Channels Equilibrio essence to instantly stabilize wounds and restore health, allowing continued combat despite injuries.",
            "Vital Flow Cleansing": "Uses Equilibrio essence to purge bodily toxins, stabilize the mind, and mitigate the effects of poison, disease, and essence imbalance.",
            "Resonant Rejuvenation": "Aligns the body's natural healing rhythms with Equilibrio essence, accelerating long-term recovery from severe injuries, chronic conditions, and lingering ailments."
        }
    },
    
    # Durabilis (D)
    "Ironclad Will": {
        "Abilities": {
            "Durabilis": 0.6,    # Maximizes endurance
            "Willpower": 0.4     # Bolsters mental fortitude
        },
        "Sliders": {},
        "Skillsets": {
            "Unbreakable Will": "Resists mental attacks and manipulation, maintaining focus and determination in the face of psychological threats.",
            "Pain is Power": "When damaged, the next attack is fueled with more strength and power.",
            "Stalwart Focus": "Maintains unwavering focus during complex tasks, combat, or high-pressure situations, making it harder to be distracted or mentally disrupted."
        }
    },
    "Phoenix's Flight": {
        "Abilities": {
            "Durabilis": 0.6,    # Represents physical endurance
            "Recovery":  0.4     # Enhances natural regeneration
        },
        "Sliders": {},
        "Skillsets": {
            "Vital Forge": "Channels Durabilis essence to accelerate natural regeneration, allowing rapid recovery from wounds and physical damage over time.",
            "Nectar of the Gods": "Enables the consumption of Ambrosia Sap Tea to enhance regeneration, curing ailments and restoring vitality beyond normal limits.",
            "Enduring Embers": "When critically wounded, fatigued, or malnourished, the user's Durabilis essence sustains them, preventing immediate incapacitation and allowing continued action until full collapse."
        }
    },
    "Pangolin's Plaitmancer [Requires: Artisan]": {
        "Abilities": {
            "Durabilis": 0.5,    # Fundamental resilience
            "Smithing":  0.5     # Masterful integration with armor and protection
        },
        "Sliders": {},
        "Skillsets": {
            "Durabilis Metalworking": "Ability to smith with the Durabilis metal.",
            "Kinestal Metalworking": "Ability to smith with the Kinestal metal.",
            "Libranium Metalworking": "Ability to smith with the Libranium metal.",
            "Alloy Metalworking": "Ability to smith metal alloys."
        }
    },
    
    # Arcanum (A)
    "Portalmaster [Requires: Gatewalker]": {
        "Abilities": {
            "Arcanum":   0.5,   # Superior mastery over arcane energies
            "Portaling": 0.5    # Enhanced spatial manipulation
        },
        "Sliders": {},
        "Skillsets": {
            "Aetheric Riven": "Disrupts portal formation and stability, making it harder or impossible for others to create or maintain the portal.",
            "Aetheric Awareness": "Ability to sense the presence of portals and their signatures, both active and closed.",
            "Horizon Veiling": "Conceals the presence of portals, making them harder to detect or disrupt.",
            "Waypoint Expansion": "Increases the Range of portals, allowing for longer-distance travel.",
            "Tethered Entanglement": "Enhances the Capacity of portals, enabling the transport of larger and more complex loads (e.g., objects, animals, multiple people).",
            "Aetherstreaming": "Reduces the Efficiency (i.e., Time and Essence) required to form portals, making travel faster and more efficient."
        }
    },
    "Runic Aegis": {
        "Abilities": {
            "Arcanum":   0.35,   # Enhances understanding of magical symbols
            "Technique": 0.2,    # Improves handling of enchanted items
            "Crafting":  0.2,     # Boosts efficiency with magical artifacts
            "Smithing":  0.15,      # Enhances crafting of magical items
            "Construction": 0.1,     # Improves magical construction
        },
        "Sliders": {},
        "Skillsets": {
            "Aetheric Armory": "Ability to build essence-based armor.",
            "Hexagonal Bastion": "Ability to use multi-essence armor.",
            "Aether Contain": "Ability to withstand essence manipulation from others."
        }
    },
    "Bladebound Runes": {
        "Abilities": {
            "Arcanum":   0.35,   # Enhances understanding of magical symbols
            "Technique": 0.2,    # Improves handling of enchanted items
            "Crafting":  0.2,     # Boosts efficiency with magical artifacts
            "Smithing":  0.15,      # Enhances crafting of magical items
            "Construction": 0.1,     # Improves magical construction
        },
        "Sliders": {},
        "Skillsets": {
            "Elemental Convergence": "Ability to use multi-essence weaponry.",
            "Aetheric Attack": "Ability to build essence-based weapons.",
            "Mindgilding": "Ability to build with Celestial Bindstones.",
            "Arcanum Inscription": "Ability to build with Arcanum Crystals."
        }
    },
    
    # Symbiosis (B)
    "Beastkin": {
        "Abilities": {
            "Symbiosis": 0.5,    # Deep affinity with nature and animals
            "Taming":    0.5     # Enhanced control over wildlife
        },
        "Sliders": {},
        "Skillsets": {
            "Primal Concord": "Establishes an innate bond with nearby wildlife, allowing the user to sense emotions, detect disturbances in nature, and build trust with animals faster.",
            "Soulbonded Companion": "Uses Symbiosis essence to form a deep connection with a single creature, granting enhanced communication, shared awareness, and minor boosts to the bonded animal's abilities.",
            "Warden's Call": "Projects a controlled essence pulse that influences the behavior of beasts, allowing the user to calm, summon, or subtly guide multiple creatures within range.",
            "Wild Resurgence": "Harnesses Symbiosis essence to temporarily enhance the physical attributes of an animal, making it faster, stronger, or more resilient in response to danger.",
            "Echo of the Pack": "Momentarily synchronizes the user's instincts with those of surrounding wildlife, improving reaction speed, tracking ability, and evasive movement when in natural environments."
        }
    },
    "Vitalist": {
        "Abilities": {
            "Symbiosis": 0.5,    # Strengthens overall life-force energy
            "Recovery":  0.1,     # Improves regenerative capabilities
            "Medicine":  0.1,      # Enhances healing and recovery
            "Farming":   0.1,       # Boosts sustainable food production
            "Foraging":  0.1,        # Improves resource gathering
            "Brewing":   0.1          # Enhances alchemical concoctions
        },
        "Sliders": {},
        "Skillsets": {
            "Verdant Awakening": "Channels Symbiosis essence to accelerate plant growth, restoring damaged flora, strengthening crops, and revitalizing natural environments.",
            "Floral Communion": "Enhances the ability to sense and interact with plant life, allowing the user to detect rare flora, predict natural growth patterns, and intuitively understand a plant's properties.",
            "Ambrosia Weaving": "Manipulates Ambrosia Sap as a living material, using it to reinforce structures, enhance medicinal properties, and integrate it into organic crafting.",
            "Sustained Harvest": "Extracts resources from plants with minimal harm, ensuring faster regrowth and improving the potency of harvested herbs, fruits, and alchemical ingredients.",
            "Bramble Ward": "Temporarily hardens or animates surrounding plant life for defensive or offensive purposes, creating reactive plant movement."
        }
    },
    "Brewmaster [Requires: Brewer]": {
        "Abilities": {
            "Symbiosis": 0.5,    # Harnesses natural fermentation and alchemy
            "Brewing":   0.5     # Excels in medicinal and restorative concoctions
        },
        "Sliders": {},
        "Skillsets": {
            "Alchemical Concoctions": "Produces volatile, experimental mixtures, including poisons, mind-altering substances, smoke bombs, and other tactical or unpredictable brews.",
            "Arcane Brewing": "Produces essence-related brews.",
            "Medicinal Brewing": "Creates potions and tonics that heal wounds, cure ailments, enhance recovery, and bolster the body's resistance to disease and poisons.",
            "Mental Enhancement Brewing": "Crafts brews that temporarily boost mental clarity, providing strategic advantages in combat or skill-based tasks.",
            "Physical Enhancement Brewing": "Crafts brews that temporarily boost physical capabilities, providing strategic advantages in combat or skill-based tasks."
        }
    },
    
    # Metamorphosis (M)
    "Chimera's Gift": {
        "Abilities": {
            "Metamorphosis": 1.0,  # Enables transformative biological adaptations
        },
        "Sliders": {},
        "Skillsets": {
            "Adaptive Aperture": "Able to adjust pupil shape (e.g., horizontal or vertical slits) to increase range and distinguish or focus on different visual stimuli.",
            "Keen Scent": "Enhances olfactory perception, allowing the user to detect distant scents, track individuals, and distinguish complex odors with precision.",
            "Respiratory Shift": "Temporarily enhances oxygen storage in the blood and muscles, allowing the user to function efficiently in low-oxygen environments, hold breath for extended periods, and resist airborne toxins.",
            "Adaptive Camouflage": "Temporarily alters skin pigmentation and texture to blend seamlessly into surroundings, greatly improving stealth and evasive capabilities.",
            "Electroreception": "Enhances sensory perception by detecting the bioelectric fields of living beings, allowing the user to sense creatures through conductive environments."
        }
    },
    "Essence Weaver": {
        "Abilities": {
            "Metamorphosis": 0.6,  # Improves internal transfer between essence types
            "Arcanum":    0.3,
            "Equilibrio":  0.1
        },
        "Sliders": {},
        "Skillsets": {
            "Amorphize Essence": "Able to convert crystallized (type-specific) essence to amorphous (raw) essence.",
            "Crystallize Essence": "Able to convert amorphous (raw) essence to crystallized (type-specific) essence.",
            "Transmute Essence": "Able to convert crystallized (type-specific) essence to another crystallized (type-specific) essence."
        }
    },
    "Folkwise": {
        "Abilities": {
            "Metamorphosis": 0.5,  # Supports adaptive transformation
            "Diplomacy":     0.1,   # Enhances cultural adaptation and negotiation
            "Persuasion":    0.1,    # Improves communication and influence
            "Stealth":       0.1,       # Enhances covert integration
            "Deception":     0.1,       # Improves disguises and social infiltration
            "Intimidation":  0.1        # Enhances social presence
        },
        "Sliders": {
            "Learning Rate":         0.01,
            "Inverse Metabolic Rate": -0.01,
            "Inverse Sleep Cycle":   -0.01,
            "Memory":                0.01
        },
        "Skillsets": {
            "Instinctive Synchrony": "Subconsciously absorbs local accents, speech cadences, and social gestures, allowing for seamless verbal and nonverbal integration into any culture.",
            "Metabolic Adaptation": "Subtly adjusts internal rhythms (such as sleep cycle, dietary tolerance, and scent signature) to match those of the surrounding population.",
            "Implicit Trust": "Projects an aura of familiarity, reducing initial suspicion and making people instinctively less guarded, as if you are someone they should already know.",
            "Veilborn Gaze": "Able to temporarily change eye color."
        }
    },
    
    # Sapien (I)
    "Memory Palace": {
        "Abilities": {
            "Sapien": .6,    # Enhances intellectual capacity and retention
            "Durabilis": 0.15,
            "Arcanum": 0.15,
            "Symbiosis": 0.1
        },
        "Sliders": {
            "Inverse Metabolic Rate": -0.10,
            "Inverse Sleep Cycle":   -0.10,
            "Memory":                0.20
        },
        "Skillsets": {
            "Lucid Reconstruction": "Mentally reconstructs an event, allowing for the re-experience of sensory details and perspectives, even extrapolating missing pieces based on logic and prior knowledge.",
            "Temporal Reflection": "Revisits past experiences in the mind with heightened detail, allowing the user to reanalyze situations and extract new insights or overlooked information.",
            "Foresight Loop": "Mentally simulates future scenarios by analyzing past experiences, recognizing patterns, and predicting the most probable outcomes of a situation before it unfolds."
        }
    },
    "Prodigal Polymath": {
        "Abilities": {
            "Sapien":   0.5,
            "Metamorphosis": 0.1,
            "Intimidation": 0.1,
            "Perception": 0.1,
            "Diplomacy": 0.1,
            "Persuasion": 0.1
        },
        "Sliders": {
            "Learning Rate":         0.10,
            "Inverse Metabolic Rate": -0.05,
            "Inverse Sleep Cycle":   -0.05,
        },
        "Skillsets": {
            "Tireless Mind": "Absorbs and mimics new techniques by observation, allowing the user to progress even while physically fatigued.",
            "Model Abstraction": "Able to learn through explanation and representation instead of practice or observation.",
            "Self-Study": "Improves learning of skills during self-study without a tutor.",
            "Skip the Basics": "Improves learning of both skills and prerequisites when prerequisites are not fully learned.",
        }
    },
    "Quickened Mind": {
        "Abilities": {
            "Sapien":         0.5,
            "Equilibrio":     0.3,
            "Perception":     0.2,
        },
        "Sliders": {
            "Thinking Speed":        0.20,
            "Inverse Metabolic Rate": -0.10,
            "Inverse Sleep Cycle":   -0.10,
        },
        "Skillsets": {
            "Instantaneous Calculation": "Rapidly assesses probabilities, dangers, and outcomes in real time, allowing split-second tactical decisions under pressure.",
            "Synaptic Burst": "An ability to sense the next step in a task.",
            "Parallel Processing": "Channels Sapien essence to bifurcate mental processing, enabling simultaneous focus on two distinct targets or tasks (e.g., monitoring two combatants, observing two conversations, or multitasking in complex scenarios). While it slightly reduces the depth of analysis for each task, it significantly boosts overall situational awareness and rapid reaction times."
        }
    }
}

SKILLSET_ABILITY_DEPENDENCE = {
    "Adrenaline Surge": {
        "Resilience": 0.30,   # Primary: ability to endure under duress
        "Recovery":   0.25,   # Quick bounce-back when low on health
        "Reflexes":   0.15,   # React quickly in stressful situations
        "Willpower":  0.15,   # Mental grit to trigger the surge
        "Strength":   0.15   # Momentary boost in physical power
    },
    "Wilderness Fortitude": {
        "Recovery":   0.40,   # Essential for sustained healing under damage
        "Resilience": 0.30,   # Endure environmental and continuous stress
        "Perception": 0.15,   # Heightened awareness to adapt and gather resources
        "Willpower":  0.15    # Maintaining resolve during prolonged adversity
    },
    "Brace": {
        "Strength":   0.30,   # Needed to hold a solid defensive posture
        "Resilience": 0.30,   # Absorb and deflect incoming damage
        "Technique":  0.20,   # Proper blocking or parrying technique
        "Reflexes":   0.10,   # Quick response to incoming threats
        "Willpower":  0.10    # Mental focus to maintain the posture
    },
    "Survivalist's Bond": {
        "Recovery":   0.35,   # Synchronize with specialized gear for optimal performance
        "Strength":   0.25,   # Wield heavy or uniquely balanced equipment
        "Technique":  0.25,   # Skillful integration with Ambrosia Sap weaponry and armor
        "Resilience": 0.15    # The durability needed to handle specialized gear
    },
    "Precision Parry": {
        "Reflexes": 0.40,   # Quick reaction is crucial for a perfect parry
        "Technique": 0.35,  # Proper form and timing are essential
        "Resilience": 0.15, # Ability to absorb impact
        "Willpower":  0.10  # Mental focus to hold the defensive stance
    },
    "Flash Stab": {
        "Reflexes": 0.35,   # Speed to execute the quick attack
        "Technique": 0.35,  # Precision in bypassing defenses
        "Agility":   0.20,  # Nimbleness to reposition during the attack
        "Speed":     0.10   # Overall quickness to deliver the strike
    },
    "Riposte": {
        "Reflexes": 0.35,   # Reacting quickly to an opening
        "Technique": 0.30,  # Accuracy in countering the attack
        "Willpower": 0.20,  # Seizing the moment with mental resolve
        "Agility":   0.15   # Fluid movement to execute the counter
    },
    "Duelist's Perception": {
        "Perception": 0.40, # Keen awareness to detect subtle cues and enemy weaknesses
        "Technique":  0.30, # Mastery in integrating weaponry with reflexive movements
        "Reflexes":   0.20, # Quick response to dynamic combat conditions
        "Willpower":  0.10  # Sustained focus under pressure
    },
    "Unstoppable Charge": {
        "Strength": 0.40,   # Primary force for breaking through defenses
        "Speed":    0.30,   # Essential for the rapid forward rush
        "Agility":  0.15,   # Helps maneuver around obstacles during the charge
        "Resilience": 0.15   # Supports enduring impacts while charging
    },
    "Ironhide": {
        "Resilience": 0.50,  # Main focus: enduring and absorbing damage
        "Recovery":   0.30,  # Aids in rapid stabilization post-impact
        "Strength":   0.20   # Contributes to the physical bracing needed to prevent knockback
    },
    "Crushing Blow": {
        "Strength":  0.55,   # Delivers the massive force needed to shatter defenses
        "Technique": 0.30,   # Ensures the strike is precise and effective
        "Resilience": 0.15   # Provides a base to handle the recoil of such a powerful attack
    },
    "Juggernaut's Might": {
        "Strength":  0.35,   # Fundamental for wielding heavy, powerful weaponry
        "Resilience": 0.35,   # Balances the physical demands of sustained combat
        "Recovery":   0.15,   # Supports maintaining effectiveness over extended bouts
        "Technique":  0.15    # Ensures proper handling and integration of specialized gear
    },
    "Strategic Insight": {
        "Perception": 0.45,  # Keen awareness to analyze the battlefield
        "Strategy":   0.45,  # Core to formulating tactical plans
        "Willpower":  0.10   # Provides mental resolve for sustained analysis
    },
    "Combat Momentum": {
        "Reflexes":   0.40,  # Rapid reactions drive the fluidity of combos
        "Technique":  0.40,  # Precise execution is essential for chaining attacks
        "Agility":    0.20   # Supports nimble movement during rapid exchanges
    },
    "Feint": {
        "Deception":  0.50,  # Misleads opponents to create openings
        "Technique":  0.30,  # Ensures the feint is executed with finesse
        "Perception": 0.20   # Helps read enemy reactions to the feint
    },
    "Tactician's Insight": {
        "Strategy":   0.50,  # Central to wielding specialized (Celestial Bindstones) gear effectively
        "Technique":  0.30,  # Ensures proper handling and synergy with the equipment
        "Perception": 0.20   # Fine-tunes awareness for exploiting tactical advantages
    },
    "Blinding Speed": {
        "Speed":   0.50,   # Primary factor for rapid movement and attack speed
        "Agility": 0.30,   # Enhances quick directional changes and evasive maneuvers
        "Reflexes": 0.20   # Supports fast reaction times during the burst of speed
    },
    "Acrobatic": {
        "Agility":  0.45,   # Core to executing complex maneuvers and dodges
        "Reflexes": 0.35,   # Critical for quick, precise adjustments during acrobatics
        "Technique": 0.20   # Ensures the moves are executed with finesse and control
    },
    "Swift Slash": {
        "Technique": 0.40,  # Delivers the precision needed for a smooth, effective strike
        "Speed":     0.30,  # Contributes to the fluidity and rapid execution of the attack
        "Reflexes":  0.30   # Enables quick follow-through and timing against defenses
    },
    "Swiftfoot's Agility": {
        "Agility":  0.55,   # Primary for overall nimbleness and adaptability with weaponry
        "Reflexes": 0.25,   # Supports quick responses in dynamic combat situations
        "Speed":    0.20    # Helps maintain the momentum required for fluid movement
    },
    "Deadeye Mark": {
        "Stealth": 0.50,   # Core to remaining undetected while aiming
        "Technique": 0.30,  # Ensures precision in aiming and shooting
        "Perception": 0.20   # Enhances awareness of surroundings while aiming
    },
    "Armor-Split Shot": {
        "Strength": 0.80,  # Core to delivering the force needed to penetrate armor
        "Technique": 0.20  # Ensures the shot is executed with precision and control
    },
    "Rain of Arrows": {
        "Reflexes":  0.40, # Quick reaction to unleash a barrage of arrows
        "Technique": 0.40,  # Core to the rapid firing technique
        "Perception": 0.20,  # Enhances awareness of surroundings while shooting
    },
    "Sharpshooter's Focus": {
        "Symbiosis": 0.20,
        "Equilibrio": 0.20,
        "Durabilis": 0.20,
        "Metamorphosis": 0.20,
        "Technique": 0.10,
        "Perception": 0.10,
    },
    "Infuse Essence": {
        "Arcanum":    0.40,  # Core magical energy for infusion
        "Equilibrio": 0.30,  # Balance needed to flow essence properly
        "Technique":  0.20,  # Skillful application during the process
        "Willpower":  0.10   # Mental control to direct the infusion
    },
    "Siphon Essence": {
        "Symbiosis":  0.40,  # Connecting with and drawing out essence
        "Durabilis":  0.30,  # Endurance for sustaining the siphon
        "Technique":  0.20,  # Proper extraction methods
        "Willpower":  0.10   # Focus to maintain control during siphoning
    },
    "Aetheric Grasp": {
        "Perception": 0.40,  # Detect subtle flows of essence
        "Reflexes":   0.30,  # Quick reaction to secure the essence
        "Technique":  0.20,  # Precise manipulation once grasped
        "Willpower":  0.10   # Mental focus to control the grasp
    },
    "Mystic Blade's Arcana": {
        "Arcanum":   0.40,   # Channeling mystical energy through weaponry
        "Technique": 0.35,   # Mastery in handling enchanted blades and armor
        "Strength":  0.15,   # Physical force behind wielding the weapon
        "Reflexes":  0.10    # Quick adjustments in combat scenarios
    },
    "Master Planner": {
        "Strategy":   0.55,  # Emphasis on high-level planning and tactics
        "Perception": 0.25,  # Critical for situational awareness in planning
        "Willpower":  0.20   # Supports mental endurance during complex strategizing
    },
    "Commander's Presence": {
        "Persuasion": 0.40,  # Essential for inspiring and rallying allies
        "Diplomacy":  0.40,  # Fosters trust and unity among team members
        "Willpower":  0.20   # Underpins the resolute character of a commander
    },
    "Analytical Mind": {
        "Perception": 0.55,  # Keen observation to break down complex details
        "Strategy":   0.25,  # Logical reasoning to deduce effective solutions
        "Willpower":  0.20   # Mental persistence in unraveling intricate problems
    },
    "Master of Deception": {
        "Deception": 0.60,   # Primary for creating false impressions
        "Stealth":   0.20,   # Aids in misdirection and disguise
        "Persuasion":0.20    # Supports subtle influence
    },
    "Psychological Insight": {
        "Perception": 0.50,  # Key to reading emotions and cues
        "Willpower":  0.30,  # Mental fortitude for manipulation
        "Persuasion": 0.20   # Influences behavior effectively
    },
    "Mind Games": {
        "Deception": 0.40,   # Exploiting opponents' fears and desires
        "Strategy":  0.35,   # Crafting psychological tactics
        "Perception": 0.25   # Reading subtle signals in opponents
    },
    "Creative Genius": {
        "Crafting":  0.45,   # Innovating new devices and solutions
        "Technique": 0.25,   # Skillful execution of inventions
        "Strategy":  0.30    # Integrating knowledge with creativity
    },
    "Mechanical Mastery": {
        "Smithing":  0.50,   # Core understanding of machines and repairs
        "Crafting":  0.30,   # Building and modifying devices
        "Technique": 0.20    # Precision in handling mechanics
    },
    "Large-Scale Engineering": {
        "Construction": 0.40,  # Designing and building massive projects
        "Smithing":     0.10,  # Integrating structural elements
        "Strategy":     0.40,   # Planning large-scale endeavors
        "Crafting":     0.10   # Ensuring the practical application of designs
    },
    "Polyglot": {
        "Diplomacy":  0.50,   # Facilitates communication across cultures
        "Persuasion": 0.30,   # Enhances language and influence skills
        "Perception": 0.20    # Observing linguistic nuances
    },
    "Cultural Literacy": {
        "Diplomacy":  0.50,   # Key for understanding social norms
        "Persuasion": 0.30,   # Aids in smooth interactions
        "Perception": 0.20    # Recognizing cultural cues
    },
    "Lorekeeper": {
        "Perception": 0.40,   # Observing historical and contextual details
        "Strategy":   0.30,   # Analyzing and using historical insights
        "Willpower":  0.30    ,# Sustaining deep knowledge and focus
    },
    "Mind's Eye": {
        "Perception": 0.80,    # Heightened observation of terrain and hazards
        "Navigation": 0.20     # Knowledge of environmental layouts
    },
    "Intuitive Awareness": {
        "Perception": 0.70,    # Keen sensitivity to subtle body language and expressions
        "Diplomacy":  0.15,    # Interpreting social cues
        "Deception":  0.15     # Detecting hidden intentions
    },
    "Pattern Recognition": {
        "Perception": 0.60,    # Identifying recurring clues and structures
        "Strategy":   0.40     # Leveraging patterns to solve puzzles and mysteries
    },
    "Negotiation": {
        "Diplomacy":  0.50,    # Core to resolving conflicts via dialogue
        "Persuasion": 0.30,    # Influencing outcomes through compromise
        "Perception": 0.20     # Reading the room to find common ground
    },
    "Friends in High Places": {
        "Diplomacy":  0.50,    # Building and maintaining influential relationships
        "Persuasion": 0.40,    # Convincing key figures to offer support
        "Perception": 0.10     # Sensing opportunities within social circles
    },
    "Charisma": {
        "Persuasion": 0.60,    # Inspiring trust and confidence in others
        "Diplomacy":  0.20,    # Easing communication and rapport-building
        "Deception":  0.20     # Adapting persona to suit different contexts
    },
    "Menacing Presence": {
        "Intimidation": 0.70,  # Projecting threat and confidence
        "Deception":    0.20,  # Using misdirection to unsettle opponents
        "Persuasion":   0.10   # Forcing compliance through sheer presence
    },
    "Solitary Focus": {
        "Willpower":  0.60,    # Sustaining mental clarity when alone
        "Perception": 0.30,    # Heightened senses for detailed observation
        "Strategy":   0.10     # Efficient problem-solving during solo endeavors
    },
    "Shadow Operative": {
        "Stealth":   0.50,     # Core ability for silent movement and covert actions
        "Agility":   0.30,     # Enhancing nimbleness for quick, quiet maneuvers
        "Perception":0.20      # Aiding in detection avoidance and situational awareness
    },
    "Master of Disguise": {
        "Deception": 0.60,     # Adopting false identities and personas
        "Stealth":   0.20,     # Blending into diverse environments undetected
        "Diplomacy": 0.20      # Seamlessly integrating into various social circles
    },
    "Con Artist": {
        "Deception": 0.60,   # Primary ability for elaborate schemes and manipulation
        "Persuasion":0.25,  # Influencing targets to lower their defenses
        "Strategy":  0.15    # Crafting and executing intricate plans
    },
    "Counterfeit Expertise": {
        "Crafting":  0.45,   # Skill in producing convincing forgeries
        "Technique": 0.30,   # Attention to detail in replication and production
        "Perception":0.25    # Spotting subtle inconsistencies in items
    },
    "Haggler's Instinct": {
        "Trade":     0.45,   # Inherent sense for market value and bartering
        "Persuasion":0.35,   # Negotiation skills to secure better prices
        "Perception":0.20    # Reading market cues and signals effectively
    },
    "Market Opportunist": {
        "Trade":     0.40,   # Identifying lucrative trade routes and trends
        "Strategy":  0.30,   # Tactical analysis of market fluctuations
        "Navigation":0.20,   # Utilizing travel routes for strategic advantage
        "Perception":0.10    # Observing emerging shortages and opportunities
    },
    "Appraisal Expert": {
        "Perception":0.55,   # Keen observation to determine true value and quality
        "Trade":     0.25,   # Understanding market worth and demand
        "Crafting":  0.20    # Knowledge of construction and flaws in items
    },
    "Underworld Connections": {
        "Diplomacy": 0.40,   # Building and maintaining covert networks
        "Persuasion":0.35,   # Cultivating relationships with influential figures
        "Deception": 0.25    # Operating discreetly in illicit circles
    },
    "Display of Power": {
        "Intimidation":0.70, # Projecting an aura of authority and danger
        "Persuasion":  0.20,  # Commanding respect and compliance from others
        "Deception":   0.10   # Employing subtle misdirection to reinforce presence
    },
    "Shadow Broker": {
        "Stealth":   0.40,   # Maintaining anonymity in discreet dealings
        "Trade":     0.30,   # Expertise in handling secret transactions
        "Diplomacy": 0.30    # Navigating and preserving covert networks
    },
    "Basic Metalworking": {
        "Smithing":  0.60,   # Core skill for working with metals
        "Crafting":  0.30,   # Essential for assembling metal items
        "Technique": 0.10    # Precision in handling and shaping metal
    },
    "Basic Woodworking": {
        "Crafting":     0.50,   # Main ability for working with wood
        "Construction": 0.30,   # Useful for building and joining wooden structures
        "Technique":    0.20    # Fine detail and precision work
    },
    "Weaponcraft": {
        "Smithing":  0.40,   # For forging metal components of weapons
        "Crafting":  0.40,   # General assembly of weapon parts
        "Technique": 0.20    # Ensuring functional and precise design
    },
    "Armorcraft": {
        "Smithing":     0.35,  # For metal armor components
        "Crafting":     0.35,  # For non-metal or combined materials
        "Construction": 0.15,  # Assembling various parts into a cohesive piece
        "Technique":    0.15   # Precision detailing for optimal performance
    },
    "Structural Engineering": {
        "Construction": 0.60,   # Primary ability for building structures
        "Technique":    0.20,   # Precision in design and assembly
        "Strategy":     0.20    # Planning and architectural insight
    },
    "Precision Designing": {
        "Technique": 0.50,   # Core to fine-detail work and enhancements
        "Crafting":  0.30,   # Integrating complex components
        "Perception":0.20    # Noticing subtle details and synergies
    },
    "Textile & Leatherworking": {
        "Crafting":     0.60,   # Essential for working with flexible materials
        "Technique":    0.30,   # Detailed manipulation for quality work
        "Construction": 0.10    # Assembling garments and gear
    },
    "Green Thumb": {
        "Farming":   0.50,   # Primary for increasing crop yields
        "Foraging":  0.50,   # Identifying beneficial plants and herbs
    },
    "Fisherman's Luck": {
        "Fishing":    0.70,   # Core ability for successful fishing
        "Perception": 0.20,   # Spotting ideal fishing conditions
        "Navigation": 0.10    # Locating prime fishing spots
    },
    "Nature's Bounty": {
        "Foraging":  0.50,   # Finding and harvesting natural resources
        "Perception":0.30,   # Identifying rare or valuable finds
        "Tracking":  0.20    # Locating hidden caches in the environment
    },
    "Small Game Hunter": {
        "Hunting":  0.50,   # Core skill for tracking small creatures
        "Tracking": 0.30,   # Essential for following small game trails
        "Agility":  0.20    # Quick movement needed in hunting small, nimble targets
    },
    "Big Game Hunter": {
        "Hunting":  0.40,   # Central for pursuing large creatures
        "Tracking": 0.30,   # Crucial for following larger prey over long distances
        "Strength": 0.30    # Physical prowess to take down big game
    },
    "Scavenger": {
        "Foraging":  0.40,  # Key to collecting useful items from the environment
        "Perception":0.40,  # Spotting hidden or overlooked resources
        "Stealth":   0.20   # Moving quietly to avoid detection while scavenging
    },
    "Field Medic": {
        "Technique": 0.25,   # Precision in administering emergency care
        "Medicine": 0.50,   # Knowledge of ongoing treatment protocols
        "Perception":0.25,  # Observing symptoms and diagnostic cues
    },
    "Long-Term Care": {
        "Technique": 0.20,   # Precision in administering emergency care
        "Medicine": 0.40,   # Knowledge of ongoing treatment protocols
        "Willpower": 0.20,   # Sustained focus for prolonged care
        "Perception":0.10,  # Observing symptoms and diagnostic cues
        "Strategy":  0.10   # Formulating effective treatment plans
    },
    "Medical Knowledge": {
        "Medicine":  0.70,  # Deep understanding of anatomy and treatments
        "Perception":0.15,  # Observing symptoms and diagnostic cues
        "Strategy":  0.15   # Formulating effective treatment plans
    },
    "Pickpocket": {
        "Stealth":   0.20,  # Core ability to avoid detection
        "Deception": 0.30,  # Misdirecting targets during the act
        "Thieving":  0.50   # Expertise in lifting items unnoticed
    },
    "Lockpicking": {
        "Technique": 0.40,  # Precision required to bypass locks
        "Perception":0.30,   # Spotting lock mechanisms and weaknesses
        "Thieving":  0.30   # Expertise in lifting items unnoticed
    },
    "Medicinal Brewing": {
        "Brewing":  0.50,   # Core skill in crafting healing potions
        "Medicine": 0.50,   # Knowledge of beneficial ingredients and effects
    },
    "Mental Enhancement Brewing": {
        "Brewing":   0.50,  # Primary skill for crafting enhancement potions
        "Strategy":  0.50,  # Designing brews for improved mental clarity
    },
    "Physical Enhancement Brewing": {
        "Brewing":  0.60,   # Crafting potions to boost physical capabilities
        "Strategy":  0.40,   # Designing brews for improved physical performance
    },
    "Celestial Clues": {
        "Navigation": 0.50,   # Using celestial markers to determine direction and time
        "Perception": 0.30,   # Observing stars, moons, and atmospheric cues
        "Strategy":   0.20    # Planning optimal routes based on celestial data
    },
    "Seafaring": {
        "Navigation": 0.60,   # Core for charting courses on water
        "Perception": 0.25,   # Reading currents, tides, and wind patterns
        "Strategy":   0.15    # Tactical decision-making for maritime travel
    },
    "Pathfinder's Instinct": {
        "Navigation": 0.40,   # Identifying natural paths in unexplored terrain
        "Perception": 0.40,   # Spotting hidden routes and safe passages
        "Tracking":   0.20    # Following subtle environmental cues to navigate
    },
    "Flowing Stride": {
        "Taming":    0.40,    # Core ability to bond with and control mounts
        "Agility": 0.20,      # Enhancing maneuverability while riding
        "Strength": 0.20,   # Core physical power to maintain balance and control
        "Reflexes":0.20       # Quick adjustments during dynamic movement
    },
    "Endurance Synergy": {
        "Resilience": 0.30,   # Sustaining prolonged physical effort
        "Recovery":   0.20,   # Faster recuperation for both rider and mount
        "Strength":   0.10,    # Physical power to support long journeys
        "Willpower":  0.15,    # Mental fortitude to push through fatigue
        "Taming":    0.25     # Bonding with the mount to enhance performance
    },
    "Saddleborn": {
        "Taming":    0.60,    # Core for bonding with and taming mounts
        "Perception":0.20,    # Reading the behavior and cues of animals
        "Willpower": 0.20     # Mental resolve to establish trust
    },
    "Waypoint Expansion": {
        "Portaling":  0.60,   # Increasing the range of magical portals
        "Navigation": 0.20,    # Ensuring accurate long-distance travel
        "Arcanum":    0.20   # Enhancing the magical essence used in portal creation
    },
    "Tethered Entanglement": {
        "Portaling":   0.60,  # Enhancing portal capacity for larger loads
        "Arcanum":    0.20,   # Enhancing the magical essence used in portal creation
        "Construction":0.20   # Structuring portals to handle complex loads
    },
    "Aetherstreaming": {
        "Portaling": 0.60,    # Streamlining portal formation
        "Arcanum":   0.20,    # Core magical essence for efficient streaming
        "Technique": 0.20     # Precise control to improve efficiency
    },
    "Radiant Equilibrium": {
        "Equilibrio": 0.70,   # Adjusts vision across varying light conditions
        "Perception": 0.30    # Enhances visual awareness and threat detection
    },
    "Echowise": {
        "Perception": 0.90,   # Core for detecting subtle sounds and nuances
        "Willpower":  0.10    # Aids in focused auditory concentration
    },
    "Palate Perception": {
        "Perception": 0.90,   # Heightens sensitivity to tastes and flavors
        "Willpower":  0.10    # Supports concentration to isolate specific tastes
    },
    "Haptic Sensitivity": {
        "Perception": 0.90,   # Detects subtle vibrations and textures through touch
        "Technique":  0.10    # Provides the finesse needed to interpret tactile cues
    },
    "Primordial Instict": {
        "Arcanum":    0.35,   # Key to detecting and identifying magical essence
        "Perception": 0.30,    # Enhances overall sensory detection of essence sources
        "Equilibrio": 0.35   # Balances the flow of essence within the environment
    },
    "Flowstate Mastery": {
         "Equilibrio": 0.50,   # Enhances focus and precision through balanced essence
         "Technique":  0.30,   # Improves execution of repeated, skillful actions
         "Willpower":  0.20    # Supports mental clarity and sustained flow
    },
    "Effortless Repetition": {
         "Equilibrio": 0.40,   # Maintains consistent balance during repetitive tasks
         "Recovery":   0.40,   # Reduces fatigue and boosts efficiency over time
         "Technique":  0.20    # Enhances smooth, precise performance of tasks
    },
    "Equilibrium Surge": {
         "Equilibrio": 0.60,   # Channels balance essence to stabilize wounds instantly
         "Recovery":   0.30,   # Restores health rapidly in the heat of combat
         "Resilience": 0.10    # Provides added durability to endure injuries
    },
    "Vital Flow Cleansing": {
         "Equilibrio": 0.50,   # Uses essence to purge toxins and stabilize the mind
         "Medicine":   0.30,   # Enhances treatment of poisons, diseases, and imbalances
         "Willpower":  0.20    # Maintains mental steadiness during cleansing processes
    },
    "Resonant Rejuvenation": {
         "Equilibrio": 0.50,   # Aligns natural healing rhythms with Equilibrio essence
         "Recovery":   0.30,   # Accelerates long-term recovery from severe injuries
         "Medicine":   0.20    # Applies medical knowledge to chronic ailments and lingering wounds
    },
    "Unbreakable Will": {
         "Durabilis": 0.40,    # Channels Durabilis essence for mental fortitude
         "Willpower": 0.60     # Enhances focus and determination
    },
    "Pain is Power": {
         "Durabilis": 0.40,    # Harnesses pain into essence-driven strength
         "Strength":  0.40,    # Boosts physical power after damage
         "Resilience": 0.20    # Endures damage to fuel the next attack
    },
    "Stalwart Focus": {
         "Willpower":  0.65,   # Maintains unwavering mental clarity
         "Durabilis":  0.25,   # Reinforces focus with essence stability
         "Strategy":   0.10    # Aids in complex, high-pressure situations
    },
    "Vital Forge": {
         "Durabilis": 0.50,    # Accelerates regeneration via Durabilis essence
         "Recovery":  0.30,    # Speeds up natural healing processes
         "Medicine":  0.20     # Applies anatomical and treatment knowledge
    },
    "Nectar of the Gods": {
         "Durabilis": 0.40,    # Enhances regeneration with potent essence
         "Medicine":  0.10,    # Cures ailments and restores vitality
         "Brewing":   0.10,     # Crafts the Ambrosia Sap Tea for enhanced recovery
         "Resilience": 0.20,   # Provides a buffer against future ailments and injuries
         'Recovery': 0.20   # Enhances the overall recovery process, ensuring sustained vitality
    },
    "Enduring Embers": {
         "Durabilis": 0.50,    # Sustains life force when critically challenged
         "Resilience": 0.30,    # Prevents incapacitation under extreme conditions
         "Recovery":  0.20     # Aids in continued action until full collapse
    },
    "Durabilis Metalworking": {
         "Durabilis": 0.40,    # Infuses metalwork with essence properties
         "Smithing":  0.50,    # Core skill for working with metals
         "Crafting":  0.10     # Fine-tuning and assembly of metal items
    },
    "Kinestal Metalworking": {
         "Durabilis": 0.40,    # Channels Durabilis essence into Kinestal metal
         "Smithing":  0.50,    # Essential for precise metal forging
         "Crafting":  0.10     # Complements the technical aspects of metalwork
    },
    "Libranium Metalworking": {
         "Durabilis": 0.40,    # Enhances working with Libranium through essence
         "Smithing":  0.50,    # Primary skill for metal forging
         "Crafting":  0.10     # Ensures intricate and stable constructions
    },
    "Alloy Metalworking": {
         "Durabilis": 0.40,    # Imbues alloys with stabilizing essence
         "Smithing":  0.50,    # Fundamental to alloy creation and manipulation
         "Crafting":  0.10     # Supports detailed and refined metalworking
    },
    "Aetheric Riven": {
         "Arcanum":   0.50,  # Uses core essence to disrupt portal formation
         "Technique": 0.30,  # Applies precise disruption methods
         "Portaling": 0.20   # Targets portal stability mechanisms
    },
    "Aetheric Awareness": {
         "Arcanum":    0.40,  # Senses the unique signature of essence-based portals
         "Perception": 0.60   # Sharp detection of active and inactive portals
    },
    "Horizon Veiling": {
         "Arcanum":  0.40,    # Masks portal signatures with mystical essence
         "Stealth":  0.40,    # Enhances concealment of portal presence
         "Deception":0.20     # Misdirects detection attempts
    },
    "Aetheric Armory": {
         "Arcanum":  0.50,    # Infuses armor with potent essence
         "Smithing": 0.30,    # Crafts robust, essence-based armor
         "Crafting": 0.20     # Integrates intricate design elements
    },
    "Hexagonal Bastion": {
         "Arcanum":   0.35,   # Establishes a foundation of magical essence
         "Symbiosis": 0.25,   # Blends multiple essences for enhanced defense
         "Smithing":  0.25,   # Constructs the armor framework
         "Crafting":  0.15    # Fine-tunes multi-essence synergy
    },
    "Aether Contain": {
         "Arcanum":  0.40,    # Bolsters resistance against external essence manipulation
         "Willpower":0.30,    # Fortifies mental resolve
         "Resilience":0.30    # Enhances physical durability
    },
    "Elemental Convergence": {
         "Arcanum":   0.35,   # Harnesses core essence for weaponry
         "Symbiosis": 0.25,   # Integrates multiple essences into the attack
         "Smithing":  0.20,   # Forges weapon components
         "Crafting":  0.20    # Assembles and refines the multi-essence weapon
    },
    "Aetheric Attack": {
         "Arcanum":  0.50,    # Empowers weapons with potent magical energy
         "Smithing": 0.30,    # Constructs the physical form of the weapon
         "Technique":0.20     # Ensures precise and effective design
    },
    "Mindgilding": {
         "Arcanum":  0.40,    # Infuses constructs with ethereal essence
         "Crafting": 0.40,    # Builds with Celestial Bindstones
         "Strategy": 0.20     # Integrates design and tactical insight
    },
    "Arcanum Inscription": {
         "Arcanum":  0.50,    # Channels crystal essence into the build process
         "Crafting": 0.30,    # Structures and integrates the inscriptions
         "Technique":0.20     # Achieves precise detailing and stability
    },
    "Primal Concord": {
        "Symbiosis": 0.50,   # Core bonding with wildlife through essence
        "Perception": 0.30,  # Detects emotional and environmental cues
        "Taming":    0.20    # Builds trust and rapport with animals
    },
    "Soulbonded Companion": {
        "Symbiosis": 0.55,   # Deep connection with a single creature
        "Diplomacy": 0.30,   # Enhances communication and mutual understanding
        "Perception": 0.15   # Shared awareness of surroundings
    },
    "Warden's Call": {
        "Symbiosis": 0.50,   # Channels essence to influence beast behavior
        "Taming":    0.30,   # Guides animals subtly
        "Diplomacy": 0.20    # Exerts social influence over groups of creatures
    },
    "Wild Resurgence": {
        "Symbiosis": 0.40,   # Empowers animals with transformative essence
        "Strength":  0.30,   # Boosts physical power temporarily
        "Resilience":0.30    # Enhances durability in response to danger
    },
    "Echo of the Pack": {
        "Symbiosis": 0.40,   # Synchronizes instincts with surrounding wildlife
        "Tracking":  0.30,   # Improves ability to follow subtle cues in nature
        "Reflexes":  0.30    # Heightens reaction speed and evasive movement
    },
    "Verdant Awakening": {
        "Symbiosis": 0.50,   # Channels essence to rejuvenate plant life
        "Farming":   0.30,   # Strengthens crops and accelerates growth
        "Foraging":  0.20    # Enhances identification and restoration of flora
    },
    "Floral Communion": {
        "Symbiosis": 0.40,   # Enhances connection with plant life
        "Perception": 0.40,  # Detects rare flora and growth patterns
        "Foraging":  0.20    # Intuits properties and optimal harvesting methods
    },
    "Ambrosia Weaving": {
        "Symbiosis": 0.40,   # Manipulates living Ambrosia Sap for reinforcement
        "Brewing":   0.30,   # Enhances medicinal properties through crafted mixtures
        "Crafting":  0.30    # Integrates organic materials into functional constructs
    },
    "Sustained Harvest": {
        "Symbiosis": 0.40,   # Extracts resources while preserving plant vitality
        "Foraging":  0.40,   # Identifies and collects optimal botanical resources
        "Farming":   0.20    # Supports faster regrowth and improved yield quality
    },
    "Bramble Ward": {
        "Symbiosis": 0.50,   # Animates and hardens plant life defensively
        "Resilience":0.30,   # Imparts durability to the reactive flora
        "Technique": 0.20    # Ensures precise control over plant movement and structure
    },
    "Alchemical Concoctions": {
        "Brewing":   0.50,   # Primary skill for volatile, experimental mixtures
        "Crafting":  0.30,   # Integrates diverse ingredients into effective brews
        "Symbiosis": 0.20    # Leverages essence to enhance and balance concoctions
    },
    "Arcane Brewing": {
        "Symbiosis": 0.20,   # Infuses brews with the subtle power of nature’s essence
        "Arcanum":   0.40,   # Enhances the potency of arcane-infused brews
        "Brewing":   0.30,   # Crafts potent, essence-related mixtures
        "Crafting":  0.10    # Fine-tunes the integration of organic components
    },
    "Adaptive Aperture": {
        "Metamorphosis": 0.40,   # Adjusts visual range and focus via bodily transformation
        "Perception":    0.50,   # Sharp visual detection of varied stimuli
        "Technique":     0.10    # Fine control over pupil adjustments
    },
    "Keen Scent": {
        "Metamorphosis": 0.30,   # Adapts olfactory organs for enhanced detection
        "Perception":    0.60,   # Critical for distinguishing subtle odors
        "Technique":     0.10    # Aids in precise scent interpretation
    },
    "Respiratory Shift": {
        "Metamorphosis": 0.40,   # Alters physiology for low-oxygen environments
        "Recovery":      0.40,   # Supports efficient oxygen use and toxin resistance
        "Resilience":    0.20    # Enhances endurance under harsh conditions
    },
    "Adaptive Camouflage": {
        "Metamorphosis": 0.50,   # Modifies skin pigmentation and texture
        "Stealth":       0.30,   # Improves blending into surroundings
        "Perception":    0.20    # Helps judge the environment for effective concealment
    },
    "Electroreception": {
        "Metamorphosis": 0.30,   # Adapts sensory organs to detect bioelectric fields
        "Perception":    0.60,   # Key to sensing subtle electrical signals
        "Technique":     0.10    # Ensures precise detection in conductive environments
    },
    "Amorphize Essence": {
        "Metamorphosis": 0.50,   # Converts crystallized essence to raw, adaptable form
        "Arcanum":       0.20,   # Mild infusion of arcane influence in the conversion
        "Technique":     0.30    # Governs the transformation process
    },
    "Crystallize Essence": {
        "Metamorphosis": 0.50,   # Converts amorphous essence into a type-specific crystal
        "Arcanum":       0.20,   # Integrates a subtle arcane aspect during conversion
        "Technique":     0.30    # Controls the crystallization process
    },
    "Transmute Essence": {
        "Metamorphosis": 0.40,   # Alters one form of crystallized essence into another
        "Arcanum":       0.30,   # Mild arcane influence to enable precise conversion
        "Technique":     0.30    # Ensures effective transmutation between essence types
    },
    "Instinctive Synchrony": {
        "Metamorphosis": 0.30,   # Adapts to local linguistic and social cues
        "Diplomacy":     0.40,   # Facilitates seamless integration into new cultures
        "Perception":    0.30    # Detects subtle accents and gestures for smooth blending
    },
    "Metabolic Adaptation": {
        "Metamorphosis": 0.50,   # Adjusts internal rhythms to match the environment
        "Recovery":      0.30,   # Enhances physiological efficiency and tolerance
        "Resilience":    0.20    # Supports overall stability during adaptation
    },
    "Implicit Trust": {
        "Metamorphosis": 0.30,   # Adapts presence to project familiarity
        "Persuasion":    0.40,   # Encourages instinctive acceptance from others
        "Diplomacy":     0.30    # Aids in forming an aura of inherent trust
    },
    "Veilborn Gaze": {
        "Metamorphosis": 0.50,   # Alters eye appearance temporarily
        "Perception":    0.30,   # Enhances visual communication and recognition
        "Technique":     0.20    # Ensures smooth, controlled transformation of gaze
    },
    "Lucid Reconstruction": {
         "Sapien":     0.50,  # Core cognitive ability for reconstructing events
         "Perception": 0.30,  # Enhances sensory detail recall
         "Strategy":   0.20   # Fills in missing details through logical extrapolation
    },
    "Temporal Reflection": {
         "Sapien":     0.50,  # Enables detailed re-experiencing of past events
         "Perception": 0.30,  # Sharp sensory recall for heightened detail
         "Strategy":   0.20   # Assists in reanalyzing and extracting insights
    },
    "Foresight Loop": {
         "Sapien":     0.50,  # Simulates future scenarios using past insights
         "Strategy":   0.30,  # Recognizes patterns to predict outcomes
         "Perception": 0.20   # Detects subtle cues influencing future events
    },
    "Tireless Mind": {
         "Sapien":     0.50,  # Absorbs new techniques and knowledge efficiently
         "Perception": 0.25,  # Observes details even when fatigued
         "Technique":  0.25   # Mimics and integrates new methods through observation
    },
    "Model Abstraction": {
         "Sapien":     0.60,  # Learns through conceptual representation
         "Strategy":   0.30,  # Abstracts and organizes information effectively
         "Willpower":  0.10   # Supports sustained mental focus for learning
    },
    "Self-Study": {
         "Sapien":     0.60,  # Advances skills independently through cognitive learning
         "Strategy":   0.30,  # Structures and applies self-guided lessons
         "Willpower":  0.10   # Maintains focus during solo study sessions
    },
    "Skip the Basics": {
         "Sapien":     0.50,  # Accelerates learning by bypassing rudimentary steps
         "Strategy":   0.30,  # Identifies core components without full prerequisites
         "Technique":  0.20   # Applies refined methods to quickly grasp advanced skills
    },
    "Instantaneous Calculation": {
         "Sapien":     0.50,  # Rapid mental computation and probability assessment
         "Strategy":   0.40,  # Tactical analysis under pressure
         "Perception": 0.10   # Quick detection of immediate environmental cues
    },
    "Synaptic Burst": {
         "Sapien":     0.60,  # Senses and anticipates the next step in a task
         "Perception": 0.30,  # Enhances immediate situational awareness
         "Technique":  0.10   # Provides fine control over rapid cognitive transitions
    },
    "Parallel Processing": {
         "Sapien":     0.55,  # Bifurcates mental processing to handle multiple tasks
         "Strategy":   0.30,  # Manages simultaneous analyses with tactical oversight
         "Perception": 0.15   # Keeps track of subtle details across concurrent tasks
    }
}

CATEGORICAL_SKILL_MAP = {
    "Essence Carving": [
        "Infuse Essence", "Siphon Essence", "Aetheric Grasp", "Aether Contain", "Amorphize Essence", "Crystallize Essence", "Transmute Essence",
    ],
    "Combat and Physical Prowess": [
        "Flash Stab", "Swift Slash", "Unstoppable Charge", "Crushing Blow", "Deadeye Mark", "Armor-Split Shot", "Rain of Arrows",
        "Brace", "Ironhide", "Acrobatic",
        "Feint", "Precision Parry", "Riposte",
        "Adrenaline Surge", "Combat Momentum", "Blinding Speed", "Pain is Power",
        "Survivalist's Bond", "Duelist's Perception", "Juggernaut's Might", "Tactician's Insight", "Swiftfoot's Agility", "Sharpshooter's Focus", "Mystic Blade's Arcana", "Hexagonal Bastion", "Elemental Convergence",
    ],
    "Survival & Resource Management": [
        "Enduring Embers",
        "Wilderness Fortitude", 
        "Green Thumb", "Fisherman's Luck", "Nature's Bounty", "Small Game Hunter", "Big Game Hunter", "Scavenger",
        "Field Medic", "Long-Term Care", "Medical Knowledge", "Medicinal Brewing", "Equilibrium Surge", "Vital Flow Cleansing", "Resonant Rejuvenation", "Vital Forge", "Nectar of the Gods", 
        "Warden's Call", "Bramble Ward", "Primal Concord", "Soulbonded Companion", "Wild Resurgence", "Echo of the Pack", "Verdant Awakening", "Floral Communion", "Sustained Harvest", "Bramble Ward",
        "Respiratory Shift", "Adaptive Camouflage", "Metabolic Adaptation", 
    ],
    "Artifice and Engineering": [
        "Creative Genius", "Mechanical Mastery", "Large-Scale Engineering", "Structural Engineering",
        "Counterfeit Expertise", 
        "Basic Metalworking", "Basic Woodworking", "Textile & Leatherworking", "Precision Designing", 
        "Weaponcraft", "Armorcraft", "Durabilis Metalworking", "Kinestal Metalworking", "Libranium Metalworking", "Alloy Metalworking", 
        "Aetheric Armory", "Aetheric Attack", "Mindgilding", "Arcanum Inscription",
        "Alchemical Concoctions", "Mental Enhancement Brewing", "Physical Enhancement Brewing", "Arcane Brewing",
        "Ambrosia Weaving", 
    ],
    "Navigation and Portaling": [
        "Celestial Clues", "Seafaring", "Pathfinder's Instinct",
        "Waypoint Expansion", "Tethered Entanglement", "Aetherstreaming", "Aetheric Riven", "Aetheric Awareness", "Horizon Veiling", 
        "Flowing Stride", "Endurance Synergy", "Saddleborn"
    ],
    "Social & Psychological": [
        "Master of Deception", "Psychological Insight", "Mind Games", "Menacing Presence", "Master of Disguise", "Con Artist",
        "Polyglot", "Cultural Literacy", "Lorekeeper",
        "Haggler's Instinct", "Market Opportunist", "Appraisal Expert", "Shadow Broker", "Negotiation",
        "Friends in High Places", "Charisma", "Underworld Connections", "Display of Power",
        "Intuitive Awareness", 
        "Shadow Operative", "Pickpocket", "Lockpicking", 
        "Unbreakable Will", "Instinctive Synchrony", "Implicit Trust", "Veilborn Gaze"
    ],
    "Mental & Perceptive": [
        "Strategic Insight", "Commander's Presence", "Instantaneous Calculation", "Parallel Processing",
        "Master Planner", "Analytical Mind", "Solitary Focus",
        "Mind's Eye", "Pattern Recognition",
        "Radiant Equilibrium", "Echowise", "Palate Perception", "Haptic Sensitivity", "Adaptive Aperture", "Keen Scent", "Electroreception", 
        "Primordial Instict", "Flowstate Mastery", "Effortless Repetition", "Stalwart Focus",
        "Lucid Reconstruction", "Temporal Reflection", "Foresight Loop", "Tireless Mind", "Model Abstraction", "Self-Study", "Skip the Basics", "Synaptic Burst",
    ],
}

# -- HELPER FUNCTIONS --
def get_names_from_planet(planet, gender=None):
    names = {
        "Fortis Crags": {
            "Male": [
                "Tarukon", "Renshiro", "Kaelviro", "Moritayo", "Zorikunu", "Vaytaro", "Fenroku", "Hadrikor"
            ],
            "Female": [
                "Sarinai", "Velthira", "Karune", "Zorimeya", "Talyra", "Veyshika", "Rinaya", "Myatora"
            ],
            "Neutral": [
                "Kyronis", "Valithar", "Tazorin", "Loryath", "Rykaris", "Zeyoku", "Fenaris"
            ]
        },
        "Synvios": {
            "Male": [
                "Mariko", "Avarin", "Venaro", "Talimo", "Rohaku", "Lanirith", "Kaviroth", "Halorin"
            ],
            "Female": [
                "Nalia", "Selvai", "Arilune", "Veyani", "Torilma", "Lioran", "Kavira", "Amelith"
            ],
            "Neutral": [
                "Solvani", "Valureth", "Kaliro", "Morani", "Tavryn", "Zeyaro", "Halorien", "Rinothal"
            ]
        },
        "Percepio": {
            "Male": [
                "Varanith", "Kareshan", "Talvorin", "Ravikesh", "Danviran", "Koralesh", "Samrithan", "Velkaris"
            ],
            "Female": [
                "Arisena", "Vaylini", "Teshvara", "Lorisha", "Kamira", "Nalvitha", "Serithya", "Vanyora"
            ],
            "Neutral": [
                "Suvareth", "Kalorin", "Taryesh", "Valmira", "Zoravin", "Liranthya", "Koryath", "Navirith"
            ]
        },
        "Celeste": {
            "Male": [
                "Cael", "Taren", "Valk", "Ryn", "Orik", "Qiro", "Zaric", "Fynar"
            ],
            "Female": [
                "Lira", "Kora", "Veya", "Synna", "Talis", "Myra", "Zera", "Aryn"
            ],
            "Neutral": [
                "Riv", "Vren", "Lyon", "Sorin", "Toval", "Zyn", "Falik"
            ]
        },
        "Variare": {
            "Male": [
                "Renko", "Talvin", "Korath", "Vesrin", "Larek", "Fanor", "Zorik", "Mirak"
            ],
            "Female": [
                "Sariv", "Tavila", "Lorien", "Veyla", "Karyth", "Zaneth", "Rilora", "Mavrin"
            ],
            "Neutral": [
                "Viren", "Koril", "Talar", "Narek", "Zorin", "Falith", "Velkar", "Rynar"
            ]
        },
        "Nexus": {
            "Male": [
                "Valric", "Tarian", "Lucen", "Marvio", "Dorin", "Verian", "Jorven", "Veyric"
            ],
            "Female": [
                "Selva", "Vivara", "Mirel", "Calina", "Vessa", "Liora", "Seren", "Tavira"
            ],
            "Neutral": [
                "Auren", "Coren", "Velis", "Sylvan", "Torin", "Lexen", "Felan", "Zeren"
            ]
        }
    }

    gender_map = {
        "Male": "Male",
        "Female": "Female",
        "Neutral": "Neutral",
        "Any": None,
        None: None
    }

    planet_data = names.get(planet)
    if not planet_data:
        raise ValueError(f"Unknown planet: {planet}")
    
    key = gender_map.get(gender, None)
    
    if key:
        return planet_data.get(key, [])
    else:
        # Return all names for the planet if no gender is specified
        return planet_data["Male"] + planet_data["Female"] + planet_data["Neutral"]
    
# Placeholder function for get_date just return current_year = 885, current_month = 6, current_day = 1
def get_date():
    return 885, 6, 1


# ---- GENETICS CLASS ----

class Genetics:
    def __init__(self, father, mother, planet, expression_defined=False):
        """
        Initialize the genetics of a character.
        - father: List of 3 markers.
        - mother: List of 3 markers.
        - planet: List of 3 markers.
        - expression_defined: If True, assume one marker is already uppercase.
        """
        self.expression_defined = expression_defined  # New flag to check if markers are predefined

        # Store the raw inputs
        self.father = father
        self.mother = mother
        self.planet = planet

        # Process each source separately
        self.father_processed = self.process_source(self.father)
        self.mother_processed = self.process_source(self.mother)
        self.planet_processed = self.process_source(self.planet)

        # Expressed markers are the one chosen from each source
        self.expressed = [
            self.father_processed['expressed'],
            self.mother_processed['expressed'],
            self.planet_processed['expressed']
        ]

        # Dormant markers are the remaining ones (in lowercase) from all sources
        self.dormant = (
            self.father_processed['dormant'] +
            self.mother_processed['dormant'] +
            self.planet_processed['dormant']
        )

    def process_source(self, source_markers):
        """
        Given a list of 3 markers from a source, determine which marker is expressed.
        - If `expression_defined=True`, use the uppercase marker directly.
        - Otherwise, randomly choose one to be uppercase and convert the others to lowercase.
        Returns a dictionary with keys 'expressed' and 'dormant'.
        """
        if self.expression_defined:
            # If expression is predefined, find the uppercase marker
            expressed = next((m for m in source_markers if m.isupper()), None)
            if not expressed:
                raise ValueError(f"Expression is defined, but no uppercase marker found in {source_markers}")

            # The remaining two are dormant (lowercased)
            dormant = [m.lower() for m in source_markers if m != expressed]
        else:
            # Randomly select one to be expressed, rest are dormant
            chosen_index = random.randrange(len(source_markers))
            expressed = source_markers[chosen_index]  # remains uppercase
            dormant = [source_markers[i].lower() for i in range(len(source_markers)) if i != chosen_index]

        return {"expressed": expressed, "dormant": dormant}

    def get_markers(self):
        """
        Returns the markers.
        """
        return self.expressed + self.dormant

    def pass_genes(self):
        """
        Simulates passing genes to the next generation.
        """
        # Randomly choose three from the expressed markers
        return random.sample(self.expressed, 3)

    def __str__(self):
        # Print like '{Father expressed}{father dormant 1}{father dormant 2}, {Mother expressed}{mother dormant 1}{mother dormant 2}, {Planet expressed}{planet dormant 1}{planet dormant 2}'
        return (
            f"{self.father_processed['expressed']}{self.father_processed['dormant'][0]}{self.father_processed['dormant'][1]}, "
            f"{self.mother_processed['expressed']}{self.mother_processed['dormant'][0]}{self.mother_processed['dormant'][1]}, "
            f"{self.planet_processed['expressed']}{self.planet_processed['dormant'][0]}{self.planet_processed['dormant'][1]}"
        )


# ---- Player Class ----
class Player:
    def __init__(self, name, genetics, physical_trait, mental_trait, social_trait, livelihood_trait, travel_trait, essence_traits_choice, size, birthdate, eye_color):
        self.name = name
        self.birthdate = birthdate  # birthdate in Nexus calendar (1 Nexus year = 1 Earth years)
        self.eye_color = eye_color  # string
        self.size = size  # Size object; dictionary with "Height" in inches and "Weight" in lbs
        self.genetics = genetics  # Genetics object
        self.physical_trait = physical_trait  # string key from physical_traits
        self.mental_trait = mental_trait      # string key from mental_traits
        self.social_trait = social_trait      # string key from social_traits
        self.livelihood_trait = livelihood_trait  # string key from livelihood_traits
        self.travel_trait = travel_trait
        self.essence_traits_choice = essence_traits_choice  # list of 4 strings like "E: Harmonic Mind"
        self.abilities = {}  # Will hold ability rating ranges
        self.gameplay_sliders = {}  # Will hold gameplay sliders
        self.skill_init_overflow = { "Overflow Points": [] }  # Will hold skills and their levels
        self.skillsets = []  # Will hold the skillsets based on the trait modifiers
        self.initialize_abilities()
        self.initialize_skillsets()
        self.age_alter_sliders()
        
    def initialize_skillsets(self):
        """
        Initialize all skillsets for the player.
        - Create all skillsets from skillset_ability_dependence
        - Calculate normalized ability scores for each
        - Apply trait modifiers for XP distribution
        - Handle overflow points properly (limited to trait skillsets)
        - Track and report total XP per trait
        """
        
        # Constants for XP calculation
        TRAIT_XP = 500000  # Base XP per trait
        OVERFULL_XP_MULTIPLER = 2500  # Multiplier for overflow points
        
        # Dictionary to track XP per trait
        trait_xp_totals = {}
        overflow_xp_totals = {}
        
        # Map of trait to its skillsets for quick lookup
        trait_to_skillsets = {}
        
        # Step 1: Initialize all skillsets from skillset_ability_dependence
        for skillset_name, abilities in SKILLSET_ABILITY_DEPENDENCE.items():
            # Get description if available
            description = f"Skillset based on abilities: {abilities}"
            
            # Look for a better description in trait_modifiers
            for trait in TRAIT_MODIFIERS:
                if "Skillsets" in TRAIT_MODIFIERS[trait]:
                    skillsets_data = TRAIT_MODIFIERS[trait]["Skillsets"]
                    if isinstance(skillsets_data, dict) and skillset_name in skillsets_data:
                        description = skillsets_data[skillset_name]
                        break
            
            new_skillset = Skillset(skillset_name, description)
            self.skillsets.append(new_skillset)
        
        # Build a mapping of traits to their skillsets
        for trait in TRAIT_MODIFIERS:
            if "Skillsets" in TRAIT_MODIFIERS[trait]:
                skillsets_data = TRAIT_MODIFIERS[trait]["Skillsets"]
                if isinstance(skillsets_data, dict):
                    trait_to_skillsets[trait] = list(skillsets_data.keys())
                elif isinstance(skillsets_data, list):
                    trait_to_skillsets[trait] = skillsets_data
        
        # Step 2: Calculate normalized ability scores and base XP
        for skillset in self.skillsets:
            # Get ability dependencies
            abilities = SKILLSET_ABILITY_DEPENDENCE[skillset.name]
            
            # Calculate weighted sum and maximum
            ability_values = []
            ability_weights = {}
            
            # Handle different formats of ability dependencies
            if isinstance(abilities, dict):
                for ability, weight in abilities.items():
                    if ability in self.abilities:
                        ability_values.append(self.abilities[ability]["current"])
                        ability_weights[ability] = weight
            else:  # If it's a list, use equal weights
                for ability in abilities:
                    if ability in self.abilities:
                        ability_values.append(self.abilities[ability]["current"])
                        ability_weights[ability] = 1.0
            
            # Skip if no valid abilities found
            if not ability_values:
                print(f"  Warning: No valid abilities found for {skillset.name}")
                continue
            
            # Calculate normalized score
            total_weight = sum(ability_weights.values())
            weighted_sum = sum(self.abilities[ability]["current"] * weight 
                            for ability, weight in ability_weights.items() 
                            if ability in self.abilities)
            
            weighted_mean = weighted_sum / total_weight if total_weight > 0 else 0
            normalized_score = (weighted_mean) / 100
            
            # Step 3: Find traits that modify this skillset
            traits_with_skillset = []
            for trait in [self.physical_trait, self.mental_trait, self.social_trait, 
                        self.livelihood_trait, self.travel_trait] + self.essence_traits_choice:
                if trait in TRAIT_MODIFIERS and "Skillsets" in TRAIT_MODIFIERS[trait]:
                    skillsets_data = TRAIT_MODIFIERS[trait]["Skillsets"]
                    
                    # Handle different formats of skillsets data
                    if isinstance(skillsets_data, dict) and skillset.name in skillsets_data:
                        traits_with_skillset.append(trait)
                    elif isinstance(skillsets_data, list) and skillset.name in skillsets_data:
                        traits_with_skillset.append(trait)
            
            # Apply XP from each trait
            if traits_with_skillset:
                for trait in traits_with_skillset:
                    # Initialize trait in the tracking dictionary if not already present
                    if trait not in trait_xp_totals:
                        trait_xp_totals[trait] = 0
                    
                    # Count skillsets in this trait
                    trait_skillset_count = 0
                    if isinstance(TRAIT_MODIFIERS[trait]["Skillsets"], dict):
                        trait_skillset_count = len(TRAIT_MODIFIERS[trait]["Skillsets"])
                    else:
                        trait_skillset_count = len(TRAIT_MODIFIERS[trait]["Skillsets"])
                    
                    # XP distribution
                    xp_pool_per_skill = TRAIT_XP / trait_skillset_count if trait_skillset_count > 0 else 0
                    #print(f"{xp_pool_per_skill} XP per skill for trait {trait} with {trait_skillset_count} skillsets.")

                    # Get learning rate from gameplay sliders (default to 50%)
                    learning_rate = 0.5
                    if "Learning Rate" in self.gameplay_sliders:
                        learning_rate = self.gameplay_sliders["Learning Rate"]["current"] / 100
                    
                    # Calculate initial XP
                    xp_init = learning_rate * normalized_score * xp_pool_per_skill
                    skillset.increment_xp(xp_init)
                    
                    # Track XP given by this trait
                    trait_xp_totals[trait] += xp_init
        
        # Step 4: Apply overflow points - IMPROVED VERSION
        if "Overflow Points" in self.skill_init_overflow:
            # First, group overflow points by trait
            trait_overflow = {}
            for overflow_entry in self.skill_init_overflow["Overflow Points"]:
                if len(overflow_entry) >= 3:
                    overflow_value, trait, ability = overflow_entry
                    if trait not in trait_overflow:
                        trait_overflow[trait] = []
                    trait_overflow[trait].append((overflow_value, ability))
            
            # Process each trait's overflow points
            for trait, overflow_entries in trait_overflow.items():
                
                # Initialize trait in the overflow tracking dictionary
                if trait not in overflow_xp_totals:
                    overflow_xp_totals[trait] = 0
                
                # Get list of skillsets that belong to this trait
                trait_skillsets = []
                if trait in trait_to_skillsets:
                    # Create a list of Skillset objects that belong to this trait
                    for skillset in self.skillsets:
                        if skillset.name in trait_to_skillsets[trait]:
                            trait_skillsets.append(skillset)
                
                if not trait_skillsets:
                    print(f"  Warning: No skillsets found for trait {trait}")
                    continue
                
                # Calculate total overflow points for this trait
                total_overflow = sum(value for value, _ in overflow_entries)
                
                # Split overflow points equally among trait skillsets
                overflow_xp_per_skillset = total_overflow * OVERFULL_XP_MULTIPLER / len(trait_skillsets)
                
                # Apply overflow XP to each skillset
                for skillset in trait_skillsets:
                    skillset.increment_xp(overflow_xp_per_skillset)
                    
                    # Track overflow XP given by this trait
                    overflow_xp_totals[trait] += overflow_xp_per_skillset

    def compute_size_modifiers(self, ability_name):
        """
        This function computes the size modifiers for the given ability.
        The size affects the floor and ceiling of the physical abilities.
        
        Returns a tuple of (floor_modifier, ceiling_modifier) where each is in range -20 to +20.
        The neutral point (0 modifier) is at height 5'11" (71 inches) and weight 175 lbs.
        """
        # Get height in decimal feet and weight in pounds
        height_inches = self.size["Height"]  # Assuming height is stored in inches
        weight_pounds = self.size["Weight"]  # Assuming weight is stored in pounds
        
        # Convert height to decimal feet for calculations
        height_feet = height_inches / 12.0
        
        # Define neutral reference point where modifiers are 0
        NEUTRAL_HEIGHT_FEET = 5.92  # 5'11" in decimal feet
        NEUTRAL_WEIGHT = 175
        NEUTRAL_BMI = 24.4
        
        # Calculate BMI
        height_meters = height_feet * 0.3048  # Convert feet to meters
        weight_kg = weight_pounds * 0.453592  # Convert pounds to kg
        bmi = weight_kg / (height_meters ** 2)
        
        # Calculate factors for ability modifiers
        # Height factor (-20 to +20)
        height_factor = min(max((height_feet - NEUTRAL_HEIGHT_FEET) * 13, -20), 20)
        
        # Weight factor (-20 to +20)
        weight_normalized = (weight_pounds - NEUTRAL_WEIGHT) / 100
        weight_factor = min(max(weight_normalized * 20, -20), 20)
        
        # BMI difference from neutral point
        bmi_diff = bmi - NEUTRAL_BMI
        bmi_factor = min(max(bmi_diff / 0.75, -20), 20)
        
        # Special case for exact neutral point - force all values to exactly zero
        if abs(height_feet - NEUTRAL_HEIGHT_FEET) < 0.01 and abs(weight_pounds - NEUTRAL_WEIGHT) < 1:
            return 0, 0  # Both floor and ceiling are unmodified
        
        # Initialize modifiers
        floor_modifier = 0
        ceiling_modifier = 0
        
        # Compute modifiers based on ability name
        ability_name = ability_name.lower()
        
        if ability_name == "strength":
            # Strength: Favors tall and heavy characters
            # Floor: Primarily affected by height - taller = higher minimum strength
            floor_modifier = round(height_factor * 0.7 + max(0, weight_factor) * 0.3)
            # Ceiling: Affected by both height and weight - bigger = stronger potential
            ceiling_modifier = round(height_factor * 0.4 + weight_factor * 0.6)
        elif ability_name == "speed":
            # Speed: Best with lean to average build
            # Floor: Heavy weight and extreme BMI lower minimum speed
            floor_modifier = round(-max(0, weight_factor) * 0.6 - abs(bmi_factor) * 0.4)
            # Ceiling: Height gives longer stride, but heavy weight reduces max speed
            ceiling_modifier = round(min(height_factor, 10) * 0.4 - max(0, weight_factor) * 0.7 - abs(bmi_factor) * 0.3)
        elif ability_name == "agility":
            # Agility: Favors shorter, leaner characters
            # Floor: Being tall or overweight decreases minimum agility
            floor_modifier = round(-max(0, height_factor) * 0.5 - max(0, bmi_factor) * 0.5)
            # Ceiling: Short height and lean build increase maximum potential agility
            ceiling_modifier = round(-height_factor * 0.4 - max(0, bmi_factor) * 0.7 + min(0, weight_factor) * 0.3)
        elif ability_name == "reflexes":
            # Reflexes: Primarily influenced by height
            # Floor: Being tall decreases minimum reflexes (neural path length)
            floor_modifier = round(-height_factor * 0.8 - abs(bmi_factor) * 0.2)
            # Ceiling: Height is primary factor for maximum potential reflexes
            ceiling_modifier = round(-height_factor * 0.7 - abs(bmi_factor) * 0.3 + min(0, weight_factor) * 0.1)
        elif ability_name == "resilience":
            # Combined Resilience/Endurance
            # Floor: Some mass helps with minimum resilience
            floor_modifier = round(min(bmi_factor, 5) * 0.5 + min(height_factor, 5) * 0.2 - max(weight_factor - 5, 0) * 0.4)
            # Ceiling: Balanced build is best for maximum potential
            ceiling_modifier = round(-abs(bmi_factor - 2) * 0.4 + min(height_factor, 8) * 0.3 - max(weight_factor - 5, 0) * 0.5)
        elif ability_name == "recovery":
            # Recovery: How quickly the body heals
            # Floor: Extreme body types recover more slowly
            floor_modifier = round(-abs(bmi_factor - 2) * 0.6 - abs(weight_factor) * 0.3)
            # Ceiling: Athletic builds have best potential recovery
            ceiling_modifier = round(-abs(bmi_factor - 2) * 0.5 + min(height_factor, 5) * 0.2 - abs(weight_factor) * 0.2)  
        elif ability_name == "stealth":
            # Stealth: Shorter, lighter characters are best
            # Floor: Height and weight increase minimum stealth
            floor_modifier = round(-max(0, height_factor) * 0.6 - max(0, weight_factor) * 0.4)   
            # Ceiling: Height and weight decrease maximum potential stealth
            ceiling_modifier = round(-height_factor * 0.5 - weight_factor * 0.5)
        elif ability_name == "intimidation":
            # Intimidation: Height and weight increase intimidation factor
            # Floor: Being short or light decreases minimum intimidation
            floor_modifier = round(height_factor * 0.6 + max(0, weight_factor) * 0.4)
            # Ceiling: Height and weight increase maximum potential intimidation
            ceiling_modifier = round(height_factor * 0.7 + weight_factor * 0.3)
        else:
            # If ability not recognized, return no modification
            floor_modifier = 0
            ceiling_modifier = 0
        return floor_modifier, ceiling_modifier

    def size_alter_abilities(self):
        """
        This function modifies the abilities based on the player's size.
        The size affects the floor and ceiling of the physical abilities.
        """
        # For each ability in the player:
        for ability_name, ability_range in self.abilities.items():
            floor_mod, ceil_mod = self.compute_size_modifiers(ability_name)

            ability_range["floor"] += floor_mod
            ability_range["ceiling"] += ceil_mod
            
            # After modifying the ability range, check for boundaries.
            ability_range = self.boundary_check(ability_range)
        
        for slider in self.gameplay_sliders:
            # Apply size alteration to the gameplay slider
            self.gameplay_sliders[slider]["current"] += self.size_alter_sliders(slider)

    def compute_age_modifiers(self, ability: str) -> float:
        """
        Ability-specific 0-to-1 modifier at the given world-age.
        • 0  → ability sitting at its lifetime floor
        • 1  → ability at its lifetime peak (≤120 yr)
        • After age 120 a universal exponential drop pushes it back down.
        """
        # Normalised age in [0,1]
        age = self.get_age()
        
        age_norm = np.clip((age - 17) / (145 - 17), 0, 1)

        # Late-life exponential (makes 120 still ≈1, 145 about 0.14)
        late = np.exp(-0.08 * max(age - 120, 0))

        kind, a, b = ABILITY_AGE_CURVES.get(
            ability, ("sigmoid", 0.50, 3.0)
        )

        # Sigmoid (growth & plateau)
        if kind == "sigmoid":
            centre, steep = a, b
            raw = 1 / (1 + np.exp(-steep * (age_norm - centre)))     # already 0-1
        else:  # Bell (peak then decline)  — a:=μ  b:=width
            μ, width = a, b
            raw = np.exp(-((age - μ) ** 2) / (2 * width ** 2))       # 0-1

        return float(raw * late)

    def size_alter_sliders(self, slider_name):
        mod = 0
        if slider_name == "Inverse Metabolic Rate":
            # bounds for clamping extremes (in inches and pounds)
            MIN_H, MAX_H = 51, 90
            MIN_W, MAX_W = 70, 500
            # neutral reference
            NEUT_H, NEUT_W = 71, 175
            # get height and weight from size
            height_inches = self.size["Height"]  # Assuming height is stored in inches
            weight_pounds = self.size["Weight"]  # Assuming weight is stored in pounds

            # normalize height: –1 at MIN_H, 0 at NEUT_H, +1 at MAX_H
            if height_inches <= NEUT_H:
                h_norm = (height_inches - NEUT_H) / (NEUT_H - MIN_H)
            else:
                h_norm = (height_inches - NEUT_H) / (MAX_H - NEUT_H)
            h_norm = max(min(h_norm, 1.0), -1.0)

            # normalize weight: –1 at MIN_W, 0 at NEUT_W, +1 at MAX_W
            if weight_pounds <= NEUT_W:
                w_norm = (weight_pounds - NEUT_W) / (NEUT_W - MIN_W)
            else:
                w_norm = (weight_pounds - NEUT_W) / (MAX_W - NEUT_W)
            w_norm = max(min(w_norm, 1.0), -1.0)

            # combine and scale: combined of +1 → –20; –1 → +20
            combined = (h_norm + w_norm) / 2.0
            mod = -combined * 20

        return mod

    def age_alter_sliders(self):
        """
        This function modifies the gameplay sliders based on the player's age.
        The age affects the gameplay sliders.
        """
        # For each slider in the player:
        for slider_name, slider_range in self.gameplay_sliders.items():
            mod_factor = self.compute_slider_age_modifiers(slider_name)
            self.gameplay_sliders[slider_name]["current"] = slider_range["floor"] + mod_factor*(slider_range["ceiling"] - slider_range["floor"])

    def compute_slider_age_modifiers(self, slider_name: str) -> float:
        """
        Compute age-based modifiers for gameplay sliders (all in [0,1]).
        """
        age = self.get_age()

        a = np.clip(age, 0.0, 145.0)
        
        if slider_name == "Learning Rate":
            mod = _lr_interp(a)
        
        elif slider_name == "Inverse Metabolic Rate":
            mod = _imr_interp(a)
        
        elif slider_name == "Inverse Sleep Cycle":
            # Simple smooth monotonic increase from 0 at age=0 to 1 at age=145
            mod = a / 145.0
        
        elif slider_name == "Memory" or slider_name == "Thinking Speed":
            mod = _mem_interp(a)
        
        else:
            # fallback
            mod = 0.5
        
        # Just in case interpolation gives tiny numerical over/undershoots:
        return float(np.clip(mod, 0.0, 1.0))
    
    def age_alter_abilities(self):
        """
        This function modifies the abilities based on the player's age.
        The age affects the floor and ceiling of the physical abilities.
        """
        # For each ability in the player:
        for ability_name, ability_range in self.abilities.items():
            mod_factor = self.compute_age_modifiers(ability_name)
            ability_range["current"] = ability_range["floor"] + mod_factor*(ability_range["ceiling"] - ability_range["floor"])
    
    def get_age(self):
        """
        This function calculates the player's age based on the birthdate and current date.
        """
        current_year, current_month, current_day = get_date()
        
        # Calculate age in years
        age_years = current_year - self.birthdate["Year"]
        
        # Adjust for month and day
        if (current_month < self.birthdate["Month"]):
            age_years -= 1
        
        return age_years

    def genetically_alter_abilities(self):
        """
        This function modifies the abilities based on the expressed genetic markers.
        Each expressed marker applies full effect; each dormant marker applies half effect.
        The GENETIC_MODIFIERS dict provides the [floor_mod, ceiling_mod] for each (ability, gene).
        """
        # For each ability in the player:
        for ability_name, ability_range in self.abilities.items():
            # Go through each gene in the player's total marker set.
            # (Expressed markers are uppercase, dormant are lowercase.)
            for marker in self.genetics.get_markers():
                gene = marker.upper()  # We'll use uppercase to look up in GENETIC_MODIFIERS
                if ability_name in GENETIC_MODIFIERS and gene in GENETIC_MODIFIERS[ability_name]:
                    floor_mod, ceil_mod = GENETIC_MODIFIERS[ability_name][gene]
                    
                    # If the marker is uppercase, apply twice the effect.
                    # If it's lowercase, apply half effect.
                    if marker.isupper():
                        ability_range["floor"] += floor_mod * 2
                        ability_range["ceiling"] += ceil_mod * 2
                    else:
                        ability_range["floor"] += floor_mod
                        ability_range["ceiling"] += ceil_mod
                        
                    # After modifying the ability range, check for boundaries.
                    ability_range = self.boundary_check(ability_range)
    
    def boundary_check(self, ability_range):
        # Enforce boundaries so floor <= ceiling and stay within [0, 99] and make any overflows go to the other side (e.g., 100 ceil -> 99 ceil, -1 to floor, -1 floor -> 0 floor, -1 to ceil).
            # Check pedantic overflows and underflows.
            if ability_range["floor"] < 0 and ability_range["ceiling"] < 1:
                ability_range["floor"] = 0
                ability_range["ceiling"] = 1
            elif ability_range["floor"] > 99 and ability_range["ceiling"] > 99:
                ability_range["floor"] = 99
                ability_range["ceiling"] = 99
            # Check for the rest of the overflows and underflows.
            elif ability_range["floor"] < 0: # Negative case
                ability_range["ceiling"] += ability_range["floor"]
                ability_range["floor"] = 0
            elif ability_range["ceiling"] > 99: # Positive case
                ability_range["floor"] += ability_range["ceiling"] - 99
                ability_range["ceiling"] = 99
            # Check if the floor is greater than the ceiling. Set them to midpoint.
            if ability_range["floor"] > ability_range["ceiling"]:
                midpoint = (ability_range["floor"] + ability_range["ceiling"]) // 2
                ability_range["floor"] = midpoint
                ability_range["ceiling"] = midpoint
            # Set the current value to the floor.
            ability_range["current"] = ability_range["floor"]
            return ability_range
    
    def impose_trait_ability_modifiers(self):
        """
        This function modifies the abilities based on the chosen traits.
        Each trait applies its own modifiers to the abilities and sliders.
        This changes the current values and floors of the abilities.
        If, after applying the trait modifiers, the current value is above the ceiling, it is set to the ceiling and the points are converted to xp for skill progression.
        If, after applying the trait modifiers, the current value is below the floor, it is set to the floor and the ceiling is moved down by the difference.
        """
        # For each trait in the player:
        k_slider = 30
        k_ability = 10
        for trait in [self.physical_trait, self.mental_trait, self.social_trait, self.livelihood_trait, self.travel_trait] + self.essence_traits_choice:
            if trait in TRAIT_MODIFIERS:
                # Apply the ability modifiers
                for ability_name, ability_mods in TRAIT_MODIFIERS[trait]["Abilities"].items():
                    self.abilities[ability_name]["current"] += ability_mods*k_ability
                    self.abilities[ability_name]["floor"] += ability_mods*k_ability
                    if self.abilities[ability_name]["current"] > self.abilities[ability_name]["ceiling"]:
                        # Convert the overflow to skill xp
                        self.skill_init_overflow ["Overflow Points"].append([self.abilities[ability_name]["current"] - self.abilities[ability_name]["ceiling"], trait, ability_name])
                        self.abilities[ability_name]["current"] = self.abilities[ability_name]["ceiling"]
                        self.abilities[ability_name]["floor"] = self.abilities[ability_name]["ceiling"]
                    # Boundary check
                    self.abilities[ability_name] = self.boundary_check(self.abilities[ability_name])
                    
                # Apply the slider modifiers
                for slider_name, slider_mod in TRAIT_MODIFIERS[trait]["Sliders"].items():
                    self.gameplay_sliders[slider_name]["current"] += slider_mod*k_slider
    
    def initialize_abilities(self):
        base_abilities = BASE_ABILITIES.copy()
        essence_abilities = ESSENCE_ABILITIES.copy()
        slider_values = SLIDER_VALUES.copy()
        for ability in base_abilities:
            self.abilities[ability] = {"floor": 0, "ceiling": 1, "current": 0}
        for essence in essence_abilities:
            self.abilities[essence] = {"floor": 0, "ceiling": 1, "current": 0}
        for slider in slider_values:
            self.gameplay_sliders[slider] = {"floor": 1, "ceiling": 99, "current": 50}

        self.genetically_alter_abilities()
        self.size_alter_abilities()
        self.impose_trait_ability_modifiers()
        for slider in self.gameplay_sliders:
            self.gameplay_sliders[slider]["floor"] = self.gameplay_sliders[slider]["current"]-10
            self.gameplay_sliders[slider]["ceiling"] = self.gameplay_sliders[slider]["current"]+10
        self.age_alter_abilities()

# ---- SKILLSET CLASS ----

class Skillset:
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.xp = 0
        self.level = 0
    
    def get_level_for_xp(self, xp_amount):
        """
        Determine the correct level for a given XP amount
        """
        # Start from level 0 and find the highest level the XP qualifies for
        level = 0
        # Check each level up to 10 (max level)
        for lvl in range(1, 11):
            # Get XP required for this level
            required_xp = SKILL_PROGRESSION_DF.loc[SKILL_PROGRESSION_DF['Level'] == lvl, 'XP Required'].values
            
            # If level exists in the table and XP is sufficient, update level
            if len(required_xp) > 0 and xp_amount >= required_xp[0]:
                level = lvl
            else:
                # Stop once we find a level we don't qualify for
                break
                
        return level
    
    def xp_to_next_level(self):
        """
        Calculate how much XP is needed to reach the next level
        """
        if self.level >= 10:  # Max level
            return None
            
        # Get XP required for next level
        next_level = self.level + 1
        required_xp = SKILL_PROGRESSION_DF.loc[SKILL_PROGRESSION_DF['Level'] == next_level, 'XP Required'].values
        
        if len(required_xp) > 0:
            return required_xp[0] - self.xp
        else:
            return None
    
    def increment_xp(self, d_xp):
        """
        Add XP and update level accordingly
        """
        # Old level for comparison
        old_level = self.level
        
        # Add XP
        self.xp += d_xp
        
        # Recalculate level based on total XP
        new_level = self.get_level_for_xp(self.xp)
        
        # If leveled up, print messages
        if new_level > old_level:
            for lvl in range(old_level + 1, new_level + 1):
                #print(f"{self.name} leveled up to level {lvl}!")
                continue
        
        self.level = new_level

    def __str__(self):
        # Display the skillset name, level, xp to next level, and description
        xp_needed = self.xp_to_next_level()
        
        if xp_needed is None:
            return f"{self.name}: Level {self.level} (Max Level Reached)\n{self.description}"
        
        # Title for the skillset level from SKILL_PROGRESSION_DF
        return f"{self.name}: {SKILL_PROGRESSION_DF['Title'][self.level]} (Level {self.level}) ({xp_needed} XP to Next Level)\n{self.description}"

# ---- Character Creation UI ----

class CharacterCreationUI:
    def __init__(self, markers, physical_traits, mental_traits, social_traits, 
                 livelihood_traits, travel_traits, essence_traits, 
                 base_abilities, essence_abilities, slider_values,
                 genetic_modifiers, trait_modifiers, skillset_ability_dependence,
                 ability_categories):

        """Initialize the character creation UI with data"""
        self.markers = markers
        self.physical_traits = physical_traits
        self.mental_traits = mental_traits
        self.social_traits = social_traits
        self.livelihood_traits = livelihood_traits
        self.travel_traits = travel_traits
        self.essence_traits = essence_traits
        self.base_abilities = base_abilities
        self.essence_abilities = essence_abilities
        self.slider_values = slider_values
        self.genetic_modifiers = genetic_modifiers
        self.trait_modifiers = trait_modifiers
        self.skillset_ability_dependence = skillset_ability_dependence
        self.ability_categories = ability_categories
        
        # Flatten the essence traits for selection
        self.all_essence_options = []
        for essence_type, traits in essence_traits.items():
            for trait_name in traits.keys():
                self.all_essence_options.append(trait_name)

        # Build one flat dict of all essence-trait names → description
        self.flat_essence_traits = {
            trait_name: trait_desc
            for traits in self.essence_traits.values()
            for trait_name, trait_desc in traits.items()
        }
        
        # Initialize session state if not already done
        self._init_session_state()
        
    def _init_session_state(self):
        """Initialize session state variables for Streamlit"""
        if 'character_name' not in st.session_state:
            st.session_state.character_name = ''
        if 'birth_year' not in st.session_state:
            st.session_state.birth_year = 860
        if 'birth_month' not in st.session_state:
            st.session_state.birth_month = 1
        if 'player_planet' not in st.session_state:
            st.session_state.player_planet = "Synvios"
        if 'mother_planet' not in st.session_state:
            st.session_state.mother_planet = "Synvios"
        if 'father_planet' not in st.session_state:
            st.session_state.father_planet = "Synvios"
        if 'mother_extra_1' not in st.session_state:
            st.session_state.mother_extra_1 = "Equilibrio"
        if 'mother_extra_2' not in st.session_state:
            st.session_state.mother_extra_2 = "Durabilis"
        if 'father_extra_1' not in st.session_state:
            st.session_state.father_extra_1 = "Equilibrio"
        if 'father_extra_2' not in st.session_state:
            st.session_state.father_extra_2 = "Durabilis"
        if 'height' not in st.session_state:
            st.session_state.height = 66
        if 'weight' not in st.session_state:
            st.session_state.weight = 150
        if 'physical_trait' not in st.session_state:
            st.session_state.physical_trait = list(self.physical_traits.keys())[0] if self.physical_traits else None
        if 'mental_trait' not in st.session_state:
            st.session_state.mental_trait = list(self.mental_traits.keys())[0] if self.mental_traits else None  
        if 'social_trait' not in st.session_state:
            st.session_state.social_trait = list(self.social_traits.keys())[0] if self.social_traits else None
        if 'livelihood_trait' not in st.session_state:
            st.session_state.livelihood_trait = list(self.livelihood_traits.keys())[0] if self.livelihood_traits else None
        if 'travel_trait' not in st.session_state:
            st.session_state.travel_trait = list(self.travel_traits.keys())[0] if self.travel_traits else None
        if 'essence_traits' not in st.session_state:
            st.session_state.essence_traits = [""] * 4
        if 'eye_color' not in st.session_state:
            # This will be set correctly in display()
            st.session_state.eye_color = ""
        if 'character_created' not in st.session_state:
            st.session_state.character_created = False
        if 'character_output' not in st.session_state:
            st.session_state.character_output = ""

class CharacterCreationUI:
    def __init__(self, markers, physical_traits, mental_traits, social_traits, 
                 livelihood_traits, travel_traits, essence_traits, 
                 base_abilities, essence_abilities, slider_values,
                 genetic_modifiers, trait_modifiers, skillset_ability_dependence,
                 ability_categories):
        
        """Initialize the character creation UI with data"""
        self.markers = markers
        self.physical_traits = physical_traits
        self.mental_traits = mental_traits
        self.social_traits = social_traits
        self.livelihood_traits = livelihood_traits
        self.travel_traits = travel_traits
        self.essence_traits = essence_traits
        self.base_abilities = base_abilities
        self.essence_abilities = essence_abilities
        self.slider_values = slider_values
        self.genetic_modifiers = genetic_modifiers
        self.trait_modifiers = trait_modifiers
        self.skillset_ability_dependence = skillset_ability_dependence
        self.ability_categories = ability_categories
        
        # Flatten the essence traits for selection
        self.all_essence_options = []
        for essence_type, traits in essence_traits.items():
            for trait_name in traits.keys():
                self.all_essence_options.append(trait_name)

        # Build one flat dict of all essence-trait names → description
        self.flat_essence_traits = {
            trait_name: trait_desc
            for traits in self.essence_traits.values()
            for trait_name, trait_desc in traits.items()
        }
        
        # Initialize session state if not already done
        self._init_session_state()
        
    def _init_session_state(self):
        """Initialize session state variables for Streamlit"""
        if 'character_name' not in st.session_state:
            st.session_state.character_name = ''
        if 'birth_year' not in st.session_state:
            st.session_state.birth_year = 860
        if 'birth_month' not in st.session_state:
            st.session_state.birth_month = 1
        if 'player_planet' not in st.session_state:
            st.session_state.player_planet = "Synvios"
        if 'mother_planet' not in st.session_state:
            st.session_state.mother_planet = "Synvios"
        if 'father_planet' not in st.session_state:
            st.session_state.father_planet = "Synvios"
        if 'mother_extra_1' not in st.session_state:
            st.session_state.mother_extra_1 = "Equilibrio"
        if 'mother_extra_2' not in st.session_state:
            st.session_state.mother_extra_2 = "Durabilis"
        if 'father_extra_1' not in st.session_state:
            st.session_state.father_extra_1 = "Equilibrio"
        if 'father_extra_2' not in st.session_state:
            st.session_state.father_extra_2 = "Durabilis"
        if 'height' not in st.session_state:
            st.session_state.height = 66
        if 'weight' not in st.session_state:
            st.session_state.weight = 150
        if 'physical_trait' not in st.session_state:
            st.session_state.physical_trait = list(self.physical_traits.keys())[0] if self.physical_traits else None
        if 'mental_trait' not in st.session_state:
            st.session_state.mental_trait = list(self.mental_traits.keys())[0] if self.mental_traits else None  
        if 'social_trait' not in st.session_state:
            st.session_state.social_trait = list(self.social_traits.keys())[0] if self.social_traits else None
        if 'livelihood_trait' not in st.session_state:
            st.session_state.livelihood_trait = list(self.livelihood_traits.keys())[0] if self.livelihood_traits else None
        if 'travel_trait' not in st.session_state:
            st.session_state.travel_trait = list(self.travel_traits.keys())[0] if self.travel_traits else None
        if 'essence_traits' not in st.session_state:
            st.session_state.essence_traits = [""] * 4
        if 'eye_color' not in st.session_state:
            # This will be set correctly in display()
            st.session_state.eye_color = ""
        if 'character_created' not in st.session_state:
            st.session_state.character_created = False
        if 'character_output' not in st.session_state:
            st.session_state.character_output = ""

    def _planet_to_essence(self, planet_name:str)->str:
        """Maps a planet name to its essence marker (uppercase for expressed)."""
        planet_map = {
            "Synvios": 'B',   # Symbiosis
            "Fortis Crags": 'D',   # Durabilis
            "Percepio": 'E',  # Equilibrio
            "Celeste": 'I',   # Sapien
            "Nexus": 'A',     # Arcanum
            "Variare": 'M',   # Metamorphosis
        }
        return planet_map[planet_name]
    
    def _essence_name_to_marker(self, essence_name:str)->str:
            essence_map = {
                "Equilibrio": 'E', 
                "Durabilis":  'D',
                "Sapien":     'I',
                "Arcanum":    'A',
                "Symbiosis":  'B',
                "Metamorphosis": 'M',
            }
            return essence_map[essence_name]
    
    def _marker_to_essence_name(self, marker)->str:
            essence_map = {
                'E': "Equilibrio",
                'D': "Durabilis",
                'I': "Sapien",
                'A': "Arcanum",
                'B': "Symbiosis",
                'M': "Metamorphosis",
            }
            return essence_map[marker.upper()]
    
    def _markers_to_planet(self, markers) -> str | None:
        """
        Convert a list/str of essence markers (e.g. ['B','b','e'] or 'Bbe')
        into the corresponding planet name.

        Returns None if it cannot decide.
        """
        # Accept both list and string inputs
        if isinstance(markers, str):
            markers = list(markers)

        if not markers:
            return None

        # Prefer the first uppercase letter; fall back to the first char
        marker = next((ch for ch in markers if ch.isupper()), markers[0]).upper()

        return {
            'B': "Synvios",       # Symbiosis
            'D': "Fortis Crags",  # Durabilis
            'E': "Percepio",      # Equilibrio
            'I': "Celeste",       # Sapien
            'A': "Nexus",         # Arcanum
            'M': "Variare",       # Metamorphosis
        }.get(marker)

    def _marker_to_colour(self, marker:str)->str:
            """Colour table used by the eye-colour question (#5)."""
            colour_map = {
                'E': "Violet",    
                'D': "Crimson", 
                'I': "Sapphire",      
                'A': "Amber",    
                'B': "Emerald",    
                'M': "Chartreuse",      
            }
            return colour_map[marker.upper()]
    
    def _colour_to_marker(self, colour:str)->str:
            """Colour table used by the eye-colour question (#5)."""
            colour_map = {
                "Violet":    'E',    
                "Crimson":   'D', 
                "Sapphire":  'I',      
                "Amber":     'A',    
                "Emerald":   'B',    
                "Chartreuse":'M',      
            }
            return colour_map[colour]
    
    def get_eye_color_options(self):
        """Get available eye color options based on genetics"""
        markers = set()

        # YOU: expressed uppercase from your birth planet
        markers.add(
            self._planet_to_essence(st.session_state.player_planet).upper()
        )

        # MOTHER: one uppercase + two dormants
        markers.add(
            self._planet_to_essence(st.session_state.mother_planet).upper()
        )
        markers.add(
            self._essence_name_to_marker(st.session_state.mother_extra_1).upper()
        )
        markers.add(
            self._essence_name_to_marker(st.session_state.mother_extra_2).upper()
        )

        # FATHER: one uppercase + two dormants
        markers.add(
            self._planet_to_essence(st.session_state.father_planet).upper()
        )
        markers.add(
            self._essence_name_to_marker(st.session_state.father_extra_1).upper()
        )
        markers.add(
            self._essence_name_to_marker(st.session_state.father_extra_2).upper()
        )

        # Build the dropdown options: "colour name (MARKER)"
        opts = [
            f"{self._marker_to_colour(m)}"
            for m in sorted(markers)
        ]
        
        return opts
            
    def validate_essence_traits(self, essence_traits):
        """Check for duplicates in essence traits"""
        # Filter out empty values
        selected_traits = [trait for trait in essence_traits if trait]
        
        # Check for duplicates
        if len(selected_traits) != len(set(selected_traits)):
            return "Duplicate essence traits selected. Please choose different traits."
        
        return None
    
    def validate_trait_requirements(self):
        """Validate that all selected traits meet their requirements"""
        requirement_issues = []
        
        # Get all currently selected traits
        selected_traits = [
            st.session_state.physical_trait,
            st.session_state.mental_trait,
            st.session_state.social_trait,
            st.session_state.livelihood_trait,
            st.session_state.travel_trait
        ]
        
        # Filter out empty values
        selected_traits = [trait for trait in selected_traits if trait]
        
        # Add selected essence traits
        selected_essence_traits = [trait for trait in st.session_state.essence_traits if trait]
        
        # Combined list of all selected traits
        all_selected_traits = selected_traits + selected_essence_traits
        
        # Check for traits with requirements
        for trait in all_selected_traits:
            if trait and "[Requires:" in trait:
                # Extract the requirement
                match = re.search(r'\[Requires: ([^\]]+)\]', trait)
                if match:
                    required_trait = match.group(1)
                    if required_trait not in all_selected_traits:
                        requirement_issues.append(f"{trait} requires {required_trait}")
        
        return requirement_issues
    
    def randomize_selections(self):
        """Randomize all selections"""
        planets = ["Synvios", "Fortis Crags", "Percepio", "Celeste", "Nexus", "Variare"]
        essences = ["Equilibrio", "Durabilis", "Sapien", "Arcanum", "Symbiosis", "Metamorphosis"]
        
        # Randomize character information
        st.session_state.player_planet = random.choice(planets)
        st.session_state.mother_planet = random.choice(planets)
        st.session_state.father_planet = random.choice(planets)
        st.session_state.mother_extra_1 = random.choice(essences)
        st.session_state.mother_extra_2 = random.choice(essences)
        st.session_state.father_extra_1 = random.choice(essences)
        st.session_state.father_extra_2 = random.choice(essences)
        
        # Generate random name
        if 'get_names_from_planet' in globals():
            # Randomize sex and get names from the selected planet
            sexes = ["Male", "Female"]
            random.shuffle(sexes)
            sex = sexes[0]
            
            # For names randomize between neutral and sex
            genders = [sex, "Neutral"]
            random.shuffle(genders)
            gender = genders[0]
            
            try:
                random_names = get_names_from_planet(planet=st.session_state.player_planet, gender=gender)
                st.session_state.character_name = random.choice(random_names)
            except:
                st.session_state.character_name = f"Character-{random.randint(100000, 999999)}"
        else:
            st.session_state.character_name = f"Character-{random.randint(100000, 999999)}"
                
        # Randomize birthdate 
        st.session_state.birth_year = random.randint(765, 867)
        st.session_state.birth_month = random.randint(1, 12)
        
        # Randomize physical traits
        self.randomize_size(sex)
        
        # Randomize traits
        if self.physical_traits:
            st.session_state.physical_trait = random.choice(list(self.physical_traits.keys()))
            
        if self.mental_traits:
            st.session_state.mental_trait = random.choice(list(self.mental_traits.keys()))
            
        if self.social_traits:
            st.session_state.social_trait = random.choice(list(self.social_traits.keys()))
            
        if self.livelihood_traits:
            st.session_state.livelihood_trait = random.choice(list(self.livelihood_traits.keys()))
            
        if self.travel_traits:
            st.session_state.travel_trait = random.choice(list(self.travel_traits.keys()))
        
        # Randomize essence traits
        self.randomize_essence_traits()
        
        # Set eye color from the updated options
        eye_color_options = self.get_eye_color_options()
        if eye_color_options:
            st.session_state.eye_color = random.choice(eye_color_options)
    
    def randomize_size(self, sex):
        """Randomize height and weight using a skewed BMI distribution."""
        # Gaussian height centered around 69 inches (5'9") with wider spread
        if sex == 'Male':
            height_mean = 69
            height_std = 5
        else:
            height_mean = 64
            height_std = 4
        height = int(random.gauss(height_mean, height_std))
        height = max(51, min(90, height))  # Clamp to realistic bounds
        st.session_state.height = height

        # Use a Beta distribution for BMI (right-skewed toward higher values)
        bmi_min = 16.0
        bmi_max = 45.0
        a, b = 2.5, 5.0  # Skewed right
        bmi_raw = np.random.beta(a, b)
        bmi = bmi_min + bmi_raw * (bmi_max - bmi_min)

        # Compute weight using BMI formula
        weight = int((bmi * height * height) / 703)
        weight = max(70, min(weight, 500))  # Clamp to legal bounds

        # Calculate weight bounds based on height
        min_weight = max(int((18.0 * height * height) / 703), 70)
        max_weight = min(int((45.0 * height * height) / 703), 500)
        
        # Set weight within bounds
        st.session_state.weight = max(min_weight, min(max_weight, weight))
    
    def randomize_essence_traits(self):
        """Randomize essence trait selections ensuring no duplicates and all requirements satisfied."""
        # Get already selected non-essence traits
        selected_traits = [
            st.session_state.physical_trait,
            st.session_state.mental_trait,
            st.session_state.social_trait,
            st.session_state.livelihood_trait,
            st.session_state.travel_trait,
        ]
        
        # Initialize essence counts from genetic profile
        selected_counts_by_essence = {'E':0, 'D':0, 'I':0, 'A':0, 'B':0, 'M':0}
        
        # Include genetic counts for additional weighting
        selected_counts_by_essence[self._planet_to_essence(st.session_state.mother_planet)] += 1
        selected_counts_by_essence[self._essence_name_to_marker(st.session_state.mother_extra_1)] += 1
        selected_counts_by_essence[self._essence_name_to_marker(st.session_state.mother_extra_2)] += 1
        selected_counts_by_essence[self._planet_to_essence(st.session_state.father_planet)] += 1
        selected_counts_by_essence[self._essence_name_to_marker(st.session_state.father_extra_1)] += 1
        selected_counts_by_essence[self._essence_name_to_marker(st.session_state.father_extra_2)] += 1
        selected_counts_by_essence[self._planet_to_essence(st.session_state.player_planet)] += 4
        
        # Add for eye colour if already set
        if st.session_state.eye_color:
            selected_counts_by_essence[self._colour_to_marker(st.session_state.eye_color)] += 1
        
        # Get all unique traits
        all_unique_traits = list(set(self.flat_essence_traits.keys()))
        selected_essences = []
        
        # Continue selecting until we have 4 traits or run out of options
        while len(selected_essences) < 4 and all_unique_traits:
            # Create weighted selection pool based on essence counts
            weighted_traits = []
            for trait in all_unique_traits:
                # Find which essence this trait belongs to
                essence_key = next((k for k, v in self.essence_traits.items() if trait in v), None)
                if essence_key:
                    # Add the trait multiple times based on its essence count
                    weight = max(1, selected_counts_by_essence[essence_key])
                    weighted_traits.extend([trait] * weight)
            
            # If no weighted traits (shouldn't happen), use original list
            if not weighted_traits:
                weighted_traits = all_unique_traits.copy()
                
            # Select a trait with probability proportional to its essence count
            trait = random.choice(weighted_traits) if weighted_traits else random.choice(all_unique_traits)
            
            # Remove the selected trait from our pool
            if trait in all_unique_traits:
                all_unique_traits.remove(trait)
            
            # Check requirements
            if "[Requires:" in trait:
                match = re.search(r'\[Requires: ([^\]]+)\]', trait)
                if match:
                    required_trait = match.group(1)
                    if required_trait not in selected_traits and required_trait not in selected_essences:
                        continue  # requirement not met
            
            # Valid trait found - add it
            selected_essences.append(trait)
            
            # Find which essence category this trait belongs to and boost its count
            essence_key = next((k for k, v in self.essence_traits.items() if trait in v), None)
            if essence_key:
                # Boost this essence type by 3 for subsequent selections
                selected_counts_by_essence[essence_key] += 3
        
        # Update session state
        st.session_state.essence_traits = selected_essences + [""] * (4 - len(selected_essences))
    
    def create_character(self):
        """Create a character based on current selections"""
        # Check if 4 essence traits are selected
        selected_essence_traits = [trait for trait in st.session_state.essence_traits if trait]
        
        if len(selected_essence_traits) != 4:
            st.error(f"Error: Please select exactly 4 Essence Traits. Currently selected: {len(selected_essence_traits)}")
            return False
        
        # Validate trait requirements
        requirement_issues = self.validate_trait_requirements()
        if requirement_issues:
            st.error("Error: Please resolve all trait requirement issues before creating the character.")
            for issue in requirement_issues:
                st.error(issue)
            return False
        
        try:
            # Build the three raw lists:
            pm = self._planet_to_essence(st.session_state.player_planet)
            planet_markers = [pm, pm, pm]

            mm = self._planet_to_essence(st.session_state.mother_planet)
            mother_markers = [
                mm,
                self._essence_name_to_marker(st.session_state.mother_extra_1),
                self._essence_name_to_marker(st.session_state.mother_extra_2)
            ]

            fm = self._planet_to_essence(st.session_state.father_planet)
            father_markers = [
                fm,
                self._essence_name_to_marker(st.session_state.father_extra_1),
                self._essence_name_to_marker(st.session_state.father_extra_2)
            ]

            # Eye-colour override:
            eye_marker = self._colour_to_marker(st.session_state.eye_color)

            # lowercase everything
            planet_markers = [m.lower() for m in planet_markers]
            mother_markers = [m.lower() for m in mother_markers]
            father_markers = [m.lower() for m in father_markers]

            # shuffle the rows so the eye override is randomized
            rows = [planet_markers, mother_markers, father_markers]
            random.shuffle(rows)

            # apply the eye-colour override to the first matching row
            eye_lc = eye_marker.lower()
            expressed_row = None
            for row in rows:
                for idx, mark in enumerate(row):
                    if mark == eye_lc:
                        row[idx] = eye_marker      # uppercase
                        expressed_row = row
                        break
                if expressed_row:
                    break
            
            # for the other two rows, uppercase one random slot
            for row in rows:
                if row is expressed_row:
                    continue
                idx = random.randrange(len(row))
                row[idx] = row[idx].upper()

            # Final cleanup: ensure each expressed marker is first in its list
            for row_ref in [planet_markers, mother_markers, father_markers]:
                row_ref.sort(key=lambda x: x.islower())  # puts the uppercase first

            # Prepare character data
            height = st.session_state.height
            weight = st.session_state.weight
            size = {"Height": height, "Weight": weight}

            # Get birthdate
            birth_year = st.session_state.birth_year
            birth_month = st.session_state.birth_month
            birthdate = {"Year": birth_year, "Month": birth_month}

            eye_color = st.session_state.eye_color
            
            # Get selected traits
            physical_trait = st.session_state.physical_trait
            mental_trait = st.session_state.mental_trait
            social_trait = st.session_state.social_trait
            livelihood_trait = st.session_state.livelihood_trait
            travel_trait = st.session_state.travel_trait
            essence_traits_choice = selected_essence_traits
            
            # Set up globals for character creation if they exist
            for global_var in ['BASE_ABILITIES', 'ESSENCE_ABILITIES', 'SLIDER_VALUES', 'GENETIC_MODIFIERS', 'ABILITY_CATEGORIES']:
                if global_var.lower() in dir(self):
                    globals()[global_var] = getattr(self, global_var.lower())
            
            # Create player name (use a default if empty)
            player_name = st.session_state.character_name or f"Character-{random.randint(100000, 999999)}"
            
            # Create and cache the character information
            output = []
            output.append(f"Character created: {player_name}")
            output.append("\nGenetics:")
            output.append(f"  Father: {''.join(father_markers)}")
            output.append(f"  Mother: {''.join(mother_markers)}")
            output.append(f"  Planet: {''.join(planet_markers)}")
            
            output.append("\nTraits:")
            output.append(f"  Physical: {physical_trait} - {self.physical_traits[physical_trait]}")
            output.append(f"  Mental: {mental_trait} - {self.mental_traits[mental_trait]}")
            output.append(f"  Social: {social_trait} - {self.social_traits[social_trait]}")
            output.append(f"  Livelihood: {livelihood_trait} - {self.livelihood_traits[livelihood_trait]}")
            output.append(f"  Travel: {travel_trait} - {self.travel_traits[travel_trait]}")
            output.append(f"  Essence: {', '.join(essence_traits_choice)}")
            
            # Store these results in session state
            st.session_state.character_output = "\n".join(output)
            st.session_state.character_created = True
            
            # Create the actual character object if Player class is available
            if 'Genetics' in globals() and 'Player' in globals():
                try:
                    genetics = Genetics(father=father_markers, mother=mother_markers, 
                                        planet=planet_markers, expression_defined=True)
                    
                    player = Player(
                        name=player_name,
                        genetics=genetics,
                        physical_trait=physical_trait,
                        mental_trait=mental_trait,
                        social_trait=social_trait,
                        livelihood_trait=livelihood_trait,
                        travel_trait=travel_trait,
                        essence_traits_choice=essence_traits_choice,
                        size=size,
                        birthdate=birthdate,
                        eye_color=eye_color,
                    )

                    save = {
                        "Name": player_name,
                        "Genetics": {"Father Markers": father_markers, 
                                     "Mother Markers": mother_markers, 
                                     "Planet Markers": planet_markers},
                        "Physical Trait": physical_trait,
                        "Mental Trait": mental_trait,
                        "Social Trait": social_trait,
                        "Livelihood Trait": livelihood_trait,
                        "Travel Trait": travel_trait,
                        "Essence Traits": essence_traits_choice,
                        "Size": size,
                        "Birthdate": birthdate,
                        "Eye Color": eye_color,
                        "SkillXP": {s.name: s.xp for s in player.skillsets}
                    }
                    st.session_state["current_save_data"] = save
                    st.session_state.character_created = True
                    
                    # Store the player object for further use
                    st.session_state.player = player
                except Exception as e:
                    st.error(f"Error creating character object: {str(e)}")
            
            return True
            
        except Exception as e:
            st.error(f"Error creating character: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
            return False
    
    def display_player_card(self):
        """Display a comprehensive, organized player card in Streamlit"""
        if 'player' not in st.session_state or not st.session_state.character_created:
            st.warning("Please create a character first!")
            return
        
        player = st.session_state.player

        # MANAGEMENT PANEL -----------------------------------------------------------
        with st.expander("Admin / XP Management", expanded=False):
            # Choose a skillset
            selectable = {s.name: s for s in player.skillsets}
            sk_name = st.selectbox("Select skillset", list(selectable.keys()))
            delta   = st.number_input("XP to add (±)", step=100, value=0)

            if st.button("Apply XP", key="xp_btn") and delta != 0:
                selectable[sk_name].increment_xp(delta)
                st.success(f"Added {delta:+} XP to {sk_name}. "
                        f"Level is now {selectable[sk_name].level}.")
        
        # Create a container with a border
        with st.container():
            # HEADER SECTION
            col1, col2 = st.columns([2, 1])
            with col1:
                st.title(f"{player.name}")
                
                # Age, height, weight in a neat format
                height_ft = player.size["Height"] // 12
                height_in = player.size["Height"] % 12
                st.subheader(f"Age: {player.get_age()} | Height: {height_ft}'{height_in}\" | Weight: {player.size['Weight']} lbs")
                st.write(f"Eye Color: {player.eye_color}")
            
            with col2:
                # Genetics display as an expandable section
                with st.expander("### Genetic Profile", expanded=False):
                    # Get essences from genetics
                    # Get the markers from the genetics object
                    # and convert them to the essence names

                    gene_counts = {"E": 0, "D": 0, "I": 0, "A": 0, "B": 0, "M": 0}
                    for set in [player.genetics.father, player.genetics.mother, player.genetics.planet]:
                        for marker in set:
                            if marker.isupper():
                                gene_counts[marker] += 2
                            else:
                                gene_counts[marker.upper()] += 1
                    
                    total = sum(gene_counts.values())
                    # Get the percentage of each essence
                    for marker, count in gene_counts.items():
                        if count > 0:
                            gene_counts[marker] = count / total
                    # Order by percentage
                    sorted_percentages = sorted(gene_counts.items(), key=lambda x: x[1], reverse=True)
                    for marker, percentage in sorted_percentages:
                        if percentage > 0:
                            # Display in a neat format
                            st.write(f"**{self._marker_to_essence_name(marker)}**")
                            # Try progress bar
                            st.progress(percentage, text =f"{percentage:.2%}")
            
            # TRAITS SECTION
            st.markdown("---")
            st.markdown("## Character Traits")
            
            # Create 3 columns for traits
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Core Traits")
                st.write(f"**{player.physical_trait}** (Physical): {self.physical_traits[player.physical_trait]}")
                st.write(f"**{player.mental_trait}** (Mental): {self.mental_traits[player.mental_trait]}")
                st.write(f"**{player.social_trait}** (Social): {self.social_traits[player.social_trait]}")
                st.write(f"**{player.livelihood_trait}** (Livelihood): {self.livelihood_traits[player.livelihood_trait]}")
                st.write(f"**{player.travel_trait}** (Travel) - {self.travel_traits[player.travel_trait]}")
            
            with col2:
                st.markdown("### Essence Traits")
                # Sort essence traits by their essence type using the ESSENCE_TRAITS dictionary
                # that is one must check the value in ESSENCE_TRAITS which matches the player.essence_traits_choice
                # get the key and go from marker to essence type
                essence_traits_sorted = sorted(player.essence_traits_choice, key=lambda x: next((k for k, v in ESSENCE_TRAITS.items() if x in v), None))
                for trait in essence_traits_sorted:
                    # Get the essence type from the trait
                    essence_type = next((k for k, v in ESSENCE_TRAITS.items() if trait in v), None)
                    essence_type_full_name = self._marker_to_essence_name(essence_type)
                    st.write(f"**{trait}** ({essence_type_full_name}): {self.flat_essence_traits[trait]}")
            
            # ABILITIES SECTION
            st.markdown("---")
            st.markdown("## Abilities")
            
            # Group abilities by category for organization
            ability_by_category = {}
            for category, abilities in ABILITY_CATEGORIES.items():
                ability_by_category[category] = [a for a in abilities if a in player.abilities]

            # Build tab labels (all the categories + our new “All Abilities Sorted”)
            tab_labels = list(ability_by_category.keys()) + ["All Abilities Sorted"]
            tabs = st.tabs(tab_labels)

            # Iterate over each tab
            for tab_label, tab in zip(tab_labels, tabs):
                with tab:
                    if tab_label != "All Abilities Sorted":
                        # the existing per-category logic
                        data = []
                        for ability in ability_by_category[tab_label]:
                            values = player.abilities[ability]
                            data.append({
                                "Ability": ability.title(),
                                "Current": int(values["current"]),
                                "Floor":   int(values["floor"]),
                                "Ceiling": int(values["ceiling"]),
                                "Range":   int(values["ceiling"] - values["floor"])
                            })
                        if data:
                            for item in data:
                                st.write(f"**{item['Ability']}**")
                                st.progress(item["Current"], text =f"{item['Current']}")
                    else:
                        # new “All Abilities Sorted” tab
                        all_data = []
                        for ability, values in player.abilities.items():
                            all_data.append({
                                "Ability": ability.title(),
                                "Current": int(values["current"]),
                                "Floor":   int(values["floor"]),
                                "Ceiling": int(values["ceiling"]),
                                "Range":   int(values["ceiling"] - values["floor"])
                            })
                        # sort descending by Current
                        all_data = sorted(all_data, key=lambda x: x["Current"], reverse=True)

                        for item in all_data:
                            st.write(f"**{item['Ability']}**")
                            st.progress(item["Current"], text =f"{item['Current']}")
            
            # GAMEPLAY SLIDERS SECTION
            if hasattr(player, 'gameplay_sliders') and player.gameplay_sliders:
                st.markdown("---")
                st.markdown("## Gameplay Sliders")
                
                slider_data = []
                for slider in player.gameplay_sliders:
                    slider_data.append({
                        "Slider": slider,
                        "Current": int(player.gameplay_sliders[slider]["current"]),
                        "Floor": int(player.gameplay_sliders[slider]["floor"]),
                        "Ceiling": int(player.gameplay_sliders[slider]["ceiling"])
                    })

                # Display sliders in order of "Inverse Metabolic Rate", "Inverse Sleep Cycle", "Thinking Speed", "Memory", "Learning Rate"
                slider_order = ["Inverse Metabolic Rate", "Inverse Sleep Cycle", "Thinking Speed", "Memory", "Learning Rate"]
                slider_data = sorted(slider_data, key=lambda x: slider_order.index(x["Slider"]) if x["Slider"] in slider_order else len(slider_order))

                if slider_data:
                    # Visual representation of sliders using Streamlit's native slider
                    for item in slider_data:
                        if item['Slider'] == "Inverse Metabolic Rate":
                            st.write("Hunger Resistance")
                        elif item['Slider'] == "Inverse Sleep Cycle":
                            st.write("Sleep Resistance")
                        else:
                            st.write(f"**{item['Slider']}**")
                        st.progress(item["Current"], text = f"{item['Current']}")
            
            # SKILLSETS SECTION
            if hasattr(player, 'skillsets') and player.skillsets:
                st.markdown("---")
                st.markdown("## Skillsets")
                
                # Create tabs for different views
                skill_tabs = st.tabs(["By Category", "By Level"])
                
                # Filter out zero-XP skillsets
                relevant_skillsets = [s for s in player.skillsets if s.xp > 0]

                with skill_tabs[0]:  # By Category
                    # Try to identify categories based on skillset names
                    categories = {}
            
                    # Categorize skills
                    for skill in relevant_skillsets:
                        
                        # Extract category from skill name given CATEGORICAL_SKILL_MAP = {"Category Name": ["Skill1", "Skill2", ...]}
                        category = next((cat for cat, skills in CATEGORICAL_SKILL_MAP.items() if skill.name in skills), "Uncategorized")

                        if category not in categories:
                            categories[category] = []
                        categories[category].append(skill)
                    
                    # Display by category
                    for category in sorted(categories.keys()):
                        st.subheader(category)
                        # Sort by level within category
                        sorted_skills = sorted(categories[category], key=lambda s: s.level, reverse=True)
                        
                        cols = st.columns(2)
                        for i, skill in enumerate(sorted_skills):
                            with cols[i % 2]:
                                with st.expander(f"{skill.name} (Level {skill.level})"):
                                    st.write(skill.description)
                                    st.progress(skill.xp/(skill.xp+skill.xp_to_next_level()), text = f"{int(skill.xp)} XP ({int(skill.xp_to_next_level())} XP to Level {skill.level + 1})")
                
                with skill_tabs[1]:  # By Level
                    # Group skillsets by level
                    by_level = {}
                    for skillset in relevant_skillsets:
                        level = skillset.level
                        if level not in by_level:
                            by_level[level] = []
                        by_level[level].append(skillset)
                    
                    # Display grouped by level, highest first
                    for level in sorted(by_level.keys(), reverse=True):
                        st.subheader(f"Level {level}")
                        for skill in by_level[level]:
                            with st.expander(f"{skill.name}"):
                                st.write(skill.description)
                                st.progress(skill.xp/(skill.xp+skill.xp_to_next_level()), text = f"{int(skill.xp)} XP ({int(skill.xp_to_next_level())} XP to Level {skill.level + 1})")

            save = st.session_state.get("current_save_data")
            if save:
                buffer = io.BytesIO(json.dumps(save, indent=2).encode("utf-8"))
                st.download_button(
                    "Download character save (JSON)",
                    data=buffer,
                    file_name=f"Harmony_{save['Name']}.json",
                    mime="application/json",
                )

    def _load_character_from_json(self, buffer: io.BytesIO) -> bool:
        """Parse a save-file and push its fields into session_state."""
        try:
            data = json.load(buffer)

            # --- Simple scalar fields --------------------------------------------------
            st.session_state.character_name  = data["Name"]
            # ------------------ Birth-planet selectors ------------------------
            st.session_state.player_planet = (
                data.get("Player Planet")                                  # new saves
                or self._markers_to_planet(data["Genetics"]["Planet Markers"])
                or "Synvios"
            )

            st.session_state.mother_planet = (
                data.get("Mother Planet")
                or self._markers_to_planet(data["Genetics"]["Mother Markers"])
                or "Synvios"
            )

            st.session_state.father_planet = (
                data.get("Father Planet")
                or self._markers_to_planet(data["Genetics"]["Father Markers"])
                or "Synvios"
            )

            st.session_state.birth_year      = data["Birthdate"]["Year"]
            st.session_state.birth_month     = data["Birthdate"]["Month"]

            st.session_state.height          = data["Size"]["Height"]
            st.session_state.weight          = data["Size"]["Weight"]
            st.session_state.eye_color       = data["Eye Color"]

            # --- Trait fields ----------------------------------------------------------
            st.session_state.physical_trait  = data["Physical Trait"]
            st.session_state.mental_trait    = data["Mental Trait"]
            st.session_state.social_trait    = data["Social Trait"]
            st.session_state.livelihood_trait= data["Livelihood Trait"]
            st.session_state.travel_trait    = data["Travel Trait"]
            st.session_state.essence_traits  = data["Essence Traits"] + [""]*(4-len(data["Essence Traits"]))

            # --- Regenerate the Player object -----------------------------------------
            self.create_character()          # reuses the existing builder

            # Restore skill-set progress
            xp_table = data.get("SkillXP", {})
            player   = st.session_state.player              # freshly rebuilt

            name_to_skill = {s.name: s for s in player.skillsets}

            for skill_name, saved_xp in xp_table.items():
                skill = name_to_skill.get(skill_name)
                if skill is None:
                    st.warning(f"Obsolete or renamed skill-set '{skill_name}' "
                            f"found in save – ignored.")
                    continue
                delta = saved_xp - skill.xp                 # bring to exact XP
                if delta:
                    skill.increment_xp(delta)
            # ------------------------------------------------------------------

            st.session_state.character_created = True
            return True
        except Exception as e:
            st.error(f"Could not load file: {e}")
            return False

    def display(self):
        """Display the UI using Streamlit"""
        st.title("Harmony Character Creator")
        
        # Create tabs for organization
        tab1, tab2, tab3, tab4 = st.tabs(["Basic Info", "Traits", "Create Character", "Results"])
        
        with tab1:
            # Character name
            st.session_state.character_name = st.text_input("Character Name", 
                                                           value=st.session_state.character_name)
            
            # Birth information
            st.header("Birth Information")
            col1, col2 = st.columns(2)
            
            with col1:
                st.session_state.birth_year = st.slider("Birth Year (Campaign begins in 885 A.A.)", 
                                                       min_value=765, max_value=867, 
                                                       value=st.session_state.birth_year)
            
            with col2:
                st.session_state.birth_month = st.slider("Birth Month", 
                                                        min_value=1, max_value=12, 
                                                        value=st.session_state.birth_month)
            
            # Calculate age
            current_year = 885
            current_month = 6
            age = current_year - st.session_state.birth_year
            if st.session_state.birth_month > current_month:
                age -= 1
            
            st.info(f"Current Age: {age} years")
            
            # Planet information
            st.header("Genetic Background")
            planets = ["Synvios", "Fortis Crags", "Percepio", "Celeste", "Nexus", "Variare"]
            essences = ["Equilibrio", "Durabilis", "Sapien", "Arcanum", "Symbiosis", "Metamorphosis"]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.session_state.player_planet = st.selectbox("Your Birth Planet", 
                                                             options=planets,
                                                             index=planets.index(st.session_state.player_planet))
                
                st.session_state.mother_planet = st.selectbox("Mother's Birth Planet", 
                                                             options=planets,
                                                             index=planets.index(st.session_state.mother_planet))
            
            with col2:
                st.session_state.father_planet = st.selectbox("Father's Birth Planet", 
                                                             options=planets,
                                                             index=planets.index(st.session_state.father_planet))
            
            # Mother's essence markers
            st.subheader("Mother's Additional Essence Markers")
            st.caption("One marker comes from her birth planet. Select two more:")
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.mother_extra_1 = st.selectbox("First Additional", 
                                                              options=essences,
                                                              index=essences.index(st.session_state.mother_extra_1))
            with col2:
                st.session_state.mother_extra_2 = st.selectbox("Second Additional", 
                                                              options=essences,
                                                              index=essences.index(st.session_state.mother_extra_2))
            
            # Father's essence markers
            st.subheader("Father's Additional Essence Markers")
            st.caption("One marker comes from his birth planet. Select two more:")
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.father_extra_1 = st.selectbox("First Additional ", 
                                                              options=essences,
                                                              index=essences.index(st.session_state.father_extra_1))
            with col2:
                st.session_state.father_extra_2 = st.selectbox("Second Additional ", 
                                                              options=essences,
                                                              index=essences.index(st.session_state.father_extra_2))
            
            # Eye color (options depend on genetic selections)
            eye_color_options = self.get_eye_color_options()
            if eye_color_options:
                # Set default eye color if none set or if current not in options
                if not st.session_state.eye_color or st.session_state.eye_color not in eye_color_options:
                    st.session_state.eye_color = eye_color_options[0]
                
                st.session_state.eye_color = st.selectbox("Eye Color", 
                                                         options=eye_color_options,
                                                         index=eye_color_options.index(st.session_state.eye_color))
            
            # Physical size
            st.header("Physical Size")
            
            col1, col2 = st.columns(2)
            with col1:
                # Height slider
                st.session_state.height = st.slider("Height (inches)", 
                                                   min_value=51, max_value=90, 
                                                   value=st.session_state.height)
                
                # Display height in feet and inches
                feet = st.session_state.height // 12
                inches = st.session_state.height % 12
                st.caption(f"Height: {feet}'{inches}\"")
            
            with col2:
                # Calculate weight bounds based on height
                height = st.session_state.height
                min_weight = max(int((18.0 * height * height) / 703), 70)
                max_weight = min(int((45.0 * height * height) / 703), 500)
                
                # Weight slider
                st.session_state.weight = st.slider("Weight (lbs)", 
                                                   min_value=min_weight, 
                                                   max_value=max_weight,
                                                   value=min(max(st.session_state.weight, min_weight), max_weight))
                
                # Calculate and display BMI
                bmi = round(st.session_state.weight * 703 / (height * height), 1)
                st.caption(f"BMI: {bmi}")
                
        with tab2:
            st.header("Trait Selection")
            
            # Basic traits
            col1, col2 = st.columns(2)
            
            with col1:
                # Physical trait
                if self.physical_traits:
                    st.session_state.physical_trait = st.selectbox("Physical Trait", 
                                                                  options=list(self.physical_traits.keys()),
                                                                  index=list(self.physical_traits.keys()).index(st.session_state.physical_trait))
                
                # Mental trait
                if self.mental_traits:
                    st.session_state.mental_trait = st.selectbox("Mental Trait", 
                                                                options=list(self.mental_traits.keys()),
                                                                index=list(self.mental_traits.keys()).index(st.session_state.mental_trait))
                
                # Social trait
                if self.social_traits:
                    st.session_state.social_trait = st.selectbox("Social Trait", 
                                                                options=list(self.social_traits.keys()),
                                                                index=list(self.social_traits.keys()).index(st.session_state.social_trait))
            
            with col2:
                # Livelihood trait
                if self.livelihood_traits:
                    st.session_state.livelihood_trait = st.selectbox("Livelihood Trait", 
                                                                    options=list(self.livelihood_traits.keys()),
                                                                    index=list(self.livelihood_traits.keys()).index(st.session_state.livelihood_trait))
                
                # Travel trait
                if self.travel_traits:
                    st.session_state.travel_trait = st.selectbox("Travel Trait", 
                                                                options=list(self.travel_traits.keys()),
                                                                index=list(self.travel_traits.keys()).index(st.session_state.travel_trait))
            
            # Essence traits section
            st.subheader("Essence Traits (select 4 different traits)")
            
            # Add dropdown for each essence trait
            essence_options = [""] + list(self.flat_essence_traits.keys())
            for i in range(4):
                # Make sure session state has a valid index or default to empty
                if (i >= len(st.session_state.essence_traits) or 
                    (st.session_state.essence_traits[i] not in essence_options)):
                    if i < len(st.session_state.essence_traits):
                        st.session_state.essence_traits[i] = ""
                    else:
                        st.session_state.essence_traits.append("")
                
                # Add the selectbox 
                trait_index = essence_options.index(st.session_state.essence_traits[i]) if st.session_state.essence_traits[i] in essence_options else 0
                st.session_state.essence_traits[i] = st.selectbox(f"Essence Trait {i+1}", 
                                                                 options=essence_options,
                                                                 index=trait_index,
                                                                 key=f"essence_{i}")
            
            # Check for duplicate essence traits
            essence_error = self.validate_essence_traits(st.session_state.essence_traits)
            if essence_error:
                st.error(essence_error)
            
            # Check trait requirements
            requirement_issues = self.validate_trait_requirements()
            if requirement_issues:
                st.error("Trait Requirement Issues:")
                for issue in requirement_issues:
                    st.error(issue)
            else:
                st.success("Requirement Status: No issues detected")
                
            # Display trait descriptions
            st.subheader("Trait Descriptions")
            
            # Physical trait description
            if st.session_state.physical_trait and st.session_state.physical_trait in self.physical_traits:
                st.write(f"**Physical - {st.session_state.physical_trait}:** {self.physical_traits[st.session_state.physical_trait]}")
            
            # Mental trait description
            if st.session_state.mental_trait and st.session_state.mental_trait in self.mental_traits:
                st.write(f"**Mental - {st.session_state.mental_trait}:** {self.mental_traits[st.session_state.mental_trait]}")
            
            # Social trait description
            if st.session_state.social_trait and st.session_state.social_trait in self.social_traits:
                st.write(f"**Social - {st.session_state.social_trait}:** {self.social_traits[st.session_state.social_trait]}")
            
            # Livelihood trait description
            if st.session_state.livelihood_trait and st.session_state.livelihood_trait in self.livelihood_traits:
                st.write(f"**Livelihood - {st.session_state.livelihood_trait}:** {self.livelihood_traits[st.session_state.livelihood_trait]}")
            
            # Travel trait description
            if st.session_state.travel_trait and st.session_state.travel_trait in self.travel_traits:
                st.write(f"**Travel - {st.session_state.travel_trait}:** {self.travel_traits[st.session_state.travel_trait]}")
            
            # Essence trait descriptions
            st.subheader("Selected Essence Traits")
            for trait in st.session_state.essence_traits:
                if trait and trait in self.flat_essence_traits:
                    st.write(f"**{trait}:** {self.flat_essence_traits[trait]}")
                    
        with tab3:
            st.header("Create or Load a Character")

            upload = st.file_uploader("Load existing save-file (JSON)", type="json")
            if upload is not None:
                if self._load_character_from_json(upload):
                    st.success("Character loaded successfully!")
            st.divider()
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Create Custom Character", use_container_width=True):
                    if self.create_character():
                        st.success("Character created successfully!")
                        # TODO: Switch to the Results tab automatically
                        st.session_state.character_created = True
                        st.rerun()
            
            with col2:
                if st.button("Create Random Character (Will Clear Selections)", use_container_width=True):
                    self.randomize_selections()
                    self.create_character()
                    st.rerun()

        with tab4:  # This is the "Results" tab
            if st.session_state.character_created:
                st.header("Character Results")
                
                # Enhanced player card display
                if 'player' in st.session_state:
                    try:
                        self.display_player_card()
                    except Exception as e:
                        st.error(f"Error displaying player card: {str(e)}")
                        st.exception(e)
                        
            else:
                st.info("Create a character to see results here.")



# Main Streamlit app
def main():
    st.set_page_config(
        page_title="Character Creator",
        page_icon="🧙",#TODO: include custom icon
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Create character creator instance
    character_creator = CharacterCreationUI(
        markers=MARKERS,
        physical_traits=PHYSICAL_TRAITS,
        mental_traits=MENTAL_TRAITS,
        social_traits=SOCIAL_TRAITS,
        livelihood_traits=LIVELIHOOD_TRAITS,
        travel_traits=TRAVEL_TRAITS,
        essence_traits=ESSENCE_TRAITS,
        base_abilities=BASE_ABILITIES,
        essence_abilities=ESSENCE_ABILITIES,
        slider_values=SLIDER_VALUES,
        genetic_modifiers=GENETIC_MODIFIERS,
        trait_modifiers=TRAIT_MODIFIERS,
        skillset_ability_dependence=SKILLSET_ABILITY_DEPENDENCE,
        ability_categories=ABILITY_CATEGORIES
    )
    
    # Display the UI
    character_creator.display()

if __name__ == "__main__":
    main()

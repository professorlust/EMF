#!/usr/bin/env python3

import sys
import datetime
import ck2parser

from collections import defaultdict

emf_path = ck2parser.rootpath / 'EMF/EMF'
sr_modifier_path = emf_path / 'common/event_modifiers/emf_sr_codegen_modifiers.txt'
sr_effect_path = emf_path / 'common/scripted_effects/emf_sr_codegen_effects.txt'
sr_trigger_path = emf_path / 'common/scripted_triggers/emf_sr_codegen_triggers.txt'
sr_holy_site_decisions_path = emf_path / 'decisions/emf_secretly_convert_to_holy_site_codegen_decisions.txt'
sr_localisation_path = emf_path / 'localisation/1_emf_sr_codegen.csv'
sr_custom_loc_path = emf_path / 'localisation/customizable_localisation/emf_sr_custom_loc_codegen.txt'

###

g_codegen_file_hdr = '''
################################################################################
# WARNING: Do NOT modify this file manually!
#
# This file is code-generated and used as a part of the implementation for the
# secret religion (SR) feature which first appeared in CKII v2.7.0.
#
# Generated by src/sr_codegen.py on: {}
################################################################################
'''.format(datetime.date.today())

###

TAB_WIDTH = 4
TAB = ' ' * TAB_WIDTH


def main():
    global g_religions, g_rg_religions_map
    
    # grab a list of religions & a map of religion_groups to their religions from the religions folder
    g_religions = []
    g_rg_religions_map = defaultdict(list)

    for _, tree in ck2parser.SimpleParser(emf_path).parse_files('common/religions/*.txt'):
        for n, v in tree:
            if n.val.endswith('_trigger'):
                continue
            for n2, v2 in v:
                if isinstance(v2, ck2parser.Obj) and n2.val not in ['color', 'male_names', 'female_names']:
                    if v2.has_pair('secret_religion', 'no'):
                        continue
                    g_religions.append(n2.val)
                    g_rg_religions_map[n.val].append(n2.val)

    # remove the old code-generated SR localisation file & then load all of localisation for vanilla & EMF
    if sr_localisation_path.exists():
        sr_localisation_path.unlink()
    loc = ck2parser.get_localisation(moddirs=(emf_path,))
    new_loc = {}

    # create SR community event modifiers
    with sr_modifier_path.open('w', encoding='cp1252', newline='\n') as f:
        print_file_header(f, 'ck2.event_modifiers')
        print_modifiers_secret_community(f, loc, new_loc)

    # generate SR scripted triggers
    with sr_trigger_path.open('w', encoding='cp1252', newline='\n') as f:
        print_file_header(f, 'ck2.scripted_triggers')
        print_trigger_has_any_religion_char_flag(f)
        print_trigger_is_in_PREVs_interesting_society(f)
        print_trigger_has_any_char_old_religion(f)
        print_trigger_has_secret_community_of_ROOT(f)
        print_trigger_can_have_new_secret_community_of_FROM(f)
        print_trigger_has_not_religion_or_community_of_ROOT_sr(f)
        print_triggers_event_desc(f)
        print_triggers_does_cult_need_DLC(f)
        print_trigger_old_religion_is_liege_sr(f)

    # generate SR scripted effects
    with sr_effect_path.open('w', encoding='cp1252', newline='\n') as f:
        print_file_header(f, 'ck2.scripted_effects')
        print_effect_set_sr_and_clr_religion_char_flag(f)
        print_effect_add_religion_char_flag(f)
        print_effect_clr_religion_char_flag(f)
        print_effect_event_target_old_religion_from_flag(f)
        print_effect_flip_secret_community_provinces(f)
        print_effect_flip_secret_community_provinces_of_PREV(f)
        print_effect_flip_secret_community_provinces_to_my_religion(f)
        print_effect_set_adopt_faith_flag_of_my_cult_on_ROOT(f)
        print_effect_adopt_faith_from_flag(f)
        print_effect_clr_adopt_faith_flag(f)
        print_effect_set_prov_flip_char_flag_of_my_cult_on_ROOT(f)
        print_effect_flip_secret_community_provinces_by_prov_flip_char_flag(f)
        print_effect_add_secret_community_to_target_province(f)
        print_effect_ai_try_to_join_society(f)

    # generate "secretly convert to this holy site's religion" decisions
    with sr_holy_site_decisions_path.open('w', encoding='cp1252', newline='\n') as f:
        print_file_header(f, 'ck2.decisions')
        print_decisions_secretly_convert_to_holy_site(f, loc, new_loc)


    with sr_custom_loc_path.open('w', encoding='cp1252', newline='\n') as f:
        print_file_header(f, 'ck2.custom_loc')
        print_custom_loc_GetTrueReligionAdherent(f, loc, new_loc)
        print_custom_loc_GetReligionAdherent(f, loc, new_loc)

    # write default SR localisation
    generate_default_sr_localisation(loc, new_loc)

    with sr_localisation_path.open('w', encoding='cp1252', newline='\n') as f:
        print('#CODE;ENGLISH;FRENCH;GERMAN;;SPANISH;;;;;;;;;x', file=f)
        for k in sorted(new_loc):
            print('{};{};;;;;;;;;;;;;x'.format(k, new_loc[k]), file=f)

    return 0


def print_file_header(f, spec=None):
    if spec:
        print('# -*- {} -*-'.format(spec), file=f)
    print(g_codegen_file_hdr, file=f)


def generate_default_sr_localisation(loc, new_loc):
    for r in g_religions:
        base_key = 'secret_religious_society_' + r
        add_loc_if_needed(loc, new_loc, base_key, 'the {} Society'.format(loc[r]))
        add_loc_if_needed(loc, new_loc, base_key + '_desc',
                          'In this society, secret followers of the {} religion try to advance their true faith and hope to one day be able to openly adopt it.'.format(loc[r]))
        add_loc_if_needed(loc, new_loc, base_key + '_leader_desc',
                          'The High Priest, leading the international effort of bringing more people into the fold.')
        add_loc_if_needed(loc, new_loc, base_key + '_currency', 'Devotion')
        add_loc_if_needed(loc, new_loc, base_key + '_rank_1_female', 'Faithful')
        add_loc_if_needed(loc, new_loc, base_key + '_rank_1_male', 'Faithful')
        add_loc_if_needed(loc, new_loc, base_key + '_rank_2_female', 'Adherent')
        add_loc_if_needed(loc, new_loc, base_key + '_rank_2_male', 'Adherent')
        add_loc_if_needed(loc, new_loc, base_key + '_rank_3_female', 'Preacher')
        add_loc_if_needed(loc, new_loc, base_key + '_rank_3_male', 'Preacher')
        add_loc_if_needed(loc, new_loc, base_key + '_rank_4_female', 'Herald')
        add_loc_if_needed(loc, new_loc, base_key + '_rank_4_male', 'Herald')


def add_loc_if_needed(loc, new_loc, key, val):
    if not loc.get(key):
        new_loc[key] = val


#### MODIFIERS ####


def print_modifiers_secret_community(f, loc, new_loc):
    for r in g_religions:
        modifier = 'secret_{}_community'.format(r)
        desc = modifier + '_desc'
        if not loc.get(modifier):
            new_loc[modifier] = 'Secret {} Community'.format(loc[r])
        if not loc.get(desc):
            new_loc[desc] = 'In secret, {0} faithfuls have organized around a small community in this province. From there it converts others, grows, and protects its own.'.format(loc[r])
        print('''\
{} = {{
    icon = 18
    is_visible = {{ society_member_of = secret_religious_society_{} }}
}}'''.format(modifier, r), file=f)


#### TRIGGERS ####


def print_trigger_has_any_religion_char_flag(f):
    print('''
emf_sr_has_any_religion_char_flag = {
    OR = {''', file=f)

    for r in g_religions:
        print(TAB*2 + 'has_character_flag = character_was_' + r, file=f)

    print(TAB + '}\n}', file=f)


def print_trigger_is_in_PREVs_interesting_society(f):
    print('''
emf_sr_is_in_PREVs_interesting_society = {
    OR = {''', file=f)

    for r in g_religions:
        print('''\
        AND = {{
            society_member_of = secret_religious_society_{0}
            PREV = {{ interested_in_society = secret_religious_society_{0} }}
        }}'''.format(r), file=f)

    print(TAB + '}\n}', file=f)


def print_trigger_has_any_char_old_religion(f):
    print('''
emf_sr_has_any_char_old_religion = {
    OR = {''', file=f)

    for r in g_religions:
        print('''\
        AND = {{
            has_character_flag = character_was_{0}
            any_character = {{ religion = {0} }}
        }}'''.format(r), file=f)

    print(TAB + '}\n}', file=f)


def print_trigger_has_secret_community_of_ROOT(f):
    print('''
# THIS = province, ROOT is in a society which correspond to a secret religious community in THIS
emf_sr_has_secret_community_of_ROOT = {
    OR = {''', file=f)

    for r in g_religions:
        print('''\
        AND = {{
            has_province_modifier = secret_{0}_community
            ROOT = {{ society_member_of = secret_religious_society_{0} }}
        }}'''.format(r), file=f)

    print(TAB + '}\n}', file=f)


def print_trigger_can_have_new_secret_community_of_FROM(f):
    print('''
# THIS = county title, FROM's secret religious society is used
emf_sr_can_have_new_secret_community_of_FROM = {
    OR = {''', file=f)

    for r in g_religions:
        print('''\
        AND = {{
            FROM = {{ society_member_of = secret_religious_society_{0} }}
            location = {{
                NOR = {{
                    religion = {0}
                    has_province_modifier = secret_{0}_community
                }}
            }}
        }}'''.format(r), file=f)

    print(TAB + '}\n}', file=f)


def print_trigger_has_not_religion_or_community_of_ROOT_sr(f):
    print('''
# THIS = province, ROOT's secret_religion is considered
emf_sr_has_not_religion_or_community_of_ROOT_sr = {
    OR = {''', file=f)

    for r in g_religions:
        print('''\
        AND = {{
            ROOT = {{ secret_religion = {0} }}
            NOR = {{
                religion = {0}
                has_province_modifier = secret_{0}_community
            }}
        }}'''.format(r), file=f)

    print(TAB + '}\n}', file=f)


# NOTE: this function does not use the auto-populated religion list, so if it changes,
# so should this function (if affected). reason: IDEK what the exact reasons for the
# vanilla groupings are, and while I've got theories, even a more dynamic solution
# would have to include some direct-coded elements (such as parent religions).
def print_triggers_event_desc(f):
    classes = {
        'christian_group_1':
            ['catholic', 'cathar', 'fraticelli', 'waldensian', 'lollard', 'nestorian', 'messalian',
            'adoptionist', 'arian', 'maronite', 'syriac'], # EMF
        'christian_group_2':
            ['orthodox', 'bogomilist', 'monothelite', 'iconoclast', 'paulician', 'miaphysite', 'monophysite',
            'apostolic', 'tondrakian'], # EMF
        'muslim_group_1':
            ['sunni', 'zikri', 'ibadi', 'kharijite', # vanilla, but moved yazidi out (ours is zoroastrian_group)
            'mahdiyya', 'nabawiyya', 'haruri'], # EMF
        'muslim_group_2':
            ['shiite', 'druze', 'hurufi',
            'waqifi', 'zaydi', 'ismaili', 'qarmatian'], # EMF
        'african_pagan_group':
            ['west_african_pagan_reformed', 'west_african_pagan',
            'east_african_pagan_reformed', 'east_african_pagan'], # EMF
    }

    for c in sorted(classes):
        print('''
emf_sr_event_desc_{} = {{
    OR = {{'''.format(c), file=f)

        for r in classes[c]:
            print(TAB*2 + 'religion = ' + r, file=f)

        print(TAB + '}\n}', file=f)


def print_triggers_does_cult_need_DLC(f):
    dlc_rgroups_map = {
        'SoI': ['muslim'],
        'SoA': ['jewish_group'],
        'TOG': ['zoroastrian_group', 'pagan_group'],
        'RoI': ['indian_group'],
    }
    dlc_religion_map = {
        'JD': ['taoist', 'bon', 'khurmazta'],
    }

    for dlc, rgroups in sorted(dlc_rgroups_map.items()):
        print('''
# THIS = character
emf_sr_does_cult_need_{} = {{
    OR = {{'''.format(dlc), file=f)

        for rg in rgroups:
            for r in g_rg_religions_map[rg]:
                print(TAB*2 + 'society_member_of = secret_religious_society_' + r, file=f)
        print(TAB + '}\n}', file=f)

    for dlc, rlist in sorted(dlc_religion_map.items()):
        print('''
# THIS = character
emf_sr_does_cult_need_{} = {{
    OR = {{'''.format(dlc), file=f)

        for r in rlist:
            print(TAB*2 + 'society_member_of = secret_religious_society_' + r, file=f)
        print(TAB + '}\n}', file=f)


def print_trigger_old_religion_is_liege_sr(f):
    print('''
emf_sr_old_religion_is_liege_sr = {
    OR = {''', file=f)

    for r in g_religions:
        print('''\
        AND = {{
            has_character_flag = character_was_{0}
            liege = {{ secret_religion = {0} }}
        }}'''.format(r), file=f)

    print(TAB + '}\n}', file=f)


#### EFFECTS ####


def print_effect_set_sr_and_clr_religion_char_flag(f):
    print('''
emf_sr_set_sr_and_clr_religion_char_flag = {''', file=f)

    for rel in g_religions:
        print('''\
    if = {{
        limit = {{
            OR = {{
                has_character_flag = character_was_{0}
                AND = {{
                    religion = {0}
                    emf_sr_has_any_religion_char_flag = no
                }}
            }}
        }}
        set_secret_religion = {0}
        clr_character_flag = character_was_{0}
        break = yes
    }}'''.format(rel), file=f)

    print('}', file=f)


def print_effect_add_religion_char_flag(f):
    print('''
emf_sr_add_religion_char_flag = {
    trigger_switch = {
        on_trigger = religion''', file=f)

    for rel in g_religions:
        print(TAB*2 + '{0} = {{ set_character_flag = character_was_{0} }}'.format(rel), file=f)

    print(TAB + '}\n}', file=f)


def print_effect_clr_religion_char_flag(f):
    print('''
emf_sr_clr_religion_char_flag = {''', file=f)

    for rel in g_religions:
        print(TAB + 'clr_character_flag = character_was_{}'.format(rel), file=f)

    print('}', file=f)


def print_effect_event_target_old_religion_from_flag(f):
    print('''
emf_sr_event_target_old_religion_from_flag = {
    trigger_switch = {
        on_trigger = has_character_flag''', file=f)

    for rel in g_religions:
        print('''\
        character_was_{0} = {{
            {0} = {{ save_event_target_as = old_religion }}
        }}'''.format(rel), file=f)

    print(TAB + '}\n}', file=f)


def print_effect_flip_secret_community_provinces(f):
    print('''
# ROOT is assumed to own the provinces which may need flipping
emf_sr_flip_secret_community_provinces = {
    trigger_switch = {
        on_trigger = society_member_of''', file=f)

    for rel in g_religions:
        print('''\
        secret_religious_society_{0} = {{
            ROOT = {{
                any_demesne_province = {{
                    limit = {{ has_province_modifier = secret_{0}_community }}
                    religion = {0}
                    remove_province_modifier = secret_{0}_community
                }}
            }}
        }}'''.format(rel), file=f)

    print(TAB + '}\n}', file=f)


def print_effect_flip_secret_community_provinces_of_PREV(f):
    print('''
# THIS = society member, PREV = owner of provinces in question
emf_sr_flip_secret_community_provinces_of_PREV = {
    trigger_switch = {
        on_trigger = society_member_of''', file=f)

    for rel in g_religions:
        print('''\
        secret_religious_society_{0} = {{
            PREV = {{
                any_demesne_province = {{
                    limit = {{ has_province_modifier = secret_{0}_community }}
                    religion = {0}
                    remove_province_modifier = secret_{0}_community
                }}
            }}
        }}'''.format(rel), file=f)

    print(TAB + '}\n}', file=f)


def print_effect_flip_secret_community_provinces_to_my_religion(f):
    print('''
# THIS owns the provinces which may need flipping, and we base the flip on THIS's religion
# NOTE: for some reason, we don't remove the secret_X_community province modifiers, however. (?!)
emf_sr_flip_secret_community_provinces_to_my_religion = {
    trigger_switch = {
        on_trigger = religion''', file=f)

    for rel in g_religions:
        print('''\
        {0} = {{
            any_demesne_province = {{
                limit = {{ has_province_modifier = secret_{0}_community }}
                religion = {0}
                # remove_province_modifier = secret_{0}_community
            }}
        }}'''.format(rel), file=f)

    print(TAB + '}\n}', file=f)


def print_effect_set_adopt_faith_flag_of_my_cult_on_ROOT(f):
    print('''
# THIS = society member
emf_sr_set_adopt_faith_flag_of_my_cult_on_ROOT = {
    trigger_switch = {
        on_trigger = society_member_of''', file=f)

    for rel in g_religions:
        print('''\
        secret_religious_society_{0} = {{
            ROOT = {{ set_character_flag = adopt_faith_{0} }}
        }}'''.format(rel), file=f)

    print(TAB + '}\n}', file=f)


def print_effect_adopt_faith_from_flag(f):
    print('''
emf_sr_adopt_faith_from_flag = {
    trigger_switch = {
        on_trigger = has_character_flag''', file=f)

    for rel in g_religions:
        print(TAB*2 + 'adopt_faith_{0} = {{ religion = {0} }}'.format(rel), file=f)

    print(TAB + '}\n}', file=f)


def print_effect_clr_adopt_faith_flag(f):
    print('''
emf_sr_clr_adopt_faith_flag = {''', file=f)

    for rel in g_religions:
        print(TAB + 'clr_character_flag = adopt_faith_' + rel, file=f)

    print('}', file=f)


def print_effect_set_prov_flip_char_flag_of_my_cult_on_ROOT(f):
    print('''
# THIS = society member
emf_sr_set_prov_flip_char_flag_of_my_cult_on_ROOT = {
    trigger_switch = {
        on_trigger = society_member_of''', file=f)

    for rel in g_religions:
        print('''\
        secret_religious_society_{0} = {{
            ROOT = {{ set_character_flag = sr_{0}_prov_flip }}
        }}'''.format(rel), file=f)

    print(TAB + '}\n}', file=f)


def print_effect_flip_secret_community_provinces_by_prov_flip_char_flag(f):
    print('''
# THIS owns the provinces which may need flipping, and we base the flip on THIS's flag sr_X_prov_flip
emf_sr_flip_secret_community_provinces_by_prov_flip_char_flag = {
    trigger_switch = {
        on_trigger = has_character_flag''', file=f)

    for rel in g_religions:
        print('''\
        sr_{0}_prov_flip = {{
            any_demesne_province = {{
                limit = {{ has_province_modifier = secret_{0}_community }}
                religion = {0}
                remove_province_modifier = secret_{0}_community
            }}
            clr_character_flag = sr_{0}_prov_flip
        }}'''.format(rel), file=f)

    print(TAB + '}\n}', file=f)


def print_effect_add_secret_community_to_target_province(f):
    print('''
# THIS's secret religion determines which type of secret community to add to event_target:target_province
emf_sr_add_secret_community_to_target_province = {
    trigger_switch = {
        on_trigger = secret_religion''', file=f)

    for rel in g_religions:
        print('''\
        {0} = {{
            event_target:target_province = {{
                add_province_modifier = {{ name = secret_{0}_community duration = -1 }}
            }}
        }}'''.format(rel), file=f)

    print(TAB + '}\n}', file=f)


def print_effect_ai_try_to_join_society(f):
    print('''
# contains most of the implementation of vanilla event MNM.10031, except with support for joining all
# secret religious cults (vanilla only supported a select few)
emf_sr_ai_try_to_join_society = {
    random_list = {
        700 = { } # Fall back dead weight
        100 = {
            trigger = {
                can_join_society = monastic_order_benedictine
            }
            modifier = {
                factor = 3
                OR = {
                    trait = zealous
                    trait = scholar
                    trait = theologian
                    trait = gardener
                    trait = monk
                    trait = nun
                    learning = 16
                    is_priest = yes
                }
            }
            join_society = monastic_order_benedictine
            emf_sr_add_random_society_influence_if_small = yes
            emf_sr_set_grandmaster_if_none = yes
        }
        100 = {
            trigger = {
                can_join_society = monastic_order_dominican
            }
            modifier = {
                factor = 3
                OR = {
                    trait = zealous
                    trait = scholar
                    trait = theologian
                    trait = gardener
                    trait = monk
                    trait = nun
                    learning = 16
                    is_priest = yes
                }
            }
            join_society = monastic_order_dominican
            emf_sr_add_random_society_influence_if_small = yes
            emf_sr_set_grandmaster_if_none = yes
        }
        100 = {
            trigger = {
                can_join_society = monastic_order_orthodox
            }
            modifier = {
                factor = 3
                OR = {
                    trait = zealous
                    trait = scholar
                    trait = theologian
                    trait = gardener
                    trait = monk
                    trait = nun
                    learning = 16
                    is_priest = yes
                }
            }
            join_society = monastic_order_orthodox
            emf_sr_add_random_society_influence_if_small = yes
            emf_sr_set_grandmaster_if_none = yes
        }
        100 = {
            trigger = {
                can_join_society = monastic_order_nestorian
            }
            modifier = {
                factor = 3
                OR = {
                    trait = zealous
                    trait = scholar
                    trait = theologian
                    trait = gardener
                    trait = monk
                    trait = nun
                    learning = 16
                    is_priest = yes
                }
            }
            join_society = monastic_order_nestorian
            emf_sr_add_random_society_influence_if_small = yes
            emf_sr_set_grandmaster_if_none = yes
        }
        100 = {
            trigger = {
                can_join_society = monastic_order_monophysite
            }
            modifier = {
                factor = 3
                OR = {
                    trait = zealous
                    trait = scholar
                    trait = theologian
                    trait = gardener
                    trait = monk
                    trait = nun
                    learning = 16
                    is_priest = yes
                }
            }
            join_society = monastic_order_monophysite
            emf_sr_add_random_society_influence_if_small = yes
            emf_sr_set_grandmaster_if_none = yes
        }
        100 = {
            trigger = {
                can_join_society = monastic_order_hindu
            }
            modifier = {
                factor = 3
                OR = {
                    trait = zealous
                    trait = scholar
                    trait = theologian
                    trait = brahmin
                    learning = 16
                    is_priest = yes
                }
            }
            join_society = monastic_order_hindu
            emf_sr_add_random_society_influence_if_small = yes
            emf_sr_set_grandmaster_if_none = yes
        }
        100 = {
            trigger = {
                can_join_society = monastic_order_buddhist
            }
            modifier = {
                factor = 3
                OR = {
                    trait = zealous
                    trait = scholar
                    trait = theologian
                    trait = brahmin
                    learning = 16
                    is_priest = yes
                }
            }
            join_society = monastic_order_buddhist
            emf_sr_add_random_society_influence_if_small = yes
            emf_sr_set_grandmaster_if_none = yes
        }
        100 = {
            trigger = {
                can_join_society = monastic_order_jain
            }
            modifier = {
                factor = 3
                OR = {
                    trait = zealous
                    trait = scholar
                    trait = theologian
                    trait = brahmin
                    learning = 16
                    is_priest = yes
                }
            }
            join_society = monastic_order_jain
            emf_sr_add_random_society_influence_if_small = yes
            emf_sr_set_grandmaster_if_none = yes
        }
        150 = {
            trigger = {
                can_join_society = hermetics
            }
            modifier = {
                factor = 5
                is_dumb_trigger = no
                OR = { 
                    learning = 12
                    trait = scholar
                    trait = erudite
                    trait = genius
                    trait = mystic
                }
            }
            modifier = {
                factor = 0
                is_landed = no
            }
            join_society = hermetics
            emf_sr_add_random_society_influence_if_small = yes
            emf_sr_set_grandmaster_if_none = yes
        }
        100 = { 
            trigger = {
                can_join_society = the_assassins
            }
            modifier = {
                factor = 0.5
                is_landed = no
            }
            modifier = {
                factor = 2
                is_landed = yes
            }
            modifier = {
                factor = 5
                NOT = { trait = decadent }
                OR = {
                    trait = zealous
                    trait = schemer
                    trait = elusive_shadow
                    trait = deceitful
                    trait = ambitious
                    intrigue = 18
                }
            }
            join_society = the_assassins
            emf_sr_add_random_society_influence_if_small = yes
            emf_sr_set_grandmaster_if_none = yes
        }
        50 = { 
            trigger = {
                can_join_society = the_satanists
            }
            modifier = {
                factor = 5
                OR = {
                    has_impious_trait_trigger = yes
                    has_vice_trigger = yes
                    trait = drunkard
                    trait = possessed
                    trait = lunatic
                }
            }
            join_society = the_satanists
            emf_sr_add_random_society_influence_if_small = yes
            emf_sr_set_grandmaster_if_none = yes
        }
        50 = { 
            trigger = {
                can_join_society = the_trollcrafters
            }
            modifier = {
                factor = 5
                OR = {
                    has_impious_trait_trigger = yes
                    has_vice_trigger = yes
                    trait = drunkard
                    trait = possessed
                    trait = lunatic
                }
            }
            join_society = the_trollcrafters
            emf_sr_add_random_society_influence_if_small = yes
            emf_sr_set_grandmaster_if_none = yes
        }
        50 = { 
            trigger = {
                can_join_society = the_cult_of_kali
            }
            modifier = {
                factor = 5
                OR = {
                    has_impious_trait_trigger = yes
                    has_vice_trigger = yes
                    trait = drunkard
                    trait = possessed
                    trait = lunatic
                }
            }
            join_society = the_cult_of_kali
            emf_sr_add_random_society_influence_if_small = yes
            emf_sr_set_grandmaster_if_none = yes
        }
        50 = { 
            trigger = {
                can_join_society = the_cold_ones
            }
            modifier = {
                factor = 5
                OR = {
                    has_impious_trait_trigger = yes
                    has_vice_trigger = yes
                    trait = drunkard
                    trait = possessed
                    trait = lunatic
                }
            }
            join_society = the_cold_ones
            emf_sr_add_random_society_influence_if_small = yes
            emf_sr_set_grandmaster_if_none = yes
        }
        50 = {
            trigger = {
                can_join_society = the_plaguebringers
            }
            modifier = {
                factor = 5
                OR = {
                    has_impious_trait_trigger = yes
                    has_vice_trigger = yes
                    trait = drunkard
                    trait = possessed
                    trait = lunatic
                }
            }
            join_society = the_plaguebringers
            emf_sr_add_random_society_influence_if_small = yes
            emf_sr_set_grandmaster_if_none = yes
        }''', file=f)

    for r in g_religions:
        print('''\
        200 = {{
            trigger = {{ can_join_society = secret_religious_society_{0} }}
            join_society = secret_religious_society_{0}
            emf_sr_add_random_society_influence_if_small = yes
            emf_sr_set_grandmaster_if_none = yes
        }}'''.format(r), file=f)

    print(TAB + '}\n}', file=f)


#### DECISIONS ####


def print_decisions_secretly_convert_to_holy_site(f, loc, new_loc):
    print('title_decisions = {', file=f)

    for rel in g_religions:
        decision = 'secretly_convert_to_{0}_holy_site'.format(rel)
        desc = decision + '_desc'
        if not loc.get(decision):
            new_loc[decision] = 'Secretly Convert to ' + loc[rel]
        if not loc.get(desc):
            new_loc[desc] = 'The §Y{0}§! pilgrims that flock to the holy site in §Y[Root.Location.GetName]§! impress me with the depth and passion of their faith. I am tempted to convert in secrecy...'.format(loc[rel])
        print('''\
    {1} = {{
        filter = owned
        ai_target_filter = self

        only_playable = yes
        
        from_potential = {{
            ai = no
            is_incapable = no
            NOT = {{ secret_religion = {0} }}
            NOT = {{ religion = {0} }}
            NOT = {{ controls_religion = yes }}
            OR = {{
                any_province = {{
                    religion = {0}
                    is_heretic = no
                }}
                any_character = {{
                    religion = {0}
                    is_heretic = no
                }}
            }}
        }}
        potential = {{
            lower_tier_than = DUKE
            owner = {{
                OR = {{
                    character = FROM
                    AND = {{
                        ROOT = {{ tier = BARON }}
                        vassal_of = FROM
                    }}
                }}
            }}
            NOT = {{ location = {{ religion = {0} }} }}
            OR = {{
                is_holy_site = {0}
                any_de_jure_vassal_title = {{
                    is_holy_site = {0}
                }}
            }}
        }}
        allow = {{
            FROM = {{
                custom_tooltip = {{
                    text = NEEDS_250_PIETY_COST
                    hidden_tooltip = {{ piety = 250 }}
                }}
                prisoner = no
                is_incapable = no
                NOT = {{ is_inaccessible_trigger = yes }}
                NOT = {{ society_member_of = secret_religious_cult }}
            }}
        }}
        effect = {{
            FROM = {{
                piety = -250
                set_secret_religion = {0}
            }}
        }}
        revoke_allowed = {{
            always = no
        }}
        ai_will_do = {{
            factor = 0
        }}
    }}'''.format(rel, decision), file=f)

    print('}', file=f)


#### CUSTOM LOCALISATION ####

g_rel_adherent_special = {
    'catholic': 'String_Catholic',
    'orthodox': 'String_Orthodox_Christian',
    'sunni': 'String_Sunni',
    'shiite': 'String_Shia',
    'jewish': 'String_Jew',
    'zoroastrian': 'String_Zoroastrian',
    'hindu': 'String_Hindu',
    'buddhist': 'String_Buddhist',
    'jain': 'String_Jain',
    'norse_pagan_reformed': 'String_Norse_Follower',
    'slavic_pagan_reformed': 'String_Slav',
    'tengri_pagan_reformed': 'String_Tengri',
    'baltic_pagan_reformed': 'String_Romuvan',
    'finnish_pagan_reformed': 'String_Suomenusko_Follower',
    'west_african_pagan_reformed': 'String_West_African',
    'zun_pagan_reformed': 'String_Zunist',
    'norse_pagan': 'String_Norse_Follower',
    'slavic_pagan': 'String_Slav',
    'tengri_pagan': 'String_Tengri',
    'baltic_pagan': 'String_Romuvan',
    'finnish_pagan': 'String_Suomenusko_Follower',
    'west_african_pagan': 'String_West_African',
    'zun_pagan': 'String_Zunist',
}


def print_custom_loc_GetTrueReligionAdherent(f, loc, new_loc):
    print('''
defined_text = {
    name = GetTrueReligionAdherent
''', file=f)

    for r in g_religions:
        print('''\
    text = {{
        localisation_key = {}
        trigger = {{ true_religion = {} }}
    }}'''.format(g_rel_adherent_special.get(r, r), r), file=f)

    print('}', file=f)

def print_custom_loc_GetReligionAdherent(f, loc, new_loc):
    print('''
defined_text = {
    name = GetReligionAdherent
''', file=f)

    for r in g_religions:
        print('''\
    text = {{
        localisation_key = {}
        trigger = {{ religion = {} }}
    }}'''.format(g_rel_adherent_special.get(r, r), r), file=f)

    print('}', file=f)


if __name__ == '__main__':
    sys.exit(main())

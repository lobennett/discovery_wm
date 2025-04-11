# Define regressor configurations
regressor_config = {
    "cuedTS": {
        "omission": {
            "amplitude_column": "omission",
            "duration_column": "constant_1_column",
            "subset": "trial_type != 'tn/a_cn/a'",
        },
        "commission": {
            "amplitude_column": "commission",
            "duration_column": "constant_1_column",
            "subset": "trial_type != 'tn/a_cn/a'",
        },
        "rt_fast": {
            "amplitude_column": "rt_fast",
            "duration_column": "constant_1_column",
            "subset": "trial_type != 'tn/a_cn/a'",
        },
        "n/a": {
            "amplitude_column": "constant_1_column",
            "duration_column": "constant_1_column",
            "subset": "trial_type == 'tn/a_cn/a'",
        },
        "task_stay_cue_switch": {
            "amplitude_column": "constant_1_column",
            "duration_column": "constant_1_column",
            "subset": (
                "key_press == correct_response and response_time >= 0.2 "
                "and trial_type == 'tstay_cswitch'"
            ),
        },
        "task_stay_cue_stay": {
            "amplitude_column": "constant_1_column",
            "duration_column": "constant_1_column",
            "subset": (
                "key_press == correct_response and response_time >= 0.2 "
                "and trial_type == 'tstay_cstay'"
            ),
        },
        "task_switch_cue_switch": {
            "amplitude_column": "constant_1_column",
            "duration_column": "constant_1_column",
            "subset": (
                "key_press == correct_response and response_time >= 0.2 "
                "and trial_type == 'tswitch_cswitch'"
            ),
        },
        "response_time": {
            "amplitude_column": "response_time_centered",
            "duration_column": "constant_1_column",
            "subset": (
                "key_press == correct_response and response_time >= 0.2 "
                "and trial_type != 'tn/a_cn/a' and trial_id == 'test_trial'"
            ),
        }
    },
    "directedForgetting": {
        "omission": {
            "amplitude_column": "omission",
            "duration_column": "constant_1_column",
            "subset": None,
        },
        "commission": {
            "amplitude_column": "commission",
            "duration_column": "constant_1_column",
            "subset": None,
        },
        "rt_fast": {
            "amplitude_column": "rt_fast",
            "duration_column": "constant_1_column",
            "subset": None,
        },
        "memory_and_cue": {
            "amplitude_column": "constant_1_column",
            "duration_column": "duration",
            "subset": 'trial_id == "test_stim" or trial_id == "test_cue"',
        },
        "con": {
            "amplitude_column": "constant_1_column",
            "duration_column": "constant_1_column",
            "subset": (
                'key_press == correct_response and response_time >= 0.2 '
                'and trial_type == "con"'
            ),
        },
        "pos": {
            "amplitude_column": "constant_1_column",
            "duration_column": "constant_1_column",
            "subset": (
                'key_press == correct_response and response_time >= 0.2 '
                'and trial_type == "pos"'
            ),
        },
        "neg": {
            "amplitude_column": "constant_1_column",
            "duration_column": "constant_1_column",
            "subset": (
                'key_press == correct_response and response_time >= 0.2 '
                'and trial_type == "neg"'
            ),
        },
        "response_time": {
            "amplitude_column": "response_time_centered",
            "duration_column": "constant_1_column",
            "subset": (
                "key_press == correct_response and response_time >= 0.2 "
                "and trial_id == 'test_trial'"
            ),
        }
    },
    "flanker": {
        "omission": {
            "amplitude_column": "omission",
            "duration_column": "constant_1_column",
            "subset": None,
        },
        "commission": {
            "amplitude_column": "commission",
            "duration_column": "constant_1_column",
            "subset": None,
        },
        "rt_fast": {
            "amplitude_column": "rt_fast",
            "duration_column": "constant_1_column",
            "subset": None,
        },
        "congruent": {
            "amplitude_column": "constant_1_column",
            "duration_column": "constant_1_column",
            "subset": (
                "key_press == correct_response and response_time >= 0.2 "
                "and trial_type =='congruent'"
            ),
        },
        "incongruent": {
            "amplitude_column": "constant_1_column",
            "duration_column": "constant_1_column",
            "subset": (
                "key_press == correct_response and response_time >= 0.2 "
                "and trial_type =='incongruent'"
            ),
        },
        "response_time": {
            "amplitude_column": "response_time_centered",
            "duration_column": "constant_1_column",
            "subset": (
                "key_press == correct_response and response_time >= 0.2 "
                "and trial_id == 'test_trial'"
            ),
        }
    },
    "goNogo": {
        "go_omission": {
            "amplitude_column": "omission",
            "duration_column": "constant_1_column",
            "subset": None,
        },
        "go_commission": {
            "amplitude_column": "commission",
            "duration_column": "constant_1_column",
            "subset": None,
        },
        "go_rt_fast": {
            "amplitude_column": "rt_fast",
            "duration_column": "constant_1_column",
            "subset": None,
        },
        "nogo_failure": {
            "amplitude_column": "constant_1_column",
            "duration_column": "constant_1_column",
            "subset": "trial_type == 'nogo_failure'",
        },
        "go": {
            "amplitude_column": "constant_1_column",
            "duration_column": "constant_1_column",
            "subset": (
                "trial_id == 'test_trial' and "
                "key_press == correct_response and response_time >= 0.2 "
                "and trial_type == 'go'"
            ),
        },
        "nogo_success": {
            "amplitude_column": "constant_1_column",
            "duration_column": "constant_1_column",
            "subset": "trial_type == 'nogo_success'",
        },
        "response_time": {
            "amplitude_column": "response_time_centered",
            "duration_column": "constant_1_column",
            "subset": (
                "key_press == correct_response and response_time >= 0.2 "
                "and trial_type == 'go'"
            ),
        }
    },
    "nBack": {
        "omission": {
            "amplitude_column": "omission",
            "duration_column": "constant_1_column",
            "subset": "trial_type != 'n/a'",
        },
        "commission": {
            "amplitude_column": "commission",
            "duration_column": "constant_1_column",
            "subset": "trial_type != 'n/a'",
        },
        "rt_fast": {
            "amplitude_column": "rt_fast",
            "duration_column": "constant_1_column",
            "subset": "trial_type != 'n/a'",
        },
        "mismatch_1back": {
            "amplitude_column": "constant_1_column",
            "duration_column": "constant_1_column",
            "subset": (
                "key_press == correct_response and response_time >= 0.2 "
                "and trial_type == 'mismatch' and delay == 1"
            ),
        },
        "match_1back": {
            "amplitude_column": "constant_1_column",
            "duration_column": "constant_1_column",
            "subset": (
                "key_press == correct_response and response_time >= 0.2 "
                "and trial_type == 'match' and delay == 1"
            ),
        },
        "mismatch_2back": {
            "amplitude_column": "constant_1_column",
            "duration_column": "constant_1_column",
            "subset": (
                "key_press == correct_response and response_time >= 0.2 "
                "and trial_type == 'mismatch' and delay == 2"
            ),
        },
        "match_2back": {
            "amplitude_column": "constant_1_column",
            "duration_column": "constant_1_column",
            "subset": (
                "key_press == correct_response and response_time >= 0.2 "
                "and trial_type == 'match' and delay == 2"
            ),
        },
        "response_time": {
            "amplitude_column": "response_time_centered",
            "duration_column": "constant_1_column",
            "subset": (
                "key_press == correct_response and response_time >= 0.2 "
                "and trial_type != 'n/a'"
            ),
        }
    },
    "stopSignal": {
        "go_omission": {
            "amplitude_column": "omission",
            "duration_column": "constant_1_column",
            "subset": None,
        },
        "go_commission": {
            "amplitude_column": "commission",
            "duration_column": "constant_1_column",
            "subset": None,
        },
        "go_rt_fast": {
            "amplitude_column": "rt_fast",
            "duration_column": "constant_1_column",
            "subset": None,
        },
        "go": {
            "amplitude_column": "constant_1_column",
            "duration_column": "constant_1_column",
            "subset": (
                "trial_id == 'test_trial' and "
                "key_press == correct_response and response_time >= 0.2 "
                "and trial_type == 'go'"
            ),
        },
        "stop_success": {
            "amplitude_column": "constant_1_column",
            "duration_column": "constant_1_column",
            "subset": "trial_type == 'stop_success'",
        },
        "stop_failure": {
            "amplitude_column": "constant_1_column",
            "duration_column": "constant_1_column",
            "subset": "trial_type == 'stop_failure'",
        },
        "response_time": {
            "amplitude_column": "response_time_centered",
            "duration_column": "constant_1_column",
            "subset": (
                "key_press == correct_response and response_time >= 0.2 "
                "and trial_type == 'go'"
            ),
        }
    },
    "shapeMatching": {
        "omission": {
            "amplitude_column": "omission",
            "duration_column": "constant_1_column",
            "subset": None,
        },
        "commission": {
            "amplitude_column": "commission",
            "duration_column": "constant_1_column",
            "subset": None,
        },
        "rt_fast": {
            "amplitude_column": "rt_fast",
            "duration_column": "constant_1_column",
            "subset": None,
        },
        "SSS": {
            "amplitude_column": "constant_1_column",
            "duration_column": "constant_1_column",
            "subset": (
                "key_press == correct_response and response_time >= 0.2 "
                "and trial_type == 'SSS'"
            ),
        },
        "SDD": {
            "amplitude_column": "constant_1_column",
            "duration_column": "constant_1_column",
            "subset": (
                "key_press == correct_response and response_time >= 0.2 "
                "and trial_type == 'SDD'"
            ),
        },
        "SNN": {
            "amplitude_column": "constant_1_column",
            "duration_column": "constant_1_column",
            "subset": (
                "key_press == correct_response and response_time >= 0.2 "
                "and trial_type == 'SNN'"
            ),
        },
        "DSD": {
            "amplitude_column": "constant_1_column",
            "duration_column": "constant_1_column",
            "subset": (
                "key_press == correct_response and response_time >= 0.2 "
                "and trial_type == 'DSD'"
            ),
        },
        "DNN": {
            "amplitude_column": "constant_1_column",
            "duration_column": "constant_1_column",
            "subset": (
                "key_press == correct_response and response_time >= 0.2 "
                "and trial_type == 'DNN'"
            ),
        },
        "DDD": {
            "amplitude_column": "constant_1_column",
            "duration_column": "constant_1_column",
            "subset": (
                "key_press == correct_response and response_time >= 0.2 "
                "and trial_type == 'DDD'"
            ),
        },
        "DDS": {
            "amplitude_column": "constant_1_column",
            "duration_column": "constant_1_column",
            "subset": (
                "key_press == correct_response and response_time >= 0.2 "
                "and trial_type == 'DDS'"
            ),
        },
        "response_time": {
            "amplitude_column": "response_time_centered",
            "duration_column": "constant_1_column",
            "subset": (
                "key_press == correct_response and response_time >= 0.2 "
                "and trial_id == 'test_trial'"
            ),
        }
    },
    "spatialTS": {
        "omission": {
            "amplitude_column": "omission",
            "duration_column": "constant_1_column",
            "subset": "trial_type != 'n/a'",
        },
        "commission": {
            "amplitude_column": "commission",
            "duration_column": "constant_1_column",
            "subset": "trial_type != 'n/a'",
        },
        "rt_fast": {
            "amplitude_column": "rt_fast",
            "duration_column": "constant_1_column",
            "subset": "trial_type != 'n/a'",
        },
        "task_stay_cue_switch": {
            "amplitude_column": "constant_1_column",
            "duration_column": "constant_1_column",
            "subset": (
                "key_press == correct_response and response_time >= 0.2 "
                "and trial_type == 'tstay_cswitch'"
            ),
        },
        "task_stay_cue_stay": {
            "amplitude_column": "constant_1_column",
            "duration_column": "constant_1_column",
            "subset": (
                "key_press == correct_response and response_time >= 0.2 "
                "and trial_type == 'tstay_cstay'"
            ),
        },
        "task_switch_cue_switch": {
            "amplitude_column": "constant_1_column",
            "duration_column": "constant_1_column",
            "subset": (
                "key_press == correct_response and response_time >= 0.2 "
                "and trial_type == 'tswitch_cswitch'"
            ),
        },
        "response_time": {
            "amplitude_column": "response_time_centered",
            "duration_column": "constant_1_column",
            "subset": (
                "key_press == correct_response and response_time >= 0.2 "
                "and trial_type != 'n/a'"
            ),
        }
    },
}

contrasts_config = {
    # BASE TASKS
    "cuedTS": {
        "task_switch_cost": "task_switch_cue_switch-task_stay_cue_switch",
        "cue_switch_cost": "task_stay_cue_switch-task_stay_cue_stay",
        "task_switch_cue_switch-task_stay_cue_stay": (
            "task_switch_cue_switch-task_stay_cue_stay"
        ),
        "task-baseline": (
            "1/3*(task_stay_cue_switch+task_stay_cue_stay+"
            "task_switch_cue_switch)"
        ),
        "response_time": "response_time"
    },
    "directedForgetting": {
        "neg-con": "neg-con",
        "task-baseline": "1/4*(con+pos+neg+memory_and_cue)",
        "response_time": "response_time"
    },
    "flanker": {
        "incongruent-congruent": "incongruent-congruent",
        "task-baseline": "1/2*congruent + 1/2*incongruent",
        "response_time": "response_time"
    },
    "goNogo": {
        "go": "go",
        "nogo_success": "nogo_success",
        "nogo_success-go": "nogo_success-go",
        "task-baseline": "1/2*go+1/2*nogo_success",
        "response_time": "response_time"
    },
    "nBack": {
        "twoBack-oneBack": (
            "1/2*(mismatch_2back+match_2back-mismatch_1back-match_1back)"
        ),
        "match-mismatch": (
            "1/2*(match_2back+match_1back-mismatch_2back-mismatch_1back)"
        ),
        "task-baseline": (
            "1/4*(mismatch_1back+match_1back+mismatch_2back+match_2back)"
        ),
        "response_time": "response_time"
    },
    "stopSignal": {
        "go": "go",
        "stop_success": "stop_success",
        "stop_failure": "stop_failure",
        "stop_success-go": "stop_success-go",
        "stop_failure-go": "stop_failure-go",
        "stop_success-stop_failure": "stop_success-stop_failure",
        "stop_failure-stop_success": "stop_failure-stop_success",
        "task-baseline": "1/3*go + 1/3*stop_failure + 1/3*stop_success",
        "response_time": "response_time"
    },
    "shapeMatching": {
        "task-baseline": "1/7*(SSS+SDD+SNN+DSD+DDD+DDS+DNN)",
        "main_vars": "1/3*(SDD+DDD+DDS)-1/2*(SNN+DNN)",
        "SSS": "SSS",
        "SDD": "SDD",
        "SNN": "SNN",
        "DSD": "DSD",
        "DDD": "DDD",
        "DDS": "DDS",
        "DNN": "DNN",
        "response_time": "response_time"
    },
    "spatialTS": {
        "task_switch_cost": "task_switch_cue_switch-task_stay_cue_switch",
        "cue_switch_cost": "task_stay_cue_switch-task_stay_cue_stay",
        "task_switch_cue_switch-task_stay_cue_stay": (
            "task_switch_cue_switch-task_stay_cue_stay"
        ),
        "task-baseline": (
            "1/3*(task_stay_cue_switch+task_stay_cue_stay+"
            "task_switch_cue_switch)"
        ),
        "response_time": "response_time"
    }
}

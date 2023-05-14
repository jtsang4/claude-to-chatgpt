models_list = [
    {
        "id": "gpt-3.5-turbo",
        "object": "model",
        "created": 1677610602,
        "owned_by": "openai",
        "permission": [
            {
                "id": "modelperm-YO9wdQnaovI4GD1HLV59M0AV",
                "object": "model_permission",
                "created": 1683753011,
                "allow_create_engine": False,
                "allow_sampling": True,
                "allow_logprobs": True,
                "allow_search_indices": False,
                "allow_view": True,
                "allow_fine_tuning": False,
                "organization": "*",
                "group": None,
                "is_blocking": False,
            }
        ],
        "root": "gpt-3.5-turbo",
        "parent": None,
    },
    {
        "id": "gpt-3.5-turbo-0301",
        "object": "model",
        "created": 1677649963,
        "owned_by": "openai",
        "permission": [
            {
                "id": "modelperm-tsdKKNwiNtHfnKWWTkKChjoo",
                "object": "model_permission",
                "created": 1683753015,
                "allow_create_engine": False,
                "allow_sampling": True,
                "allow_logprobs": True,
                "allow_search_indices": False,
                "allow_view": True,
                "allow_fine_tuning": False,
                "organization": "*",
                "group": None,
                "is_blocking": False,
            }
        ],
        "root": "gpt-3.5-turbo-0301",
        "parent": None,
    },
    {
        "id": "gpt-4",
        "object": "model",
        "created": 1678604602,
        "owned_by": "openai",
        "permission": [
            {
                "id": "modelperm-nqKDpzYoZMlqbIltZojY48n9",
                "object": "model_permission",
                "created": 1683768705,
                "allow_create_engine": False,
                "allow_sampling": False,
                "allow_logprobs": False,
                "allow_search_indices": False,
                "allow_view": False,
                "allow_fine_tuning": False,
                "organization": "*",
                "group": None,
                "is_blocking": False,
            }
        ],
        "root": "gpt-4",
        "parent": None,
    },
    {
        "id": "gpt-4-0314",
        "object": "model",
        "created": 1678604601,
        "owned_by": "openai",
        "permission": [
            {
                "id": "modelperm-PGbNkIIZZLRipow1uFL0LCvV",
                "object": "model_permission",
                "created": 1683768678,
                "allow_create_engine": False,
                "allow_sampling": False,
                "allow_logprobs": False,
                "allow_search_indices": False,
                "allow_view": False,
                "allow_fine_tuning": False,
                "organization": "*",
                "group": None,
                "is_blocking": False,
            }
        ],
        "root": "gpt-4-0314",
        "parent": None,
    },
]

model_map = {
    "gpt-3.5-turbo": "claude-v1.3",
    "gpt-3.5-turbo-0301": "claude-v1.3",
    "gpt-4": "claude-v1.3-100k",
    "gpt-4-0314": "claude-v1.3-100k",
}

def exclude_empty_values(dict):
    return {k: v for k, v in dict.items() if v}

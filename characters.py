CHARACTERS = [
    {"name": "Alex",    "gender": "male",   "hair_color": "brown",  "hair_type": "straight", "eye_color": "brown", "has_glasses": False, "has_hat": False, "has_beard": False, "has_mustache": False, "skin_tone": "light"},
    {"name": "Ana",     "gender": "female", "hair_color": "blonde", "hair_type": "straight", "eye_color": "blue",  "has_glasses": False, "has_hat": False, "has_beard": False, "has_mustache": False, "skin_tone": "light"},
    {"name": "Ben",     "gender": "male",   "hair_color": "black",  "hair_type": "straight", "eye_color": "brown", "has_glasses": True,  "has_hat": False, "has_beard": False, "has_mustache": False, "skin_tone": "medium"},
    {"name": "Clara",   "gender": "female", "hair_color": "red",    "hair_type": "curly",    "eye_color": "green", "has_glasses": False, "has_hat": False, "has_beard": False, "has_mustache": False, "skin_tone": "light"},
    {"name": "David",   "gender": "male",   "hair_color": "brown",  "hair_type": "curly",    "eye_color": "blue",  "has_glasses": True,  "has_hat": False, "has_beard": True,  "has_mustache": False, "skin_tone": "light"},
    {"name": "Elena",   "gender": "female", "hair_color": "black",  "hair_type": "straight", "eye_color": "brown", "has_glasses": False, "has_hat": True,  "has_beard": False, "has_mustache": False, "skin_tone": "dark"},
    {"name": "Frank",   "gender": "male",   "hair_color": "white",  "hair_type": "straight", "eye_color": "blue",  "has_glasses": True,  "has_hat": False, "has_beard": True,  "has_mustache": True,  "skin_tone": "light"},
    {"name": "Grace",   "gender": "female", "hair_color": "blonde", "hair_type": "curly",    "eye_color": "green", "has_glasses": False, "has_hat": True,  "has_beard": False, "has_mustache": False, "skin_tone": "light"},
    {"name": "Hector",  "gender": "male",   "hair_color": "black",  "hair_type": "straight", "eye_color": "brown", "has_glasses": False, "has_hat": True,  "has_beard": True,  "has_mustache": False, "skin_tone": "dark"},
    {"name": "Iris",    "gender": "female", "hair_color": "brown",  "hair_type": "straight", "eye_color": "green", "has_glasses": True,  "has_hat": False, "has_beard": False, "has_mustache": False, "skin_tone": "medium"},
    {"name": "Jake",    "gender": "male",   "hair_color": "blonde", "hair_type": "straight", "eye_color": "blue",  "has_glasses": False, "has_hat": False, "has_beard": False, "has_mustache": True,  "skin_tone": "light"},
    {"name": "Karen",   "gender": "female", "hair_color": "red",    "hair_type": "straight", "eye_color": "brown", "has_glasses": True,  "has_hat": False, "has_beard": False, "has_mustache": False, "skin_tone": "medium"},
    {"name": "Leo",     "gender": "male",   "hair_color": "none",   "hair_type": "bald",     "eye_color": "brown", "has_glasses": False, "has_hat": False, "has_beard": True,  "has_mustache": True,  "skin_tone": "dark"},
    {"name": "Maya",    "gender": "female", "hair_color": "black",  "hair_type": "curly",    "eye_color": "brown", "has_glasses": False, "has_hat": False, "has_beard": False, "has_mustache": False, "skin_tone": "dark"},
    {"name": "Nick",    "gender": "male",   "hair_color": "brown",  "hair_type": "straight", "eye_color": "blue",  "has_glasses": True,  "has_hat": True,  "has_beard": False, "has_mustache": False, "skin_tone": "light"},
    {"name": "Olivia",  "gender": "female", "hair_color": "blonde", "hair_type": "straight", "eye_color": "blue",  "has_glasses": False, "has_hat": False, "has_beard": False, "has_mustache": False, "skin_tone": "light"},
    {"name": "Paul",    "gender": "male",   "hair_color": "red",    "hair_type": "curly",    "eye_color": "green", "has_glasses": False, "has_hat": False, "has_beard": True,  "has_mustache": False, "skin_tone": "light"},
    {"name": "Quinn",   "gender": "female", "hair_color": "white",  "hair_type": "straight", "eye_color": "blue",  "has_glasses": True,  "has_hat": False, "has_beard": False, "has_mustache": False, "skin_tone": "light"},
    {"name": "Ryan",    "gender": "male",   "hair_color": "black",  "hair_type": "straight", "eye_color": "green", "has_glasses": False, "has_hat": False, "has_beard": False, "has_mustache": True,  "skin_tone": "medium"},
    {"name": "Sofia",   "gender": "female", "hair_color": "brown",  "hair_type": "curly",    "eye_color": "brown", "has_glasses": False, "has_hat": True,  "has_beard": False, "has_mustache": False, "skin_tone": "medium"},
    {"name": "Tom",     "gender": "male",   "hair_color": "blonde", "hair_type": "straight", "eye_color": "brown", "has_glasses": True,  "has_hat": False, "has_beard": False, "has_mustache": False, "skin_tone": "light"},
    {"name": "Uma",     "gender": "female", "hair_color": "black",  "hair_type": "straight", "eye_color": "blue",  "has_glasses": False, "has_hat": False, "has_beard": False, "has_mustache": False, "skin_tone": "dark"},
    {"name": "Victor",  "gender": "male",   "hair_color": "none",   "hair_type": "bald",     "eye_color": "brown", "has_glasses": True,  "has_hat": False, "has_beard": False, "has_mustache": True,  "skin_tone": "medium"},
    {"name": "Wendy",   "gender": "female", "hair_color": "red",    "hair_type": "curly",    "eye_color": "green", "has_glasses": False, "has_hat": True,  "has_beard": False, "has_mustache": False, "skin_tone": "light"},
]

VALID_ATTRIBUTES = {
    "gender":        ["male", "female"],
    "hair_color":    ["black", "brown", "blonde", "red", "white", "none"],
    "hair_type":     ["straight", "curly", "bald"],
    "eye_color":     ["brown", "blue", "green"],
    "has_glasses":   [True, False],
    "has_hat":       [True, False],
    "has_beard":     [True, False],
    "has_mustache":  [True, False],
    "skin_tone":     ["light", "medium", "dark"],
}

CHARACTER_NAMES = [c["name"] for c in CHARACTERS]

def get_character(name: str) -> dict | None:
    return next((c for c in CHARACTERS if c["name"] == name), None)

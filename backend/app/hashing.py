from hashlib import sha256

def mock_hashfunc(string: str) -> str:
    salt = 'Very salty'
    return sha256((string + salt).encode('utf-8')).hexdigest()


def hash_string(string: str) -> str:
    raise NotImplementedError()


hash_string = mock_hashfunc
# raise RuntimeWarning("You are using a mock hashing function that is publicly available " +
#                      "on the repository.")
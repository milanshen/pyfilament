FUNC_REGISTRY = {}


def lookup_func(func_address):
    if func_address in FUNC_REGISTRY:
        return FUNC_REGISTRY[func_address]
    module_name, func_name = func_address.split(":")
    module = __import__(module_name, fromlist=[func_name])
    func = getattr(module, func_name)
    FUNC_REGISTRY[func_address] = func
    return func


def register_func(func):
    func_address = get_func_address(func)
    if func_address in FUNC_REGISTRY:
        return func_address
    FUNC_REGISTRY[func_address] = func
    return func_address


def get_func_address(func):
    func_address = f"{func.__module__}:{func.__name__}"
    return func_address

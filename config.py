import yaml

def singleton(cls):
    __instance = {}
    def wrapper(*args, **kwargs):
        if cls not in __instance:
            __instance[cls] = cls(*args, **kwargs)
            return __instance[cls]
        else:
            return __instance[cls]
    return wrapper

@singleton
class Config:         
    def __init__(self):
        with open('project.yaml', 'r', encoding='utf-8') as f:
            self.env = yaml.load(f.read(), Loader=yaml.FullLoader)
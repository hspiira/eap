from cuid2 import cuid_wrapper

cuid_generator = cuid_wrapper()


def generate_cuid() -> str:
    """Generate a collision-resistant unique identifier"""
    return cuid_generator()

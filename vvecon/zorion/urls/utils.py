__all__ = ['generateGETString']


def generateGETString(data: dict) -> str:
    """
	Generates the GET string from the given data
	:param data: The data to be converted
	:type data: dict
	:return: The GET string
	:rtype: str
	"""
    getString = ''
    for key, value in data.items():
        if isinstance(value, list):
            for val in value:
                getString += f'{key}[]={val}&'
        else:
            getString += f'{key}={value}&'
    return getString[:-1]

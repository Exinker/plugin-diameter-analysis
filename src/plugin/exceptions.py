import logging
from functools import wraps

LOGGER = logging.getLogger('plugin-diameter-analysis')


def get_initial_exception(error: Exception) -> Exception:

    parent = error.__cause__ or error.__context__
    if parent is None:
        return error

    return get_initial_exception(parent)


def exception_wrapper(func):

    @wraps(func)
    def wrapped(*args, **kwargs):

        try:
            result = func(*args, **kwargs)

        except Exception as error:
            LOGGER.warning(
                'Plugin ware not refreshed successfully!',
                exc_info=True,
            )
            raise get_initial_exception(error)

        else:
            LOGGER.info('Plugin are refreshed!')
            return result

    return wrapped


class PluginError(Exception):
    pass

import functools


def Debounce(threshold=100, print_status=True):
    """
    Simple debouncing decorator for apigpio callbacks.
    Unlike the apigpio version this one works per gpio pin, not per callback fn
    So you can share a callback for multiple pins and not debounce between them

    Example:

    `@Debouncer()
     def my_cb(gpio, level, tick)
         print('gpio cb: {} {} {}'.format(gpio, level, tick))
    `

    The threshold can be given to the decorator as an argument (in millisec).
    This decorator can be used both on function and object's methods.

    Warning: as the debouncer uses the tick from pigpio, which wraps around
    after approximately 1 hour 12 minutes, you could theoretically miss one
    call if your callback is called twice with that interval.
    """
    threshold *= 1000
    max_tick = 0xFFFFFFFF

    class _decorated(object):

        def __init__(self, pigpio_cb):
            self._fn = pigpio_cb
            self.last = {}
            self.is_method = False

        def __call__(self, *args, **kwargs):
            if self.is_method:
                gpio = args[1]
                tick = args[3]
            else:
                gpio = args[0]
                tick = args[2]
            
            last = self.last.get(gpio) or 0
            if last > tick:
                delay = max_tick-last + tick
            else:
                delay = tick - last
            if delay > threshold:
                self._fn(*args, **kwargs)
                if print_status:
                    print('call passed by debouncer {} {} {} {}'
                      .format(gpio, tick, last, threshold)) 
                self.last[gpio] = tick
            elif print_status:
                print('call filtered out by debouncer {} {} {} {}'
                      .format(gpio, tick, last, threshold))

        def __get__(self, instance, type=None):
            # with is called when an instance of `_decorated` is used as a class
            # attribute, which is the case when decorating a method in a class
            self.is_method = True
            return functools.partial(self, instance)

    return _decorated

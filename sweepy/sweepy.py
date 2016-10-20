import ctypes
import collections

libsweep = ctypes.cdll.LoadLibrary('libsweep.so')

libsweep.sweep_get_version.restype = ctypes.c_int32
libsweep.sweep_get_version.argtypes = None

libsweep.sweep_is_abi_compatible.restype = ctypes.c_bool
libsweep.sweep_is_abi_compatible.argtypes = None

libsweep.sweep_error_message.restype = ctypes.c_char_p
libsweep.sweep_error_message.argtypes = [ctypes.c_void_p]

libsweep.sweep_error_destruct.restype = None
libsweep.sweep_error_destruct.argtypes = [ctypes.c_void_p]

libsweep.sweep_device_construct_simple.restype = ctypes.c_void_p
libsweep.sweep_device_construct_simple.argtypes = [ctypes.c_void_p]

libsweep.sweep_device_construct.restype = ctypes.c_void_p
libsweep.sweep_device_construct.argtypes = [ctypes.c_char_p, ctypes.c_int32, ctypes.c_int32, ctypes.c_void_p]

libsweep.sweep_device_destruct.restype = None
libsweep.sweep_device_destruct.argtypes = [ctypes.c_void_p]

libsweep.sweep_device_start_scanning.restype = None
libsweep.sweep_device_start_scanning.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

libsweep.sweep_device_stop_scanning.restype = None
libsweep.sweep_device_stop_scanning.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

libsweep.sweep_device_get_scan.restype = ctypes.c_void_p
libsweep.sweep_device_get_scan.argtypes = [ctypes.c_void_p, ctypes.c_int32, ctypes.c_void_p]

libsweep.sweep_scan_destruct.restype = None
libsweep.sweep_scan_destruct.argtypes = [ctypes.c_void_p]

libsweep.sweep_scan_get_number_of_samples.restype = ctypes.c_int32
libsweep.sweep_scan_get_number_of_samples.argtypes = [ctypes.c_void_p]

libsweep.sweep_scan_get_angle.restype = ctypes.c_int32
libsweep.sweep_scan_get_angle.argtypes = [ctypes.c_void_p, ctypes.c_int32]

libsweep.sweep_scan_get_distance.restype = ctypes.c_int32
libsweep.sweep_scan_get_distance.argtypes = [ctypes.c_void_p, ctypes.c_int32]

libsweep.sweep_device_get_motor_speed.restype = ctypes.c_int32
libsweep.sweep_device_get_motor_speed.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

libsweep.sweep_device_set_motor_speed.restype = None
libsweep.sweep_device_set_motor_speed.argtypes = [ctypes.c_void_p, ctypes.c_int32, ctypes.c_void_p]

libsweep.sweep_device_get_sample_rate.restype = ctypes.c_int32
libsweep.sweep_device_get_sample_rate.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

libsweep.sweep_device_reset.restype = None
libsweep.sweep_device_reset.argtypes = [ctypes.c_void_p, ctypes.c_void_p]


def error_to_exception(error):
    assert error
    what = libsweep.sweep_error_message(error)
    libsweep.sweep_error_destruct(error)
    return RuntimeError(what)


class Scan(collections.namedtuple('Scan', 'samples')):
    pass


class Sample(collections.namedtuple('Sample', 'angle distance')):
    pass


class Sweep:
    def __init__(_):
        _.scoped = False

    def __enter__(_):
        _.scoped = True
        _.device = None

        assert libsweep.sweep_is_abi_compatible(), 'Your installed libsweep is not ABI compatible with these bindings'

        error = ctypes.c_void_p();
        device = libsweep.sweep_device_construct_simple(ctypes.byref(error))

        if error:
            raise error_to_exception(error)

        _.device = device

        return _

    def __exit__(_, *args):
        _.scoped = False

        if _.device:
            libsweep.sweep_device_destruct(_.device)

    def _assert_scoped(_):
        assert _.scoped, 'Use the `with` statement to guarantee for deterministic resource management'

    def start_scanning(_):
        _._assert_scoped()

        error = ctypes.c_void_p();
        libsweep.sweep_device_start_scanning(_.device, ctypes.byref(error))

        if error:
            raise error_to_exception(error)

    def stop_scanning(_):
        _._assert_scoped();

        error = ctypes.c_void_p();
        libsweep.sweep_device_stop_scanning(_.device, ctypes.byref(error))

        if error:
            raise error_to_exception(error)

    def get_motor_speed(_):
        _._assert_scoped()

        error = ctypes.c_void_p()
        speed = libsweep.sweep_device_get_motor_speed(_.device, ctypes.byref(error))

        if error:
            raise error_to_exception(error)

        return speed

    def set_motor_speed(_, speed):
        _._assert_scoped()

        error = ctypes.c_void_p()
        libsweep.sweep_device_set_motor_speed(_.device, speed, ctypes.byref(error))

        if error:
            raise error_to_exception(error)

    def get_sample_rate(_):
        _._assert_scoped()

        error = ctypes.c_void_p()
        rate = libsweep.sweep_device_get_sample_rate(_.device, ctypes.byref(error))

        if error:
            raise error_to_exception(error)

        return rate

    def get_scans(_, timeout = 2000):
        _._assert_scoped()

        error = ctypes.c_void_p()

        while True:
            scan = libsweep.sweep_device_get_scan(_.device, timeout, ctypes.byref(error))

            if error:
                raise error_to_exception(error)

            num_samples = libsweep.sweep_scan_get_number_of_samples(scan)

            samples = [Sample(angle=libsweep.sweep_scan_get_angle(scan, n), distance=libsweep.sweep_scan_get_distance(scan, n))
                       for n in range(num_samples)]

            libsweep.sweep_scan_destruct(scan)

            yield Scan(samples=samples)


    def reset(_):
        _._assert_scoped();

        error = ctypes.c_void_p();
        libsweep.sweep_device_reset(_.device, ctypes.byref(error))

        if error:
            raise error_to_exception(error)


if __name__ == '__main__':
    error = ctypes.c_void_p()

    with Sweep() as sweep:
        sweep.start_scanning()
        sweep.stop_scanning()
        sweep.start_scanning()

        speed = sweep.get_motor_speed()
        sweep.set_motor_speed(speed + 1)

        rate = sweep.get_sample_rate()

        # get_scans is coroutine-based generator lazily returning scans ad infinitum
        for n, scan in enumerate(sweep.get_scans()):
            print('{}\n'.format(scan))

            if n == 3:
                break

        # resets the hardware; not needed to shut down this library, just for testing purpose
        sweep.reset()

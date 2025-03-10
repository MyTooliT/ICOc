"""Support for acceleration based sensor devices (SHA and STH)"""

# -- Imports ------------------------------------------------------------------

from icotronic.can.calibration import CalibrationMeasurementFormat
from icotronic.can.message import Message
from icotronic.can.sensor import SensorDevice

# -- Classes ------------------------------------------------------------------


class STH(SensorDevice):
    """Communicate and control a connected SHA or STH"""

    # ---------------------------
    # - Calibration Measurement -
    # ---------------------------

    async def _acceleration_self_test(
        self, activate: bool = True, dimension: str = "x"
    ) -> None:
        """Activate/Deactivate the accelerometer self test

        Parameters
        ----------

        activate:
            Either `True` to activate the self test or `False` to
            deactivate the self test

        dimension:
            The dimension (x=1, y=2, z=3) for which the self test should be
            activated/deactivated.

        """

        node = self.id
        method = "Activate" if activate else "Deactivate"

        try:
            dimension_number = "xyz".index(dimension) + 1
        except ValueError as error:
            raise ValueError(
                f"Invalid dimension value: “{dimension}”"
            ) from error

        message = Message(
            block="Configuration",
            block_command="Calibration Measurement",
            sender=self.spu.id,
            receiver=node,
            request=True,
            data=CalibrationMeasurementFormat(
                set=True,
                element="Data",
                method=method,
                dimension=dimension_number,
            ).data,
        )

        # pylint: disable=protected-access
        await self.spu._request(
            message,
            description=(
                f"{method.lower()} self test of {dimension}-axis of “{node}”"
            ),
        )
        # pylint: enable=protected-access

    async def activate_acceleration_self_test(
        self, dimension: str = "x"
    ) -> None:
        """Activate self test of STH accelerometer

        Parameters
        ----------

        dimension:
            The dimension (`x`, `y` or `z`) for which the self test should
            be activated.

        Examples
        --------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Activate and deactivate acceleration self-test

        >>> async def test_self_test():
        ...     async with Connection() as stu:
        ...         # We assume that at least one sensor device is available
        ...         async with stu.connect_sensor_device(0, STH) as sth:
        ...             await sth.activate_acceleration_self_test()
        ...             await sth.deactivate_acceleration_self_test()
        >>> run(test_self_test())

        """

        await self._acceleration_self_test(activate=True, dimension=dimension)

    async def deactivate_acceleration_self_test(
        self, dimension: str = "x"
    ) -> None:
        """Deactivate self test of STH accelerometer

        Parameters
        ----------

        dimension:
            The dimension (`x`, `y` or `z`) for which the self test should
            be deactivated.

        """

        await self._acceleration_self_test(activate=False, dimension=dimension)


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import testmod

    testmod()

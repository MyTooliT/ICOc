"""Test performance of streaming code"""

# -- Imports ------------------------------------------------------------------

from asyncio import run, wait_for
from time import perf_counter_ns, process_time_ns

from icotronic.can.adc import ADCConfiguration
from mytoolit.can import Network
from mytoolit.can.streaming import StreamingConfiguration

# -- Functions ----------------------------------------------------------------


async def stream(network):
    async with network.open_data_stream(
        StreamingConfiguration(first=True)
    ) as stream:
        async for data, _ in stream:
            pass


async def read_streaming_data(identifier, measurement_time=60):
    async with Network() as network:
        await network.connect_sensor_device(identifier)
        print(f"Connected to {identifier}")

        adc_config = ADCConfiguration(
            prescaler=2,
            acquisition_time=8,
            oversampling_rate=64,
        )
        await network.write_adc_configuration(**adc_config)
        sample_rate = adc_config.sample_rate()
        print(
            f"Sample rate: {sample_rate} Hz",
        )

        perf_start, cpu_start = perf_counter_ns(), process_time_ns()

        try:
            await wait_for(stream(network), timeout=measurement_time)
        except TimeoutError:
            pass

        perf_end, cpu_end = perf_counter_ns(), process_time_ns()
        run_time_command = perf_end - perf_start
        cpu_time_command = cpu_end - cpu_start
        cpu_usage = cpu_time_command / run_time_command * 100
        print(
            f"Ran {run_time_command / 10**9:.2f} seconds (CPU time:"
            f" {cpu_time_command / 10**9:.2f} seconds, CPU Usage:"
            f" {cpu_usage:.2f} %)"
        )


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    run(read_streaming_data(identifier="Test-STH"))
